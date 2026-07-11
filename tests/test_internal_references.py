from __future__ import annotations

from pathlib import Path

from lxml import html

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder


def build_reference_site(tmp_path: Path, body: str) -> Path:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre references</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      {body}
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )

    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))
    return result.output_dir


def content_pages(output_dir: Path) -> list[Path]:
    return sorted(path for path in output_dir.glob("*.html") if path.name != "index.html")


def parse_page(path: Path) -> html.HtmlElement:
    return html.fromstring(path.read_text(encoding="utf-8"))


def test_internal_ref_to_other_page_is_rewritten(tmp_path: Path) -> None:
    output_dir = build_reference_site(
        tmp_path,
        """
        <group xml:id="intro" type="chapter" data-page-title="Introduction">
          <body>
            <div type="section1">
              <head>Introduction</head>
              <p>Voir <ref target="#section-chapitre-2">la section du chapitre 2</ref>.</p>
            </div>
          </body>
        </group>
        <group xml:id="chapitre" type="chapter" data-page-title="Chapitre">
          <body>
            <div xml:id="section-chapitre-2" type="section1">
              <head>Section du chapitre 2</head>
              <p>Texte cible.</p>
            </div>
          </body>
        </group>
        """,
    )
    first_page, second_page = content_pages(output_dir)
    doc = parse_page(first_page)
    link = doc.xpath("//a[normalize-space(.)='la section du chapitre 2']")[0]

    assert link.get("href") == f"{second_page.name}#section-chapitre-2"


def test_internal_ref_to_same_page_stays_fragment_only(tmp_path: Path) -> None:
    output_dir = build_reference_site(
        tmp_path,
        """
        <group xml:id="intro" type="chapter" data-page-title="Introduction">
          <body>
            <div type="section1">
              <head>Introduction</head>
              <p>Voir <ref target="#section-locale">la section locale</ref>.</p>
              <div xml:id="section-locale" type="section2">
                <head>Section locale</head>
                <p>Texte.</p>
              </div>
            </div>
          </body>
        </group>
        """,
    )
    first_page = content_pages(output_dir)[0]
    doc = parse_page(first_page)
    link = doc.xpath("//a[normalize-space(.)='la section locale']")[0]

    assert link.get("href") == "#section-locale"


def test_missing_internal_ref_target_is_left_unchanged(tmp_path: Path) -> None:
    output_dir = build_reference_site(
        tmp_path,
        """
        <group xml:id="intro" type="chapter" data-page-title="Introduction">
          <body>
            <div type="section1">
              <head>Introduction</head>
              <p>Voir <ref target="#cible-absente">une cible absente</ref>.</p>
            </div>
          </body>
        </group>
        """,
    )
    first_page = content_pages(output_dir)[0]
    doc = parse_page(first_page)
    link = doc.xpath("//a[normalize-space(.)='une cible absente']")[0]

    assert link.get("href") == "#cible-absente"


def test_external_ref_is_not_rewritten(tmp_path: Path) -> None:
    output_dir = build_reference_site(
        tmp_path,
        """
        <group xml:id="intro" type="chapter" data-page-title="Introduction">
          <body>
            <div type="section1">
              <head>Introduction</head>
              <p><ref target="https://example.org">lien externe</ref></p>
            </div>
          </body>
        </group>
        """,
    )
    first_page = content_pages(output_dir)[0]
    doc = parse_page(first_page)
    link = doc.xpath("//a[normalize-space(.)='lien externe']")[0]

    assert link.get("href") == "https://example.org"
    assert link.get("target") == "_blank"
    assert link.get("rel") == "noopener"


def test_internal_ptr_to_other_page_is_rewritten(tmp_path: Path) -> None:
    output_dir = build_reference_site(
        tmp_path,
        """
        <group xml:id="intro" type="chapter" data-page-title="Introduction">
          <body>
            <div type="section1">
              <head>Introduction</head>
              <p>Voir aussi <ptr target="#section-chapitre-2"/>.</p>
            </div>
          </body>
        </group>
        <group xml:id="chapitre" type="chapter" data-page-title="Chapitre">
          <body>
            <div xml:id="section-chapitre-2" type="section1">
              <head>Section du chapitre 2</head>
              <p>Texte cible.</p>
            </div>
          </body>
        </group>
        """,
    )
    first_page, second_page = content_pages(output_dir)
    doc = parse_page(first_page)
    link = doc.xpath("//a[contains(@class, 'tei-ptr')]")[0]

    assert link.get("href") == f"{second_page.name}#section-chapitre-2"
    assert "#section-chapitre-2" in link.text_content()


