from __future__ import annotations

"""Tests d'intégrité du normaliseur TEI.

Politique vérifiée :
- les xml:id source uniques sont conservés strictement ;
- les identifiants générés sont déterministes, stables et sans collision ;
- des xml:id dupliqués mais jamais référencés (cas courant d'un livre
  assemblé par XInclude à partir de chapitres numérotant chacun leurs
  propres paragraphes) sont renommés silencieusement, sans bloquer ;
- des xml:id dupliqués dont un ou plusieurs porteurs SONT la cible d'une
  référence locale restent, eux, une erreur bloquante (ambiguïté réelle) ;
- note/@n n'est jamais écrit ni modifié par le normaliseur ;
- les pointeurs locaux "#id" sont contrôlés (target, corresp, who, ana, wit…) ;
- les rendus HTML et LaTEI restent fonctionnels avec cette politique.
"""

from pathlib import Path

import pytest
from lxml import etree, html

from purh_site.config import BuildConfig
from purh_site.normalizer import DuplicateXmlIdError, TeiNormalizer
from purh_site.reversible import run_tei_latex_tei_roundtrip
from purh_site.site_builder import SiteBuilder
from purh_site.utils import NSMAP, XML_NS

XMLID = f"{{{XML_NS}}}id"


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
            <head>Section</head>
            {body}
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
"""


def normalize_document(body: str):
    tree = etree.ElementTree(etree.fromstring(tei_document(body).encode("utf-8")))
    report = TeiNormalizer().normalize(tree)
    return tree, report


def serialize(tree: etree._ElementTree) -> bytes:
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def build_site(tmp_path: Path, body: str) -> Path:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(tei_document(body), encoding="utf-8")
    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))
    return result.output_dir


# ---------------------------------------------------------------------------
# Identifiants
# ---------------------------------------------------------------------------

def test_unique_source_xml_id_is_kept_verbatim() -> None:
    tree, _ = normalize_document(
        '<p xml:id="Mon_Id.Éditorial-01">Texte<note xml:id="ftn-A">Note.</note></p>'
    )
    assert tree.xpath("//tei:body//tei:p/@xml:id", namespaces=NSMAP) == ["Mon_Id.Éditorial-01"]
    assert tree.xpath("//tei:note/@xml:id", namespaces=NSMAP) == ["ftn-A"]


def test_element_without_id_receives_stable_generated_id() -> None:
    body = "<p>Premier.</p>"
    tree_a, report_a = normalize_document(body)
    tree_b, report_b = normalize_document(body)
    ids_a = [el.get(XMLID) for el in tree_a.xpath("//tei:p", namespaces=NSMAP)]
    ids_b = [el.get(XMLID) for el in tree_b.xpath("//tei:p", namespaces=NSMAP)]

    assert ids_a == ids_b
    assert all(ids_a)
    assert report_a.assigned_ids == report_b.assigned_ids > 0


def test_normalization_is_idempotent() -> None:
    tree, _ = normalize_document('<p xml:id="p-source">Texte<note n="4">Note.</note></p>')
    first_pass = serialize(tree)

    report_second = TeiNormalizer().normalize(tree)
    second_pass = serialize(tree)

    assert second_pass == first_pass
    assert report_second.assigned_ids == 0


def test_generated_id_does_not_collide_with_source_id() -> None:
    tree, _ = normalize_document('<p xml:id="p-001">Occupé.</p><p>Sans identifiant.</p>')
    body_ids = tree.xpath("//tei:body//tei:p/@xml:id", namespaces=NSMAP)
    all_ids = tree.xpath("//*/@xml:id", namespaces=NSMAP)

    assert body_ids[0] == "p-001"
    assert body_ids[1] != "p-001"
    assert len(set(all_ids)) == len(all_ids)


def test_unreferenced_duplicate_ids_are_renamed_not_rejected() -> None:
    # Cas réel : un livre assemblé par XInclude à partir de chapitres
    # indépendants, chacun numérotant ses propres paragraphes (p1, p2...)
    # sans que rien ne pointe explicitement vers ces identifiants une fois
    # le livre assemblé. Rien n'étant référencé, aucune ambiguïté réelle ne
    # peut résulter d'un renommage : ce n'est plus une erreur bloquante.
    tree = etree.ElementTree(
        etree.fromstring(tei_document("<p>Premier.</p><p>Second.</p>").encode("utf-8"))
    )
    for paragraph in tree.xpath("//tei:body//tei:p", namespaces=NSMAP):
        paragraph.set(XMLID, "doublon")

    report = TeiNormalizer().normalize(tree)

    ids = tree.xpath("//tei:body//tei:p/@xml:id", namespaces=NSMAP)
    assert ids[0] == "doublon"
    assert ids[1] == "doublon-2"
    assert len(set(ids)) == len(ids)
    assert report.renamed_duplicate_ids == 1
    assert any("doublon" in warning for warning in report.warnings)


def test_duplicate_id_that_is_referenced_still_raises_a_clear_error() -> None:
    # Un xml:id dupliqué qui EST la cible d'une référence locale reste, lui,
    # une ambiguïté réelle (vers lequel des porteurs le lien pointe-t-il ?) —
    # aucun renommage automatique ne peut la lever silencieusement.
    tree = etree.ElementTree(
        etree.fromstring(
            tei_document(
                '<p>Premier.</p><p>Second.</p><p>Voir <ref target="#doublon">ici</ref>.</p>'
            ).encode("utf-8")
        )
    )
    for paragraph in tree.xpath("//tei:body//tei:p", namespaces=NSMAP)[:2]:
        paragraph.set(XMLID, "doublon")

    with pytest.raises(DuplicateXmlIdError) as excinfo:
        TeiNormalizer().normalize(tree)
    message = str(excinfo.value)
    assert "doublon" in message
    assert "<p>" in message
    assert "/p[" in message  # XPath lisible des porteurs


def test_duplicate_id_error_message_stays_bounded_with_many_referenced_duplicates() -> None:
    # Un livre à nombreux chapitres peut aussi, dans le pire cas, avoir de
    # nombreux xml:id à la fois dupliqués ET référencés (donc bloquants) —
    # le message ne doit pas pour autant exploser à des dizaines de milliers
    # de caractères, impraticable dans une boîte de dialogue. Les totaux
    # réels doivent rester visibles même si le détail est plafonné.
    paragraphs = "".join(f"<p>Texte {n}.</p>" for n in range(30))
    paragraphs += "".join(f'<p>Voir <ref target="#p{n}">ici</ref>.</p>' for n in range(5))
    tree = etree.ElementTree(etree.fromstring(tei_document(paragraphs).encode("utf-8")))
    body_paragraphs = tree.xpath("//tei:body//tei:p", namespaces=NSMAP)[:30]
    for index, paragraph in enumerate(body_paragraphs):
        paragraph.set(XMLID, f"p{index % 5}")

    with pytest.raises(DuplicateXmlIdError) as excinfo:
        TeiNormalizer().normalize(tree)
    message = str(excinfo.value)

    assert len(message) < 10_000
    assert "5 xml:id dupliqué" in message
    assert "p0" in message
    assert "occurrences" in message


# ---------------------------------------------------------------------------
# Défauts de métadonnées déjà présents en amont (non introduits par ce
# pipeline, mais qui doivent remonter jusqu'à l'éditrice au lieu d'être
# masqués silencieusement dans le rendu final)
# ---------------------------------------------------------------------------

def test_literal_html_markup_in_subtitle_is_reported() -> None:
    # Cas réel observé : un sous-titre exporté depuis un autre outil garde
    # "<em>...</em>" comme texte littéral au lieu d'un balisage interprété.
    tree = etree.ElementTree(
        etree.fromstring(
            b"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader><fileDesc>
    <titleStmt>
      <title type='main'>Titre principal</title>
      <title type='sub'>&lt;em&gt;Sous-titre&lt;/em&gt; complet</title>
    </titleStmt>
    <publicationStmt><p/></publicationStmt>
    <sourceDesc><p/></sourceDesc>
  </fileDesc></teiHeader>
  <text><body><p>Texte.</p></body></text>
</TEI>"""
        )
    )

    report = TeiNormalizer().normalize(tree)

    matches = [w for w in report.warnings if "Balisage HTML littéral" in w]
    assert len(matches) == 1
    assert "<em>Sous-titre</em>" in matches[0]
    assert "title[2]" in matches[0]


