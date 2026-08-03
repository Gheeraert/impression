from __future__ import annotations

"""Frontières inline et appels de note (référentiel PURH v0.5, "Espaces et
jonctions" / "Frontières inline et appels de note") : l'audit décrit des
formes comme "LouisXIV" et "FrançoisIer" (espace insécable perdue devant un
<hi>) et des espaces parasites avant certains appels de note, et demande des
fixtures minimales ciblées : Louis XIV, François Ier, un mot suivi
immédiatement d'une note, italique suivi de ponctuation, petite capitale
suivie d'un exposant, combinaisons de rendus.

Investigation (2026-08-03) : aucun de ces cas ne reproduit avec le code
actuel — texte et tail sont déjà traités comme des données pures par
tei_reader.py (aucun strip/normalisation), préservant espaces ordinaires et
insécables aux frontières hi/sup/note. Vraisemblablement déjà corrigé par
des travaux antérieurs à cette session (cf. "Corrige les points
structurants" / "Corrige trois défauts réels révélés par un vrai livre
Métopes multi-chapitres" dans l'historique). Ce fichier verrouille le
comportement correct par des tests, comme demandé par le référentiel,
plutôt que d'appliquer un correctif à un défaut non reproduit."""

import shutil
from pathlib import Path

import pytest
from lxml import etree

from purh_site.reversible import compare_tei_elements, read_latex_document, write_tei_element
from purh_site.reversible_integration import run_reversible_export_for_file

_NBSP = "\xa0"

# Patterns below are drawn from real markup in
# tests/fixtures/metopes/heraldique_ii.book.normalized.xml (e.g. "Jules XIII",
# "début XVIIe siècle", "...Merito</hi><note>...") — not the whole book, just
# the boundary shapes it actually contains.
_INLINE_BOUNDARIES_XML = f"""<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Frontieres Test</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="article" data-page-title="Article frontieres" xml:id="a1">
        <front><div type="titlePage"><p rend="title-main">Article frontieres</p></div></front>
        <body>
          <div>
            <p xml:id="p-louis">Louis{_NBSP}<hi rend="small-caps">XIV</hi> et François{_NBSP}<hi rend="sup">Ier</hi> regnaient.</p>
            <p xml:id="p-note">Il cite <hi rend="italic">Merito</hi><note><p>Contenu de la note.</p></note> ensuite.</p>
            <p xml:id="p-punct"><hi rend="italic">italique</hi>, suivi de ponctuation.</p>
            <p xml:id="p-combo">début <hi rend="small-caps">xvii</hi><hi rend="sup">e</hi>{_NBSP}siècle.</p>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def boundaries_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_inline_boundaries")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_INLINE_BOUNDARIES_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_nbsp_survives_before_small_caps_and_sup(boundaries_export) -> None:
    body = boundaries_export.latei_body_path.read_text(encoding="utf-8")

    assert f"Louis{_NBSP}\\teiHi[rend={{small-caps}}]{{XIV}}" in body
    assert f"François{_NBSP}\\teiHi[rend={{sup}}]{{Ier}}" in body


def test_no_space_introduced_between_word_and_immediate_note(boundaries_export) -> None:
    body = boundaries_export.latei_body_path.read_text(encoding="utf-8")

    assert r"\teiHi[rend={italic}]{Merito}\teiNote{" in body


def test_punctuation_stays_glued_to_closing_italic(boundaries_export) -> None:
    body = boundaries_export.latei_body_path.read_text(encoding="utf-8")

    assert r"\teiHi[rend={italic}]{italique}, suivi de ponctuation." in body


def test_small_caps_immediately_followed_by_sup_no_space(boundaries_export) -> None:
    body = boundaries_export.latei_body_path.read_text(encoding="utf-8")

    assert r"\teiHi[rend={small-caps}]{xvii}\teiHi[rend={sup}]{e}" in body


def test_inline_boundaries_round_trip_without_diagnostics(boundaries_export) -> None:
    assert boundaries_export.success is True
    assert boundaries_export.diagnostics_count == 0

    body = boundaries_export.latei_body_path.read_text(encoding="utf-8")
    emitted = write_tei_element(read_latex_document(body))
    source = etree.parse(str(boundaries_export.source_path)).getroot()
    assert compare_tei_elements(source, emitted) == []


def test_inline_boundaries_render_with_correct_spacing_in_pdf(boundaries_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not boundaries_export.latei_pdf_success:
        log = boundaries_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Inline-boundaries sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(boundaries_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    text = " ".join(process.stdout.split())

    assert "Louis XIV et" in text, text
    assert "LouisXIV" not in text
    assert "et François Ier regnaient" in text, text
    assert "début xviie siècle" in text, text
