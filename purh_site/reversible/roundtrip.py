from __future__ import annotations

from dataclasses import dataclass

from lxml import etree

from .latex_reader import read_latex_document
from .latex_writer import write_latex
from .nodes import ElementNode
from .tei_reader import read_tei_element
from .tei_writer import write_tei_element


@dataclass(slots=True)
class Diagnostic:
    code: str
    message: str
    path: str


@dataclass(slots=True)
class RoundTripResult:
    source: etree._Element
    first_tree: ElementNode
    latex: str
    second_tree: ElementNode
    emitted: etree._Element
    diagnostics: list[Diagnostic]


def tei_latex_tei_roundtrip(element: etree._Element) -> etree._Element:
    tree = read_tei_element(element)
    latex = write_latex(tree)
    tree2 = read_latex_document(latex)
    return write_tei_element(tree2)


def run_tei_latex_tei_roundtrip(element: etree._Element) -> RoundTripResult:
    first_tree = read_tei_element(element)
    latex = write_latex(first_tree)
    second_tree = read_latex_document(latex)
    emitted = write_tei_element(second_tree)
    diagnostics = compare_tei_elements(element, emitted)
    return RoundTripResult(
        source=element,
        first_tree=first_tree,
        latex=latex,
        second_tree=second_tree,
        emitted=emitted,
        diagnostics=diagnostics,
    )


def compare_tei_elements(source: etree._Element, emitted: etree._Element) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    _compare_element(source, emitted, _element_path(source), diagnostics)
    return diagnostics


def _compare_element(
    source: etree._Element,
    emitted: etree._Element,
    path: str,
    diagnostics: list[Diagnostic],
) -> None:
    source_qname = etree.QName(source)
    emitted_qname = etree.QName(emitted)

    if source_qname.localname != emitted_qname.localname:
        diagnostics.append(
            Diagnostic(
                code="TAG_MISMATCH",
                message=f"Expected tag {source_qname.localname!r}, got {emitted_qname.localname!r}.",
                path=path,
            )
        )
    if source_qname.namespace != emitted_qname.namespace:
        diagnostics.append(
            Diagnostic(
                code="NAMESPACE_MISMATCH",
                message=f"Expected namespace {source_qname.namespace!r}, got {emitted_qname.namespace!r}.",
                path=path,
            )
        )
    if dict(source.attrib) != dict(emitted.attrib):
        diagnostics.append(
            Diagnostic(
                code="ATTR_MISMATCH",
                message=f"Expected attributes {dict(source.attrib)!r}, got {dict(emitted.attrib)!r}.",
                path=path,
            )
        )
    if source.text != emitted.text:
        diagnostics.append(
            Diagnostic(
                code="TEXT_MISMATCH",
                message=f"Expected text {source.text!r}, got {emitted.text!r}.",
                path=path,
            )
        )
    if source.tail != emitted.tail:
        diagnostics.append(
            Diagnostic(
                code="TAIL_MISMATCH",
                message=f"Expected tail {source.tail!r}, got {emitted.tail!r}.",
                path=path,
            )
        )
    if len(source) != len(emitted):
        diagnostics.append(
            Diagnostic(
                code="CHILD_COUNT_MISMATCH",
                message=f"Expected {len(source)} child element(s), got {len(emitted)}.",
                path=path,
            )
        )

    for index, (source_child, emitted_child) in enumerate(zip(source, emitted), start=1):
        _compare_element(source_child, emitted_child, _child_path(path, source_child, index), diagnostics)


def _element_path(element: etree._Element) -> str:
    return f"/{etree.QName(element).localname}"


def _child_path(parent_path: str, child: etree._Element, index: int) -> str:
    return f"{parent_path}/{etree.QName(child).localname}[{index}]"
