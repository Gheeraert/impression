from __future__ import annotations

from pathlib import Path

import pytest

from purh_site.reversible.latex_reader import (
    LAYOUT_PARAM_STANDALONE_MACROS,
    LAYOUT_PARAM_WRAPPER_MACROS,
    LAYOUT_STANDALONE_MACROS,
    LAYOUT_WRAPPER_MACROS,
    LatexParseError,
    _Parser,
)
from purh_site.reversible.nodes import ElementNode
from purh_site.utils import TEI_NS

# ---------------------------------------------------------------------------
# 8.1 — Enveloppes simples : toutes les commandes LAYOUT_WRAPPER_MACROS
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("macro", sorted(LAYOUT_WRAPPER_MACROS))
def test_layout_wrapper_is_transparent_single_paragraph(macro: str) -> None:
    latex = rf"\{macro}{{\teiP[xmlid={{p-001}}]{{Texte.}}}}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 1
    node = nodes[0]
    assert isinstance(node, ElementNode)
    assert node.name == "p"
    assert node.namespace == TEI_NS
    assert node.attrs.get("{http://www.w3.org/XML/1998/namespace}id") == "p-001"


@pytest.mark.parametrize("macro", sorted(LAYOUT_WRAPPER_MACROS))
def test_layout_wrapper_passes_through_multiple_nodes(macro: str) -> None:
    latex = rf"\{macro}{{\teiP{{Premier.}}\teiP{{Second.}}}}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 2
    assert all(isinstance(n, ElementNode) and n.name == "p" for n in nodes)


@pytest.mark.parametrize("macro", sorted(LAYOUT_WRAPPER_MACROS))
def test_layout_wrapper_requires_braced_content(macro: str) -> None:
    latex = rf"\{macro} sans accolades"
    with pytest.raises(LatexParseError, match="Expected braced content"):
        _Parser(latex).parse_nodes()


# ---------------------------------------------------------------------------
# 8.2 — Enveloppes à paramètre : lateiSpaceBefore, lateiSpaceAfter
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("macro", sorted(LAYOUT_PARAM_WRAPPER_MACROS))
@pytest.mark.parametrize("size", ["small", "medium", "large"])
def test_layout_param_wrapper_is_transparent(macro: str, size: str) -> None:
    latex = rf"\{macro}{{{size}}}{{\teiP{{Texte.}}}}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 1
    assert isinstance(nodes[0], ElementNode)
    assert nodes[0].name == "p"


@pytest.mark.parametrize("macro", sorted(LAYOUT_PARAM_WRAPPER_MACROS))
def test_layout_param_wrapper_rejects_invalid_size(macro: str) -> None:
    latex = rf"\{macro}{{12pt}}{{\teiP{{Texte.}}}}"
    with pytest.raises(LatexParseError, match="Invalid size"):
        _Parser(latex).parse_nodes()


@pytest.mark.parametrize("macro", sorted(LAYOUT_PARAM_WRAPPER_MACROS))
def test_layout_param_wrapper_rejects_huge(macro: str) -> None:
    latex = rf"\{macro}{{huge}}{{\teiP{{Texte.}}}}"
    with pytest.raises(LatexParseError, match="Invalid size"):
        _Parser(latex).parse_nodes()


# ---------------------------------------------------------------------------
# 8.3 — Commandes autonomes : lateiPageBreak, lateiClearPage
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("macro", sorted(LAYOUT_STANDALONE_MACROS))
def test_layout_standalone_produces_no_nodes(macro: str) -> None:
    latex = rf"\{macro}"
    nodes = _Parser(latex).parse_nodes()
    assert nodes == []


def test_layout_standalone_between_paragraphs_yields_only_paragraphs() -> None:
    latex = r"\teiP{Avant.}\lateiPageBreak\teiP{Après.}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 2
    assert all(isinstance(n, ElementNode) and n.name == "p" for n in nodes)


def test_latei_clear_page_between_paragraphs_yields_only_paragraphs() -> None:
    latex = r"\teiP{Avant.}\lateiClearPage\teiP{Après.}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 2
    assert all(isinstance(n, ElementNode) and n.name == "p" for n in nodes)


# ---------------------------------------------------------------------------
# 8.4 — Commandes autonomes paramétrées : lateiVSpace
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("size", ["small", "medium", "large"])
def test_latei_vspace_produces_no_nodes(size: str) -> None:
    latex = rf"\lateiVSpace{{{size}}}"
    nodes = _Parser(latex).parse_nodes()
    assert nodes == []


