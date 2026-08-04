from __future__ import annotations

"""Référentiel PURH v0.6 §9 ("Table des matières", P1 item 5) :

- « exclut les sections internes » — l'état constaté incluait à tort les
  intertitres (<div type="section1">/<div type="section2">, niveaux
  \\section/\\subsection) dans la TDM, la gonflant à trois pages au lieu de
  deux. tocdepth=2 -> 0 : seuls les niveaux \\part (-1) et
  \\addcontentsline{toc}{chapter}{...} (0, ouvertures de contribution/front
  matter) restent, conformément à la cible.
- « utilise une page de style spécifique » — l'état constaté ne montrait le
  style dédié (sans titre courant) que sur la première page de la TDM ; les
  pages suivantes reprenaient le titre courant ordinaire, un comportement
  standard de \\tableofcontents (dont seule la première page, via
  \\chapter*, reçoit un \\thispagestyle{plain} explicite). \\pagestyle{plain}
  est maintenant appliqué avant \\tableofcontents pour couvrir toutes ses
  pages, pas seulement la première.

Non traité dans cette passe (référentiel §9.1) : affichage de l'auteur
comme élément typographique distinct sous chaque entrée de contribution
(nécessite de faire transiter la métadonnée auteur jusqu'à l'entrée de TDM,
absente aujourd'hui de data-page-title) et accueil du colophon en bas de
la seconde page."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_ARTICLE_TEMPLATE = """
      <group type="article" data-page-title="Article {n}" xml:id="a{n}">
        <front><div type="titlePage"><p rend="title-main">Article {n}</p></div></front>
        <body><div type="section1"><head>Intertitre {n}</head><p>Corps {n}.</p></div></body>
      </group>"""

_MANY_ARTICLES_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <group type="book">
      {articles}
    </group>
  </text>
</TEI>""".format(articles="".join(_ARTICLE_TEMPLATE.format(n=n) for n in range(1, 21)))


@pytest.fixture(scope="module")
def many_articles_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_toc_depth")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_MANY_ARTICLES_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_tocdepth_is_zero_to_exclude_internal_sections() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\setcounter{{tocdepth}}{{0}}" in preamble_source
    assert r"\setcounter{{tocdepth}}{{2}}" not in preamble_source


def test_pagestyle_plain_is_set_before_tableofcontents() -> None:
    driver_source = Path("purh_site/latei_driver.py").read_text(encoding="utf-8")
    assert driver_source.count(r'r"\pagestyle{plain}"') == 2
    for chunk in driver_source.split(r'r"\pagestyle{plain}"')[1:]:
        assert r'r"\tableofcontents"' in chunk.split("]")[0]


def test_toc_excludes_internal_section_headings(many_articles_export) -> None:
    """tocdepth ne filtre pas l'écriture du fichier .toc (\\section y écrit
    toujours sa \\contentsline, quelle que soit la valeur de tocdepth) — seul
    l'affichage au moment de \\tableofcontents est concerné (\\l@section
    vérifie tocdepth). Le fichier .toc brut n'est donc pas le bon point de
    contrôle ; il faut vérifier le texte réellement composé dans le PDF."""
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not many_articles_export.latei_pdf_success:
        log = many_articles_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Many-articles sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    toc_path = many_articles_export.latei_pdf_path.with_suffix(".toc")
    assert toc_path.exists()
    toc = toc_path.read_text(encoding="utf-8", errors="replace")
    # Written unconditionally by \section itself — confirms the fixture
    # genuinely exercises intertitres, independently of tocdepth.
    assert r"\contentsline {chapter}{Article 1}" in toc
    assert r"\contentsline {section}{Intertitre 1}" in toc

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", str(many_articles_export.latei_pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert process.returncode == 0, process.stderr
    toc_marker = process.stdout.upper().index("TABLE DES MATI")
    rendered_toc_text = process.stdout[toc_marker:]

    assert "Article 1" in rendered_toc_text
    assert "Intertitre" not in rendered_toc_text


def test_second_toc_page_has_no_running_title_header(many_articles_export) -> None:
    """Vingt articles forcent la TDM sur deux pages physiques ; la seconde
    ne doit porter aucun titre courant (référentiel : « page de style
    spécifique », pas seulement sur la première page)."""
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not many_articles_export.latei_pdf_success:
        log = many_articles_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Many-articles sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    pdf_path = many_articles_export.latei_pdf_path
    full_text = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", str(pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    ).stdout
    toc_page = None
    for page in range(1, 60):
        process = subprocess.run(
            [shutil.which("pdftotext"), "-enc", "UTF-8", "-f", str(page), "-l", str(page), str(pdf_path), "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        if "TABLE DES MATI" in process.stdout.upper():
            toc_page = page
            break
    assert toc_page is not None, f"Could not locate the TOC page.\n{full_text[:2000]}"

    second_toc_page_text = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-f", str(toc_page + 1), "-l", str(toc_page + 1), str(pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    ).stdout

    assert "Article 20" in second_toc_page_text
    # No running-title header line: neither the book's own fallback title
    # ("TEI", from the minimal fixture's untitled teiHeader) nor a folio
    # should appear before the first TOC entry line.
    lines_before_first_entry = second_toc_page_text.split("Article", 1)[0]
    assert lines_before_first_entry.strip() == ""
