from __future__ import annotations

"""Reader for the controlled semantic LaTeX emitted by `latex_writer`.

This module does not parse general LaTeX. It only reads the controlled
semantic grammar documented in `LATEX_GRAMMAR.md`; any unknown macro is an
explicit parse error rather than silently interpreted or discarded.
"""

from dataclasses import dataclass

from purh_site.utils import TEI_NS, XML_NS

from .nodes import ElementNode, Node, TextNode, make_element_node


class LatexParseError(ValueError):
    """Raised when controlled semantic LaTeX cannot be parsed."""


MACRO_TO_ELEMENT = {
    "teiAuthor": "author",
    "teiBiblScope": "biblScope",
    "teiCell": "cell",
    "teiDate": "date",
    "teiEditor": "editor",
    "teiForeign": "foreign",
    "teiFormula": "formula",
    "teiHead": "head",
    "teiHi": "hi",
    "teiIdno": "idno",
    "teiItem": "item",
    "teiLabel": "label",
    "teiName": "name",
    "teiNote": "note",
    "teiNum": "num",
    "teiOrgName": "orgName",
    "teiP": "p",
    "teiPersName": "persName",
    "teiPlaceName": "placeName",
    "teiPublisher": "publisher",
    "teiQ": "q",
    "teiQuoteInline": "quote",
    "teiRef": "ref",
    "teiRow": "row",
    "teiSaid": "said",
    "teiTerm": "term",
    "teiTitle": "title",
}

EMPTY_MACRO_TO_ELEMENT = {
    "teiAnchor": "anchor",
    "teiGraphic": "graphic",
    "teiLb": "lb",
    "teiPb": "pb",
    "teiPtr": "ptr",
}

ENVIRONMENT_TO_ELEMENT = {
    "teiBibl": "bibl",
    "teiCit": "cit",
    "teiDiv": "div",
    "teiFigure": "figure",
    "teiList": "list",
    "teiQuote": "quote",
    "teiTable": "table",
}

LAYOUT_WRAPPER_MACROS = {
    "lateiNoIndent",
    "lateiIndent",
    "lateiPageBreakBefore",
    "lateiPageBreakAfter",
    "lateiClearPageBefore",
    "lateiClearPageAfter",
    "lateiKeepWithNext",
    "lateiKeepTogether",
    "lateiNoPageBreakBefore",
    "lateiNoPageBreakAfter",
}

LAYOUT_PARAM_WRAPPER_MACROS = {
    "lateiSpaceBefore",
    "lateiSpaceAfter",
}

LAYOUT_STANDALONE_MACROS = {
    "lateiPageBreak",
    "lateiClearPage",
}

LAYOUT_PARAM_STANDALONE_MACROS = {
    "lateiVSpace",
}

_VALID_SPACE_SIZES = {"small", "medium", "large"}

KNOWN_TEXT_ESCAPES = {
    r"\textbackslash{}": "\\",
    r"\textasciicircum{}": "^",
    r"\textasciitilde{}": "~",
    r"\{": "{",
    r"\}": "}",
    r"\%": "%",
    r"\$": "$",
    r"\&": "&",
    r"\_": "_",
    r"\#": "#",
}


