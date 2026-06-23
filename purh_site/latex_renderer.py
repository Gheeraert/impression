from __future__ import annotations

"""Rendu LaTeX à partir du modèle sémantique minimal.

Ce module convertit les objets définis dans ``semantic_model.py`` en une
chaîne LaTeX complète, prête à être compilée avec LuaLaTeX.

Choix de conception pour la V1
------------------------------
- rester lisible et pédagogique ;
- produire un PDF éditeur sobre et robuste ;
- éviter les raffinements typographiques prématurés ;
- couvrir correctement les cas PURH les plus fréquents.

Le renderer assume que le parseur TEI a déjà produit un modèle propre :
- notes séparées du flux ;
- inline structurés ;
- divisions hiérarchisées ;
- figures et bibliographie déjà identifiées.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable

from .semantic_model import (
    BibliographicEntry,
    BibliographicIdentifier,
    BibliographicPerson,
    BibliographicTitle,
    BibliographyBlock,
    BibliographyItem,
    BlockNode,
    Book,
    BookMetadata,
    Bold,
    Contributor,
    Division,
    DivisionType,
    FigureBlock,
    Footnote,
    InlineNode,
    InlineQuote,
    Italic,
    Link,
    ListBlock,
    ListItem,
    ListKind,
    NoteRef,
    Paragraph,
    PublicationInfo,
    QuoteBlock,
    Section,
    SmallCaps,
    Subscript,
    Superscript,
    TableBlock,
    TableCell,
    TextRun,
    TitlePageBlock,
    VerseBlock,
    VerseLine,
)


from .latei_typography import _short_running_title as _compute_short_running_title


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class LatexRenderOptions:
    """Options simples de rendu pour la V1."""

    style: str = "default"
    document_class: str = "memoir"
    font_size_pt: int = 11
    paper_width_mm: int = 155
    paper_height_mm: int = 230

    # Marges / bloc de texte : valeurs prudentes et faciles à ajuster ensuite.
    inner_margin_mm: int = 23
    outer_margin_mm: int = 22
    upper_margin_mm: int = 24
    lower_margin_mm: int = 22

    main_font: str = "TeX Gyre Pagella"
    sans_font: str = "TeX Gyre Heros"
    mono_font: str = "Latin Modern Mono"
    main_language: str = "french"

    include_toc: bool = True
    hyperlink_color: str = "black"
    oneside: bool = True
    openany: bool = True

    figure_max_width: str = r"0.95\linewidth"
    quote_left_margin_em: float = 2.0
    bibliography_hangindent_em: float = 1.5

    show_toc_in_pdf_bookmarks: bool = True


# ---------------------------------------------------------------------------
# Renderer principal
# ---------------------------------------------------------------------------


class LatexRenderer:
    """Convertit un ``Book`` en document LaTeX complet."""

    def __init__(self, options: LatexRenderOptions | None = None) -> None:
        self.options = options or LatexRenderOptions()
        self._current_notes: dict[str, Footnote] = {}
        self._in_footnote = False
        self._appendix_started = False

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def render_book(self, book: Book) -> str:
        """Retourne le document LaTeX complet pour le livre donné."""

        parts: list[str] = [self._render_preamble(book), "\\begin{document}"]

        parts.append(self._render_volume_title_page(book))

        parts.append("\\frontmatter")
        parts.append(self._render_front_divisions(book))

        parts.append("\\mainmatter")
        parts.append(self._render_body_divisions(book))

        if book.back_divisions:
            parts.append("\\backmatter")
            parts.append(self._render_back_divisions(book))

        if self.options.include_toc:
            parts.append("\\cleardoublepage")
            parts.append("\\tableofcontents")

        parts.append("\\end{document}")
        return "\n\n".join(part for part in parts if part.strip()) + "\n"

    def write_book(self, book: Book, output_path: str | Path) -> Path:
        """Écrit le document LaTeX sur disque et retourne le chemin."""

        output = Path(output_path)
        output.write_text(self.render_book(book), encoding="utf-8")
        return output


# ---------------------------------------------------------------------------
# Preambule
# ---------------------------------------------------------------------------

    def _render_preamble(self, book: Book) -> str:
        if self.options.style == "purh":
            return self._render_purh_preamble(book)

        class_options = [f"{self.options.font_size_pt}pt"]
        if self.options.oneside:
            class_options.append("oneside")
        if self.options.openany:
            class_options.append("openany")
        class_options_str = ",".join(class_options)

        title = self._escape_text(book.metadata.title)
        author = self._escape_text(self._join_contributor_names(book.metadata.contributors))

        return rf"""
