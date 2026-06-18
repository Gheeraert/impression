from __future__ import annotations

from lxml import etree

from purh_site.reversible import ElementNode, read_tei_element
from purh_site.utils import TEI_NS, XML_NS


def parse_node(xml: str) -> ElementNode:
    element = etree.fromstring(xml.encode("utf-8"))
    return read_tei_element(element)


def test_xml_id_reads_xml_namespace_attribute() -> None:
    node = parse_node('<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p1">Text</p>')

    assert node.xml_id == "p1"
    assert node.get_attr(f"{{{XML_NS}}}id") == "p1"
    assert f"{{{XML_NS}}}id" in node.attrs


def test_xml_lang_stays_available_as_qualified_attribute() -> None:
    node = parse_node('<p xmlns="http://www.tei-c.org/ns/1.0" xml:lang="fr">Text</p>')

    assert node.get_attr(f"{{{XML_NS}}}lang") == "fr"
    assert node.get_attr("xml:lang") == "fr"
    assert f"{{{XML_NS}}}lang" in node.attrs
    assert "xml:lang" not in node.attrs


def test_local_name_and_namespace_describe_tei_tag() -> None:
    node = parse_node('<p xmlns="http://www.tei-c.org/ns/1.0">Text</p>')

    assert node.name == "p"
    assert node.local_name == "p"
    assert node.namespace == TEI_NS


def test_get_attr_helpers_keep_original_attribute_store() -> None:
    node = parse_node(
        '<ref xmlns="http://www.tei-c.org/ns/1.0" type="internal" rend="italic" target="#x">Text</ref>'
    )

    assert node.get_attr("type") == "internal"
    assert node.get_attr("rend") == "italic"
    assert node.get_attr("target") == "#x"
    assert node.has_attr("target")
    assert node.attrs == {"type": "internal", "rend": "italic", "target": "#x"}


def test_set_attr_preserves_qualified_xml_attribute_keys() -> None:
    node = ElementNode("p")

    node.set_attr("xml:id", "p2")
    node.set_attr("rend", "bold")

    assert node.xml_id == "p2"
    assert node.attrs == {f"{{{XML_NS}}}id": "p2", "rend": "bold"}


def test_generic_indicator_marks_unknown_elements_only() -> None:
    paragraph = parse_node('<p xmlns="http://www.tei-c.org/ns/1.0">Text</p>')
    unknown = parse_node('<unknown xmlns="http://www.tei-c.org/ns/1.0">Text</unknown>')

    assert not paragraph.is_generic
    assert unknown.is_generic
    assert type(unknown) is ElementNode


def test_iter_elements_walks_document_order() -> None:
    node = parse_node(
        '<div xmlns="http://www.tei-c.org/ns/1.0"><head>H</head><p>A <hi>B</hi></p><note>N</note></div>'
    )

    assert [element.local_name for element in node.iter_elements()] == ["div", "head", "p", "hi", "note"]


def test_iter_text_reads_complete_text_in_document_order() -> None:
    node = parse_node(
        '<p xmlns="http://www.tei-c.org/ns/1.0">A <hi>B</hi> C <ref target="#d">D</ref>E</p>'
    )

    assert list(node.iter_text()) == ["A ", "B", " C ", "D", "E"]
    assert "".join(node.iter_text()) == "A B C DE"
