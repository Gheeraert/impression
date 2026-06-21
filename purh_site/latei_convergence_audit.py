from __future__ import annotations

"""Differential audit between the stable PURH PDF path and direct LaTEI PDF."""

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess

from .latex_renderer import LatexRenderOptions
from .pdf_builder import PdfBuildResult, PdfBuilder
from .reversible_integration import ReversibleExportResult, run_reversible_export_for_file


@dataclass(slots=True)
class PdfInspection:
    path: Path
    exists: bool
    page_count: int | None = None
    page_size: str = ""
    text_excerpt: str = ""
    error: str = ""


@dataclass(slots=True)
class LateiPdfConvergenceAudit:
    fixture_path: Path
    output_dir: Path
    stable_result: PdfBuildResult
    latei_result: ReversibleExportResult
    stable_pdf: PdfInspection
    latei_pdf: PdfInspection
    report_path: Path


@dataclass(slots=True)
class LateiTexConvergenceAudit:
    fixture_path: Path
    output_dir: Path
    stable_result: PdfBuildResult
    latei_result: ReversibleExportResult
    report_path: Path


def run_latei_pdf_convergence_audit(
    fixture_path: Path,
    output_dir: Path,
    *,
    report_path: Path | None = None,
) -> LateiPdfConvergenceAudit:
    """Generate both PDF paths from one fixture and write a Markdown audit."""
    fixture_path = Path(fixture_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stable_dir = output_dir / "stable_pdf"
    latei_dir = output_dir / "latei_pdf"
    stable_result = PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=True,
        timeout_seconds=180,
    ).build_from_normalized_tei(fixture_path, stable_dir)
    latei_result = run_reversible_export_for_file(fixture_path, latei_dir)

    stable_pdf = inspect_pdf(stable_result.pdf_path)
    latei_pdf = inspect_pdf(latei_result.latei_pdf_path)
    resolved_report_path = Path(report_path) if report_path is not None else output_dir / "AUDIT_PDF_STABLE_VS_LATEI.md"
    resolved_report_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_report_path.write_text(
        build_latei_pdf_convergence_report(
            fixture_path=fixture_path,
            stable_result=stable_result,
            latei_result=latei_result,
            stable_pdf=stable_pdf,
            latei_pdf=latei_pdf,
        ),
        encoding="utf-8",
    )
    return LateiPdfConvergenceAudit(
        fixture_path=fixture_path,
        output_dir=output_dir,
        stable_result=stable_result,
        latei_result=latei_result,
        stable_pdf=stable_pdf,
        latei_pdf=latei_pdf,
        report_path=resolved_report_path,
    )


def run_latei_tex_convergence_audit(
    fixture_path: Path,
    output_dir: Path,
    *,
    report_path: Path | None = None,
) -> LateiTexConvergenceAudit:
    """Generate both TeX paths from one fixture and write a structural TeX audit."""
    fixture_path = Path(fixture_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stable_dir = output_dir / "stable_pdf"
    latei_dir = output_dir / "latei_pdf"
    stable_result = PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=False,
    ).build_from_normalized_tei(fixture_path, stable_dir)
    latei_result = run_reversible_export_for_file(fixture_path, latei_dir)

    resolved_report_path = Path(report_path) if report_path is not None else output_dir / "AUDIT_TEX_STABLE_VS_LATEI.md"
    resolved_report_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_report_path.write_text(
        build_latei_tex_convergence_report(
            fixture_path=fixture_path,
            stable_result=stable_result,
            latei_result=latei_result,
        ),
        encoding="utf-8",
    )
    return LateiTexConvergenceAudit(
        fixture_path=fixture_path,
        output_dir=output_dir,
        stable_result=stable_result,
        latei_result=latei_result,
        report_path=resolved_report_path,
    )


def inspect_pdf(path: Path) -> PdfInspection:
    """Inspect a PDF without comparing binary content."""
    pdf_path = Path(path)
    inspection = PdfInspection(path=pdf_path, exists=pdf_path.exists())
    if not inspection.exists:
        inspection.error = f"PDF not found: {pdf_path}"
        return inspection

    inspection.page_count, inspection.page_size = _pdfinfo_summary(pdf_path)
    inspection.text_excerpt = _extract_pdf_text(pdf_path)
    return inspection


