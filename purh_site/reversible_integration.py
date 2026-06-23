from __future__ import annotations

"""Experimental application-facing adapter for the reversible TEI core.

This module exposes a narrow, optional entry point above ``purh_site.reversible``.
It does not replace the existing publication pipeline; it only writes controlled
LaTeX, round-trip TEI, and a human-readable diagnostics report for one XML file.
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from lxml import etree

from .latei_assets import package_latei_graphics
from .latei_driver import build_latei_driver, build_latei_monofile, compile_latei_pdf
from .latei_metadata import extract_latei_metadata
from .latei_running_titles import package_latei_running_titles
from .reversible import Diagnostic, extract_latei_document_zone, read_latex_document, run_tei_latex_tei_roundtrip, write_tei_element


@dataclass(slots=True)
class ReversibleExportResult:
    source_path: Path
    output_dir: Path
    latex_path: Path
    latei_body_path: Path
    latei_main_path: Path
    latei_macros_path: Path
    latei_graphics_map_path: Path
    latei_running_titles_map_path: Path
    latei_assets_dir: Path
    latei_copied_images_count: int
    latei_short_running_titles_count: int
    latei_asset_warnings: list[str]
    latei_pdf_path: Path
    latei_log_path: Path | None
    latei_pdf_success: bool
    latei_pdf_message: str
    latei_monofile_path: Path
    latei_monofile_pdf_path: Path
    latei_monofile_log_path: Path | None
    latei_monofile_pdf_success: bool
    latei_monofile_pdf_message: str
    roundtrip_xml_path: Path
    diagnostics_path: Path
    diagnostics_count: int
    manifest_path: Path
    success: bool
    message: str

    @property
    def primary_latei_path(self) -> Path:
        """Artefact LaTEI principal remis à l'éditrice."""
        return self.latei_monofile_path

    @property
    def primary_pdf_path(self) -> Path:
        """PDF principal issu du monofichier."""
        return self.latei_monofile_pdf_path

    @property
    def debug_latei_paths(self) -> tuple[Path, ...]:
        """Fragments LaTEI conservés à titre de debug."""
        return (
            self.latei_body_path,
            self.latei_main_path,
            self.latei_macros_path,
            self.latei_graphics_map_path,
            self.latei_running_titles_map_path,
        )


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
        latei_macros_path,
        latei_graphics_map_path,
        latei_running_titles_map_path,
        latei_assets_dir,
        latei_pdf_path,
        latei_log_path,
        roundtrip_xml_path,
        diagnostics_path,
        latei_monofile_path,
        latei_monofile_pdf_path,
        latei_monofile_log_path,
        manifest_path,
    ) = _output_paths(source_path, resolved_output_dir)

    if not source_path.exists():
        message = f"XML file does not exist: {source_path}"
        _write_error_report(diagnostics_path, message)
        _write_manifest(manifest_path, _error_manifest(
            source_path, resolved_output_dir,
            latei_monofile_path, latei_monofile_pdf_path,
            latei_body_path, latei_main_path, latei_macros_path,
            latei_graphics_map_path, latei_running_titles_map_path,
            roundtrip_xml_path, diagnostics_path, message,
        ))
        return ReversibleExportResult(
            source_path=source_path,
            output_dir=resolved_output_dir,
            latex_path=latex_path,
            latei_body_path=latei_body_path,
            latei_main_path=latei_main_path,
            latei_macros_path=latei_macros_path,
            latei_graphics_map_path=latei_graphics_map_path,
            latei_running_titles_map_path=latei_running_titles_map_path,
            latei_assets_dir=latei_assets_dir,
            latei_copied_images_count=0,
            latei_short_running_titles_count=0,
            latei_asset_warnings=[],
            latei_pdf_path=latei_pdf_path,
            latei_log_path=None,
            latei_pdf_success=False,
            latei_pdf_message="LaTEI PDF not produced because the source XML was not read.",
            latei_monofile_path=latei_monofile_path,
            latei_monofile_pdf_path=latei_monofile_pdf_path,
            latei_monofile_log_path=None,
            latei_monofile_pdf_success=False,
            latei_monofile_pdf_message="LaTEI monofile not produced because the source XML was not read.",
            roundtrip_xml_path=roundtrip_xml_path,
            diagnostics_path=diagnostics_path,
            diagnostics_count=1,
            manifest_path=manifest_path,
            success=False,
            message=message,
        )
    if not source_path.is_file():
        message = f"XML path is not a file: {source_path}"
        _write_error_report(diagnostics_path, message)
        _write_manifest(manifest_path, _error_manifest(
            source_path, resolved_output_dir,
            latei_monofile_path, latei_monofile_pdf_path,
            latei_body_path, latei_main_path, latei_macros_path,
            latei_graphics_map_path, latei_running_titles_map_path,
            roundtrip_xml_path, diagnostics_path, message,
        ))
        return ReversibleExportResult(
            source_path=source_path,
            output_dir=resolved_output_dir,
            latex_path=latex_path,
            latei_body_path=latei_body_path,
            latei_main_path=latei_main_path,
            latei_macros_path=latei_macros_path,
            latei_graphics_map_path=latei_graphics_map_path,
            latei_running_titles_map_path=latei_running_titles_map_path,
            latei_assets_dir=latei_assets_dir,
            latei_copied_images_count=0,
            latei_short_running_titles_count=0,
            latei_asset_warnings=[],
            latei_pdf_path=latei_pdf_path,
            latei_log_path=None,
            latei_pdf_success=False,
            latei_pdf_message="LaTEI PDF not produced because the source XML was not a file.",
            latei_monofile_path=latei_monofile_path,
            latei_monofile_pdf_path=latei_monofile_pdf_path,
            latei_monofile_log_path=None,
            latei_monofile_pdf_success=False,
            latei_monofile_pdf_message="LaTEI monofile not produced because the source XML was not a file.",
            roundtrip_xml_path=roundtrip_xml_path,
            diagnostics_path=diagnostics_path,
            diagnostics_count=1,
            manifest_path=manifest_path,
            success=False,
            message=message,
        )

    try:
        element = etree.parse(str(source_path)).getroot()
    except etree.XMLSyntaxError as exc:
        message = f"Malformed XML in {source_path}: {exc}"
        _write_error_report(diagnostics_path, message)
        _write_manifest(manifest_path, _error_manifest(
            source_path, resolved_output_dir,
            latei_monofile_path, latei_monofile_pdf_path,
            latei_body_path, latei_main_path, latei_macros_path,
            latei_graphics_map_path, latei_running_titles_map_path,
            roundtrip_xml_path, diagnostics_path, message,
        ))
        return ReversibleExportResult(
            source_path=source_path,
            output_dir=resolved_output_dir,
            latex_path=latex_path,
            latei_body_path=latei_body_path,
            latei_main_path=latei_main_path,
            latei_macros_path=latei_macros_path,
            latei_graphics_map_path=latei_graphics_map_path,
            latei_running_titles_map_path=latei_running_titles_map_path,
            latei_assets_dir=latei_assets_dir,
            latei_copied_images_count=0,
            latei_short_running_titles_count=0,
            latei_asset_warnings=[],
            latei_pdf_path=latei_pdf_path,
            latei_log_path=None,
            latei_pdf_success=False,
            latei_pdf_message="LaTEI PDF not produced because the source XML was malformed.",
            latei_monofile_path=latei_monofile_path,
            latei_monofile_pdf_path=latei_monofile_pdf_path,
            latei_monofile_log_path=None,
            latei_monofile_pdf_success=False,
            latei_monofile_pdf_message="LaTEI monofile not produced because the source XML was malformed.",
            roundtrip_xml_path=roundtrip_xml_path,
            diagnostics_path=diagnostics_path,
            diagnostics_count=1,
            manifest_path=manifest_path,
            success=False,
            message=message,
        )

    metadata = extract_latei_metadata(element)
    result = run_tei_latex_tei_roundtrip(element)

    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    latex_path.write_text(result.latex, encoding="utf-8")
    latei_body_path.write_text(result.latex, encoding="utf-8")
    asset_package = package_latei_graphics(
        element,
        source_xml_path=source_path,
        output_dir=resolved_output_dir,
        graphics_map_path=latei_graphics_map_path,
    )
    running_titles_package = package_latei_running_titles(
        element,
        latei_running_titles_map_path,
    )
    build_latei_driver(
        latei_body_path,
        latei_main_path,
        macros_tex_path=latei_macros_path,
        graphics_map_tex_path=latei_graphics_map_path,
        running_titles_map_tex_path=latei_running_titles_map_path,
        metadata=metadata,
    )
    pdf_result = compile_latei_pdf(
        latei_main_path,
        latei_pdf_path,
        log_path=latei_log_path,
    )

    graphics_map_content = latei_graphics_map_path.read_text(encoding="utf-8") if latei_graphics_map_path.exists() else None
    running_titles_map_content = latei_running_titles_map_path.read_text(encoding="utf-8") if latei_running_titles_map_path.exists() else None
    build_latei_monofile(
        result.latex,
        latei_monofile_path,
        graphics_map_content=graphics_map_content,
        running_titles_map_content=running_titles_map_content,
        metadata=metadata,
    )
    monofile_pdf_result = compile_latei_pdf(
        latei_monofile_path,
        latei_monofile_pdf_path,
        log_path=latei_monofile_log_path,
    )

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

    _write_manifest(manifest_path, {
        "version": 1,
        "source_xml": _rel_path(source_path, resolved_output_dir),
        "primary": {
            "latei": _rel_path(latei_monofile_path, resolved_output_dir),
            "pdf": _rel_path(latei_monofile_pdf_path, resolved_output_dir),
            "xml_restore_supported": True,
        },
        "debug": {
            "latei_body": _rel_path(latei_body_path, resolved_output_dir),
            "latei_main": _rel_path(latei_main_path, resolved_output_dir),
            "latei_macros": _rel_path(latei_macros_path, resolved_output_dir),
            "graphics_map": _rel_path(latei_graphics_map_path, resolved_output_dir),
            "running_titles_map": _rel_path(latei_running_titles_map_path, resolved_output_dir),
        },
        "roundtrip": {
            "xml": _rel_path(roundtrip_xml_path, resolved_output_dir),
            "diagnostics": _rel_path(diagnostics_path, resolved_output_dir),
            "diagnostics_count": diagnostics_count,
        },
        "messages": {
            "latei_pdf": pdf_result.message,
            "latei_monofile_pdf": monofile_pdf_result.message,
        },
    })

    return ReversibleExportResult(
        source_path=source_path,
        output_dir=resolved_output_dir,
        latex_path=latex_path,
        latei_body_path=latei_body_path,
        latei_main_path=latei_main_path,
        latei_macros_path=latei_macros_path,
        latei_graphics_map_path=latei_graphics_map_path,
        latei_running_titles_map_path=latei_running_titles_map_path,
        latei_assets_dir=asset_package.assets_dir,
        latei_copied_images_count=asset_package.copied_count,
        latei_short_running_titles_count=running_titles_package.shortened_count,
        latei_asset_warnings=asset_package.warnings,
        latei_pdf_path=latei_pdf_path,
        latei_log_path=pdf_result.log_path,
        latei_pdf_success=pdf_result.success,
        latei_pdf_message=pdf_result.message,
        latei_monofile_path=latei_monofile_path,
        latei_monofile_pdf_path=latei_monofile_pdf_path,
        latei_monofile_log_path=monofile_pdf_result.log_path,
        latei_monofile_pdf_success=monofile_pdf_result.success,
        latei_monofile_pdf_message=monofile_pdf_result.message,
        roundtrip_xml_path=roundtrip_xml_path,
        diagnostics_path=diagnostics_path,
        diagnostics_count=diagnostics_count,
        manifest_path=manifest_path,
        success=success,
        message=message,
    )


