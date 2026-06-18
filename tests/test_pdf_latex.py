from __future__ import annotations

from pathlib import Path

from purh_site.latex_renderer import LatexRenderer, LatexRenderOptions, _short_running_title
from purh_site.pdf_builder import PdfBuilder
from purh_site.semantic_model import BibliographyBlock, FigureBlock, Italic, NoteRef, Paragraph, TableBlock, TextRun
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


def render_latex_with_options(xml_path: Path, options: LatexRenderOptions) -> str:
    return LatexRenderer(options=options).render_book(parse_normalized_tei(xml_path))


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
    assert r"\newcommand{\PurhVolumeTitle}" not in latex
    assert r"\pagestyle{purh}" not in latex
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


def test_existing_figure_path_is_rendered_with_includegraphics(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    figure_path = images_dir / "figure test.png"
    figure_path.write_bytes(b"fake-png")
    xml_path = write_tei(
        tmp_path,
        """
        <figure>
          <graphic url="images/figure test.png"/>
          <head>Figure existante</head>
          <p rend="caption">Légende.</p>
        </figure>
        """,
    )

    result = PdfBuilder(compile_pdf=False).build_from_normalized_tei(xml_path, tmp_path / "pdf")
    tex = result.tex_path.read_text(encoding="utf-8")

    assert result.success is True
    assert result.warnings == []
    assert r"\includegraphics" in tex
    assert r"\detokenize{" in tex
    assert "images/figure test.png" in tex
    assert figure_path.resolve().as_posix() in tex
    assert "Image absente ou non fournie" not in tex


def test_missing_figure_path_renders_fallback_and_warning(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <figure>
          <graphic url="images/manquante.png"/>
          <head>Figure manquante</head>
        </figure>
        """,
    )

    result = PdfBuilder(compile_pdf=False).build_from_normalized_tei(xml_path, tmp_path / "pdf")
    tex = result.tex_path.read_text(encoding="utf-8")
    report = result.report_path.read_text(encoding="utf-8")

    assert result.success is True
    assert "Image absente ou non fournie" in tex
    assert any("Image introuvable" in warning for warning in result.warnings)
    assert "Image introuvable" in report


def test_figure_title_caption_and_credits_are_rendered(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "figure.png").write_bytes(b"fake-png")
    xml_path = write_tei(
        tmp_path,
        """
        <figure>
          <graphic url="images/figure.png"/>
          <head>Figure 1. Titre &amp; détail</head>
          <p rend="caption">Légende 50% de la figure.</p>
          <p rend="credits">Crédits : PURH #1.</p>
        </figure>
        """,
    )

    result = PdfBuilder(compile_pdf=False).build_from_normalized_tei(xml_path, tmp_path / "pdf")
    tex = result.tex_path.read_text(encoding="utf-8")

    assert r"\textbf{Figure 1. Titre \& détail}" in tex
    assert r"Légende 50\% de la figure" in tex
    assert r"Crédits : PURH \#1" in tex
    assert "None" not in tex


def test_figure_uses_existing_alternative_image_when_main_image_is_missing(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    alternative_path = images_dir / "alternative figure.png"
    alternative_path.write_bytes(b"fake-png")
    xml_path = write_tei(
        tmp_path,
        """
        <figure>
          <graphic url="images/manquante.png"/>
          <graphic type="alternative" url="images/alternative figure.png"/>
          <head>Figure alternative</head>
        </figure>
        """,
    )

    result = PdfBuilder(compile_pdf=False).build_from_normalized_tei(xml_path, tmp_path / "pdf")
    tex = result.tex_path.read_text(encoding="utf-8")

    assert result.success is True
    assert result.warnings == []
    assert r"\includegraphics" in tex
    assert alternative_path.resolve().as_posix() in tex
    assert "images/manquante.png" not in tex
    assert "Image absente ou non fournie" not in tex


def test_biblstruct_monograph_is_parsed_and_rendered_to_latex(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <head>Bibliographie</head>
          <biblStruct>
            <monogr>
              <author><persName><forename>Blaise</forename><surname>Pascal</surname></persName></author>
              <title level="m">Pensées</title>
              <imprint>
                <pubPlace>Paris</pubPlace>
                <publisher>Gallimard</publisher>
                <date when="1976">1976</date>
              </imprint>
              <idno type="ISBN">9782070100010</idno>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    book = parse_normalized_tei(xml_path)
    bibliography = next(block for block in book.body_divisions[0].blocks if isinstance(block, BibliographyBlock))
    item = bibliography.items[0]
    latex = LatexRenderer().render_book(book)

    assert item.structured is not None
    assert item.structured.kind == "monograph"
    assert [author.name for author in item.structured.authors] == ["Blaise Pascal"]
    assert item.structured.monograph_title is not None
    assert item.structured.monograph_title.text == "Pensées"
    assert item.structured.pub_place == "Paris"
    assert item.structured.publisher == "Gallimard"
    assert item.structured.date == "1976"
    assert item.structured.identifiers[0].value == "9782070100010"
    assert r"Blaise Pascal, \textit{Pensées}, Paris, Gallimard, 1976. ISBN 9782070100010." in latex
    assert "None" not in latex


def test_biblstruct_contribution_in_edited_volume_is_rendered_to_latex(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <analytic>
              <author><persName><forename>Jean</forename><surname>Dupont</surname></persName></author>
              <title level="a">Un chapitre important</title>
            </analytic>
            <monogr>
              <editor><persName><forename>Claire</forename><surname>Martin</surname></persName></editor>
              <title level="m">Volume collectif</title>
              <imprint>
                <pubPlace>Rouen</pubPlace>
                <publisher>PURH</publisher>
                <date>2026</date>
                <biblScope unit="page" from="15" to="32">p. 15-32</biblScope>
              </imprint>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert r"Jean Dupont, \enquote{Un chapitre important}, dans Claire Martin (dir.)" in latex
    assert r"\textit{Volume collectif}, Rouen, PURH, 2026, p.~15-32." in latex
    assert "dans (dir.)" not in latex
    assert "(dir.), ," not in latex


def test_biblstruct_journal_article_is_rendered_to_latex(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <analytic>
              <author><persName><forename>Marie</forename><surname>Leroy</surname></persName></author>
              <title level="a">Article savant</title>
            </analytic>
            <monogr>
              <title level="j">Revue d’histoire littéraire</title>
              <imprint>
                <biblScope unit="volume">123</biblScope>
                <biblScope unit="issue">2</biblScope>
                <date>2024</date>
                <biblScope unit="page">p. 45-67</biblScope>
              </imprint>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert r"Marie Leroy, \enquote{Article savant}, \textit{Revue d’histoire littéraire}" in latex
    assert "vol.~123" in latex
    assert r"n\textsuperscript{o}~2" in latex
    assert "2024" in latex
    assert "p.~45-67" in latex
    assert "vol. 123" not in latex
    assert "no 2" not in latex


def test_biblstruct_pages_are_normalized_in_purh_style(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <analytic><author>Alice</author><title level="a">Premier</title></analytic>
            <monogr><title level="j">Revue</title><imprint><biblScope unit="page">45-67</biblScope></imprint></monogr>
          </biblStruct>
          <biblStruct>
            <analytic><author>Bruno</author><title level="a">Deuxième</title></analytic>
            <monogr><title level="j">Revue</title><imprint><biblScope unit="page">p. 45-67</biblScope></imprint></monogr>
          </biblStruct>
          <biblStruct>
            <analytic><author>Claire</author><title level="a">Troisième</title></analytic>
            <monogr><title level="j">Revue</title><imprint><biblScope unit="page">p.~45-67</biblScope></imprint></monogr>
          </biblStruct>
          <biblStruct>
            <analytic><author>David</author><title level="a">Quatrième</title></analytic>
            <monogr><title level="j">Revue</title><imprint><biblScope unit="page">15</biblScope></imprint></monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert latex.count("p.~45-67") == 3
    assert "p.~15" in latex
    assert "p. p." not in latex
    assert "p.~p." not in latex


def test_biblstruct_journal_volume_and_issue_use_french_latex_style(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <analytic><author>Alice</author><title level="a">Article</title></analytic>
            <monogr>
              <title level="j">Revue</title>
              <imprint>
                <biblScope unit="volume">vol. 123</biblScope>
                <biblScope unit="issue">no 2</biblScope>
              </imprint>
            </monogr>
          </biblStruct>
          <biblStruct>
            <analytic><author>Bruno</author><title level="a">Article bis</title></analytic>
            <monogr>
              <title level="j">Revue</title>
              <imprint>
                <biblScope unit="volume">123</biblScope>
                <biblScope unit="issue">n° 2</biblScope>
              </imprint>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert latex.count("vol.~123") == 2
    assert latex.count(r"n\textsuperscript{o}~2") == 2
    assert "vol. 123" not in latex
    assert "no 2" not in latex


def test_biblstruct_contribution_pages_use_non_breaking_space(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <analytic>
              <author>Jean Dupont</author>
              <title level="a">Chapitre</title>
            </analytic>
            <monogr>
              <editor>Claire Martin</editor>
              <title level="m">Volume collectif</title>
              <imprint><biblScope unit="page">p. 15-32</biblScope></imprint>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert "p.~15-32" in latex
    assert "p. 15-32" not in latex


def test_biblstruct_missing_publication_parts_do_not_leave_orphan_punctuation(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <monogr>
              <author>Autrice</author>
              <title level="m">Titre seul avec date</title>
              <imprint><date>2026</date></imprint>
            </monogr>
          </biblStruct>
          <biblStruct>
            <monogr>
              <title level="m">Titre seul</title>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert r"Autrice, \textit{Titre seul avec date}, 2026." in latex
    assert r"\textit{Titre seul}." in latex
    assert ", ," not in latex
    assert ", ." not in latex
    assert "None" not in latex


def test_biblstruct_multiple_authors_and_editors_are_joined_readably(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <monogr>
              <author><persName><forename>Alice</forename><surname>Auteur</surname></persName></author>
              <author><persName><forename>Bruno</forename><surname>Auteur</surname></persName></author>
              <title level="m">Livre à deux voix</title>
            </monogr>
          </biblStruct>
          <biblStruct>
            <analytic>
              <author><persName><forename>Claire</forename><surname>Autrice</surname></persName></author>
              <author><persName><forename>David</forename><surname>Auteur</surname></persName></author>
              <author><persName><forename>Emma</forename><surname>Autrice</surname></persName></author>
              <title level="a">Contribution collective</title>
            </analytic>
            <monogr>
              <editor><persName><forename>Paul</forename><surname>Durand</surname></persName></editor>
              <editor><persName><forename>Anne</forename><surname>Petit</surname></persName></editor>
              <editor><persName><forename>Luc</forename><surname>Morel</surname></persName></editor>
              <title level="m">Volume dirigé</title>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert r"Alice Auteur et Bruno Auteur, \textit{Livre à deux voix}." in latex
    assert "Claire Autrice, David Auteur et Emma Autrice" in latex
    assert "Paul Durand, Anne Petit et Luc Morel (dir.)" in latex
    assert latex.count("(dir.)") == 1


def test_biblstruct_article_title_already_quoted_is_not_double_quoted(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <analytic>
              <author>Autrice</author>
              <title level="a">« Déjà guillemeté »</title>
            </analytic>
            <monogr>
              <title level="j">Revue</title>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert r"\enquote{« Déjà guillemeté »}" not in latex
    assert "« Déjà guillemeté »" in latex
    assert latex.count("« Déjà guillemeté »") == 1


def test_biblstruct_identifiers_are_rendered_readably(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <monogr>
              <author>Autrice</author>
              <title level="m">Livre avec identifiants</title>
              <idno type="ISBN-13">978-2-87775-000-1</idno>
              <idno type="DOI">10.4000/test_pdf</idno>
              <ref type="DOI" target="https://doi.org/10.4000/deja">https://doi.org/10.4000/deja</ref>
              <idno type="URI">https://example.org/ouvrage</idno>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert "ISBN 978-2-87775-000-1." in latex
    assert r"\href{https://doi.org/10.4000/test\_pdf}{10.4000/test\_pdf}" in latex
    assert r"\href{https://doi.org/10.4000/deja}{https://doi.org/10.4000/deja}" in latex
    assert r"URI \href{https://example.org/ouvrage}{https://example.org/ouvrage}." in latex
    assert "https://doi.org/https://doi.org" not in latex
    assert ".." not in latex


def test_biblstruct_identifiers_do_not_duplicate_periods_or_doi_prefix(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <monogr>
              <author>Autrice</author>
              <title level="m">Livre avec ponctuation</title>
              <idno type="DOI">10.4000/brut.</idno>
              <idno type="DOI">https://doi.org/10.4000/deja.</idno>
              <idno type="URI">https://example.org/ouvrage.</idno>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert r"DOI \href{https://doi.org/10.4000/brut}{10.4000/brut}." in latex
    assert r"DOI \href{https://doi.org/10.4000/deja}{https://doi.org/10.4000/deja}." in latex
    assert r"URI \href{https://example.org/ouvrage}{https://example.org/ouvrage}." in latex
    assert "https://doi.org/https://doi.org" not in latex
    assert ".." not in latex


def test_biblstruct_in_footnote_is_rendered_without_breaking_footnote(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <p>Texte<note>
          <biblStruct>
            <monogr>
              <author><persName><forename>Blaise</forename><surname>Pascal</surname></persName></author>
              <title level="m">Pensées</title>
              <imprint><date>1976</date></imprint>
            </monogr>
          </biblStruct>
        </note>.</p>
        """,
    )

    latex = render_latex(xml_path)

    assert r"\footnote{Blaise Pascal, \textit{Pensées}, 1976.}" in latex
    assert r"\footnote{\begin{PurhBibliography}" not in latex


def test_simple_bibl_rendering_is_not_regressed(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <bibl>Entrée déjà formulée.</bibl>
        </listBibl>
        """,
    )

    book = parse_normalized_tei(xml_path)
    bibliography = next(block for block in book.body_divisions[0].blocks if isinstance(block, BibliographyBlock))
    latex = LatexRenderer().render_book(book)

    assert bibliography.items[0].structured is None
    assert r"\noindent\hangindent=1.5em\hangafter=1 Entrée déjà formulée.\par" in latex


def test_simple_tei_table_is_parsed_to_semantic_model(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <table>
          <head>Tableau de test</head>
          <row>
            <cell role="label">Colonne 1</cell>
            <cell role="label">Colonne 2</cell>
          </row>
          <row>
            <cell>Valeur 1</cell>
            <cell><hi rend="italic">Valeur 2</hi></cell>
          </row>
        </table>
        """,
    )

    book = parse_normalized_tei(xml_path)
    table = book.body_divisions[0].blocks[0]

    assert isinstance(table, TableBlock)
    assert table.caption is not None
    assert paragraph_text(Paragraph(content=table.caption)) == "Tableau de test"
    assert len(table.rows) == 2
    assert [len(row.cells) for row in table.rows] == [2, 2]
    assert table.rows[0].cells[0].role == "label"
    assert any(isinstance(node, Italic) for node in table.rows[1].cells[1].content)


def test_simple_tei_table_is_rendered_to_latex(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <table>
          <head>Tableau de test</head>
          <row>
            <cell role="label">Colonne 1</cell>
            <cell role="label">Colonne 2</cell>
          </row>
          <row>
            <cell>Valeur 1</cell>
            <cell><hi rend="italic">Valeur 2</hi></cell>
          </row>
        </table>
        """,
    )

    latex = render_latex(xml_path)

    assert r"\begin{tabularx}{\linewidth}{XX}" in latex
    assert r"\toprule" in latex
    assert r"\midrule" in latex
    assert r"\bottomrule" in latex
    assert r"\textbf{Colonne 1}" in latex
    assert r"\textbf{Colonne 2}" in latex
    assert "Valeur 1" in latex
    assert r"\textit{Valeur 2}" in latex
    assert "Tableau de test" in latex
    assert "None" not in latex


def test_table_escapes_latex_special_characters(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <table>
          <row>
            <cell role="label">Nom</cell>
            <cell role="label">Valeur</cell>
          </row>
          <row>
            <cell>Racine &amp; Port-Royal</cell>
            <cell>50% mot_cle #1</cell>
          </row>
        </table>
        """,
    )

    latex = render_latex(xml_path)

    assert r"Racine \& Port-Royal" in latex
    assert r"50\%" in latex
    assert r"mot\_cle" in latex
    assert r"\#1" in latex
    assert "Racine & Port-Royal" not in latex
    assert "50% mot_cle #1" not in latex


def test_empty_table_does_not_break_latex_renderer(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<table><head>Table vide</head></table>")

    latex = render_latex(xml_path)

    assert "% Table omise sans lignes: Table vide" in latex
    assert r"\begin{tabularx}" not in latex
    assert "None" not in latex


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


def test_latex_renderer_purh_style_activates_expected_page_profile(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte style PURH.</p>")

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))

    assert r"\documentclass[12pt,twoside,openany]{book}" in latex
    assert "{memoir}" not in latex
    assert r"\usepackage[" in latex
    assert r"]{geometry}" in latex
    assert "paperwidth=155mm" in latex
    assert "paperheight=230mm" in latex
    assert "top=30mm" in latex
    assert "bottom=19mm" in latex
    assert "inner=23mm" in latex
    assert "outer=23mm" in latex
    assert "headheight=14pt" in latex
    assert "headsep=8mm" in latex
    assert "footskip=10mm" in latex
    assert r"\raggedbottom" in latex


def test_latex_renderer_purh_style_activates_running_heads(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte style PURH.</p>")

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))

    assert r"\usepackage[nobottomtitles*]{titlesec}" in latex
    assert r"\usepackage{titletoc}" in latex
    assert r"\usepackage{fancyhdr}" in latex
    assert r"\pagestyle{fancy}" in latex
    assert r"\fancyhead[LE]{\PURHHeaderFont\thepage}" in latex
    assert r"\fancyhead[RE]{\PURHHeaderFont\nouppercase{\PURHBookTitle}}" in latex
    assert r"\fancyhead[LO]{\PURHHeaderFont\nouppercase{\leftmark}}" in latex
    assert r"\fancyhead[RO]{\PURHHeaderFont\thepage}" in latex
    assert r"\renewcommand{\chaptermark}[1]{\markboth{#1}{}}" in latex
    assert r"\fancypagestyle{plain}" in latex