@dataclass(slots=True)
class _Parser:
    latex: str
    pos: int = 0

    def parse_document(self) -> Node:
        nodes = self.parse_nodes()
        if len(nodes) == 1:
            return nodes[0]
        if nodes and all(isinstance(node, TextNode) for node in nodes):
            return TextNode("".join(node.text for node in nodes))
        raise LatexParseError("Expected one root node in controlled LaTeX document.")

    def parse_nodes(self, end_environment: str | None = None) -> list[Node]:
        nodes: list[Node] = []
        text_start = self.pos

        while self.pos < len(self.latex):
            if end_environment and self._starts_end_environment(end_environment):
                text_end = self.pos
                if text_end > text_start and self.latex[text_end - 1] == "\n":
                    text_end -= 1
                self._flush_text(nodes, text_start, text_end)
                self._consume_end_environment(end_environment)
                return nodes

            if self.latex.startswith(r"\begin{", self.pos):
                self._flush_text(nodes, text_start, self.pos)
                nodes.append(self._parse_environment())
                text_start = self.pos
                continue

            macro_name = self._controlled_macro_at_pos()
            if macro_name:
                self._flush_text(nodes, text_start, self.pos)
                if macro_name in LAYOUT_WRAPPER_MACROS:
                    nodes.extend(self._parse_layout_wrapper(macro_name))
                elif macro_name in LAYOUT_PARAM_WRAPPER_MACROS:
                    nodes.extend(self._parse_layout_param_wrapper(macro_name))
                elif macro_name in LAYOUT_STANDALONE_MACROS:
                    self._consume_layout_standalone(macro_name)
                elif macro_name in LAYOUT_PARAM_STANDALONE_MACROS:
                    self._consume_layout_param_standalone(macro_name)
                else:
                    nodes.append(self._parse_macro(macro_name))
                text_start = self.pos
                continue

            if self.latex[self.pos] == "\\" and not self._starts_known_text_escape():
                raise LatexParseError(f"Unknown macro or escape at offset {self.pos}.")

            self.pos += 1

        if end_environment:
            raise LatexParseError(f"Missing \\end{{{end_environment}}}.")
        self._flush_text(nodes, text_start, self.pos)
        return nodes

    def _flush_text(self, nodes: list[Node], start: int, end: int) -> None:
        if end > start:
            nodes.append(TextNode(unescape_latex(self.latex[start:end])))

    def _parse_macro(self, macro_name: str) -> ElementNode:
        self.pos += len(macro_name) + 1
        attrs = self._parse_options()
        if macro_name == "teiRef":
            internal_target = attrs.pop("internaltarget", None)
            if internal_target is not None:
                attrs["target"] = f"#{internal_target}"
        if macro_name in EMPTY_MACRO_TO_ELEMENT:
            if self.pos < len(self.latex) and self.latex[self.pos] == "{":
                raise LatexParseError(f"Empty controlled macro \\{macro_name} must not have braced content.")
            return make_element_node(EMPTY_MACRO_TO_ELEMENT[macro_name], attrs, [], namespace=TEI_NS)
        element_name = MACRO_TO_ELEMENT[macro_name]
        if self.pos >= len(self.latex) or self.latex[self.pos] != "{":
            raise LatexParseError(f"Expected braced content for \\{macro_name}.")
        if macro_name == "teiFormula":
            # Formula content is raw LaTeX math source, not controlled TEI
            # macro grammar (\frac, \partial... are not registered macros) —
            # read verbatim rather than recursively parsing it as content.
            content = self._read_group()
            return make_element_node("formula", attrs, [TextNode(content)], namespace=TEI_NS)
        if macro_name == "teiRow":
            # Cells are joined by a literal "&" written straight into the
            # source (see _write_row/_write_cell in latex_writer), not by
            # controlled macro grammar — split on top-level "&" instead of
            # recursively parsing as ordinary content.
            content = self._read_group()
            return make_element_node("row", attrs, _parse_row_cells(content), namespace=TEI_NS)
        content = self._read_group()
        children = _Parser(content).parse_nodes()
        return make_element_node(element_name, attrs, children, namespace=TEI_NS)

    def _parse_environment(self) -> ElementNode:
        self.pos += len(r"\begin")
        env_name = self._read_group()
        if env_name == "teiElement":
            attrs = self._parse_options()
            self._consume_cosmetic_environment_newline()
            element_name = attrs.pop("name", None)
            namespace = attrs.pop("namespace", TEI_NS)
            if not element_name:
                raise LatexParseError("teiElement requires a name option.")
            children = self.parse_nodes(end_environment=env_name)
            return ElementNode(name=element_name, attrs=attrs, children=children, namespace=namespace)
        if env_name not in ENVIRONMENT_TO_ELEMENT:
            raise LatexParseError(f"Unknown controlled environment: {env_name}.")
        attrs = self._parse_options()
        if env_name == "teiTable":
            # numcols is synthesized by the writer (_write_table) to size
            # the longtable's column spec; it has no TEI source counterpart.
            attrs.pop("numcols", None)
        self._consume_cosmetic_environment_newline()
        children = self.parse_nodes(end_environment=env_name)
        return make_element_node(ENVIRONMENT_TO_ELEMENT[env_name], attrs, children, namespace=TEI_NS)

    def _parse_options(self) -> dict[str, str]:
        if self.pos >= len(self.latex) or self.latex[self.pos] != "[":
            return {}
        self.pos += 1
        start = self.pos
        depth = 0
        while self.pos < len(self.latex):
            char = self.latex[self.pos]
            if char == "\\":
                self.pos += 1
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth < 0:
                    raise LatexParseError("Unbalanced option braces.")
            elif char == "]" and depth == 0:
                raw = self.latex[start:self.pos]
                self.pos += 1
                return parse_options(raw)
            self.pos += 1
        raise LatexParseError("Unclosed option block.")

    def _read_group(self) -> str:
        if self.pos >= len(self.latex) or self.latex[self.pos] != "{":
            raise LatexParseError(f"Expected group at offset {self.pos}.")
        self.pos += 1
        start = self.pos
        depth = 1
        while self.pos < len(self.latex):
            char = self.latex[self.pos]
            if char == "\\":
                self.pos += 2
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    content = self.latex[start:self.pos]
                    self.pos += 1
                    return content
            self.pos += 1
        raise LatexParseError("Unclosed braced group.")

    def _parse_layout_wrapper(self, macro_name: str) -> list[Node]:
        self.pos += len(macro_name) + 1
        if self.pos >= len(self.latex) or self.latex[self.pos] != "{":
            raise LatexParseError(f"Expected braced content for \\{macro_name}.")
        content = self._read_group()
        return _Parser(content).parse_nodes()

    def _parse_layout_param_wrapper(self, macro_name: str) -> list[Node]:
        self.pos += len(macro_name) + 1
        size = self._read_group()
        if size not in _VALID_SPACE_SIZES:
            raise LatexParseError(
                f"Invalid size '{size}' for \\{macro_name}. Expected: small, medium, large."
            )
        if self.pos >= len(self.latex) or self.latex[self.pos] != "{":
            raise LatexParseError(f"Expected braced content after size for \\{macro_name}.")
        content = self._read_group()
        return _Parser(content).parse_nodes()

    def _consume_layout_standalone(self, macro_name: str) -> None:
        self.pos += len(macro_name) + 1

    def _consume_layout_param_standalone(self, macro_name: str) -> None:
        self.pos += len(macro_name) + 1
        size = self._read_group()
        if size not in _VALID_SPACE_SIZES:
            raise LatexParseError(
                f"Invalid size '{size}' for \\{macro_name}. Expected: small, medium, large."
            )

    def _controlled_macro_at_pos(self) -> str | None:
        macro_names = [
            *MACRO_TO_ELEMENT,
            *EMPTY_MACRO_TO_ELEMENT,
            *LAYOUT_WRAPPER_MACROS,
            *LAYOUT_PARAM_WRAPPER_MACROS,
            *LAYOUT_STANDALONE_MACROS,
            *LAYOUT_PARAM_STANDALONE_MACROS,
        ]
        for macro_name in sorted(macro_names, key=len, reverse=True):
            if self.latex.startswith(f"\\{macro_name}", self.pos):
                return macro_name
        return None

    def _starts_known_text_escape(self) -> bool:
        return any(self.latex.startswith(escape, self.pos) for escape in KNOWN_TEXT_ESCAPES)

    def _starts_end_environment(self, env_name: str) -> bool:
        return self.latex.startswith(f"\\end{{{env_name}}}", self.pos)

    def _consume_end_environment(self, env_name: str) -> None:
        self.pos += len(f"\\end{{{env_name}}}")

    def _consume_cosmetic_environment_newline(self) -> None:
        if self.pos < len(self.latex) and self.latex[self.pos] == "\n":
            self.pos += 1


