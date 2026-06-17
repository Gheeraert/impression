from __future__ import annotations

from pathlib import Path

from purh_site.latex_renderer import LatexRenderer
from purh_site.pdf_builder import PdfBuilder
from purh_site.semantic_model import FigureBlock, Italic, NoteRef, Paragraph, TextRun
from purh_site.tei_to_model import parse_normalized_tei


def write_tei(tmp_path: Path, body: str, *, title_stmt: str | None = None, publication_stmt: str | None = None) -> Path:
    title_stmt = title_stmt or """
      <titleStmt>
        <title type="main">Livre PDF</title>
        <title type="sub">Sous-titre PDF</title>
        <author>
          <persName>
            <forename>Alice</forename>
            <surname>Auteur</surname>
          </persName>
        </author>
      </titleStmt>
    """
    publication_stmt = publication_stmt or """
      <publicationStmt>
        <publisher>PURH</publisher>
        <pubPlace>Rouen</pubPlace>
        <date type="publishing" when="2024">2024</date>
      </publicationStmt>
    """
    xml_path = tmp_path / "book.normalized.xml"
    xml_path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      {title_stmt}
      {publication_stmt}
      <sourceDesc><p>Source de test.</p></sourceDesc>
    </fileDesc>
    <profileDesc>
      <langUsage><language ident="fr">français</language></langUsage>
    </profileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group xml:id="chapitre-1" type="chapter">
        <body>
          <head>Chapitre PDF</head>
          {body}
        </body>
      </group>
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    return xml_path


def render_latex(xml_path: Path) -> str:
    return LatexRenderer().render_book(parse_normalized_tei(xml_path))


def paragraph_text(paragraph: Paragraph) -> str:
    return "".join(node.text for node in paragraph.content if isinstance(node, TextRun))


def test_parse_minimal_tei_to_semantic_model(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Premier paragraphe du chapitre.</p>")

    book = parse_normalized_tei(xml_path)

    assert book.metadata.title == "Livre PDF"
    assert book.metadata.subtitle == "Sous-titre PDF"
    assert [contributor.full_name for contributor in book.metadata.contributors] == ["Alice Auteur"]
    assert book.metadata.publication.publisher == "PURH"
    assert book.metadata.publication.publication_year == "2024"
    assert len(book.body_divisions) == 1
    division = book.body_divisions[0]
    assert division.title == "Chapitre PDF"
    assert isinstance(division.blocks[0], Paragraph)
    assert paragraph_text(division.blocks[0]) == "Premier paragraphe du chapitre."


def test_latex_renderer_outputs_minimal_document(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Premier paragraphe du chapitre.</p>")

    latex = render_latex(xml_path)

    assert r"\documentclass[11pt,oneside,openany]{memoir}" in latex
    assert r"\begin{document}" in latex
    assert r"\end{document}" in latex
    assert "Livre PDF" in latex
    assert "Sous-titre PDF" in latex
    assert "Chapitre PDF" in latex
    assert "Premier paragraphe du chapitre." in latex
    assert "None" not in latex


def test_latex_renderer_escapes_dangerous_characters(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        "<p>Racine &amp; Port-Royal 50% prix $5 mot_cle #1 {texte}</p>",
    )

    latex = render_latex(xml_path)

    assert r"Racine \& Port-Royal" in latex
    assert r"50\%" in latex
    assert r"prix \$5" in latex
    assert r"mot\_cle" in latex
    assert r"\#1" in latex
    assert r"\{texte\}" in latex
    assert "Racine & Port-Royal" not in latex
    assert "50% prix $5 mot_cle #1 {texte}" not in latex


def test_latex_renderer_keeps_simple_inline_typography(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <p>
          Texte
          <hi rend="italic">italique</hi>
          <hi rend="bold">gras</hi>
          <hi rend="small-caps">Port-Royal</hi>
          <hi rend="sup">e</hi>
          <hi rend="sub">i</hi>.
        </p>
        """,
    )

    book = parse_normalized_tei(xml_path)
    paragraph = book.body_divisions[0].blocks[0]
    latex = LatexRenderer().render_book(book)

    assert isinstance(paragraph, Paragraph)
    assert any(isinstance(node, Italic) for node in paragraph.content)
    assert r"\textit{italique}" in latex
    assert r"\textbf{gras}" in latex
    assert r"\textsc{Port-Royal}" in latex
    assert r"\textsuperscript{e}" in latex
    assert r"$_{i}$" in latex


def test_simple_note_without_place_is_rendered_as_footnote(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte<note>Note simple.</note></p>")

    book = parse_normalized_tei(xml_path)
    paragraph = book.body_divisions[0].blocks[0]
    latex = LatexRenderer().render_book(book)

    assert isinstance(paragraph, Paragraph)
    assert any(isinstance(node, NoteRef) for node in paragraph.content)
    assert len(book.body_divisions[0].notes) == 1
    assert r"\footnote{Note simple.}" in latex
    assert "TexteNote simple." not in latex


def test_note_with_place_foot_is_rendered_as_footnote(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, '<p>Texte<note place="foot">Note de bas de page.</note></p>')

    latex = render_latex(xml_path)

    assert r"\footnote{Note de bas de page.}" in latex


def test_simple_figure_is_parsed_and_rendered_without_compilation(tmp_path: Path) -> None:
    figure_path = tmp_path / "figure.png"
    figure_path.write_bytes(b"fake-png")
    xml_path = write_tei(
        tmp_path,
        """
        <figure>
          <graphic url="figure.png"/>
          <head>Figure de test</head>
          <p rend="caption">Légende de test.</p>
        </figure>
        """,
    )

    book = parse_normalized_tei(xml_path)
    figure = book.body_divisions[0].blocks[0]

    assert isinstance(figure, FigureBlock)
    assert figure.image_path == "figure.png"
    assert LatexRenderer().render_book(book).count("Image absente ou non fournie") == 1

    result = PdfBuilder(compile_pdf=False).build_from_normalized_tei(xml_path, tmp_path / "pdf")
    tex = result.tex_path.read_text(encoding="utf-8")

    assert result.success is True
    assert result.commands == []
    assert r"\includegraphics" in tex
    assert "Figure de test" in tex
    assert "Légende de test" in tex


def test_pdf_builder_writes_latex_without_compilation(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte sans compilation.</p>")

    result = PdfBuilder(compile_pdf=False).build_from_normalized_tei(xml_path, tmp_path / "pdf")

    assert result.success is True
    assert result.tex_path.exists()
    assert result.report_path.exists()
    assert result.log_path.exists()
    assert result.commands == []
    assert not result.pdf_path.exists()
    assert "Texte sans compilation." in result.tex_path.read_text(encoding="utf-8")
    assert "Compilation PDF" in result.log_path.read_text(encoding="utf-8")
    assert "Aucune compilation" in result.report_path.read_text(encoding="utf-8")


def test_pdf_builder_reports_missing_latex_engine_without_real_tex_dependency(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte avec moteur absent.</p>")

    result = PdfBuilder(
        compile_pdf=True,
        latex_engine="moteur-introuvable-impressions",
    ).build_from_normalized_tei(xml_path, tmp_path / "pdf")

    assert result.success is False
    assert result.tex_path.exists()
    assert result.commands == []
    assert result.error_message is not None
    assert "Moteur LaTeX introuvable" in result.error_message
    assert "moteur-introuvable-impressions" in result.log_path.read_text(encoding="utf-8")
    assert "Succ" in result.report_path.read_text(encoding="utf-8")
