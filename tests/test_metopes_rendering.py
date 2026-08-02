from __future__ import annotations

from pathlib import Path

from lxml import etree, html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder


def render_chapter_html(tmp_path: Path, fragment: str) -> str:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre Métopes</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre de rendu'>
        <body>
          <div type='section1'>
            <head>Section de test</head>
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
    page_path = result.output_dir / "01-chapitre-de-rendu.html"
    return page_path.read_text(encoding="utf-8")


def render_chapter(tmp_path: Path, fragment: str) -> html.HtmlElement:
    return html.fromstring(render_chapter_html(tmp_path, fragment))


def render_raw_tei_fragment(fragment: str) -> str:
    root = etree.fromstring(
        f"""<group xmlns='http://www.tei-c.org/ns/1.0' type='chapter'>
  <body>
    {fragment}
  </body>
</group>""".encode()
    )
    return SiteBuilder()._render_page_fragment(root, etree.ElementTree(root))


def test_tei_table_renders_as_html_table(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <table>
          <head>Tableau des exemples</head>
          <row role='label'><cell>Nom</cell><cell>Valeur</cell></row>
          <row><cell>Alpha</cell><cell>10</cell></row>
        </table>
        """,
    )

    assert doc.xpath("count(//table)") == 1
    assert doc.xpath("string(//table/caption)") == "Tableau des exemples"
    assert [cell.text_content() for cell in doc.xpath("//table/tr[1]/th")] == ["Nom", "Valeur"]
    assert [cell.text_content() for cell in doc.xpath("//table/tr[2]/td")] == ["Alpha", "10"]


def test_choice_abbr_expan_prefers_visible_abbreviation_with_title(tmp_path: Path) -> None:
    # Politique minimale : conserver l'abreviation dans le flux de lecture
    # et placer l'expansion dans title pour eviter le rendu fautif "M.Monsieur".
    doc = render_chapter(
        tmp_path,
        "<p>Il rencontre <choice><abbr>M.</abbr><expan>Monsieur</expan></choice> Dupont.</p>",
    )

    paragraph = doc.xpath("//div[contains(@class, 'tei-fragment')]//p")[0]
    abbr = paragraph.xpath(".//abbr")[0]

    assert abbr.text_content() == "M."
    assert abbr.get("title") == "Monsieur"
    assert "M.Monsieur" not in paragraph.text_content()
    assert "M. Dupont" in paragraph.text_content()


def test_inline_quotes_remain_inline_but_long_quotes_stay_block(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <p>Une <q>formule brève</q> reste inline.</p>
        <p>Une <quote>citation dans un paragraphe</quote> reste aussi inline.</p>
        <quote>Une citation longue isolée.</quote>
        """,
    )

    assert doc.xpath("string(//p[.//q][1]/q)") == "formule brève"
    assert doc.xpath("string(//p[.//q][2]/q)") == "citation dans un paragraphe"
    assert doc.xpath("count(//p//blockquote)") == 0
    assert doc.xpath("string(//blockquote)") == "Une citation longue isolée."


def test_bibl_rendering_depends_on_context(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <p>Texte avec note<note>Voir <bibl>Auteur, <title>Titre en note</title>.</bibl></note>.</p>
        <cit>
          <quote>Citation longue.</quote>
          <bibl>Auteur, <title>Titre cité</title>.</bibl>
        </cit>
        <listBibl>
          <bibl>Auteur, <title>Titre général</title>, 2020.</bibl>
        </listBibl>
        """,
    )

    endnote = doc.xpath("//section[contains(@class, 'endnotes')]//li")[0]
    citation = doc.xpath("//div[contains(@class, 'cit-block')]")[0]
    bibliography = doc.xpath("//section[contains(@class, 'bibliography-block')]")[0]

    assert endnote.xpath("count(.//li)") == 0
    assert endnote.xpath("string(.//cite)") == "Auteur, Titre en note."
    assert citation.xpath("string(.//cite)") == "Auteur, Titre cité."
    assert bibliography.xpath("count(.//ol[contains(@class, 'bibl-list')]/li)") == 1
    assert bibliography.xpath("string(.//ol[contains(@class, 'bibl-list')]/li)") == "Auteur, Titre général, 2020."


def test_cit_inside_paragraph_stays_inline_and_valid(tmp_path: Path) -> None:
    html_source = render_chapter_html(
        tmp_path,
        """
        <p>
          Texte avant
          <cit>
            <quote>citation brève</quote>
            <bibl>Source brève</bibl>
          </cit>
          texte après.
        </p>
        """,
    )
    doc = html.fromstring(html_source)
    paragraph = doc.xpath("//div[contains(@class, 'tei-fragment')]//p")[0]

    assert "cit-block" not in html_source
    assert paragraph.xpath("count(.//div[contains(@class, 'cit-block')])") == 0
    assert paragraph.xpath("string(.//q)") == "citation brève"
    assert paragraph.xpath("string(.//cite)") == "Source brève"
    paragraph_text = " ".join(paragraph.text_content().split())
    assert "Texte avant" in paragraph_text
    assert "citation brève" in paragraph_text
    assert "Source brève" in paragraph_text
    assert "texte après." in paragraph_text


def test_xslt_omits_empty_html_ids_but_preserves_existing_xml_ids() -> None:
    html_source = render_raw_tei_fragment(
        """
        <div>
          <p>Paragraphe sans identifiant.</p>
          <listBibl>
            <bibl>Notice sans identifiant.</bibl>
          </listBibl>
          <figure><head>Figure sans identifiant</head></figure>
        </div>
        <div xml:id='div-explicit'>
          <p xml:id='p-explicit'>Paragraphe avec identifiant.</p>
          <listBibl xml:id='biblio-explicit'>
            <bibl xml:id='notice-explicit'>Notice avec identifiant.</bibl>
          </listBibl>
          <figure xml:id='figure-explicit'><head>Figure avec identifiant</head></figure>
        </div>
        """
    )

    assert 'id=""' not in html_source
    assert 'id="div-explicit"' in html_source
    assert 'id="p-explicit"' in html_source
    assert 'id="biblio-explicit"' in html_source
    assert 'id="notice-explicit"' in html_source
    assert 'id="figure-explicit"' in html_source
