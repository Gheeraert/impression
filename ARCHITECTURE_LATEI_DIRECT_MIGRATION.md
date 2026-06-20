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

1. Footnotes and inline policies that are already well defined in the stable
   renderer.
2. Figure path handling, captions, credits, and missing-image fallback.
3. Bibliography blocks and hanging layout.
4. Lists, tables, and remaining structured blocks.

Each migration should keep the LaTEI body reversible and should compare against
the stable pipeline rather than inventing a parallel typographic system.
