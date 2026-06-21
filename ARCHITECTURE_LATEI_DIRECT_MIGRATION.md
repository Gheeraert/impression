# LaTEI Direct Migration Notes

This note tracks the first real migration of stable PURH book-structure
decisions into the direct LaTEI path. It complements
`ARCHITECTURE_PURH_STABLE_DECISIONS.md`; the stable PDF pipeline remains the
typographic reference and is not replaced by this work.

## Passe 17I: Book Skeleton

The reversible LaTEI body is unchanged. It still contains only the controlled
semantic serialization produced by `purh_site.reversible.latex_writer`, and it
remains readable by `purh_site.reversible.latex_reader`.

The direct LaTEI driver/macros now begin to reproduce the stable book skeleton:

| Stable decision migrated | LaTEI direct implementation | Notes |
| --- | --- | --- |
| Front matter switch | `latei_macros.tex` emits `\frontmatter` for observed liminary `group` types such as `acknowledgments`, `abbreviations`, and `introduction`. | The source `teiHeader` stays in the body but is suppressed typographically. |
| Main matter switch | `latei_macros.tex` emits `\mainmatter` when entering article/chapter groups or part containers. | The driver no longer forces a global `\mainmatter` before the reversible body. |
| Back matter switch | `latei_macros.tex` emits `\backmatter` for back wrappers or back-like groups currently recognized as `conclusion` or `bibliography`. | This is intentionally minimal until more real back-matter fixtures are covered. |
| Part containers | `group type="section1"` sets a `part` head context and renders its `teiHead` with `\part*`, running marks, and a TOC entry. | Matches the observed part containers in the real Metopes fixture. |
| Article/chapter groups | `group type="article"` and `group type="chapter"` use `data-page-title` to emit numbered `\chapter` headings. | Embedded `div type="titlePage"` is suppressed typographically to avoid duplicate titles. |
| Section levels | `div type="section1"`, `section2`, and `section3` keep using contextual `\section`, `\subsection`, and `\subsubsection`. | The body grammar is unchanged. |
| Running titles | Parts, chapters, and unnumbered liminary chapters emit `\markboth` where a title is known. | The stable header style still comes from the inherited PURH preamble. |
| Table of contents | The driver emits `\tableofcontents` after the reversible body, following the stable renderer's current ordering. | No PDF binary comparison is attempted. |

## Not Migrated In This Passe

- Notes beyond the existing simple LaTEI macro behavior.
- Figures, image path resolution, missing-image policy, and captions.
- Bibliography and bibliography fine structure.
- Tables and tabular layout.
- Full title-page detail for chapter contributors.
- Appendix-specific behavior.
- Visual parity with the stable PDF.

## Passe 17J: Notes And Inline Typography

This passe migrates the stable inline decisions that can safely live in the
typographic LaTEI macro layer. The controlled LaTEI body remains unchanged and
continues to serialize semantic commands such as `\teiNote`, `\teiHi`,
`\teiRef`, `\teiQ`, and `\teiTitle`.

| Stable decision migrated | LaTEI direct implementation | Notes |
| --- | --- | --- |
| Footnotes | `\teiNote` renders simple notes with `\footnote`. | The PURH preamble still supplies the stable footnote styling. |
| Nested-note guard | `\teiNote` tracks whether it is already inside a footnote and emits a symbolic superscript marker for nested notes. | This follows the stable renderer's conservative anti-nesting policy. |
| Italic | `\teiHi[rend={italic}]` renders with `\textit`. | Combined `rend` values are supported without changing the body grammar. |
| Bold | `\teiHi[rend={bold}]` and `rend={gras}` render with `\textbf`. | The French token mirrors the stable parser tolerance. |
| Small caps | `small-caps`, `small_caps`, and `small caps` render with `\textsc`. | This keeps the macro tolerant of common normalized forms. |
| Superscript | `sup` and `exposant` render with `\textsuperscript`. | Same semantic policy as the stable inline renderer. |
| Subscript | `sub` and `indice` render as math subscript. | This intentionally matches the existing stable renderer's simple form. |
| External links | `\teiRef[target={...}]{...}` renders with `\href`. | Missing targets fall back to visible content. |
| Inline quotations | `\teiQ` and `\teiSaid` render with `\enquote`. | The stable preamble already loads `csquotes`. |
| Inline titles | `\teiTitle[level={m/j/a}]` keeps the existing controlled macro policy: italic for monograph/journal, quotation for article-level. | This remains a conservative inline rule, not a full bibliographic model. |

