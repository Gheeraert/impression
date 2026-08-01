from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from lxml import etree

from purh_site.latei_metadata import extract_latei_metadata
from purh_site.reversible import run_tei_latex_tei_roundtrip
from purh_site.reversible_integration import ReversibleExportResult, run_reversible_export_for_file
from purh_site.utils import TEI_NS, XML_NS

FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")
NS = {"tei": TEI_NS, "xml": XML_NS}


@pytest.fixture(scope="module")
def source_root() -> etree._Element:
    return etree.parse(str(FIXTURE_PATH)).getroot()


@pytest.fixture(scope="module")
def roundtrip_result(source_root: etree._Element):
    return run_tei_latex_tei_roundtrip(source_root)


@pytest.fixture(scope="module")
def export_result(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    output_dir = tmp_path_factory.mktemp("heraldique_latei_export")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir)


def test_real_metopes_fixture_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_real_metopes_fixture_metadata_matches_commons_publication_blocks(source_root: etree._Element) -> None:
    metadata = extract_latei_metadata(source_root)

    assert metadata.title == "Héraldique et papauté. Moyen Âge-Temps modernes. II"
    assert metadata.subtitle == ""
    assert metadata.publisher == "PURH"
    assert metadata.publication_year == "2025"
    assert metadata.isbn_print == "979-10-240-1855-3"
    assert metadata.isbn_pdf == ""
    assert metadata.isbn_epub == ""
    assert metadata.doi == ""
    assert metadata.issn == ""
    assert metadata.collection_title == ""
    assert metadata.collection_number == ""
    assert metadata.collection_issn == ""
    assert metadata.language == "fr-FR"


def test_real_metopes_fixture_round_trips_without_diagnostics(roundtrip_result) -> None:
    emitted = roundtrip_result.emitted

    assert roundtrip_result.diagnostics == []
    assert emitted.tag == f"{{{TEI_NS}}}TEI"
    assert emitted.get(f"{{{XML_NS}}}id") is None
    assert emitted.find("./tei:teiHeader", namespaces=NS) is not None
    assert emitted.xpath("count(./tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:ab)", namespaces=NS) == 5.0
    assert emitted.xpath(
        "string(./tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:ab[@type='book']//tei:idno[@type='ISBN-13'])",
        namespaces=NS,
    ) == "979-10-240-1855-3"
    assert emitted.xpath(
        "boolean(./tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:ab[@type='digital_download' and @subtype='PDF'])",
        namespaces=NS,
    )
    assert emitted.xpath(
        "boolean(./tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:ab[@type='digital_download' and @subtype='EPUB'])",
        namespaces=NS,
    )


def test_real_metopes_fixture_latex_preserves_metopes_structures(roundtrip_result) -> None:
    latex = roundtrip_result.latex

    assert r"\begin{teiElement}[name={teiHeader}]" in latex
    assert r"\teiTitle[type={main}]{Héraldique et papauté. Moyen Âge-Temps modernes. II}" in latex
    assert r"\begin{teiElement}[name={ab},type={book}]" in latex
    assert r"\begin{teiElement}[name={ab},subtype={PDF},type={digital\_download}]" in latex
    assert r"\begin{teiElement}[name={ab},subtype={EPUB},type={digital\_download}]" in latex
    assert r"\begin{teiDiv}[type={section1},xmlid={div01}]" in latex
    assert r"\teiHead[xmlid={le-pontifical-de-1520-001}]{Le pontifical de 1520}" in latex
    assert r"\begin{teiFigure}[xmlid={figure01}]" in latex
    assert r"\teiGraphic[url={../icono/br/Ch02\_Doulkaridou/fig1.jpg}]" in latex
    assert r"\teiRef[target={http://corsair.themorgan.org/vwebv/holdingsInfo?bibId=76897}]" in latex


def test_real_metopes_fixture_preserves_key_counts_and_attributes(source_root: etree._Element, roundtrip_result) -> None:
    emitted = roundtrip_result.emitted

    for expression in [
        "count(.//tei:div[@type='section1'])",
        "count(.//tei:div[@type='section2'])",
        "count(.//tei:div[@type='section3'])",
        "count(.//tei:figure)",
        "count(.//tei:graphic[@url])",
        "count(.//tei:ref[@target])",
        "count(.//*[@xml:id])",
    ]:
        assert emitted.xpath(expression, namespaces=NS) == source_root.xpath(expression, namespaces=NS)

    assert emitted.xpath("string((.//tei:graphic[@url])[1]/@url)", namespaces=NS) == "../icono/br/Ch02_Doulkaridou/fig1.jpg"
    assert emitted.xpath("string((.//tei:div[@type='section1']/tei:head)[1])", namespaces=NS) == "Le pontifical de 1520"
    assert emitted.xpath("boolean(.//tei:hi[@rend='italic'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:hi[@rend='small-caps'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:hi[@rend='sup'])", namespaces=NS)


