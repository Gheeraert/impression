from __future__ import annotations

"""Ouvertures à droite (belle page) : le référentiel PURH v0.5 (§5.2) note
que la classe openany ne garantit aucune politique fiable d'ouverture à
droite pour les parties et articles ("blancs techniques si nécessaire").
\\cleardoublepage force l'ouverture sur une page recto (impaire) quelle que
soit l'option de classe openany/openright — utilisé ici pour chaque partie
et chaque ouverture de contribution (front/chapitre/back), indépendamment
du fait qu'il s'agisse ou non de la toute première bascule de matière."""

import re
import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_FILLER = "<p>Texte de remplissage pour forcer un saut de page supplementaire.</p>" * 15

_TWO_PARTS_XML = f"""<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Livre Ouvertures</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="section1">
        <head>Premiere Partie</head>
        <group type="article" data-page-title="Article Un" xml:id="a1">
          <front><div type="titlePage"><p rend="title-main">Article Un</p></div></front>
          <body><div><p>Corps un.</p>{_FILLER}</div></body>
        </group>
      </group>
      <group type="section1">
        <head>Seconde Partie</head>
        <group type="article" data-page-title="Article Deux" xml:id="a2">
          <front><div type="titlePage"><p rend="title-main">Article Deux</p></div></front>
          <body><div><p>Corps deux.</p></div></body>
        </group>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def two_parts_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_recto_openings")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_TWO_PARTS_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_contribution_opening_break_uses_cleardoublepage_not_clearpage() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert r"\cleardoublepage" in macros
    # The contribution-opening break macro itself must not fall back to a
    # plain \clearpage — that was the exact defect (openany gave no
    # guarantee of a recto start).
    break_macro = macros.split(r"\cs_new_protected:Npn \latei_add_contribution_opening_break:")[1].split(r"\NewDocumentCommand{\lateiRenderFrontGroup}")[0]
    assert r"\cleardoublepage" in break_macro
    assert r"\clearpage" not in break_macro.replace(r"\cleardoublepage", "")


def test_part_group_forces_cleardoublepage_on_every_part() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    part_group = macros.split(r"\NewDocumentCommand{\lateiRenderPartGroup}")[1].split(r"\NewDocumentCommand{\lateiRenderBackGroup}")[0]
    assert r"\cleardoublepage" in part_group


def test_part_star_toc_entry_is_not_duplicated() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    # \part* already registers its own TOC entry under our [display] shape
    # (verified empirically) — a manual \addcontentsline{toc}{part}{...}
    # right after it would duplicate every part in the table of contents.
    assert r"\part*{#1}\lateiMarkBothVerso{#1}\addcontentsline{toc}{part}" not in macros


def test_every_part_and_article_starts_on_an_odd_recto_page(two_parts_export) -> None:
    assert two_parts_export.latei_pdf_success is True, two_parts_export.latei_pdf_message

    toc_path = two_parts_export.latei_pdf_path.with_suffix(".toc")
    assert toc_path.exists()
    toc = toc_path.read_text(encoding="utf-8", errors="replace")

    # The title group allows one level of nested braces: part-level entries
    # are wrapped in \MakeUppercase []{...} since 2026-08-05 (fake small
    # caps for the TOC, \scshape being inert on Josefin Sans), which a
    # brace-free [^{}]* group can no longer match.
    entries = re.findall(r"\\contentsline\s*\{(?:part|chapter)\}\{((?:[^{}]|\{[^{}]*\})*)\}\{(\d+)\}", toc)
    assert len(entries) == 4, f"Expected 4 TOC entries (2 parts, 2 articles), got: {toc!r}"

    def _strip_uppercase_wrapper(title: str) -> str:
        match = re.fullmatch(r"\\MakeUppercase\s*(?:\[\])?\{([^{}]*)\}", title)
        return match.group(1) if match else title

    pages_by_title = {_strip_uppercase_wrapper(title): int(page) for title, page in entries}
    # Décalées de 6 pages depuis l'ajout des liminaires (référentiel PURH
    # v0.6 §8.1 : 2 pages blanches, faux-titre, crédits, page de titre,
    # page blanche avant tout contenu) — voir test_latei_front_matter_sequence.py.
    assert pages_by_title == {
        "Premiere Partie": 7,
        "Article Un": 9,
        "Seconde Partie": 11,
        "Article Deux": 13,
    }
    for title, page in pages_by_title.items():
        assert page % 2 == 1, f"{title!r} opens on an even (verso) page {page}, expected odd (recto)."


def test_recto_openings_still_compile_with_pdfinfo(two_parts_export) -> None:
    if shutil.which("pdfinfo") is None:
        pytest.skip("pdfinfo is unavailable.")
    import subprocess

    process = subprocess.run(
        [shutil.which("pdfinfo"), str(two_parts_export.latei_pdf_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    assert "Pages:" in process.stdout