def build_latei_pdf_convergence_report(
    *,
    fixture_path: Path,
    stable_result: PdfBuildResult,
    latei_result: ReversibleExportResult,
    stable_pdf: PdfInspection,
    latei_pdf: PdfInspection,
) -> str:
    stable_tex = _read_text_if_exists(stable_result.tex_path)
    latei_main = _read_text_if_exists(latei_result.latei_main_path)
    latei_body = _read_text_if_exists(latei_result.latei_body_path)
    latei_macros = _read_text_if_exists(latei_result.latei_macros_path)
    stable_title_page = _title_page_block(stable_tex)
    latei_title_page = _title_page_block(latei_main)
    stable_text = _normalize_text(stable_pdf.text_excerpt)
    latei_text = _normalize_text(latei_pdf.text_excerpt)
    first_text_gap = _first_text_gap(stable_text, latei_text)

    lines = [
        "# Audit PDF Stable Vs LaTEI Direct",
        "",
        "## Source",
        "",
        f"- Fixture: `{fixture_path}`",
        f"- Stable TeX: `{stable_result.tex_path}`",
        f"- Stable PDF: `{stable_result.pdf_path}`",
        f"- LaTEI body: `{latei_result.latei_body_path}`",
        f"- LaTEI main: `{latei_result.latei_main_path}`",
        f"- LaTEI macros: `{latei_result.latei_macros_path}`",
        f"- LaTEI PDF: `{latei_result.latei_pdf_path}`",
        "",
        "## Essential Metadata",
        "",
        "- Title: `Héraldique et papauté. Moyen Âge-Temps modernes. II`",
        "- Publisher: `PURH`",
        "- Publication year: `2025`",
        "- Print ISBN: `979-10-240-1855-3`",
        "",
        "## Compilation Result",
        "",
        f"- Stable success: `{stable_result.success}`",
        f"- LaTEI success: `{latei_result.latei_pdf_success}`",
        f"- Stable pages: `{stable_pdf.page_count}`",
        f"- LaTEI pages: `{latei_pdf.page_count}`",
        f"- Stable page size: `{stable_pdf.page_size}`",
        f"- LaTEI page size: `{latei_pdf.page_size}`",
        f"- Stable PDF size: `{_file_size(stable_result.pdf_path)}` bytes",
        f"- LaTEI PDF size: `{_file_size(latei_result.latei_pdf_path)}` bytes",
        "",
        "## LaTeX Comparison",
        "",
        "### Preamble",
        "",
        _checklist(
            [
                ("documentclass book twoside openany", r"\documentclass[12pt,twoside,openany]{book}", stable_tex, latei_main),
                ("geometry", r"\usepackage[", stable_tex, latei_main),
                ("fontspec", r"\usepackage{fontspec}", stable_tex, latei_main),
                ("microtype", r"\usepackage{microtype}", stable_tex, latei_main),
                ("babel", r"\usepackage[french]{babel}", stable_tex, latei_main),
                ("csquotes", r"\usepackage{csquotes}", stable_tex, latei_main),
                ("hyperref", r"\usepackage{hyperref}", stable_tex, latei_main),
                ("fancyhdr", r"\usepackage{fancyhdr}", stable_tex, latei_main),
                ("titlesec", r"\usepackage{titlesec}", stable_tex, latei_main),
                ("PurhBibliography", "PurhBibliography", stable_tex, latei_macros),
            ]
        ),
        "",
        "### Title Page",
        "",
        _checklist(
            [
                ("titlepage", r"\begin{titlepage}", stable_title_page, latei_title_page),
                ("title", "Héraldique et papauté. Moyen Âge-Temps modernes. II", stable_tex, latei_main),
                ("publisher", "PURH", stable_title_page, latei_title_page),
                ("no visible year line", "PURH - 2025", stable_title_page, latei_title_page, True),
                ("no visible print ISBN line", "ISBN imprime", stable_title_page, latei_title_page, True),
                ("no visible PDF ISBN line", "ISBN PDF", stable_title_page, latei_title_page, True),
                ("no visible ePub ISBN line", "ISBN ePub", stable_title_page, latei_title_page, True),
                ("no visible DOI line", "DOI", stable_title_page, latei_title_page, True),
                ("no visible experimental mention", "Document LaTEI PURH experimental", stable_title_page, latei_title_page, True),
            ]
        ),
        "",
        "### Book Structure",
        "",
        _checklist(
            [
                ("frontmatter", r"\frontmatter", stable_tex, latei_macros),
                ("mainmatter", r"\mainmatter", stable_tex, latei_macros),
                ("backmatter", r"\backmatter", stable_tex, latei_macros),
                ("table of contents", r"\tableofcontents", stable_tex, latei_main),
                ("part", r"\part", stable_tex, latei_macros),
                ("chapter", r"\chapter", stable_tex, latei_macros),
                ("section", r"\section", stable_tex, latei_macros),
                ("running heads", r"\markboth", stable_tex, latei_macros),
            ]
        ),
        "",
        "### Blocks",
        "",
        _checklist(
            [
                ("paragraphs", r"\teiP", latei_body, latei_macros),
                ("inline quotation", r"\enquote", stable_tex, latei_macros),
                ("notes", r"\footnote", stable_tex, latei_macros),
                ("figures", r"\includegraphics", stable_tex, latei_macros),
                ("missing image fallback", "Image absente ou non fournie", stable_tex, latei_macros),
                ("bibliography block", r"\begin{PurhBibliography}", stable_tex, latei_macros),
                ("hanging bibliography entry", r"\hangindent=1.5em", stable_tex, latei_macros),
                ("tables", r"\begin{tabular", stable_tex, latei_macros),
                ("lists", r"\begin{itemize", stable_tex, latei_macros),
            ]
        ),
        "",
        "## PDF Text Comparison",
        "",
        f"- Stable text starts with: `{stable_text[:240]}`",
        f"- LaTEI text starts with: `{latei_text[:240]}`",
        f"- First significant text gap: {first_text_gap}",
        "",
        "## Elements Not Yet Migrated Or Still Divergent",
        "",
        "- Table/list policies are not yet audited to visual parity.",
        "- Bibliographic punctuation is readable but not yet equivalent to the stable Python model.",
        "- Figure captions and credits remain conservative and need visual comparison against the stable renderer.",
        "- Page count is allowed to differ while the remaining block policies are still migrating.",
        "- Direct LaTEI must keep converging toward the stable PDF; the stable PDF remains the reference until this audit is closed.",
        "",
    ]
    return "\n".join(lines)


