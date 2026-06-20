from __future__ import annotations

"""Bridge a reversible LaTEI body back into the stable PURH PDF pipeline.

This module deliberately does not render PDF from LaTEI macros. It restores
TEI from the controlled LaTEI body, writes an intermediate XML file, and then
delegates to the existing stable ``PdfBuilder``.
"""

from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from .latex_renderer import LatexRenderOptions
from .pdf_builder import PdfBuildResult, PdfBuilder
from .reversible import read_latex_document, write_tei_element
from .utils import TEI_NS


@dataclass(slots=True)
class LateiStablePdfResult:
    latei_body_path: Path
    output_dir: Path
    restored_xml_path: Path
    stable_output_dir: Path
    stable_pdf_result: PdfBuildResult
    success: bool
    message: str

    @property
    def stable_tex_path(self) -> Path:
        return self.stable_pdf_result.tex_path

    @property
    def stable_pdf_path(self) -> Path:
        return self.stable_pdf_result.pdf_path

    @property
    def stable_log_path(self) -> Path:
        return self.stable_pdf_result.log_path

    @property
    def stable_report_path(self) -> Path:
        return self.stable_pdf_result.report_path


def build_stable_pdf_from_latei_body(
    latei_body_path: Path,
    output_dir: Path,
    *,
    latex_engine: str = "lualatex",
    compile_pdf: bool = True,
    timeout_seconds: int = 180,
) -> LateiStablePdfResult:
    """Restore TEI from a LaTEI body and build it with the stable PDF pipeline."""
    body_path = Path(latei_body_path).resolve()
    resolved_output_dir = Path(output_dir).resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    restored_xml_path = resolved_output_dir / f"{_latei_source_stem(body_path)}.from_latei.xml"
    stable_output_dir = resolved_output_dir / f"{_latei_source_stem(body_path)}.stable_from_latei"
    stable_output_dir.mkdir(parents=True, exist_ok=True)

    restored = restore_tei_from_latei_body(body_path)
    _ensure_stable_pdf_tei(restored)
    etree.ElementTree(restored).write(
        str(restored_xml_path),
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=False,
    )

    builder = PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        latex_engine=latex_engine,
        compile_pdf=compile_pdf,
        timeout_seconds=timeout_seconds,
    )
    pdf_result = builder.build_from_normalized_tei(restored_xml_path, stable_output_dir)
    message = (
        "Stable PURH PDF pipeline completed from restored LaTEI TEI."
        if pdf_result.success
        else "Stable PURH PDF pipeline did not complete successfully from restored LaTEI TEI."
    )
    return LateiStablePdfResult(
        latei_body_path=body_path,
        output_dir=resolved_output_dir,
        restored_xml_path=restored_xml_path,
        stable_output_dir=stable_output_dir,
        stable_pdf_result=pdf_result,
        success=pdf_result.success,
        message=message,
    )


def restore_tei_from_latei_body(latei_body_path: Path) -> etree._Element:
    """Read a controlled LaTEI body and restore the corresponding TEI element."""
    latex = Path(latei_body_path).read_text(encoding="utf-8")
    return write_tei_element(read_latex_document(latex))


def _ensure_stable_pdf_tei(element: etree._Element) -> None:
    qname = etree.QName(element)
    if qname.namespace != TEI_NS or qname.localname != "TEI":
        raise ValueError(
            "Stable PDF build from LaTEI requires a full TEI document root; "
            f"got {element.tag!r}."
        )


def _latei_source_stem(path: Path) -> str:
    stem = path.stem
    suffix = ".latei_body"
    if stem.endswith(suffix):
        return stem[: -len(suffix)]
    return stem
