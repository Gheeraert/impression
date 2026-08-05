from __future__ import annotations

from pathlib import Path

from lxml import html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder


def build_structure_site(tmp_path: Path, groups: str) -> Path:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type='main'>Livre structure</title>
        <editor>Directeur, Volume</editor>
      </titleStmt>
      <publicationStmt><publisher>PURH</publisher><date when='2024'>2024</date></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      {groups}
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))
    return result.output_dir


def chapter_group(xml_id: str, title: str, body: str = "<p>Texte.</p>", **attrs: str) -> str:
    extra_attrs = " ".join(f'{name.replace("_", "-")}="{value}"' for name, value in attrs.items())
    if extra_attrs:
        extra_attrs = " " + extra_attrs
    return f"""
    <group xml:id="{xml_id}" type="chapter" data-page-title="{title}"{extra_attrs}>
      <body>
        <div type="section1">
          <head>{title}</head>
          {body}
        </div>
      </body>
    </group>
    """


def parse_page(path: Path) -> html.HtmlElement:
    return html.fromstring(path.read_text(encoding="utf-8"))


def content_pages(output_dir: Path) -> list[Path]:
    return sorted(path for path in output_dir.glob("*.html") if path.name != "index.html")


def visible_text(element: html.HtmlElement) -> str:
    return " ".join(element.text_content().split())


def nav_links(doc: html.HtmlElement) -> list[tuple[str, str]]:
    return [(link.get("href") or "", visible_text(link)) for link in doc.xpath("//nav[contains(@class, 'sidebar-nav')]//a")]


def toc_links(doc: html.HtmlElement) -> list[tuple[str, str]]:
    return [
        (link.get("href") or "", visible_text(link))
        for link in doc.xpath("//section[contains(@class, 'home-panel') and .//h2[normalize-space(.)='Sommaire']]//a")
    ]


def test_simple_book_generates_ordered_pages_toc_sidebar_and_pager(tmp_path: Path) -> None:
    output_dir = build_structure_site(
        tmp_path,
        chapter_group("chapitre-1", "Chapitre 1") + chapter_group("chapitre-2", "Chapitre 2"),
    )
    pages = content_pages(output_dir)

    assert [page.name for page in pages] == ["01-chapitre-1.html", "02-chapitre-2.html"]

    index_doc = parse_page(output_dir / "index.html")
    assert toc_links(index_doc) == [("01-chapitre-1.html", "Chapitre 1"), ("02-chapitre-2.html", "Chapitre 2")]

    first_doc = parse_page(pages[0])
    second_doc = parse_page(pages[1])
    first_sidebar = nav_links(first_doc)
    assert ("01-chapitre-1.html", "Chapitre 1") in first_sidebar
    assert ("02-chapitre-2.html", "Chapitre 2") in first_sidebar
    assert first_doc.xpath("//nav[contains(@class, 'pager')]//a[contains(@class, 'pager-link--next')]/@href") == ["02-chapitre-2.html"]
    assert first_doc.xpath("//nav[contains(@class, 'pager')]//a[not(contains(@class, 'pager-link--next'))]") == []
    assert second_doc.xpath("//nav[contains(@class, 'pager')]//a[not(contains(@class, 'pager-link--next'))]/@href") == ["01-chapitre-1.html"]
    assert second_doc.xpath("//nav[contains(@class, 'pager')]//a[contains(@class, 'pager-link--next')]") == []


def test_directors_override_corrects_misattributed_pbd_author_on_the_homepage(tmp_path: Path) -> None:
    """Constaté sur *Dissimuler pour mieux régner* (2026-08-06) : le même
    TEI <author role="pbd"> alimente à la fois la page de titre LaTeX/PDF
    (reversible_integration.run_reversible_export_for_file) et cette page
    d'accueil HTML (SiteStructureBuilder._extract_site_meta) — un premier
    correctif n'avait câblé directors_override QUE pour le PDF, laissant le
    HTML afficher le même nom erroné ("Anaïs Lebreton" deux fois, faute
    d'éditrices scientifiques correctement balisées dans le TEI source)."""
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type='main'>Dissimuler pour mieux regner</title>
        <author role="pbd">Lebreton, Anais</author>
        <author role="pbd">Lebreton, Anais</author>
      </titleStmt>
      <publicationStmt><publisher>PURH</publisher><date when='2024'>2024</date></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group xml:id="intro" type="introduction" data-page-title="Introduction">
        <body><div type="section1"><head>Introduction</head><p>Texte.</p></div></body>
      </group>
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(
            output_dir=tmp_path / "site",
            directors_override="Floriane Daguise et Florence Fix",
        ),
    )
    index_doc = parse_page(result.output_dir / "index.html")
    index_text = index_doc.xpath("string(//body)")
    assert "Floriane Daguise" in index_text
    assert "Florence Fix" in index_text
    assert "Lebreton" not in index_text