def test_duplicate_author_in_metadata_is_reported() -> None:
    # Cas réel observé : la même personne listée deux fois dans titleStmt.
    tree = etree.ElementTree(
        etree.fromstring(
            """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader><fileDesc>
    <titleStmt>
      <title type='main'>Titre</title>
      <author><persName><forename>Anaïs</forename><surname>Lebreton</surname></persName></author>
      <author><persName><forename>Anaïs</forename><surname>Lebreton</surname></persName></author>
    </titleStmt>
    <publicationStmt><p/></publicationStmt>
    <sourceDesc><p/></sourceDesc>
  </fileDesc></teiHeader>
  <text><body><p>Texte.</p></body></text>
</TEI>""".encode()
        )
    )

    report = TeiNormalizer().normalize(tree)

    matches = [w for w in report.warnings if "Auteur" in w and "dupliqué" in w]
    assert len(matches) == 1
    assert "Anaïs" in matches[0]
    assert "Lebreton" in matches[0]
    assert "2 fois" in matches[0]


def test_single_author_is_not_reported_as_duplicate() -> None:
    tree, report = normalize_document("<p>Texte.</p>")

    assert not [w for w in report.warnings if "dupliqué" in w and "Auteur" in w]


def test_existing_references_survive_normalization() -> None:
    tree, report = normalize_document(
        '<p xml:id="cible">Texte cible.</p>'
        '<p>Voir <ref target="#cible">la cible</ref>.</p>'
    )
    assert tree.xpath("//tei:ref/@target", namespaces=NSMAP) == ["#cible"]
    assert tree.xpath("//tei:p[@xml:id='cible']", namespaces=NSMAP)
    assert report.unresolved_references == 0


