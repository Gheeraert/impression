from __future__ import annotations

"""Tests des points structurants identifiés lors de l'analyse du fixture
TEI Commons Publishing (tests/fixtures/commons-publishing/) : front/back
des unités TEI autonomes, tableaux et formules dans les figures,
résolution des chemins d'images, listes ordonnées et @rendition, ancres
et citations avec xml:id, styles @rend combinés/uppercase.
"""

from pathlib import Path

from lxml import html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder


def render_chapter(tmp_path: Path, fragment: str) -> html.HtmlElement:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre structurel</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
    <encodingDesc>
      <tagsDecl>
        <rendition xml:id="rendition_upper_roman" scheme="css">list-style-type:upper-roman</rendition>
        <rendition xml:id="rendition_disc" scheme="css">list-style-type:disc</rendition>
        <rendition xml:id="rtl" scheme="css">direction:rtl;</rendition>
        <rendition xml:id="Cell" scheme="css">border-top:2.25pt solid #000000;</rendition>
      </tagsDecl>
    </encodingDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre structurel'>
        <body>
          <div type='section1'>
            <head>Section structurelle</head>
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
    page_html = (result.output_dir / "01-chapitre-structurel.html").read_text(encoding="utf-8")
    return html.fromstring(page_html)


def render_standalone_unit(tmp_path: Path, front: str, body: str, back: str) -> tuple[html.HtmlElement, str]:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Unité autonome</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <front>{front}</front>
    <body>{body}</body>
    <back>{back}</back>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))
    pages = sorted(p for p in result.output_dir.glob("*.html") if p.name != "index.html")
    assert len(pages) == 1
    page_html = pages[0].read_text(encoding="utf-8")
    return html.fromstring(page_html), page_html


# ---------------------------------------------------------------------------
# 1. Front/back des unités TEI autonomes (<text> sans <group>)
# ---------------------------------------------------------------------------

def test_standalone_unit_renders_front_matter(tmp_path: Path) -> None:
    doc, page_html = render_standalone_unit(
        tmp_path,
        front="<div type='abstract'><p>Résumé du document.</p></div>",
        body="<div type='section1'><head>Corps</head><p>Texte du corps.</p></div>",
        back="",
    )
    assert "Résumé du document." in page_html
    assert "Texte du corps." in page_html


def test_standalone_unit_renders_back_matter(tmp_path: Path) -> None:
    doc, page_html = render_standalone_unit(
        tmp_path,
        front="",
        body="<div type='section1'><head>Corps</head><p>Texte du corps.</p></div>",
        back="<div type='appendix'><div type='section1'><head>Annexe</head><p>Contenu annexe.</p></div></div>",
    )
    assert "Contenu annexe." in page_html


def test_standalone_unit_front_and_back_appear_around_body_in_order(tmp_path: Path) -> None:
    _, page_html = render_standalone_unit(
        tmp_path,
        front="<div type='abstract'><p>MARQUEUR-FRONT</p></div>",
        body="<div type='section1'><head>Corps</head><p>MARQUEUR-BODY</p></div>",
        back="<div type='bibliography'><listBibl><bibl>MARQUEUR-BACK</bibl></listBibl></div>",
    )
    assert page_html.index("MARQUEUR-FRONT") < page_html.index("MARQUEUR-BODY") < page_html.index("MARQUEUR-BACK")


# ---------------------------------------------------------------------------
# 2. Tableaux et formules dans les figures
# ---------------------------------------------------------------------------

def test_table_inside_figure_is_rendered(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure xml:id="figure-table">
          <head>Titre du tableau</head>
          <table>
            <row role="label"><cell>Entête A</cell><cell>Entête B</cell></row>
            <row><cell>A1</cell><cell cols="1">B1</cell></row>
          </table>
        </figure>
        """,
    )
    table = doc.xpath("//figure[@id='figure-table']//table")
    assert len(table) == 1
    assert table[0].xpath(".//th[normalize-space(.)='Entête A']")
    assert table[0].xpath(".//td[normalize-space(.)='A1']")


def test_table_cell_cols_attribute_becomes_html_colspan(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure><table>
          <row><cell cols="2">Fusionnée</cell></row>
        </table></figure>
        """,
    )
    cell = doc.xpath("//td[normalize-space(.)='Fusionnée']")
    assert len(cell) == 1
    assert cell[0].get("colspan") == "2"


def test_formula_inside_figure_is_preserved_as_text(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <figure>
          <formula notation="latex">\\[\\frac{a}{b}\\]</formula>
        </figure>
        """,
    )
    formula = doc.xpath("//span[contains(@class, 'tei-formula')]")
    assert len(formula) == 1
    assert "\\frac{a}{b}" in formula[0].text_content()
    assert formula[0].get("data-notation") == "latex"


# ---------------------------------------------------------------------------
# 3. Résolution des chemins d'images
# ---------------------------------------------------------------------------

def test_image_url_with_own_images_folder_is_not_doubled(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<figure><graphic url="images/fig.jpg"/></figure>""",
    )
    img = doc.xpath("//img")
    assert len(img) == 1
    assert img[0].get("src") == "assets/images/fig.jpg"