## Still Not Migrated After 17J

- Figure paths, captions, credits, and missing-image fallback.
- Bibliography blocks and structured bibliography formatting.
- Tables and tabular layout.
- Complex list policies beyond the current simple macro behavior.
- Full visual parity with the stable PDF.

## Passe 17K: Figures And Image Fallback

This passe migrates the stable figure fallback policy that can safely live in
the direct LaTEI macro layer. The controlled body remains unchanged and still
serializes figures as `teiFigure`, `teiHead`, `teiGraphic`, and ordinary
paragraph macros with their TEI attributes.

| Stable decision migrated | LaTEI direct implementation | Notes |
| --- | --- | --- |
| Centered figure block | `teiFigure` keeps a centered block and sets the `figure` head context. | This remains a typographic wrapper only. |
| Figure title/head | `teiHead` in figure context renders as a bold figure title/legend line. | The stable renderer later combines title and caption more precisely; direct LaTEI is still conservative. |
| Graphic source priority | `\teiGraphic` reads `url`, then `target`, then `n`. | This mirrors the stable parser's source selection order. |
| Image inclusion | If the selected image path is found by LaTeX, `\includegraphics[width=0.95\linewidth,keepaspectratio]` is used. | Paths are passed through `\detokenize` for underscores, spaces, and similar characters. |
| Missing-image fallback | If no image path is present or the file is not found, the macro renders `Image absente ou non fournie` in a framed box. | This is intentionally close to the stable fallback text. |
| Captions and credits | `\teiP[rend={caption}]` and `\teiP[rend={credits}]` receive small and footnote-size figure-context rendering. | The paragraph remains semantically reversible. |

## Still Not Migrated After 17K

- Stable Python-side image path absolutization from the XML source directory.
- Alternative image source selection beyond the first emitted `\teiGraphic`.
- Full stable caption composition with title/caption punctuation parity.
- Bibliography blocks and structured bibliography formatting.
- Tables and tabular layout.
- Complex list policies and verse.
- Full visual parity with the stable PDF.

## Passe 17K-bis: Portable Image Assets

This passe closes the main portability gap left by 17K without changing the
reversible LaTEI body. Documentary graphic paths stay in `*.latei_body.tex`;
local image paths are compilation artifacts.

| Packaging decision | LaTEI direct implementation | Notes |
| --- | --- | --- |
| Preserve documentary path | The body still contains the original `\teiGraphic[url={...}]`, `target`, or `n` value. | The body remains the reversible source. |
| Copy existing images | `purh_site.latei_assets.package_latei_graphics` resolves graphic paths relative to the XML source file and copies existing files into `latei_assets/images/`. | Copied file names are collision-resistant and preserve extensions. |
| Mapping file | The export writes `<stem>.latei_graphics_map.tex` with `\lateiDeclareGraphic{documentary}{local}` entries. | This file is not reversible and is not a source document. |
| Driver inclusion | The driver inputs the graphics map after LaTEI macros and before the body. | The driver remains the compilation wrapper only. |
| Macro lookup | `\teiGraphic` first looks up the documentary path in the graphics map, then falls back to the original path, then to the missing-image box. | `url`, `target`, then `n` keep the stable priority order. |
| Missing images | Missing files are reported as non-blocking export warnings and still compile with the 17K fallback. | The stable pipeline is unchanged. |

## Still Not Migrated After 17K-bis

