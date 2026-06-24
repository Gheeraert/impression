from __future__ import annotations

import pytest

from purh_site.reversible.latex_reader import (
    LatexParseError,
    _Parser,
    read_latex,
)
from purh_site.reversible.nodes import ElementNode, TextNode
from purh_site.utils import TEI_NS


def test_latei_no_indent_is_transparent_single_paragraph() -> None:
    latex = r"\lateiNoIndent{\teiP{Premier paragraphe sans retrait.}}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 1
    node = nodes[0]
    assert isinstance(node, ElementNode)
    assert node.name == "p"
    assert node.namespace == TEI_NS


def test_latei_no_indent_passes_through_multiple_nodes() -> None:
    latex = r"\lateiNoIndent{\teiP{Premier.}\teiP{Second.}}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 2
    assert all(isinstance(n, ElementNode) and n.name == "p" for n in nodes)


def test_latei_no_indent_passes_through_text_node() -> None:
    latex = r"\lateiNoIndent{texte libre}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 1
    assert isinstance(nodes[0], TextNode)
    assert nodes[0].text == "texte libre"


def test_latei_no_indent_nested_inside_tei_paragraph() -> None:
    latex = r"\teiP{\lateiNoIndent{contenu}}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 1
    p = nodes[0]
    assert isinstance(p, ElementNode)
    assert p.name == "p"
    assert len(p.children) == 1
    assert isinstance(p.children[0], TextNode)
    assert p.children[0].text == "contenu"


def test_latei_no_indent_requires_braced_content() -> None:
    latex = r"\lateiNoIndent sans accolades"
    with pytest.raises(LatexParseError, match="Expected braced content"):
        _Parser(latex).parse_nodes()


def test_latei_no_indent_macro_defined_in_macros_file() -> None:
    from pathlib import Path
    source = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert r"\lateiNoIndent" in source
    assert r"\NewDocumentCommand{\lateiNoIndent}" in source


def test_latei_no_indent_documented_in_layout_commands_file() -> None:
    from pathlib import Path
    doc = Path("LATEI_LAYOUT_COMMANDS.md").read_text(encoding="utf-8")
    assert "lateiNoIndent" in doc
    assert "parindent" in doc or "retrait" in doc
