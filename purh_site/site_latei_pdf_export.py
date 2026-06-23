from __future__ import annotations

"""Adaptateur LaTEI compatible avec les attentes du site statique.

Ce module prépare la migration du mode PDF du site vers la chaîne LaTEI.
Il n'est pas encore branché dans site_builder.py.

Il traduit les artefacts natifs LaTEI :
- {stem}.latei.tex
- {stem}.latei_mono.pdf
- {stem}.latei_manifest.json

vers les noms contractuels attendus par le site :
- assets/generated/book.tex
- assets/generated/book.pdf
- assets/generated/book.latei_manifest.json
- assets/generated/pdf_build_report.txt

Les artefacts natifs LaTEI restent en place ; latei_assets/ n'est pas déplacé.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path

from .reversible_integration import run_reversible_export_for_file


@dataclass(frozen=True)
class SiteLateiPdfExportResult:
    tex_path: Path
    pdf_path: Path
    manifest_path: Path
    report_path: Path

    source_latei_path: Path
    source_pdf_path: Path
    source_manifest_path: Path

    success: bool
    message: str


def build_site_latei_pdf_artifacts(
    xml_input_path: Path,
    output_dir: Path,
    *,
    compile_pdf: bool,
    latex_engine: str = "lualatex",
) -> SiteLateiPdfExportResult:
    """Build LaTEI PDF artifacts and present them under site-compatible names.

    Delegates to run_reversible_export_for_file, then copies:
    - primary_latei_path  → output_dir / "book.tex"
    - manifest_path       → output_dir / "book.latei_manifest.json"
    - primary_pdf_path    → output_dir / "book.pdf"  (seulement si compile_pdf=True et PDF produit)

    Écrit toujours output_dir / "pdf_build_report.txt" avec une synthèse.

    Les artefacts natifs LaTEI ({stem}.latei.tex, latei_assets/, etc.) ne sont pas supprimés.

    Note : latex_engine est accepté pour symétrie d'API avec stable_pdf_export, mais n'est
    pas encore transmis à run_reversible_export_for_file (qui gère son propre moteur).
    """
    xml_input_path = Path(xml_input_path)
    output_dir = Path(output_dir)

    result = run_reversible_export_for_file(xml_input_path, output_dir)

    tex_path = output_dir / "book.tex"
    pdf_path = output_dir / "book.pdf"
    manifest_path = output_dir / "book.latei_manifest.json"
    report_path = output_dir / "pdf_build_report.txt"

    if result.primary_latei_path.exists():
        shutil.copy2(result.primary_latei_path, tex_path)

    if result.manifest_path.exists():
        shutil.copy2(result.manifest_path, manifest_path)

    pdf_copied = False
    if compile_pdf and result.primary_pdf_path.exists():
        shutil.copy2(result.primary_pdf_path, pdf_path)
        pdf_copied = True

    pdf_site_status = str(pdf_path) if pdf_copied else "non produit"
    report_lines = [
        "PDF build report — LaTEI pipeline",
        "",
        f"XML source              : {xml_input_path}",
        f"LaTEI natif             : {result.primary_latei_path}",
        f"LaTEI site (book.tex)   : {tex_path}",
        f"PDF natif               : {result.primary_pdf_path}",
        f"PDF site (book.pdf)     : {pdf_site_status}",
        f"Manifeste natif         : {result.manifest_path}",
        f"Manifeste site          : {manifest_path}",
        f"Succès export           : {result.success}",
        f"Message                 : {result.message}",
        f"Message PDF monofichier : {result.latei_monofile_pdf_message}",
    ]
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    return SiteLateiPdfExportResult(
        tex_path=tex_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
        report_path=report_path,
        source_latei_path=result.primary_latei_path,
        source_pdf_path=result.primary_pdf_path,
        source_manifest_path=result.manifest_path,
        success=result.success,
        message=result.message,
    )