def test_title_page_puts_publisher_at_bottom(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte style PURH.</p>")

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))
    title_page = latex[latex.index(r"\begin{titlepage}"):latex.index(r"\end{titlepage}")]

    assert r"\begin{titlepage}" in title_page
    assert r"\thispagestyle{empty}" in title_page
    assert title_page.index(r"\vfill") < title_page.index("PURH")


def test_table_of_contents_is_at_end(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte style PURH.</p>")

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))

    assert latex.index(r"\chapter{Chapitre PDF}") < latex.index(r"\tableofcontents")
    assert latex.index(r"\tableofcontents") < latex.index(r"\end{document}")
    assert r"\tableofcontents" not in latex[latex.index(r"\frontmatter"):latex.index(r"\mainmatter")]


def test_starred_chapters_reset_running_headers(tmp_path: Path) -> None:
    xml_path = tmp_path / "front.normalized.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title type="main">Livre PDF</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source.</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <front>
      <div type="introduction">
        <head>Introduction</head>
        <p>Texte introduction.</p>
      </div>
    </front>
    <group type="book">
      <group type="chapter" data-page-title="Chapitre principal">
        <body><p>Texte chapitre.</p></body>
      </group>
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))

    chapter_index = latex.index(r"\chapter*{Introduction}")
    mark_index = latex.index(r"\markboth{Introduction}{Introduction}", chapter_index)
    text_index = latex.index("Texte introduction.", chapter_index)
    assert chapter_index < mark_index < text_index


