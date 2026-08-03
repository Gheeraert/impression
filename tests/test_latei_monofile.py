from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import ReversibleExportResult, run_reversible_export_for_file

FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


@pytest.fixture(scope="module")
def monofile_result(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    output_dir = tmp_path_factory.mktemp("latei_monofile")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir, compile_pdf=False)


@pytest.fixture(scope="module")
def monofile_result_with_pdf(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    output_dir = tmp_path_factory.mktemp("latei_monofile_pdf")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir, compile_pdf=True)


def test_monofile_is_created(monofile_result: ReversibleExportResult) -> None:
    assert monofile_result.latei_monofile_path.exists()
    assert monofile_result.latei_monofile_path.stat().st_size > 0


def test_monofile_stem_ends_with_latei_tex(monofile_result: ReversibleExportResult) -> None:
    assert monofile_result.latei_monofile_path.name.endswith(".latei.tex")


def test_monofile_has_begin_latei_document(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    assert r"\begin{lateiDocument}" in content


def test_monofile_has_end_latei_document(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    assert r"\end{lateiDocument}" in content


def test_monofile_zone_contains_body_content(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    begin_pos = content.find(r"\begin{lateiDocument}")
    end_pos = content.find(r"\end{lateiDocument}")
    assert begin_pos >= 0 and end_pos > begin_pos
    zone = content[begin_pos:end_pos]
    assert r"\begin{teiElement}[name={teiHeader}]" in zone
    assert r"\begin{teiElement}[name={body}]" in zone


def test_monofile_has_preamble(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    assert r"\documentclass" in content
    assert r"\usepackage{fontspec}" in content
    assert r"\PURHBookTitle" in content


def test_monofile_has_macros_inline(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    assert r"\newenvironment{lateiDocument}{}{}" in content
    assert r"\NewDocumentCommand{\teiP}" in content
    assert r"\NewDocumentCommand{\teiNote}" in content
    assert r"\NewDocumentEnvironment{teiDiv}" in content


def test_monofile_has_graphics_map_inline(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    assert "Experimental LaTEI graphic mapping" in content


def test_monofile_has_no_input_body(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    assert r"\input{" not in content


def test_monofile_has_begin_document(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    assert r"\begin{document}" in content
    assert r"\end{document}" in content


def test_monofile_zone_comes_after_begin_document(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    begin_doc = content.find(r"\begin{document}")
    begin_zone = content.find(r"\begin{lateiDocument}")
    assert begin_doc >= 0 and begin_zone > begin_doc


def test_monofile_has_table_of_contents(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    assert r"\tableofcontents" in content


def test_monofile_has_TeX_program_magic_comment(monofile_result: ReversibleExportResult) -> None:
    content = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    assert "% !TeX program = lualatex" in content


def test_legacy_fragments_still_produced(monofile_result: ReversibleExportResult) -> None:
    assert monofile_result.latei_body_path.exists()
    assert monofile_result.latei_main_path.exists()
    assert monofile_result.latei_macros_path.exists()


def test_legacy_body_unchanged_from_monofile_zone(monofile_result: ReversibleExportResult) -> None:
    body = monofile_result.latei_body_path.read_text(encoding="utf-8").strip()
    monofile = monofile_result.latei_monofile_path.read_text(encoding="utf-8")
    begin_pos = monofile.find(r"\begin{lateiDocument}") + len(r"\begin{lateiDocument}")
    if monofile[begin_pos] == "\n":
        begin_pos += 1
    end_pos = monofile.find(r"\end{lateiDocument}")
    zone = monofile[begin_pos:end_pos].rstrip()
    assert zone == body


@pytest.mark.full_book
def test_monofile_compiles_when_lualatex_is_available(monofile_result_with_pdf: ReversibleExportResult) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not monofile_result_with_pdf.latei_monofile_pdf_success:
        log_path = monofile_result_with_pdf.latei_monofile_log_path
        if log_path is not None and log_path.exists():
            excerpt = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[:160])
            pytest.fail(f"LaTEI monofile did not compile.\n{excerpt}")
        else:
            pytest.fail(f"LaTEI monofile did not compile: {monofile_result_with_pdf.latei_monofile_pdf_message}")

    assert monofile_result_with_pdf.latei_monofile_pdf_path.exists()
    assert monofile_result_with_pdf.latei_monofile_pdf_path.stat().st_size > 0
