from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from purh_site.latei_metadata import extract_latei_metadata
from purh_site.reversible_integration import ReversibleExportResult, run_reversible_export_for_file

FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


@pytest.fixture(scope="module")
def latei_result(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    output_dir = tmp_path_factory.mktemp("latei_direct_title_page")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir / "latei", compile_pdf=False)


@pytest.fixture(scope="module")
def latei_result_with_pdf(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    output_dir = tmp_path_factory.mktemp("latei_direct_title_page_pdf")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir / "latei", compile_pdf=True)


def test_latei_title_page_structure_and_publisher(latei_result: ReversibleExportResult) -> None:
    title_page = _title_page_from_path(latei_result.latei_main_path)
    assert r"\begin{titlepage}" in title_page
    assert r"\end{titlepage}" in title_page
    assert "PURH" in title_page


def test_latei_title_page_no_experimental_marker(latei_result: ReversibleExportResult) -> None:
    title_page = _title_page_from_path(latei_result.latei_main_path)
    assert "Document LaTEI PURH experimental" not in title_page


def test_latei_title_page_does_not_print_absent_metadata(latei_result: ReversibleExportResult) -> None:
    """Metadata absent from the fixture must not appear visually on the title page."""
    metadata = extract_latei_metadata(etree.parse(str(FIXTURE_PATH)).getroot())
    title_page = _title_page_from_path(latei_result.latei_main_path)

    # Heraldique II fixture: no isbn_pdf, isbn_epub, doi — they must not appear in the title page.
    if not metadata.isbn_pdf:
        assert "ISBN PDF" not in title_page
    if not metadata.isbn_epub:
        assert "ISBN ePub" not in title_page
    if not metadata.doi:
        assert "DOI" not in title_page


def test_latei_title_page_keeps_metadata_available_but_not_printed(latei_result: ReversibleExportResult) -> None:
    main = latei_result.latei_main_path.read_text(encoding="utf-8")
    title_page = _title_page_from_text(main)
    metadata = extract_latei_metadata(etree.parse(str(FIXTURE_PATH)).getroot())

    assert metadata.publication_year == "2025"
    assert metadata.isbn_print == "979-10-240-1855-3"
    assert metadata.isbn_pdf == ""
    assert metadata.isbn_epub == ""
    assert metadata.doi == ""

    # Macros must be defined even when values are empty.
    assert r"\newcommand{\PURHYear}{2025}" in main
    assert r"\newcommand{\PURHISBN}{979-10-240-1855-3}" in main
    assert r"\newcommand{\PURHDOI}{}" in main

    # Year and print ISBN must not appear as raw text in the title page block.
    assert "2025" not in title_page
    assert "979-10-240-1855-3" not in title_page


@pytest.mark.full_book
def test_latei_title_page_export_compiles_or_reports_status(latei_result_with_pdf: ReversibleExportResult) -> None:
    assert isinstance(latei_result_with_pdf, ReversibleExportResult)
    assert latei_result_with_pdf.latei_main_path.exists()
    assert latei_result_with_pdf.latei_log_path is not None
    assert latei_result_with_pdf.latei_log_path.exists()
    if latei_result_with_pdf.latei_pdf_success:
        assert latei_result_with_pdf.latei_pdf_path is not None
        assert latei_result_with_pdf.latei_pdf_path.exists()


def _title_page_from_path(path: Path) -> str:
    return _title_page_from_text(path.read_text(encoding="utf-8", errors="replace"))


def _title_page_from_text(text: str) -> str:
    start = text.find(r"\begin{titlepage}")
    end = text.find(r"\end{titlepage}", start)
    assert start >= 0, "No \\begin{titlepage} found in LaTEI main file"
    assert end >= 0, "No \\end{titlepage} found in LaTEI main file"
    return text[start : end + len(r"\end{titlepage}")]