def test_short_running_title_keeps_short_titles() -> None:
    assert _short_running_title("Introduction") == "Introduction"


def test_short_running_title_truncates_without_ending_on_stopword() -> None:
    title = "Aspects ludiques dans l’appareil héraldique des manuscrits de Léon X (1513-1521)"

    short = _short_running_title(title)

    assert short == "Aspects ludiques dans l’appareil héraldique…"
    assert " des…" not in short
    assert " de…" not in short


def test_long_chapter_title_keeps_full_title_but_uses_short_mark(tmp_path: Path) -> None:
    long_title = "Aspects ludiques dans l’appareil héraldique des manuscrits de Léon X (1513-1521)"
    short_title = "Aspects ludiques dans l’appareil héraldique…"
    xml_path = tmp_path / "long-title.normalized.xml"
    xml_path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title type="main">Livre PDF</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source.</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="chapter" data-page-title="{long_title}">
        <body><p>Texte chapitre.</p></body>
      </group>
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))

    assert rf"\chapter{{{long_title}}}" in latex
    assert rf"\markboth{{{short_title}}}{{{short_title}}}" in latex
    assert rf"\addcontentsline{{toc}}{{chapter}}{{{short_title}}}" not in latex


def test_blank_pages_are_empty(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte style PURH.</p>")

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))

    assert r"\usepackage{emptypage}" in latex
    assert r"\thispagestyle{empty}" in latex


