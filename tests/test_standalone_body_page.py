from __future__ import annotations

"""Tests de prise en charge des unités TEI autonomes (<text><body> sans <group>).

Contexte : un document produit par Mini-Métopes est un TEI valide qui place
tout son contenu éditorial directement dans <text><body>, sans <group>. Avant
ce correctif, SiteStructureBuilder.build() ne trouvait pas de <group> racine
et retournait un site sans aucune page de contenu, alors que le document
contient bien du texte exploitable.
"""

from pathlib import Path

import pytest
from lxml import etree, html

from purh_site.config import BuildConfig
from purh_site.normalizer import TeiNormalizer
from purh_site.site_builder import SiteBuilder
from purh_site.site_structure import SiteStructureBuilder
from purh_site.tei_loader import TeiLoader
from purh_site.utils import NSMAP, XML_NS

FIXTURE_PATH = Path("tests/fixtures/minimetopes/conclusion_racine_queer_styles_natifs_minimetopes.xml")
XMLID = f"{{{XML_NS}}}id"


def load_and_normalize(path: Path) -> etree._ElementTree:
    tree, _ = TeiLoader().load_single(path)
    TeiNormalizer().normalize(tree)
    return tree


# ---------------------------------------------------------------------------
# Fixture et structure
# ---------------------------------------------------------------------------

def test_fixture_exists_and_contains_a_body_without_group() -> None:
    assert FIXTURE_PATH.exists()
    tree = etree.parse(str(FIXTURE_PATH))
    assert tree.xpath("/tei:TEI/tei:text/tei:body", namespaces=NSMAP)
    assert not tree.xpath("/tei:TEI/tei:text/tei:group", namespaces=NSMAP)


def test_standalone_body_receives_a_stable_xml_id_after_normalization() -> None:
    tree = load_and_normalize(FIXTURE_PATH)
    bodies = tree.xpath("/tei:TEI/tei:text/tei:body", namespaces=NSMAP)
    assert len(bodies) == 1
    assert bodies[0].get(XMLID)


def test_structure_builder_produces_exactly_one_page_and_one_nav_item() -> None:
    tree = load_and_normalize(FIXTURE_PATH)
    site_meta, pages, nav = SiteStructureBuilder().build(tree)

    assert len(pages) == 1
    assert len(nav) == 1
    page = pages[0]
    assert page.title == "Racine queer : des styles natifs"
    assert page.subtitle == "Conclusion"
    assert page.sequence == 1
    assert nav[0].href == page.file_name
    assert site_meta.title == "Racine queer : des styles natifs"


def test_structure_builder_reports_standalone_body_diagnostic() -> None:
    tree = load_and_normalize(FIXTURE_PATH)
    builder = SiteStructureBuilder()
    builder.build(tree)

    assert any("autonome" in message for message in builder.last_diagnostics)


def test_structure_builder_reports_no_content_when_neither_group_nor_body_exists() -> None:
    xml = """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Sans contenu</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text/>
</TEI>
"""
    tree = etree.ElementTree(etree.fromstring(xml.encode("utf-8")))
    TeiNormalizer().normalize(tree)
    builder = SiteStructureBuilder()
    _, pages, nav = builder.build(tree)

    assert pages == []
    assert nav == []
    assert any("Aucun group" in message for message in builder.last_diagnostics)


# ---------------------------------------------------------------------------
# Génération réelle du site
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output_dir = tmp_path_factory.mktemp("minimetopes_site")
    result = SiteBuilder().build_from_master(FIXTURE_PATH, BuildConfig(output_dir=output_dir))
    return result.output_dir


def content_pages(output_dir: Path) -> list[Path]:
    return sorted(path for path in output_dir.glob("*.html") if path.name != "index.html")


def test_site_generates_index_and_exactly_one_content_page(built_site: Path) -> None:
    assert (built_site / "index.html").exists()
    pages = content_pages(built_site)
    assert len(pages) == 1


def test_content_page_contains_first_paragraph(built_site: Path) -> None:
    page = content_pages(built_site)[0]
    text = page.read_text(encoding="utf-8")
    assert "En général, le confident attire peu l’attention." in text


