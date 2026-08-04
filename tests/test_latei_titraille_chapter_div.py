from __future__ import annotations

"""Titraille du chemin <div type="chapter"> (complément à la micropasse 7,
"Titraille") : ce \\chapter numéroté, distinct de l'ouverture de
contribution corrigée en micropasse 5, était resté en Chaparral/Josefin
Bold bas de casse. Passé au même traitement Josefin Sans 16 pt capitales que
le titre de partie/contribution — seule la police change, le libellé
"Chapitre N" (une question structurelle distincte) est inchangé.

Graisse re-corrigée le 2026-08-04 : Thin d'abord (référentiel §2.5/§5.3),
puis Bold après vérification humaine directe du PDF généré face au PDF
imprimeur (voir test_latei_titraille.py pour le détail de cette
contradiction assumée avec le texte du référentiel)."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_CHAPTER_DIV_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="chapter" xml:id="c1">
        <head>Titre de chapitre</head>
        <p>Corps du chapitre.</p>
      </div>
    </body>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def chapter_div_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_titraille_chapter_div")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_CHAPTER_DIV_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_chapter_titleformat_uses_bold_family_16pt_uppercase() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    chapter_block = preamble_source.split(r"\titleformat{{\chapter}}[display]")[1].split(r"\titleformat{{\part}}")[0]

    assert r"\PURHTitleFont\bfseries\fontsize{{16pt}}{{19pt}}\selectfont" in chapter_block
    assert r"{{\MakeUppercase}}" in chapter_block


def test_chapter_div_renders_uppercase_title_keeps_chapitre_label(chapter_div_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not chapter_div_export.latei_pdf_success:
        log = chapter_div_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Chapter-div titraille sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(chapter_div_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    assert "TITRE DE CHAPITRE" in text
    # The "Chapitre N" label is a structural question distinct from
    # titraille (font/case/size) and is untouched by this pass.
    assert "Chapitre 1" in text
