from __future__ import annotations

"""Writer for controlled semantic LaTeX from the reversible TEI tree.

This module does not emit free-form presentation LaTeX. It emits a small,
controlled semantic LaTeX vocabulary that should remain readable and
reversible back to the Python document tree, then to TEI Commons-Publishing.
"""

from purh_site.utils import TEI_NS, XML_NS

from .nodes import ElementNode, Node, TextNode

ENVIRONMENT_ELEMENTS = {
    "bibl": "teiBibl",
    "cit": "teiCit",
    "div": "teiDiv",
    "figure": "teiFigure",
    "lg": "teiLg",
    "list": "teiList",
    "table": "teiTable",
}

# Elements whose direct prose runs on regardless of nesting depth (note is
# sticky like the HTML XSLT's "note//cit" match; p/item are not sticky in
# the XSLT — it only matches "p/cit" one level down — but nothing block-level
# can legally nest deeper inside a TEI <p>/<item> anyway, so treating them as
# sticky too is harmless and simpler). See _write_quote.
_INLINE_QUOTE_HOST_ELEMENTS = {"p", "item", "note"}

EMPTY_MACRO_ELEMENTS = {
    "anchor": "teiAnchor",
    "graphic": "teiGraphic",
    "lb": "teiLb",
    "pb": "teiPb",
    "ptr": "teiPtr",
}

MACRO_ELEMENTS = {
    "author": "teiAuthor",
    "biblScope": "teiBiblScope",
    "date": "teiDate",
    "editor": "teiEditor",
    "foreign": "teiForeign",
    "formula": "teiFormula",
    "head": "teiHead",
    "hi": "teiHi",
    "idno": "teiIdno",
    "item": "teiItem",
    "l": "teiL",
    "label": "teiLabel",
    "name": "teiName",
    "note": "teiNote",
    "num": "teiNum",
    "orgName": "teiOrgName",
    "p": "teiP",
    "persName": "teiPersName",
    "placeName": "teiPlaceName",
    "publisher": "teiPublisher",
    "q": "teiQ",
    "ref": "teiRef",
    "said": "teiSaid",
    "term": "teiTerm",
    "title": "teiTitle",
}


def write_latex(node: Node, inline_quote_context: bool = False) -> str:
    if isinstance(node, TextNode):
        return escape_latex(node.text)
    if isinstance(node, ElementNode):
        return _write_element(node, inline_quote_context)
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
        # A literal "[" is not special to LaTeX compilation itself, but our
        # own reader treats "[" right after a controlled macro name as the
        # start of that macro's option list (see _parse_options) — genuine
        # prose containing an editorial elision bracket ("[…]", common in
        # scholarly quotations) directly after an empty macro like \teiLb
        # would otherwise be misparsed as if it belonged to that macro
        # ("Expected '=' after option key"). The LaTeX idiom "{[}" avoids
        # that ambiguity for a *reader's* option-list check, but its own
        # leading "{" then collides with the separate "must not have
        # braced content" check empty macros do (\teiLb{[}... looks like
        # \teiLb is being given an argument). \lbrack{}/\rbrack{} are
        # ordinary control words (like \textbackslash{}), starting with
        # neither "{" nor "[", so neither check can ever trip on them.
        "[": r"\lbrack{}",
        "]": r"\rbrack{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _write_element(node: ElementNode, inline_quote_context: bool) -> str:
    name = node.local_name
    if name == "ref":
        return _write_ref(node, inline_quote_context)
    if name == "formula":
        return _write_formula(node)
    if name == "table":
        return _write_table(node, inline_quote_context)
    if name == "row":
        return _write_row(node, inline_quote_context)
    if name == "cell":
        return _write_cell(node, inline_quote_context)
    if name == "quote":
        return _write_quote(node, inline_quote_context)
    if name in ENVIRONMENT_ELEMENTS:
        return _environment(ENVIRONMENT_ELEMENTS[name], _options(node), _children_latex(node, inline_quote_context))
    if name in EMPTY_MACRO_ELEMENTS:
        return _empty_macro(EMPTY_MACRO_ELEMENTS[name], _options(node))
    if name in MACRO_ELEMENTS:
        return _macro(MACRO_ELEMENTS[name], _options(node), _children_latex(node, inline_quote_context))
    return _generic_element(node, inline_quote_context)


def _write_ref(node: ElementNode, inline_quote_context: bool) -> str:
    """<ref target="#id"> needs internal PDF navigation (\\hyperlink), not an
    external \\href — but \\# is a character-insertion primitive in LaTeX,
    not expandable text, so the internal/external distinction cannot be made
    reliably at the macro level once "#" has been escaped. Made here instead:
    an internal target is passed as a separate, unescaped "internaltarget"
    option (leading "#" stripped), and \\teiRef only has to check whether
    that option is present."""
    attrs = _latex_attrs(node)
    target = attrs.pop("target", None)
    if target is not None:
        if target.startswith("#"):
            attrs["internaltarget"] = target[1:]
        else:
            attrs["target"] = target
    return _macro("teiRef", _format_options(attrs), _children_latex(node, inline_quote_context))


