from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from lxml import etree

from purh_site.reversible import compare_tei_elements, read_latex_document, write_tei_element
from purh_site.reversible_integration import ReversibleExportResult, run_reversible_export_for_file

FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


def write_xml(path: Path, xml: str) -> Path:
    path.write_text(xml, encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def inline_export(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    tmp_path = tmp_path_factory.mktemp("latei_direct_inline")
    xml_path = write_xml(
        tmp_path / "inline.xml",
        '<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_inline">'
        'Un <hi rend="italic">italique</hi>, '
        '<hi rend="small-caps">petites capitales</hi>, '
        '<hi rend="bold">gras</hi>, '
        '<hi rend="sup">exposant</hi>, '
        '<hi rend="sub">indice</hi>, '
        '<hi rend="italic small-caps bold">combine</hi>, '
        '<ref target="https://example.org?a=1&amp;b=2">lien</ref>, '
        '<q>citation</q>'
        '<note place="foot" xml:id="n_inline">Note avec <hi rend="italic">style</hi> '
        '<note place="foot" xml:id="n_nested">note imbriquee</note>.</note>'
        ".</p>",
    )
    return run_reversible_export_for_file(xml_path, tmp_path)


@pytest.fixture(scope="module")
def note_paragraph_export(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    tmp_path = tmp_path_factory.mktemp("latei_direct_note_paragraph")
    xml_path = write_xml(
        tmp_path / "note_paragraph.xml",
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<text><body>"
        "<p>Texte avec note<note place=\"foot\"><p>Texte de note en paragraphe.</p></note>.</p>"
        "</body></text>"
        "</TEI>",
    )
    return run_reversible_export_for_file(xml_path, tmp_path)


@pytest.fixture(scope="module")
def fixture_export(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    output_dir = tmp_path_factory.mktemp("latei_direct_inline_fixture")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir)


def test_latei_direct_inline_body_remains_reversible(inline_export: ReversibleExportResult) -> None:
    source = etree.parse(str(inline_export.source_path)).getroot()
    body = inline_export.latei_body_path.read_text(encoding="utf-8")
    emitted = write_tei_element(read_latex_document(body))

    assert inline_export.success is True
    assert inline_export.diagnostics_count == 0
    assert r"\teiHi[rend={italic}]" in body
    assert r"\teiHi[rend={small-caps}]" in body
    assert r"\teiHi[rend={bold}]" in body
    assert r"\teiHi[rend={sup}]" in body
    assert r"\teiHi[rend={sub}]" in body
    assert r"\teiRef[target={https://example.org?a=1\&b=2}]" in body
    assert r"\teiQ{citation}" in body
    assert r"\teiNote[place={foot},xmlid={n_inline}]" in body
    assert compare_tei_elements(source, emitted) == []


def test_latei_direct_note_with_paragraph_body_remains_reversible(
    note_paragraph_export: ReversibleExportResult,
) -> None:
    source = etree.parse(str(note_paragraph_export.source_path)).getroot()
    body = note_paragraph_export.latei_body_path.read_text(encoding="utf-8")
    emitted = write_tei_element(read_latex_document(body))

    assert note_paragraph_export.success is True
    assert note_paragraph_export.diagnostics_count == 0
    assert r"\teiNote[place={foot}]{\teiP" in body
    assert r"\teiP{Texte de note en paragraphe.}" in body
    assert compare_tei_elements(source, emitted) == []


def test_latei_direct_inline_macros_follow_stable_inline_contract(
    inline_export: ReversibleExportResult,
) -> None:
    macros = inline_export.latei_macros_path.read_text(encoding="utf-8")

    assert r"\footnote" in macros
    assert r"\iflateiinfootnote" in macros
    assert "Nested footnotes are not valid LaTeX" in macros
    assert r"\textsuperscript{*}" in macros
    assert r"\textit" in macros
    assert r"\textbf" in macros
    assert r"\textsc" in macros
    assert r"\textsuperscript" in macros
    assert r"$_{#2}$" in macros
    assert r"\href" in macros
    assert r"\enquote" in macros
    assert "small-caps" in macros
    assert "small_caps" in macros
    assert "small caps" in macros
    assert "gras" in macros
    assert "exposant" in macros
    assert "indice" in macros


def test_latei_direct_note_paragraph_macro_contract(
    note_paragraph_export: ReversibleExportResult,
) -> None:
    macros = note_paragraph_export.latei_macros_path.read_text(encoding="utf-8")
    paragraph_definition = macros[
        macros.index(r"\NewDocumentCommand{\lateiRenderParagraph}") : macros.index("% Matter switches")
    ]

    assert r"\iflateiinfootnote" in paragraph_definition
    assert r"#2\unskip\space" in paragraph_definition
    assert r"\IfStrEq{\lateiHeadContext}{figure}" in paragraph_definition
    assert r"\par #2\par" in paragraph_definition
    assert r"\footnote{#2}" in macros
    assert "Nested footnotes are not valid LaTeX" in macros


def test_latei_direct_inline_pdf_compiles_when_lualatex_is_available(
    inline_export: ReversibleExportResult,
) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not inline_export.latei_pdf_success:
        log = inline_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:140])
        pytest.fail(f"Direct LaTEI inline sample did not compile.\n{excerpt}")

    assert inline_export.latei_pdf_path.exists()
    assert inline_export.latei_pdf_path.stat().st_size > 0


def test_latei_direct_note_paragraph_pdf_text_has_no_number_only_note_line(
    note_paragraph_export: ReversibleExportResult,
) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    pdftotext = shutil.which("pdftotext")
    if pdftotext is None:
        pytest.skip("pdftotext is unavailable.")
    if not note_paragraph_export.latei_pdf_success:
        log = note_paragraph_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:120])
        pytest.fail(f"Direct LaTEI note paragraph sample did not compile.\n{excerpt}")

    process = subprocess.run(
        [pdftotext, "-enc", "UTF-8", str(note_paragraph_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert process.returncode == 0
    assert "Texte de note en paragraphe." in process.stdout
    assert not re.search(r"(?m)^\s*1\s*$\s*^Texte de note en paragraphe\.", process.stdout)


def test_latei_direct_real_fixture_still_round_trips_and_compiles(
    fixture_export: ReversibleExportResult,
) -> None:
    assert fixture_export.success is True
    assert fixture_export.diagnostics_count == 0

    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not fixture_export.latei_pdf_success:
        log = fixture_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:160])
        pytest.fail(f"Direct LaTEI PDF failed on the real Metopes fixture.\n{excerpt}")

    assert fixture_export.latei_pdf_path.exists()
    assert fixture_export.latei_pdf_path.stat().st_size > 0
