from __future__ import annotations

from pathlib import Path

from lxml import html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder


def render_note_page(tmp_path: Path, fragment: str) -> html.HtmlElement:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre notes</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre notes'>
        <body>
          <div type='section1'>
            <head>Section notes</head>
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
    page_html = (result.output_dir / "01-chapitre-notes.html").read_text(encoding="utf-8")
    return html.fromstring(page_html)


def first_endnote(doc: html.HtmlElement) -> html.HtmlElement:
    return doc.xpath("//section[contains(@class, 'endnotes')]//li")[0]


def test_note_preserves_italic_inline_markup(tmp_path: Path) -> None:
    doc = render_note_page(
        tmp_path,
        '<p>Texte avec note<note>Voir <hi rend="italic">Passio</hi> dans le manuscrit.</note>.</p>',
    )
    paragraph = doc.xpath("//div[contains(@class, 'tei-fragment')]//p")[0]
    note = first_endnote(doc)

    assert paragraph.xpath("count(.//sup[contains(@class, 'note-ref')])") == 1
    assert note.xpath("string(.//em)") == "Passio"
    assert "Voir Passio dans le manuscrit." in note.text_content()


def test_note_preserves_small_caps_markup(tmp_path: Path) -> None:
    doc = render_note_page(
        tmp_path,
        '<p>Texte<note>Comparer avec <hi rend="small-caps">Port-Royal</hi>.</note></p>',
    )
    note = first_endnote(doc)
    smallcaps = note.xpath(".//span[contains(@class, 'smallcaps')]")[0]

    assert smallcaps.text_content() == "Port-Royal"


def test_note_preserves_superscript_and_subscript(tmp_path: Path) -> None:
    doc = render_note_page(
        tmp_path,
        '<p>Texte<note>Voir XVII<hi rend="sup">e</hi> siècle et H<hi rend="sub">2</hi>O.</note></p>',
    )
    note = first_endnote(doc)

    assert note.xpath("string(.//sup[contains(@class, 'tei-sup')])") == "e"
    assert note.xpath("string(.//sub[contains(@class, 'tei-sub')])") == "2"
    assert "Voir XVIIe siècle et H2O." in note.text_content()


def test_note_preserves_combined_small_caps_italic_regardless_of_order(tmp_path: Path) -> None:
    doc = render_note_page(
        tmp_path,
        '<p>Texte<note><hi rend="small-caps italic">Port-Royal</hi> et <hi rend="italic small-caps">Solitaires</hi>.</note></p>',
    )
    note = first_endnote(doc)
    spans = note.xpath(".//span[contains(@class, 'smallcaps')]")

    assert [span.xpath("string(.//em)") for span in spans] == ["Port-Royal", "Solitaires"]


def test_note_preserves_scholarly_inline_elements(tmp_path: Path) -> None:
    doc = render_note_page(
        tmp_path,
        '<p>Texte<note>Voir <title>Les Provinciales</title>, <persName ref="#pascal">Pascal</persName>, <ref target="#chapitre-2">chapitre II</ref>.</note></p>',
    )
    note = first_endnote(doc)

    assert note.xpath("string(.//cite[contains(@class, 'tei-title')])") == "Les Provinciales"
    assert note.xpath("string(.//span[contains(@class, 'pers-name')])") == "Pascal"
    assert note.xpath(".//span[contains(@class, 'pers-name')]/@data-ref") == ["#pascal"]
    assert note.xpath("string(.//a[@href='#chapitre-2'])") == "chapitre II"


def test_note_preserves_citation_and_bibliographic_reference(tmp_path: Path) -> None:
    doc = render_note_page(
        tmp_path,
        '<p>Texte<note><cit><quote>citation brève</quote><bibl>Source, p. 12</bibl></cit></note></p>',
    )
    note = first_endnote(doc)

    assert note.xpath("count(.//div[contains(@class, 'cit-block')])") == 0
    assert note.xpath("count(.//span[contains(@class, 'cit-inline')])") == 1
    assert note.xpath("string(.//q)") == "citation brève"
    assert note.xpath("string(.//cite[contains(@class, 'bibl-ref')])") == "Source, p. 12"


def test_note_receives_final_french_typography(tmp_path: Path) -> None:
    doc = render_note_page(
        tmp_path,
        "<p>Texte<note>l'homme dit « bonjour » : XVIIe siècle !</note></p>",
    )
    note_html = html.tostring(first_endnote(doc), encoding="unicode")

    assert "l’homme" in note_html
    assert "«\u202fbonjour\u202f»" in note_html
    assert "\u202f:" in note_html
    assert "XVII<sup>e</sup> siècle" in note_html
    assert "\u202f!" in note_html
