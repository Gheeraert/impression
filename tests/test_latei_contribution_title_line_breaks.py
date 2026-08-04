from __future__ import annotations

"""Référentiel PURH v0.5/v0.6 §7.3 ("coupures éditoriales", P1 item 4,
exécuté le 2026-08-04 sur demande explicite : « reproduire les règles de
coupure du PDF imprimeur, qui sont sans doute implicites »).

Vérification empirique sur le PDF imprimeur réel de *Dissimuler pour mieux
régner* (7 titres de chapitre/article rendus en PNG et inspectés
visuellement, pas seulement extraits en texte brut — pdftotext sans
-layout fusionne parfois plusieurs lignes visuelles réelles en une seule
ligne de texte extrait, piège rencontré puis corrigé pendant cette
investigation) : le référentiel avertit qu'il ne faut pas reconstruire ces
coupures « par une largeur de boîte arbitraire », mais la largeur mesurée
n'est PAS arbitraire ici — elle correspond à la largeur d'empagement du
profil 155×230 (105 mm), calibrée à 104 mm par comparaison directe avec la
police réellement utilisée (Josefin Sans Bold, réellement installée, pas
une graisse synthétique). \\lateiContributionTitle rend donc son texte dans
un \\parbox de cette largeur, laissant l'algorithme de coupure de ligne
standard de LaTeX (Knuth-Plass) faire le travail — au lieu, par exemple,
d'un mécanisme de coupures manuelles par titre, qui aurait nécessité une
nouvelle convention de source non demandée ici.

Résultat : correspondance exacte du nombre de lignes ET du contenu de
chaque ligne pour la plupart des titres testés ; sur certains titres, un
mot court ("à", "de") atterrit sur la ligne précédente plutôt que suivante
par rapport au PDF imprimeur — écart d'un mot, probablement dû à une règle
InDesign de conservation des mots courts que LaTeX ne reproduit pas
nativement. Documenté comme limite connue, pas silencieusement corrigé."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_CALIBRATION_TITLES = {
    "a_short": "Un secret de polichinelle",
    "a_short2": "Spectacle et dissimulation",
    "a_short3": "La politique dans le caveau",
    "a_wraps2": "Les espaces du secret à Clarens",
    "a_wraps2b": "Un cabinet de toilette bien politique",
    "a_wraps4": "Les lieux de la conjuration : société secrète et hétérotopie dans la littérature romantique",
}

_CALIBRATION_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <group type="book">
      {articles}
    </group>
  </text>
</TEI>"""

_ARTICLE_TEMPLATE = """
      <group type="article" data-page-title="{key}" xml:id="{key}">
        <front><div type="titlePage"><p rend="title-main">{title}</p></div></front>
        <body><div><p>Corps.</p></div></body>
      </group>"""


@pytest.fixture(scope="module")
def calibration_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_title_line_breaks")
    xml_path = tmp_path / "book.xml"
    articles = "".join(
        _ARTICLE_TEMPLATE.format(key=key, title=title) for key, title in _CALIBRATION_TITLES.items()
    )
    xml_path.write_text(_CALIBRATION_XML.format(articles=articles), encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_contribution_title_is_rendered_in_a_narrower_parbox() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert r"\newcommand{\PURHContributionTitleWidth}{104mm}" in macros
    title_macro = macros.split(r"\newcommand{\lateiContributionTitle}[1]{")[1].split(
        r"\newcommand{\lateiContributionSubtitle}"
    )[0]
    assert r"\parbox{\PURHContributionTitleWidth}" in title_macro


def test_short_titles_stay_on_a_single_line(calibration_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not calibration_export.latei_pdf_success:
        log = calibration_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Calibration sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(calibration_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    # Confirmed on the real Dissimuler printer PDF: these titles are short
    # enough to stay on one line — must not be artificially split.
    assert "UN SECRET DE POLICHINELLE" in text
    assert "SPECTACLE ET DISSIMULATION" in text
    assert "LA POLITIQUE DANS LE CAVEAU" in text


def test_long_title_wraps_exactly_like_the_printer_pdf(calibration_export) -> None:
    """Cas de correspondance exacte (nombre de lignes ET contenu) avec le
    PDF imprimeur, vérifié par rendu PNG sur la vraie page 37 de
    *Dissimuler pour mieux régner*."""
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not calibration_export.latei_pdf_success:
        log = calibration_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Calibration sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(calibration_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    lines = [line.strip() for line in process.stdout.splitlines()]

    assert "LES LIEUX DE LA CONJURATION :" in lines
    assert "SOCIÉTÉ SECRÈTE ET HÉTÉROTOPIE" in lines
    assert "DANS LA LITTÉRATURE" in lines
    assert "ROMANTIQUE" in lines


def test_medium_titles_wrap_onto_two_lines_instead_of_overflowing(calibration_export) -> None:
    """Écart connu d'un mot par rapport au PDF imprimeur (voir docstring du
    module) : on ne vérifie ici que l'absence du défaut initial (titre sur
    une seule ligne débordante), pas la coupure exacte mot pour mot."""
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not calibration_export.latei_pdf_success:
        log = calibration_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Calibration sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(calibration_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    assert "LES ESPACES DU SECRET À CLARENS" not in text
    assert "CLARENS" in text
    assert "UN CABINET DE TOILETTE BIEN POLITIQUE" not in text
    assert "POLITIQUE" in text
