from __future__ import annotations

"""Adaptateur transitoire vers l'ancienne chaîne PDF stable.

Isole PdfBuilder et LatexRenderOptions hors de site_builder.py, afin que la
chaîne HTML/site ne connaisse plus directement les modules stable/legacy.

Ce module n'est pas le chemin PDF cible à long terme.  Il pourra être déplacé
en legacy lorsque le PDF LaTEI deviendra le chemin de production (Passe E).
"""

from pathlib import Path

from .latex_renderer import LatexRenderOptions
from .pdf_builder import PdfBuildResult, PdfBuilder

__all__ = ["PdfBuildResult", "build_stable_pdf_artifacts"]


def build_stable_pdf_artifacts(
    xml_input_path: Path,
    output_dir: Path,
    *,
    compile_pdf: bool,
    latex_engine: str = "lualatex",
) -> PdfBuildResult:
    """Build stable PURH PDF artifacts from a normalized TEI XML file."""
    return PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=compile_pdf,
        latex_engine=latex_engine,
    ).build_from_normalized_tei(xml_input_path, output_dir)
