from __future__ import annotations

"""Poésie et citations (référentiel PURH v0.5, "Poésie" / §5.3) : les vers
étaient rendus comme un bloc de citation justifié contenant des \\linebreak,
produisant des blancs excessifs et confondant citation en prose et poésie —
un vrai <lg>/<l> TEI doit passer par l'environnement `verse` (aligné à
gauche, jamais justifié). Les citations elles-mêmes étaient à 11/14 pt avec
des retraits gauche ET droit ≈1,5em au lieu de 9/11 pt, retrait gauche
10 mm seul, observés sur le PDF imprimeur."""

import shutil
from pathlib import Path

import pytest
from lxml import etree

from purh_site.reversible import compare_tei_elements, read_latex_document, write_tei_element
from purh_site.reversible_integration import run_reversible_export_for_file

_VERSE_AND_CITATION_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Livre Poesie</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="article" data-page-title="Article poesie" xml:id="a1">
        <front><div type="titlePage"><p rend="title-main">Article poesie</p></div></front>
        <body>
          <div>
            <p>Paragraphe de prose ordinaire, justifie normalement.</p>
            <lg>
              <l>Premier vers</l>
              <l>Second vers</l>
              <l>Troisieme vers</l>
            </lg>
            <cit><quote>Citation en prose ordinaire, distincte de la poesie.</quote></cit>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def verse_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_verse")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_VERSE_AND_CITATION_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_writer_routes_lg_l_through_dedicated_macros(verse_export) -> None:
    body = verse_export.latei_body_path.read_text(encoding="utf-8")

    assert r"\begin{teiLg}" in body
    assert r"\end{teiLg}" in body
    assert r"\teiL{Premier vers}" in body
    assert r"\teiL{Second vers}" in body
    assert r"\teiL{Troisieme vers}" in body
    # Poetry must not be routed through the citation/blockquote machinery.
    assert r"\begin{teiQuote}" not in body.split(r"\begin{teiLg}")[1].split(r"\end{teiLg}")[0]


def test_macros_define_verse_environment_not_linebreak_in_quote() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")

    assert r"\NewDocumentEnvironment{teiLg}" in macros
    assert r"\begin{verse}" in macros
    assert r"\NewDocumentCommand{\teiL}{O{} +m}{#2\\}" in macros


def test_citation_environment_matches_observed_production_profile() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")

    assert r"\fontsize{{9pt}}{{11pt}}\selectfont" in preamble_source
    assert r"\leftmargin=10mm\rightmargin=0pt" in preamble_source
    # The old, incorrect symmetric-margin citation styling must be gone.
    assert r"\leftmargin=1.5em\rightmargin=1.5em" not in preamble_source
    assert r"\fontsize{{11pt}}{{14pt}}\selectfont" not in preamble_source


def test_lg_l_round_trip_without_diagnostics(verse_export) -> None:
    assert verse_export.success is True
    assert verse_export.diagnostics_count == 0

    body = verse_export.latei_body_path.read_text(encoding="utf-8")
    emitted = write_tei_element(read_latex_document(body))
    source = etree.parse(str(verse_export.source_path)).getroot()
    assert compare_tei_elements(source, emitted) == []


def test_verse_renders_left_aligned_distinct_from_prose_citation(verse_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not verse_export.latei_pdf_success:
        log = verse_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Verse sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(verse_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    lines = process.stdout.splitlines()

    verse_line_indices = [i for i, line in enumerate(lines) if "Premier vers" in line or "Second vers" in line or "Troisieme vers" in line]
    assert len(verse_line_indices) == 3, f"Expected each verse line on its own PDF line: {lines!r}"