def _parse_row_cells(content: str) -> list[Node]:
    return [_parse_row_cell(segment) for segment in _split_top_level_ampersand(content)]


def _split_top_level_ampersand(content: str) -> list[str]:
    segments: list[str] = []
    depth = 0
    start = 0
    pos = 0
    while pos < len(content):
        char = content[pos]
        if char == "\\":
            pos += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "&" and depth == 0:
            segments.append(content[start:pos])
            start = pos + 1
        pos += 1
    segments.append(content[start:pos])
    return segments


def _parse_row_cell(segment: str) -> ElementNode:
    text = segment.strip()
    span = 1
    if text.startswith(r"\multicolumn{"):
        parser = _Parser(text, len(r"\multicolumn"))
        span_raw = parser._read_group()
        try:
            span = int(span_raw)
        except ValueError:
            raise LatexParseError(f"Invalid \\multicolumn span: {span_raw!r}.") from None
        parser._read_group()  # column type (always "l"), not reversible content
        cell_source = parser._read_group()
    else:
        cell_source = text
    cell_parser = _Parser(cell_source)
    macro_name = cell_parser._controlled_macro_at_pos()
    if macro_name != "teiCell":
        raise LatexParseError(f"Expected \\teiCell in table cell, got: {cell_source[:30]!r}.")
    cell_node = cell_parser._parse_macro(macro_name)
    if span != 1:
        cell_node.attrs["cols"] = str(span)
    return cell_node


