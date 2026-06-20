from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from purh_site.latei_convergence_audit import run_latei_pdf_convergence_audit


FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


@pytest.fixture(scope="module")
def convergence_audit(tmp_path_factory: pytest.TempPathFactory):
    output_dir = tmp_path_factory.mktemp("latei_pdf_convergence")
    return run_latei_pdf_convergence_audit(FIXTURE_PATH, output_dir)


def test_latei_pdf_convergence_audit_report_is_produced(convergence_audit) -> None:
    report = convergence_audit.report_path.read_text(encoding="utf-8")

    assert convergence_audit.report_path.exists()
    assert "Audit PDF Stable Vs LaTEI Direct" in report
    assert "Preamble" in report
    assert "Title Page" in report
    assert "Book Structure" in report
    assert "Elements Not Yet Migrated Or Still Divergent" in report
    assert "Héraldique et papauté. Moyen Âge-Temps modernes. II" in report


def test_stable_and_latei_paths_compile_when_lualatex_is_available(convergence_audit) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    assert convergence_audit.stable_result.success is True
    assert convergence_audit.stable_result.pdf_path.exists()
    assert convergence_audit.stable_result.pdf_path.stat().st_size > 0
    assert convergence_audit.latei_result.latei_pdf_success is True
    assert convergence_audit.latei_result.latei_pdf_path.exists()
    assert convergence_audit.latei_result.latei_pdf_path.stat().st_size > 0


def test_latei_direct_title_page_has_no_visible_experimental_marker(convergence_audit) -> None:
    main = convergence_audit.latei_result.latei_main_path.read_text(encoding="utf-8")
    macros = convergence_audit.latei_result.latei_macros_path.read_text(encoding="utf-8")
    report = convergence_audit.report_path.read_text(encoding="utf-8")

    assert "Document LaTEI PURH experimental" not in main
    assert "Document LaTEI PURH experimental" not in macros
    assert "no visible experimental mention: stable `yes` / LaTEI `yes`" in report
    if convergence_audit.latei_pdf.exists and convergence_audit.latei_pdf.text_excerpt:
        assert "Document LaTEI PURH experimental" not in convergence_audit.latei_pdf.text_excerpt


def test_stable_and_latei_pdfs_share_page_format_when_pdfinfo_is_available(convergence_audit) -> None:
    if shutil.which("pdfinfo") is None:
        pytest.skip("pdfinfo is unavailable.")
    if not convergence_audit.stable_pdf.exists or not convergence_audit.latei_pdf.exists:
        pytest.skip("One of the PDFs was not produced.")

    assert convergence_audit.stable_pdf.page_size
    assert convergence_audit.latei_pdf.page_size
    assert convergence_audit.stable_pdf.page_size == convergence_audit.latei_pdf.page_size


def test_extracted_pdf_text_contains_essential_title_metadata(convergence_audit) -> None:
    excerpts = [convergence_audit.stable_pdf.text_excerpt, convergence_audit.latei_pdf.text_excerpt]
    if not all(excerpts) or any(excerpt.startswith("[") for excerpt in excerpts):
        pytest.skip("PDF text extraction is unavailable.")

    for text in excerpts:
        assert "Héraldique et papauté" in text
        assert "PURH" in text