def _write_formula(node: ElementNode) -> str:
    """<formula notation="latex"> content is itself LaTeX math source (its
    TEI text already includes its own \\(...\\) / \\[...\\] delimiters) — it
    must reach the compiler verbatim. Escaping it like ordinary prose (the
    default for every other element) would print the literal escaped source
    in the PDF instead of a typeset formula, so its raw text is used as-is
    rather than routed through write_latex()/escape_latex()."""
    return _macro("teiFormula", _options(node), _raw_text(node))


def _raw_text(node: Node) -> str:
    if isinstance(node, TextNode):
        return node.text
    if isinstance(node, ElementNode):
        return "".join(_raw_text(child) for child in node.children)
    raise TypeError(f"Unsupported reversible node: {type(node).__name__}")


def _write_table(node: ElementNode, inline_quote_context: bool) -> str:
    """teiTable builds a real tabular grid (longtable/booktabs), which needs
    the column count up front to declare its column spec — LaTeX cannot
    discover this from the row/cell environments as they are typeset one at
    a time. Computed here, from the tree, and passed as a "numcols" option
    (a table-level count, not to be confused with a cell's own "cols" —
    its colspan)."""
    attrs = dict(_latex_attrs(node))
    attrs["numcols"] = str(_table_column_count(node))
    return _environment("teiTable", _format_options(attrs), _children_latex(node, inline_quote_context))


def _table_column_count(node: ElementNode) -> int:
    max_columns = 1
    for row in node.children:
        if not (isinstance(row, ElementNode) and row.local_name == "row"):
            continue
        columns = 0
        for cell in row.children:
            if not (isinstance(cell, ElementNode) and cell.local_name == "cell"):
                continue
            span_raw = cell.get_attr("cols") or "1"
            try:
                span = int(span_raw)
            except ValueError:
                span = 1
            columns += max(span, 1)
        max_columns = max(max_columns, columns)
    return max_columns


def _write_row(node: ElementNode, inline_quote_context: bool) -> str:
    """Cells are joined with a literal "&" written directly into the LaTeX
    source, not inserted conditionally by a macro at compile time: TeX's
    \\ifnum...\\fi false-branch skipping uses a tokenizer that does not know
    "&" is special inside an alignment, and corrupts the tabular's column
    scan ("Incomplete \\ifnum") when a bare "&" only appears inside a
    conditionally-skipped branch. Non-cell children (stray whitespace text
    from source indentation) are dropped: TEI rows carry no other content.

    A header row's \\rowcolor (référentiel PURH v0.6 §11.3, "fond foncé noir
    30 %") has the same constraint as a spanning cell's \\multicolumn: it
    must be the literal, unwrapped first token TeX's alignment scanner sees
    for the row, or colortbl's internal \\noalign is "misplaced" and the
    whole tabular breaks. So it is written directly here, before \\teiRow,
    rather than left to a conditional inside that macro (confirmed by
    reproduction: \\iflateirowisheader\\rowcolor{...}\\fi inside \\teiRow
    raised "Misplaced \\noalign")."""
    cells = [child for child in node.children if isinstance(child, ElementNode) and child.local_name == "cell"]
    content = " & ".join(_write_cell(cell, inline_quote_context) for cell in cells)
    role = node.get_attr("role")
    prefix = r"\rowcolor{black!30}" if role in ("label", "header") else ""
    return prefix + _macro("teiRow", _options(node), content)


def _write_cell(node: ElementNode, inline_quote_context: bool) -> str:
    """A spanning cell's \\multicolumn must be the literal, unwrapped first
    token TeX's alignment scanner sees for that cell: wrapping it inside any
    macro or environment (even a plain, non-protected one — confirmed by
    isolated reproduction) makes TeX's \\omit look-ahead miss it, corrupting
    the whole tabular ("Misplaced \\omit"). So it is written directly here
    rather than left to a \\teiCell macro, and only for cells that actually
    span (@cols on <cell>) — plain cells stay a single \\teiCell call, no
    \\multicolumn wrapper at all."""
    attrs = dict(_latex_attrs(node))
    span_raw = attrs.pop("cols", None) or "1"
    try:
        span = int(span_raw)
    except ValueError:
        span = 1
    cell_macro = _macro("teiCell", _format_options(attrs), _children_latex(node, inline_quote_context))
    if span > 1:
        return f"\\multicolumn{{{span}}}{{l}}{{{cell_macro}}}"
    return cell_macro


