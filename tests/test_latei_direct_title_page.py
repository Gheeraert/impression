from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from purh_site.latei_metadata import extract_latei_metadata
from purh_site.latex_renderer import LatexRenderOptions
from purh_site.pdf_builder import PdfBuilder
from purh_site.reversible_integration import ReversibleExportResult, run_reversible_export_for_file


FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


@pytest.fixture(scope="module")
def title_page_paths(tmp_path_factory: pytest.TempPathFactory):
    output_dir = tmp_path_factory.mktemp("latei_direct_title_page")
    stable = PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=False,
    ).build_from_normalized_tei(FIXTURE_PATH, output_dir / "stable")
    latei = run_reversible_export_for_file(FIXTURE_PATH, output_dir / "latei")
    return stable, latei


def test_latei_title_page_matches_stable_visible_metadata_policy(title_page_paths) -> None:
    stable, latei = title_page_paths
    stable_title_page = _title_page_block(stable.tex_path)
    latei_title_page = _title_page_block(latei.latei_main_path)

    assert r"\begin{titlepage}" in stable_title_page
    assert r"\begin{titlepage}" in latei_title_page
    assert "PURH" in stable_title_page
    assert "PURH" in latei_title_page
    assert "Document LaTEI PURH experimental" not in latei_title_page

    if "PURH - 2025" not in stable_title_page:
        assert "PURH - 2025" not in latei_title_page
    if "ISBN imprime" not in stable_title_page:
        assert "ISBN imprime" not in latei_title_page
    if "ISBN PDF" not in stable_title_page:
        assert "ISBN PDF" not in latei_title_page
    if "ISBN ePub" not in stable_title_page:
        assert "ISBN ePub" not in latei_title_page
    if "DOI" not in stable_title_page:
        assert "DOI" not in latei_title_page


def test_latei_title_page_keeps_metadata_available_but_not_printed(title_page_paths) -> None:
    _stable, latei = title_page_paths
    main = latei.latei_main_path.read_text(encoding="utf-8")
    title_page = _title_page_from_text(main)
    metadata = extract_latei_metadata(etree.parse(str(FIXTURE_PATH)).getroot())

    assert metadata.publication_year == "2025"
    assert metadata.isbn_print == "979-10-240-1855-3"
    assert metadata.isbn_pdf == ""
    assert metadata.isbn_epub == ""
    assert metadata.doi == ""

    assert r"\newcommand{\PURHYear}{2025}" in main
    assert r"\newcommand{\PURHISBN}{979-10-240-1855-3}" in main
    assert r"\newcommand{\PURHDOI}{}" in main
    assert "2025" not in title_page
    assert "979-10-240-1855-3" not in title_page


def test_latei_title_page_export_compiles_or_reports_status(title_page_paths) -> None:
    _stable, latei = title_page_paths

    assert isinstance(latei, ReversibleExportResult)
    assert latei.latei_main_path.exists()
    assert latei.latei_log_path is not None
    assert latei.latei_log_path.exists()
    if latei.latei_pdf_success:
        assert latei.latei_pdf_path is not None
        assert latei.latei_pdf_path.exists()


def _title_page_block(path: Path) -> str:
    return _title_page_from_text(path.read_text(encoding="utf-8", errors="replace"))


def _title_page_from_text(text: str) -> str:
    start = text.find(r"\begin{titlepage}")
    end = text.find(r"\end{titlepage}", start)
    assert start >= 0
    assert end >= 0
    return text[start : end + len(r"\end{titlepage}")]