def restore_xml_from_latei_body(latei_body_path: Path, output_xml_path: Path) -> Path:
    """Restore TEI XML from a controlled reversible LaTEI body file."""
    body_path = Path(latei_body_path).expanduser()
    if not body_path.exists():
        raise FileNotFoundError(f"LaTEI body file does not exist: {body_path}")
    if not body_path.is_file():
        raise ValueError(f"LaTEI body path is not a file: {body_path}")

    output_path = Path(output_xml_path).expanduser()
    latex = body_path.read_text(encoding="utf-8")
    element = write_tei_element(read_latex_document(latex))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    etree.ElementTree(element).write(
        str(output_path),
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )
    return output_path


def restore_xml_from_latei_monofile(monofile_path: Path, output_xml_path: Path) -> Path:
    """Restore TEI XML from the reversible zone of a LaTEI monofile.

    Extracts the content between \\begin{lateiDocument} and
    \\end{lateiDocument}, then passes it to the strict parser exactly as
    ``restore_xml_from_latei_body`` would. The preamble, macros, mappings,
    and title page are never seen by the parser.
    """
    mono_path = Path(monofile_path).expanduser()
    if not mono_path.exists():
        raise FileNotFoundError(f"LaTEI monofile does not exist: {mono_path}")
    if not mono_path.is_file():
        raise ValueError(f"LaTEI monofile path is not a file: {mono_path}")

    output_path = Path(output_xml_path).expanduser()
    monofile_text = mono_path.read_text(encoding="utf-8")
    zone = extract_latei_document_zone(monofile_text)
    element = write_tei_element(read_latex_document(zone))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    etree.ElementTree(element).write(
        str(output_path),
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )
    return output_path


