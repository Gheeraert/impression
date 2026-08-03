from __future__ import annotations

from pathlib import Path

from lxml import html as lxml_html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder

_TITLE_STMT = "<title type='main'>Livre langue</title><author>Auteur, Une</author>"
_PUBLICATION_STMT = "<publisher>PURH</publisher><date when='2024'>2024</date>"


def _build_site(tmp_path: Path, lang_usage: str, body: str = "") -> Path:
    chapter = body or """
<group xml:id='chapitre' type='chapter' data-page-title='Chapitre un'>
  <body>
    <div type='section1'>
      <head>Chapitre un</head>
      <p>Texte.</p>
    </div>
  </body>
</group>
"""
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>{_TITLE_STMT}</titleStmt>
      <publicationStmt>{_PUBLICATION_STMT}</publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
    {lang_usage}
  </teiHeader>
  <text>
    <group type='book'>
      {chapter}
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


def test_html_lang_defaults_to_fr_without_metadata(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, lang_usage="")
    doc = _parse(output_dir / "index.html")

    assert doc.xpath("string(/html/@lang)") == "fr"


def test_html_lang_reflects_document_language_metadata(tmp_path: Path) -> None:
    output_dir = _build_site(
        tmp_path,
        lang_usage="<profileDesc><langUsage><language ident='en-GB'/></langUsage></profileDesc>",
    )
    doc = _parse(output_dir / "index.html")
    chapter_doc = _parse(next(p for p in output_dir.glob("*.html") if p.name != "index.html"))

    assert doc.xpath("string(/html/@lang)") == "en-GB"
    assert chapter_doc.xpath("string(/html/@lang)") == "en-GB"


def test_citation_language_uses_primary_subtag_only(tmp_path: Path) -> None:
    output_dir = _build_site(
        tmp_path,
        lang_usage="<profileDesc><langUsage><language ident='en-GB'/></langUsage></profileDesc>",
    )
    doc = _parse(output_dir / "index.html")

    assert doc.xpath("string(//meta[@name='citation_language']/@content)") == "en"


def test_content_images_get_loading_lazy(tmp_path: Path) -> None:
    chapter_with_image = """
<group xml:id='chapitre' type='chapter' data-page-title='Chapitre un'>
  <body>
    <div type='section1'>
      <head>Chapitre un</head>
      <p>Texte.</p>
      <figure><graphic url='img/fig1.jpg'/></figure>
    </div>
  </body>
</group>
"""
    output_dir = _build_site(tmp_path, lang_usage="", body=chapter_with_image)
    chapter_doc = _parse(next(p for p in output_dir.glob("*.html") if p.name != "index.html"))

    images = chapter_doc.xpath("//figure//img")
    assert images, "Expected at least one content image"
    assert all(img.get("loading") == "lazy" for img in images)