\documentclass[{class_options_str}]{{{self.options.document_class}}}

\usepackage{{fontspec}}
\usepackage{{polyglossia}}
\setmainlanguage{{{self.options.main_language}}}
\setmainfont{{{self.options.main_font}}}
\setsansfont{{{self.options.sans_font}}}
\setmonofont{{{self.options.mono_font}}}

\usepackage[final]{{microtype}}
\usepackage{{graphicx}}
\usepackage{{csquotes}}
\usepackage{{hyperref}}
\usepackage{{bookmark}}
\usepackage{{caption}}
\usepackage{{enumitem}}
\usepackage{{array}}
\usepackage{{tabularx}}
\usepackage{{booktabs}}
\usepackage{{verse}}
\usepackage{{ragged2e}}
\usepackage{{xurl}}

\hypersetup{{
  unicode=true,
  pdftitle={{{title}}},
  pdfauthor={{{author}}},
  colorlinks=true,
  allcolors={self.options.hyperlink_color}
}}

% -----------------------------------------------------------------
% Format de page PURH V1 (sobre et ajustable)
% -----------------------------------------------------------------
\setstocksize{{{self.options.paper_height_mm}mm}}{{{self.options.paper_width_mm}mm}}
\settrimmedsize{{\stockheight}}{{\stockwidth}}{{*}}
\setlrmarginsandblock{{{self.options.inner_margin_mm}mm}}{{{self.options.outer_margin_mm}mm}}{{*}}
\setulmarginsandblock{{{self.options.upper_margin_mm}mm}}{{{self.options.lower_margin_mm}mm}}{{*}}
\checkandfixthelayout

% -----------------------------------------------------------------
% Réglages de base
% -----------------------------------------------------------------
\setsecnumdepth{{subsection}}
\settocdepth{{subsection}}
\captionnamefont{{\small\bfseries}}
\captiontitlefont{{\small}}
\footnotesize
\AtBeginDocument{{\normalsize}}
\setlength{{\parindent}}{{1.25em}}
\setlength{{\parskip}}{{0pt}}
\setlength{{\footmarkwidth}}{{1.8em}}
\setlength{{\footmarksep}}{{0.4em}}
\setlength{{\skip\footins}}{{1.1\baselineskip}}

