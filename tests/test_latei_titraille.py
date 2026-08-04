from __future__ import annotations

"""Titraille (référentiel PURH v0.5, §2.5/§5.3): part and contribution
titles, 16 pt, capitals, centered; subtitle 12 pt italic; section titles
12 pt, capitals. The pre-existing code used Chaparral Pro / Josefin Bold at
~24.8 pt in lowercase instead.

Part/contribution titles were first corrected to Josefin Sans Thin
(référentiel §2.5/§5.3/§4.3), then re-corrected to Josefin Sans BOLD after
direct human verification of a generated PDF against the printer PDF: part
titles there are black and bold, not thin and grayish — the référentiel's
own claim of "Thin" for this specific level was contradicted by that live
observation and is no longer followed (chantier de parité v0.6, 2026-08-04).

The same 2026-08-04 verification extended the correction to every
intertitre level (section/subsection/subsubsection, i.e. the headings
*inside* a chapter/article body, distinct from the chapter/article's own
opening title) — also black and bold in the printer PDF, contradicting an
earlier, narrower fix that had deliberately kept subsection/subsubsection
in the Thin family.

The running-title header (\\PURHHeaderFont) went through two rounds on the
same day: first reported too light gray (Thin family swapped for the
regular Josefin Sans weight), then reported too dark/visually bold with
that same swap (the printer PDF has "no weight" at all on this level) —
settled by reverting to the Thin family and applying an explicit gray
\\color instead of changing family, since weight and color are two
different levers and only color was ever the actual target here.

A second, separate round of feedback the same day also corrected the
contribution subtitle (référentiel §5.3's "Thin Italic" was contradicted:
the printer PDF shows Bold Italic lowercase for this level)."""

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


def test_section_titleformat_is_12pt_bold_uppercase() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\PURHTitleFont\bfseries\fontsize{{12pt}}{{14pt}}\selectfont\raggedright" in preamble_source


def test_subsection_and_subsubsection_titleformat_are_bold() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    subsection_block = preamble_source.split(r"\titleformat{{\subsection}}[block]")[1].split(
        r"\titleformat{{\subsubsection}}[block]"
    )[0]
    subsubsection_block = preamble_source.split(r"\titleformat{{\subsubsection}}[block]")[1].split(
        r"\titlespacing*"
    )[0]

    assert r"\PURHTitleFont\bfseries\large\raggedright" in subsection_block
    assert r"\PURHTitleFont\bfseries\normalsize\raggedright" in subsubsection_block


def test_running_title_header_uses_thin_family_with_explicit_color() -> None:
    """Trois vérifications humaines successives (2026-08-04) : la première
    jugeait le gris trop clair (Thin -> famille standard, sans succès) ; la
    seconde a trouvé ce résultat trop noir et visuellement gras — retour à
    la famille Thin (« pas de graisse » sur le PDF imprimeur) ; la
    troisième a trouvé le gris qui en résultait encore trop clair — passé au
    système noir X % (CMJN) à 50 %, voir test_latei_colophon.py."""
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    # xcolor (pas le simple package color) depuis la passe P2 tableaux —
    # nécessaire pour \rowcolor sur les lignes d'entête.
    assert r"\usepackage[table]{{xcolor}}" in preamble_source
    assert r"\newcommand{{\PURHHeaderFont}}{{\PURHTitreFont\small\color[cmyk]{{0,0,0,0.5}}}}" in preamble_source
    assert r"\PURHTitleFont" not in preamble_source.split(r"\newcommand{{\PURHHeaderFont}}")[1].split("\n")[0]


def test_contribution_title_and_subtitle_are_both_bold() -> None:
    """Le sous-titre était resté Thin Italic (référentiel §5.3), corrigé en
    Bold Italic bas de casse le 2026-08-04 après vérification humaine
    directe montrant explicitement gras + italique sur le PDF imprimeur."""
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert r"\PURHTitleFont\bfseries\fontsize{16pt}{19pt}\selectfont\centering\MakeUppercase{#1}" in macros
    assert r"\PURHTitleFont\bfseries\fontsize{12pt}{14pt}\selectfont\itshape\centering #1" in macros


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
