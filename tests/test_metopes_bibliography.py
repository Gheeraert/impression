from __future__ import annotations

from pathlib import Path

from lxml import html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder


def render_bibliography_html(tmp_path: Path, fragment: str) -> str:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre bibliographie</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre bibliographie'>
        <body>
          <div type='section1'>
            <head>Section bibliographie</head>
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
    return (result.output_dir / "01-chapitre-bibliographie.html").read_text(encoding="utf-8")


def render_bibliography(tmp_path: Path, fragment: str) -> html.HtmlElement:
    return html.fromstring(render_bibliography_html(tmp_path, fragment))


def visible_text(element: html.HtmlElement) -> str:
    return " ".join(element.text_content().split())


def test_biblstruct_monograph_renders_structured_entry(tmp_path: Path) -> None:
    html_source = render_bibliography_html(
        tmp_path,
        """
        <listBibl>
          <biblStruct xml:id="bibl-pascal-provinciales">
            <monogr>
              <author>Pascal, Blaise</author>
              <title level="m">Les Provinciales</title>
              <imprint>
                <pubPlace>Paris</pubPlace>
                <publisher>Guillaume Desprez</publisher>
                <date when="1657">1657</date>
              </imprint>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )
    doc = html.fromstring(html_source)
    entry = doc.xpath("//li[contains(@class, 'bibl-entry')]")[0]

    assert entry.get("id") == "bibl-pascal-provinciales"
    assert entry.xpath("string(.//span[contains(@class, 'bibl-author')])") == "Pascal, Blaise"
    assert entry.xpath("string(.//cite[contains(@class, 'bibl-title')])") == "Les Provinciales"
    assert entry.xpath(".//cite[contains(@class, 'bibl-title')]/@data-level") == ["m"]
    assert "Paris" in entry.text_content()
    assert "Guillaume Desprez" in entry.text_content()
    assert entry.xpath("string(.//time[@datetime='1657'])") == "1657"
    entry_text = visible_text(entry)
    assert entry_text == "Pascal, Blaise, Les Provinciales, Paris, Guillaume Desprez, 1657."
    assert ", ," not in entry_text
    assert ",." not in entry_text
    assert 'id=""' not in html_source


def test_biblstruct_contribution_in_collective_volume(tmp_path: Path) -> None:
    doc = render_bibliography(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <analytic>
              <author>Dupont, Jeanne</author>
              <title level="a">Port-Royal et la lecture</title>
            </analytic>
            <monogr>
              <editor>Martin, Paul</editor>
              <title level="m">Lectures classiques</title>
              <imprint>
                <pubPlace>Rouen</pubPlace>
                <publisher>PURH</publisher>
                <date when="2020">2020</date>
                <biblScope unit="page" from="25" to="48">p. 25-48</biblScope>
              </imprint>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )
    entry = doc.xpath("//li[contains(@class, 'bibl-entry')]")[0]

    assert entry.xpath("string(.//span[contains(@class, 'bibl-author')])") == "Dupont, Jeanne"
    assert entry.xpath("string(.//cite[contains(@class, 'bibl-title') and @data-level='a'])") == "Port-Royal et la lecture"
    assert entry.xpath("string(.//span[contains(@class, 'bibl-editor')])") == "Martin, Paul"
    assert "(dir.)" in entry.text_content()
    assert entry.xpath("string(.//cite[contains(@class, 'bibl-title') and @data-level='m'])") == "Lectures classiques"
    assert "Rouen" in entry.text_content()
    assert "PURH" in entry.text_content()
    assert "2020" in entry.text_content()
    assert entry.xpath("string(.//span[contains(@class, 'bibl-scope') and @data-unit='page'])") == "p. 25-48"
    entry_text = visible_text(entry)
    assert entry_text == "Dupont, Jeanne, « Port-Royal et la lecture », dans Martin, Paul (dir.), Lectures classiques, Rouen, PURH, 2020, p. 25-48."
    assert ", ," not in entry_text
    assert ",." not in entry_text


def test_biblstruct_journal_article_renders_core_fields(tmp_path: Path) -> None:
    doc = render_bibliography(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <analytic>
              <author>Durand, Marie</author>
              <title level="a">La grace et le signe</title>
            </analytic>
            <monogr>
              <title level="j">Revue d'histoire litteraire de la France</title>
              <imprint>
                <date when="2019">2019</date>
                <biblScope unit="volume">119</biblScope>
                <biblScope unit="issue">3</biblScope>
                <biblScope unit="page">p. 511-530</biblScope>
              </imprint>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )
    entry = doc.xpath("//li[contains(@class, 'bibl-entry')]")[0]

    assert entry.xpath("string(.//span[contains(@class, 'bibl-author')])") == "Durand, Marie"
    assert entry.xpath("string(.//cite[contains(@class, 'bibl-title') and @data-level='a'])") == "La grace et le signe"
    assert entry.xpath("string(.//cite[contains(@class, 'bibl-title') and @data-level='j'])") == "Revue d’histoire litteraire de la France"
    assert "2019" in entry.text_content()
    assert entry.xpath("string(.//span[contains(@class, 'bibl-scope') and @data-unit='volume'])") == "119"
    assert entry.xpath("string(.//span[contains(@class, 'bibl-scope') and @data-unit='issue'])") == "3"
    assert entry.xpath("string(.//span[contains(@class, 'bibl-scope') and @data-unit='page'])") == "p. 511-530"
    entry_text = visible_text(entry)
    assert entry_text == "Durand, Marie, « La grace et le signe », Revue d’histoire litteraire de la France, 119, no 3, 2019, p. 511-530."
    assert ", ," not in entry_text
    assert ",." not in entry_text


def test_biblstruct_idno_renders_doi_uri_and_plain_identifiers(tmp_path: Path) -> None:
    html_source = render_bibliography_html(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <monogr>
              <author>Nom, Auteur</author>
              <title level="m">Livre avec identifiants</title>
              <imprint>
                <publisher>PURH</publisher>
                <date when="2022">2022</date>
              </imprint>
              <idno type="ISBN">979-10-240-0000-0</idno>
              <idno type="DOI">10.4000/books.purh.1234</idno>
              <idno type="URI">https://books.openedition.org/purh/1234</idno>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )
    doc = html.fromstring(html_source)
    entry = doc.xpath("//li[contains(@class, 'bibl-entry')]")[0]
    doi = entry.xpath(".//a[contains(@class, 'bibl-idno') and @data-type='DOI']")[0]
    uri = entry.xpath(".//a[contains(@class, 'bibl-idno') and @data-type='URI']")[0]

    assert "ISBN 979-10-240-0000-0" in entry.text_content()
    assert doi.get("href") == "https://doi.org/10.4000/books.purh.1234"
    assert doi.get("target") == "_blank"
    assert doi.get("rel") == "noopener"
    assert uri.get("href") == "https://books.openedition.org/purh/1234"
    assert uri.get("target") == "_blank"
    assert uri.get("rel") == "noopener"
    entry_text = visible_text(entry)
    assert "ISBN 979-10-240-0000-0. DOI 10.4000/books.purh.1234. URI https://books.openedition.org/purh/1234." in entry_text
    assert 'href=""' not in html_source
    assert 'data-type=""' not in html_source


def test_biblstruct_inside_note_keeps_note_mechanics(tmp_path: Path) -> None:
    doc = render_bibliography(
        tmp_path,
        """
        <p>Texte<note>
          <listBibl>
            <biblStruct>
              <monogr>
                <author>Pascal, Blaise</author>
                <title level="m">Les Provinciales</title>
                <imprint>
                  <date when="1657">1657</date>
                </imprint>
              </monogr>
            </biblStruct>
          </listBibl>
        </note></p>
        """,
    )
    paragraph = doc.xpath("//div[contains(@class, 'tei-fragment')]//p")[0]
    note = doc.xpath("//section[contains(@class, 'endnotes')]//li")[0]

    assert paragraph.xpath("count(.//sup[contains(@class, 'note-ref')])") == 1
    assert note.xpath("string(.//span[contains(@class, 'bibl-author')])") == "Pascal, Blaise"
    assert note.xpath("string(.//cite[contains(@class, 'bibl-title')])") == "Les Provinciales"
    assert "1657" in note.text_content()


def test_simple_bibl_still_avoids_nested_cites(tmp_path: Path) -> None:
    doc = render_bibliography(
        tmp_path,
        """
        <listBibl>
          <bibl>Auteur, <title>Un titre</title>, 2020.</bibl>
        </listBibl>
        """,
    )
    entry = doc.xpath("//section[contains(@class, 'bibliography-block')]//ol[contains(@class, 'bibl-list')]/li")[0]

    assert "Auteur, Un titre, 2020." in entry.text_content()
    assert entry.xpath("count(.//cite//cite)") == 0
    assert entry.xpath("string(.//span[contains(@class, 'tei-title')])") == "Un titre"


def test_biblstruct_with_missing_fields_has_no_orphan_punctuation(tmp_path: Path) -> None:
    doc = render_bibliography(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <monogr>
              <title level="m">Livre sans auteur ni imprint</title>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )
    entry = doc.xpath("//li[contains(@class, 'bibl-entry')]")[0]
    entry_text = visible_text(entry)

    assert entry_text == "Livre sans auteur ni imprint."
    assert not entry_text.startswith(",")
    assert ", ," not in entry_text
    assert ",." not in entry_text
    assert "()" not in entry_text


def test_biblstruct_contribution_without_editor_has_no_empty_director_marker(tmp_path: Path) -> None:
    doc = render_bibliography(
        tmp_path,
        """
        <listBibl>
          <biblStruct>
            <analytic>
              <author>Auteur, Exemple</author>
              <title level="a">Chapitre sans editeur</title>
            </analytic>
            <monogr>
              <title level="m">Volume sans directeur</title>
              <imprint>
                <date when="2021">2021</date>
              </imprint>
            </monogr>
          </biblStruct>
        </listBibl>
        """,
    )
    entry = doc.xpath("//li[contains(@class, 'bibl-entry')]")[0]
    entry_text = visible_text(entry)

    assert entry_text == "Auteur, Exemple, « Chapitre sans editeur », dans Volume sans directeur, 2021."
    assert "(dir.)" not in entry_text
    assert ", ," not in entry_text
    assert ",." not in entry_text
