from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from purh_site.latei_typography import _short_running_title
from purh_site.reversible_integration import run_reversible_export_for_file

LONG_CHAPTER_TITLE = (
    "Les cérémonies pontificales et les pratiques héraldiques dans les "
    "manuscrits enluminés de la première modernité"
)


def test_minimal_latei_running_title_uses_short_mark_without_touching_body(tmp_path: Path) -> None:
    xml_path = tmp_path / "minimal_running_title.xml"
    paragraphs = "\n".join(
        "<p>Texte de remplissage pour forcer plusieurs pages et rendre visible "
        "le titre courant abrégé dans les en-têtes du PDF LaTEI direct.</p>"
        for _ in range(120)
    )
    xml_path.write_text(
        f"""<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="chapter" xml:id="chapitre-long">
        <head>{LONG_CHAPTER_TITLE}</head>
        {paragraphs}
      </div>
    </body>
  </text>
</TEI>""",
        encoding="utf-8",
    )
    result = run_reversible_export_for_file(xml_path, tmp_path / "out")

    body = result.latei_body_path.read_text(encoding="utf-8")
    main = result.latei_main_path.read_text(encoding="utf-8")
    macros = result.latei_macros_path.read_text(encoding="utf-8")
    running_map = result.latei_running_titles_map_path.read_text(encoding="utf-8")
    expected_short_title = _short_running_title(LONG_CHAPTER_TITLE)

    assert expected_short_title != LONG_CHAPTER_TITLE

    # Diagnostic: the reversible body keeps the full title and no typographic map.
    assert rf"\teiHead{{{LONG_CHAPTER_TITLE}}}" in body
    assert "latei_running_titles_map" not in body

    # Diagnostic: the non-reversible mapping is loaded by the driver before the body.
    assert result.latei_running_titles_map_path.exists()
    assert rf'\input{{"{result.latei_running_titles_map_path.name}"}}' in main
    assert main.index(result.latei_running_titles_map_path.name) < main.index(result.latei_body_path.name)

    # Diagnostic: the mapping key and value are exactly the full title and stable short title.
    assert rf"\lateiDeclareRunningTitle{{{LONG_CHAPTER_TITLE}}}{{{expected_short_title}}}" in running_map

    # Diagnostic: chapter titles remain complete, but marks go through the short-title resolver.
    assert r"\lateiChapter{#1}" in macros
    assert r"\lateiCurrentRunningTitle" in macros
    assert r"\fancyhead[LO,RE]{\PURHHeaderFont\nouppercase{\lateiCurrentRunningTitle}}" in macros
    assert r"\RenewDocumentCommand{\chaptermark}{m}{\lateiMarkBoth{#1}}" in macros
    assert r"\chapter[\tl_use:N \l_latei_running_title_tl]{#1}" not in macros
    assert r"\chapter{#1}" in macros
    assert r"\addcontentsline{toc}{chapter}{#1}" in macros
    assert r"\addcontentsline{toc}{part}{#1}" in macros
    assert r"\latei_markboth:n" in macros
    assert r"\prop_get:NnNTF \g_latei_running_titles_map_prop { #1 }" in macros
    assert rf"\markboth{{{LONG_CHAPTER_TITLE}}}{{{LONG_CHAPTER_TITLE}}}" not in macros
    assert rf"\markboth{{{LONG_CHAPTER_TITLE}}}{{{LONG_CHAPTER_TITLE}}}" not in main
    assert rf"\markboth{{{LONG_CHAPTER_TITLE}}}{{{LONG_CHAPTER_TITLE}}}" not in body

    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    assert result.latei_pdf_success is True, result.latei_pdf_message
    assert result.latei_pdf_path.exists()
    assert result.latei_pdf_path.stat().st_size > 0

    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    raw_pdf_text = _extract_pdf_text(result.latei_pdf_path)
    pdf_text = _normalize_pdf_text(raw_pdf_text)
    full_count = pdf_text.count(LONG_CHAPTER_TITLE)
    short_count = pdf_text.count(expected_short_title)
    short_stem = expected_short_title.rstrip("â€¦…�")
    running_title_lines = [
        _normalize_pdf_text(line)
        for line in raw_pdf_text.splitlines()
        if short_stem in _normalize_pdf_text(line) and LONG_CHAPTER_TITLE not in _normalize_pdf_text(line)
    ]
    title_debug_lines = [
        _normalize_pdf_text(line)
        for line in raw_pdf_text.splitlines()
        if LONG_CHAPTER_TITLE in _normalize_pdf_text(line)
        or short_stem in _normalize_pdf_text(line)
    ]

    assert full_count >= 1
    assert full_count <= 2, (
        f"full_count={full_count}\n"
        f"short_count={short_count}\n"
        f"short_title={expected_short_title}\n"
        + "\n".join(title_debug_lines)
    )
    assert short_count >= 1 or running_title_lines
    assert running_title_lines


def _extract_pdf_text(path: Path) -> str:
    process = subprocess.run(
        [shutil.which("pdftotext") or "pdftotext", "-enc", "UTF-8", str(path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    return process.stdout


def _normalize_pdf_text(text: str) -> str:
    return " ".join(text.split())
