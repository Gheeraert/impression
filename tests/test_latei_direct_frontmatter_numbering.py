from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

LATEI_MACROS_PATH = Path("purh_site/resources/latei_macros.tex")


def test_latei_frontmatter_numbering_policy() -> None:
    """PURH pagination is arabe continue (référentiel PURH v0.5 §5.5/§5.6,
    P0 — état de pagination): liminaries are never roman-numbered, and the
    switch to the main matter never restarts the page counter. The macros
    file is a single static resource shared by every book, so this reads it
    directly instead of exporting a whole fixture through the pipeline."""
    macros = LATEI_MACROS_PATH.read_text(encoding="utf-8")

    assert r"\lateiEnsureFrontMatter" in macros
    assert r"\lateiEnsureMainMatter" in macros
    assert r"\pagenumbering{roman}" not in macros
    assert macros.count(r"\pagenumbering{arabic}") == 1
    assert "arabe continue" in macros


def test_latei_frontmatter_direct_pdf_compiles_on_minimal_liminaires(tmp_path: Path) -> None:
    xml_path = tmp_path / "frontmatter.xml"
    xml_path.write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Frontmatter Test</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="introduction" data-page-title="Introduction">
        <text><front><div><p>Texte liminaire.</p></div></front></text>
      </group>
      <group type="chapter" data-page-title="Chapitre principal">
        <text><body><div><p>Texte du corps.</p></div></body></text>
      </group>
      <group type="chapter" data-page-title="Second chapitre">
        <text><body><div><p>Texte du second chapitre.</p></div></body></text>
      </group>
    </group>
  </text>
</TEI>""",
        encoding="utf-8",
    )
    result = run_reversible_export_for_file(xml_path, tmp_path / "out")
    macros = result.latei_macros_path.read_text(encoding="utf-8")

    assert r"\lateiEnsureFrontMatter" in macros
    assert r"\lateiEnsureMainMatter" in macros
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    assert result.latei_pdf_success is True, result.latei_pdf_message
    assert result.latei_pdf_path.exists()
    assert result.latei_pdf_path.stat().st_size > 0

    # Chapter-opening pages use PURH's blanked "plain" pagestyle (no visible
    # folio at all, référentiel §2.2) — every page in this tiny fixture is
    # one, so there is nothing to scrape from the rendered PDF text. The
    # .toc file records the real \thepage value LaTeX assigned to each
    # chapter, independent of whether that number is ever displayed.
    toc_path = result.latei_pdf_path.with_suffix(".toc")
    assert toc_path.exists(), f"No .toc file next to {result.latei_pdf_path}"
    toc = toc_path.read_text(encoding="utf-8", errors="replace")
    page_numbers = [int(n) for n in re.findall(r"\\contentsline\s*\{chapter\}.*?\{(\d+)\}\{chapter", toc)]
    assert len(page_numbers) == 3, f"Expected 3 chapter entries in the .toc, got: {toc!r}"
    assert page_numbers == sorted(set(page_numbers)), (
        f"Page numbering is not strictly increasing without repeats (a reset was detected): {page_numbers!r}"
    )