def _resolve_output_dir(source_path: Path, output_dir: Path | None) -> Path:
    if output_dir is None:
        return source_path.parent
    resolved = Path(output_dir).expanduser()
    if resolved.exists() and not resolved.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {resolved}")
    return resolved


def _output_paths(
    source_path: Path, output_dir: Path
) -> tuple[Path, Path, Path, Path, Path, Path, Path, Path, Path, Path, Path, Path, Path, Path, Path]:
    stem = source_path.stem
    return (
        output_dir / f"{stem}.reversible.tex",
        output_dir / f"{stem}.latei_body.tex",
        output_dir / f"{stem}.latei_main.tex",
        output_dir / f"{stem}.latei_macros.tex",
        output_dir / f"{stem}.latei_graphics_map.tex",
        output_dir / f"{stem}.latei_running_titles_map.tex",
        output_dir / "latei_assets",
        output_dir / f"{stem}.latei.pdf",
        output_dir / f"{stem}.latei_build.log",
        output_dir / f"{stem}.roundtrip.xml",
        output_dir / f"{stem}.roundtrip_diagnostics.txt",
        output_dir / f"{stem}.latei.tex",
        output_dir / f"{stem}.latei_mono.pdf",
        output_dir / f"{stem}.latei_mono_build.log",
        output_dir / f"{stem}.latei_manifest.json",
    )


