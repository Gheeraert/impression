from __future__ import annotations

from pathlib import Path

from lxml import html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder


def render_chapter_html(tmp_path: Path, fragment: str) -> str:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre figures</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre figures'>
        <body>
          <div type='section1'>
            <head>Section figures</head>
            {fragment}
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )

    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))
    return (result.output_dir / "01-chapitre-figures.html").read_text(encoding="utf-8")


def render_chapter(tmp_path: Path, fragment: str) -> html.HtmlElement:
    return html.fromstring(render_chapter_html(tmp_path, fragment))


def test_figure_with_graphic_head_and_figdesc_uses_figdesc_as_alt(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure xml:id="fig-1">
          <head>Figure 1. Port-Royal des Champs</head>
          <graphic url="port-royal.jpg"/>
          <figDesc>Vue de Port-Royal des Champs.</figDesc>
        </figure>
        """,
    )

    figure = doc.xpath("//figure[@id='fig-1']")[0]
    image = figure.xpath(".//img")[0]

    assert image.get("src") == "assets/images/port-royal.jpg"
    assert image.get("alt") == "Vue de Port-Royal des Champs."
    assert figure.xpath("string(.//figcaption)") == "Figure 1. Port-Royal des Champs"
    assert "Vue de Port-Royal des Champs." not in figure.xpath("string(.//figcaption)")


def test_external_figure_url_is_not_prefixed(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure>
          <head>Image externe</head>
          <graphic url="https://example.org/image.jpg"/>
        </figure>
        """,
    )

    image = doc.xpath("//figure//img")[0]

    assert image.get("src") == "https://example.org/image.jpg"


def test_data_image_url_is_not_prefixed(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure>
          <head>Image embarquée</head>
          <graphic url="data:image/png;base64,AAAA"/>
        </figure>
        """,
    )

    image = doc.xpath("//figure//img")[0]

    assert image.get("src") == "data:image/png;base64,AAAA"


def test_figure_without_figdesc_uses_head_as_alt(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure>
          <head>Carte de la Normandie</head>
          <graphic url="carte.jpg"/>
        </figure>
        """,
    )

    figure = doc.xpath("//figure")[0]
    image = figure.xpath(".//img")[0]

    assert image.get("src") == "assets/images/carte.jpg"
    assert image.get("alt") == "Carte de la Normandie"
    assert figure.xpath("string(.//figcaption)") == "Carte de la Normandie"


def test_figure_without_head_uses_figdesc_as_alt_without_empty_caption(tmp_path: Path) -> None:
    html_source = render_chapter_html(
        tmp_path,
        """
        <figure>
          <graphic url="portrait.jpg"/>
          <figDesc>Portrait gravé de l'auteur.</figDesc>
        </figure>
        """,
    )
    doc = html.fromstring(html_source)
    figure = doc.xpath("//figure")[0]
    image = figure.xpath(".//img")[0]

    assert image.get("alt") == "Portrait gravé de l'auteur."
    assert figure.xpath("count(.//figcaption)") == 0
    assert "alt=\"\"" not in html_source
    assert "data-lightbox-alt=\"\"" not in html_source


def test_multiple_graphics_render_multiple_images_with_one_caption(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure>
          <head>Deux états de la gravure</head>
          <graphic url="etat-1.jpg"/>
          <graphic url="etat-2.jpg"/>
          <figDesc>Comparaison de deux états de la gravure.</figDesc>
        </figure>
        """,
    )

    figure = doc.xpath("//figure")[0]
    images = figure.xpath(".//img")

    assert [image.get("src") for image in images] == [
        "assets/images/etat-1.jpg",
        "assets/images/etat-2.jpg",
    ]
    assert [image.get("alt") for image in images] == [
        "Comparaison de deux états de la gravure.",
        "Comparaison de deux états de la gravure.",
    ]
    assert figure.xpath("count(.//figcaption)") == 1
    assert figure.xpath("string(.//figcaption)") == "Deux états de la gravure"


def test_graphic_width_height_are_preserved_when_present(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure>
          <head>Image mesurée</head>
          <graphic url="image.jpg" width="600" height="400"/>
        </figure>
        """,
    )

    image = doc.xpath("//figure//img")[0]

    assert image.get("src") == "assets/images/image.jpg"
    assert image.get("width") == "600"
    assert image.get("height") == "400"


def test_graphic_without_url_is_ignored(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure>
          <head>Figure incomplète</head>
          <graphic/>
          <graphic url="image.jpg"/>
        </figure>
        """,
    )

    images = doc.xpath("//figure//img")

    assert len(images) == 1
    assert images[0].get("src") == "assets/images/image.jpg"


def test_graphic_with_empty_url_is_ignored(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure>
          <head>Figure incomplète</head>
          <graphic url="   "/>
          <graphic url="image.jpg"/>
        </figure>
        """,
    )

    images = doc.xpath("//figure//img")

    assert len(images) == 1
    assert images[0].get("src") == "assets/images/image.jpg"


def test_empty_graphic_width_height_are_not_rendered(tmp_path: Path) -> None:
    html_source = render_chapter_html(
        tmp_path,
        """
        <figure>
          <head>Image sans mesures</head>
          <graphic url="image.jpg" width="   " height=""/>
        </figure>
        """,
    )
    doc = html.fromstring(html_source)
    image = doc.xpath("//figure//img")[0]

    assert image.get("src") == "assets/images/image.jpg"
    assert image.get("width") is None
    assert image.get("height") is None
    assert 'width=""' not in html_source
    assert 'height=""' not in html_source