% -----------------------------------------------------------------
% Macros utilitaires PURH
% -----------------------------------------------------------------
\newcommand{{\PurhSubtitle}}[1]{{%
  \par\vspace{{0.4\baselineskip}}%
  {{\large\itshape #1\par}}%
  \vspace{{0.6\baselineskip}}%
}}

\newcommand{{\PurhContributors}}[1]{{%
  \par\vspace{{0.5\baselineskip}}%
  {{\normalsize\scshape #1\par}}%
  \vspace{{0.6\baselineskip}}%
}}

\newcommand{{\PurhTitleExtra}}[1]{{%
  {{\small #1\par}}%
}}

\newenvironment{{PurhBlockQuote}}
  {{%
    \begin{{quote}}\small
  }}
  {{%
    \end{{quote}}
  }}

\newenvironment{{PurhBibliography}}
  {{%
    \par
    \setlength{{\parindent}}{{0pt}}%
    \setlength{{\leftskip}}{{0pt}}%
  }}
  {{%
    \par
  }}
""".strip()

    def _render_purh_preamble(self, book: Book) -> str:
        """Préambule PURH minimal aligné sur les témoins typographiques.

        Le style ``purh`` suit explicitement l'architecture validée par l'audit :
        ``book`` + ``geometry`` + ``babel`` + ``titlesec``/``titletoc`` +
        ``fancyhdr``. Le style par défaut reste volontairement sur ``memoir``.

        Délègue à ``latei_preamble.render_purh_latex_preamble`` pour partager
        exactement le même template entre la chaîne stable et la chaîne LaTEI.
        """
        from .latei_preamble import PurhPreambleData, render_purh_latex_preamble

        publication = book.metadata.publication
        return render_purh_latex_preamble(PurhPreambleData(
            title=book.metadata.title or "",
            subtitle=book.metadata.subtitle or "",
            authors=tuple(
                c.full_name for c in book.metadata.contributors
                if getattr(c, "full_name", "").strip()
            ),
            publisher=publication.publisher or "Presses universitaires de Rouen et du Havre",
            year=publication.publication_year or "",
            doi=publication.doi or "",
            isbn=publication.isbn_pdf or publication.isbn_print or "",
        ))


# ---------------------------------------------------------------------------
# Rendu global des parties du livre
# ---------------------------------------------------------------------------

    def _render_volume_title_page(self, book: Book) -> str:
        contributors = self._join_contributor_names(book.metadata.contributors)
        lines: list[str] = [
            "\\begin{titlepage}",
            "\\thispagestyle{empty}",
            "\\centering",
            "\\vspace*{0.15\\textheight}",
        ]
        lines.append(rf"{{\Huge\bfseries {self._escape_text(book.metadata.title)}\par}}")

        if book.metadata.subtitle:
            lines.append(rf"\PurhSubtitle{{{self._escape_text(book.metadata.subtitle)}}}")

        if contributors:
            lines.append(rf"\PurhContributors{{{self._escape_text(contributors)}}}")

        publication_line = self._volume_publication_line(book)
        lines.append("\\vfill")
        if publication_line:
            lines.append(rf"\PurhTitleExtra{{{self._escape_text(publication_line)}}}")

        lines.extend(["\\end{titlepage}", "\\clearpage"])
        return "\n".join(lines)

    def _render_front_divisions(self, book: Book) -> str:
        return self._render_division_sequence(book.front_divisions, frontmatter=True)

    def _render_body_divisions(self, book: Book) -> str:
        return self._render_division_sequence(book.body_divisions, frontmatter=False)

    def _render_back_divisions(self, book: Book) -> str:
        return self._render_division_sequence(book.back_divisions, frontmatter=False, backmatter=True)

    def _render_division_sequence(
        self,
        divisions: list[Division],
        *,
        frontmatter: bool = False,
        backmatter: bool = False,
    ) -> str:
        rendered: list[str] = []
        for division in divisions:
            rendered.append(self._render_division(division, frontmatter=frontmatter, backmatter=backmatter))
        return "\n\n".join(part for part in rendered if part.strip())


# ---------------------------------------------------------------------------
# Divisions
# ---------------------------------------------------------------------------

    def _render_division(
        self,
        division: Division,
        *,
        frontmatter: bool = False,
        backmatter: bool = False,
    ) -> str:
        previous_notes = self._current_notes
        self._current_notes = division.notes
        try:
            lines: list[str] = []

            heading = self._render_division_heading(division, frontmatter=frontmatter, backmatter=backmatter)
            if heading:
                lines.append(heading)

            if division.title_page and division.div_type not in {DivisionType.PART}:
                contributor_block = self._render_division_titlepage_details(division.title_page)
                if contributor_block:
                    lines.append(contributor_block)
            elif division.contributors:
                contributors = self._join_contributor_names(division.contributors)
                if contributors:
                    lines.append(rf"\PurhContributors{{{self._escape_text(contributors)}}}")

            blocks_and_sections = []
            blocks_and_sections.append(self._render_blocks(division.blocks))
            for section in division.sections:
                blocks_and_sections.append(self._render_section(section))
            if blocks_and_sections:
                lines.append("\n\n".join(chunk for chunk in blocks_and_sections if chunk.strip()))

            return "\n\n".join(chunk for chunk in lines if chunk.strip())
        finally:
            self._current_notes = previous_notes

    def _render_division_heading(
        self,
        division: Division,
        *,
        frontmatter: bool,
        backmatter: bool,
    ) -> str:
        title = division.title or (division.title_page.title if division.title_page else None)
        if not title:
            return ""

        escaped_title = self._escape_text(title)
        running_title = self._escape_text(_compute_short_running_title(title))
        running_mark = rf"\markboth{{{running_title}}}{{{running_title}}}"

        if division.div_type == DivisionType.PART:
            return (
                    rf"\part*{{{escaped_title}}}" + "\n"
                    + running_mark + "\n"
                    + rf"\addcontentsline{{toc}}{{part}}{{{escaped_title}}}"
            )

        numbered = division.div_type == DivisionType.CHAPTER
        if numbered and not frontmatter and not backmatter:
            return rf"\chapter{{{escaped_title}}}" + "\n" + running_mark

        if division.div_type == DivisionType.APPENDIX and not self._appendix_started:
            self._appendix_started = True
            return (
                "\\appendix\n"
                rf"\chapter{{{escaped_title}}}" + "\n"
                + running_mark
            )

        # Par défaut, on reste non numéroté pour les liminaires et la plupart des post-liminaires.
        return (
                rf"\chapter*{{{escaped_title}}}" + "\n"
                + running_mark + "\n"
                + rf"\addcontentsline{{toc}}{{chapter}}{{{escaped_title}}}"
        )

    def _render_division_titlepage_details(self, title_page: TitlePageBlock) -> str:
        lines: list[str] = []

        if title_page.subtitle:
            lines.append(rf"\PurhSubtitle{{{self._escape_text(title_page.subtitle)}}}")

        contributors = self._join_contributor_names(title_page.contributors)
        if contributors:
            lines.append(rf"\PurhContributors{{{self._escape_text(contributors)}}}")

        for extra in title_page.extra_lines:
            if extra.strip():
                lines.append(rf"\PurhTitleExtra{{{self._escape_text(extra)}}}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

    def _render_section(self, section: Section) -> str:
        lines: list[str] = []
        title = self._escape_text(section.title)

        if section.level == 1:
            lines.append(rf"\section{{{title}}}")
        elif section.level == 2:
            lines.append(rf"\subsection{{{title}}}")
        else:
            lines.append(rf"\subsubsection{{{title}}}")

        if section.blocks:
            lines.append(self._render_blocks(section.blocks))
        for child in section.sections:
            lines.append(self._render_section(child))

        return "\n\n".join(chunk for chunk in lines if chunk.strip())


# ---------------------------------------------------------------------------
# Blocs
# ---------------------------------------------------------------------------

    def _render_blocks(self, blocks: Iterable[BlockNode]) -> str:
        rendered: list[str] = []
        for block in blocks:
            chunk = self._render_block(block)
            if chunk.strip():
                rendered.append(chunk)
        return "\n\n".join(rendered)

    def _render_block(self, block: BlockNode) -> str:
        if isinstance(block, Paragraph):
            return self._render_paragraph(block)
        if isinstance(block, QuoteBlock):
            return self._render_quote_block(block)
        if isinstance(block, FigureBlock):
            return self._render_figure_block(block)
        if isinstance(block, BibliographyBlock):
            return self._render_bibliography_block(block)
        if isinstance(block, ListBlock):
            return self._render_list_block(block)
        if isinstance(block, TableBlock):
            return self._render_table_block(block)
        if isinstance(block, VerseBlock):
            return self._render_verse_block(block)
        if isinstance(block, TitlePageBlock):
            return self._render_division_titlepage_details(block)
        return ""

    def _render_paragraph(self, paragraph: Paragraph) -> str:
        content = self._render_inline_nodes(paragraph.content)
        if not content.strip():
            return ""

        if paragraph.render_hint == "signature":
            return rf"\begin{{flushright}}{content}\end{{flushright}}"
        if paragraph.render_hint == "lead":
            return rf"{{\noindent\bfseries {content}}}"
        if paragraph.render_hint == "break":
            return r"\bigskip"
        return content

    def _render_quote_block(self, quote_block: QuoteBlock) -> str:
        body = self._render_blocks(quote_block.blocks)
        source = self._render_inline_nodes(quote_block.source) if quote_block.source else ""

        lines = ["\\begin{PurhBlockQuote}", body]
        if source.strip():
            lines.append(rf"\par\raggedleft\small {source}")
        lines.append("\\end{PurhBlockQuote}")
        return "\n".join(chunk for chunk in lines if chunk.strip())

    def _render_figure_block(self, figure: FigureBlock) -> str:
        image_path = self._select_figure_image_path(figure)
        title = self._render_inline_nodes(figure.title) if figure.title else ""
        caption = self._render_inline_nodes(figure.caption) if figure.caption else ""
        credits = self._render_inline_nodes(figure.credits) if figure.credits else ""

        caption_parts: list[str] = []
        if title.strip():
            caption_parts.append(rf"\textbf{{{title}}}")
        if caption.strip():
            caption_parts.append(caption)

        full_caption = ". ".join(
            part.strip().rstrip(".") for part in caption_parts if part.strip()
        )

        lines = ["\\begin{center}"]

        if image_path:
            lines.append(
                rf"\includegraphics[width={self.options.figure_max_width},keepaspectratio]{{{image_path}}}"
            )
        else:
            lines.append(
                r"\fbox{\parbox{0.8\linewidth}{\centering\footnotesize Image absente ou non fournie}}"
            )

        if full_caption:
            lines.append(rf"\par\small {full_caption}")
        elif title.strip():
            lines.append(rf"\par\small \textbf{{{title}}}")

        if credits.strip():
            lines.append(rf"\par\footnotesize {credits}")

        lines.append("\\end{center}")
        return "\n".join(lines)

    def _render_bibliography_block(self, bibliography: BibliographyBlock) -> str:
        lines: list[str] = []

        if self._in_footnote:
            return "; ".join(
                rendered
                for rendered in (self._render_bibliography_item_content(item) for item in bibliography.items)
                if rendered.strip()
            )

        if bibliography.title:
            title = self._escape_text(bibliography.title)
            lines.append(rf"\section*{{{title}}}")
            lines.append(rf"\addcontentsline{{toc}}{{section}}{{{title}}}")

        lines.append("\\begin{PurhBibliography}")
        for item in bibliography.items:
            lines.append(self._render_bibliography_item(item))
        lines.append("\\end{PurhBibliography}")
        return "\n".join(lines)

    def _render_bibliography_item(self, item: BibliographyItem) -> str:
        content = self._render_bibliography_item_content(item)
        if not content.strip():
            return ""
        hang = self.options.bibliography_hangindent_em
        return rf"\noindent\hangindent={hang}em\hangafter=1 {content}\par"

    def _render_bibliography_item_content(self, item: BibliographyItem) -> str:
        if item.structured is not None:
            return self._render_bibliographic_entry(item.structured)
        return self._render_inline_nodes(item.content)

    def _render_bibliographic_entry(self, entry: BibliographicEntry) -> str:
        if entry.kind == "article":
            return self._render_journal_article_entry(entry)
        if entry.kind == "contribution":
            return self._render_contribution_entry(entry)
        return self._render_monograph_entry(entry)

    def _render_monograph_entry(self, entry: BibliographicEntry) -> str:
        parts = [
            self._format_people(entry.authors),
            self._format_bibl_title(entry.monograph_title),
        ]
        parts.extend(self._publication_parts(entry))
        text = self._join_bibl_parts(parts)
        return self._append_identifier_sentence(text, entry.identifiers)

    def _render_contribution_entry(self, entry: BibliographicEntry) -> str:
        parts = [
            self._format_people(entry.authors),
            self._format_bibl_title(entry.analytic_title),
        ]
        container_parts = [
            self._format_editors(entry.editors),
            self._format_bibl_title(entry.monograph_title),
        ]
        container_parts.extend(self._publication_parts(entry))
        container_parts.append(self._format_pages(entry.pages))
        container = self._join_bibl_parts(container_parts)
        if container:
            parts.append(f"dans {container}")

        text = self._join_bibl_parts(parts)
        return self._append_identifier_sentence(text, entry.identifiers)

    def _render_journal_article_entry(self, entry: BibliographicEntry) -> str:
        parts = [
            self._format_people(entry.authors),
            self._format_bibl_title(entry.analytic_title),
            self._format_bibl_title(entry.journal_title),
            self._format_volume(entry.volume),
            self._format_issue(entry.issue),
            entry.date,
            self._format_pages(entry.pages),
        ]
        text = self._join_bibl_parts(parts)
        return self._append_identifier_sentence(text, entry.identifiers)

    def _publication_parts(self, entry: BibliographicEntry) -> list[str | None]:
        return [entry.pub_place, entry.publisher, entry.date]

    def _format_people(self, people: list[BibliographicPerson]) -> str:
        names = [self._escape_text(person.name) for person in people if person.name.strip()]
        return self._join_readable_names(names)

    def _format_editors(self, editors: list[BibliographicPerson]) -> str:
        names = self._format_people(editors)
        return f"{names} (dir.)" if names else ""

    def _join_readable_names(self, names: list[str]) -> str:
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} et {names[1]}"
        return f"{', '.join(names[:-1])} et {names[-1]}"

    def _format_bibl_title(self, title: BibliographicTitle | None) -> str:
        if title is None or not title.text.strip():
            return ""
        escaped = self._escape_text(title.text)
        level = (title.level or "").strip().lower()
        if level == "a":
            stripped = title.text.strip()
            if stripped.startswith("«") and stripped.endswith("»"):
                return escaped
            return rf"\enquote{{{escaped}}}"
        if level in {"m", "j"}:
            return rf"\textit{{{escaped}}}"
        return escaped

    def _format_pages(self, value: str | None) -> str:
        if not value:
            return ""
        text = value.strip()
        text = re.sub(r"^(p{1,2}\.)\s*~?\s*", "", text, flags=re.IGNORECASE)
        if not text:
            return ""
        return rf"p.~{self._escape_text(text)}"

    def _format_volume(self, value: str | None) -> str:
        if not value:
            return ""
        text = value.strip()
        text = re.sub(r"^vol\.\s*~?\s*", "", text, flags=re.IGNORECASE)
        if not text:
            return ""
        return rf"vol.~{self._escape_text(text)}"

    def _format_issue(self, value: str | None) -> str:
        if not value:
            return ""
        text = value.strip()
        text = re.sub(
            r"^(?:no|n°|nº|n\\textsuperscript\{o\})\s*~?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )
        if not text:
            return ""
        return rf"n\textsuperscript{{o}}~{self._escape_text(text)}"

    def _join_bibl_parts(self, parts: Iterable[str | None]) -> str:
        clean = [part.strip(" ,") for part in parts if part and part.strip(" ,")]
        return ", ".join(clean)

    def _append_identifier_sentence(self, text: str, identifiers: list[BibliographicIdentifier]) -> str:
        result = self._ensure_sentence_period(text)
        for identifier in identifiers:
            rendered = self._render_bibl_identifier(identifier)
            if rendered:
                result = f"{result} {rendered}".strip()
        return result

    def _render_bibl_identifier(self, identifier: BibliographicIdentifier) -> str:
        kind = identifier.type.strip().upper()
        value = identifier.value.strip().rstrip(".")
        if not kind or not value:
            return ""
        if kind in {"ISBN", "ISBN-13"}:
            return f"ISBN {self._escape_text(value)}."
        if kind == "DOI":
            return f"DOI {self._bibl_identifier_link(value, self._doi_target(value))}."
        if kind in {"URI", "URL", "SITE"}:
            return f"URI {self._bibl_identifier_link(value, value)}."
        return f"{self._escape_text(kind)} {self._escape_text(value)}."

    def _ensure_sentence_period(self, text: str) -> str:
        result = re.sub(r"\s+", " ", text).strip(" ,")
        result = re.sub(r"(?:,\s*)+\.", ".", result)
        result = re.sub(r"\.{2,}$", ".", result)
        if result and not result.endswith("."):
            result += "."
        return result

    def _doi_target(self, value: str) -> str:
        if value.lower().startswith(("http://", "https://")):
            return value
        return f"https://doi.org/{value}"

    def _bibl_identifier_link(self, label: str, target: str) -> str:
        if not target.strip():
            return self._escape_text(label)
        return rf"\href{{{self._escape_url(target)}}}{{{self._escape_text(label)}}}"

    def _render_list_block(self, list_block: ListBlock) -> str:
        env = "enumerate" if list_block.kind == ListKind.ORDERED else "itemize"
        lines = [rf"\begin{{{env}}}[leftmargin=*]"]
        for item in list_block.items:
            lines.append(self._render_list_item(item))
        lines.append(rf"\end{{{env}}}")
        return "\n".join(lines)

    def _render_list_item(self, item: ListItem) -> str:
        content = self._render_blocks(item.blocks)
        content = content.strip() or ""
        return rf"\item {content}"

    def _render_table_block(self, table: TableBlock) -> str:
        rows = [row for row in table.rows if row.cells]
        caption = self._render_inline_nodes(table.caption) if table.caption else ""
        if not rows:
            if caption.strip():
                return rf"% Table omise sans lignes: {caption}"
            return "% Table omise sans lignes"

        column_count = max(len(row.cells) for row in rows)
        if column_count <= 0:
            return "% Table omise sans colonnes"

        has_merged_cells = any(
            cell.cols > 1 or cell.rows > 1
            for row in rows
            for cell in row.cells
        )

        lines: list[str] = []
        if has_merged_cells:
            lines.append(
                r"% AVERTISSEMENT Impressions : cellules fusionnées TEI non encore rendues (cols/rows ignorés)"
            )
        lines += [
            r"\begin{center}",
            rf"\begin{{tabularx}}{{\linewidth}}{{{'X' * column_count}}}",
            r"\toprule",
        ]

        for row_index, row in enumerate(rows):
            rendered_cells = [self._render_table_cell(cell) for cell in row.cells]
            while len(rendered_cells) < column_count:
                rendered_cells.append("")
            lines.append(" & ".join(rendered_cells) + r"\\")
            if row_index == 0 and any((cell.role or "").strip().lower() == "label" for cell in row.cells):
                lines.append(r"\midrule")

        lines.extend([r"\bottomrule", r"\end{tabularx}"])
        if caption.strip():
            lines.append(rf"\par\small {caption}")
        lines.append(r"\end{center}")
        return "\n".join(lines)

    def _render_table_cell(self, cell: TableCell) -> str:
        content = self._render_inline_nodes(cell.content).strip()
        if (cell.role or "").strip().lower() == "label" and content:
            return rf"\textbf{{{content}}}"
        return content

    def _render_verse_block(self, verse_block: VerseBlock) -> str:
        lines = ["\\begin{verse}"]
        for verse_line in verse_block.lines:
            lines.append(self._render_verse_line(verse_line))
        lines.append("\\end{verse}")
        return "\n".join(lines)

    def _render_verse_line(self, verse_line: VerseLine) -> str:
        content = self._render_inline_nodes(verse_line.content)
        if verse_line.number:
            number = self._escape_text(verse_line.number)
            return rf"{content}\hfill{{\footnotesize {number}}}\\"
        return rf"{content}\\"


# ---------------------------------------------------------------------------
# Inline
# ---------------------------------------------------------------------------

    def _render_inline_nodes(self, nodes: Iterable[InlineNode] | None) -> str:
        if not nodes:
            return ""
        return "".join(self._render_inline_node(node) for node in nodes)

    def _render_inline_node(self, node: InlineNode) -> str:
        if isinstance(node, TextRun):
            return self._escape_text(node.text)
        if isinstance(node, Italic):
            return rf"\textit{{{self._render_inline_nodes(node.children)}}}"
        if isinstance(node, Bold):
            return rf"\textbf{{{self._render_inline_nodes(node.children)}}}"
        if isinstance(node, SmallCaps):
            return rf"\textsc{{{self._render_inline_nodes(node.children)}}}"
        if isinstance(node, Superscript):
            return rf"\textsuperscript{{{self._render_inline_nodes(node.children)}}}"
        if isinstance(node, Subscript):
            return rf"$_{{{self._render_inline_nodes(node.children)}}}$"
        if isinstance(node, Link):
            label = self._render_inline_nodes(node.children) or self._escape_text(node.target)
            target = self._escape_url(node.target)
            return rf"\href{{{target}}}{{{label}}}"
        if isinstance(node, InlineQuote):
            return rf"\enquote{{{self._render_inline_nodes(node.children)}}}"
        if isinstance(node, NoteRef):
            return self._render_note_ref(node)
        return ""

    def _render_note_ref(self, note_ref: NoteRef) -> str:
        if self._in_footnote:
            return r"\textsuperscript{*}"

        note = self._current_notes.get(note_ref.note_id)
        if note is None:
            missing = self._escape_text(note_ref.note_id)
            return rf"\footnote{{[Note introuvable : {missing}]}}"

        content = self._render_footnote_content(note)
        return rf"\footnote{{{content}}}"

    def _render_footnote_content(self, note: Footnote) -> str:
        previous_state = self._in_footnote
        self._in_footnote = True
        try:
            pieces: list[str] = []
            for block in note.blocks:
                rendered = self._render_block(block).strip()
                if rendered:
                    pieces.append(rendered)
            return r"\par ".join(pieces) if pieces else ""
        finally:
            self._in_footnote = previous_state


# ---------------------------------------------------------------------------
# Utilitaires éditoriaux et LaTeX
# ---------------------------------------------------------------------------

    def _volume_publication_line(self, book: Book) -> str:
        items: list[str] = []
        publication = book.metadata.publication
        if publication.publisher:
            items.append(publication.publisher)
        if publication.publication_year:
            items.append(publication.publication_year)
        return " · ".join(item for item in items if item)

    def _join_contributor_names(self, contributors) -> str:
        names = [c.full_name for c in contributors if getattr(c, "full_name", "").strip()]
        return " ; ".join(names)

    def _latex_path(self, path_value: str | None) -> str:
        if not path_value:
            return ""
        return str(Path(path_value).as_posix())

    def _latex_image_path(self, path_value: str | None) -> str:
        if not path_value:
            return ""
        normalized = str(Path(path_value).as_posix())
        normalized = normalized.replace("}", r"\}")
        return rf"\detokenize{{{normalized}}}"

    def _select_figure_image_path(self, figure: FigureBlock) -> str:
        for raw_path in (figure.image_path, figure.alt_image_path):
            if raw_path and Path(raw_path).exists():
                return self._latex_image_path(raw_path)
        return ""

    def _escape_url(self, value: str | None) -> str:
        if value is None:
            return ""
        replacements = {
            "\\": "/",
            "{": r"\{",
            "}": r"\}",
            "&": r"\&",
            "%": r"\%",
            "#": r"\#",
            "_": r"\_",
        }
        return "".join(replacements.get(char, char) for char in value)

    def _escape_text(self, value: str | None) -> str:
        if value is None:
            return ""

        replacements = {
            "\\": r"\textbackslash{}",
            "{": r"\{",
            "}": r"\}",
            "$": r"\$",
            "&": r"\&",
            "%": r"\%",
            "#": r"\#",
            "_": r"\_",
            "^": r"\textasciicircum{}",
            "~": r"\textasciitilde{}",
        }

        escaped = []
        for char in value:
            escaped.append(replacements.get(char, char))
        return "".join(escaped)


# ---------------------------------------------------------------------------
# Fonctions de confort
# ---------------------------------------------------------------------------


def render_book_to_latex(book: Book, options: LatexRenderOptions | None = None) -> str:
    """Fonction de confort pour produire le LaTeX en une ligne."""

    renderer = LatexRenderer(options=options)
    return renderer.render_book(book)


def render_purh_preamble_for_latei(
    *,
    title: str | None = None,
    subtitle: str | None = None,
    contributors: list[str] | None = None,
    publisher: str | None = None,
    publication_year: str | None = None,
    doi: str | None = None,
    isbn_print: str | None = None,
    isbn_pdf: str | None = None,
    collection_title: str | None = None,
    collection_number: str | None = None,
    issn: str | None = None,
) -> str:
    """Wrapper de compatibilité — délègue à latei_preamble.render_purh_latex_preamble.

    Conservé pour les tests legacy et les modules de comparaison. La chaîne LaTEI
    active n'appelle plus cette fonction : elle passe directement par latei_preamble.
    """
    from .latei_preamble import PurhPreambleData, render_purh_latex_preamble

    return render_purh_latex_preamble(PurhPreambleData(
        title=title or "LaTEI PURH",
        subtitle=subtitle or "",
        authors=tuple(v for v in (contributors or []) if v.strip()),
        publisher=publisher or "Presses universitaires de Rouen et du Havre",
        year=publication_year or "",
        doi=doi or "",
        isbn=isbn_pdf or isbn_print or "",
    ))
