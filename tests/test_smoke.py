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


def test_lightbox_markup_is_present_for_figures_and_covers(tmp_path: Path) -> None:
    xml_path = tmp_path / 'book.xml'
    xml_path.write_text(TEI_SAMPLE_WITH_FIGURE, encoding='utf-8')

    assets_dir = tmp_path / 'source_assets'
    figure_path = assets_dir / 'icono' / 'br' / 'Ch03_Loskoutoff_1' / 'fig10.jpg'
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.write_bytes(b'fake-jpg')
    cover_path = assets_dir / 'images' / 'cover.jpg'
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    cover_path.write_bytes(b'fake-cover')

    builder = SiteBuilder()
    result = builder.build_from_master(xml_path, BuildConfig(output_dir=tmp_path / 'site', assets_dir=assets_dir))

    index_html = result.html_path.read_text(encoding='utf-8')
    page_html = (tmp_path / 'site' / '01-chapitre-image.html').read_text(encoding='utf-8')

    assert 'class="book-cover-link book-cover-trigger"' in index_html
    assert 'data-lightbox-src="assets/images/cover.jpg"' in index_html
    assert 'class="figure-zoom-trigger media-zoom-trigger"' in page_html
    assert 'data-lightbox-src="assets/images/../icono/br/Ch03_Loskoutoff_1/fig10.jpg"' in page_html

    app_js = (tmp_path / 'site' / 'assets' / 'app.js').read_text(encoding='utf-8')
    assert 'Télécharger l’original' in app_js
    assert "lb.download.href = src;" in app_js


def test_article_images_are_normalized_in_default_css(tmp_path: Path) -> None:
    xml_path = tmp_path / 'book.xml'
    xml_path.write_text(TEI_SAMPLE_WITH_FIGURE, encoding='utf-8')

    builder = SiteBuilder()
    builder.build_from_master(xml_path, BuildConfig(output_dir=tmp_path / 'site'))

    css = (tmp_path / 'site' / 'assets' / 'site.css').read_text(encoding='utf-8')

    assert '.figure-zoom-trigger img {' in css
    assert 'max-width: min(100%, 760px);' in css
    assert 'max-height: clamp(260px, 46vh, 520px);' in css


TEI_SAMPLE_WITHOUT_TITLE_OR_COLLECTION = """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt/>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre sans metadata'>
        <body>
          <div type='section1'>
            <head>Section simple</head>
            <p>Texte.</p>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
"""


def test_build_config_fallbacks_are_used_when_xml_is_silent(tmp_path: Path) -> None:
    xml_path = tmp_path / 'book.xml'
    xml_path.write_text(TEI_SAMPLE_WITHOUT_TITLE_OR_COLLECTION, encoding='utf-8')

    builder = SiteBuilder()
    result = builder.build_from_master(
        xml_path,
        BuildConfig(
            output_dir=tmp_path / 'site',
            collection_title='Collection de repli',
            collection_number='42',
            collection_issn='1234-5678',
            site_title_fallback='Titre de repli',
        ),
    )

    index_html = result.html_path.read_text(encoding='utf-8')

    assert '<h1>Titre de repli</h1>' in index_html
    assert 'name="citation_series_title" content="Collection de repli"' in index_html
    assert 'name="citation_series_number" content="42"' in index_html
    assert 'name="citation_issn" content="1234-5678"' in index_html


def test_xml_metadata_keeps_priority_over_config_fallbacks(tmp_path: Path) -> None:
    xml_path = tmp_path / 'book.xml'
    xml_path.write_text(TEI_SAMPLE, encoding='utf-8')

    builder = SiteBuilder()
    result = builder.build_from_master(
        xml_path,
        BuildConfig(
            output_dir=tmp_path / 'site',
            collection_title='Collection de repli',
            site_title_fallback='Titre de repli',
        ),
    )

    index_html = result.html_path.read_text(encoding='utf-8')

    assert '<h1>Livre de test</h1>' in index_html
    assert '<h1>Titre de repli</h1>' not in index_html


def test_write_normalized_tei_false_skips_export_and_download_link(tmp_path: Path) -> None:
    xml_path = tmp_path / 'book.xml'
    xml_path.write_text(TEI_SAMPLE, encoding='utf-8')

    builder = SiteBuilder()
    result = builder.build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / 'site', write_normalized_tei=False),
    )

    index_html = result.html_path.read_text(encoding='utf-8')

    assert result.normalized_tei_path is None
    assert not (tmp_path / 'site' / 'book.normalized.xml').exists()
    assert 'href="book.normalized.xml"' not in index_html


def test_external_back_cover_path_is_used_as_fallback(tmp_path: Path) -> None:
    xml_path = tmp_path / 'book.xml'
    xml_path.write_text(TEI_SAMPLE, encoding='utf-8')
    back_cover_path = tmp_path / 'quatrieme.md'
    back_cover_path.write_text('Texte de **quatrieme** externe.', encoding='utf-8')

    builder = SiteBuilder()
    result = builder.build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / 'site', back_cover_path=back_cover_path),
    )

    index_html = result.html_path.read_text(encoding='utf-8')
    report = result.report_path.read_text(encoding='utf-8')

    assert '<p>Texte de <strong>quatrieme</strong> externe.</p>' in index_html
    assert str(back_cover_path) in report


def test_build_from_many_accepts_gui_style_config_overrides(tmp_path: Path) -> None:
    xml_one = tmp_path / 'one.xml'
    xml_two = tmp_path / 'two.xml'
    xml_one.write_text(TEI_SAMPLE, encoding='utf-8')
    xml_two.write_text(TEI_SAMPLE_WITH_FIGURE, encoding='utf-8')

    builder = SiteBuilder()
    results = builder.build_from_many(
        [xml_one, xml_two],
        tmp_path / 'sites',
        assets_dir=None,
        config_overrides=BuildConfig(
            output_dir=tmp_path / 'unused',
            collection_title='Collection GUI',
            write_normalized_tei=False,
        ),
    )

    assert len(results) == 2
    assert (tmp_path / 'sites' / 'one' / 'index.html').exists()
    assert (tmp_path / 'sites' / 'two' / 'index.html').exists()
    assert results[0].normalized_tei_path is None
    assert not (tmp_path / 'sites' / 'one' / 'book.normalized.xml').exists()
    assert 'Collection GUI' in (tmp_path / 'sites' / 'one' / 'index.html').read_text(encoding='utf-8')