def test_latex_renderer_purh_style_defines_editorial_macros(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte style PURH.</p>")

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))

    assert r"\newcommand{\PURHBookTitle}{Livre PDF}" in latex
    assert r"\newcommand{\PURHBookSubtitle}{Sous-titre PDF}" in latex
    assert r"\newcommand{\PURHBookAuthor}{Alice Auteur}" in latex
    assert r"\newcommand{\PURHPublisher}{PURH}" in latex
    assert r"\newcommand{\PURHYear}{2024}" in latex
    assert r"\newcommand{\PURHDOI}{}" in latex
    assert r"\newcommand{\PURHISBN}{}" in latex
    assert r"\title{\PURHBookTitle}" in latex
    assert r"\author{\PURHBookAuthor}" in latex
    assert r"\date{\PURHYear}" in latex


def test_latex_renderer_purh_style_adds_french_typography_settings(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte style PURH.</p>")

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))

    assert r"\usepackage[french]{babel}" in latex
    assert "polyglossia" not in latex
    assert r"\setmainlanguage" not in latex
    assert r"\usepackage{microtype}" in latex
    assert r"\usepackage{csquotes}" in latex
    assert r"\usepackage{indentfirst}" in latex
    assert r"\usepackage[hang,flushmargin]{footmisc}" in latex
    assert r"\captionsetup{" in latex
    assert "labelfont=bf" in latex
    assert r"\clubpenalty=10000" in latex
    assert r"\widowpenalty=10000" in latex
    assert r"\displaywidowpenalty=10000" in latex
    assert r"\emergencystretch=3em" in latex
    assert r"\setlength{\parindent}{5mm}" in latex


