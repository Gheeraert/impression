from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from purh_site.latex_renderer import LatexRenderOptions
from purh_site.pdf_builder import PdfBuilder
from purh_site.reversible_integration import run_reversible_export_for_file


FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


def test_latei_frontmatter_numbering_policy_matches_stable_book_switches(tmp_path: Path) -> None:
    stable = PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=False,
    ).build_from_normalized_tei(FIXTURE_PATH, tmp_path / "stable")
    result = run_reversible_export_for_file(FIXTURE_PATH, tmp_path / "latei")

    stable_tex = stable.tex_path.read_text(encoding="utf-8")
    macros = result.latei_macros_path.read_text(encoding="utf-8")

    assert r"\frontmatter" in stable_tex
    assert r"\mainmatter" in stable_tex
    assert r"\frontmatter" in macros
    assert r"\mainmatter" in macros
    assert "separate numbering policy" in macros
    assert r"\pagenumbering{arabic}" not in macros


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
