from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from purh_site.latei_metadata import extract_latei_metadata
from purh_site.reversible import run_tei_latex_tei_roundtrip
from purh_site.utils import TEI_NS, XML_NS


FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")
NS = {"tei": TEI_NS, "xml": XML_NS}


@pytest.fixture(scope="module")
def source_root() -> etree._Element:
    return etree.parse(str(FIXTURE_PATH)).getroot()


@pytest.fixture(scope="module")
def roundtrip_result(source_root: etree._Element):
    return run_tei_latex_tei_roundtrip(source_root)


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