def test_note_links_are_not_rewritten(tmp_path: Path) -> None:
    output_dir = build_reference_site(
        tmp_path,
        """
        <group xml:id="intro" type="chapter" data-page-title="Introduction">
          <body>
            <div type="section1">
              <head>Introduction</head>
              <p>Texte<note>Une note.</note></p>
            </div>
          </body>
        </group>
        """,
    )
    first_page = content_pages(output_dir)[0]
    doc = parse_page(first_page)

    call_hrefs = doc.xpath("//sup[contains(@class, 'note-ref')]/a/@href")
    assert len(call_hrefs) == 1
    # L'ancre technique est le xml:id stable de la note, jamais son @n.
    note_anchor = call_hrefs[0]
    assert note_anchor.startswith("#") and "/" not in note_anchor and ".html" not in note_anchor
    note_id = note_anchor[1:]
    assert doc.xpath(f"//section[contains(@class, 'endnotes')]//li[@id='{note_id}']")
    assert doc.xpath(f"//section[contains(@class, 'endnotes')]//a[@href='#noteref-{note_id}']")
    assert doc.xpath(f"//sup[contains(@class, 'note-ref') and @id='noteref-{note_id}']")


def test_internal_ref_to_other_page_group_id_uses_page_href_without_fragment(tmp_path: Path) -> None:
    output_dir = build_reference_site(
        tmp_path,
        """
        <group xml:id="intro" type="chapter" data-page-title="Introduction">
          <body>
            <div type="section1">
              <head>Introduction</head>
              <p>Voir <ref target="#chapitre">le chapitre</ref>.</p>
            </div>
          </body>
        </group>
        <group xml:id="chapitre" type="chapter" data-page-title="Chapitre">
          <body>
            <div type="section1">
              <head>Chapitre</head>
              <p>Texte cible.</p>
            </div>
          </body>
        </group>
        """,
    )
    first_page, second_page = content_pages(output_dir)
    doc = parse_page(first_page)
    link = doc.xpath("//a[normalize-space(.)='le chapitre']")[0]

    assert link.get("href") == second_page.name


def test_internal_ptr_to_other_page_group_id_uses_page_href_without_fragment(tmp_path: Path) -> None:
    output_dir = build_reference_site(
        tmp_path,
        """
        <group xml:id="intro" type="chapter" data-page-title="Introduction">
          <body>
            <div type="section1">
              <head>Introduction</head>
              <p>Voir aussi <ptr target="#chapitre"/>.</p>
            </div>
          </body>
        </group>
        <group xml:id="chapitre" type="chapter" data-page-title="Chapitre">
          <body>
            <div type="section1">
              <head>Chapitre</head>
              <p>Texte cible.</p>
            </div>
          </body>
        </group>
        """,
    )
    first_page, second_page = content_pages(output_dir)
    doc = parse_page(first_page)
    link = doc.xpath("//a[contains(@class, 'tei-ptr')]")[0]

    assert link.get("href") == second_page.name


def test_internal_ref_to_current_page_group_id_stays_fragment_only(tmp_path: Path) -> None:
    output_dir = build_reference_site(
        tmp_path,
        """
        <group xml:id="intro" type="chapter" data-page-title="Introduction">
          <body>
            <div type="section1">
              <head>Introduction</head>
              <p>Voir <ref target="#intro">cette introduction</ref>.</p>
            </div>
          </body>
        </group>
        """,
    )
    first_page = content_pages(output_dir)[0]
    doc = parse_page(first_page)
    link = doc.xpath("//a[normalize-space(.)='cette introduction']")[0]

    assert link.get("href") == "#intro"
    assert doc.xpath("//*[@id='intro']")
    assert doc.xpath("//header[contains(@class, 'page-header') and @id='intro']")
