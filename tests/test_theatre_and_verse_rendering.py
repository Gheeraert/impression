from __future__ import annotations

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
      <titleStmt><title type='main'>Livre théâtre et vers</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre théâtre'>
        <body>
          <div type='section1'>
            <head>Section théâtre</head>
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
    page_html = (result.output_dir / "01-chapitre-theatre.html").read_text(encoding="utf-8")
    return html.fromstring(page_html)


def test_standalone_speaker_renders_as_labeled_paragraph(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <sp>
          <speaker>Locuteur 1</speaker>
          <p>Réplique du locuteur.</p>
        </sp>
        """,
    )

    speaker = doc.xpath("//p[contains(@class, 'speaker')]")
    assert len(speaker) == 1
    assert speaker[0].text_content().strip() == "Locuteur 1"


def test_standalone_stage_direction_renders_as_own_block(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <sp><p>Première réplique.</p></sp>
        <stage>Didascalie</stage>
        <sp><p>Seconde réplique.</p></sp>
        """,
    )

    stage = doc.xpath("//p[contains(@class, 'stage-direction') and not(contains(@class, 'stage-direction-inline'))]")
    assert len(stage) == 1
    assert stage[0].text_content().strip() == "Didascalie"


def test_inline_stage_direction_renders_as_span_within_paragraph(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <sp><p>Avant <stage>(un geste)</stage> après.</p></sp>
        """,
    )

    inline_stage = doc.xpath("//span[contains(@class, 'stage-direction-inline')]")
    assert len(inline_stage) == 1
    assert inline_stage[0].text_content().strip() == "(un geste)"
    # Le marqueur reste dans le paragraphe, pas dans un bloc à part.
    assert inline_stage[0].getparent().tag == "p"


def test_caesura_renders_as_marker_span_inside_verse_line(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <lg>
          <l>Premier hémistiche <caesura/>second hémistiche</l>
        </lg>
        """,
    )

    verse_line = doc.xpath("//div[contains(@class, 'verse-line')]")[0]
    caesura = verse_line.xpath(".//span[contains(@class, 'caesura')]")
    assert len(caesura) == 1
    assert "Premier hémistiche" in verse_line.text_content()
    assert "second hémistiche" in verse_line.text_content()


def test_verse_number_is_leading_child_of_verse_line_for_margin_display(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <lg>
          <l n="1"><num>(1)</num> Premier vers numéroté.</l>
          <l>Second vers, sans numéro.</l>
        </lg>
        """,
    )

    verse_lines = doc.xpath("//div[contains(@class, 'verse-line')]")
    assert len(verse_lines) == 2
    first_child = verse_lines[0][0]
    assert first_child.get("class") == "tei-num"
    assert first_child.text_content().strip() == "(1)"
    assert not verse_lines[1].xpath(".//*[contains(@class, 'tei-num')]")


def test_sp_wraps_each_speech_in_its_own_div_for_spacing(tmp_path: Path) -> None:
    """Vérification humaine directe, 2026-08-06 : <sp> retombait jusqu'ici
    sur le comportement XSLT par défaut (aucune enveloppe, simple
    récursion), laissant deux répliques consécutives se toucher sans
    séparation visuelle."""
    doc = render_chapter(
        tmp_path,
        """
        <sp><speaker>Locuteur 1</speaker><p>Premiere replique.</p></sp>
        <sp><speaker>Locuteur 2</speaker><p>Seconde replique.</p></sp>
        """,
    )

    speeches = doc.xpath("//div[contains(@class, 'speech')]")
    assert len(speeches) == 2
    assert "Premiere replique" in speeches[0].text_content()
    assert "Seconde replique" in speeches[1].text_content()


def test_theatre_verse_dialogue_l_directly_in_sp_renders_as_verse_lines(tmp_path: Path) -> None:
    """<l> directement enfant de <sp>, sans <lg> intermédiaire (théâtre en
    vers, cas authentique constaté sur *Dissimuler pour mieux régner*,
    chapitre "Secrets de théâtre") — doit rendre chaque vers comme une
    ligne de vers à part, exactement comme un <l> dans un <lg> autonome."""
    doc = render_chapter(
        tmp_path,
        """
        <sp>
          <speaker>Maguelonne</speaker>
          <stage>riant</stage>
          <l>Monsieur, vous m'avez l'air d'un libertin parfait !</l>
        </sp>
        """,
    )

    speech = doc.xpath("//div[contains(@class, 'speech')]")
    assert len(speech) == 1
    verse_lines = speech[0].xpath(".//div[contains(@class, 'verse-line')]")
    assert len(verse_lines) == 1
    assert "libertin parfait" in verse_lines[0].text_content()


def test_poem_block_css_rule_exists(tmp_path: Path) -> None:
    """<lg> avait un template XSLT (poem-block) mais aucune règle CSS
    associée : un simple <div> sans marge, indiscernable du texte
    environnant."""
    doc = render_chapter(tmp_path, "<lg><l>Un vers.</l></lg>")

    css_path = doc.xpath("//link[@rel='stylesheet']/@href")
    assert css_path, "la page doit référencer la feuille de style du site"
    css_content = (tmp_path / "site" / css_path[0]).read_text(encoding="utf-8")
    assert ".poem-block" in css_content


def test_inline_citation_quotes_are_not_duplicated_by_browser_default(tmp_path: Path) -> None:
    doc = render_chapter(
        tmp_path,
        """
        <p>Comme le disait Jean, <cit><quote>"le renard..." (La Fontaine)</quote></cit>, blah.</p>
        """,
    )

    css_path = doc.xpath("//link[@rel='stylesheet']/@href")
    assert css_path, "la page doit référencer la feuille de style du site"

    css_content = (tmp_path / "site" / css_path[0]).read_text(encoding="utf-8")
    assert ".cit-inline q" in css_content
    assert "quotes: none" in css_content

    quote = doc.xpath("//span[contains(@class, 'cit-inline')]//q")
    assert len(quote) == 1
    # Les guillemets déjà présents dans le texte source sont conservés tels quels.
    assert quote[0].text_content().strip() == '"le renard..." (La Fontaine)'
