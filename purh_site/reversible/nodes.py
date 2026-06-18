from __future__ import annotations

"""Document nodes for the experimental reversible TEI projection.

This tree is not a canonical model competing with TEI. It is a reversible
documentary projection: it keeps the tag, namespace, attributes, ordered
children, text nodes, mixed content, and unknown elements so later HTML,
LaTeX, or other outputs can be produced without impoverishing the source.
"""

from dataclasses import dataclass, field
from typing import Iterator

from purh_site.utils import TEI_NS, XML_NS


@dataclass(slots=True)
class Node:
    """Base class for the experimental reversible document tree."""


@dataclass(slots=True)
class TextNode(Node):
    text: str


@dataclass(slots=True)
class ElementNode(Node):
    name: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Node] = field(default_factory=list)
    namespace: str | None = TEI_NS

    @property
    def local_name(self) -> str:
        if self.name.startswith("{"):
            return self.name.rsplit("}", 1)[1]
        return self.name

    @property
    def is_generic(self) -> bool:
        return type(self) is ElementNode

    @property
    def xml_id(self) -> str | None:
        return self.get_attr(f"{{{XML_NS}}}id")

    def get_attr(self, name: str) -> str | None:
        return self.attrs.get(_attribute_key(name))

    def set_attr(self, name: str, value: str) -> None:
        self.attrs[_attribute_key(name)] = value

    def has_attr(self, name: str) -> bool:
        return _attribute_key(name) in self.attrs

    def iter_elements(self) -> Iterator[ElementNode]:
        yield self
        for child in self.children:
            if isinstance(child, ElementNode):
                yield from child.iter_elements()

    def iter_text(self) -> Iterator[str]:
        for child in self.children:
            if isinstance(child, TextNode):
                yield child.text
            elif isinstance(child, ElementNode):
                yield from child.iter_text()


class DivNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("div", attrs or {}, children or [], namespace)


class HeadNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("head", attrs or {}, children or [], namespace)


class ParagraphNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("p", attrs or {}, children or [], namespace)


class HiNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("hi", attrs or {}, children or [], namespace)


class NoteNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("note", attrs or {}, children or [], namespace)


class RefNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("ref", attrs or {}, children or [], namespace)


class FigureNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("figure", attrs or {}, children or [], namespace)


class TitleNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("title", attrs or {}, children or [], namespace)


class ForeignNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("foreign", attrs or {}, children or [], namespace)


class TermNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("term", attrs or {}, children or [], namespace)


class NameNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("name", attrs or {}, children or [], namespace)


class PersNameNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("persName", attrs or {}, children or [], namespace)


class PlaceNameNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("placeName", attrs or {}, children or [], namespace)


class OrgNameNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("orgName", attrs or {}, children or [], namespace)


class DateNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("date", attrs or {}, children or [], namespace)


class NumNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("num", attrs or {}, children or [], namespace)


class LabelNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("label", attrs or {}, children or [], namespace)


class QNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("q", attrs or {}, children or [], namespace)


class SaidNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("said", attrs or {}, children or [], namespace)


class CitNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("cit", attrs or {}, children or [], namespace)


class BiblNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("bibl", attrs or {}, children or [], namespace)


class PtrNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("ptr", attrs or {}, children or [], namespace)


class LbNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("lb", attrs or {}, children or [], namespace)


class PbNode(ElementNode):
    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        children: list[Node] | None = None,
        namespace: str | None = TEI_NS,
    ) -> None:
        super().__init__("pb", attrs or {}, children or [], namespace)


SPECIALIZED_NODE_TYPES: dict[str, type[ElementNode]] = {
    "bibl": BiblNode,
    "cit": CitNode,
    "div": DivNode,
    "head": HeadNode,
    "p": ParagraphNode,
    "hi": HiNode,
    "note": NoteNode,
    "ref": RefNode,
    "figure": FigureNode,
    "title": TitleNode,
    "foreign": ForeignNode,
    "term": TermNode,
    "name": NameNode,
    "persName": PersNameNode,
    "placeName": PlaceNameNode,
    "orgName": OrgNameNode,
    "date": DateNode,
    "num": NumNode,
    "label": LabelNode,
    "lb": LbNode,
    "pb": PbNode,
    "ptr": PtrNode,
    "q": QNode,
    "said": SaidNode,
}


def make_element_node(
    name: str,
    attrs: dict[str, str],
    children: list[Node],
    namespace: str | None = TEI_NS,
) -> ElementNode:
    node_type = SPECIALIZED_NODE_TYPES.get(name)
    if node_type is None:
        return ElementNode(name=name, attrs=attrs, children=children, namespace=namespace)
    return node_type(attrs=attrs, children=children, namespace=namespace)


def _attribute_key(name: str) -> str:
    if name.startswith("xml:"):
        return f"{{{XML_NS}}}{name.split(':', 1)[1]}"
    return name
