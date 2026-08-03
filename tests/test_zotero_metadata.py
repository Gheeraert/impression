from __future__ import annotations

from pathlib import Path

from lxml import html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder


def build_metadata_site(tmp_path: Path, title_stmt: str, publication_stmt: str, body: str, series_stmt: str = "") -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>{title_stmt}</titleStmt>
      <publicationStmt>{publication_stmt}</publicationStmt>
      {series_stmt}
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      {body}
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))
    return result.output_dir


def parse_page(path: Path) -> html.HtmlElement:
    return html.fromstring(path.read_text(encoding="utf-8"))


def meta_contents(doc: html.HtmlElement, name: str) -> list[str]:
    return doc.xpath(f"//meta[@name={name!r}]/@content")


def meta_content(doc: html.HtmlElement, name: str) -> str:
    values = meta_contents(doc, name)
    return values[0] if values else ""


def content_pages(output_dir: Path) -> list[Path]:
    return sorted(path for path in output_dir.glob("*.html") if path.name != "index.html")


FULL_TITLE_STMT = """
<title type='main'>Livre savant</title>
<title type='sub'>Sous-titre critique</title>
<editor>Directeur, Claire</editor>
<editor>Directeur, Marc</editor>
"""

FULL_PUBLICATION_STMT = """
<publisher>PURH</publisher>
<date type='publishing' when='2024'>2024</date>
<ab type='book'>
  <idno type='ISBN'>979-10-240-1234-5</idno>
  <idno type='ISSN'>2427-0000</idno>
</ab>
<idno type='DOI'>10.4000/books.purh.9999</idno>
<ab type='digital_online'>
  <ref type='site' target='https://example.org/livre/'/>
</ab>
"""

FULL_SERIES_STMT = """
<seriesStmt>
  <title level='s'>Collection essais</title>
  <biblScope unit='volume'>42</biblScope>
  <idno type='ISSN'>2600-1111</idno>
</seriesStmt>
"""

ONE_CHAPTER = """
<group xml:id='chapitre' type='chapter' data-page-title='Chapitre un' data-page-authors='Auteur, Alice'>
  <body>
    <div type='section1'>
      <head>Chapitre un</head>
      <p>Texte.</p>
    </div>
  </body>
</group>
"""

ONE_CHAPTER_WITHOUT_AUTHOR = """
<group xml:id='chapitre' type='chapter' data-page-title='Chapitre sans auteur'>
  <body>
    <div type='section1'>
      <head>Chapitre sans auteur</head>
      <p>Texte.</p>
    </div>
  </body>
</group>
"""


def test_home_page_exposes_book_zotero_and_dublin_core_metadata(tmp_path: Path) -> None:
    output_dir = build_metadata_site(tmp_path, FULL_TITLE_STMT, FULL_PUBLICATION_STMT, ONE_CHAPTER, FULL_SERIES_STMT)
    doc = parse_page(output_dir / "index.html")

    assert doc.xpath("string(//title)") == "Livre savant"
    assert meta_content(doc, "citation_title") == "Livre savant. Sous-titre critique"
    assert meta_contents(doc, "citation_editor") == ["Directeur, Claire", "Directeur, Marc"]
    assert meta_content(doc, "citation_publisher") == "PURH"
    assert meta_content(doc, "citation_publication_date") == "2024"
    assert meta_content(doc, "citation_isbn") == "979-10-240-1234-5"
    assert meta_content(doc, "citation_issn") == "2427-0000"
    assert meta_content(doc, "citation_series_title") == "Collection essais"
    assert meta_content(doc, "citation_series_number") == "42"
    assert meta_content(doc, "citation_doi") == "10.4000/books.purh.9999"
    assert meta_content(doc, "citation_language") == "fr"
    assert meta_content(doc, "DC.Title") == "Livre savant. Sous-titre critique"
    assert meta_content(doc, "DC.Type") == "book"
    assert meta_content(doc, "DC.Publisher") == "PURH"
    assert meta_content(doc, "DC.Date") == "2024"
    assert meta_content(doc, "DC.Identifier") == "https://example.org/livre/index.html"
    assert meta_contents(doc, "DC.Contributor") == ["Directeur, Claire", "Directeur, Marc"]