# ---------------------------------------------------------------------------
# Références locales
# ---------------------------------------------------------------------------

def test_local_target_to_existing_id_is_accepted() -> None:
    _, report = normalize_document(
        '<p xml:id="section-a">A.</p><p><ref target="#section-a">renvoi</ref></p>'
    )
    assert report.unresolved_references == 0
    assert not any("introuvable" in w for w in report.warnings)


def test_orphan_local_reference_is_detected() -> None:
    _, report = normalize_document('<p><ref target="#nulle-part">renvoi</ref></p>')
    assert report.unresolved_references == 1
    assert any("#nulle-part" in w and "target" in w for w in report.warnings)


def test_multivalued_pointer_attribute_is_checked_token_by_token() -> None:
    _, report = normalize_document(
        '<p xml:id="a">A.</p><p ana="#a #b">Analyse.</p>'
    )
    assert report.unresolved_references == 1
    assert any("#b" in w for w in report.warnings)
    assert not any('"#a"' in w for w in report.warnings)


def test_external_url_with_fragment_is_not_a_local_reference() -> None:
    _, report = normalize_document(
        '<p><ref target="https://example.org/page#section">lien externe</ref></p>'
    )
    assert report.unresolved_references == 0


def test_template_placeholder_pointer_is_invalid_not_orphan() -> None:
    # "##" et "#" isolé sont des valeurs de gabarit Métopes non remplies :
    # elles ne doivent pas être comptées comme références orphelines.
    _, report = normalize_document(
        '<p who="##">Parole.</p><p><ref target="#">renvoi vide</ref></p>'
    )
    assert report.invalid_pointers == 2
    assert report.unresolved_references == 0
    assert not any("introuvable" in w for w in report.warnings)
    invalid = [w for w in report.warnings if "invalide" in w]
    assert any('who="##"' in w for w in invalid)
    assert any('target="#"' in w for w in invalid)


def test_placeholder_and_real_orphan_are_reported_distinctly() -> None:
    _, report = normalize_document(
        '<p who="##">Gabarit.</p><p><ref target="#nulle-part">orphelin</ref></p>'
    )
    assert report.invalid_pointers == 1
    assert report.unresolved_references == 1
    assert any("invalide" in w and '"##"' in w for w in report.warnings)
    assert any("introuvable" in w and "#nulle-part" in w for w in report.warnings)