def test_latei_vspace_between_paragraphs_yields_only_paragraphs() -> None:
    latex = r"\teiP{Avant.}\lateiVSpace{medium}\teiP{Après.}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 2
    assert all(isinstance(n, ElementNode) and n.name == "p" for n in nodes)


def test_latei_vspace_rejects_invalid_size() -> None:
    with pytest.raises(LatexParseError, match="Invalid size"):
        _Parser(r"\lateiVSpace{12pt}").parse_nodes()


def test_latei_vspace_rejects_arbitrary_dimension() -> None:
    with pytest.raises(LatexParseError, match="Invalid size"):
        _Parser(r"\lateiVSpace{huge}").parse_nodes()


# ---------------------------------------------------------------------------
# 8.5 — Imbrication de commandes \latei...
# ---------------------------------------------------------------------------

def test_nested_param_wrapper_and_simple_wrapper() -> None:
    latex = r"\lateiSpaceBefore{small}{\lateiNoIndent{\teiP{Texte.}}}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 1
    assert isinstance(nodes[0], ElementNode)
    assert nodes[0].name == "p"


def test_nested_wrappers_all_transparent() -> None:
    latex = r"\lateiPageBreakBefore{\lateiNoIndent{\teiP[xmlid={p-042}]{Contenu.}}}"
    nodes = _Parser(latex).parse_nodes()
    assert len(nodes) == 1
    node = nodes[0]
    assert isinstance(node, ElementNode)
    assert node.name == "p"
    assert node.attrs.get("{http://www.w3.org/XML/1998/namespace}id") == "p-042"


def test_standalone_and_vspace_together_produce_no_nodes() -> None:
    latex = r"\lateiPageBreak\lateiVSpace{large}\lateiClearPage"
    nodes = _Parser(latex).parse_nodes()
    assert nodes == []


# ---------------------------------------------------------------------------
# 8.6 — LaTeX brut rejeté dans la zone réversible
# ---------------------------------------------------------------------------

def test_noindent_rejected() -> None:
    with pytest.raises(LatexParseError):
        _Parser(r"\noindent\teiP{Texte.}").parse_nodes()


def test_vspace_raw_rejected() -> None:
    with pytest.raises(LatexParseError):
        _Parser(r"\vspace{1em}").parse_nodes()


def test_newpage_rejected() -> None:
    with pytest.raises(LatexParseError):
        _Parser(r"\newpage").parse_nodes()


def test_clearpage_rejected() -> None:
    with pytest.raises(LatexParseError):
        _Parser(r"\clearpage").parse_nodes()


def test_nopagebreak_rejected() -> None:
    with pytest.raises(LatexParseError):
        _Parser(r"\nopagebreak").parse_nodes()


def test_pagebreak_raw_rejected() -> None:
    with pytest.raises(LatexParseError):
        _Parser(r"\pagebreak").parse_nodes()


# ---------------------------------------------------------------------------
# 8.7 — Toutes les macros publiques définies dans latei_macros.tex
# ---------------------------------------------------------------------------

_ALL_PUBLIC_MACROS = (
    LAYOUT_WRAPPER_MACROS
    | LAYOUT_PARAM_WRAPPER_MACROS
    | LAYOUT_STANDALONE_MACROS
    | LAYOUT_PARAM_STANDALONE_MACROS
)


@pytest.mark.parametrize("macro", sorted(_ALL_PUBLIC_MACROS))
def test_macro_defined_in_latei_macros_tex(macro: str) -> None:
    source = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert rf"\{macro}" in source, f"\\{macro} introuvable dans latei_macros.tex"


def test_latei_layout_commands_doc_covers_all_macros() -> None:
    doc = Path("LATEI_LAYOUT_COMMANDS.md").read_text(encoding="utf-8")
    for macro in _ALL_PUBLIC_MACROS:
        assert macro in doc, f"{macro} absent de LATEI_LAYOUT_COMMANDS.md"


def test_mode_emploi_covers_all_macros() -> None:
    doc = Path("MODE_EMPLOI_LATEI_EDITRICES.md").read_text(encoding="utf-8")
    for macro in _ALL_PUBLIC_MACROS:
        assert macro in doc, f"{macro} absent de MODE_EMPLOI_LATEI_EDITRICES.md"
