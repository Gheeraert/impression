from __future__ import annotations

from lxml import etree

from purh_site.utils import TEI_NS, XML_NS

from .nodes import ElementNode, Node, TextNode


def write_tei_element(node: ElementNode, *, nsmap: dict[str | None, str] | None = None) -> etree._Element:
    """Rebuild an lxml TEI element from the experimental Python tree."""
    element = etree.Element(_element_qname(node), nsmap=nsmap or {None: node.namespace or TEI_NS})
    for key, value in node.attrs.items():
        element.set(_attribute_qname(key), value)
    _append_children(element, node.children)
    return element


def _append_children(parent: etree._Element, children: list[Node]) -> None:
    previous_element: etree._Element | None = None

    for child in children:
        if isinstance(child, TextNode):
            if previous_element is None:
                parent.text = (parent.text or "") + child.text
            else:
                previous_element.tail = (previous_element.tail or "") + child.text
            continue

        if isinstance(child, ElementNode):
            child_element = write_tei_element(child, nsmap=None)
            parent.append(child_element)
            previous_element = child_element
            continue

        raise TypeError(f"Unsupported reversible node: {type(child).__name__}")


def _element_qname(node: ElementNode) -> str:
    if node.name.startswith("{"):
        return node.name
    if node.namespace:
        return f"{{{node.namespace}}}{node.name}"
    return node.name


def _attribute_qname(name: str) -> str:
    if name.startswith("xml:"):
        return f"{{{XML_NS}}}{name.split(':', 1)[1]}"
    return name