def test_subtype_is_not_treated_as_a_pointer_attribute() -> None:
    # subtype n'est pas un attribut pointeur TEI : idno/@subtype="##" est un
    # trou de gabarit de métadonnées, pas une référence locale.
    _, report = normalize_document('<p><idno subtype="##" type="DOI"/></p>')
    assert report.unresolved_references == 0
    assert report.invalid_pointers == 0
    assert not any("subtype" in w for w in report.warnings)


def test_rendition_pointer_to_missing_definition_stays_an_orphan_warning() -> None:
    # rendition est bien un pointeur : sans rendition/@xml:id correspondant
    # dans le document, l'avertissement de référence orpheline est conservé.
    _, report = normalize_document('<list rendition="#list-ndash"><item>a</item></list>')
    assert report.unresolved_references == 1
    assert any('rendition="#list-ndash"' in w and "introuvable" in w for w in report.warnings)


def test_rendition_pointer_to_existing_id_is_resolved() -> None:
    _, report = normalize_document(
        '<p xml:id="list-tiret">déf.</p>'
        '<list rendition="#list-tiret"><item>a</item></list>'
    )
    assert report.unresolved_references == 0
    assert not any("rendition" in w for w in report.warnings)


def test_who_wit_corresp_pointer_attributes_are_covered() -> None:
    _, report = normalize_document(
        '<p xml:id="temoin-a">A.</p>'
        '<p who="#absent-qui">Parole.</p>'
        '<p wit="#temoin-a #absent-temoin">Leçon.</p>'
        '<p corresp="#absent-corresp">Correspondance.</p>'
    )
    unresolved = [w for w in report.warnings if "introuvable" in w]
    assert report.unresolved_references == 3
    assert any("#absent-qui" in w and "who" in w for w in unresolved)
    assert any("#absent-temoin" in w and "wit" in w for w in unresolved)
    assert any("#absent-corresp" in w and "corresp" in w for w in unresolved)


# ---------------------------------------------------------------------------
# Notes : @n est une donnée éditoriale source
# ---------------------------------------------------------------------------

def test_numeric_note_n_is_preserved() -> None:
    tree, _ = normalize_document('<p>Texte<note n="12">Note.</note></p>')
    assert tree.xpath("//tei:note/@n", namespaces=NSMAP) == ["12"]


def test_symbolic_note_n_is_preserved() -> None:
    tree, _ = normalize_document('<p>Texte<note n="*">Note.</note></p>')
    assert tree.xpath("//tei:note/@n", namespaces=NSMAP) == ["*"]


def test_repeated_note_n_across_chapters_is_not_mutated() -> None:
    xml = """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Deux chapitres</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Un'>
        <body><div type='section1'><head>Un</head>
          <p>Texte<note n="1">Note un.</note></p>
        </div></body>
      </group>
      <group type='chapter' data-page-title='Deux'>
        <body><div type='section1'><head>Deux</head>
          <p>Texte<note n="1">Note deux.</note></p>
        </div></body>
      </group>
    </group>
  </text>
</TEI>
"""
    tree = etree.ElementTree(etree.fromstring(xml.encode("utf-8")))
    TeiNormalizer().normalize(tree)
    assert tree.xpath("//tei:note/@n", namespaces=NSMAP) == ["1", "1"]


def test_note_without_n_stays_without_n_in_normalized_xml() -> None:
    tree, _ = normalize_document("<p>Texte<note>Note sans numéro.</note></p>")
    note = tree.xpath("//tei:note", namespaces=NSMAP)[0]
    assert note.get("n") is None
    assert note.get(XMLID)  # identifiant technique attribué, @n éditorial absent


