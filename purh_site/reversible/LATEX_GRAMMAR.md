# Controlled Semantic LaTeX Grammar

This LaTeX is not general LaTeX. It is a controlled semantic serialization of
the reversible TEI document tree used by `purh_site.reversible`.

The goal is reversibility: a future `latex_reader.py` must be able to rebuild
the Python tree, then TEI Commons-Publishing, without guessing the intended TEI
semantics. The writer therefore emits only a small vocabulary of TEI-oriented
macros and environments.

## Emitted Forms

Inline or braced-content commands:

```latex
\teiP[...]{...}
\teiHead[...]{...}
\teiHi[...]{...}
\teiNote[...]{...}
\teiRef[...]{...}
\teiItem[...]{...}
\teiGraphic[...]
\teiTitle[...]{...}
\teiForeign[...]{...}
\teiTerm[...]{...}
\teiName[...]{...}
\teiPersName[...]{...}
\teiPlaceName[...]{...}
\teiOrgName[...]{...}
\teiDate[...]{...}
\teiNum[...]{...}
\teiLabel[...]{...}
```

The scholarly inline commands above are braced-content macros. Their
attributes remain ordinary options written as `key={value}`.

Environment forms:

```latex
\begin{teiDiv}[...]
...
\end{teiDiv}

\begin{teiList}[...]
...
\end{teiList}

\begin{teiQuote}[...]
...
\end{teiQuote}

\begin{teiFigure}[...]
...
\end{teiFigure}
```

Unknown or not-yet-specialized TEI elements are preserved with a generic
environment:

```latex
\begin{teiElement}[name={seg},type={...}]
...
\end{teiElement}
```

The `name` option is required for `teiElement`. If the original element was not
in the TEI namespace, the writer may also emit a `namespace={...}` option.

## Attribute Options

Attributes are emitted in LaTeX options:

```latex
[key={value},other={value}]
```

Current conventions:

- `xml:id` becomes `xmlid`.
- `xml:lang` becomes `xmllang`.
- Ordinary TEI attributes keep their local name, for example `type`,
  `subtype`, `rend`, `place`, `target`, `n`, `role`, `ref`, `key`,
  `when`, `from`, `to`, `notBefore`, `notAfter`, `calendar`, and `level`.
- Unknown attributes are preserved as far as possible.
- Attribute values are always braced: `key={value}`.
- Options are separated by commas.

A future reader must parse options while respecting braces. It must not split
naively on every comma, because escaped or future braced values may contain
commas.

## Escaping

Text nodes and option values are escaped by the writer. Generated macros and
environments are not escaped and must not be double-escaped.

The current writer escapes at least:

```text
\ { } % $ & _ # ^ ~
```

A future reader must unescape text and option values when reconstructing the
Python tree.

## Voluntary Limits

- This grammar does not parse general LaTeX.
- It does not promise to read ordinary `\section`, `\emph`, `\footnote`, or
  similar presentation macros.
- Only the macros and environments in this controlled grammar are guaranteed to
  be reversible.
- Unknown macros should produce a diagnostic in a later pass rather than being
  silently interpreted.

## Canonical Example

TEI fragment:

```xml
<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_001">Un <hi rend="italic">mot</hi> avec une <ref target="#x">reference</ref>.</p>
```

Controlled LaTeX:

```latex
\teiP[xmlid={p\_001}]{Un \teiHi[rend={italic}]{mot} avec une \teiRef[target={\#x}]{reference}.}
```
