from __future__ import annotations

from pathlib import Path

from lxml import etree

from purh_site.latei_metadata import extract_latei_metadata, parse_directors_override
from purh_site.reversible import compare_tei_elements, read_latex_document, write_tei_element
from purh_site.reversible_integration import run_reversible_export_for_file


def parse_xml(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


def write_xml(path: Path, xml: str) -> Path:
    path.write_text(xml, encoding="utf-8")
    return path


METOPES_HEADER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="tei-realiste">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type="main">Livre Metopes realiste</title>
        <title type="sub">Essai de structure PURH</title>
        <author role="pbd">
          <persName>
            <forename>Claire</forename>
            <surname>Directrice</surname>
          </persName>
        </author>
        <author>
          <persName>
            <forename>Alice</forename>
            <surname>Auteur</surname>
          </persName>
        </author>
        <editor>
          <persName>
            <forename>Marc</forename>
            <surname>Editeur</surname>
          </persName>
        </editor>
      </titleStmt>
      <publicationStmt>
        <publisher>Presses universitaires de Rouen et du Havre</publisher>
        <pubPlace>Rouen</pubPlace>
        <date type="publishing" when="2026">2026</date>
        <ab type="book">
          <idno type="ISBN-13">978-2-87775-000-0</idno>
          <idno type="ISSN">2427-0000</idno>
        </ab>
        <ab type="digital_download" subtype="PDF">
          <idno type="ISBN">978-2-87775-001-7</idno>
          <idno type="DOI">10.4000/purh.test-realiste</idno>
        </ab>
        <availability status="restricted">
          <licence target="https://creativecommons.org/licenses/by/4.0/">CC BY</licence>
        </availability>
      </publicationStmt>
      <seriesStmt>
        <title level="s">Collection essais</title>
        <biblScope unit="volume">42</biblScope>
        <idno type="ISSN">2600-1111</idno>
      </seriesStmt>
      <sourceDesc><p>TEI normalisee de test.</p></sourceDesc>
    </fileDesc>
    <profileDesc>
      <langUsage><language ident="fr">francais</language></langUsage>
      <abstract rend="resume"><p>Resume d'un volume de test pour la chaine PDF PURH.</p></abstract>
      <textClass>
        <keywords><term>edition</term><term>Metopes</term></keywords>
      </textClass>
    </profileDesc>
  </teiHeader>
  <text type="book" xml:id="book">
    <body><div type="chapter" xml:id="ch_001"><head>Introduction</head><p>Texte.</p></div></body>
  </text>
</TEI>
"""


def test_extract_latei_metadata_from_minimal_controlled_header() -> None:
    root = parse_xml(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc>"
        "<titleStmt><title type='main'>Titre principal</title></titleStmt>"
        "<publicationStmt>"
        "<publisher>PURH</publisher>"
        "<date type='publishing' when='2024'>2024</date>"
        "</publicationStmt>"
        "<sourceDesc><p>Source</p></sourceDesc>"
        "</fileDesc></teiHeader>"
        "<text><body><p>Texte.</p></body></text>"
        "</TEI>"
    )

    metadata = extract_latei_metadata(root)

    assert metadata.title == "Titre principal"
    assert metadata.subtitle == ""
    assert metadata.publisher == "PURH"
    assert metadata.publication_year == "2024"
    assert metadata.isbn_print == ""
    assert metadata.isbn_pdf == ""
    assert metadata.doi == ""


def test_extract_latei_metadata_from_realistic_metopes_header() -> None:
    metadata = extract_latei_metadata(parse_xml(METOPES_HEADER_XML))

    assert metadata.title == "Livre Metopes realiste"
    assert metadata.subtitle == "Essai de structure PURH"
    assert metadata.authors == ["Alice Auteur"]
    assert metadata.editors == ["Marc Editeur"]
    assert metadata.directors == ["Claire Directrice"]
    assert metadata.contributor_line == "Alice Auteur ; Marc Editeur ; Claire Directrice"
    assert metadata.publisher == "Presses universitaires de Rouen et du Havre"
    assert metadata.publication_place == "Rouen"
    assert metadata.publication_year == "2026"
    assert metadata.isbn_print == "978-2-87775-000-0"
    assert metadata.isbn_pdf == "978-2-87775-001-7"
    assert metadata.isbn_epub == ""
    assert metadata.preferred_isbn == "978-2-87775-001-7"
    assert metadata.doi == "10.4000/purh.test-realiste"
    assert metadata.issn == "2427-0000"
    assert metadata.collection_title == "Collection essais"
    assert metadata.collection_number == "42"
    assert metadata.collection_issn == "2600-1111"
    assert metadata.language == "fr"
    assert metadata.abstract == "Resume d'un volume de test pour la chaine PDF PURH."
    assert metadata.keywords == []
    assert metadata.rights == ""


def test_extract_latei_metadata_keeps_missing_fields_empty() -> None:
    root = parse_xml(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><titleStmt><title>Titre sans type</title></titleStmt>"
        "<publicationStmt><p>Publication</p></publicationStmt>"
        "<sourceDesc><p>Source</p></sourceDesc></fileDesc></teiHeader>"
        "<text><body><p>Texte.</p></body></text>"
        "</TEI>"
    )

    metadata = extract_latei_metadata(root)

    assert metadata.title == "Titre sans type"
    assert metadata.publisher == ""
    assert metadata.authors == []
    assert metadata.isbn_print == ""
    assert metadata.isbn_pdf == ""
    assert metadata.doi == ""
    assert metadata.language == ""
    assert metadata.abstract == ""
    assert metadata.keywords == []


def test_parse_directors_override_splits_on_et_comma_or_semicolon() -> None:
    """Fonction partagée entre le pipeline LaTeX/PDF
    (reversible_integration.py) et le pipeline HTML (site_builder.py) —
    voir référentiel PURH v0.7 §4.4."""
    assert parse_directors_override("Floriane Daguise et Florence Fix") == [
        "Floriane Daguise",
        "Florence Fix",
    ]
    assert parse_directors_override("Jean Dupont, Marie Martin") == ["Jean Dupont", "Marie Martin"]
    assert parse_directors_override("Jean Dupont; Marie Martin") == ["Jean Dupont", "Marie Martin"]
    assert parse_directors_override("  Jean Dupont  ") == ["Jean Dupont"]
    assert parse_directors_override("") == []


def test_latei_roundtrip_preserves_full_metopes_header(tmp_path: Path) -> None:
    xml_path = write_xml(tmp_path / "metopes.xml", METOPES_HEADER_XML)

    result = run_reversible_export_for_file(xml_path)
    body = result.latei_body_path.read_text(encoding="utf-8")
    source = etree.parse(str(xml_path)).getroot()
    emitted = write_tei_element(read_latex_document(body))

    assert result.success is True
    assert "name={teiHeader}" in body
    assert emitted.find(".//{http://www.tei-c.org/ns/1.0}teiHeader") is not None
    assert compare_tei_elements(source, emitted) == []
