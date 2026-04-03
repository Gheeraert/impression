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


TEI_SAMPLE_WITH_FIGURE = """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type='main'>Livre avec figure</title>
      </titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre image'>
        <body>
          <div type='section1'>
            <head>Section image</head>
            <figure>
              <graphic url='../icono/br/Ch03_Loskoutoff_1/fig10.jpg'/>
              <head>Figure 10</head>
            </figure>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
"""


def test_build_preserves_xml_driven_asset_paths(tmp_path: Path) -> None:
    xml_path = tmp_path / 'book.xml'
    xml_path.write_text(TEI_SAMPLE_WITH_FIGURE, encoding='utf-8')

    assets_dir = tmp_path / 'source_assets'
    figure_path = assets_dir / 'icono' / 'br' / 'Ch03_Loskoutoff_1' / 'fig10.jpg'
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.write_bytes(b'fake-jpg')

    builder = SiteBuilder()
    result = builder.build_from_master(xml_path, BuildConfig(output_dir=tmp_path / 'site', assets_dir=assets_dir))

    page_html = (tmp_path / 'site' / '01-chapitre-image.html').read_text(encoding='utf-8')
    assert 'src="assets/images/../icono/br/Ch03_Loskoutoff_1/fig10.jpg"' in page_html
    assert (tmp_path / 'site' / 'assets' / 'icono' / 'br' / 'Ch03_Loskoutoff_1' / 'fig10.jpg').exists()


TEI_SAMPLE_WITH_VOLUME_AUTHOR = """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type='main'>Héraldique et papauté</title>
        <title type='sub'>Moyen Âge – Temps modernes. II</title>
        <author role='pbd'>
          <persName>
            <forename>Yvan</forename>
            <surname>Loskoutoff</surname>
          </persName>
        </author>
      </titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre gamma' data-page-authors='Jeanne Test'>
        <body>
          <div type='section1'>
            <head>Section C</head>
            <p>Texte 3.</p>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
"""


def test_banner_and_credit_box_use_plain_names(tmp_path: Path) -> None:
    xml_path = tmp_path / 'book.xml'
    xml_path.write_text(TEI_SAMPLE_WITH_VOLUME_AUTHOR, encoding='utf-8')

    builder = SiteBuilder()
    result = builder.build_from_master(xml_path, BuildConfig(output_dir=tmp_path / 'site'))

    index_html = result.html_path.read_text(encoding='utf-8')
    page_html = (tmp_path / 'site' / '01-chapitre-gamma.html').read_text(encoding='utf-8')

    assert 'site-banner-subtitle' in index_html
    assert 'Moyen Âge – Temps modernes. II' in index_html
    assert 'site-banner-creators-role' not in index_html
    assert 'Auteur<' not in index_html
    assert 'Auteur·rice' not in page_html
    assert '<p class="credit-names">Jeanne Test</p>' in page_html