_BEGIN_LATEI_DOCUMENT = r"\begin{lateiDocument}"
_END_LATEI_DOCUMENT = r"\end{lateiDocument}"


def extract_latei_document_zone(monofile_text: str) -> str:
    """Extract the reversible body from a complete LaTEI monofile.

    Returns only the text between \\begin{lateiDocument} and
    \\end{lateiDocument}. Everything outside (preamble, macros, mappings,
    title page) is ignored. This function does not parse LaTeX; it is a
    plain string search.
    """
    first_begin = monofile_text.find(_BEGIN_LATEI_DOCUMENT)
    if first_begin == -1:
        raise LatexParseError(r"Missing \begin{lateiDocument} in monofile text.")
    second_begin = monofile_text.find(_BEGIN_LATEI_DOCUMENT, first_begin + 1)
    if second_begin != -1:
        raise LatexParseError(
            r"Multiple \begin{lateiDocument} found in monofile text; expected exactly one."
        )
    content_start = first_begin + len(_BEGIN_LATEI_DOCUMENT)
    if monofile_text[content_start : content_start + 1] == "\n":
        content_start += 1
    end = monofile_text.find(_END_LATEI_DOCUMENT, content_start)
    if end == -1:
        raise LatexParseError(
            r"Missing \end{lateiDocument} after \begin{lateiDocument} in monofile text."
        )
    return monofile_text[content_start:end].rstrip("\n")


def read_latex(latex: str) -> Node:
    return _Parser(latex).parse_document()


def read_latex_document(latex: str) -> ElementNode:
    node = read_latex(latex)
    if not isinstance(node, ElementNode):
        raise LatexParseError("Expected an element root in controlled LaTeX document.")
    return node


def parse_options(raw: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    pos = 0
    while pos < len(raw):
        while pos < len(raw) and raw[pos].isspace():
            pos += 1
        key_start = pos
        while pos < len(raw) and raw[pos] not in "={},":
            pos += 1
        key = raw[key_start:pos].strip()
        if not key:
            raise LatexParseError("Expected option key.")
        if pos >= len(raw) or raw[pos] != "=":
            raise LatexParseError(f"Expected '=' after option key {key}.")
        pos += 1
        if pos >= len(raw) or raw[pos] != "{":
            raise LatexParseError(f"Expected braced option value for {key}.")
        value, pos = _read_option_value(raw, pos)
        attrs[_attribute_name(key)] = unescape_latex(value)
        if pos < len(raw):
            if raw[pos] != ",":
                raise LatexParseError("Expected comma between options.")
            pos += 1
    return attrs


def unescape_latex(text: str) -> str:
    result: list[str] = []
    pos = 0
    while pos < len(text):
        matched = False
        for escape, value in KNOWN_TEXT_ESCAPES.items():
            if text.startswith(escape, pos):
                result.append(value)
                pos += len(escape)
                matched = True
                break
        if matched:
            continue
        result.append(text[pos])
        pos += 1
    return "".join(result)


def _read_option_value(raw: str, pos: int) -> tuple[str, int]:
    pos += 1
    start = pos
    depth = 1
    while pos < len(raw):
        char = raw[pos]
        if char == "\\":
            pos += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return raw[start:pos], pos + 1
        pos += 1
    raise LatexParseError("Unclosed option value.")


def _attribute_name(name: str) -> str:
    if name == "xmlid":
        return f"{{{XML_NS}}}id"
    if name == "xmllang":
        return f"{{{XML_NS}}}lang"
    return name
