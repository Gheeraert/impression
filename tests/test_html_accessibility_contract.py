from __future__ import annotations

"""Tests du contrat HTML/accessibilité identifié par un audit externe du
rendu : identifiants des <head> TEI, texte alternatif des images,
width/height réels, aria-current sur la navigation."""

import base64
from pathlib import Path

from lxml import html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder

# PNG 15x10 valide minimal (généré avec Pillow, figé en base64 — voir aussi
# tests/test_image_dimensions.py).
PNG_15x10_B64 = "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAKCAIAAADkeZOuAAAAGElEQVR4nGP8z0ACYCJFMcOoakxAyzABAN0IARNDUhaOAAAAAElFTkSuQmCC"


def render_chapter(tmp_path: Path, fragment: str, assets_dir: Path | None = None) -> html.HtmlElement:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre accessibilité</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre un'>
        <body>
          <div type='section1'>
            <head>Section</head>
            {fragment}
          </div>
        </body>
      </group>
      <group type='chapter' data-page-title='Chapitre deux'>
        <body>
          <div type='section1'><head>Autre section</head><p>Texte.</p></div>
        </body>
      </group>
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )

    config = BuildConfig(output_dir=tmp_path / "site", assets_dir=assets_dir)
    result = SiteBuilder().build_from_master(xml_path, config)
    page_html = (result.output_dir / "01-chapitre-un.html").read_text(encoding="utf-8")
    return html.fromstring(page_html)


# ---------------------------------------------------------------------------
# 1. xml:id des <head> TEI reporté en HTML
# ---------------------------------------------------------------------------

def test_div_head_xml_id_becomes_heading_id(tmp_path: Path) -> None:
    doc = render_chapter(tmp_path, """<div type="section2"><head xml:id="ma-section">Sous-titre</head><p>Texte.</p></div>""")
    heading = doc.xpath("//*[@id='ma-section']")
    assert len(heading) == 1
    assert heading[0].tag == "h3"
    assert heading[0].text_content().strip() == "Sous-titre"


def test_figure_head_xml_id_becomes_figcaption_id(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<figure><head xml:id="titre-figure">Titre de la figure</head><figDesc>Description.</figDesc></figure>""",
    )
    caption = doc.xpath("//*[@id='titre-figure']")
    assert len(caption) == 1
    assert caption[0].tag == "figcaption"


def test_table_head_xml_id_becomes_caption_id(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<figure><table><head xml:id="titre-tableau">Titre du tableau</head>
          <row><cell>A</cell></row></table></figure>""",
    )
    caption = doc.xpath("//*[@id='titre-tableau']")
    assert len(caption) == 1
    assert caption[0].tag == "caption"


def test_listbibl_head_xml_id_becomes_heading_id(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<listBibl><head xml:id="titre-biblio">Références</head><bibl>Notice.</bibl></listBibl>""",
    )
    heading = doc.xpath("//*[@id='titre-biblio']")
    assert len(heading) == 1
    assert heading[0].tag == "h2"


def test_div_without_source_head_id_still_gets_a_stable_generated_id(tmp_path: Path) -> None:
    # Le normaliseur attribue un xml:id déterministe aux <head> qui n'en ont
    # pas dans la source ; ce correctif le reporte donc lui aussi en HTML.
    doc = render_chapter(tmp_path, """<div type="section2"><head>Sans identifiant</head><p>Texte.</p></div>""")
    heading = doc.xpath("//h3[normalize-space(.)='Sans identifiant']")
    assert len(heading) == 1
    assert heading[0].get("id")


# ---------------------------------------------------------------------------
# 2. Texte alternatif des images
# ---------------------------------------------------------------------------

def test_graphic_desc_takes_priority_for_alt_text(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<figure>
          <graphic url="fig.png"><desc>Description visuelle courte.</desc></graphic>
          <figDesc>Légende bibliographique plus longue.</figDesc>
        </figure>""",
    )
    img = doc.xpath("//img")[0]
    assert img.get("alt") == "Description visuelle courte."


def test_figdesc_used_as_alt_when_no_desc(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<figure><graphic url="fig.png"/><figDesc>Légende bibliographique.</figDesc></figure>""",
    )
    img = doc.xpath("//img")[0]
    assert img.get("alt") == "Légende bibliographique."


def test_lightbox_caption_keeps_bibliographic_text_even_with_desc(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<figure>
          <graphic url="fig.png"><desc>Alt court.</desc></graphic>
          <figDesc>Légende affichée dans la visionneuse.</figDesc>
        </figure>""",
    )
    trigger = doc.xpath("//button[contains(@class, 'figure-zoom-trigger')]")[0]
    assert trigger.get("data-lightbox-alt") == "Alt court."
    assert trigger.get("data-lightbox-caption") == "Légende affichée dans la visionneuse."


# ---------------------------------------------------------------------------
# 3. width/height réels
# ---------------------------------------------------------------------------

def test_image_width_height_injected_from_real_file(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets_src"
    (assets_dir / "images").mkdir(parents=True)
    (assets_dir / "images" / "fig.png").write_bytes(base64.b64decode(PNG_15x10_B64))

    doc = render_chapter(tmp_path, """<figure><graphic url="fig.png"/></figure>""", assets_dir=assets_dir)
    img = doc.xpath("//img")[0]
    assert img.get("width") == "15"
    assert img.get("height") == "10"


def test_no_width_height_injected_when_image_file_missing(tmp_path: Path) -> None:
    doc = render_chapter(tmp_path, """<figure><graphic url="absente.png"/></figure>""")
    img = doc.xpath("//img")[0]
    assert img.get("width") is None
    assert img.get("height") is None


def test_xml_declared_width_height_are_not_overwritten(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets_src"
    (assets_dir / "images").mkdir(parents=True)
    (assets_dir / "images" / "fig.png").write_bytes(base64.b64decode(PNG_15x10_B64))

    doc = render_chapter(
        tmp_path,
        """<figure><graphic url="fig.png" width="999" height="888"/></figure>""",
        assets_dir=assets_dir,
    )
    img = doc.xpath("//img")[0]
    assert img.get("width") == "999"
    assert img.get("height") == "888"


# ---------------------------------------------------------------------------
# 4. aria-current="page" sur la navigation
# ---------------------------------------------------------------------------

def test_current_nav_item_has_aria_current_page(tmp_path: Path) -> None:
    doc = render_chapter(tmp_path, "<p>Texte.</p>")
    current_link = doc.xpath("//nav[contains(@class,'sidebar-nav')]//li[contains(@class,'is-current')]/a")
    assert len(current_link) == 1
    assert current_link[0].get("aria-current") == "page"


def test_non_current_nav_item_has_no_aria_current(tmp_path: Path) -> None:
    doc = render_chapter(tmp_path, "<p>Texte.</p>")
    other_link = doc.xpath("//nav[contains(@class,'sidebar-nav')]//li[not(contains(@class,'is-current'))]/a")
    assert len(other_link) == 1
    assert other_link[0].get("aria-current") is None
