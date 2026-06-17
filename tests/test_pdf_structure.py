from __future__ import annotations

import re
from pathlib import Path

from lxml import etree

from purh_site.latex_renderer import LatexRenderer, LatexRenderOptions
from purh_site.semantic_model import Division
from purh_site.site_structure import NavItem, PageDef, SiteStructureBuilder
from purh_site.tei_to_model import parse_normalized_tei


def write_structure_tei(
    tmp_path: Path,
    *,
    groups: str,
    front: str = "",
    back: str = "",
) -> Path:
    xml_path = tmp_path / "book.normalized.xml"
    xml_path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type="main">Livre structure</title>
        <author><persName><forename>Alice</forename><surname>Auteur</surname></persName></author>
      </titleStmt>
      <publicationStmt>
        <publisher>PURH</publisher>
        <date type="publishing" when="2024">2024</date>
      </publicationStmt>
      <sourceDesc><p>Source de test.</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    {front}
    <group type="book">
      {groups}
    </group>
    {back}
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    return xml_path


def chapter_group(xml_id: str, title: str, body_text: str = "Texte.") -> str:
    return f"""
      <group xml:id="{xml_id}" type="chapter" data-page-title="{title}">
        <body>
          <div type="section1">
            <head>{title}</head>
            <p>{body_text}</p>
          </div>
        </body>
      </group>
    """


def site_pages(xml_path: Path) -> list[PageDef]:
    tree = etree.parse(str(xml_path))
    _, pages, _ = SiteStructureBuilder().build(tree)
    return pages


def site_nav_titles(xml_path: Path) -> list[str]:
    tree = etree.parse(str(xml_path))
    _, _, nav = SiteStructureBuilder().build(tree)
    return flatten_nav_titles(nav)


def flatten_nav_titles(items: list[NavItem]) -> list[str]:
    titles: list[str] = []
    for item in items:
        titles.append(item.title)
        titles.extend(flatten_nav_titles(item.children))
    return titles


def body_division_titles(divisions: list[Division]) -> list[str]:
    return [division.title or "" for division in divisions]


def latex_headings(latex: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"\\(part\*?|chapter\*?|section\*?)\{([^{}]+)\}")
    return [(match.group(1), match.group(2)) for match in pattern.finditer(latex)]


def latex_heading_titles(latex: str, commands: set[str]) -> list[str]:
    return [title for command, title in latex_headings(latex) if command in commands]


def test_pdf_structure_matches_site_order_for_two_simple_chapters(tmp_path: Path) -> None:
    xml_path = write_structure_tei(
        tmp_path,
        groups=chapter_group("chapitre-1", "Chapitre 1", "Texte 1.")
        + chapter_group("chapitre-2", "Chapitre 2", "Texte 2."),
    )

    book = parse_normalized_tei(xml_path)
    latex = LatexRenderer().render_book(book)

    assert [page.title for page in site_pages(xml_path)] == ["Chapitre 1", "Chapitre 2"]
    assert body_division_titles(book.body_divisions) == ["Chapitre 1", "Chapitre 2"]
    assert latex_heading_titles(latex, {"chapter"}) == ["Chapitre 1", "Chapitre 2"]


def test_pdf_structure_keeps_part_before_nested_chapters(tmp_path: Path) -> None:
    xml_path = write_structure_tei(
        tmp_path,
        groups=f"""
        <group xml:id="partie-1" type="part" data-page-title="Première partie">
          {chapter_group("chapitre-1", "Chapitre 1", "Texte 1.")}
          {chapter_group("chapitre-2", "Chapitre 2", "Texte 2.")}
        </group>
        """,
    )

    book = parse_normalized_tei(xml_path)
    latex = LatexRenderer().render_book(book)

    assert site_nav_titles(xml_path) == ["Première partie", "Chapitre 1", "Chapitre 2"]
    assert [page.title for page in site_pages(xml_path)] == ["Chapitre 1", "Chapitre 2"]
    assert body_division_titles(book.body_divisions) == ["Première partie", "Chapitre 1", "Chapitre 2"]
    assert [
        item for item in latex_headings(latex) if item[0] in {"part*", "chapter"}
    ] == [
        ("part*", "Première partie"),
        ("chapter", "Chapitre 1"),
        ("chapter", "Chapitre 2"),
    ]


