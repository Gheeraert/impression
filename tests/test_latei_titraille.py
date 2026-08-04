from __future__ import annotations

"""Titraille (référentiel PURH v0.5, §2.5/§5.3): part and contribution
titles observed in Josefin Sans Thin, 16 pt, capitals, centered; subtitle
Thin Italic 12 pt; section titles Thin 12 pt, capitals. The pre-existing
code used Chaparral Pro / Josefin Bold at ~24.8 pt in lowercase instead."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_TITRAILLE_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Livre Titraille</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="section1">
        <head>Titre de partie</head>
        <group type="article" data-page-title="Titre article" xml:id="a1">
          <front>
            <div type="titlePage">
              <p rend="title-main">Titre article</p>
              <p rend="author-aut">Prenom Nom</p>
            </div>
          </front>
          <body>
            <div type="section1"><head>Titre de section</head><p>Corps de section.</p></div>
          </body>
        </group>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def titraille_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_titraille")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_TITRAILLE_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_preamble_declares_a_dedicated_thin_titling_family() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\newfontfamily\PURHTitreFont{{Josefin Sans Thin}}" in preamble_source


def test_part_titleformat_is_16pt_uppercase_centered() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\titleformat{{\part}}[display]" in preamble_source
    assert r"\PURHTitreFont\fontsize{{16pt}}{{19pt}}\selectfont\centering" in preamble_source


def test_section_titleformat_is_12pt_uppercase() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\PURHTitreFont\fontsize{{12pt}}{{14pt}}\selectfont\raggedright" in preamble_source


def test_contribution_title_and_subtitle_macros_use_thin_family() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert r"\PURHTitreFont\fontsize{16pt}{19pt}\selectfont\centering\MakeUppercase{#1}" in macros
    assert r"\PURHTitreFont\fontsize{12pt}{14pt}\selectfont\itshape\centering #1" in macros


def test_titraille_renders_uppercase_part_article_and_section_titles(titraille_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not titraille_export.latei_pdf_success:
        log = titraille_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Titraille sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(titraille_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    assert "TITRE DE PARTIE" in text
    assert "TITRE ARTICLE" in text
    assert "TITRE DE SECTION" in text
    # Auteur et affiliation ne sont plus imprimés sur l'ouverture de
    # contribution (référentiel PURH v0.6 §7.2/§17 P1 item 3, profil de
    # production par défaut) — voir test_latei_opening_templates.py pour la
    # vérification dédiée (métadonnées conservées dans le corps réversible,
    # affichage seulement désactivé).
    assert "Prenom Nom" not in text
    assert "PRENOM NOM" not in text
    # Running-title headers stay in original case (a different, non-titling
    # rendering path — see test_latei_running_titles_verso_recto.py).
    assert "Titre de partie" in text
    assert "Titre article" in text
