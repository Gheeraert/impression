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
      <titleStmt><title type='main'>Livre inline</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre inline'>
        <body>
          <div type='section1'>
            <head>Section inline</head>
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
    return (result.output_dir / "01-chapitre-inline.html").read_text(encoding="utf-8")


def render_chapter(tmp_path: Path, fragment: str) -> html.HtmlElement:
    return html.fromstring(render_chapter_html(tmp_path, fragment))


def first_fragment_paragraph(doc: html.HtmlElement) -> html.HtmlElement:
    return doc.xpath("//div[contains(@class, 'tei-fragment')]//p")[0]


def test_title_renders_as_inline_cite_with_metadata(tmp_path: Path) -> None:
    html_source = render_chapter_html(
        tmp_path,
        "<p>Il cite <title level='m' type='main'>Les Provinciales</title>.</p>",
    )
    doc = html.fromstring(html_source)
    paragraph = first_fragment_paragraph(doc)
    cite = paragraph.xpath(".//cite[contains(@class, 'tei-title')]")[0]

    assert paragraph.xpath("count(.//div | .//blockquote)") == 0
    assert cite.text_content() == "Les Provinciales"
    assert cite.get("data-level") == "m"
    assert cite.get("data-type") == "main"
    assert "Il cite Les Provinciales." in paragraph.text_content()


def test_foreign_preserves_xml_lang_inline(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        '<p>Une formule <foreign xml:lang="la">in medias res</foreign>.</p>',
    )
    paragraph = first_fragment_paragraph(doc)
    foreign = paragraph.xpath(".//span[contains(@class, 'foreign')]")[0]

    assert paragraph.xpath("count(.//div | .//blockquote)") == 0
    assert foreign.text_content() == "in medias res"
    assert foreign.get("lang") == "la"


def test_terms_and_names_render_inline_with_classes_and_data_ref(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <p><persName ref="#pascal">Pascal</persName> séjourne à <placeName ref="#port-royal">Port-Royal</placeName>.</p>
        <p>Le <term ref="#jansenisme">jansénisme</term> est discuté avec <name ref="#nom-simple">un nom</name> et <orgName ref="#oratoire">l'Oratoire</orgName>.</p>
        """,
    )

    assert doc.xpath("string(//span[contains(@class, 'pers-name')])") == "Pascal"
    assert doc.xpath("//span[contains(@class, 'pers-name')]/@data-ref") == ["#pascal"]
    assert doc.xpath("string(//span[contains(@class, 'place-name')])") == "Port-Royal"
    assert doc.xpath("//span[contains(@class, 'place-name')]/@data-ref") == ["#port-royal"]
    assert doc.xpath("string(//span[contains(@class, 'term')])") == "jansénisme"
    assert doc.xpath("//span[contains(@class, 'term')]/@data-ref") == ["#jansenisme"]
    assert doc.xpath("string(//span[@class='name'])") == "un nom"
    assert doc.xpath("//span[@class='name']/@data-ref") == ["#nom-simple"]
    assert doc.xpath("string(//span[contains(@class, 'org-name')])") == "l'Oratoire"
    assert doc.xpath("//span[contains(@class, 'org-name')]/@data-ref") == ["#oratoire"]


def test_ref_and_ptr_render_visible_links(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <p>Voir <ref target="#note-source">la source</ref>.</p>
        <p>Voir aussi <ptr target="https://example.org/document"/>.</p>
        """,
    )

    internal = doc.xpath("//a[text()='la source']")[0]
    external = doc.xpath("//a[text()='https://example.org/document']")[0]

    assert internal.get("href") == "#note-source"
    assert internal.get("target") is None
    assert internal.get("rel") is None
    assert external.get("href") == "https://example.org/document"
    assert external.get("target") == "_blank"
    assert external.get("rel") == "noopener"


def test_line_break_and_page_break_are_distinct_inline_markers(tmp_path: Path) -> None:
    html_source = render_chapter_html(
        tmp_path,
        """
        <p>ligne 1<lb/>ligne 2</p>
        <p>Texte<pb n="12"/>suite.</p>
        """,
    )
    doc = html.fromstring(html_source)
    paragraphs = doc.xpath("//div[contains(@class, 'tei-fragment')]//p")
    page_break = paragraphs[1].xpath(".//span[contains(@class, 'page-break')]")[0]

    # Choix minimal : lb reste un saut de ligne, pb devient un marqueur inline
    # porteur du numero de page, afin de ne pas confondre les deux phenomenes.
    assert paragraphs[0].xpath("count(.//br)") == 1
    assert paragraphs[1].xpath("count(.//br)") == 0
    assert page_break.get("data-n") == "12"
    assert page_break.text_content() == "[p. 12]"
    assert "Texte[p. 12]suite." in paragraphs[1].text_content()
    assert "id=\"\"" not in html_source
    assert "data-n=\"\"" not in html_source


def test_date_num_and_label_render_inline_with_useful_attributes(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <p>Le <date when="1670">XVIIe siècle</date>.</p>
        <p><label>Fig. 1</label> <num type="cardinal" value="12">douze</num></p>
        """,
    )

    date = doc.xpath("//time[contains(@class, 'tei-date')]")[0]
    label = doc.xpath("//span[contains(@class, 'tei-label')]")[0]
    num = doc.xpath("//span[contains(@class, 'tei-num')]")[0]

    assert date.text_content() == "XVIIe siècle"
    assert date.get("datetime") == "1670"
    assert label.text_content() == "Fig. 1"
    assert num.text_content() == "douze"
    assert num.get("data-type") == "cardinal"
    assert num.get("data-value") == "12"


def test_cit_inside_list_item_stays_inline(tmp_path: Path) -> None:
    html_source = render_chapter_html(
        tmp_path,
        """
        <list>
          <item>
            Élément avec <cit><quote>citation brève</quote><bibl>Source brève</bibl></cit>.
          </item>
        </list>
        """,
    )
    doc = html.fromstring(html_source)
    item = doc.xpath("//div[contains(@class, 'tei-fragment')]//li")[0]

    assert item.xpath("count(.//div[contains(@class, 'cit-block')])") == 0
    assert item.xpath("count(.//span[contains(@class, 'cit-inline')])") == 1
    assert item.xpath("string(.//q)") == "citation brève"
    assert item.xpath("string(.//cite[contains(@class, 'bibl-ref')])") == "Source brève"
    item_text = " ".join(item.text_content().split())
    assert "Élément avec" in item_text
    assert "citation brève" in item_text
    assert "Source brève" in item_text


def test_title_inside_bibl_does_not_nest_cite_elements(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <listBibl>
          <bibl>Auteur, <title level="m" type="main">Un titre</title>, 2020.</bibl>
        </listBibl>
        """,
    )
    bibl_item = doc.xpath("//section[contains(@class, 'bibliography-block')]//li")[0]
    title = bibl_item.xpath(".//span[contains(@class, 'tei-title')]")[0]

    assert bibl_item.xpath("count(.//cite//cite)") == 0
    assert bibl_item.xpath("count(.//cite[contains(@class, 'tei-title')])") == 0
    assert title.text_content() == "Un titre"
    assert title.get("data-level") == "m"
    assert title.get("data-type") == "main"
    assert "Auteur, Un titre, 2020." in bibl_item.text_content()