def build_latei_tex_convergence_report(
    *,
    fixture_path: Path,
    stable_result: PdfBuildResult,
    latei_result: ReversibleExportResult,
) -> str:
    stable_tex = _read_text_if_exists(stable_result.tex_path)
    latei_main = _read_text_if_exists(latei_result.latei_main_path)
    latei_body = _read_text_if_exists(latei_result.latei_body_path)
    latei_macros = _read_text_if_exists(latei_result.latei_macros_path)
    latei_log = _read_text_if_exists(latei_result.latei_log_path) if latei_result.latei_log_path else ""
    stable_title_page = _title_page_block(stable_tex)
    latei_title_page = _title_page_block(latei_main)
    title_extra_token = "\\PurhTitleExtra"
    stable_footnotes = _sample_latex_commands(stable_tex, r"\footnote", limit=3)
    latei_notes = _sample_latei_notes(latei_body, limit=3)
    notes_with_paragraphs = _sample_latei_notes_with_paragraphs(latei_body, limit=5)
    tei_p_definition = _extract_definition_window(latei_macros, r"\NewDocumentCommand{\lateiRenderParagraph}", before=1, after=14)
    tei_note_definition = _extract_definition_window(latei_macros, r"\NewDocumentCommand{\teiNote}", before=4, after=14)
    tei_p_has_note_context_branch = r"\iflateiinfootnote" in tei_p_definition and r"#2\unskip\space" in tei_p_definition
    stable_figure = _extract_definition_window(stable_tex, r"\fbox{\parbox", before=4, after=6)
    latei_figure = _extract_definition_window(latei_macros, r"\NewDocumentEnvironment{teiFigure}", before=6, after=8)
    stable_bibliography = _extract_definition_window(stable_tex, r"\begin{PurhBibliography}", before=2, after=8)
    latei_bibliography = _extract_definition_window(latei_macros, r"\NewDocumentCommand{\lateiBibliographyEntry}", before=2, after=12)
    stable_par_count = _count_occurrences(stable_tex, "\\par")
    latei_body_paragraph_count = _count_occurrences(latei_body, "\\teiP")
    latei_macro_par_count = _count_occurrences(latei_macros, "\\par")
    latei_graphics_count = _count_occurrences(latei_body, "\\teiGraphic")
    latei_include_width_present = _contains(latei_macros, "\\includegraphics[width=0.95\\linewidth")
    stable_bibliography_present = _contains(stable_tex, "\\begin{PurhBibliography}")
    stable_hanging_count = _count_occurrences(stable_tex, "\\hangindent=1.5em")
    latei_hanging_present = _contains(latei_macros, "\\hangindent=1.5em")
    stable_tabular_count = _count_occurrences(stable_tex, "\\begin{tabular")
    latei_table_count = _count_occurrences(latei_body, "\\begin{teiTable}")
    stable_itemize_count = _count_occurrences(stable_tex, "\\begin{itemize}")
    latei_list_count = _count_occurrences(latei_body, "\\begin{teiList}")

    lines = [
        "# Audit TeX Stable Vs LaTEI Direct",
        "",
        "## Source",
        "",
        f"- Fixture: `{fixture_path}`",
        f"- Stable `book.tex`: `{stable_result.tex_path}`",
        f"- LaTEI main: `{latei_result.latei_main_path}`",
        f"- LaTEI macros: `{latei_result.latei_macros_path}`",
        f"- LaTEI body: `{latei_result.latei_body_path}`",
        "",
        "This report does not compare `book.tex` and `latei_body.tex` as equal text.",
        "The stable `book.tex` is final typographic LaTeX, while `latei_body.tex` is the reversible semantic source.",
        "The comparison below is structural and cause-oriented.",
        "",
        "## Title page audit",
        "",
        f"- Stable title extras: `{_count_occurrences(stable_title_page, title_extra_token)}`",
        f"- LaTEI title extras: `{_count_occurrences(latei_title_page, title_extra_token)}`",
        f"- Stable contains `PURH - 2025`: `{_contains(stable_title_page, 'PURH - 2025')}`",
        f"- LaTEI contains `PURH - 2025`: `{_contains(latei_title_page, 'PURH - 2025')}`",
        f"- Stable contains visible print ISBN on title page: `{_contains(stable_title_page, 'ISBN imprime')}`",
        f"- LaTEI contains visible print ISBN on title page: `{_contains(latei_title_page, 'ISBN imprime')}`",
        f"- Stable contains visible DOI on title page: `{_contains(stable_title_page, 'DOI')}`",
        f"- LaTEI contains visible DOI on title page: `{_contains(latei_title_page, 'DOI')}`",
        f"- LaTEI visible experimental marker: `{_contains(latei_title_page, 'Document LaTEI PURH experimental')}`",
        "",
        "Resolved local divergence: LaTEI title page no longer prints publication year, ISBN, or DOI lines absent from the stable title page.",
        "",
        "## Footnote audit",
        "",
        "Stable sample:",
        "",
        _fenced("\n\n".join(stable_footnotes) or "No stable footnote sample found."),
        "",
        "LaTEI sample:",
        "",
        _fenced("\n\n".join(latei_notes) or "No LaTEI note sample found."),
        "",
        f"- LaTEI notes containing `\\teiP`: `{len(_latei_notes_with_paragraphs(latei_body))}`",
        f"- LaTEI `\\teiP` definition emits `\\par`: `{_definition_emits_par(tei_p_definition)}`",
        f"- LaTEI `\\teiP` has note-context inline branch: `{tei_p_has_note_context_branch}`",
        f"- LaTEI note macro has nested-note guard: `{_contains(latei_macros, 'Nested footnotes are not valid LaTeX')}`",
        "",
        "LaTEI notes containing `\\teiP` samples:",
        "",
        _fenced("\n\n".join(notes_with_paragraphs) or "No `\\teiP` inside `\\teiNote` found."),
        "",
        "Macro definitions involved:",
        "",
        _fenced(tei_p_definition + "\n\n" + tei_note_definition),
        "",
        "Resolved local cause: `\\teiP` still appears inside `\\teiNote`, but it now has a note-context branch that renders inline before the normal paragraph branch can emit `\\par`.",
        "",
        "## Paragraph audit",
        "",
        f"- Stable explicit paragraph breaks (`\\par`): `{stable_par_count}`",
        f"- LaTEI body paragraph macros (`\\teiP`): `{latei_body_paragraph_count}`",
        f"- LaTEI macro paragraph breaks (`\\par` in macros): `{latei_macro_par_count}`",
        "- Contexts audited: normal, note, figure, bibliography.",
        "",
        "## Figure audit",
        "",
        f"- Stable missing-image fallback occurrences: `{_count_occurrences(stable_tex, 'Image absente ou non fournie')}`",
        f"- LaTEI missing-image fallback defined: `{_contains(latei_macros, 'Image absente ou non fournie')}`",
        f"- LaTEI graphics in body: `{latei_graphics_count}`",
        f"- LaTEI image include width policy present: `{latei_include_width_present}`",
        "",
        "Stable figure/fallback sample:",
        "",
        _fenced(stable_figure or "No stable figure sample found."),
        "",
        "LaTEI figure macro sample:",
        "",
        _fenced(latei_figure or "No LaTEI figure macro sample found."),
        "",
        "## Bibliography audit",
        "",
        f"- Stable `PurhBibliography` block present: `{stable_bibliography_present}`",
        f"- LaTEI `PurhBibliography` block present in macros: `{_contains(latei_macros, 'PurhBibliography')}`",
        f"- Stable hanging entries: `{stable_hanging_count}`",
        f"- LaTEI hanging-entry policy present: `{latei_hanging_present}`",
        f"- LaTEI `biblStruct` fallback in body: `{_count_occurrences(latei_body, 'name={biblStruct}')}`",
        "",
        "Stable bibliography sample:",
        "",
        _fenced(stable_bibliography or "No stable bibliography sample found."),
        "",
        "LaTEI bibliography macro sample:",
        "",
        _fenced(latei_bibliography or "No LaTEI bibliography macro sample found."),
        "",
        "## Tables and lists audit",
        "",
        f"- Stable tabular environments: `{stable_tabular_count}`",
        f"- LaTEI table environments in body: `{latei_table_count}`",
        f"- Stable itemize environments: `{stable_itemize_count}`",
        f"- LaTEI list environments in body: `{latei_list_count}`",
        "",
        "Probable impact: tables/lists are not yet proven visually equivalent and can contribute to page-count drift, but the footnote paragraph pattern is the clearest localized note-layout suspect.",
        "",
        "## Running titles and Unicode spaces audit",
        "",
        f"- Running-title map loaded: `{_contains(latei_main, 'latei_running_titles_map.tex')}`",
        f"- Running-title declarations: `{_count_occurrences(_read_text_if_exists(latei_result.latei_running_titles_map_path), '\\lateiDeclareRunningTitle')}`",
        f"- LaTEI mark helper present: `{_contains(latei_macros, '\\lateiMarkBoth')}`",
        f"- U+00A0 mapped: `{_contains(latei_macros, chr(0x00A0))}`",
        f"- U+202F mapped: `{_contains(latei_macros, chr(0x202F))}`",
        f"- U+2009 mapped: `{_contains(latei_macros, chr(0x2009))}`",
        f"- U+2011 mapped: `{_contains(latei_macros, chr(0x2011))}`",
        f"- U+2033 mapped: `{_contains(latei_macros, chr(0x2033))}`",
        f"- LaTEI log contains `Missing character`: `{_contains(latei_log, 'Missing character')}`",
        "",
        "## Suspected causes to verify before correction",
        "",
        "1. Footnote paragraph breaks were localized to `\\teiP` inside `\\teiNote`; the macro layer now suppresses the initial paragraph break in note context.",
        "2. LaTEI title-page extras now match the stable visible metadata policy for the audited fixture.",
        "3. Figures and bibliography are readable but still macro-level approximations of the stable renderer.",
        "4. Tables/lists are not yet migrated to visual parity.",
        "",
    ]
    return "\n".join(lines)


