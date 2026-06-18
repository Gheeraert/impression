# Reversible TEI Core

`purh_site.reversible` is an experimental documentary core for conservative
round-trips between TEI, a Python tree, and a controlled semantic LaTeX format.
It is not wired into the current static generator and does not replace the
existing renderers.

The intended experimental chain is:

```text
TEI -> reversible Python tree -> controlled LaTeX -> reversible Python tree -> TEI
```

The Python tree is a reversible projection of TEI, not a competing canonical
model. It keeps element names, namespaces, attributes, text, tails, mixed
content, child order, and unknown elements whenever possible.

## Controlled LaTeX

The LaTeX produced here is not general-purpose LaTeX. It is a stable semantic
serialization intended to be read back by `latex_reader.py`.

Specialized TEI elements use dedicated controlled macros or environments, for
example `\teiP{...}`, `\teiHi[...]{...}`, `\begin{teiDiv}[...]`, and
`\begin{teiTable}[...]`.

Elements without a dedicated controlled form are preserved through the generic
fallback:

```latex
\begin{teiElement}[name={...},...]
...
\end{teiElement}
```

This fallback is part of the reversible contract: unsupported TEI vocabulary
must not be silently flattened or dropped.

## Content And Empty Macros

The grammar distinguishes two macro families:

- content macros always have a braced content group, even when empty:
  `\teiP{}`, `\teiHead{}`, `\teiHi[rend={italic}]{}`;
- empty macros never have a braced content group:
  `\teiGraphic[...]`, `\teiPtr[...]`, `\teiLb[...]`, `\teiPb[...]`.

An empty macro followed by braced content is an explicit parse error.

See `LATEX_GRAMMAR.md` for the current controlled LaTeX grammar and
`TEI_COVERAGE.md` for the covered TEI vocabulary.

## Non-Goals

- Do not parse general LaTeX.
- Do not produce final typographic LaTeX for publication.
- Do not replace the current HTML, PDF, or static-site renderers.
- Do not convert a complete book yet.
- Do not interpret the full Metopes bibliographic model.

## Experimental Public API

The main import surface currently used by tests is:

- `read_tei_element`
- `write_tei_element`
- `write_latex`
- `read_latex_document`
- `run_tei_latex_tei_roundtrip`
- `compare_tei_elements`

Related diagnostic objects such as `Diagnostic` and `RoundTripResult` are also
exported for inspection.

## Useful Test Commands

```bash
python -m pytest tests/test_reversible_roundtrip.py -q
python -m pytest tests/test_reversible_real_metopes_fragments.py -q
python -m pytest tests -q
```