def _write_quote(node: ElementNode, inline_quote_context: bool) -> str:
    """<quote> renders as a block quotation by default (\\teiQuote ->
    PurhBlockQuote, LaTeX's own quote environment: indentation, no marks —
    the standard French convention for set-off quotations). But used inline
    mid-sentence — inside <p>/<item>, or anywhere inside <note>, the same
    distinction the HTML XSLT already draws between cit-block/div and
    cit-inline/span (tei_to_html.xsl) — forcing that environment breaks the
    paragraph, since \\begin{quote}/\\end{quote} always insert \\list/\\par
    boundaries even when spliced mid-sentence inside a \\teiP{...} argument.
    Inline uses \\teiQuoteInline instead: a plain macro, no paragraph break,
    that adds the correct guillemets via csquotes' \\enquote (matching
    \\teiQ). A straight quote mark sometimes typed by hand right at the
    very start/end of the quoted text (redundant now that the element
    itself carries quotation semantics) would double up with \\enquote's
    own marks, so it is stripped in that case — only when both ends match,
    to avoid guessing on ambiguous content."""
    if inline_quote_context:
        children = _strip_redundant_straight_quote_marks(node.children)
        return _macro("teiQuoteInline", _options(node), _join_children_latex(children, True))
    return _environment("teiQuote", _options(node), _children_latex(node, inline_quote_context))


_STRAIGHT_DOUBLE_QUOTE = '"'


def _strip_redundant_straight_quote_marks(children: list[Node]) -> list[Node]:
    if not children:
        return children
    first, last = children[0], children[-1]
    if not (isinstance(first, TextNode) and isinstance(last, TextNode)):
        return children
    if first is last:
        text = first.text
        if len(text) < 2 or text[0] != _STRAIGHT_DOUBLE_QUOTE or text[-1] != _STRAIGHT_DOUBLE_QUOTE:
            return children
        return [TextNode(text[1:-1])]
    if not (first.text.startswith(_STRAIGHT_DOUBLE_QUOTE) and last.text.endswith(_STRAIGHT_DOUBLE_QUOTE)):
        return children
    stripped = list(children)
    stripped[0] = TextNode(first.text[1:])
    stripped[-1] = TextNode(last.text[:-1])
    return stripped


def _generic_element(node: ElementNode, inline_quote_context: bool) -> str:
    attrs = {"name": node.local_name, **_latex_attrs(node)}
    if node.namespace and node.namespace != TEI_NS:
        attrs["namespace"] = node.namespace
    return _environment("teiElement", _format_options(attrs), _children_latex(node, inline_quote_context))


def _children_latex(node: ElementNode, inline_quote_context: bool) -> str:
    child_context = inline_quote_context or node.local_name in _INLINE_QUOTE_HOST_ELEMENTS
    return _join_children_latex(node.children, child_context)


def _join_children_latex(children: list[Node], inline_quote_context: bool) -> str:
    return "".join(write_latex(child, inline_quote_context) for child in children)


def _environment(name: str, options: str, content: str) -> str:
    return f"\\begin{{{name}}}{options}\n{content}\n\\end{{{name}}}"


def _macro(name: str, options: str, content: str) -> str:
    return f"\\{name}{options}{{{content}}}"


def _empty_macro(name: str, options: str) -> str:
    if options:
        return f"\\{name}{options}"
    # A control word (multi-letter macro name) glued directly to following
    # prose that starts with a letter — real case: "<lb/>Parce..." in
    # poetry, no space in the source — is not "\teiLb" + text "Parce": TeX
    # consumes all subsequent letters into the control word's own name,
    # producing a bogus "\teiLbParce" ("Undefined control sequence"). "{}"
    # is a hard boundary a letter can never extend past; harmless and
    # invisible otherwise. Only needed without options: "]" already stops
    # name-consumption, so \teiLb[n={3}]Parce is never at risk.
    return f"\\{name}{{}}"


def _options(node: ElementNode) -> str:
    return _format_options(_latex_attrs(node))


# xmlid (and internaltarget, an xmlid fragment stripped of its leading "#")
# are identifiers, not prose: XML NCName syntax already forbids every
# character escape_latex() would otherwise escape. Escaping them anyway
# would make \hypertarget/\hyperlink names disagree once expanded (\_ is a
# command, not literal text, so a hypertarget and the hyperlink meant to
# reach it can end up with different PDF destination names).
_UNESCAPED_OPTION_KEYS = {"xmlid", "internaltarget"}


def _format_options(attrs: dict[str, str]) -> str:
    if not attrs:
        return ""
    body = ",".join(f"{key}={{{_format_option_value(key, value)}}}" for key, value in attrs.items())
    return f"[{body}]"


def _format_option_value(key: str, value: str) -> str:
    if key in _UNESCAPED_OPTION_KEYS:
        return value
    return escape_latex(value)


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
