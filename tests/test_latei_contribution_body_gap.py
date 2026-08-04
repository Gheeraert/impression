from __future__ import annotations

"""Référentiel PURH v0.6 §7.2 (P1, complément du 2026-08-04) : vérification
humaine directe du PDF généré face au PDF imprimeur — celui-ci montre un
grand espace vertical (estimé à 5-6 lignes de titre) entre le bloc de titre
d'ouverture (titre, sous-titre, auteur/affiliation) et le début du corps du
chapitre/article ; le généré n'en montrait aucun."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_OPENING_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <group type="book">
      <group type="article" data-page-title="Article Un" xml:id="a1">
        <front><div type="titlePage"><p rend="title-main">Titre Article</p></div></front>
        <body><div><p>PREMIERELIGNEDUCORPS.</p></div></body>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def opening_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_contribution_body_gap")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_OPENING_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_body_gap_macro_is_defined_and_substantial() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert r"\newcommand{\PURHContributionBodyGap}{\vspace{105pt}}" in macros


def test_titlepage_div_inserts_the_body_gap_before_closing() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    titlepage_branch = macros.split(r"\IfSubStr{#1}{type={titlePage}}{")[1].split(r"}{%")[0]

    assert r"\PURHContributionBodyGap" in titlepage_branch
    # The gap must come after the title-page content (#2), not before it.
    assert titlepage_branch.index("#2") < titlepage_branch.index(r"\PURHContributionBodyGap")


def test_opening_compiles_with_the_gap_before_body(opening_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not opening_export.latei_pdf_success:
        log = opening_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Contribution opening sample did not compile.\n{log[:4000]}")

    assert opening_export.latei_pdf_path.exists()
    assert opening_export.latei_pdf_path.stat().st_size > 0
