from __future__ import annotations

import json
from pathlib import Path

from lxml import html as lxml_html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder

_TITLE_STMT = "<title type='main'>Livre structure</title><author>Auteur, Une</author>"

_ONE_CHAPTER = """
<group xml:id='chapitre' type='chapter' data-page-title='Chapitre un'>
  <body>
    <div type='section1'>
      <head>Chapitre un</head>
      <p>Texte du chapitre.</p>
    </div>
  </body>
</group>
"""

_PUBLICATION_STMT_WITH_SITE_URL = """
<publisher>PURH</publisher>
<date when='2024'>2024</date>
<ab type='book'><idno type='ISBN'>979-10-240-1234-5</idno></ab>
<idno type='DOI'>10.4000/books.purh.9999</idno>
<ab type='digital_online'>
  <ref type='site' target='https://example.org/livre/'/>
</ab>
"""

_PUBLICATION_STMT_WITHOUT_SITE_URL = "<publisher>PURH</publisher><date when='2024'>2024</date>"


def _build_site(tmp_path: Path, publication_stmt: str) -> Path:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>{_TITLE_STMT}</titleStmt>
      <publicationStmt>{publication_stmt}</publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      {_ONE_CHAPTER}
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))
    return result.output_dir


def _parse(path: Path) -> lxml_html.HtmlElement:
    return lxml_html.fromstring(path.read_text(encoding="utf-8"))


def _json_ld(doc: lxml_html.HtmlElement) -> dict:
    scripts = doc.xpath("//script[@type='application/ld+json']/text()")
    assert scripts, "No JSON-LD script found"
    return json.loads(scripts[0])


def test_canonical_link_uses_absolute_site_url(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITH_SITE_URL)

    index_doc = _parse(output_dir / "index.html")
    chapter_path = next(p for p in output_dir.glob("*.html") if p.name != "index.html")
    chapter_doc = _parse(chapter_path)

    assert index_doc.xpath("string(//link[@rel='canonical']/@href)") == "https://example.org/livre/index.html"
    assert chapter_doc.xpath("string(//link[@rel='canonical']/@href)") == f"https://example.org/livre/{chapter_path.name}"


def test_canonical_link_omitted_without_site_url(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITHOUT_SITE_URL)
    index_doc = _parse(output_dir / "index.html")

    assert not index_doc.xpath("//link[@rel='canonical']")


def test_book_json_ld_on_home_page(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITH_SITE_URL)
    data = _json_ld(_parse(output_dir / "index.html"))

    assert data["@type"] == "Book"
    assert data["name"] == "Livre structure"
    assert data["url"] == "https://example.org/livre/index.html"
    assert data["author"] == [{"@type": "Person", "name": "Auteur, Une"}]
    assert data["publisher"] == {"@type": "Organization", "name": "PURH"}
    assert data["datePublished"] == "2024"
    assert data["isbn"] == "979-10-240-1234-5"
    assert data["sameAs"] == "https://doi.org/10.4000/books.purh.9999"


def test_chapter_json_ld_references_parent_book(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITH_SITE_URL)
    chapter_path = next(p for p in output_dir.glob("*.html") if p.name != "index.html")
    data = _json_ld(_parse(chapter_path))

    assert data["@type"] == "Chapter"
    assert data["name"] == "Chapitre un"
    assert data["url"] == f"https://example.org/livre/{chapter_path.name}"
    assert data["isPartOf"] == {
        "@type": "Book",
        "name": "Livre structure",
        "url": "https://example.org/livre/index.html",
    }
    assert "Texte du chapitre" in data["description"]


def test_json_ld_omitted_without_site_url(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITHOUT_SITE_URL)
    index_doc = _parse(output_dir / "index.html")

    assert not index_doc.xpath("//script[@type='application/ld+json']")
