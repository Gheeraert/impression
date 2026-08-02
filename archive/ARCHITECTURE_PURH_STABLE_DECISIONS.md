# PURH Stable PDF Decisions Contract

This document captures the typographic and layout decisions already implemented
by the stable PURH PDF pipeline. Its purpose is to prepare progressive migration
toward the final LaTEI PURH path without creating a second, divergent renderer
inside `latei_macros.tex`.

The stable pipeline remains:

```text
normalized TEI
-> purh_site.tei_to_model.parse_normalized_tei
-> purh_site.semantic_model.Book
-> purh_site.latex_renderer.LatexRenderer(style="purh")
-> purh_site.pdf_builder.PdfBuilder
-> LuaLaTeX
```

The final LaTEI target remains:

```text
XML Commons-Publishing / Metopes
-> reversible Python tree
-> LaTEI PURH carrying semantics and layout instructions
-> LuaLaTeX
-> PURH PDF

Corrected LaTEI PURH
-> reversible Python tree
-> XML Commons-Publishing / Metopes
```

The 17G bridge, `LaTEI body -> restored TEI -> stable PdfBuilder`, is a proof
bench and comparison path. It is not the final paper-production architecture.

## Stable Decision Table

| Stable PURH decision | Current module/function | Observed TEI input | Stable LaTeX output | Migrate to LaTEI? | Priority |
| --- | --- | --- | --- | --- | --- |
| Whole book matter order | `LatexRenderer.render_book` | full `TEI/text` split into model `front_divisions`, `body_divisions`, `back_divisions` | `\frontmatter`, then `\mainmatter`, then optional `\backmatter`, then optional `\tableofcontents` | yes | high |
| Volume title page | `TeiToModelParser._parse_book_metadata`; `LatexRenderer._render_volume_title_page` | `teiHeader/fileDesc/titleStmt`, `publicationStmt` | `titlepage`, `\thispagestyle{empty}`, `\PurhSubtitle`, `\PurhContributors`, `\PurhTitleExtra`, `\clearpage` | yes | high |
| Front divisions | `TeiToModelParser._parse_volume_front_divisions`; `LatexRenderer._render_front_divisions` | `text/front/div`, excluding `div type="titlePage"` | frontmatter `\chapter*{...}`, running mark, TOC chapter entry | yes | high |
| Body divisions from grouped books | `TeiToModelParser._parse_grouped_body_divisions`; `_iter_group_divisions`; `_parse_group_division` | `text/group[@type='book']/group` | model `Division` objects later rendered as parts, chapters, or unnumbered chapters | yes | high |
| Back divisions | `TeiToModelParser._parse_volume_back_divisions`; `LatexRenderer._render_back_divisions` | `text/back/div` | `\backmatter` plus unnumbered or appendix chapters | yes | high |
| Part containers | `_iter_group_divisions`; `_is_group_container`; `_map_division_type` | grouping `group` containers or `type="part"` / `type="section1"` at container level | `\part*{...}`, `\markboth`, `\addcontentsline{toc}{part}{...}` | yes | high |
| Numbered chapters | `_map_division_type`; `LatexRenderer._render_division_heading` | `group type="chapter"` or `type="article"` outside front/back | `\chapter{...}` plus `\markboth` | yes | high |
| Liminaires and post-liminaires | `_map_division_type`; `_guess_division_title_from_type`; `_render_division_heading` | `dedication`, `acknowledgments`, `foreword`, `preface`, `introduction`, `conclusion`, `bibliography` | usually `\chapter*{...}` plus `\addcontentsline{toc}{chapter}{...}` and running mark | yes | high |
| Appendix start | `_render_division_heading` | `DivisionType.APPENDIX` | first appendix emits `\appendix` then `\chapter{...}` | yes | medium |
| Section levels | `TeiToModelParser._is_section_div`; `_section_level`; `LatexRenderer._render_section` | `div type="section1"`, `section2`, `section3` | `\section`, `\subsection`, `\subsubsection` | yes | high |
| Running titles | `_short_running_title`; `_render_division_heading`; `_render_purh_preamble` | division titles | `\markboth{short title}{short title}`, `fancyhdr` `\leftmark` | yes | high |
| Table of contents | `LatexRenderOptions.include_toc`; `LatexRenderer.render_book`; `_render_purh_preamble` | all rendered divisions/sections | `\tableofcontents`, `titletoc`, `\addcontentsline` for unnumbered units | yes | high |
| Page format and fonts | `LatexRenderOptions`; `_render_purh_preamble` | global render options | `book` class, 155 x 230 mm geometry, `fontspec`, Chaparral Pro when available, `microtype`, `babel`, `csquotes` | yes | high |
| Page headers and footers | `_render_purh_preamble` | metadata title and running marks | `fancyhdr`, page numbers outside, book title on verso, chapter mark on recto | yes | high |
| Title styling and spacing | `_render_purh_preamble` | rendered `chapter`/`section` commands | `titlesec` rules for chapter, section, subsection, subsubsection spacing and fonts | yes | high |
| Paragraph hints | `TeiToModelParser._parse_block`; `LatexRenderer._render_paragraph` | `p@rend` | plain paragraph, `flushright` for `signature`, bold no-indent for `lead`, `\bigskip` for `break` | yes | medium |
| Footnotes | `_parse_inline_element`; `_parse_footnote`; `LatexRenderer._render_note_ref`; `_render_footnote_content` | inline `note` with `place=""` or `place="foot"` and standard type | `NoteRef` in flow, then `\footnote{...}` with nested-note guard `\textsuperscript{*}` | yes | high |
| Inline italics/bold/small caps/sup/sub | `_apply_hi_rend`; `LatexRenderer._render_inline_node` | `hi@rend` tokens | `\textit`, `\textbf`, `\textsc`, `\textsuperscript`, subscript math | yes | high |
| Links | `_parse_inline_element`; `_render_inline_node` | `ref@target`, optional `@type` | `\href{target}{label}` or escaped target as fallback label | yes | medium |
| Inline quotes | `_parse_inline_element`; `_render_inline_node` | `quote` or inline `cit/quote` | `\enquote{...}` | yes | medium |
| Block quotes | `_parse_quote_block`; `_render_quote_block`; `_render_purh_preamble` | block `cit` containing `quote` and optional `bibl` | `PurhBlockQuote` environment, optional ragged-left source | yes | medium |
| Lists | `_parse_list_block`; `_render_list_block`; `_render_list_item` | `list type="ordered"` or other list | `enumerate[leftmargin=*]` or `itemize[leftmargin=*]`, with `\item` | yes | medium |
| Figures | `_parse_figure_block`; `PdfBuilder._absolutize_figure_paths`; `_render_figure_block` | `figure/head`, `graphic@url|@target|@n`, `p@rend='caption'`, `p@rend='credits'` | centered `\includegraphics[width=...,keepaspectratio]{...}` or missing-image `\fbox`, then title/caption/credits | yes | medium |
| Missing image policy | `PdfBuilder._absolutize_blocks_paths`; `_render_figure_block` | graphic path absent or unresolved | build warnings such as `Image introuvable`, and rendered fallback box if no usable path | yes | medium |
| Bibliography blocks | `_parse_container_blocks`; `_parse_bibliography_item`; `_render_bibliography_block` | consecutive `bibl`, `biblStruct`, or `listBibl` | optional `\section*`, TOC entry, `PurhBibliography`, hanging entries | yes | medium |
| Structured bibliography | `_parse_bibl_struct`; `_render_bibliographic_entry` and helpers | `biblStruct` with analytic/monogr/imprint/idno | formatted monograph/article/contribution strings, `\textit`, `\enquote`, DOI/URI links | yes | medium |
| Tables | `_parse_table_block`; `_render_table_block`; `_render_table_cell` | `table/head/row/cell`, `cell@role`, `cell@cols`, `cell@rows` | centered `tabularx`, `booktabs`, label row bolding, warning comment for merged cells | yes | medium |
| Verse | `_parse_verse_block`; `_render_verse_block` | `lg/l`, optional `num` or `l@n` | `verse` environment, line numbers with small footnote-size number | yes | low |
| Title page blocks inside divisions | `_parse_title_page`; `_parse_title_page_contributors`; `_render_division_titlepage_details` | `front/div type="titlePage"` and title-page metadata | `\PurhSubtitle`, `\PurhContributors`, `\PurhTitleExtra` below division heading | yes | medium |
| Image path portability | `PdfBuilder._resolve_asset_path`; `_absolutize_figure_paths` | relative figure paths in normalized XML | absolute POSIX paths before LaTeX rendering | yes | medium |
| Build logs and reports | `PdfBuilder.build_from_normalized_tei`; `_compile_latex`; `_write_report` | XML path and output directory | `book.tex`, `book.pdf`, `latex_build.log`, `pdf_build_report.txt`, warnings and stats | no, but keep comparable | low |

## Migration Order Recommended

1. Book skeleton and matter structure: `frontmatter`, `mainmatter`,
   `backmatter`, title page, TOC, running heads.
2. Division and `head` policy: parts, chapters, front/back unnumbered units,
   appendices, section levels 1-3.
3. Notes and inline typography: footnotes, `hi@rend`, links, inline quotes.
4. Figures and assets: path resolution, missing-image fallback, captions,
   credits.
5. Bibliography: `listBibl`, `bibl`, `biblStruct`, identifiers, hanging layout.
6. Lists, tables, verse and remaining block policies.
7. Build/report parity: logs, warnings, and diagnostics comparable to the
   stable builder.

## Guardrails

- Do not migrate by copy-pasting the entire stable renderer into
  `latei_macros.tex`.
- Prefer moving stable decisions into the LaTEI generation path explicitly and
  testably.
- Keep the LaTEI body reversible by `purh_site.reversible.latex_reader`.
- Keep the 17G stable-PDF bridge as a comparison oracle while the direct LaTEI
  production path matures.
- Do not touch the HTML/static-site pipeline while working on these PDF
  decisions.