- Alternative image source policies beyond independent `teiGraphic` mappings.
- Full stable caption composition with title/caption punctuation parity.
- Bibliography blocks and structured bibliography formatting.
- Tables and tabular layout.
- Complex list policies and verse.
- Full visual parity with the stable PDF.

## Passe 17L: Bibliography Blocks

This passe migrates the stable bibliography block shape into the direct LaTEI
macro layer without introducing BibLaTeX or flattening the reversible body. The
body still carries semantic TEI-oriented commands and generic `teiElement`
fallbacks for bibliography structures not yet specialized by the reversible
grammar.

| Stable decision migrated | LaTEI direct implementation | Notes |
| --- | --- | --- |
| Bibliography block | `teiElement[name={listBibl}]` renders as a `PurhBibliography` block. | `listBibl` remains generic and reversible in the body. |
| Simple bibliography entry | `teiBibl` renders as a hanging entry. | Uses the stable hanging shape: `\noindent\hangindent=1.5em\hangafter=1`. |
| Structured bibliography entry | `teiElement[name={biblStruct}]` renders as a hanging entry while preserving and printing its children. | This is conservative: structure is visible, but not yet normalized into a CSL-like sentence. |
| Fine bibliography children | Existing inline macros render `author`, `editor`, `title`, `publisher`, `date`, `biblScope`, `idno`, and `ref`. | Unknown or not-yet-specialized children such as `analytic`, `monogr`, `imprint`, and `pubPlace` pass through visibly. |
| Title styling | Existing `\teiTitle` handles `level={m}` and `level={j}` with italic and `level={a}` with `\enquote`. | This reuses the inline migration from 17J. |
| DOI/URI links | Existing `\teiRef` and `\teiIdno` remain printable; links use `\href` where a `target` is present. | No external bibliography database is used. |

## Still Not Migrated After 17L

- Full stable bibliographic punctuation and sentence reconstruction.
- Structured `biblStruct` interpretation equivalent to the stable Python model.
- Bibliographic heading/TOC policy beyond simple `listBibl` block rendering.
- Tables and tabular layout.
- Complex list policies and verse.
- Full visual parity with the stable PDF.

## Passe 17N: PDF Convergence Audit

The direct LaTEI PDF is intended to converge toward the stable PURH PDF and to
become the reference paper-production path once the documented gaps are closed.
Until then, the existing stable PDF remains the typographic and editorial
reference.

The differential report is written in `AUDIT_PDF_STABLE_VS_LATEI.md`. It
compares the stable `book.tex`, the direct LaTEI package, the stable PDF, and
the direct LaTEI PDF without binary PDF comparison. The audit currently records
that both paths compile on the real Heraldiques fixture and share the same page
format, while page count and extracted title-page text still differ.

Trivial divergence fixed in this passe:

- The printed `Document LaTEI PURH experimental` title-page marker was removed
  from the direct LaTEI driver.

The remaining divergences listed in the audit should be resolved by small
migration passes, always against the stable PDF behavior rather than by inventing
an independent typographic policy.

### Passe 17N-bis: TeX Convergence Audit

The PDF audit identifies symptoms: page-count drift and extracted text
differences. The TeX audit in `AUDIT_TEX_STABLE_VS_LATEI.md` looks for causes in
the stable `book.tex` and in the direct LaTEI package.

The stable `book.tex` and `*.latei_body.tex` are not equivalent layers:

- `book.tex` is final typographic LaTeX emitted by the stable renderer.
- `*.latei_body.tex` is the reversible semantic source.
- `*.latei_main.tex` and `*.latei_macros.tex` are the direct LaTEI typographic
  layer.

The audit localizes the current footnote suspicion: the real fixture contains
many `\teiNote{... \teiP{...} ...}` forms, while `\teiP` emits paragraph breaks
through `\par`. This gives a concrete hypothesis for note text starting on a new
line after the footnote number. Corrections should be made in a focused note
pass, not mixed with title-page, figure, bibliography, table, or list work.

### Passe 17N-ter: Footnote Paragraph Convergence

