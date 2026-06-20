from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest
from lxml import etree

from purh_site.latei_stable_pdf import build_stable_pdf_from_latei_body, restore_tei_from_latei_body
from purh_site.latex_renderer import LatexRenderOptions
from purh_site.pdf_builder import PdfBuilder
from purh_site.reversible import compare_tei_elements
from purh_site.reversible_integration import run_reversible_export_for_file


FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


@pytest.fixture(scope="module")
def latei_export(tmp_path_factory: pytest.TempPathFactory):
    output_dir = tmp_path_factory.mktemp("heraldique_latei_for_stable_pdf")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir)


@pytest.fixture(scope="module")
def stable_from_latei(tmp_path_factory: pytest.TempPathFactory, latei_export):
    output_dir = tmp_path_factory.mktemp("heraldique_stable_from_latei")
    return build_stable_pdf_from_latei_body(latei_export.latei_body_path, output_dir)


def test_latei_body_restores_equivalent_metopes_tei(latei_export, stable_from_latei) -> None:
    source = etree.parse(str(FIXTURE_PATH)).getroot()
    restored = restore_tei_from_latei_body(latei_export.latei_body_path)

    assert latei_export.success is True
    assert latei_export.diagnostics_count == 0
    assert stable_from_latei.restored_xml_path.exists()
    assert stable_from_latei.restored_xml_path.name == "heraldique_ii.book.normalized.from_latei.xml"
    assert compare_tei_elements(source, restored) == []

    restored_from_disk = etree.parse(str(stable_from_latei.restored_xml_path)).getroot()
    assert restored_from_disk.tag == "{http://www.tei-c.org/ns/1.0}TEI"
    assert compare_tei_elements(source, restored_from_disk) == []


def test_stable_pdf_pipeline_runs_from_restored_latei_tei(stable_from_latei) -> None:
    result = stable_from_latei

    assert result.stable_output_dir.exists()
    assert result.stable_tex_path.exists()
    assert result.stable_log_path.exists()
    assert result.stable_report_path.exists()
    assert result.stable_pdf_result.tex_path.name == "book.tex"

    stable_tex = result.stable_tex_path.read_text(encoding="utf-8")
    assert r"\documentclass[12pt,twoside,openany]{book}" in stable_tex
    assert "latei_macros" not in stable_tex
    assert r"\teiP" not in stable_tex
    assert r"\begin{teiDiv}" not in stable_tex

    if shutil.which("lualatex") is None:
        assert result.success is False
        assert result.stable_pdf_result.error_message is not None
        assert "Moteur LaTeX introuvable" in result.stable_pdf_result.error_message
        return

    if not result.success:
        log_excerpt = result.stable_log_path.read_text(encoding="utf-8", errors="replace")[:4000]
        pytest.fail(f"Stable PDF build from restored LaTEI TEI failed.\n{log_excerpt}")

    assert result.stable_pdf_path.exists()
    assert result.stable_pdf_path.stat().st_size > 0


def test_stable_latex_from_source_and_restored_latei_use_same_builder(
    tmp_path: Path,
    stable_from_latei,
) -> None:
    direct_output = tmp_path / "direct_stable"
    direct = PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=False,
    ).build_from_normalized_tei(FIXTURE_PATH, direct_output)

    assert direct.success is True
    assert direct.tex_path.exists()
    assert stable_from_latei.stable_tex_path.exists()
    assert direct.tex_path.name == stable_from_latei.stable_tex_path.name == "book.tex"
    assert r"\documentclass[12pt,twoside,openany]{book}" in direct.tex_path.read_text(encoding="utf-8")


def test_stable_pdf_page_count_matches_direct_stable_when_tools_are_available(
    tmp_path: Path,
    stable_from_latei,
) -> None:
    if shutil.which("lualatex") is None or shutil.which("pdfinfo") is None:
        pytest.skip("LuaLaTeX or pdfinfo is unavailable.")

    direct = PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=True,
        timeout_seconds=180,
    ).build_from_normalized_tei(FIXTURE_PATH, tmp_path / "direct_stable_pdf")

    if not direct.success:
        excerpt = direct.log_path.read_text(encoding="utf-8", errors="replace")[:4000]
        pytest.fail(f"Direct stable PDF build failed.\n{excerpt}")

    assert stable_from_latei.success is True
    assert _pdf_page_count(direct.pdf_path) == _pdf_page_count(stable_from_latei.stable_pdf_path)


def test_stable_pdf_bridge_rejects_non_document_latei_body(tmp_path: Path) -> None:
    body_path = tmp_path / "fragment.latei_body.tex"
    body_path.write_text(r"\teiP{Fragment seulement.}", encoding="utf-8")

    with pytest.raises(ValueError, match="requires a full TEI document root"):
        build_stable_pdf_from_latei_body(body_path, tmp_path / "out", compile_pdf=False)


def _pdf_page_count(path: Path) -> int:
    process = subprocess.run(
        [shutil.which("pdfinfo") or "pdfinfo", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    for line in process.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise AssertionError(f"pdfinfo did not report a page count for {path}")