def test_latex_renderer_purh_style_does_not_load_heavy_template_dependencies(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte style PURH.</p>")

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))

    forbidden_dependencies = [
        "memoir",
        "polyglossia",
        "minted",
        "svg",
        "tikz",
        "tkz-tab",
        "biblatex",
        "makeidx",
        "listings",
    ]
    for dependency in forbidden_dependencies:
        assert dependency not in latex


def test_latex_renderer_purh_style_keeps_single_used_block_environments(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <div type="blockquote">
          <p>Citation bloc.</p>
          <p>Suite de citation.</p>
        </div>
        <listBibl>
          <head>Bibliographie</head>
          <bibl>Entrée bibliographique.</bibl>
        </listBibl>
        """,
    )

    latex = render_latex_with_options(xml_path, LatexRenderOptions(style="purh"))

    assert r"\newenvironment{PurhBlockQuote}" in latex
    assert r"\newenvironment{PurhBibliography}" in latex
    assert r"\newenvironment{PURHBlockQuote}" not in latex
    assert r"\newenvironment{PURHBibliography}" not in latex
    assert r"\begin{PurhBlockQuote}" in latex
    assert r"\end{PurhBlockQuote}" in latex
    assert r"\begin{PurhBibliography}" in latex
    assert r"\end{PurhBibliography}" in latex
    assert "Citation bloc." in latex
    assert "Entrée bibliographique." in latex


def test_pdf_builder_writes_purh_style_latex_without_compilation(tmp_path: Path) -> None:
    xml_path = write_tei(tmp_path, "<p>Texte style PURH sans compilation.</p>")

    result = PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=False,
    ).build_from_normalized_tei(xml_path, tmp_path / "pdf")
    tex = result.tex_path.read_text(encoding="utf-8")

    assert result.success is True
    assert result.commands == []
    assert result.tex_path.exists()
    assert not result.pdf_path.exists()
    assert r"\documentclass[12pt,twoside,openany]{book}" in tex
    assert r"\pagestyle{fancy}" in tex
    assert r"\usepackage[french]{babel}" in tex
    assert "Texte style PURH sans compilation." in tex


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


def test_inline_ref_target_uses_url_escaping(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <p>Voir <ref target="https://example.org/page_test?a=1&amp;b=2#section_1">le site</ref>.</p>
        """,
    )

    latex = render_latex(xml_path)

    assert r"\href{" in latex
    assert "le site" in latex
    assert r"page\_test" in latex
    assert r"a=1\&b=2" in latex
    assert r"\#section\_1" in latex
    assert "None" not in latex
    assert r"\href{https://example.org/page\_test?a=1\&b=2\#section\_1}{le site}" in latex


