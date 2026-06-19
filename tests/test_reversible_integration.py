from __future__ import annotations

from pathlib import Path

from lxml import etree

from purh_site.reversible import compare_tei_elements, read_latex_document, write_tei_element
from purh_site.reversible_integration import run_reversible_export_for_file


def write_xml(path: Path, xml: str) -> Path:
    path.write_text(xml, encoding="utf-8")
    return path


def test_reversible_export_writes_latex_roundtrip_xml_and_diagnostics(tmp_path: Path) -> None:
    xml_path = write_xml(
        tmp_path / "mon_livre.xml",
        '<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_001">'
        'Un <hi rend="italic">mot</hi>.'
        "</p>",
    )

    result = run_reversible_export_for_file(xml_path)

    assert result.success is True
    assert result.diagnostics_count == 0
    assert result.latex_path == tmp_path / "mon_livre.reversible.tex"
    assert result.latei_body_path == tmp_path / "mon_livre.latei_body.tex"
    assert result.latei_main_path == tmp_path / "mon_livre.latei_main.tex"
    assert result.latei_pdf_path == tmp_path / "mon_livre.latei.pdf"
    assert result.roundtrip_xml_path == tmp_path / "mon_livre.roundtrip.xml"
    assert result.diagnostics_path == tmp_path / "mon_livre.roundtrip_diagnostics.txt"
    assert result.latex_path.exists()
    assert result.latei_body_path.exists()
    assert result.latei_main_path.exists()
    assert result.roundtrip_xml_path.exists()
    assert result.diagnostics_path.exists()
    assert "\\teiP" in result.latex_path.read_text(encoding="utf-8")
    assert result.latei_body_path.read_text(encoding="utf-8") == result.latex_path.read_text(encoding="utf-8")
    assert "No documentary diagnostic" in result.diagnostics_path.read_text(encoding="utf-8")

    emitted = etree.parse(str(result.roundtrip_xml_path)).getroot()
    assert emitted.tag == "{http://www.tei-c.org/ns/1.0}p"
    assert emitted.get("{http://www.w3.org/XML/1998/namespace}id") == "p_001"


def test_latei_body_is_reversible_and_latei_main_is_driver_only(tmp_path: Path) -> None:
    xml_path = write_xml(
        tmp_path / "book.xml",
        '<p xmlns="http://www.tei-c.org/ns/1.0">Un <hi rend="italic">mot</hi>.</p>',
    )

    result = run_reversible_export_for_file(xml_path)
    body = result.latei_body_path.read_text(encoding="utf-8")
    main = result.latei_main_path.read_text(encoding="utf-8")

    assert r"\documentclass" not in body
    assert r"\documentclass[12pt,twoside,openany]{book}" in main
    assert "latei_macros.tex" in main
    assert "book.latei_body.tex" in main
    assert r"\input" in main
    assert r"\newcommand{\PURHBookTitle}" in main

    source = etree.parse(str(xml_path)).getroot()
    emitted = write_tei_element(read_latex_document(body))

    assert compare_tei_elements(source, emitted) == []


def test_reversible_export_uses_explicit_output_directory(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "out"
    source_dir.mkdir()
    xml_path = write_xml(
        source_dir / "livre.xml",
        '<p xmlns="http://www.tei-c.org/ns/1.0">Texte</p>',
    )

    result = run_reversible_export_for_file(xml_path, output_dir)

    assert result.success is True
    assert result.latex_path.parent == output_dir
    assert result.latei_body_path.parent == output_dir
    assert result.latei_main_path.parent == output_dir
    assert result.latei_pdf_path.parent == output_dir
    assert result.roundtrip_xml_path.parent == output_dir
    assert result.diagnostics_path.parent == output_dir
    assert not (source_dir / "livre.reversible.tex").exists()
    assert not (source_dir / "livre.latei_body.tex").exists()
    assert not (source_dir / "livre.latei_main.tex").exists()
    assert xml_path.read_text(encoding="utf-8") == '<p xmlns="http://www.tei-c.org/ns/1.0">Texte</p>'


def test_reversible_export_reports_missing_file_without_writing_source(tmp_path: Path) -> None:
    missing = tmp_path / "absent.xml"

    result = run_reversible_export_for_file(missing)

    assert result.success is False
    assert result.diagnostics_count == 1
    assert "does not exist" in result.message
    assert result.diagnostics_path.exists()
    assert not result.latex_path.exists()
    assert not result.latei_body_path.exists()
    assert not result.latei_main_path.exists()
    assert not result.roundtrip_xml_path.exists()


def test_reversible_export_reports_malformed_xml(tmp_path: Path) -> None:
    xml_path = write_xml(tmp_path / "malformed.xml", "<p>")

    result = run_reversible_export_for_file(xml_path)

    assert result.success is False
    assert result.diagnostics_count == 1
    assert "Malformed XML" in result.message
    assert result.diagnostics_path.exists()
    assert "failed" in result.diagnostics_path.read_text(encoding="utf-8")
    assert not result.latex_path.exists()
    assert not result.latei_body_path.exists()
    assert not result.latei_main_path.exists()
    assert not result.roundtrip_xml_path.exists()


def test_reversible_export_overwrites_only_expected_output_files(tmp_path: Path) -> None:
    xml_path = write_xml(
        tmp_path / "sample.xml",
        '<p xmlns="http://www.tei-c.org/ns/1.0">Texte</p>',
    )
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    unrelated = output_dir / "unrelated.txt"
    unrelated.write_text("keep me", encoding="utf-8")

    first = run_reversible_export_for_file(xml_path, output_dir)
    first.latex_path.write_text("old", encoding="utf-8")
    first.latei_body_path.write_text("old body", encoding="utf-8")
    first.latei_main_path.write_text("old main", encoding="utf-8")
    second = run_reversible_export_for_file(xml_path, output_dir)

    assert second.success is True
    assert second.latex_path.read_text(encoding="utf-8") == r"\teiP{Texte}"
    assert second.latei_body_path.read_text(encoding="utf-8") == r"\teiP{Texte}"
    assert r"\documentclass" in second.latei_main_path.read_text(encoding="utf-8")
    assert unrelated.read_text(encoding="utf-8") == "keep me"