def _rel_path(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return str(path)


def _write_manifest(manifest_path: Path, data: dict) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _error_manifest(
    source_path: Path,
    output_dir: Path,
    latei_monofile_path: Path,
    latei_monofile_pdf_path: Path,
    latei_body_path: Path,
    latei_main_path: Path,
    latei_macros_path: Path,
    latei_graphics_map_path: Path,
    latei_running_titles_map_path: Path,
    roundtrip_xml_path: Path,
    diagnostics_path: Path,
    error_message: str,
) -> dict:
    return {
        "version": 1,
        "source_xml": _rel_path(source_path, output_dir),
        "primary": {
            "latei": _rel_path(latei_monofile_path, output_dir),
            "pdf": _rel_path(latei_monofile_pdf_path, output_dir),
            "xml_restore_supported": False,
        },
        "debug": {
            "latei_body": _rel_path(latei_body_path, output_dir),
            "latei_main": _rel_path(latei_main_path, output_dir),
            "latei_macros": _rel_path(latei_macros_path, output_dir),
            "graphics_map": _rel_path(latei_graphics_map_path, output_dir),
            "running_titles_map": _rel_path(latei_running_titles_map_path, output_dir),
        },
        "roundtrip": {
            "xml": _rel_path(roundtrip_xml_path, output_dir),
            "diagnostics": _rel_path(diagnostics_path, output_dir),
            "diagnostics_count": 1,
        },
        "messages": {
            "latei_pdf": "not produced",
            "latei_monofile_pdf": "not produced",
        },
        "error": error_message,
    }


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
    print("")
    print("Fichier LaTEI éditable (principal) :")
    print(f"  {result.primary_latei_path}")
    if result.latei_monofile_pdf_success:
        print(f"PDF principal : {result.primary_pdf_path}")
    else:
        print(f"PDF principal : non produit ({result.latei_monofile_pdf_message})")
    print(f"Manifeste : {result.manifest_path}")
    print("")
    print("Fragments debug :")
    print(f"  Corps réversible : {result.latei_body_path}")
    print(f"  Driver compilable : {result.latei_main_path}")
    print(f"  Macros : {result.latei_macros_path}")
    print(f"  Mapping images : {result.latei_graphics_map_path}")
    print(f"  Mapping titres courants : {result.latei_running_titles_map_path}")
    print(f"LaTEI assets: {result.latei_assets_dir} ({result.latei_copied_images_count} copied image(s))")
    print(f"LaTEI shortened running titles: {result.latei_short_running_titles_count}")
    for warning in result.latei_asset_warnings:
        print(f"LaTEI asset warning: {warning}")
    if result.latei_pdf_success:
        print(f"PDF LaTEI (debug) : {result.latei_pdf_path}")
    else:
        print(f"PDF LaTEI (debug) : non produit ({result.latei_pdf_message})")
    if result.latei_log_path is not None:
        print(f"LaTEI log: {result.latei_log_path}")
    print(f"Round-trip XML: {result.roundtrip_xml_path}")
    print(f"Diagnostics: {result.diagnostics_path}")
    print(f"LaTeX: {result.latex_path}")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
