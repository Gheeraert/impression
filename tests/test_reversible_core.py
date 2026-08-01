from __future__ import annotations

from lxml import etree

from purh_site.reversible import ElementNode, read_tei_element, write_tei_element
from purh_site.reversible.nodes import HiNode, ParagraphNode, RefNode
from purh_site.utils import TEI_NS, XML_NS

NS = {"tei": TEI_NS, "xml": XML_NS}


def round_trip(xml: str) -> etree._Element:
    source = etree.fromstring(xml.encode("utf-8"))
    node = read_tei_element(source)
    return write_tei_element(node)


def text_content(element: etree._Element) -> str:
    return "".join(element.itertext())


def test_simple_paragraph_is_read_and_emitted() -> None:
    emitted = round_trip('<p xmlns="http://www.tei-c.org/ns/1.0">Un paragraphe.</p>')

    assert emitted.tag == f"{{{TEI_NS}}}p"
    assert text_content(emitted) == "Un paragraphe."


def test_paragraph_with_italic_hi_preserves_rend() -> None:
    source = etree.fromstring(
        b'<p xmlns="http://www.tei-c.org/ns/1.0">Un <hi rend="italic">mot</hi> ici.</p>'
    )
    node = read_tei_element(source)
    emitted = write_tei_element(node)

    assert isinstance(node, ParagraphNode)
    assert isinstance(node.children[1], HiNode)
    hi = emitted.xpath("./tei:hi", namespaces=NS)[0]
    assert hi.get("rend") == "italic"
    assert text_content(emitted) == "Un mot ici."
    assert hi.tail == " ici."


def test_footnote_with_xml_id_is_preserved() -> None:
    emitted = round_trip(
        '<note xmlns="http://www.tei-c.org/ns/1.0" place="foot" xml:id="n1">Note.</note>'
    )

    assert emitted.get("place") == "foot"
    assert emitted.get(f"{{{XML_NS}}}id") == "n1"


def test_ref_target_is_preserved() -> None:
    source = etree.fromstring(
        b'<p xmlns="http://www.tei-c.org/ns/1.0">Voir <ref target="#fig1">figure</ref>.</p>'
    )
    node = read_tei_element(source)
    emitted = write_tei_element(node)

    assert isinstance(node.children[1], RefNode)
    ref = emitted.xpath("./tei:ref", namespaces=NS)[0]
    assert ref.get("target") == "#fig1"
    assert ref.text == "figure"


def test_division_with_head_and_paragraph_preserves_order() -> None:
    emitted = round_trip(
        '<div xmlns="http://www.tei-c.org/ns/1.0"><head>Titre</head><p>Texte</p></div>'
    )

    assert [etree.QName(child).localname for child in emitted] == ["head", "p"]
    assert emitted[0].text == "Titre"
    assert emitted[1].text == "Texte"


def test_unknown_tei_element_is_preserved_as_element_node() -> None:
    source = etree.fromstring(
        '<custom xmlns="http://www.tei-c.org/ns/1.0" type="x">Avant <hi rend="bold">gras</hi> après</custom>'.encode()
    )
    node = read_tei_element(source)
    emitted = write_tei_element(node)

    assert type(node) is ElementNode
    assert node.name == "custom"
    assert node.attrs == {"type": "x"}
    assert emitted.tag == f"{{{TEI_NS}}}custom"
    assert emitted.get("type") == "x"
    assert text_content(emitted) == "Avant gras après"


def test_round_trip_preserves_essential_tags_attributes_and_mixed_content() -> None:
    source = etree.fromstring(
        b"""
        <div xmlns="http://www.tei-c.org/ns/1.0" type="chapter" xml:id="d1">
          <head rend="caps">Titre</head>
          <p>Un <hi rend="italic">mot</hi>, une <ref target="#n1">note</ref>.</p>
          <note place="foot" xml:id="n1">Contenu</note>
        </div>
        """
    )

    node = read_tei_element(source)
    emitted = write_tei_element(node)

    assert emitted.get("type") == "chapter"
    assert emitted.get(f"{{{XML_NS}}}id") == "d1"
    assert emitted.xpath("boolean(./tei:head[@rend='caps'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:p/tei:hi[@rend='italic'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:p/tei:ref[@target='#n1'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:note[@place='foot' and @xml:id='n1'])", namespaces=NS)
