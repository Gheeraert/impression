from __future__ import annotations

from pathlib import Path

from lxml import html as lxml_html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder

_TITLE_STMT = "<title type='main'>Livre social</title><author>Auteur, Une</author>"

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
<ab type='digital_online'>
  <ref type='site' target='https://example.org/livre/'/>
</ab>
"""

_PUBLICATION_STMT_WITHOUT_SITE_URL = "<publisher>PURH</publisher><date when='2024'>2024</date>"


def _build_site(tmp_path: Path, publication_stmt: str, lang_usage: str = "") -> Path:
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
    {lang_usage}
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


def _og(doc: lxml_html.HtmlElement, prop: str) -> str:
    values = doc.xpath(f"string(//meta[@property={prop!r}]/@content)")
    return values


def _twitter(doc: lxml_html.HtmlElement, name: str) -> str:
    return doc.xpath(f"string(//meta[@name={name!r}]/@content)")


def test_open_graph_and_twitter_tags_on_chapter_page(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITH_SITE_URL)
    chapter_path = next(p for p in output_dir.glob("*.html") if p.name != "index.html")
    doc = _parse(chapter_path)

    assert _og(doc, "og:type") == "article"
    assert _og(doc, "og:title") == "Chapitre un"
    assert _og(doc, "og:url") == f"https://example.org/livre/{chapter_path.name}"
    assert _og(doc, "og:site_name") == "Livre social"
    assert "Texte du chapitre" in _og(doc, "og:description")
    assert _twitter(doc, "twitter:card") == "summary"  # no cover image available
    assert _twitter(doc, "twitter:title") == "Chapitre un"


def test_open_graph_type_is_website_on_home_page(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITH_SITE_URL)
    doc = _parse(output_dir / "index.html")

    assert _og(doc, "og:type") == "website"
    assert _og(doc, "og:title") == "Livre social"


def test_social_meta_omitted_without_site_url(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITHOUT_SITE_URL)
    doc = _parse(output_dir / "index.html")

    assert not doc.xpath("//meta[starts-with(@property, 'og:')]")
    assert not doc.xpath("//meta[starts-with(@name, 'twitter:')]")


def test_og_locale_derived_from_document_language(tmp_path: Path) -> None:
    output_dir = _build_site(
        tmp_path,
        _PUBLICATION_STMT_WITH_SITE_URL,
        lang_usage="<profileDesc><langUsage><language ident='en-GB'/></langUsage></profileDesc>",
    )
    doc = _parse(output_dir / "index.html")

    assert _og(doc, "og:locale") == "en_GB"
