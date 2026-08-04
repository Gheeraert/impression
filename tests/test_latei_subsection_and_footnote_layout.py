from __future__ import annotations

"""Deux défauts signalés directement par l'utilisateur en comparant le PDF
généré au PDF imprimeur de *Dissimuler pour mieux régner* (référentiel PURH
v0.6, chantier de parité 2026-08-03) :

1. Titres de section (<div type="section2">, i.e. head-context "subsection")
   restés en Josefin Sans Bold au lieu de Thin — seul le niveau section1
   avait été corrigé lors de la passe titraille précédente. Confirmé sur le
   livre réel : tests/fixtures/commons-publishing/dissimuler/xml contient
   4 <div type="section2"> portant de vrais sous-titres phrastiques (ex.
   "Montage narratif : un je entre inclusion et exclusion"), jamais des
   libellés courts — pas de capitales forcées à ce niveau.
2. Notes de bas de page : sur le PDF imprimeur le numéro est calé à gauche
   avec un retrait négatif de première ligne (hanging indent), sans point
   après le numéro — contrairement au référentiel (qui indique "point +
   espace cadratin", jamais revérifié depuis la v0.5), l'observation directe
   de l'utilisateur sur le PDF imprimeur fait foi ici.

Correctif du 2026-08-04, après nouvelle vérification humaine du PDF généré :
le retrait négatif de première ligne restait invisible malgré le
\\leftskip/\\parindent négatif déjà en place, parce qu'un \\noindent placé
juste avant \\@thefnmark annulait l'effet du \\parindent négatif sur la
première ligne (celle-ci se retrouvait alignée sur \\leftskip comme les
lignes suivantes). Supprimer ce \\noindent laisse LaTeX indenter
naturellement la première ligne de \\parindent, donc la ramener à la marge —
c'est précisément l'effet recherché."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_SUBSECTION_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title type="main">Livre</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="article" data-page-title="Article un" xml:id="a1">
        <front><div type="titlePage"><p rend="title-main">Article un</p></div></front>
        <body>
          <div type="section1">
            <head>Une section de premier niveau</head>
            <p>Corps.</p>
            <div type="section2">
              <head>Un sous-titre phrastique de section</head>
              <p>Corps de sous-section.</p>
            </div>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>"""

_FOOTNOTE_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="chapter" xml:id="c1">
        <head>Test notes</head>
        <p>Un texte avec un appel de note<note><p>Contenu de la note.</p></note> et la suite.</p>
      </div>
    </body>
  </text>
</TEI>"""

_LONG_FOOTNOTE_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="chapter" xml:id="c1">
        <head>Test notes longues</head>
        <p>Un texte avec un appel de note<note><p>Ceci est une note assez longue pour forcer un retour a la ligne automatique dans le corps du texte de la note elle meme afin de verifier le retrait.</p></note> et la suite du texte normal.</p>
      </div>
    </body>
  </text>
</TEI>"""


def test_subsection_titleformat_uses_thin_family_without_bold() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    subsection_block = preamble_source.split(r"\titleformat{{\subsection}}[block]")[1].split(
        r"\titleformat{{\subsubsection}}[block]"
    )[0]

    assert r"\PURHTitreFont" in subsection_block
    assert r"\bfseries" not in subsection_block
    assert r"\PURHTitleFont" not in subsection_block


def test_footnote_makefntext_uses_hanging_indent_and_no_period() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")

    assert r"\@makefntext" in preamble_source
    assert r"\leftskip}}{{1.2em}}" in preamble_source
    assert r"\parindent}}{{-1.2em}}" in preamble_source
    # No literal period between the footnote mark and its separator.
    assert r"\@thefnmark\enskip#1" in preamble_source
    assert r"\@thefnmark.\enskip" not in preamble_source
    assert r"\@thefnmark. " not in preamble_source
    # Regression guard (bug réel corrigé le 2026-08-04) : un \noindent placé
    # ici annule l'effet du \parindent négatif sur la première ligne — la
    # première ligne resterait alors alignée sur \leftskip comme les
    # suivantes, sans retrait négatif visible.
    assert r"\noindent\@thefnmark" not in preamble_source


def test_footnote_override_is_registered_after_hyperref() -> None:
    """Real bug hit while implementing this: hyperref/bookmark redefine
    \\@makefntext via their own \\AtBeginDocument hook, which silently wins
    over a plain preamble-time \\renewcommand placed even textually after
    their \\usepackage — the override only takes effect once it is itself
    deferred to \\AtBeginDocument, registered after hyperref's own hook."""
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")

    hyperref_pos = preamble_source.index("{{hyperref}}")
    override_pos = preamble_source.index(r"\@makefntext")
    assert override_pos > hyperref_pos
    assert r"\AtBeginDocument{{%" in preamble_source


@pytest.fixture(scope="module")
def subsection_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_subsection")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_SUBSECTION_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


@pytest.fixture(scope="module")
def footnote_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_footnote_layout")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_FOOTNOTE_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


@pytest.fixture(scope="module")
def long_footnote_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_footnote_hanging_indent")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_LONG_FOOTNOTE_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_subsection_compiles_without_bold_josefin_in_body(subsection_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not subsection_export.latei_pdf_success:
        log = subsection_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Subsection sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(subsection_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    assert "Un sous-titre phrastique de section" in process.stdout


def test_footnote_number_has_no_trailing_period_in_rendered_pdf(footnote_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not footnote_export.latei_pdf_success:
        log = footnote_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Footnote sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(footnote_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    assert "1. Contenu de la note" not in text
    assert "Contenu de la note" in text


def test_footnote_first_line_is_flush_left_and_continuation_is_indented(long_footnote_export) -> None:
    """Vérification directe du retrait négatif de première ligne : le numéro
    doit démarrer au niveau de la marge gauche (sans retrait), la ligne de
    suite doit être indentée sur \\leftskip — sinon la note entière apparaît
    alignée d'un seul bloc, sans le décroché attendu (bug du 2026-08-04)."""
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not long_footnote_export.latei_pdf_success:
        log = long_footnote_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Long footnote sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(long_footnote_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    lines = process.stdout.splitlines()

    first_line = next((line for line in lines if "Ceci est une note" in line), None)
    continuation_line = next((line for line in lines if "le corps du texte de la note" in line), None)
    assert first_line is not None, f"Footnote first line not found in:\n{process.stdout}"
    assert continuation_line is not None, f"Footnote continuation line not found in:\n{process.stdout}"

    first_line_indent = len(first_line) - len(first_line.lstrip(" "))
    continuation_indent = len(continuation_line) - len(continuation_line.lstrip(" "))

    assert first_line.lstrip(" ").startswith("1"), f"Expected the footnote mark at the very start: {first_line!r}"
    assert first_line_indent < continuation_indent, (
        f"First line indent ({first_line_indent}) should be smaller than the "
        f"continuation line indent ({continuation_indent}) — got first={first_line!r}, "
        f"continuation={continuation_line!r}"
    )
