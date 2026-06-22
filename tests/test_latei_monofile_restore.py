from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from purh_site.reversible import compare_tei_elements, read_tei_element, write_latex
from purh_site.reversible.latex_reader import (
    LatexParseError,
    extract_latei_document_zone,
    read_latex_document,
)
from purh_site.reversible_integration import (
    restore_xml_from_latei_body,
    restore_xml_from_latei_monofile,
    run_reversible_export_for_file,
)


TEI_NS = "http://www.tei-c.org/ns/1.0"

FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


def parse_xml(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


# ---------------------------------------------------------------------------
# Test 1 — extraction simple
# ---------------------------------------------------------------------------

def test_extract_latei_document_zone_returns_inner_content() -> None:
    monofile = (
        "\\documentclass{book}\n"
        "\\begin{document}\n"
        "\\begin{lateiDocument}\n"
        "\\teiP{Texte.}\n"
        "\\end{lateiDocument}\n"
        "\\end{document}\n"
    )
    zone = extract_latei_document_zone(monofile)
    assert zone.strip() == "\\teiP{Texte.}"


def test_extract_latei_document_zone_excludes_preamble() -> None:
    monofile = (
        "\\documentclass{book}\n"
        "\\usepackage{fontspec}\n"
        "\\begin{document}\n"
        "\\begin{lateiDocument}\n"
        "\\teiP{Contenu.}\n"
        "\\end{lateiDocument}\n"
        "\\end{document}\n"
    )
    zone = extract_latei_document_zone(monofile)
    assert "\\documentclass" not in zone
    assert "\\usepackage" not in zone
    assert "\\begin{document}" not in zone
    assert "\\teiP{Contenu.}" in zone


# ---------------------------------------------------------------------------
# Test 2 — erreur si marqueur absent
# ---------------------------------------------------------------------------

def test_extract_latei_document_zone_raises_if_begin_missing() -> None:
    with pytest.raises(LatexParseError, match=r"Missing \\begin\{lateiDocument\}"):
        extract_latei_document_zone(
            "\\documentclass{book}\n\\begin{document}\n\\end{document}\n"
        )


def test_extract_latei_document_zone_raises_if_end_missing() -> None:
    with pytest.raises(LatexParseError, match=r"Missing \\end\{lateiDocument\}"):
        extract_latei_document_zone(
            "\\begin{lateiDocument}\n\\teiP{Texte.}\n"
        )


# ---------------------------------------------------------------------------
# Test 3 — erreur si zone multiple
# ---------------------------------------------------------------------------

def test_extract_latei_document_zone_raises_on_multiple_zones() -> None:
    monofile = (
        "\\begin{lateiDocument}\n"
        "\\teiP{A.}\n"
        "\\end{lateiDocument}\n"
        "\\begin{lateiDocument}\n"
        "\\teiP{B.}\n"
        "\\end{lateiDocument}\n"
    )
    with pytest.raises(LatexParseError, match=r"Multiple"):
        extract_latei_document_zone(monofile)


# ---------------------------------------------------------------------------
# Shared fixture for tests 4 and 5
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def monofile_export(tmp_path_factory: pytest.TempPathFactory):
    output_dir = tmp_path_factory.mktemp("latei_monofile_restore")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir)


# ---------------------------------------------------------------------------
# Test 4 — restauration XML depuis monofichier généré
# ---------------------------------------------------------------------------

def test_restore_xml_from_latei_monofile_produces_xml(
    monofile_export, tmp_path: Path
) -> None:
    output_xml = tmp_path / "restored_from_mono.xml"
    restored_path = restore_xml_from_latei_monofile(
        monofile_export.latei_monofile_path, output_xml
    )
    assert restored_path == output_xml
    assert restored_path.exists()
    root = etree.parse(str(restored_path)).getroot()
    assert root is not None
    assert root.tag is not None


def test_restore_xml_from_latei_monofile_contains_tei_body(
    monofile_export, tmp_path: Path
) -> None:
    output_xml = tmp_path / "restored_with_body.xml"
    restore_xml_from_latei_monofile(monofile_export.latei_monofile_path, output_xml)
    content = output_xml.read_text(encoding="utf-8")
    assert "teiHeader" in content or "body" in content


# ---------------------------------------------------------------------------
# Test 5 — équivalence body / monofichier
# ---------------------------------------------------------------------------

def test_restore_body_and_monofile_are_equivalent(
    monofile_export, tmp_path: Path
) -> None:
    xml_from_body = tmp_path / "from_body.xml"
    xml_from_mono = tmp_path / "from_mono.xml"

    restore_xml_from_latei_body(monofile_export.latei_body_path, xml_from_body)
    restore_xml_from_latei_monofile(monofile_export.latei_monofile_path, xml_from_mono)

    root_body = etree.parse(str(xml_from_body)).getroot()
    root_mono = etree.parse(str(xml_from_mono)).getroot()

    assert compare_tei_elements(root_body, root_mono) == []


# ---------------------------------------------------------------------------
# Test 6 — le parser strict reste strict
# ---------------------------------------------------------------------------

def test_parser_strict_rejects_full_monofile(monofile_export) -> None:
    monofile_text = monofile_export.latei_monofile_path.read_text(encoding="utf-8")
    with pytest.raises(LatexParseError):
        read_latex_document(monofile_text)
