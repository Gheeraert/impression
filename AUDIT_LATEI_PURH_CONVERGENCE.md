# Audit LaTEI / PURH Convergence

## Scope

This audit prepares convergence between the stable PURH LaTeX/PDF pipeline and
the experimental reversible LaTEI pipeline. It does not change application
behavior, the stable PDF renderer, or the reversible core.

Target architecture:

```text
XML Commons-Publishing / Metopes
-> reversible Python tree
-> LaTEI PURH
-> PURH PDF

LaTEI PURH corrected by humans
-> reversible Python tree
-> XML Commons-Publishing / Metopes
```

## Stable LaTeX/PDF Pipeline

Main files:

- `purh_site/tei_to_model.py`: parses normalized TEI into the stable semantic
  PDF model.
- `purh_site/semantic_model.py`: stable, rendering-oriented model used by the
  PDF pipeline.
- `purh_site/latex_renderer.py`: renders a complete LaTeX document from the
  semantic model.
- `purh_site/pdf_builder.py`: orchestrates TEI -> model -> LaTeX -> optional
  LuaLaTeX PDF compilation.
- `purh_site/site_builder.py`: activates LaTeX/PDF generation when
  `BuildConfig.pdf_export_mode` is `latex` or `latex_pdf`.
- `purh_site/config.py`: defines `pdf_export_mode` and `latex_engine`.
- `purh_site/gui.py`: exposes the stable PDF/LaTeX mode through radio buttons.

Important tests:

- `tests/test_pdf_latex.py`
- `tests/test_pdf_structure.py`
- PDF-related assertions in `tests/test_smoke.py`

Current activation path:

```text
SiteBuilder._finalize_build
-> SiteBuilder._build_pdf_site_artifacts
-> PdfBuilder(... LatexRenderOptions(style="purh") ...)
-> parse_normalized_tei
-> LatexRenderer.render_book
-> optional LuaLaTeX compilation
```

Stable outputs are written under:

```text
assets/generated/book.normalized.xml
assets/generated/book.tex
assets/generated/book.pdf
assets/generated/latex_build.log
assets/generated/pdf_build_report.txt
```

The stable renderer produces a full document, not a fragment. In PURH mode it
uses:

- `\documentclass[12pt,twoside,openany]{book}`
- `geometry` with 155 x 230 mm page size
- `fontspec`, `babel`, `csquotes`, `microtype`, `indentfirst`, `emptypage`
- `titlesec` and `titletoc`
- `fancyhdr`
- `footmisc`
- `graphicx`, `caption`
- `array`, `longtable`, `tabularx`, `booktabs`
- `hyperref`, `bookmark`
- custom macros/environments such as `\PurhSubtitle`,
  `\PurhContributors`, `\PurhTitleExtra`, `PurhBlockQuote`,
  `PurhBibliography`

Main stable rendering commands:

- title page: `titlepage`, `\thispagestyle{empty}`, `\PurhSubtitle`,
  `\PurhContributors`, `\PurhTitleExtra`
- matter structure: `\frontmatter`, `\mainmatter`, `\backmatter`
- divisions: `\part*`, `\chapter`, `\chapter*`, `\addcontentsline`,
  `\markboth`, `\appendix`
- sections: `\section`, `\subsection`, `\subsubsection`
- paragraphs: normal LaTeX paragraph flow, plus hints such as `flushright`,
  bold lead paragraph, `\bigskip`
- notes: `\footnote{...}` with footnote state to avoid nested footnotes
- inline: `\textit`, `\textbf`, `\textsc`, `\textsuperscript`, subscript
  math, `\href`, `\enquote`
- figures: `\includegraphics` or a missing-image fallback, centered caption
  and credits
- bibliography: `PurhBibliography`, hanging entries, `\enquote`,
  `\textit`, DOI/URI links
- lists: `itemize`, `enumerate`, `\item`
- tables: `tabularx`, `\toprule`, `\midrule`, `\bottomrule`; merged-cell
  support is only warned, not rendered
- table of contents: `\tableofcontents` at the end
- blank pages: `emptypage`, `openany`, and explicit clear pages

Technical shape of the stable pipeline:

- It works from normalized TEI, then a lossy-but-useful semantic model.
- Notes are extracted from the inline flow into `Footnote` objects and inserted
  through `NoteRef`.