def test_part_hierarchy_is_preserved_in_toc_sidebar_and_header_chain(tmp_path: Path) -> None:
    output_dir = build_structure_site(
        tmp_path,
        """
        <group xml:id="partie-1" type="part" data-page-title="Premiere partie">
          <group xml:id="chapitre-1" type="chapter" data-page-title="Chapitre 1">
            <body><div type="section1"><head>Chapitre 1</head><p>Texte.</p></div></body>
          </group>
          <group xml:id="chapitre-2" type="chapter" data-page-title="Chapitre 2">
            <body><div type="section1"><head>Chapitre 2</head><p>Texte.</p></div></body>
          </group>
        </group>
        """,
    )
    pages = content_pages(output_dir)
    index_doc = parse_page(output_dir / "index.html")
    chapter_doc = parse_page(pages[0])

    assert [page.name for page in pages] == ["01-chapitre-1.html", "02-chapitre-2.html"]
    assert index_doc.xpath("//li[contains(@class, 'has-children')]/span[contains(@class, 'nav-label') and normalize-space(.)='Premiere partie']")
    assert index_doc.xpath("//li[contains(@class, 'has-children')]//a[@href='01-chapitre-1.html' and normalize-space(.)='Chapitre 1']")
    assert chapter_doc.xpath("string(//header[contains(@class, 'page-header')]//p[contains(@class, 'eyebrow')])") == "Premiere partie"


def test_article_and_authored_chapter_pages_keep_contribution_citation_label(tmp_path: Path) -> None:
    output_dir = build_structure_site(
        tmp_path,
        """
        <group xml:id="article-1" type="article" data-page-title="Article explicite">
          <body><div type="section1"><head>Article explicite</head><p>Texte.</p></div></body>
        </group>
        <group xml:id="contribution-1" type="chapter" data-page-title="Contribution" data-page-authors="Auteur, Alice">
          <body><div type="section1"><head>Contribution</head><p>Texte.</p></div></body>
        </group>
        """,
    )
    pages = content_pages(output_dir)
    first_doc = parse_page(pages[0])
    second_doc = parse_page(pages[1])

    assert [page.name for page in pages] == ["01-article-explicite.html", "02-contribution.html"]
    assert "Pour citer cette contribution" in first_doc.xpath("string(//section[contains(@class, 'credit-box')])")
    assert "Pour citer cette contribution" in second_doc.xpath("string(//section[contains(@class, 'credit-box')])")
    assert second_doc.xpath("string(//header[contains(@class, 'page-header')]//div[contains(@class, 'author-name')])") == "Auteur, Alice"


def test_page_title_subtitle_html_title_and_header_are_rendered(tmp_path: Path) -> None:
    output_dir = build_structure_site(
        tmp_path,
        chapter_group("chapitre", "Titre principal", data_page_subtitle="Sous-titre de page"),
    )
    page_doc = parse_page(content_pages(output_dir)[0])

    assert page_doc.xpath("string(//title)") == "Titre principal — Livre structure"
    assert page_doc.xpath("string(//header[contains(@class, 'page-header')]//h1)") == "Titre principal"
    assert page_doc.xpath("string(//header[contains(@class, 'page-header')]//p[contains(@class, 'subtitle')])") == "Sous-titre de page"
    assert "None" not in page_doc.xpath("string(//header[contains(@class, 'page-header')])")