def test_content_page_contains_section_headings(built_site: Path) -> None:
    doc = html.fromstring(content_pages(built_site)[0].read_text(encoding="utf-8"))
    headings = [h.text_content().strip() for h in doc.xpath("//h2 | //h3 | //h4")]
    assert "Le confident, une discrétion trompeuse" in headings
    assert "Styles natifs et voix secondaires" in headings
    assert "Pour une lecture queer des styles natifs" in headings


def test_content_page_contains_versified_quotation(built_site: Path) -> None:
    doc = html.fromstring(content_pages(built_site)[0].read_text(encoding="utf-8"))
    lines = [l.text_content().strip() for l in doc.xpath("//*[contains(@class, 'cit-block') or self::blockquote or self::div]//l") if l.text_content().strip()]
    verse_text = " ".join(lines) if lines else doc.text_content()
    assert "Ami, dans ce désordre où tu me vois réduite" in verse_text


def test_content_page_contains_notes(built_site: Path) -> None:
    doc = html.fromstring(content_pages(built_site)[0].read_text(encoding="utf-8"))
    endnotes = doc.xpath("//section[contains(@class, 'endnotes')]")
    assert endnotes
    endnote_text = endnotes[0].text_content()
    assert "confident dans la" in endnote_text or "style" in endnote_text.lower()


def test_no_body_text_is_silently_lost(built_site: Path) -> None:
    doc = html.fromstring(content_pages(built_site)[0].read_text(encoding="utf-8"))
    rendered_text = " ".join(doc.text_content().split())
    for expected in (
        "En général, le confident attire peu l’attention.",
        "Ce style natif, propre aux voix secondaires",
        "Cette tirade, adressée à un confident",
        "En guise de conclusion",
    ):
        assert expected in rendered_text


def test_navigation_points_to_the_single_page(built_site: Path) -> None:
    index_doc = html.fromstring((built_site / "index.html").read_text(encoding="utf-8"))
    toc_links = index_doc.xpath(
        "//section[contains(@class, 'home-panel') and .//h2[normalize-space(.)='Sommaire']]//a"
    )
    page_name = content_pages(built_site)[0].name
    assert [link.get("href") for link in toc_links] == [page_name]


def test_build_report_announces_two_generated_pages_and_diagnostic(built_site: Path) -> None:
    report = (built_site / "build_report.txt").read_text(encoding="utf-8")
    assert "Pages générées : 2" in report
    assert "Unité TEI autonome détectée" in report


def test_normalized_xml_keeps_text_body_without_synthetic_group(built_site: Path) -> None:
    normalized = etree.parse(str(built_site / "book.normalized.xml"))
    assert normalized.xpath("/tei:TEI/tei:text/tei:body", namespaces=NSMAP)
    assert not normalized.xpath("/tei:TEI/tei:text/tei:group", namespaces=NSMAP)


# ---------------------------------------------------------------------------
# Non-régression des livres structurés en <group>
# ---------------------------------------------------------------------------

def book_with_group_xml() -> str:
    return """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre structure</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group xml:id='chapitre-1' type='chapter' data-page-title='Chapitre 1'>
        <body><div type='section1'><head>Chapitre 1</head><p>Texte du chapitre.</p></div></body>
      </group>
    </group>
  </text>
</TEI>
"""


def test_book_with_group_still_produces_the_same_pages_and_ignores_body_fallback(tmp_path: Path) -> None:
    tree = etree.ElementTree(etree.fromstring(book_with_group_xml().encode("utf-8")))
    TeiNormalizer().normalize(tree)
    builder = SiteStructureBuilder()
    _, pages, nav = builder.build(tree)

    assert len(pages) == 1
    assert pages[0].file_name == "01-chapitre-1.html"
    assert len(nav) == 1
    assert not any("autonome" in message for message in builder.last_diagnostics)


def test_book_with_group_full_build_generates_expected_pages(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(book_with_group_xml(), encoding="utf-8")
    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))

    pages = content_pages(result.output_dir)
    assert [page.name for page in pages] == ["01-chapitre-1.html"]
    report = (result.output_dir / "build_report.txt").read_text(encoding="utf-8")
    assert "Pages générées : 2" in report
    assert "Unité TEI autonome détectée" not in report