The observed problem was a visible line break after the footnote number in the
direct LaTEI PDF. The TeX audit confirmed the likely local cause: many notes in
the real Metopes fixture contain `\teiP` inside `\teiNote`, and the normal
paragraph behavior of `\teiP` emitted `\par` before note text.

The correction stays entirely in the typographic macro layer. `\teiP` now checks
the existing footnote context and renders inline inside `\teiNote`; outside a
note, it keeps the normal paragraph behavior, including figure caption and
credits handling. Multiple paragraph notes are rendered compactly rather than
forcing an initial vertical break.

The reversible body is unchanged. The writer and reader grammar are unchanged,
and notes containing paragraph elements still round-trip back to Metopes TEI.
The stable PDF pipeline remains the reference. On the Heraldiques fixture, the
direct LaTEI page count moved from 365 pages to 353 pages while the stable PDF
remains 351 pages, so the major footnote break cause is removed but convergence
is not complete.

### Passe 17N-quater: Title-Page Metadata Convergence

The remaining first textual gap after 17N-ter came from visible metadata printed
on the direct LaTEI title page: `PURH - 2025` and ISBN lines. The stable PDF for
the Heraldiques fixture prints the title and the visible publisher line, then
continues into front matter; it does not print publication year, ISBN, ePub,
PDF ISBN, or DOI lines on the title page.

The correction keeps metadata extraction intact but narrows the visible direct
LaTEI title page to the stable policy. `\PURHYear`, `\PURHISBN`, `\PURHDOI`,
and related metadata commands remain available in the preamble and reports, but
`_title_page(...)` no longer prints those values as title-page extras. The
reversible body, LaTEI reader/writer, and grammar remain unchanged.

The stable PDF remains the reference. After this correction, the PDF audit no
longer reports the `PURH - 2025` / ISBN title-page gap; the direct LaTEI PDF
still needs later block-level convergence work.

### Passe 17N-quinquies: Frontmatter Numbering, Running Titles And Unicode Spaces

The stable renderer uses the book-class matter switches: `\frontmatter` for
liminaries, then `\mainmatter` for the main body. Direct LaTEI keeps this policy
instead of forcing a separate page-numbering command; liminary numbering remains
the book-class/stable policy, and the body numbering restarts at `\mainmatter`.

Running titles now reuse the stable Python shortening logic
`_short_running_title(...)` and the same stopword list. The reversible body is
not enriched with typographic attributes. Instead, the export writes a technical
`*.latei_running_titles_map.tex` file with `\lateiDeclareRunningTitle{full}{short}`
declarations, and the macro layer consults that mapping only when emitting
`\markboth`. Chapter, part, and section titles printed in the body remain full.

Unicode spacing characters remain in the controlled LaTEI body so they can
round-trip back to Metopes TEI. The direct LaTEI macro layer maps U+00A0,
U+202F, and U+2009 with `newunicodechar` so LuaLaTeX does not render missing
glyph boxes for ordinary French typographic spaces.

The LaTEI reader/writer and grammar remain unchanged. The stable PDF remains
the reference for later pagination and block-level convergence work.

## Remaining Differences

The direct LaTEI PDF is no longer a completely flat stream, but it is still not
the finished PURH paper-production path. It uses the stable preamble and has the
first book-level structure, yet many block-level and asset-level decisions still
come from provisional macros.

The 17G bridge remains useful as a comparison bench:

```text
LaTEI body -> restored Metopes TEI -> stable PdfBuilder
```

It proves that the editable LaTEI source can restore a Metopes document that the
stable pipeline accepts. It is not the final architecture.

## Recommended Next Passe

Migrate the next stable decisions in small groups:

1. Structured bibliography interpretation where needed by real fixtures.
2. Tables and tabular layout.
3. Lists, verse, and remaining structured blocks.
4. Remaining asset policy details only where comparison against the stable
   pipeline shows they are needed.

Each migration should keep the LaTEI body reversible and should compare against
the stable pipeline rather than inventing a parallel typographic system.
