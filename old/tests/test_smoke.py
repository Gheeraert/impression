from pathlib import Path

from lxml import etree

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder

TEI_SAMPLE = """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type='main'>Livre de test</title>
        <title type='sub'>Sous-titre</title>
      </titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='section1'>
        <head>Première partie</head>
        <group type='chapter' data-page-title='Chapitre alpha'>
          <body>
            <div type='section1'>
              <head>Section A</head>
              <p>Texte avec <note>une note</note>.</p>
            </div>
          </body>
        </group>
      </group>
      <group type='chapter' data-page-title='Chapitre bêta' data-page-authors='Jeanne Test'>
        <body>
          <div type='section1'>
            <head>Section B</head>
            <p>Texte 2.</p>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
"""


def test_build_multipage(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    builder = SiteBuilder()
    result = builder.build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))

    assert result.html_path.exists()
    assert (tmp_path / "site" / "01-chapitre-alpha.html").exists()
    assert (tmp_path / "site" / "02-chapitre-beta.html").exists()
    index_html = result.html_path.read_text(encoding="utf-8")
    page_html = (tmp_path / "site" / "02-chapitre-beta.html").read_text(encoding="utf-8")
    assert "Première partie" in index_html
    assert "Jeanne Test" in page_html
    assert "Crédits et citabilité" in page_html
