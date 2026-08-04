from __future__ import annotations

"""Référentiel PURH v0.6 §6.2 (P1 item 6) : « le bandeau généré est situé
environ 3,1 mm plus bas que dans le PDF imprimeur ». Statut : « correction
mineure mais mesurable ».

\\topmargin remonte le bandeau de titre courant de 3,1 mm ; \\headsep
compense d'autant pour que le corps de texte démarre à la même position
qu'avant ce correctif — la marge du haut mesurée sur le maître InDesign
(profile.margin_top_mm) n'est pas remise en cause, seul un écart de rendu
propre au bandeau est corrigé."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_TWO_PAGE_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <group type="book">
      <group type="article" data-page-title="Article Un" xml:id="a1">
        <front><div type="titlePage"><p rend="title-main">Titre</p></div></front>
        <body><div>
          <p>Un texte de corps assez long pour remplir entierement une page et forcer un saut vers une deuxieme page normale avec titre courant visible en haut, afin de verifier que le bandeau y est correctement positionne.</p>
          <p>Deuxieme paragraphe pour continuer a remplir suffisamment la page afin d'obtenir un saut de page automatique et disposer d'une page suivante complete de corps de texte ordinaire.</p>
          <p>Troisieme paragraphe de remplissage pour etre bien certain de depasser une pleine page de corps de texte et forcer ainsi un veritable saut de page physique dans le PDF genere pour ce test.</p>
        </div></body>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def two_page_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_running_title_offset")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_TWO_PAGE_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_topmargin_and_headsep_are_adjusted_by_3_1mm() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\addtolength{{\topmargin}}{{-3.1mm}}" in preamble_source
    assert r"\addtolength{{\headsep}}{{3.1mm}}" in preamble_source


def test_adjustment_is_registered_after_geometry_so_it_is_not_overwritten() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    geometry_pos = preamble_source.index(r"]{{geometry}}")
    topmargin_pos = preamble_source.index(r"\addtolength{{\topmargin}}")
    assert topmargin_pos > geometry_pos


def test_compiles_with_the_adjusted_header_position(two_page_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not two_page_export.latei_pdf_success:
        log = two_page_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Two-page sample did not compile.\n{log[:4000]}")

    assert two_page_export.latei_pdf_path.exists()
    assert two_page_export.latei_pdf_path.stat().st_size > 0