- `teiHeader` is read for metadata, not printed as document content.
- Bibliography has interpreted paths for `biblStruct`, monographs, articles,
  identifiers, pages, volumes, issues, and people.
- Figures and image paths are normalized in `PdfBuilder` before rendering.

## Reversible LaTEI Pipeline

Main files:

- `purh_site/reversible/nodes.py`: reversible documentary tree.
- `purh_site/reversible/tei_reader.py`: TEI -> reversible tree.
- `purh_site/reversible/tei_writer.py`: reversible tree -> TEI.
- `purh_site/reversible/latex_writer.py`: reversible tree -> controlled LaTEI.
- `purh_site/reversible/latex_reader.py`: controlled LaTEI -> reversible tree.
- `purh_site/reversible/roundtrip.py`: TEI -> LaTEI -> TEI and diagnostics.
- `purh_site/reversible/LATEX_GRAMMAR.md`: controlled grammar.
- `purh_site/reversible/TEI_COVERAGE.md`: covered vocabulary.
- `purh_site/reversible_integration.py`: optional experimental export from a
  real XML file to LaTEI, round-trip XML, and diagnostics.

Current LaTEI commands and environments:

- content macros: `\teiP`, `\teiHead`, `\teiHi`, `\teiNote`, `\teiRef`,
  `\teiItem`, `\teiTitle`, `\teiForeign`, `\teiTerm`, `\teiName`,
  `\teiPersName`, `\teiPlaceName`, `\teiOrgName`, `\teiDate`, `\teiNum`,
  `\teiLabel`, `\teiQ`, `\teiSaid`, `\teiAuthor`, `\teiEditor`,
  `\teiPublisher`, `\teiBiblScope`, `\teiIdno`
- empty macros: `\teiGraphic`, `\teiPtr`, `\teiLb`, `\teiPb`
- environments: `teiDiv`, `teiList`, `teiQuote`, `teiFigure`, `teiCit`,
  `teiBibl`, `teiTable`, `teiRow`, `teiCell`
- fallback: `teiElement` with `name={...}` and optional `namespace={...}`

Attribute conventions:

- `xml:id` -> `xmlid`
- `xml:lang` -> `xmllang`
- ordinary attributes remain local names, such as `type`, `subtype`, `rend`,
  `place`, `target`, `n`, `role`, `ref`, `key`, `when`, `from`, `to`, `level`,
  `unit`, `rows`, `cols`, etc.

Technical shape of the reversible pipeline:

- It preserves XML element names, namespace, attributes, text, tails, mixed
  content, unknown elements, and child order.
- It currently emits a reversible fragment, not a compilable PURH document.
- Its LaTEI commands are semantic carriers; they do not yet have typographic
  LaTeX definitions.
- It can read its own grammar back to the reversible tree and then to TEI.

## Correspondence Table

