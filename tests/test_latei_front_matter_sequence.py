from __future__ import annotations

"""Séquence complète des liminaires (référentiel PURH v0.6 §8.1, P0 item 3) :
2 pages blanches, faux-titre, crédits, page de titre, page blanche, puis
l'introduction — bâtie uniquement depuis les métadonnées du livre, jamais
depuis le contenu LaTEI réversible (IMPORTANT signalé par l'utilisateur :
préserver absolument la réversibilité)."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_FULL_METADATA_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type="main">Titre du livre</title>
        <title type="sub">Un sous-titre</title>
        <author role="pbd"><persName><forename>Prenom</forename><surname>Nom</surname></persName></author>
      </titleStmt>
      <publicationStmt>
        <publisher>PURH</publisher>
        <pubPlace>Mont-Saint-Aignan</pubPlace>
        <date type="publishing" when="2026">2026</date>
        <ab type="book"><idno type="ISBN-13">979-10-240-0000-0</idno></ab>
        <idno type="DOI">10.4000/books.purh.0000</idno>
      </publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="introduction" data-page-title="Introduction" xml:id="intro">
        <front><div type="titlePage"><p rend="title-main">Introduction</p></div></front>
        <body><div><p>Corps de introduction.</p></div></body>
      </group>
    </group>
  </text>
</TEI>"""

_MINIMAL_METADATA_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title type="main">Livre minimal</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="introduction" data-page-title="Introduction" xml:id="intro">
        <front><div type="titlePage"><p rend="title-main">Introduction</p></div></front>
        <body><div><p>Corps.</p></div></body>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def full_metadata_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_front_matter_full")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_FULL_METADATA_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


@pytest.fixture(scope="module")
def minimal_metadata_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_front_matter_minimal")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_MINIMAL_METADATA_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_front_matter_sequence_macros_are_defined_generically() -> None:
    """No book-specific value in the general macros (référentiel/consigne :
    "ne code aucune valeur propre au titre [d'un livre] dans les macros
    générales") — everything comes from a metadata argument."""
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")

    assert r"\newcommand{{\PURHBlankPage}}" in preamble_source
    assert r"\newcommand{{\PURHFalseTitle}}[1]" in preamble_source
    assert r"\newcommand{{\PURHCreditsPage}}[1]" in preamble_source
    assert r"\newcommand{{\PURHTitlePage}}[1]" in preamble_source
    assert "Dissimuler" not in preamble_source
    assert "Beaut" not in preamble_source


def test_reversible_body_is_untouched_by_front_matter(full_metadata_export) -> None:
    """IMPORTANT signalé par l'utilisateur : le LaTEI réversible ne doit
    porter aucune trace des liminaires (page blanche, faux-titre, crédits,
    page de titre sont hors du corps réversible, générés séparément)."""
    body = full_metadata_export.latei_body_path.read_text(encoding="utf-8")

    for macro in (r"\PURHBlankPage", r"\PURHFalseTitle", r"\PURHCreditsPage", r"\PURHTitlePage"):
        assert macro not in body


def test_introduction_lands_on_page_7(full_metadata_export) -> None:
    assert full_metadata_export.latei_pdf_success is True, full_metadata_export.latei_pdf_message

    toc_path = full_metadata_export.latei_pdf_path.with_suffix(".toc")
    assert toc_path.exists()
    toc = toc_path.read_text(encoding="utf-8", errors="replace")
    assert r"\contentsline {chapter}{Introduction}{7}{" in toc


def test_physical_page_count_matches_six_front_matter_pages_plus_content(full_metadata_export) -> None:
    if shutil.which("pdfinfo") is None:
        pytest.skip("pdfinfo is unavailable.")
    import subprocess

    process = subprocess.run(
        [shutil.which("pdfinfo"), str(full_metadata_export.latei_pdf_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    pages_line = next(line for line in process.stdout.splitlines() if line.startswith("Pages:"))
    pages = int(pages_line.split(":", 1)[1].strip())
    # 6 front-matter pages (1-6) + introduction starting page 7: at least 7.
    assert pages >= 7


def test_credits_page_shows_only_available_metadata(full_metadata_export, minimal_metadata_export) -> None:
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")
    import subprocess

    def render(pdf_path):
        process = subprocess.run(
            [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert process.returncode == 0, process.stderr
        return process.stdout

    # Colophon (référentiel PURH v0.6 §8.1, 2026-08-04) : année et ISBN
    # viennent du XML ; adresse et URL sont des mentions institutionnelles
    # PURH fixes, toujours présentes. DOI n'y figure plus (jamais demandé
    # pour ce contenu précis) — voir test_latei_colophon.py pour la
    # vérification dédiée des lignes couverture/suivi éditorial, fournies
    # par le GUI et absentes de tout XML.
    full_text = render(full_metadata_export.latei_pdf_path)
    assert "2026" in full_text
    assert "979-10-240-0000-0" in full_text
    assert "purh.univ-rouen.fr" in full_text

    # No source data at all beyond the title: no fabricated boilerplate
    # (no invented "Tous droits réservés" or similar), but the fixed
    # institutional address/URL still appear (not book-specific data).
    minimal_text = render(minimal_metadata_export.latei_pdf_path)
    assert "979-10-240-0000-0" not in minimal_text
    assert "©" not in minimal_text
    assert "Tous droits" not in minimal_text
    assert "purh.univ-rouen.fr" in minimal_text