def test_chapter_page_exposes_section_metadata_and_volume_relation(tmp_path: Path) -> None:
    output_dir = build_metadata_site(tmp_path, FULL_TITLE_STMT, FULL_PUBLICATION_STMT, ONE_CHAPTER, FULL_SERIES_STMT)
    chapter_path = content_pages(output_dir)[0]
    doc = parse_page(chapter_path)

    assert meta_content(doc, "citation_title") == "Chapitre un"
    assert meta_content(doc, "citation_book_title") == "Livre savant. Sous-titre critique"
    assert meta_contents(doc, "citation_author") == ["Auteur, Alice"]
    assert meta_contents(doc, "citation_editor") == ["Directeur, Claire", "Directeur, Marc"]
    assert meta_content(doc, "citation_publisher") == "PURH"
    assert meta_content(doc, "citation_publication_date") == "2024"
    assert meta_content(doc, "citation_isbn") == "979-10-240-1234-5"
    assert meta_content(doc, "citation_language") == "fr"
    assert meta_content(doc, "DC.Type") == "bookSection"
    assert meta_content(doc, "DC.Relation") == "Livre savant. Sous-titre critique"
    assert meta_content(doc, "DC.Identifier") == f"https://example.org/livre/{chapter_path.name}"


def test_volume_creator_role_controls_author_or_editor_metadata(tmp_path: Path) -> None:
    author_output = build_metadata_site(
        tmp_path / "authors",
        "<title type='main'>Livre auteur</title><author>Auteur, Volume</author>",
        "<publisher>PURH</publisher><date when='2024'>2024</date>",
        ONE_CHAPTER,
    )
    editor_output = build_metadata_site(
        tmp_path / "editors",
        "<title type='main'>Livre dirige</title><editor>Directeur, Volume</editor>",
        "<publisher>PURH</publisher><date when='2024'>2024</date>",
        ONE_CHAPTER,
    )

    author_home = parse_page(author_output / "index.html")
    editor_home = parse_page(editor_output / "index.html")
    author_chapter = parse_page(content_pages(author_output)[0])

    assert meta_contents(author_home, "citation_author") == ["Auteur, Volume"]
    assert meta_contents(author_home, "citation_editor") == []
    assert meta_contents(editor_home, "citation_editor") == ["Directeur, Volume"]
    assert meta_contents(editor_home, "citation_author") == []
    assert meta_contents(author_chapter, "citation_editor") == []


def test_edited_volume_chapter_without_own_author_uses_editors_not_authors(tmp_path: Path) -> None:
    output_dir = build_metadata_site(
        tmp_path,
        "<title type='main'>Volume dirige</title><editor>Directeur, Volume</editor>",
        "<publisher>PURH</publisher><date when='2024'>2024</date>",
        ONE_CHAPTER_WITHOUT_AUTHOR,
    )
    chapter_doc = parse_page(content_pages(output_dir)[0])

    assert meta_contents(chapter_doc, "citation_author") == []
    assert meta_contents(chapter_doc, "citation_editor") == ["Directeur, Volume"]
    assert meta_contents(chapter_doc, "DC.Creator") == []
    assert meta_contents(chapter_doc, "DC.Contributor") == ["Directeur, Volume"]


def test_authored_monograph_chapter_without_own_author_uses_volume_author(tmp_path: Path) -> None:
    output_dir = build_metadata_site(
        tmp_path,
        "<title type='main'>Monographie</title><author>Auteur, Volume</author>",
        "<publisher>PURH</publisher><date when='2024'>2024</date>",
        ONE_CHAPTER_WITHOUT_AUTHOR,
    )
    chapter_doc = parse_page(content_pages(output_dir)[0])

    assert meta_contents(chapter_doc, "citation_author") == ["Auteur, Volume"]
    assert meta_contents(chapter_doc, "citation_editor") == []
    assert meta_contents(chapter_doc, "DC.Creator") == ["Auteur, Volume"]