| TEI semantics | Current LaTEI | Stable LaTeX/PURH target | Difficulty | Notes |
| --- | --- | --- | --- | --- |
| paragraph | `\teiP{...}` | normal paragraph flow | simple | Macro can likely expand to its content plus paragraph handling. |
| heading | `\teiHead{...}` | depends on context: `\chapter`, `\section`, figure title | important | Needs parent context; `head` alone is ambiguous. |
| chapter division | `\begin{teiDiv}[type={chapter}]...\end{teiDiv}` + `\teiHead` | `\chapter{...}`, `\markboth`, TOC entry | important | Requires structure-aware processing, not a pure macro in all cases. |
| part/front/back division | `teiDiv` with `type` or generic `teiElement` | `\part*`, `\chapter*`, `\frontmatter`, `\backmatter` | important | Needs mapping for `text/front/body/back/group/div`. |
| TEI header | likely generic `teiElement[name={teiHeader}]` if exported whole | metadata only, not printed | important | LaTEI driver must either omit/consume it or use it for metadata. |
| italic | `\teiHi[rend={italic}]{...}` | `\textit{...}` or stable equivalent | simple | Macro-level rendering is sufficient. |
| small caps | `\teiHi[rend={small-caps}]{...}` | `\textsc{...}` | simple | Needs `rend` dispatch. |
| bold/sup/sub | `\teiHi[rend={...}]` if present | `\textbf`, `\textsuperscript`, subscript math | simple/medium | Requires agreed `rend` vocabulary. |
| note | `\teiNote[place={foot},xmlid={...}]{...}` | `\footnote{...}` plus nested-note guard | medium | Inline macro works for simple notes; nested notes need stable guard behavior. |
| ref | `\teiRef[target={...}]{...}` | `\href{...}{...}` or internal-link logic | medium | Internal anchors need mapping; external links can be macro-level. |
| ptr | `\teiPtr[target={...}]` | link marker or suppressed target | medium | Empty milestone in flow; presentation depends on editorial intent. |
| lb | `\teiLb[...]` | line break or ignored | simple/medium | Needs policy per context. |
| pb | `\teiPb[...]` | page marker, ignored, or margin note | medium | Should not force physical PDF page breaks by default. |
| quote block | `teiQuote` environment | `PurhBlockQuote` | simple/medium | Environment can wrap stable block quote once block/inline nesting is handled. |
| inline quote | `\teiQ{...}` | `\enquote{...}` | simple | Macro-level rendering is sufficient. |
| said | `\teiSaid[who={...}]{...}` | likely `\enquote` or plain text | simple/medium | `who` may become metadata or annotation later. |
| list | `teiList[type={ordered}]` | `enumerate` / `itemize` | simple | Environment can branch on `type`. |
| item | `\teiItem{...}` | `\item ...` | simple/medium | Easier inside a `teiList` environment than standalone. |
| figure | `teiFigure`, `\teiGraphic` | centered figure block, `\includegraphics`, caption/credits | important | Stable model chooses paths and fallback; LaTEI needs a macro policy for `graphic target/url`. |
| graphic | `\teiGraphic[target={...}]` or `url={...}` | `\includegraphics` with `\detokenize` | medium | Attribute names differ in real TEI (`url` appears in tests) and must be normalized carefully. |
| bibl simple | `teiBibl` | stable bibliography text or `PurhBibliography` entry | medium/important | Can wrap simple content, but stable renderer has interpreted bibliography logic. |
| biblStruct | fallback unless not specialized | interpreted monograph/article/contribution | important | Not covered by current LaTEI specialization; stable parser has more bibliographic intelligence. |
| author/editor/publisher/idno/biblScope | dedicated macros | formatted bibliography parts | medium | Reversible macros exist, but no typographic composition layer yet. |
| table | `teiTable/teiRow/teiCell` | `tabularx` + booktabs | important | Needs table-aware expansion and warnings for merged cells. |
| title element | `\teiTitle[level={...}]{...}` | italics/enquote/plain depending on `level` | simple/medium | Stable bibliography title rules can be reused conceptually. |
| persName/placeName/orgName/name | dedicated macros | usually plain text with possible metadata | simple | Macro can print content initially. |
| date/num/label/term/foreign | dedicated macros | mostly content, sometimes italics/language | simple/medium | `foreign` may need language handling later. |
| unknown TEI element | `teiElement[name={...}]` | usually content, diagnostic, or suppressed by policy | medium | Must not break PDF; should remain reversible. |

## Obstacles And Design Questions

1. Whole-document shape is not yet aligned.
   The stable renderer expects a `Book` model. The reversible writer can emit
   whatever TEI root it receives. If that root is a complete `TEI`, `teiHeader`
   will probably be serialized as generic `teiElement` and would print unless
   the LaTEI typographic layer suppresses it or interprets it.

2. `teiHeader` must not be printed.
   Stable PDF uses `teiHeader` for metadata. LaTEI must distinguish metadata
   extraction from body rendering. A pure macro such as `teiElement` is not
   enough unless `name={teiHeader}` is explicitly swallowed by the driver/macros.

3. Stable PDF currently uses a second model.
   `tei_to_model.py` builds `semantic_model.Book`, which loses some reversible
   TEI detail but knows how to structure pages, notes, bibliography, figures,
   and metadata. Direct LaTEI rendering from the reversible tree must either:
   reuse stable preamble and define LaTEI macros, or add a bridge from
   reversible tree to stable `Book`.

4. The stable preamble is reusable, but it is embedded in `LatexRenderer`.
   `_render_purh_preamble(book)` already contains most layout decisions. A
   future pass should avoid copy-pasting it blindly; the safest first step is a
   small driver generator that can reuse `LatexRenderer` output or factor the
   preamble only after tests lock behavior.

5. Some LaTEI can be implemented by LaTeX macros only.
   `teiP`, `teiHi`, `teiRef`, `teiQ`, `teiTitle`, simple names, simple dates,
   and simple notes can be expanded by macros/environments in a driver.