def test_escape_url_handles_ampersand_in_bibl_identifier(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <monogr>
              <author>Autrice</author>
              <title level="m">Livre</title>
              <idno type="URI">https://example.org/search?q=test&amp;lang=fr</idno>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    latex = render_latex(xml_path)

    assert r"https://example.org/search?q=test\&lang=fr" in latex
    assert "https://example.org/search?q=test&lang=fr" not in latex
    assert "None" not in latex


def test_pdf_builder_absolutizes_figure_paths_inside_footnotes(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    figure_path = images_dir / "note figure.png"
    figure_path.write_bytes(b"fake-png")
    xml_path = write_tei(
        tmp_path,
        """
        <p>Texte<note>
          <figure>
            <graphic url="images/note figure.png"/>
            <head>Figure en note</head>
          </figure>
        </note>.</p>
        """,
    )

    result = PdfBuilder(compile_pdf=False).build_from_normalized_tei(xml_path, tmp_path / "pdf")
    tex = result.tex_path.read_text(encoding="utf-8")

    assert result.success is True
    assert r"\includegraphics" in tex
    assert r"\detokenize{" in tex
    assert figure_path.resolve().as_posix() in tex
    assert "Image absente ou non fournie" not in tex
    assert not any("Image introuvable" in w for w in result.warnings)


def test_biblstruct_duplicate_doi_identifiers_are_deduplicated(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <monogr>
              <author>Autrice</author>
              <title level="m">Livre avec DOI</title>
              <idno type="DOI">10.4000/foo</idno>
              <ref type="DOI" target="https://doi.org/10.4000/foo">https://doi.org/10.4000/foo</ref>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )

    book = parse_normalized_tei(xml_path)
    item = next(
        block for block in book.body_divisions[0].blocks if isinstance(block, BibliographyBlock)
    ).items[0]
    latex = LatexRenderer().render_book(book)

    assert item.structured is not None
    assert len([i for i in item.structured.identifiers if i.type == "DOI"]) == 1
    # Un seul lien DOI rendu (la valeur apparaît deux fois dans \href{url}{label},
    # donc on compte les occurrences du préfixe de rendu)
    assert latex.count(r"DOI \href{") == 1
    assert "https://doi.org/https://doi.org" not in latex
    assert "None" not in latex


def test_table_with_merged_cells_emits_latex_warning_comment(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <table>
          <row>
            <cell role="label" cols="2">En-tête fusionnée</cell>
          </row>
          <row>
            <cell>A</cell>
            <cell>B</cell>
          </row>
        </table>
        """,
    )

    latex = render_latex(xml_path)

    assert "AVERTISSEMENT Impressions" in latex
    assert "cols/rows ignorés" in latex
    assert r"\begin{tabularx}" in latex
    assert "En-tête fusionnée" in latex
    assert "None" not in latex


def test_simple_tei_table_without_merged_cells_has_no_fusion_warning(tmp_path: Path) -> None:
    xml_path = write_tei(
        tmp_path,
        """
        <table>
          <row>
            <cell role="label">Colonne 1</cell>
            <cell role="label">Colonne 2</cell>
          </row>
          <row>
            <cell>Valeur 1</cell>
            <cell>Valeur 2</cell>
          </row>
        </table>
        """,
    )

    latex = render_latex(xml_path)

    assert "AVERTISSEMENT Impressions" not in latex
    assert r"\begin{tabularx}" in latex
    assert "None" not in latex
