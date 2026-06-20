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
                ("titlepage", r"\begin{titlepage}", stable_tex, latei_main),
                ("title", "Héraldique et papauté. Moyen Âge-Temps modernes. II", stable_tex, latei_main),
                ("publisher", "PURH", stable_tex, latei_main),
                ("year", "2025", stable_tex, latei_main),
                ("print ISBN", "979-10-240-1855-3", stable_tex, latei_main),
                ("no visible experimental mention", "Document LaTEI PURH experimental", stable_tex, latei_main, True),
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


def _read_text_if_exists(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace") if Path(path).exists() else ""


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
