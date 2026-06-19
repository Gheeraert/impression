from __future__ import annotations

from pathlib import Path

from lxml import etree

from purh_site.latei_driver import compile_latei_pdf
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
    assert result.latei_macros_path == tmp_path / "mon_livre.latei_macros.tex"
    assert result.latei_pdf_path == tmp_path / "mon_livre.latei.pdf"
    assert result.latei_log_path == tmp_path / "mon_livre.latei_build.log"
    assert result.roundtrip_xml_path == tmp_path / "mon_livre.roundtrip.xml"
    assert result.diagnostics_path == tmp_path / "mon_livre.roundtrip_diagnostics.txt"
    assert result.latex_path.exists()
    assert result.latei_body_path.exists()
    assert result.latei_main_path.exists()
    assert result.latei_macros_path.exists()
    assert result.latei_log_path is not None
    assert result.latei_log_path.exists()
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
    assert "purh_site/resources/latei_macros.tex" not in main.replace("\\", "/")
    assert "book.latei_body.tex" in main
    assert r"\input" in main
    assert r"\newcommand{\PURHBookTitle}" in main

    source = etree.parse(str(xml_path)).getroot()
    emitted = write_tei_element(read_latex_document(body))

    assert compare_tei_elements(source, emitted) == []


def test_latei_driver_uses_header_metadata_and_keeps_header_reversible(tmp_path: Path) -> None:
    xml_path = write_xml(
        tmp_path / "metopes.xml",
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader>"
        "<fileDesc>"
        "<titleStmt>"
        '<title type="main">Titre principal</title>'
        '<title type="sub">Sous-titre</title>'
        "<author>Alice Auteur</author>"
        "</titleStmt>"
        "<publicationStmt>"
        "<publisher>PURH</publisher>"
        '<date type="publishing" when="2026-06-20">2026</date>'
        '<ab type="book"><idno type="ISBN-13">979-10-000-0000-0</idno></ab>'
        '<ab type="digital_download" subtype="PDF">'
        '<idno type="ISBN">979-10-000-0000-1</idno>'
        '<idno type="DOI">10.0000/purh.test</idno>'
        "</ab>"
        "</publicationStmt>"
        "<sourceDesc><p>Source</p></sourceDesc>"
        "</fileDesc>"
        "</teiHeader>"
        "<text><body><div type=\"chapter\" xml:id=\"ch_001\">"
        "<head>Introduction</head><p>Texte.</p>"
        "</div></body></text>"
        "</TEI>",
    )

    result = run_reversible_export_for_file(xml_path)
    body = result.latei_body_path.read_text(encoding="utf-8")
    main = result.latei_main_path.read_text(encoding="utf-8")
    macros = result.latei_macros_path.read_text(encoding="utf-8")

    assert result.success is True
    assert r"name={teiHeader}" in body
    assert r"\newcommand{\PURHBookTitle}{Titre principal}" in main
    assert r"\newcommand{\PURHBookSubtitle}{Sous-titre}" in main
    assert r"\newcommand{\PURHBookAuthor}{Alice Auteur}" in main
    assert r"\newcommand{\PURHPublisher}{PURH}" in main
    assert r"\newcommand{\PURHYear}{2026}" in main
    assert r"\newcommand{\PURHISBN}{979-10-000-0000-1}" in main
    assert r"\newcommand{\PURHDOI}{10.0000/purh.test}" in main
    assert r"\PurhSubtitle{\PURHBookSubtitle}" in main
    assert r"\PurhContributors{\PURHBookAuthor}" in main
    assert r"\PurhTitleExtra{ISBN PDF 979-10-000-0000-1}" in main
    assert r"\PurhTitleExtra{ISBN imprime 979-10-000-0000-0}" in main
    assert "name={teiHeader}" in macros
    assert "teiHeader is metadata, not running text" in macros

    source = etree.parse(str(xml_path)).getroot()
    emitted = write_tei_element(read_latex_document(body))

    assert emitted.find(".//{http://www.tei-c.org/ns/1.0}teiHeader") is not None
    assert compare_tei_elements(source, emitted) == []


def test_latei_macros_render_head_from_structural_context(tmp_path: Path) -> None:
    xml_path = write_xml(
        tmp_path / "heads.xml",
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<text><body>"
        '<div type="chapter"><head>Chapitre</head><p>Texte.</p></div>'
        '<div type="section"><head>Section</head><p>Texte.</p></div>'
        '<div type="section2"><head>Sous-section</head><p>Texte.</p></div>'
        '<div type="section3"><head>Sous-sous-section</head><p>Texte.</p></div>'
        "<figure><head>Figure 1</head><graphic target=\"fig.png\"/></figure>"
        '<table><head>Tableau 1</head><row><cell>A</cell></row></table>'
        "</body></text>"
        "</TEI>",
    )

    result = run_reversible_export_for_file(xml_path)
    body = result.latei_body_path.read_text(encoding="utf-8")
    macros = result.latei_macros_path.read_text(encoding="utf-8")

    assert result.success is True
    assert r"\teiHead{Chapitre}" in body
    assert r"\chapter{#1}" in macros
    assert r"\section{#1}" in macros
    assert r"\subsection{#1}" in macros
    assert r"\subsubsection{#1}" in macros
    assert r"\lateiSetHeadContext{chapter}" in macros
    assert r"\lateiSetHeadContext{figure}" in macros
    assert r"\lateiSetHeadContext{table}" in macros
    assert r"\lateiSetHeadContext{list}" in macros

    source = etree.parse(str(xml_path)).getroot()
    emitted = write_tei_element(read_latex_document(body))

    assert compare_tei_elements(source, emitted) == []