def test_image_url_without_folder_still_resolves_under_assets_images(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<figure><graphic url="fig.jpg"/></figure>""",
    )
    img = doc.xpath("//img")
    assert img[0].get("src") == "assets/images/fig.jpg"


def test_image_url_navigating_to_sibling_folder_is_preserved(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<figure><graphic url="../icono/fig.jpg"/></figure>""",
    )
    img = doc.xpath("//img")
    assert img[0].get("src") == "assets/images/../icono/fig.jpg"


# ---------------------------------------------------------------------------
# 4. Listes ordonnées / non ordonnées et @rendition
# ---------------------------------------------------------------------------

def test_ordered_list_renders_as_ol_with_rendition_style(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<list type="ordered" rendition="#rendition_upper_roman"><item>un</item><item>deux</item></list>""",
    )
    ol = doc.xpath("//div[contains(@class, 'tei-fragment')]//ol")
    assert len(ol) == 1
    assert "list-style-type:upper-roman" in ol[0].get("style", "")


def test_unordered_list_stays_ul_with_rendition_style(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<list type="unordered" rendition="#rendition_disc"><item>un</item></list>""",
    )
    assert not doc.xpath("//div[contains(@class, 'tei-fragment')]//ol")
    ul = doc.xpath("//div[contains(@class, 'tei-fragment')]//ul")
    assert len(ul) == 1
    assert "list-style-type:disc" in ul[0].get("style", "")


def test_ordered_list_continues_numbering_via_prev(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <list type="ordered" xml:id="list01"><item>un</item><item>deux</item><item>trois</item></list>
        <list type="ordered" xml:id="list02" prev="#list01"><item>quatre</item><item>cinq</item></list>
        """,
    )
    lists = doc.xpath("//div[contains(@class, 'tei-fragment')]//ol")
    assert len(lists) == 2
    assert lists[0].get("start") is None
    assert lists[1].get("start") == "4"


# ---------------------------------------------------------------------------
# 5. Ancres et citations avec xml:id
# ---------------------------------------------------------------------------

def test_cit_xml_id_is_preserved_as_html_id(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <cit xml:id="cit-cible"><quote>Citation cible.</quote></cit>
        <p>Voir <ref target="#cit-cible">la citation</ref>.</p>
        """,
    )
    target = doc.xpath("//*[@id='cit-cible']")
    assert len(target) == 1
    link = doc.xpath("//a[@href='#cit-cible']")
    assert len(link) == 1


def test_anchor_xml_id_is_rendered_as_link_target(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <p>Texte <anchor xml:id="ancre-cible"/>avec une ancre.</p>
        <p>Voir <ref target="#ancre-cible">l'ancre</ref>.</p>
        """,
    )
    target = doc.xpath("//*[@id='ancre-cible']")
    assert len(target) == 1


# ---------------------------------------------------------------------------
# 6. Styles @rend : uppercase et combinaisons à 3+ valeurs
# ---------------------------------------------------------------------------

def test_hi_uppercase_is_applied(tmp_path: Path) -> None:
    doc = render_chapter(tmp_path, """<p><hi rend="uppercase">majuscule</hi></p>""")
    span = doc.xpath("//span[contains(@class, 'tei-uppercase')]")
    assert len(span) == 1
    assert span[0].text_content().strip() == "majuscule"


def test_hi_combined_three_way_rend_applies_all_styles(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<p><hi rend="sup small-caps underline">texte combiné</hi></p>""",
    )
    sup = doc.xpath("//sup[contains(@class, 'tei-sup')]")
    smallcaps = doc.xpath("//span[contains(@class, 'smallcaps')]")
    underline = doc.xpath("//span[contains(@class, 'tei-underline')]")
    assert len(sup) == 1
    assert len(smallcaps) == 1
    assert len(underline) == 1
    assert sup[0].text_content().strip() == "texte combiné"


# ---------------------------------------------------------------------------
# 7. @rendition générique : RTL, bordures de cellule
# ---------------------------------------------------------------------------

def test_rtl_rendition_on_paragraph_becomes_inline_style(tmp_path: Path) -> None:
    doc = render_chapter(tmp_path, """<p rendition="#rtl">نص عربي</p>""")
    paragraphs = doc.xpath("//p[contains(@style, 'direction:rtl')]")
    assert len(paragraphs) == 1


def test_cell_rendition_becomes_inline_style(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """<figure><table><row><cell rendition="#Cell">contenu</cell></row></table></figure>""",
    )
    cell = doc.xpath("//td[contains(@style, 'border-top')]")
    assert len(cell) == 1


# ---------------------------------------------------------------------------
# 8. listBibl imbriqué : intitulé propre plutôt qu'un texte fixe
# ---------------------------------------------------------------------------

def test_nested_listbibl_uses_its_own_heading(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <listBibl>
          <head>Bibliographie générale</head>
          <listBibl>
            <head>Partie 1</head>
            <bibl>Notice A.</bibl>
          </listBibl>
          <listBibl>
            <head>Partie 2</head>
            <bibl>Notice B.</bibl>
          </listBibl>
        </listBibl>
        """,
    )
    headings = [h.text_content().strip() for h in doc.xpath("//section[contains(@class,'bibliography-block')]/h2")]
    assert "Bibliographie générale" in headings
    assert "Partie 1" in headings
    assert "Partie 2" in headings