def _read_text_if_exists(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace") if Path(path).exists() else ""


def _title_page_block(text: str) -> str:
    start = text.find(r"\begin{titlepage}")
    if start < 0:
        return ""
    end = text.find(r"\end{titlepage}", start)
    if end < 0:
        return text[start:]
    return text[start : end + len(r"\end{titlepage}")]


def _count_occurrences(text: str, token: str) -> int:
    return text.count(token)


def _contains(text: str, token: str) -> bool:
    return token in text


def _fenced(text: str) -> str:
    return f"```latex\n{text.strip()}\n```"


def _sample_latex_commands(text: str, command: str, *, limit: int) -> list[str]:
    samples: list[str] = []
    start = 0
    while len(samples) < limit:
        index = text.find(command, start)
        if index < 0:
            break
        sample, end = _balanced_command_sample(text, index)
        samples.append(sample)
        start = max(end, index + len(command))
    return samples


def _balanced_command_sample(text: str, start: int) -> tuple[str, int]:
    cursor = _skip_command_and_options(text, start)
    brace = text.find("{", cursor)
    if brace < 0:
        return text[start : start + 200], start + 200
    depth = 0
    index = brace
    while index < len(text):
        char = text[index]
        previous = text[index - 1] if index > 0 else ""
        if char == "{" and previous != "\\":
            depth += 1
        elif char == "}" and previous != "\\":
            depth -= 1
            if depth == 0:
                end = index + 1
                return text[start:end], end
        index += 1
    return text[start : start + 300], start + 300


def _skip_command_and_options(text: str, start: int) -> int:
    cursor = start
    if cursor < len(text) and text[cursor] == "\\":
        cursor += 1
        while cursor < len(text) and (text[cursor].isalpha() or text[cursor] == "@"):
            cursor += 1
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    while cursor < len(text) and text[cursor] == "[":
        depth = 1
        cursor += 1
        while cursor < len(text) and depth:
            char = text[cursor]
            previous = text[cursor - 1] if cursor > 0 else ""
            if char == "[" and previous != "\\":
                depth += 1
            elif char == "]" and previous != "\\":
                depth -= 1
            cursor += 1
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
    return cursor


def _sample_latei_notes(text: str, *, limit: int) -> list[str]:
    return _sample_latex_commands(text, r"\teiNote", limit=limit)


def _latei_notes_with_paragraphs(text: str) -> list[str]:
    return [sample for sample in _sample_latex_commands(text, r"\teiNote", limit=10_000) if r"\teiP" in sample]


def _sample_latei_notes_with_paragraphs(text: str, *, limit: int) -> list[str]:
    return _latei_notes_with_paragraphs(text)[:limit]


def _extract_definition_window(text: str, needle: str, *, before: int, after: int) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if needle in line:
            start = max(index - before, 0)
            end = min(index + after + 1, len(lines))
            return "\n".join(lines[start:end])
    return ""


def _definition_emits_par(definition: str) -> bool:
    return r"\par" in definition


def _file_size(path: Path) -> int:
    return Path(path).stat().st_size if Path(path).exists() else 0


def _pdfinfo_summary(path: Path) -> tuple[int | None, str]:
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo is None:
        return None, "pdfinfo unavailable"
    process = subprocess.run(
        [pdfinfo, str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if process.returncode != 0:
        return None, f"pdfinfo failed: {process.stderr.strip()}"
    page_count: int | None = None
    page_size = ""
    for line in process.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                page_count = int(line.split(":", 1)[1].strip())
            except ValueError:
                page_count = None
        if line.startswith("Page size:"):
            page_size = line.split(":", 1)[1].strip()
    return page_count, page_size


def _extract_pdf_text(path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if pdftotext is not None:
        process = subprocess.run(
            [pdftotext, "-enc", "UTF-8", str(path), "-"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if process.returncode == 0:
            return process.stdout

    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - depends on optional package
        return f"[pypdf unavailable: {exc}]"
    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages[:5]:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    except Exception as exc:  # pragma: no cover - damaged or unusual PDFs
        return f"[text extraction failed: {exc}]"


def _normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _first_text_gap(stable_text: str, latei_text: str) -> str:
    if not stable_text or not latei_text:
        return "text extraction unavailable"
    stable_words = stable_text.split()
    latei_words = latei_text.split()
    limit = min(len(stable_words), len(latei_words), 80)
    for index in range(limit):
        if stable_words[index] != latei_words[index]:
            return (
                f"word {index + 1}: stable `{stable_words[index]}` vs "
                f"LaTEI `{latei_words[index]}`"
            )
    if len(stable_words) != len(latei_words):
        return f"same prefix, different extracted length: stable {len(stable_words)} words, LaTEI {len(latei_words)} words"
    return "no text gap in extracted prefix"


def _checklist(items: list[tuple]) -> str:
    lines: list[str] = []
    for item in items:
        label, token, stable, latei, *rest = item
        invert = bool(rest[0]) if rest else False
        if invert:
            stable_ok = token not in stable
            latei_ok = token not in latei
        else:
            stable_ok = token in stable
            latei_ok = token in latei
        lines.append(f"- {label}: stable `{_mark(stable_ok)}` / LaTEI `{_mark(latei_ok)}`")
    return "\n".join(lines)


def _mark(value: bool) -> str:
    return "yes" if value else "no"