def test_real_metopes_fixture_full_latei_export_package(export_result: ReversibleExportResult) -> None:
    result = export_result

    assert result.success is True
    assert result.diagnostics_count == 0
    assert result.latei_body_path.exists()
    assert result.latei_main_path.exists()
    assert result.latei_macros_path.exists()
    assert result.latei_log_path is not None
    assert result.latei_log_path.exists()
    assert result.roundtrip_xml_path.exists()
    assert result.diagnostics_path.exists()

    body = result.latei_body_path.read_text(encoding="utf-8")
    main = result.latei_main_path.read_text(encoding="utf-8")

    assert r"\documentclass" not in body
    assert r"\documentclass[12pt,twoside,openany]{book}" in main
    assert rf'\input{{"{result.latei_macros_path.name}"}}' in main
    assert rf'\input{{"{result.latei_body_path.name}"}}' in main
    assert "purh_site/resources/latei_macros.tex" not in main.replace("\\", "/")
    assert r"\begin{teiElement}[name={teiHeader}]" in body
    assert r"\begin{teiDiv}[type={section1},xmlid={div01}]" in body
    assert r"\teiHead[xmlid={le-pontifical-de-1520-001}]{Le pontifical de 1520}" in body
    assert r"\begin{teiFigure}[xmlid={figure01}]" in body
    assert r"\teiGraphic[url={../icono/br/Ch02\_Doulkaridou/fig1.jpg}]" in body


def test_real_metopes_fixture_full_export_uses_real_metadata(export_result: ReversibleExportResult) -> None:
    main = export_result.latei_main_path.read_text(encoding="utf-8")

    assert r"\newcommand{\PURHBookTitle}{Héraldique et papauté. Moyen Âge-Temps modernes. II}" in main
    assert r"\newcommand{\PURHPublisher}{PURH}" in main
    assert r"\newcommand{\PURHYear}{2025}" in main
    assert r"\newcommand{\PURHISBN}{979-10-240-1855-3}" in main
    assert r"\newcommand{\PURHDOI}{}" in main
    assert r"\newcommand{\PURHBookSubtitle}{}" in main
    assert r"\PurhTitleExtra{PURH}" in main
    assert r"\PurhTitleExtra{PURH - 2025}" not in main
    assert r"\PurhTitleExtra{ISBN imprime 979-10-240-1855-3}" not in main

    metadata = extract_latei_metadata(etree.parse(str(FIXTURE_PATH)).getroot())
    assert metadata.language == "fr-FR"
    assert metadata.isbn_pdf == ""
    assert metadata.isbn_epub == ""
    assert metadata.doi == ""


def test_real_metopes_running_titles_map_preserves_nbsp_in_keys(export_result: ReversibleExportResult) -> None:
    """Running-title map keys for titles containing U+00A0 must preserve NBSP.
    Audit F2 identified 6 chapters where the lookup failed because _normalize_space
    converted NBSP to a regular space while LaTeX's \\newunicodechar{ }{~} produced
    ~ from the body-attribute U+00A0.  After F3, the map keys must carry NBSP so
    that \\newunicodechar converts both sides of the prop lookup identically."""
    running_map = export_result.latei_running_titles_map_path.read_text(encoding="utf-8")

    # Four of the six problematic chapters — all contain U+00A0 between first name
    # and Roman numeral and exceed 58 chars, so they need a map entry.
    for fragment in [
        "L\xe9on\xa0X",
        "Jules\xa0III",
        "Urbain\xa0VIII",
        "Cl\xe9ment\xa0XIII",
    ]:
        assert fragment in running_map, (
            f"NBSP-preserved fragment {fragment!r} not found in running-title map.\n"
            "This means _normalize_space is still converting U+00A0 to a regular space."
        )


def test_real_metopes_fixture_latei_compilation_status_is_explicit(export_result: ReversibleExportResult) -> None:
    log_path = export_result.latei_log_path

    assert log_path is not None
    assert log_path.exists()
    log = log_path.read_text(encoding="utf-8", errors="replace")
    assert "LaTEI build log" in log
    assert "Command:" in log

    if shutil.which("lualatex") is None:
        assert export_result.latei_pdf_success is False
        assert "engine not found" in export_result.latei_pdf_message
        assert "LaTeX engine not found: lualatex" in log
        return

    if not export_result.latei_pdf_success:
        excerpt = "\n".join(log.splitlines()[:120])
        pytest.fail(f"LaTEI PDF compilation failed on the real Metopes fixture.\n{excerpt}")

    assert export_result.latei_pdf_path.exists()
    assert export_result.latei_pdf_path.stat().st_size > 0