def test_pdf_structure_renders_front_divisions_before_mainmatter(tmp_path: Path) -> None:
    xml_path = write_structure_tei(
        tmp_path,
        front="""
        <front>
          <div type="preface"><head>Préface</head><p>Texte préface.</p></div>
          <div type="introduction"><head>Avant-propos</head><p>Texte avant-propos.</p></div>
        </front>
        """,
        groups=chapter_group("chapitre-1", "Chapitre 1"),
    )

    book = parse_normalized_tei(xml_path)
    latex = LatexRenderer().render_book(book)

    assert [division.title for division in book.front_divisions] == ["Préface", "Avant-propos"]
    assert body_division_titles(book.body_divisions) == ["Chapitre 1"]
    assert latex.index(r"\chapter*{Préface}") < latex.index(r"\mainmatter")
    assert latex.index(r"\chapter*{Avant-propos}") < latex.index(r"\mainmatter")
    assert latex.index(r"\mainmatter") < latex.index(r"\chapter{Chapitre 1}")


def test_pdf_structure_renders_back_divisions_after_body(tmp_path: Path) -> None:
    xml_path = write_structure_tei(
        tmp_path,
        groups=chapter_group("chapitre-1", "Chapitre 1"),
        back="""
        <back>
          <div type="bibliography"><head>Bibliographie</head><p>Bibliographie simple.</p></div>
          <div type="appendix"><head>Annexe</head><p>Texte annexe.</p></div>
        </back>
        """,
    )

    book = parse_normalized_tei(xml_path)
    latex = LatexRenderer().render_book(book)

    assert body_division_titles(book.body_divisions) == ["Chapitre 1"]
    assert [division.title for division in book.back_divisions] == ["Bibliographie", "Annexe"]
    assert latex.index(r"\chapter{Chapitre 1}") < latex.index(r"\backmatter")
    assert latex.index(r"\backmatter") < latex.index(r"\chapter*{Bibliographie}")
    assert latex.index(r"\chapter*{Bibliographie}") < latex.index(r"\chapter{Annexe}")


def test_pdf_structure_keeps_local_contribution_title_and_authors(tmp_path: Path) -> None:
    xml_path = write_structure_tei(
        tmp_path,
        groups="""
        <group xml:id="contribution-1" type="chapter" data-page-title="Contribution locale" data-page-authors="Alice Locale@@Université||Bob Local">
          <body>
            <div type="section1">
              <head>Titre interne ignoré</head>
              <p>Texte contribution.</p>
            </div>
          </body>
        </group>
        """,
    )

    book = parse_normalized_tei(xml_path)
    page = site_pages(xml_path)[0]
    division = book.body_divisions[0]

    assert page.title == "Contribution locale"
    assert page.authors == ["Alice Locale", "Bob Local"]
    assert division.title == "Contribution locale"
    assert [contributor.full_name for contributor in division.contributors] == ["Alice Locale", "Bob Local"]


def test_pdf_structure_uses_site_title_fallback_without_none_in_latex(tmp_path: Path) -> None:
    xml_path = write_structure_tei(
        tmp_path,
        groups="""
        <group xml:id="fallback" type="chapter">
          <body>
            <div type="section1">
              <head>Titre depuis la structure</head>
              <p>Texte fallback.</p>
            </div>
          </body>
        </group>
        """,
    )

    book = parse_normalized_tei(xml_path)
    latex = LatexRenderer().render_book(book)

    assert [page.title for page in site_pages(xml_path)] == ["Titre depuis la structure"]
    assert body_division_titles(book.body_divisions) == ["Titre depuis la structure"]
    assert r"\chapter{Titre depuis la structure}" in latex
    assert "Sans titre" not in latex
    assert "None" not in latex


def test_pdf_structure_order_is_identical_with_purh_style(tmp_path: Path) -> None:
    xml_path = write_structure_tei(
        tmp_path,
        groups=f"""
        <group xml:id="partie-1" type="part" data-page-title="Première partie">
          {chapter_group("chapitre-1", "Chapitre 1", "Texte 1.")}
          {chapter_group("chapitre-2", "Chapitre 2", "Texte 2.")}
        </group>
        """,
    )

    book = parse_normalized_tei(xml_path)
    default_latex = LatexRenderer().render_book(book)
    purh_latex = LatexRenderer(options=LatexRenderOptions(style="purh")).render_book(book)

    expected_order = ["Première partie", "Chapitre 1", "Chapitre 2"]
    assert body_division_titles(book.body_divisions) == expected_order
    assert latex_heading_titles(default_latex, {"part*", "chapter"}) == expected_order
    assert latex_heading_titles(purh_latex, {"part*", "chapter"}) == expected_order
