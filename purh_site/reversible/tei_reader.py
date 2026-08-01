from __future__ import annotations

from lxml import etree

from purh_site.utils import XML_NS

from .nodes import ElementNode, Node, TextNode, make_element_node


def read_tei_element(element: etree._Element) -> ElementNode:
    """Build a conservative Python tree from an lxml TEI element."""
    name = _local_name(element.tag)
    namespace = _namespace(element.tag)
    attrs = {_attribute_name(key): value for key, value in element.attrib.items()}
    children: list[Node] = []

    if element.text is not None:
        children.append(TextNode(element.text))

    for child in element:
        children.append(read_tei_element(child))
        if child.tail is not None:
            children.append(TextNode(child.tail))

    return make_element_node(name=name, attrs=attrs, children=children, namespace=namespace)


def _local_name(tag: str) -> str:
    qname = etree.QName(tag)
    return qname.localname


def _namespace(tag: str) -> str | None:
    return etree.QName(tag).namespace


def _attribute_name(name: str) -> str:
    qname = etree.QName(name)
    if qname.namespace == XML_NS:
        return f"{{{XML_NS}}}{qname.localname}"
    if qname.namespace:
        return f"{{{qname.namespace}}}{qname.localname}"
    return qname.localname