def test_sidebar_marks_only_current_page(tmp_path: Path) -> None:
    output_dir = build_structure_site(
        tmp_path,
        chapter_group("chapitre-1", "Chapitre 1")
        + chapter_group("chapitre-2", "Chapitre 2")
        + chapter_group("chapitre-3", "Chapitre 3"),
    )
    second_doc = parse_page(content_pages(output_dir)[1])
    current_links = second_doc.xpath("//nav[contains(@class, 'sidebar-nav')]//li[contains(@class, 'is-current')]/a")

    assert [(link.get("href"), visible_text(link)) for link in current_links] == [("02-chapitre-2.html", "Chapitre 2")]
    assert len(second_doc.xpath("//nav[contains(@class, 'sidebar-nav')]//li[contains(@class, 'is-current')]")) == 1


def test_prev_next_links_for_three_pages_are_stable_and_non_empty(tmp_path: Path) -> None:
    output_dir = build_structure_site(
        tmp_path,
        chapter_group("chapitre-1", "Chapitre 1")
        + chapter_group("chapitre-2", "Chapitre 2")
        + chapter_group("chapitre-3", "Chapitre 3"),
    )
    first_doc, second_doc, third_doc = [parse_page(path) for path in content_pages(output_dir)]

    assert first_doc.xpath("//nav[contains(@class, 'pager')]//a/@href") == ["02-chapitre-2.html"]
    assert second_doc.xpath("//nav[contains(@class, 'pager')]//a/@href") == ["01-chapitre-1.html", "03-chapitre-3.html"]
    assert third_doc.xpath("//nav[contains(@class, 'pager')]//a/@href") == ["02-chapitre-2.html"]
    assert not first_doc.xpath("//nav[contains(@class, 'pager')]//a[@href='']")
    assert not second_doc.xpath("//nav[contains(@class, 'pager')]//a[@href='']")
    assert not third_doc.xpath("//nav[contains(@class, 'pager')]//a[@href='']")


def test_duplicate_titles_get_distinct_slugs_without_overwriting(tmp_path: Path) -> None:
    output_dir = build_structure_site(
        tmp_path,
        chapter_group("intro-1", "Introduction") + chapter_group("intro-2", "Introduction"),
    )
    pages = content_pages(output_dir)

    assert [page.name for page in pages] == ["01-introduction.html", "02-introduction-2.html"]
    assert all(page.exists() for page in pages)


def test_page_without_data_title_uses_head_fallback(tmp_path: Path) -> None:
    output_dir = build_structure_site(
        tmp_path,
        """
        <group xml:id="fallback" type="chapter">
          <body>
            <div type="section1">
              <head>Titre depuis head</head>
              <p>Texte.</p>
            </div>
          </body>
        </group>
        """,
    )
    page = content_pages(output_dir)[0]
    page_doc = parse_page(page)

    assert page.name == "01-titre-depuis-head.html"
    assert page_doc.xpath("string(//header[contains(@class, 'page-header')]//h1)") == "Titre depuis head"
    assert ("", "") not in nav_links(page_doc)


def test_home_toc_links_are_ordered_hierarchical_and_non_empty(tmp_path: Path) -> None:
    output_dir = build_structure_site(
        tmp_path,
        """
        <group xml:id="partie-1" type="part" data-page-title="Partie">
          <group xml:id="chapitre-1" type="chapter" data-page-title="Chapitre 1">
            <body><div type="section1"><head>Chapitre 1</head><p>Texte.</p></div></body>
          </group>
        </group>
        <group xml:id="chapitre-2" type="chapter" data-page-title="Chapitre 2">
          <body><div type="section1"><head>Chapitre 2</head><p>Texte.</p></div></body>
        </group>
        """,
    )
    index_doc = parse_page(output_dir / "index.html")
    links = toc_links(index_doc)

    assert links == [("01-chapitre-1.html", "Chapitre 1"), ("02-chapitre-2.html", "Chapitre 2")]
    assert index_doc.xpath("//section[contains(@class, 'home-panel')]//span[contains(@class, 'nav-label') and normalize-space(.)='Partie']")
    assert not index_doc.xpath("//section[contains(@class, 'home-panel')]//a[@href='']")
