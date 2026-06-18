from __future__ import annotations

"""Writer for controlled semantic LaTeX from the reversible TEI tree.

This module does not emit free-form presentation LaTeX. It emits a small,
controlled semantic LaTeX vocabulary that should remain readable and
reversible back to the Python document tree, then to TEI Commons-Publishing.
"""

from purh_site.utils import TEI_NS, XML_NS

from .nodes import ElementNode, Node, TextNode


ENVIRONMENT_ELEMENTS = {
    "div": "teiDiv",
    "figure": "teiFigure",
    "list": "teiList",
    "quote": "teiQuote",
}

MACRO_ELEMENTS = {
    "graphic": "teiGraphic",
    "head": "teiHead",
    "hi": "teiHi",
    "item": "teiItem",
    "note": "teiNote",
    "p": "teiP",
    "ref": "teiRef",
}


def write_latex(node: Node) -> str:
    if isinstance(node, TextNode):
        return escape_latex(node.text)
    if isinstance(node, ElementNode):
        return _write_element(node)
    raise TypeError(f"Unsupported reversible node: {type(node).__name__}")


def write_latex_document(node: ElementNode) -> str:
    return write_latex(node)


def escape_latex(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "%": r"\%",
        "$": r"\$",
        "&": r"\&",
        "_": r"\_",
        "#": r"\#",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _write_element(node: ElementNode) -> str:
    name = node.local_name
    if name in ENVIRONMENT_ELEMENTS:
        return _environment(ENVIRONMENT_ELEMENTS[name], _options(node), _children_latex(node))
    if name in MACRO_ELEMENTS:
        return _macro(MACRO_ELEMENTS[name], _options(node), _children_latex(node))
    return _generic_element(node)


def _generic_element(node: ElementNode) -> str:
    attrs = {"name": node.local_name, **_latex_attrs(node)}
    if node.namespace and node.namespace != TEI_NS:
        attrs["namespace"] = node.namespace
    return _environment("teiElement", _format_options(attrs), _children_latex(node))


def _children_latex(node: ElementNode) -> str:
    return "".join(write_latex(child) for child in node.children)


def _environment(name: str, options: str, content: str) -> str:
    return f"\\begin{{{name}}}{options}\n{content}\n\\end{{{name}}}"


def _macro(name: str, options: str, content: str) -> str:
    if content:
        return f"\\{name}{options}{{{content}}}"
    return f"\\{name}{options}"


def _options(node: ElementNode) -> str:
    return _format_options(_latex_attrs(node))


def _format_options(attrs: dict[str, str]) -> str:
    if not attrs:
        return ""
    body = ",".join(f"{key}={{{escape_latex(value)}}}" for key, value in attrs.items())
    return f"[{body}]"


def _latex_attrs(node: ElementNode) -> dict[str, str]:
    return {_latex_attr_name(key): value for key, value in node.attrs.items()}


def _latex_attr_name(name: str) -> str:
    if name == f"{{{XML_NS}}}id":
        return "xmlid"
    if name == f"{{{XML_NS}}}lang":
        return "xmllang"
    if name.startswith("{"):
        return name.rsplit("}", 1)[1]
    return name.replace(":", "")
