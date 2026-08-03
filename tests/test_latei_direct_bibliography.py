from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from lxml import etree

from purh_site.reversible import compare_tei_elements, read_latex_document, write_tei_element
from purh_site.reversible_integration import ReversibleExportResult, run_reversible_export_for_file

FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


def write_xml(path: Path, xml: str) -> Path:
    path.write_text(xml, encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def bibliography_export(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    tmp_path = tmp_path_factory.mktemp("latei_direct_bibliography")
    xml_path = write_xml(
        tmp_path / "bibliography.xml",
        '<listBibl xmlns="http://www.tei-c.org/ns/1.0" xml:id="bib_001">'
        "<head>Bibliographie</head>"
        '<bibl xml:id="bibl_simple">'
        "<author>Claire Auteur</author>, "
        '<title level="m">Livre simple</title>, '
        "<pubPlace>Rouen</pubPlace>, "
        "<publisher>PURH</publisher>, "
        '<date when="2026">2026</date>, '
        '<biblScope unit="page">p. 12-18</biblScope>, '
        '<idno type="DOI">10.0000/simple</idno>, '
        '<ref target="https://doi.org/10.0000/simple">DOI</ref>.'
        "</bibl>"
        '<biblStruct xml:id="bibl_struct">'
        "<analytic>"
        "<author>Jean Article</author>"
        '<title level="a">Article savant</title>'
        "</analytic>"
        "<monogr>"
        "<editor>Anne Editrice</editor>"
        '<title level="j">Revue savante</title>'
        "<imprint>"
        "<pubPlace>Paris</pubPlace>"
        "<publisher>Éditeur</publisher>"
        '<date when="2025">2025</date>'
        '<biblScope unit="volume">12</biblScope>'
        '<biblScope unit="page" from="20" to="40">p. 20-40</biblScope>'
        "</imprint>"
        "</monogr>"
        '<idno type="ISBN">979-10-000-0000-0</idno>'
        '<ref target="https://example.org/article">URL</ref>'
        "</biblStruct>"
        "</listBibl>",
    )
    return run_reversible_export_for_file(xml_path, tmp_path)


@pytest.fixture(scope="module")
def fixture_export(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    output_dir = tmp_path_factory.mktemp("latei_direct_real_bibliography")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir)


def test_latei_direct_bibliography_body_remains_reversible(
    bibliography_export: ReversibleExportResult,
) -> None:
    source = etree.parse(str(bibliography_export.source_path)).getroot()
    body = bibliography_export.latei_body_path.read_text(encoding="utf-8")
    emitted = write_tei_element(read_latex_document(body))

    assert bibliography_export.success is True
    assert bibliography_export.diagnostics_count == 0
    assert r"\begin{teiElement}[name={listBibl},xmlid={bib_001}]" in body
    assert r"\begin{teiBibl}[xmlid={bibl_simple}]" in body
    assert r"\begin{teiElement}[name={biblStruct},xmlid={bibl_struct}]" in body
    assert r"\begin{teiElement}[name={analytic}]" in body
    assert r"\begin{teiElement}[name={monogr}]" in body
    assert r"\begin{teiElement}[name={imprint}]" in body
    assert r"\begin{teiElement}[name={pubPlace}]" in body
    assert r"\teiAuthor{Claire Auteur}" in body
    assert r"\teiEditor{Anne Editrice}" in body
    assert r"\teiTitle[level={a}]{Article savant}" in body
    assert r"\teiTitle[level={m}]{Livre simple}" in body
    assert r"\teiTitle[level={j}]{Revue savante}" in body
    assert r"\teiPublisher{PURH}" in body
    assert r"\teiBiblScope[unit={page}]{p. 12-18}" in body
    assert r"\teiIdno[type={DOI}]{10.0000/simple}" in body
    assert r"\teiRef[target={https://doi.org/10.0000/simple}]{DOI}" in body
    assert compare_tei_elements(source, emitted) == []


def test_latei_direct_bibliography_macros_follow_stable_contract(
    bibliography_export: ReversibleExportResult,
) -> None:
    macros = bibliography_export.latei_macros_path.read_text(encoding="utf-8")

    assert "name={listBibl}" in macros
    assert "name={biblStruct}" in macros
    assert r"\begin{PurhBibliography}" in macros
    assert r"\end{PurhBibliography}" in macros
    assert r"\noindent\hangindent=1.5em\hangafter=1" in macros
    assert r"\NewDocumentEnvironment{teiBibl}" in macros
    assert r"\lateiBibliographyEntry" in macros
    assert r"\teiAuthor" in macros
    assert r"\teiEditor" in macros
    assert r"\teiPublisher" in macros
    assert r"\teiBiblScope" in macros
    assert r"\teiIdno" in macros
    assert r"\teiTitle" in macros
    assert "BibLaTeX" not in macros
    assert "biblatex" not in macros


def test_latei_direct_bibliography_compiles_when_lualatex_is_available(
    bibliography_export: ReversibleExportResult,
) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not bibliography_export.latei_pdf_success:
        log = bibliography_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:160])
        pytest.fail(f"Direct LaTEI bibliography sample did not compile.\n{excerpt}")

    assert bibliography_export.latei_pdf_path.exists()
    assert bibliography_export.latei_pdf_path.stat().st_size > 0


@pytest.mark.full_book
def test_latei_direct_real_fixture_bibliography_still_round_trips_and_compiles(
    fixture_export: ReversibleExportResult,
) -> None:
    body = fixture_export.latei_body_path.read_text(encoding="utf-8")

    assert fixture_export.success is True
    assert fixture_export.diagnostics_count == 0
    assert r"\begin{teiBibl}[xmlid={bibl-001}]" in body
    assert r"\begin{teiBibl}[xmlid={bibl-451}]" in body

    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not fixture_export.latei_pdf_success:
        log = fixture_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:160])
        pytest.fail(f"Direct LaTEI PDF failed on the real Metopes fixture.\n{excerpt}")

    assert fixture_export.latei_pdf_path.exists()
    assert fixture_export.latei_pdf_path.stat().st_size > 0