6. Some LaTEI requires Python or context-aware rendering.
   `teiDiv` + `teiHead` -> `\chapter`/`\section`, `teiHeader` suppression,
   `text/front/body/back`, figure captions, bibliography, table conversion,
   and internal references probably require a Python writer or a more capable
   LaTEI driver layer. Pure TeX macros can do some of this, but they would make
   the reversible grammar harder to reason about.

7. Notes are structurally different.
   Stable PDF stores notes out of band and emits `\footnote` at `NoteRef`.
   LaTEI keeps `teiNote` inline. That is better for reversibility but needs
   nested-note protection equivalent to the stable renderer.

8. Bibliography coverage differs.
   Reversible LaTEI covers simple `bibl` and fine elements such as `author`,
   `publisher`, `idno`, but stable PDF has special logic for `biblStruct`.
   A convergence pass should not regress the stable bibliography tests.

9. Tables differ by intent.
   LaTEI tables are semantic and reversible. Stable tables are typographic
   `tabularx` output and already warn about merged cells. The conversion from
   `teiTable` to `tabularx` should be a derived rendering layer, not a change
   to the reversible grammar.

10. Asset paths need a policy.
    Stable `PdfBuilder` absolutizes image paths before rendering. LaTEI
    currently preserves attributes. A PURH LaTEI compiler must decide where
    relative graphic paths are resolved.

## Recommended Three-Pass Convergence Plan

### Passe 17B: LaTEI driver, no replacement

Create an experimental writer that wraps existing controlled LaTEI in a
compilable PURH driver, without changing the stable PDF pipeline.

Deliverables:

- a new optional module, for example `purh_site/latei_driver.py` or
  `purh_site/reversible_latei_driver.py`;
- a function that receives TEI or a reversible tree and writes:
  - `book.latei_body.tex` with current controlled LaTEI;
  - `book.latei_main.tex` with a PURH document shell;
- reuse the stable PURH preamble as much as possible;
- define only placeholder-safe typography for the already existing LaTEI
  commands;
- tests that compile generation of `.tex` files without invoking LuaLaTeX.

Success criterion:

- stable `book.tex` generation is untouched;
- LaTEI emits a full document that is at least syntactically plausible and
  explicitly experimental.

### Passe 17C: Base LaTEI typographic macros

Define a minimal typographic layer for simple inline and block LaTEI while
keeping reversibility unchanged.

Focus:

- `teiP`, `teiHi`, `teiNote`, `teiRef`, `teiQ`, `teiTitle`;
- `teiList`/`teiItem`;
- `teiQuote`;
- simple `teiBibl`;
- fallback `teiElement` that prints content but can suppress known structural
  metadata elements.

Tests:

- compare expected LaTeX snippets for simple paragraphs, notes, refs, lists,
  quotes, and bibliography;
- no change to `latex_writer.py` grammar unless a documented ambiguity blocks
  compilation.

Success criterion:

- a small body fragment can produce both reversible LaTEI and a readable PURH
  PDF-oriented LaTeX document.

### Passe 17D: Book structure and metadata

Handle document-level TEI structures and the first realistic book layout.

Focus:

- `TEI`, `teiHeader`, `text`, `front`, `body`, `back`, `group`, `div`, `head`;
- suppress or consume `teiHeader`;
- map chapter-like `teiDiv` to stable chapter/section behavior;
- preserve title page and running heads using stable logic where possible;
- keep stable PDF tests green.

Tests:

- a complete minimal TEI document with header and one chapter;
- a front/body/back example;
- assertions that `teiHeader` is not printed;
- assertions that existing stable `pdf_export_mode` output remains unchanged.

Success criterion:

- the experimental LaTEI route can produce a coherent PURH-shaped document
  without replacing the stable PDF renderer.

## Risk Summary

- Biggest risk: copying stable PURH preamble logic into a second divergent
  implementation.
- Biggest semantic gap: stable model is rendering-oriented while the reversible
  tree is documentary and conservative.
- Biggest PDF risk: `teiHeader` and generic fallback elements becoming visible
  text.
- Biggest editorial risk: creating two correction targets again if stable
  `book.tex` and reversible LaTEI diverge.
- Best mitigation: keep the stable renderer untouched, introduce LaTEI as an
  explicit experimental route, and make each bridge layer testable.

