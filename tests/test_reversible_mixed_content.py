from __future__ import annotations

from lxml import etree

from purh_site.reversible import ElementNode, TextNode, read_tei_element, write_tei_element
from purh_site.utils import TEI_NS, XML_NS


NS = {"tei": TEI_NS, "xml": XML_NS}


def parse_tei(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


def round_trip_pair(xml: str) -> tuple[etree._Element, etree._Element]:
    source = parse_tei(xml)
    return source, write_tei_element(read_tei_element(source))


def expanded_attrs(element: etree._Element) -> dict[str, str]:
    return dict(element.attrib)


def structural_signature(element: etree._Element) -> tuple:
    return (
        element.tag,
        tuple(sorted(expanded_attrs(element).items())),
        element.text,
        element.tail,
        tuple(structural_signature(child) for child in element),
    )


def child_names(element: etree._Element) -> list[str]:
    return [etree.QName(child).localname for child in element]


def test_mixed_content_preserves_text_inline_child_and_tail() -> None:
    source, emitted = round_trip_pair(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Avant <hi rend="italic">dedans</hi> après.</p>'
    )

    assert structural_signature(emitted) == structural_signature(source)
    assert emitted.text == "Avant "
    assert emitted[0].text == "dedans"
    assert emitted[0].tail == " après."


def test_mixed_content_preserves_multiple_successive_inline_children() -> None:
    source, emitted = round_trip_pair(
        '<p xmlns="http://www.tei-c.org/ns/1.0">A <hi rend="italic">B</hi>C <ref target="#d">D</ref>E</p>'
    )

    assert structural_signature(emitted) == structural_signature(source)
    assert child_names(emitted) == ["hi", "ref"]
    assert emitted.text == "A "
    assert emitted[0].tail == "C "
    assert emitted[1].tail == "E"


def test_inline_note_preserves_note_and_text_after_note() -> None:
    source, emitted = round_trip_pair(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Texte<note place="foot" xml:id="n1">Note</note> suite.</p>'
    )

    note = emitted.xpath("./tei:note", namespaces=NS)[0]
    assert structural_signature(emitted) == structural_signature(source)
    assert note.get("place") == "foot"
    assert note.get(f"{{{XML_NS}}}id") == "n1"
    assert note.tail == " suite."


def test_xml_id_and_xml_lang_use_xml_namespace_after_round_trip() -> None:
    _, emitted = round_trip_pair(
        '<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p1" xml:lang="fr">Texte</p>'
    )

    assert emitted.get(f"{{{XML_NS}}}id") == "p1"
    assert emitted.get(f"{{{XML_NS}}}lang") == "fr"
    assert "xml:id" not in emitted.attrib
    assert "xml:lang" not in emitted.attrib


def test_required_attributes_are_preserved_without_specialization() -> None:
    _, emitted = round_trip_pair(
        '<seg xmlns="http://www.tei-c.org/ns/1.0" type="main" subtype="sub" rend="italic" '
        'place="margin" target="#x" n="12" role="lemma" xml:lang="la">Texte</seg>'
    )

    assert emitted.get("type") == "main"
    assert emitted.get("subtype") == "sub"
    assert emitted.get("rend") == "italic"
    assert emitted.get("place") == "margin"
    assert emitted.get("target") == "#x"
    assert emitted.get("n") == "12"
    assert emitted.get("role") == "lemma"
    assert emitted.get(f"{{{XML_NS}}}lang") == "la"


def test_unknown_tei_element_keeps_generic_node_and_mixed_content() -> None:
    source = parse_tei(
        '<milestoneGroup xmlns="http://www.tei-c.org/ns/1.0" type="custom">A <unknownInline role="x">B</unknownInline> C</milestoneGroup>'
    )
    node = read_tei_element(source)
    emitted = write_tei_element(node)

    assert type(node) is ElementNode
    assert type(node.children[1]) is ElementNode
    assert node.children[1].name == "unknownInline"
    assert isinstance(node.children[0], TextNode)
    assert structural_signature(emitted) == structural_signature(source)


def test_exact_child_order_is_preserved_for_block_sequence() -> None:
    source, emitted = round_trip_pair(
        '<div xmlns="http://www.tei-c.org/ns/1.0"><head>T</head><p>P1</p><list><item>I</item></list><p>P2</p><note>N</note></div>'
    )

    assert structural_signature(emitted) == structural_signature(source)
    assert child_names(emitted) == ["head", "p", "list", "p", "note"]


def test_realistic_commons_publishing_fragment_round_trips_structurally() -> None:
    source, emitted = round_trip_pair(
        """
<div xmlns="http://www.tei-c.org/ns/1.0"
     type="chapter"
     xml:id="ch_001">
  <head>Introduction</head>
  <p xml:id="p_001">Un texte avec <hi rend="italic">italique</hi>, une <ref target="#x">référence</ref> et une note<note place="foot" xml:id="n_001">Texte de <hi rend="italic">note</hi>.</note>.</p>
  <list type="ordered">
    <item n="1">Premier item</item>
    <item n="2">Second item avec <hi rend="small-caps">petites capitales</hi>.</item>
  </list>
</div>
        """
    )

    assert structural_signature(emitted) == structural_signature(source)
    assert emitted.get("type") == "chapter"
    assert emitted.get(f"{{{XML_NS}}}id") == "ch_001"
    assert emitted.xpath("boolean(./tei:p[@xml:id='p_001'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:p/tei:hi[@rend='italic'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:p/tei:ref[@target='#x'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:p/tei:note[@place='foot' and @xml:id='n_001'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:list[@type='ordered']/tei:item[@n='1'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:list/tei:item[@n='2']/tei:hi[@rend='small-caps'])", namespaces=NS)
