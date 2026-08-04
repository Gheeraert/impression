from __future__ import annotations

"""Verify that latei_preamble is independent of the legacy stable-PDF chain."""

import importlib
import sys


def _import_fresh(module_name: str):
    """Import a module in a subprocess-style isolation by temporarily removing it."""
    for key in list(sys.modules.keys()):
        if key == module_name or key.startswith(module_name + "."):
            del sys.modules[key]
    return importlib.import_module(module_name)


def _import_lines(module_name: str) -> list[str]:
    mod = sys.modules[module_name]
    with open(mod.__file__, encoding="utf-8") as f:
        return [line for line in f if line.startswith("import ") or line.startswith("from ")]


def test_latei_preamble_imports_without_latex_renderer() -> None:
    for line in _import_lines("purh_site.latei_preamble"):
        assert "latex_renderer" not in line, f"Unexpected import: {line!r}"
        assert "LatexRenderer" not in line, f"Unexpected import: {line!r}"


def test_latei_preamble_imports_without_semantic_model() -> None:
    for line in _import_lines("purh_site.latei_preamble"):
        assert "semantic_model" not in line, f"Unexpected import: {line!r}"
        assert "pdf_builder" not in line, f"Unexpected import: {line!r}"
        assert "tei_to_model" not in line, f"Unexpected import: {line!r}"


def test_latei_driver_does_not_import_latex_renderer() -> None:
    import purh_site.latei_driver as driver_mod
    source_file = driver_mod.__file__ or ""
    with open(source_file, encoding="utf-8") as f:
        source = f.read()
    assert "latex_renderer" not in source
    assert "LatexRenderer" not in source


def test_purh_preamble_data_defaults() -> None:
    from purh_site.latei_preamble import PurhPreambleData
    data = PurhPreambleData()
    assert data.title == "LaTEI PURH"
    assert data.subtitle == ""
    assert data.authors == ()
    assert "Rouen" in data.publisher
    assert data.year == ""
    assert data.doi == ""
    assert data.isbn == ""


def test_render_purh_latex_preamble_contains_essential_elements() -> None:
    from purh_site.latei_preamble import PurhPreambleData, render_purh_latex_preamble
    data = PurhPreambleData(
        title="Héraldique et papauté",
        subtitle="Moyen Âge",
        authors=("Jean Dupont", "Marie Martin"),
        publisher="PURH",
        year="2024",
        doi="10.1234/test",
        isbn="979-10-240-1855-3",
    )
    preamble = render_purh_latex_preamble(data)

    assert r"\documentclass[11pt,twoside,openany]{book}" in preamble
    assert r"\usepackage[french]{babel}" in preamble
    assert "]{geometry}" in preamble
    assert r"\usepackage{fancyhdr}" in preamble
    assert "]{titlesec}" in preamble
    assert "]{hyperref}" in preamble
    assert r"\newenvironment{PurhBibliography}" in preamble
    assert "Héraldique et papauté" in preamble
    assert "Jean Dupont" in preamble
    assert "Marie Martin" in preamble
    assert "PURH" in preamble
    assert "2024" in preamble


def test_render_purh_latex_preamble_escapes_special_chars() -> None:
    from purh_site.latei_preamble import PurhPreambleData, render_purh_latex_preamble
    data = PurhPreambleData(title="Titre & spécial % #1")
    preamble = render_purh_latex_preamble(data)
    assert r"\&" in preamble
    assert r"\%" in preamble
    assert r"\#" in preamble


def test_render_purh_latex_preamble_author_joining() -> None:
    from purh_site.latei_preamble import PurhPreambleData, render_purh_latex_preamble
    data = PurhPreambleData(authors=("Alpha Beta", "Gamma Delta", ""))
    preamble = render_purh_latex_preamble(data)
    assert "Alpha Beta ; Gamma Delta" in preamble


def test_render_purh_latex_preamble_empty_authors() -> None:
    from purh_site.latei_preamble import PurhPreambleData, render_purh_latex_preamble
    data = PurhPreambleData(title="Sans auteur")
    preamble = render_purh_latex_preamble(data)
    assert r"\PURHBookAuthor}{}" in preamble


def test_render_purh_latex_preamble_defaults_to_production_2025_profile() -> None:
    from purh_site.latei_preamble import PurhPreambleData, render_purh_latex_preamble
    from purh_site.purh_layout_profiles import PURH_155X230_PRODUCTION_2025
    preamble = render_purh_latex_preamble(PurhPreambleData())
    assert PurhPreambleData().profile == PURH_155X230_PRODUCTION_2025
    assert "inner=20mm" in preamble
    assert "outer=30mm" in preamble
    assert r"\renewcommand{\normalsize}{\fontsize{11pt}{13.5pt}\selectfont}" in preamble
    # \footnotelayout n'est plus le mécanisme actif depuis le 2026-08-04 :
    # \@makefntext applique directement la taille de note du profil (voir
    # test_latei_microtypography_p2.py pour le détail de ce changement).
    assert r"\fontsize{8.5pt}{10.2pt}\selectfont" in preamble


def test_render_purh_latex_preamble_honors_explicit_profile() -> None:
    from purh_site.latei_preamble import PurhPreambleData, render_purh_latex_preamble
    from purh_site.purh_layout_profiles import PURH_155X230_CURRENT_2026
    preamble = render_purh_latex_preamble(PurhPreambleData(profile=PURH_155X230_CURRENT_2026))
    assert "inner=25mm" in preamble
    assert "outer=23mm" in preamble


