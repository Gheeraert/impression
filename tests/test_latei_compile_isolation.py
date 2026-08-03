from __future__ import annotations

"""Compilation must never let a stale auxiliary file bleed into a document
that has nothing to do with it — confirmed real case: a Beautés vitales
table of contents survived inside a Dissimuler pour mieux régner PDF,
traced to a single-pass LuaLaTeX run that never overwrote (or even had a
chance to overwrite) a leftover .toc from an earlier, unrelated document
compiled under the same jobname."""

import shutil
import subprocess
from pathlib import Path

import pytest

from purh_site.latei_driver import (
    _LATEI_AUX_SUFFIXES,
    _purge_stale_latei_aux_files,
    compile_latei_pdf,
)
from purh_site.reversible_integration import run_reversible_export_for_file

TWO_CHAPTER_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="chapter" xml:id="c1">
        <head>Premier chapitre authentique</head>
        <p>Texte du premier chapitre.</p>
      </div>
      <div type="chapter" xml:id="c2">
        <head>Second chapitre authentique</head>
        <p>Texte du second chapitre.</p>
      </div>
    </body>
  </text>
</TEI>"""


def test_purge_stale_latei_aux_files_removes_every_known_suffix(tmp_path: Path) -> None:
    jobname = "monlivre"
    for suffix in _LATEI_AUX_SUFFIXES:
        (tmp_path / f"{jobname}{suffix}").write_text("contenu perime", encoding="utf-8")

    _purge_stale_latei_aux_files(tmp_path, jobname)

    for suffix in _LATEI_AUX_SUFFIXES:
        assert not (tmp_path / f"{jobname}{suffix}").exists()


def test_purge_stale_latei_aux_files_leaves_other_jobnames_alone(tmp_path: Path) -> None:
    unrelated = tmp_path / "autrelivre.toc"
    unrelated.write_text("table des matieres d'un autre livre", encoding="utf-8")

    _purge_stale_latei_aux_files(tmp_path, "monlivre")

    assert unrelated.exists()


def test_stale_toc_from_another_document_does_not_survive_recompilation(tmp_path: Path) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    xml_path = tmp_path / "livre.xml"
    xml_path.write_text(TWO_CHAPTER_XML, encoding="utf-8")
    result = run_reversible_export_for_file(xml_path, tmp_path / "out", compile_pdf=True)
    assert result.latei_monofile_pdf_success is True, result.latei_monofile_pdf_message

    # A single compile_latei_pdf call must already run enough passes for
    # \tableofcontents to resolve its own entries — not just avoid stale
    # content, but genuinely reflect this document on the very first build.
    fresh_pdf_text = _extract_pdf_text(result.latei_monofile_pdf_path)
    # Case-insensitive: the chapter-opening heading is uppercase (titraille,
    # \titleformat{\chapter} — see tests/test_latei_titraille_chapter_div.py)
    # while the TOC entry and running-title headers stay in original case;
    # this test only cares that both titles are genuinely present, not
    # which of those two renderings carries which occurrence.
    fresh_pdf_text_upper = fresh_pdf_text.upper()
    assert "TABLE DES MATI" in fresh_pdf_text_upper
    assert fresh_pdf_text_upper.count("PREMIER CHAPITRE AUTHENTIQUE") >= 2
    assert fresh_pdf_text_upper.count("SECOND CHAPITRE AUTHENTIQUE") >= 2

    # Simulate the real-world contamination: a .toc left behind by a wholly
    # different, previous document, sitting under this exact jobname.
    stale_toc = result.latei_monofile_pdf_path.with_suffix(".toc")
    stale_toc.write_text(
        r"\contentsline {chapter}{\numberline {1}Chapitre Fantome D Un Autre Livre}{99}{}\protected@file@percent"
        "\n",
        encoding="utf-8",
    )

    recompiled = compile_latei_pdf(
        result.latei_monofile_path,
        result.latei_monofile_pdf_path,
        log_path=result.latei_monofile_log_path,
    )
    assert recompiled.success is True, recompiled.message

    pdf_text = _extract_pdf_text(result.latei_monofile_pdf_path)
    assert "Chapitre Fantome" not in pdf_text
    assert "Premier chapitre authentique" in pdf_text
    assert "Second chapitre authentique" in pdf_text


def test_stale_font_cache_is_cleared_before_compiling(tmp_path: Path) -> None:
    # luaotfload's persistent font-name database (built from the system's
    # fonts the first time it's used in a given cache directory) must never
    # survive to a later compile — a font installed after that first
    # build (real case: Chaparral Pro's italic face, only added after
    # earlier builds already had a cache) would otherwise stay invisible
    # to fontspec's automatic \setmainfont shape lookup, with \textit
    # silently falling back to upright instead of failing loudly.
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    xml_path = tmp_path / "livre.xml"
    xml_path.write_text(TWO_CHAPTER_XML, encoding="utf-8")
    result = run_reversible_export_for_file(xml_path, tmp_path / "out", compile_pdf=True)
    assert result.latei_monofile_pdf_success is True, result.latei_monofile_pdf_message

    cache_dir = result.latei_monofile_pdf_path.parent / "latei_tex_cache"
    assert cache_dir.exists()
    stale_marker = cache_dir / "stale_from_a_previous_compile.marker"
    stale_marker.write_text("perime", encoding="utf-8")

    recompiled = compile_latei_pdf(
        result.latei_monofile_path,
        result.latei_monofile_pdf_path,
        log_path=result.latei_monofile_log_path,
    )
    assert recompiled.success is True, recompiled.message
    assert not stale_marker.exists()


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
