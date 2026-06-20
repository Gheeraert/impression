from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest
from lxml import etree

from purh_site.reversible import compare_tei_elements, read_latex_document, write_tei_element
from purh_site.reversible_integration import ReversibleExportResult, run_reversible_export_for_file


FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


@pytest.fixture(scope="module")
def export_result(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    output_dir = tmp_path_factory.mktemp("latei_direct_book_skeleton")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir)


def test_latei_direct_book_skeleton_keeps_body_reversible(export_result: ReversibleExportResult) -> None:
    body = export_result.latei_body_path.read_text(encoding="utf-8")
    source = etree.parse(str(FIXTURE_PATH)).getroot()
    emitted = write_tei_element(read_latex_document(body))

    assert r"\documentclass" not in body
    assert r"\begin{teiElement}[name={teiHeader}]" in body
    assert r"\begin{teiElement}[name={front}]" in body
    assert r"\begin{teiElement}[name={body}]" in body
    assert r"\begin{teiElement}[name={group},type={section1}" in body
    assert r"\begin{teiDiv}[type={section1},xmlid={div01}]" in body
    assert compare_tei_elements(source, emitted) == []
    assert export_result.diagnostics_count == 0


def test_latei_direct_driver_and_macros_have_book_skeleton_invariants(
    export_result: ReversibleExportResult,
) -> None:
    main = export_result.latei_main_path.read_text(encoding="utf-8")
    macros = export_result.latei_macros_path.read_text(encoding="utf-8")

    body_input = rf'\input{{"{export_result.latei_body_path.name}"}}'
    macros_input = rf'\input{{"{export_result.latei_macros_path.name}"}}'

    assert macros_input in main
    assert body_input in main
    assert main.index(body_input) < main.index(r"\tableofcontents")
    assert "purh_site/resources/latei_macros.tex" not in main.replace("\\", "/")

    assert "teiHeader is metadata, not running text" in macros
    assert "name={teiHeader}" in macros
    assert r"\frontmatter" in macros
    assert r"\mainmatter" in macros
    assert r"\backmatter" in macros
    assert r"\tableofcontents" in main
    assert r"\part*{#1}" in macros
    assert r"\chapter{#1}" in macros
    assert r"\chapter*" in macros
    assert r"\markboth" in macros
    assert r"\addcontentsline{toc}{chapter}" in macros
    assert "type={section1}" in macros
    assert "type={section2}" in macros
    assert "type={section3}" in macros
    assert r"\lateiSetHeadContext{part}" in macros
    assert r"\lateiSetHeadContext{section}" in macros
    assert r"\lateiSetHeadContext{subsection}" in macros
    assert r"\lateiSetHeadContext{subsubsection}" in macros
    assert "type={titlePage}" in macros


def test_latei_direct_pdf_compiles_when_lualatex_is_available(export_result: ReversibleExportResult) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not export_result.latei_pdf_success:
        log = export_result.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:160])
        pytest.fail(f"Direct LaTEI PDF did not compile on the real Metopes fixture.\n{excerpt}")

    assert export_result.latei_pdf_path.exists()
    assert export_result.latei_pdf_path.stat().st_size > 0


def test_latei_direct_pdf_is_not_a_tiny_flat_smoke_output(export_result: ReversibleExportResult) -> None:
    if shutil.which("lualatex") is None or shutil.which("pdfinfo") is None:
        pytest.skip("LuaLaTeX or pdfinfo is unavailable.")
    if not export_result.latei_pdf_success:
        pytest.skip(export_result.latei_pdf_message)

    pages = _pdf_page_count(export_result.latei_pdf_path)

    assert pages >= 10


def _pdf_page_count(path: Path) -> int:
    process = subprocess.run(
        [shutil.which("pdfinfo") or "pdfinfo", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    for line in process.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise AssertionError(f"pdfinfo did not report a page count for {path}")
