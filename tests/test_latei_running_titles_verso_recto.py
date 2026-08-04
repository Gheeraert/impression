from __future__ import annotations

"""Running titles must differ recto/verso (référentiel PURH v0.5, "Titres
courants"): verso carries the book title, or the current part's title once
inside one; recto carries the current contribution's short title. Before
this fix, \\chaptermark passed the same value to both sides of \\markboth,
so recto and verso were always identical — the exact defect described
there."""

import re
import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_FILLER_PARAGRAPHS = "<p>Texte de remplissage pour forcer un saut de page.</p>" * 40

_TWO_PART_BOOK_XML = f"""<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Livre Verso Recto</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="section1">
        <head>Premiere Partie</head>
        <group type="article" data-page-title="Titre article un" xml:id="a1">
          <front><div type="titlePage"><p rend="title-main">Titre article un</p></div></front>
          <body><div><p>Corps un.</p>{_FILLER_PARAGRAPHS}</div></body>
        </group>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def two_part_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_verso_recto")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_TWO_PART_BOOK_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_macros_track_recto_and_verso_running_titles_separately() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")

    assert r"\g_latei_verso_running_title_tl" in macros
    assert r"\g_latei_current_running_title_tl" in macros
    assert r"\latei_markboth_recto:n" in macros
    assert r"\latei_markboth_verso:n" in macros
    # The historical bug: \markboth called with the same value on both sides.
    assert re.search(r"\\markboth\{([^{}]*)\}\{\1\}", macros) is None


def test_header_font_is_roman_not_italic() -> None:
    """La famille/couleur a changé deux fois le 2026-08-04 (voir
    test_latei_titraille.py pour le détail) ; seule l'absence d'italique
    reste vérifiée ici, inchangée à travers ces deux passes."""
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\PURHHeaderFont}}{{\PURHTitreFont\small\color[gray]{{0.25}}}}" in preamble_source
    assert r"itshape" not in preamble_source.split(r"\newcommand{{\PURHHeaderFont}}")[1].split("\n")[0]


def test_part_heading_updates_verso_not_recto(two_part_export) -> None:
    macros = two_part_export.latei_macros_path.read_text(encoding="utf-8")
    assert r"\lateiMarkBothVerso" in macros


def test_verso_shows_part_title_recto_shows_contribution_title(two_part_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not two_part_export.latei_pdf_success:
        log = two_part_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Verso/recto sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(two_part_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    lines = [line.strip() for line in process.stdout.splitlines() if line.strip()]

    # The recto header line for the article's second page carries the
    # article's own title together with its folio — never the part title.
    recto_lines = [line for line in lines if line.startswith("Titre article un")]
    assert recto_lines, f"No recto header line found for the article title in: {lines!r}"
    assert all("Premiere Partie" not in line for line in recto_lines)

    # The verso header line carries the part title together with its folio —
    # never the article title.
    verso_lines = [line for line in lines if "Premiere Partie" in line and re.search(r"\d", line)]
    assert verso_lines, f"No verso header line found for the part title in: {lines!r}"
    assert all("Titre article un" not in line for line in verso_lines)
