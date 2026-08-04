from __future__ import annotations

"""Référentiel PURH v0.6 §7 (P1 items 1-3, chantier de parité *Dissimuler
pour mieux régner*) :

1. Ouverture de partie : « page de style vide » — aucun en-tête ni folio.
2. Ouverture de contribution : « aucun en-tête ni folio » (§7.2, cible page
   23) — l'état constaté (page 19) affichait en-tête et folio, marqué
   « Statut : bloquant » par le référentiel.
3. Visibilité auteur/affiliation : « auteur et affiliation non imprimés »
   sur l'ouverture de contribution, mais « le profil doit distinguer
   conservation des métadonnées et visibilité sur la page » — la donnée
   <p rend="author-aut"> / <p rend="authority_affiliation"> reste dans le
   corps LaTEI réversible, seul son affichage PDF bascule avec le profil."""

import re
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from purh_site.latei_preamble import PurhPreambleData, render_purh_latex_preamble
from purh_site.purh_layout_profiles import DEFAULT_LAYOUT_PROFILE_NAME, get_layout_profile
from purh_site.reversible_integration import run_reversible_export_for_file

_ARTICLE_WITH_AUTHOR_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Livre Ouverture</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="section1">
        <head>Une Partie</head>
        <group type="article" data-page-title="Article Test" xml:id="a1">
          <front><div type="titlePage">
            <p rend="title-main">Titre Article</p>
            <p rend="author-aut">Jean Dupont</p>
            <p rend="authority_affiliation">Universite Test</p>
          </div></front>
          <body><div><p>Corps de l'article.</p></div></body>
        </group>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def article_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_opening_templates")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_ARTICLE_WITH_AUTHOR_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_default_production_profile_hides_contribution_author() -> None:
    profile = get_layout_profile(DEFAULT_LAYOUT_PROFILE_NAME)
    assert profile.show_contribution_author is False


def test_preamble_reflects_profile_show_contribution_author_flag() -> None:
    hidden_profile = replace(get_layout_profile(DEFAULT_LAYOUT_PROFILE_NAME), show_contribution_author=False)
    visible_profile = replace(hidden_profile, show_contribution_author=True)

    hidden_preamble = render_purh_latex_preamble(PurhPreambleData(profile=hidden_profile))
    visible_preamble = render_purh_latex_preamble(PurhPreambleData(profile=visible_profile))

    assert r"\lateiShowContributionAuthorfalse" in hidden_preamble
    assert r"\lateiShowContributionAuthortrue" not in hidden_preamble
    assert r"\lateiShowContributionAuthortrue" in visible_preamble
    assert r"\lateiShowContributionAuthorfalse" not in visible_preamble


def test_contribution_author_and_affiliation_macros_are_gated_by_the_flag() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")

    author_macro = macros.split(r"\newcommand{\lateiContributionAuthor}[1]{")[1].split(r"\newcommand{\lateiContributionAffiliation}")[0]
    affiliation_macro = macros.split(r"\newcommand{\lateiContributionAffiliation}[1]{")[1].split(r"\newcommand{\lateiContributionTranslator}")[0]

    assert r"\iflateiShowContributionAuthor" in author_macro
    assert r"\iflateiShowContributionAuthor" in affiliation_macro


def test_opening_breaks_force_empty_pagestyle() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")

    contribution_break = macros.split(r"\cs_new_protected:Npn \latei_add_contribution_opening_break:")[1].split(
        r"\NewDocumentCommand{\lateiRenderFrontGroup}"
    )[0]
    assert r"\thispagestyle{empty}" in contribution_break

    part_group = macros.split(r"\NewDocumentCommand{\lateiRenderPartGroup}")[1].split(
        r"\NewDocumentCommand{\lateiRenderBackGroup}"
    )[0]
    assert r"\thispagestyle{empty}" in part_group


def test_contribution_body_stays_reversible_even_when_author_is_hidden(article_export) -> None:
    """Le drapeau ne touche que le rendu PDF : le corps LaTEI réversible
    conserve intégralement les paragraphes auteur/affiliation."""
    body = article_export.latei_body_path.read_text(encoding="utf-8")

    assert r"\teiP[rend={author-aut}]" in body
    assert "Jean Dupont" in body
    assert r"\teiP[rend={authority\_affiliation}]" in body
    assert "Universite Test" in body


def test_opening_pdf_hides_author_and_affiliation_but_shows_title(article_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not article_export.latei_pdf_success:
        log = article_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Opening template sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(article_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    assert re.search(r"TITRE ARTICLE", text)

    # Author/affiliation are hidden in the *opening title block* specifically
    # (title/subtitle/author display area) — for this minimal fixture the
    # body is short enough that the end-of-article signature (see
    # test_latei_toc_author_and_signature.py) lands on the same physical
    # page, so document order (opening block precedes the body), not a page
    # boundary, is the meaningful check here.
    title_pos = text.index("TITRE ARTICLE")
    body_pos = text.index("Corps de l")
    opening_block = text[title_pos:body_pos]
    assert "Jean Dupont" not in opening_block
    assert "Universite Test" not in opening_block
    # And the signature confirms the data was never discarded, only hidden
    # at the opening.
    assert "Jean Dupont" in text[body_pos:]


def test_opening_page_carries_no_running_title_header_text(article_export) -> None:
    """Référentiel §7.2 : « aucun en-tête ni folio » sur l'ouverture de
    contribution — le titre courant de la contribution (ici son propre
    intitulé de TDM) ne doit donc pas apparaître en double, une fois comme
    en-tête de la page d'ouverture et une fois comme titre affiché."""
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not article_export.latei_pdf_success:
        log = article_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Opening template sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    toc_path = article_export.latei_pdf_path.with_suffix(".toc")
    assert toc_path.exists()
    toc = toc_path.read_text(encoding="utf-8", errors="replace")
    # Lazy match up to the first "}{<digits>}{" rather than an exact
    # "{Article Test}" : since the signed-article TOC entry got an appended
    # \lateiTocAuthorBreak + author name (2026-08-04, see
    # test_latei_toc_author_and_signature.py), the title brace group itself
    # now contains further nested braces (\hspace*{1em}) before it closes.
    match = re.search(r"\\contentsline\s*\{chapter\}\{Article Test.*?\}\{(\d+)\}\{", toc, re.DOTALL)
    assert match, f"Expected a chapter TOC entry for Article Test, got: {toc!r}"
    opening_page_number = int(match.group(1))

    process = subprocess.run(
        [
            shutil.which("pdftotext"),
            "-enc", "UTF-8", "-layout",
            "-f", str(opening_page_number), "-l", str(opening_page_number),
            str(article_export.latei_pdf_path), "-",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    opening_page_text = process.stdout

    # The running-title header would repeat "Article Test" verbatim; the
    # visible title itself is uppercased by \lateiContributionTitle, so the
    # two are textually distinguishable.
    assert "Article Test" not in opening_page_text
