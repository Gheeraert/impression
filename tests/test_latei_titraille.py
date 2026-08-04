from __future__ import annotations

"""Titraille (référentiel PURH v0.5, §2.5/§5.3): part and contribution
titles, 16 pt, capitals, centered; subtitle Thin Italic 12 pt; section
titles Thin 12 pt, capitals. The pre-existing code used Chaparral Pro /
Josefin Bold at ~24.8 pt in lowercase instead.

Part/contribution titles were first corrected to Josefin Sans Thin
(référentiel §2.5/§5.3/§4.3), then re-corrected to Josefin Sans BOLD after
direct human verification of a generated PDF against the printer PDF: part
titles there are black and bold, not thin and grayish — the référentiel's
own claim of "Thin" for this specific level was contradicted by that live
observation and is no longer followed (chantier de parité v0.6, 2026-08-04).
Section-level titles (12 pt) were not flagged and stay Thin."""

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


def test_part_titleformat_is_16pt_bold_uppercase_centered() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\titleformat{{\part}}[display]" in preamble_source
    assert r"\PURHTitleFont\bfseries\fontsize{{16pt}}{{19pt}}\selectfont\centering" in preamble_source


def test_chapter_titleformat_is_16pt_bold() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\titleformat{{\chapter}}[display]" in preamble_source
    assert r"\PURHTitleFont\bfseries\fontsize{{16pt}}{{19pt}}\selectfont\raggedright" in preamble_source


def test_section_titleformat_is_12pt_uppercase() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\PURHTitreFont\fontsize{{12pt}}{{14pt}}\selectfont\raggedright" in preamble_source


def test_contribution_title_is_bold_and_subtitle_stays_thin() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert r"\PURHTitleFont\bfseries\fontsize{16pt}{19pt}\selectfont\centering\MakeUppercase{#1}" in macros
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


def test_part_and_contribution_titles_embed_a_bold_font(titraille_export) -> None:
    """pdffonts confirms \\titleformat{\\part} / \\lateiContributionTitle
    actually select a bold face — a plain \\PURHTitreFont (Thin-only family)
    could silently render the same text without ever engaging a bold shape,
    which pdftotext alone cannot detect (it has no notion of font weight)."""
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not titraille_export.latei_pdf_success:
        log = titraille_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Titraille sample did not compile.\n{log[:4000]}")
    if shutil.which("pdffonts") is None:
        pytest.skip("pdffonts is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdffonts"), str(titraille_export.latei_pdf_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    fonts_output = process.stdout

    bold_present = any(token in fonts_output for token in ("Bold", "bold", "-Bd", "-Bol"))
    assert bold_present, (
        "No bold font found in PDF — part/contribution titles likely still rendered "
        f"with the Thin family.\npdffonts output:\n{fonts_output}"
    )
