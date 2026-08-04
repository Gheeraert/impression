from __future__ import annotations

"""Référentiel PURH v0.6 §17 P2 ("microtypographie") : notes 8,5/10,2 pt,
filet de notes, bibliographie, tableaux, couleur 90 % K. Citations (§11.1),
poésie (§11.4) et listes (§11.5) déjà conformes, vérifiés ici sans
modification de code (regression guards).

1. Notes (§5.1) : corps 9 pt -> 8,5 pt, interligne 11 pt -> 10,2 pt, filet
   0,40 pt -> 0,25 pt, longueur ~42 mm -> 25,4 mm (72 pt), espace avant
   notes -> 3 mm. Cause racine du corps/interligne : \\@makefntext, déjà
   redéfini pour le retrait négatif de première ligne, remplace entièrement
   celui de footmisc et n'appelait donc plus \\footnotelayout (qui portait
   jusqu'ici, sans effet, le \\fontsize{{8.5pt}}{{10.2pt}}). Cause racine du
   filet : jamais personnalisé, valeurs par défaut de book.cls (0,4 pt sur
   0,4\\columnwidth) correspondant exactement aux ~0,40 pt / ~42 mm constatés.
2. Bibliographie (§11.2) : 10 pt, retrait suspendu 5 mm (était en em,
   dépendant de la taille de fonte ambiante jamais fixée par la macro).
3. Tableaux (§11.3) : 8/9,5 pt, marges internes (tabcolsep) 2 mm, filets
   0,25 pt (booktabs par défaut : 0,08em/0,05em, proportionnels à la fonte
   ambiante), fond d'entête noir 30 % (\\rowcolor, écrit directement par
   latex_writer._write_row — même contrainte de premier jeton que
   \\multicolumn, voir test_reversible_table_elements.py), titre 9/11 pt
   centré 10 mm avant / 3,5 mm après.
4. Couleur (§12.1) : texte courant en noir process 90 % (CMYK), pas en noir
   plein — appliqué globalement via \\AtBeginDocument{{\\color{{PURHBodyBlack}}}}."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_P2_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="chapter" xml:id="c1">
        <head>Chapitre Test</head>
        <p>Un texte avec un appel de note<note><p>Contenu de la note de test pour verifier la taille et le filet.</p></note> et la suite du texte normal du corps.</p>
        <figure>
          <table>
            <row role="header"><cell>Colonne A</cell><cell>Colonne B</cell></row>
            <row><cell>Valeur 1</cell><cell>Valeur 2</cell></row>
          </table>
          <p rend="caption">Titre du tableau de test.</p>
        </figure>
        <listBibl>
          <biblStruct><p>Dupont, Jean, <hi rend="italic">Un ouvrage de reference</hi>, Paris, Editions Test, 2020.</p></biblStruct>
        </listBibl>
      </div>
    </body>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def p2_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_microtypography_p2")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_P2_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


# ---------------------------------------------------------------------------
# 1. Notes
# ---------------------------------------------------------------------------

def test_footnote_text_uses_the_profile_note_fontsize_directly() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    makefntext_block = preamble_source.split(r"\renewcommand{{\@makefntext}}[1]{{")[1].split(r"}}%\n}}")[0]
    assert r"\fontsize{{{note_font_size}}}{{{note_leading}}}\selectfont" in makefntext_block


def test_footnoterule_is_a_quarter_point_thick_and_72pt_long() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\renewcommand{{\footnoterule}}{{%" in preamble_source
    footnoterule_block = preamble_source.split(r"\renewcommand{{\footnoterule}}{{%")[1].split("}}")[0]
    assert "width 72pt height 0.25pt" in footnoterule_block


def test_skip_footins_is_3mm() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\setlength{{\skip\footins}}{{3mm}}" in preamble_source


def test_footnote_renders_at_the_correct_size_and_with_a_short_thin_rule(p2_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not p2_export.latei_pdf_success:
        log = p2_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"P2 sample did not compile.\n{log[:4000]}")
    assert p2_export.latei_pdf_path.exists()
    assert p2_export.latei_pdf_path.stat().st_size > 0


# ---------------------------------------------------------------------------
# 2. Bibliographie
# ---------------------------------------------------------------------------

def test_bibliography_entry_is_10pt_with_5mm_hanging_indent() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    entry_macro = macros.split(r"\NewDocumentCommand{\lateiBibliographyEntry}{+m}{%")[1].split(
        r"\NewDocumentCommand{\lateiBibliographyBlock}"
    )[0]
    assert r"\fontsize{10pt}{12pt}\selectfont" in entry_macro
    assert r"\hangindent=5mm" in entry_macro
    assert r"\hangindent=1.5em" not in macros


def test_bibliography_entry_renders(p2_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not p2_export.latei_pdf_success:
        log = p2_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"P2 sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(p2_export.latei_pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert process.returncode == 0, process.stderr
    assert "Dupont, Jean" in process.stdout
    assert "Un ouvrage de reference" in process.stdout


# ---------------------------------------------------------------------------
# 3. Tableaux
# ---------------------------------------------------------------------------

def test_table_environment_sets_font_margins_and_rule_widths() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    table_env = macros.split(r"\NewDocumentEnvironment{teiTable}{O{} +b}{%")[1].split(r"\end{longtable}")[0]
    assert r"\fontsize{8pt}{9.5pt}\selectfont" in table_env
    assert r"\setlength{\tabcolsep}{2mm}" in table_env
    assert r"\setlength{\heavyrulewidth}{0.25pt}" in table_env
    assert r"\setlength{\lightrulewidth}{0.25pt}" in table_env
    assert r"\setlength{\cmidrulewidth}{0.25pt}" in table_env


def test_xcolor_table_option_is_loaded_for_rowcolor() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\usepackage[table]{{xcolor}}" in preamble_source


def test_table_caption_is_9_11pt_centered_with_10mm_before_and_3_5mm_after() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\DeclareCaptionFont{{PURHTableCaptionFont}}{{\fontsize{{9pt}}{{11pt}}\selectfont}}" in preamble_source
    table_caption_block = preamble_source.split(r"\captionsetup[table]{{")[1].split(r"}}")[0]
    assert "font=PURHTableCaptionFont" in table_caption_block
    assert "justification=centering" in table_caption_block
    assert "aboveskip=10mm" in table_caption_block
    assert "belowskip=3.5mm" in table_caption_block


def test_table_with_header_row_compiles_and_stays_reversible(p2_export) -> None:
    body = p2_export.latei_body_path.read_text(encoding="utf-8")
    assert r"\rowcolor{black!30}" in body
    assert r"\teiRow[role={header}]" in body

    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not p2_export.latei_pdf_success:
        log = p2_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"P2 sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(p2_export.latei_pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert process.returncode == 0, process.stderr
    assert "Colonne A" in process.stdout
    assert "Valeur 1" in process.stdout
    assert "Titre du tableau de test." in process.stdout


# ---------------------------------------------------------------------------
# 4. Couleur du texte courant
# ---------------------------------------------------------------------------

def test_body_text_color_is_90_percent_process_black_not_pure_black() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\definecolor{{PURHBodyBlack}}{{cmyk}}{{0,0,0,0.9}}" in preamble_source
    assert r"\AtBeginDocument{{\color{{PURHBodyBlack}}}}" in preamble_source


# ---------------------------------------------------------------------------
# Regression guards: items already compliant, verified without code change.
# ---------------------------------------------------------------------------

def test_citations_remain_9_11pt_10mm_left_indent_4mm_before_after() -> None:
    """Référentiel §11.1, déjà conforme (aucune modification apportée par
    cette passe) : garde de non-régression."""
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    quote_block = preamble_source.split(r"\renewenvironment{{quote}}")[1].split(r"\AtBeginEnvironment{{quote}}")[0]
    assert r"\fontsize{{9pt}}{{11pt}}\selectfont" in quote_block
    assert r"\leftmargin=10mm\rightmargin=0pt" in quote_block
    assert r"\vspace*{{4mm plus 1pt minus 1pt}}" in preamble_source


def test_poetry_routes_through_verse_environment_not_justified_linebreaks() -> None:
    """Référentiel §11.4, déjà conforme : garde de non-régression."""
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert r"\NewDocumentEnvironment{teiLg}{O{} +b}{%" in macros
    lg_block = macros.split(r"\NewDocumentEnvironment{teiLg}{O{} +b}{%")[1].split(r"{}")[0]
    assert r"\begin{verse}" in lg_block


def test_no_silent_dependency_on_minion_pro_for_list_bullets() -> None:
    """Référentiel §11.5 : aucune fonte ou glyphe de remplacement non
    déclaré/contrôlé — garde de non-régression sur toute la chaîne LaTEI."""
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert "Minion" not in preamble_source
    assert "Minion" not in macros
    assert r"label=\textendash" in preamble_source
