from __future__ import annotations

"""Théâtre et poésie mêlés (TEI <sp>/<speaker>/<stage>, Commons-Publishing) :
jusqu'ici sans macro dédiée, <sp> retombait sur le générique \\teiElement
(aucun habillage) et <speaker>/<stage> de même — locuteur, didascalie et
texte de réplique s'enchaînaient tous en un seul paragraphe justifié
indifférencié. Vérification humaine directe, 2026-08-06, sur un extrait
authentique de *Dissimuler pour mieux régner* (chapitre "Secrets de
théâtre", passage "Maguelonne, riant" à "Je suis un monstre [...]", cité
depuis *Le Roi s'amuse* de Hugo) mêlant théâtre (<sp>/<speaker>/<stage>) et
poésie (<l> directement enfant de <sp>, sans <lg> intermédiaire — une
construction TEI valide, distincte de la poésie autonome déjà couverte par
test_latei_verse_and_citations.py)."""

import shutil
from pathlib import Path

import pytest
from lxml import etree

from purh_site.reversible import compare_tei_elements, read_latex_document, write_tei_element
from purh_site.reversible_integration import run_reversible_export_for_file

_THEATRE_VERSE_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Livre Theatre</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="article" data-page-title="Article theatre" xml:id="a1">
        <front><div type="titlePage"><p rend="title-main">Article theatre</p></div></front>
        <body>
          <div>
            <p>Texte d'introduction avant la citation.</p>
            <cit xml:id="cit01">
              <quote>
                <sp>
                  <speaker>Maguelonne</speaker>
                  <stage type="delivery">riant</stage>
                  <l>Monsieur, vous m'avez l'air d'un libertin parfait !</l>
                </sp>
                <sp>
                  <speaker>Le Roi</speaker>
                  <stage type="delivery">riant aussi</stage>
                  <l>Oui, j'ai fait le malheur de plus d'une, en effet.</l>
                  <l>C'est vrai, je suis un monstre.</l>
                </sp>
              </quote>
            </cit>
            <p>Texte de suite apres la citation.</p>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def theatre_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_theatre_speech")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_THEATRE_VERSE_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_writer_routes_sp_speaker_stage_through_dedicated_macros(theatre_export) -> None:
    body = theatre_export.latei_body_path.read_text(encoding="utf-8")

    assert r"\begin{teiSp}" in body
    assert r"\end{teiSp}" in body
    assert r"\teiSpeaker{Maguelonne}" in body
    assert r"\teiStage[type={delivery}]{riant}" in body
    assert r"\teiL{Monsieur" in body
    # <sp> must not fall back to the generic, unstyled \teiElement wrapper.
    assert r"\begin{teiElement}[name={sp}" not in body


def test_standalone_stage_uses_block_macro_inline_stage_uses_inline_macro() -> None:
    """<stage> directly inside <sp> (sibling of <l>/<speaker>, not nested in
    a <p>/<l> of its own) must force a line break (\\teiStage) ; a <stage>
    nested mid-paragraph or mid-verse must not (\\teiStageInline) — mirrors
    the HTML XSLT's own tei:p/tei:stage | tei:l/tei:stage distinction."""
    import tempfile

    xml = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
      <teiHeader>
        <fileDesc>
          <titleStmt><title>Livre</title></titleStmt>
          <publicationStmt><publisher>PURH</publisher></publicationStmt>
          <sourceDesc><p>Source</p></sourceDesc>
        </fileDesc>
      </teiHeader>
      <text><group type="book">
        <group type="article" data-page-title="Article" xml:id="a1">
          <front><div type="titlePage"><p rend="title-main">Article</p></div></front>
          <body><div>
            <sp><p>Avant <stage>un geste</stage> apres.</p></sp>
            <sp><l>Vers avec <stage>geste</stage> au milieu.</l></sp>
          </div></body>
        </group>
      </group></text>
    </TEI>"""
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "book.xml"
        xml_path.write_text(xml, encoding="utf-8")
        result = run_reversible_export_for_file(xml_path, Path(tmp) / "out")
        body = result.latei_body_path.read_text(encoding="utf-8")
        assert r"\teiStageInline{un geste}" in body
        assert r"\teiStageInline{geste}" in body
        assert r"\teiStage{" not in body.replace(r"\teiStageInline{", "")


def test_macros_define_dedicated_theatre_commands() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")

    assert r"\NewDocumentEnvironment{teiSp}" in macros
    assert r"\raggedright" in macros.split(r"\NewDocumentEnvironment{teiSp}")[1].split("}{}")[0]
    assert r"\NewDocumentCommand{\teiSpeaker}{O{} +m}{{\bfseries #2}\\}" in macros
    assert r"\NewDocumentCommand{\teiStage}{O{} +m}{{\itshape (#2)}\\}" in macros
    assert r"\NewDocumentCommand{\teiStageInline}{O{} +m}{{\itshape (#2)}}" in macros


def test_theatre_verse_round_trip_without_diagnostics(theatre_export) -> None:
    assert theatre_export.success is True
    assert theatre_export.diagnostics_count == 0

    body = theatre_export.latei_body_path.read_text(encoding="utf-8")
    emitted = write_tei_element(read_latex_document(body))
    source = etree.parse(str(theatre_export.source_path)).getroot()
    assert compare_tei_elements(source, emitted) == []


def test_theatre_speeches_render_with_speaker_stage_and_verse_lines_separated(theatre_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not theatre_export.latei_pdf_success:
        log = theatre_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Theatre sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(theatre_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    lines = [line.strip() for line in process.stdout.splitlines()]

    assert "Maguelonne" in lines
    assert "(riant)" in lines
    assert any("Monsieur, vous m" in line for line in lines)
    assert "Le Roi" in lines
    assert "(riant aussi)" in lines
    assert any("Oui, j" in line for line in lines)
    assert any("C" in line and "est vrai, je suis un monstre" in line for line in lines)
