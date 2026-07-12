from __future__ import annotations

"""Tests d'intégrité du normaliseur TEI.

Ces tests verrouillent la séparation entre données éditoriales source
(`xml:id`, `note/@n`) et données techniques de rendu (ancres HTML et
numérotation automatique des seules notes sans libellé).
"""

from pathlib import Path

import pytest
from lxml import etree, html

from purh_site.config import BuildConfig
from purh_site.normalizer import DuplicateXmlIdError, TeiNormalizer
from purh_site.reversible import run_tei_latex_tei_roundtrip
from purh_site.site_builder import SiteBuilder
from purh_site.utils import NSMAP, XML_NS

XML_ID = f"{{{XML_NS}}}id"


def tei_document(body: str) -> str:
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Test normaliseur</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre'>
        <body>
          <div type='section1'>
            <head>Chapitre</head>
            {body}
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
"""


def normalize_document(body: str) -> tuple[etree._ElementTree, object]:
    root = etree.fromstring(tei_document(body).encode("utf-8"))
    tree = etree.ElementTree(root)
    report = TeiNormalizer().normalize(tree)
    return tree, report


def build_site(tmp_path: Path, body: str) -> Path:
    source = tmp_path / "book.xml"
    source.write_text(tei_document(body), encoding="utf-8")
    result = SiteBuilder().build_from_master(
        source,
        BuildConfig(output_dir=tmp_path / "site"),
    )
    return result.output_dir


def content_page(output_dir: Path) -> Path:
    return next(path for path in output_dir.glob("*.html") if path.name != "index.html")


def test_unique_source_xml_id_is_kept_verbatim() -> None:
    tree, _ = normalize_document('<p xml:id="Mon_Id.Editorial-01">Texte.</p>')

    assert tree.xpath("//tei:body//tei:p/@xml:id", namespaces=NSMAP) == [
        "Mon_Id.Editorial-01"
    ]


def test_generated_ids_are_stable_and_normalization_is_idempotent() -> None:
    first_tree, first_report = normalize_document("<p>Texte.</p><p>Suite.</p>")
    first_xml = etree.tostring(first_tree, encoding="unicode")

    second_report = TeiNormalizer().normalize(first_tree)
    second_xml = etree.tostring(first_tree, encoding="unicode")

    fresh_tree, _ = normalize_document("<p>Texte.</p><p>Suite.</p>")
    fresh_xml = etree.tostring(fresh_tree, encoding="unicode")

    assert first_report.assigned_ids > 0
    assert second_report.assigned_ids == 0
    assert second_xml == first_xml == fresh_xml


def test_generated_id_does_not_collide_with_source_id() -> None:
    tree, _ = normalize_document(
        '<p xml:id="p-001">Occupé.</p><p>Sans identifiant.</p>'
    )
    body_ids = tree.xpath("//tei:body//tei:p/@xml:id", namespaces=NSMAP)

    assert body_ids[0] == "p-001"
    assert body_ids[1] != "p-001"
    assert len(body_ids) == len(set(body_ids))


def test_duplicate_source_xml_ids_raise_a_clear_error() -> None:
    root = etree.fromstring(tei_document("<p>Premier.</p><p>Second.</p>").encode("utf-8"))
    tree = etree.ElementTree(root)
    for paragraph in tree.xpath("//tei:body//tei:p", namespaces=NSMAP):
        paragraph.set(XML_ID, "doublon")

    with pytest.raises(DuplicateXmlIdError) as excinfo:
        TeiNormalizer().normalize(tree)

    message = str(excinfo.value)
    assert "doublon" in message
    assert "<p>" in message
    assert "/TEI/text/group/group/body/div/p[1]" in message
    assert "/TEI/text/group/group/body/div/p[2]" in message


def test_existing_local_reference_is_accepted() -> None:
    _, report = normalize_document(
        '<p xml:id="cible">Cible.</p><p><ref target="#cible">Voir</ref></p>'
    )

    assert report.unresolved_references == 0
    assert report.invalid_pointers == 0


def test_orphan_local_reference_is_reported() -> None:
    _, report = normalize_document(
        '<p><ref target="#cible-absente">Voir</ref></p>'
    )

    assert report.unresolved_references == 1
    assert any("#cible-absente" in warning for warning in report.warnings)


def test_multivalued_pointers_are_checked_and_external_fragments_are_ignored() -> None:
    _, report = normalize_document(
        '<p xml:id="a">A.</p>'
        '<p xml:id="b">B.</p>'
        '<p ana="#a #b" who="#a" wit="#a #b" corresp="#b">Texte.</p>'
        '<p><ref target="https://example.org/page#section">Externe</ref></p>'
    )

    assert report.unresolved_references == 0
    assert report.invalid_pointers == 0


def test_template_placeholder_pointer_is_invalid_not_orphan() -> None:
    _, report = normalize_document(
        '<p who="##">Parole.</p><p><ref target="#">renvoi vide</ref></p>'
    )

    assert report.invalid_pointers == 2
    assert report.unresolved_references == 0
    assert any('who="##"' in warning for warning in report.warnings)
    assert any('target="#"' in warning for warning in report.warnings)


def test_subtype_is_not_treated_as_a_pointer_attribute() -> None:
    _, report = normalize_document('<p><idno subtype="##" type="DOI"/></p>')

    assert report.unresolved_references == 0
    assert report.invalid_pointers == 0
    assert not any("subtype" in warning for warning in report.warnings)


def test_missing_rendition_target_stays_an_orphan_warning() -> None:
    _, report = normalize_document(
        '<list rendition="#list-ndash"><item>Élément</item></list>'
    )

    assert report.unresolved_references == 1
    assert any('rendition="#list-ndash"' in warning for warning in report.warnings)


def test_existing_rendition_target_is_resolved() -> None:
    _, report = normalize_document(
        '<p xml:id="list-ndash">Définition.</p>'
        '<list rendition="#list-ndash"><item>Élément</item></list>'
    )

    assert report.unresolved_references == 0


def test_note_n_values_are_preserved_and_missing_n_is_not_created() -> None:
    tree, _ = normalize_document(
        '<p>Texte<note n="12">Douze.</note>'
        '<note n="*">Étoile.</note><note>Sans numéro.</note></p>'
    )
    notes = tree.xpath("//tei:body//tei:note", namespaces=NSMAP)

    assert notes[0].get("n") == "12"
    assert notes[1].get("n") == "*"
    assert "n" not in notes[2].attrib


def test_html_displays_source_note_labels_and_numbers_only_missing_labels(
    tmp_path: Path,
) -> None:
    output_dir = build_site(
        tmp_path,
        '<p>Un<note n="*">Étoile.</note> deux<note>Automatique.</note> '
        'trois<note n="12">Douze.</note>.</p>',
    )
    doc = html.fromstring(content_page(output_dir).read_text(encoding="utf-8"))

    labels = [
        element.text_content().strip()
        for element in doc.xpath("//sup[contains(@class, 'note-ref')]/a")
    ]
    assert labels == ["*", "2", "12"]


def test_html_note_anchors_are_unique_when_labels_repeat(tmp_path: Path) -> None:
    output_dir = build_site(
        tmp_path,
        '<p>Un<note n="1">Première.</note> deux<note n="1">Deuxième.</note>.</p>',
    )
    doc = html.fromstring(content_page(output_dir).read_text(encoding="utf-8"))

    call_ids = doc.xpath("//sup[contains(@class, 'note-ref')]/@id")
    call_hrefs = doc.xpath("//sup[contains(@class, 'note-ref')]/a/@href")
    endnote_ids = doc.xpath("//section[contains(@class, 'endnotes')]//li/@id")

    assert len(call_ids) == len(set(call_ids)) == 2
    assert len(call_hrefs) == len(set(call_hrefs)) == 2
    assert len(endnote_ids) == len(set(endnote_ids)) == 2
    assert {href.removeprefix("#") for href in call_hrefs} == set(endnote_ids)


def test_note_roundtrip_preserves_xml_id_and_editorial_label() -> None:
    note = etree.fromstring(
        b'<note xmlns="http://www.tei-c.org/ns/1.0" xml:id="note-a" n="*">Texte.</note>'
    )

    result = run_tei_latex_tei_roundtrip(note)

    assert result.diagnostics == []
    assert result.emitted.get(XML_ID) == "note-a"
    assert result.emitted.get("n") == "*"