def test_credit_block_for_edited_volume_chapter_without_author_does_not_use_editor_as_author(tmp_path: Path) -> None:
    output_dir = build_metadata_site(
        tmp_path,
        "<title type='main'>Volume dirige</title><editor>Directeur, Volume</editor>",
        "<publisher>PURH</publisher><date when='2024'>2024</date>",
        ONE_CHAPTER_WITHOUT_AUTHOR,
    )
    chapter_doc = parse_page(content_pages(output_dir)[0])
    credit_box = chapter_doc.xpath("//section[contains(@class, 'credit-box')]")[0]
    credit_text = " ".join(credit_box.text_content().split())
    suggested = " ".join(credit_box.xpath("string(.//p[contains(@class, 'credit-citation')])").split())

    assert "Chapitre sans auteur" in credit_text
    assert "Volume dirige" in credit_text
    assert "Directeur, Volume" in credit_text
    assert not credit_box.xpath(".//p[contains(@class, 'credit-names') and contains(., 'Directeur, Volume')]")
    assert not suggested.startswith("Reference suggeree : Directeur, Volume")


def test_credit_block_for_authored_monograph_chapter_without_author_uses_volume_author(tmp_path: Path) -> None:
    output_dir = build_metadata_site(
        tmp_path,
        "<title type='main'>Monographie</title><author>Auteur, Volume</author>",
        "<publisher>PURH</publisher><date when='2024'>2024</date>",
        ONE_CHAPTER_WITHOUT_AUTHOR,
    )
    chapter_doc = parse_page(content_pages(output_dir)[0])
    credit_box = chapter_doc.xpath("//section[contains(@class, 'credit-box')]")[0]
    suggested = " ".join(credit_box.xpath("string(.//p[contains(@class, 'credit-citation')])").split())

    assert credit_box.xpath(".//p[contains(@class, 'credit-names') and contains(., 'Auteur, Volume')]")
    assert suggested.startswith("Référence suggérée : Auteur, Volume")


def test_credit_block_for_authored_chapter_in_edited_volume_keeps_author_and_editor(tmp_path: Path) -> None:
    output_dir = build_metadata_site(
        tmp_path,
        "<title type='main'>Volume dirige</title><editor>Directeur, Volume</editor>",
        "<publisher>PURH</publisher><date when='2024'>2024</date>",
        ONE_CHAPTER,
    )
    chapter_doc = parse_page(content_pages(output_dir)[0])
    credit_box = chapter_doc.xpath("//section[contains(@class, 'credit-box')]")[0]
    credit_text = " ".join(credit_box.text_content().split())

    assert credit_box.xpath(".//p[contains(@class, 'credit-names') and contains(., 'Auteur, Alice')]")
    assert "Directeur, Volume" in credit_text


def test_doi_url_is_normalized_in_visible_credit_block_without_double_prefix(tmp_path: Path) -> None:
    raw_output = build_metadata_site(
        tmp_path / "raw",
        "<title type='main'>Livre DOI brut</title><editor>Directeur, Volume</editor>",
        "<publisher>PURH</publisher><date when='2024'>2024</date><idno type='DOI'>10.4000/books.purh.1234</idno>",
        ONE_CHAPTER,
    )
    url_output = build_metadata_site(
        tmp_path / "url",
        "<title type='main'>Livre DOI URL</title><editor>Directeur, Volume</editor>",
        "<publisher>PURH</publisher><date when='2024'>2024</date><idno type='DOI'>https://doi.org/10.4000/books.purh.1234</idno>",
        ONE_CHAPTER,
    )

    raw_chapter = parse_page(content_pages(raw_output)[0])
    url_chapter = parse_page(content_pages(url_output)[0])

    assert meta_content(parse_page(raw_output / "index.html"), "citation_doi") == "10.4000/books.purh.1234"
    assert raw_chapter.xpath("//section[contains(@class, 'credit-box')]//a[@href='https://doi.org/10.4000/books.purh.1234']")
    assert url_chapter.xpath("//section[contains(@class, 'credit-box')]//a[@href='https://doi.org/10.4000/books.purh.1234']")
    assert not url_chapter.xpath("//section[contains(@class, 'credit-box')]//a[contains(@href, 'https://doi.org/https://doi.org/')]")