def test_latei_driver_is_portable_with_spaces_and_accents_in_names(tmp_path: Path) -> None:
    xml_path = write_xml(
        tmp_path / "Mon livre été.xml",
        '<p xmlns="http://www.tei-c.org/ns/1.0">Texte avec <hi rend="small-caps italic">style</hi>.</p>',
    )

    result = run_reversible_export_for_file(xml_path)
    main = result.latei_main_path.read_text(encoding="utf-8")

    assert result.latei_body_path.name == "Mon livre été.latei_body.tex"
    assert result.latei_main_path.name == "Mon livre été.latei_main.tex"
    assert result.latei_macros_path.name == "Mon livre été.latei_macros.tex"
    assert result.latei_body_path.exists()
    assert result.latei_main_path.exists()
    assert result.latei_macros_path.exists()
    assert r'\input{"Mon livre été.latei_body.tex"}' in main
    assert r'\input{"Mon livre été.latei_macros.tex"}' in main


def test_latei_macros_cover_combined_rend_nested_notes_and_header_suppression(tmp_path: Path) -> None:
    xml_path = write_xml(
        tmp_path / "book.xml",
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><titleStmt><title>Invisible</title></titleStmt>"
        "<publicationStmt><p>Publication</p></publicationStmt><sourceDesc><p>Source</p></sourceDesc>"
        "</fileDesc></teiHeader>"
        "<text><body><p>Texte <hi rend=\"sup italic small-caps bold\">x</hi>"
        "<note>Note <note>imbriquee</note></note><pb n=\"1\"/></p></body></text>"
        "</TEI>",
    )

    result = run_reversible_export_for_file(xml_path)
    macros = result.latei_macros_path.read_text(encoding="utf-8")

    assert "small-caps" in macros
    assert "italic" in macros
    assert "bold" in macros
    assert "sup" in macros
    assert "sub" in macros
    assert r"\iflateiinfootnote" in macros
    assert "Nested footnotes are not valid LaTeX" in macros
    assert "name={teiHeader}" in macros
    assert r"\teiPb" in macros
    assert r"\ignorespaces" in macros
    assert r"\teiGraphic" in macros


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
    assert result.latei_macros_path.parent == output_dir
    assert result.latei_pdf_path.parent == output_dir
    assert result.roundtrip_xml_path.parent == output_dir
    assert result.diagnostics_path.parent == output_dir
    assert not (source_dir / "livre.reversible.tex").exists()
    assert not (source_dir / "livre.latei_body.tex").exists()
    assert not (source_dir / "livre.latei_main.tex").exists()
    assert not (source_dir / "livre.latei_macros.tex").exists()
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
    assert not result.latei_macros_path.exists()
    assert result.latei_log_path is None
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
    assert not result.latei_macros_path.exists()
    assert result.latei_log_path is None
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
    first.latei_macros_path.write_text("old macros", encoding="utf-8")
    second = run_reversible_export_for_file(xml_path, output_dir)

    assert second.success is True
    assert second.latex_path.read_text(encoding="utf-8") == r"\teiP{Texte}"
    assert second.latei_body_path.read_text(encoding="utf-8") == r"\teiP{Texte}"
    assert r"\documentclass" in second.latei_main_path.read_text(encoding="utf-8")
    assert r"\NewDocumentCommand{\teiP}" in second.latei_macros_path.read_text(encoding="utf-8")
    assert unrelated.read_text(encoding="utf-8") == "keep me"


def test_latei_compile_missing_engine_writes_non_blocking_log(tmp_path: Path) -> None:
    main_path = tmp_path / "book.latei_main.tex"
    pdf_path = tmp_path / "book.latei.pdf"
    log_path = tmp_path / "book.latei_build.log"
    main_path.write_text(r"\documentclass{article}\begin{document}Texte\end{document}", encoding="utf-8")

    result = compile_latei_pdf(
        main_path,
        pdf_path,
        log_path=log_path,
        latex_engine="moteur-latei-introuvable",
    )

    assert result.success is False
    assert result.log_path == log_path
    assert "engine not found" in result.message
    assert log_path.exists()
    log = log_path.read_text(encoding="utf-8")
    assert "moteur-latei-introuvable" in log
    assert "Return code: not available" in log