def test_note_without_n_has_working_html_call_and_backlink(tmp_path: Path) -> None:
    output_dir = build_site(tmp_path, "<p>Texte<note>Note sans numéro.</note></p>")
    page = next(p for p in output_dir.glob("*.html") if p.name != "index.html")
    doc = html.fromstring(page.read_text(encoding="utf-8"))

    call_links = doc.xpath("//sup[contains(@class, 'note-ref')]/a")
    assert len(call_links) == 1
    note_id = call_links[0].get("href")[1:]
    sup_id = call_links[0].getparent().get("id")

    endnote = doc.xpath(f"//section[contains(@class, 'endnotes')]//li[@id='{note_id}']")
    assert endnote, "L'appel de note doit pointer vers l'entrée d'endnote"
    backlinks = doc.xpath(
        f"//section[contains(@class, 'endnotes')]//a[@href='#{sup_id}']"
    )
    assert backlinks, "Le retour de note doit pointer vers l'appel"


def test_numeric_note_n_is_displayed_verbatim_in_html(tmp_path: Path) -> None:
    output_dir = build_site(tmp_path, '<p>Texte<note n="12">Note douze.</note></p>')
    page = next(p for p in output_dir.glob("*.html") if p.name != "index.html")
    doc = html.fromstring(page.read_text(encoding="utf-8"))

    calls = doc.xpath("//sup[contains(@class, 'note-ref')]/a")
    assert [c.text_content().strip() for c in calls] == ["12"]


def test_symbolic_note_n_is_displayed_verbatim_in_html(tmp_path: Path) -> None:
    output_dir = build_site(tmp_path, '<p>Texte<note n="*">Note étoile.</note></p>')
    page = next(p for p in output_dir.glob("*.html") if p.name != "index.html")
    doc = html.fromstring(page.read_text(encoding="utf-8"))

    calls = doc.xpath("//sup[contains(@class, 'note-ref')]/a")
    assert [c.text_content().strip() for c in calls] == ["*"]


def test_note_without_n_gets_automatic_display_number(tmp_path: Path) -> None:
    # La première note garde son libellé source "*" ; la seconde, sans @n,
    # reçoit un numéro d'affichage (sa position dans la page), calculé dans
    # le clone de rendu uniquement.
    output_dir = build_site(
        tmp_path,
        '<p>Un<note n="*">Avec libellé.</note> deux<note>Sans libellé.</note>.</p>',
    )
    page = next(p for p in output_dir.glob("*.html") if p.name != "index.html")
    doc = html.fromstring(page.read_text(encoding="utf-8"))

    calls = doc.xpath("//sup[contains(@class, 'note-ref')]/a")
    assert [c.text_content().strip() for c in calls] == ["*", "2"]


def test_html_anchors_stay_unique_when_notes_share_the_same_n(tmp_path: Path) -> None:
    output_dir = build_site(
        tmp_path,
        '<p>Un<note n="1">Première note.</note> et deux<note n="1">Seconde note.</note>.</p>',
    )
    page = next(p for p in output_dir.glob("*.html") if p.name != "index.html")
    doc = html.fromstring(page.read_text(encoding="utf-8"))

    ids = doc.xpath("//*[@id]/@id")
    assert len(ids) == len(set(ids)), "Aucun id HTML ne doit être dupliqué"
    assert len(doc.xpath("//sup[contains(@class, 'note-ref')]")) == 2
    assert len(doc.xpath("//section[contains(@class, 'endnotes')]//li")) == 2


def test_latei_rendering_keeps_notes_and_source_n_coherent() -> None:
    fragment = (
        '<div xmlns="http://www.tei-c.org/ns/1.0" type="chapter" xml:id="ch1">'
        "<head>Chapitre</head>"
        '<p xml:id="p1">Texte<note n="12" xml:id="n1">Note numérotée.</note> '
        "suite<note>Note sans numéro.</note>.</p>"
        "</div>"
    )
    tree = etree.ElementTree(etree.fromstring(fragment.encode("utf-8")))
    TeiNormalizer().normalize(tree)
    result = run_tei_latex_tei_roundtrip(tree.getroot())

    assert result.diagnostics == []
    notes = result.emitted.xpath(".//tei:note", namespaces=NSMAP)
    assert len(notes) == 2
    assert notes[0].get(XMLID) == "n1"
    assert notes[0].get("n") == "12"
    assert notes[1].get("n") is None
    assert "\\teiNote" in result.latex