def test_public_page_urls_are_built_from_site_url_variants(tmp_path: Path) -> None:
    for dirname, site_url in [
        ("slash", "https://example.org/livre/"),
        ("noslash", "https://example.org/livre"),
        ("index", "https://example.org/livre/index.html"),
    ]:
        output_dir = build_metadata_site(
            tmp_path / dirname,
            "<title type='main'>Livre URL</title><editor>Directeur, Volume</editor>",
            f"<publisher>PURH</publisher><date when='2024'>2024</date><ab type='digital_online'><ref type='site' target='{site_url}'/></ab>",
            ONE_CHAPTER,
        )
        chapter_path = content_pages(output_dir)[0]
        chapter_doc = parse_page(chapter_path)

        assert meta_content(chapter_doc, "DC.Identifier") == f"https://example.org/livre/{chapter_path.name}"
        assert f"https://example.org/livre/{chapter_path.name}" in chapter_doc.xpath("string(//section[contains(@class, 'credit-box')])")


def test_credit_block_contains_core_citation_information(tmp_path: Path) -> None:
    output_dir = build_metadata_site(tmp_path, FULL_TITLE_STMT, FULL_PUBLICATION_STMT, ONE_CHAPTER, FULL_SERIES_STMT)
    chapter_doc = parse_page(content_pages(output_dir)[0])
    credit_text = " ".join(chapter_doc.xpath("string(//section[contains(@class, 'credit-box')])").split())

    assert "Auteur, Alice" in credit_text
    assert "Chapitre un" in credit_text
    assert "Livre savant" in credit_text
    assert "PURH" in credit_text
    assert "2024" in credit_text
    assert "https://example.org/livre/01-chapitre-un.html" in credit_text
    assert "10.4000/books.purh.9999" in credit_text
    assert "Date de consultation" in credit_text


def test_chapter_page_gets_a_meta_description_excerpt_from_its_own_content(tmp_path: Path) -> None:
    chapter = """
<group xml:id='chapitre' type='chapter' data-page-title='Chapitre un' data-page-authors='Auteur, Alice'>
  <body>
    <div type='section1'>
      <head>Chapitre un</head>
      <p>Ce chapitre etudie precisement la question posee en introduction, avec un luxe de details.</p>
    </div>
  </body>
</group>
"""
    output_dir = build_metadata_site(tmp_path, FULL_TITLE_STMT, FULL_PUBLICATION_STMT, chapter, FULL_SERIES_STMT)
    chapter_doc = parse_page(content_pages(output_dir)[0])

    description = meta_content(chapter_doc, "description")
    assert "Ce chapitre etudie precisement la question posee" in description
    assert meta_content(chapter_doc, "DC.Description") == description
    # The excerpt must come from the chapter's own body, not the book title.
    assert "Livre savant" not in description


def test_meta_description_is_truncated_at_a_word_boundary(tmp_path: Path) -> None:
    long_sentence = " ".join(f"mot{i}" for i in range(60))
    chapter = f"""
<group xml:id='chapitre' type='chapter' data-page-title='Chapitre long'>
  <body>
    <div type='section1'>
      <head>Chapitre long</head>
      <p>{long_sentence}</p>
    </div>
  </body>
</group>
"""
    output_dir = build_metadata_site(tmp_path, FULL_TITLE_STMT, FULL_PUBLICATION_STMT, chapter, FULL_SERIES_STMT)
    chapter_doc = parse_page(content_pages(output_dir)[0])

    description = meta_content(chapter_doc, "description")
    assert len(description) <= 161  # 160 chars + ellipsis character
    assert description.endswith("…")
    assert not description[:-1].endswith(" ")
    assert " mot" in description or description.startswith("mot")


def test_minimal_metadata_does_not_emit_empty_meta_or_links(tmp_path: Path) -> None:
    output_dir = build_metadata_site(
        tmp_path,
        "<title type='main'>Livre minimal</title>",
        "<p/>",
        ONE_CHAPTER,
    )
    index_html = (output_dir / "index.html").read_text(encoding="utf-8")
    chapter_html = content_pages(output_dir)[0].read_text(encoding="utf-8")

    assert 'content=""' not in index_html
    assert 'content=""' not in chapter_html
    assert 'href=""' not in index_html
    assert 'href=""' not in chapter_html
    assert "Livre minimal" in index_html
    assert "Livre minimal" in chapter_html
