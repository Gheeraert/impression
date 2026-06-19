from __future__ import annotations

"""Experimental application-facing adapter for the reversible TEI core.

This module exposes a narrow, optional entry point above ``purh_site.reversible``.
It does not replace the existing publication pipeline; it only writes controlled
LaTeX, round-trip TEI, and a human-readable diagnostics report for one XML file.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from lxml import etree

from .latei_driver import build_latei_driver, compile_latei_pdf
from .reversible import Diagnostic, run_tei_latex_tei_roundtrip
from .utils import TEI_NS


@dataclass(slots=True)
class ReversibleExportResult:
    source_path: Path
    output_dir: Path
    latex_path: Path
    latei_body_path: Path
    latei_main_path: Path
    latei_pdf_path: Path
    latei_pdf_success: bool
    latei_pdf_message: str
    roundtrip_xml_path: Path
    diagnostics_path: Path
    diagnostics_count: int
    success: bool
    message: str


def run_reversible_export_for_file(
    xml_path: Path,
    output_dir: Path | None = None,
) -> ReversibleExportResult:
    """Run the experimental TEI -> controlled LaTeX -> TEI export for one file.

    Existing output files with the experimental suffixes are overwritten
    explicitly. The source XML file is never overwritten.
    """
    source_path = Path(xml_path).expanduser()
    resolved_output_dir = _resolve_output_dir(source_path, output_dir)
    (
        latex_path,
        latei_body_path,
        latei_main_path,
        latei_pdf_path,
        roundtrip_xml_path,
        diagnostics_path,
    ) = _output_paths(source_path, resolved_output_dir)

    if not source_path.exists():
        message = f"XML file does not exist: {source_path}"
        _write_error_report(diagnostics_path, message)
        return ReversibleExportResult(
            source_path=source_path,
            output_dir=resolved_output_dir,
            latex_path=latex_path,
            latei_body_path=latei_body_path,
            latei_main_path=latei_main_path,
            latei_pdf_path=latei_pdf_path,
            latei_pdf_success=False,
            latei_pdf_message="LaTEI PDF not produced because the source XML was not read.",
            roundtrip_xml_path=roundtrip_xml_path,
            diagnostics_path=diagnostics_path,
            diagnostics_count=1,
            success=False,
            message=message,
        )
    if not source_path.is_file():
        message = f"XML path is not a file: {source_path}"
        _write_error_report(diagnostics_path, message)
        return ReversibleExportResult(
            source_path=source_path,
            output_dir=resolved_output_dir,
            latex_path=latex_path,
            latei_body_path=latei_body_path,
            latei_main_path=latei_main_path,
            latei_pdf_path=latei_pdf_path,
            latei_pdf_success=False,
            latei_pdf_message="LaTEI PDF not produced because the source XML was not a file.",
            roundtrip_xml_path=roundtrip_xml_path,
            diagnostics_path=diagnostics_path,
            diagnostics_count=1,
            success=False,
            message=message,
        )

    try:
        element = etree.parse(str(source_path)).getroot()
    except etree.XMLSyntaxError as exc:
        message = f"Malformed XML in {source_path}: {exc}"
        _write_error_report(diagnostics_path, message)
        return ReversibleExportResult(
            source_path=source_path,
            output_dir=resolved_output_dir,
            latex_path=latex_path,
            latei_body_path=latei_body_path,
            latei_main_path=latei_main_path,
            latei_pdf_path=latei_pdf_path,
            latei_pdf_success=False,
            latei_pdf_message="LaTEI PDF not produced because the source XML was malformed.",
            roundtrip_xml_path=roundtrip_xml_path,
            diagnostics_path=diagnostics_path,
            diagnostics_count=1,
            success=False,
            message=message,
        )

    result = run_tei_latex_tei_roundtrip(element)

    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    latex_path.write_text(result.latex, encoding="utf-8")
    latei_body_path.write_text(result.latex, encoding="utf-8")
    build_latei_driver(
        latei_body_path,
        latei_main_path,
        title=_document_title(element),
    )
    pdf_result = compile_latei_pdf(latei_main_path, latei_pdf_path)
    etree.ElementTree(result.emitted).write(
        str(roundtrip_xml_path),
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )
    diagnostics_path.write_text(_format_diagnostics(result.diagnostics), encoding="utf-8")

    diagnostics_count = len(result.diagnostics)
    success = diagnostics_count == 0
    if success:
        message = "Reversible export completed without diagnostics."
    else:
        message = f"Reversible export completed with {diagnostics_count} diagnostic(s)."

    return ReversibleExportResult(
        source_path=source_path,
        output_dir=resolved_output_dir,
        latex_path=latex_path,
        latei_body_path=latei_body_path,
        latei_main_path=latei_main_path,
        latei_pdf_path=latei_pdf_path,
        latei_pdf_success=pdf_result.success,
        latei_pdf_message=pdf_result.message,
        roundtrip_xml_path=roundtrip_xml_path,
        diagnostics_path=diagnostics_path,
        diagnostics_count=diagnostics_count,
        success=success,
        message=message,
    )


def _resolve_output_dir(source_path: Path, output_dir: Path | None) -> Path:
    if output_dir is None:
        return source_path.parent
    resolved = Path(output_dir).expanduser()
    if resolved.exists() and not resolved.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {resolved}")
    return resolved


def _output_paths(source_path: Path, output_dir: Path) -> tuple[Path, Path, Path, Path, Path, Path]:
    stem = source_path.stem
    return (
        output_dir / f"{stem}.reversible.tex",
        output_dir / f"{stem}.latei_body.tex",
        output_dir / f"{stem}.latei_main.tex",
        output_dir / f"{stem}.latei.pdf",
        output_dir / f"{stem}.roundtrip.xml",
        output_dir / f"{stem}.roundtrip_diagnostics.txt",
    )


def _format_diagnostics(diagnostics: list[Diagnostic]) -> str:
    if not diagnostics:
        return "No documentary diagnostic was reported.\n"

    lines = ["Documentary diagnostics:"]
    for diagnostic in diagnostics:
        lines.append(f"- {diagnostic.code} at {diagnostic.path}: {diagnostic.message}")
    return "\n".join(lines) + "\n"


def _write_error_report(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"Reversible export failed.\n{message}\n", encoding="utf-8")


def _document_title(element: etree._Element) -> str | None:
    ns = {"tei": TEI_NS}
    candidates = [
        "string(.//tei:teiHeader//tei:titleStmt/tei:title[@type='main'][1])",
        "string(.//tei:teiHeader//tei:titleStmt/tei:title[1])",
        "string(.//tei:head[1])",
    ]
    for expression in candidates:
        value = str(element.xpath(expression, namespaces=ns)).strip()
        if value:
            return value
    return etree.QName(element).localname


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Experimental TEI -> controlled LaTeX -> TEI reversible export."
    )
    parser.add_argument("xml_path", type=Path, help="Path to the TEI/XML file to test.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to the XML file directory.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_reversible_export_for_file(args.xml_path, args.output_dir)
    except Exception as exc:
        print(f"Reversible export failed: {exc}")
        return 1

    print(result.message)
    print(f"LaTeX: {result.latex_path}")
    print(f"LaTEI body: {result.latei_body_path}")
    print(f"LaTEI main: {result.latei_main_path}")
    if result.latei_pdf_success:
        print(f"LaTEI PDF: {result.latei_pdf_path}")
    else:
        print(f"LaTEI PDF: not produced ({result.latei_pdf_message})")
    print(f"Round-trip XML: {result.roundtrip_xml_path}")
    print(f"Diagnostics: {result.diagnostics_path}")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
