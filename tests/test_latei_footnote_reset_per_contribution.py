from __future__ import annotations

"""Référentiel PURH v0.6 §5/§17 (P0 item 5) : « notes remise à 1 par
contribution » — chaque ouverture de contribution (introduction, article,
chapitre, back matter) redémarre sa propre numérotation de notes plutôt que
de poursuivre celle de la contribution précédente sur tout le livre.
Confirmé comme défaut réel sur *Dissimuler pour mieux régner* : page 19 du
PDF imprimeur redémarre à 1, la même page dans le PDF généré poursuivait à
33 (voir Referentiel_mise_en_page_PURH_audit_v0.6.md, §"État actuel")."""

import re
import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_TWO_CONTRIBUTIONS_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Livre Notes</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="article" data-page-title="Article Un" xml:id="a1">
        <front><div type="titlePage"><p rend="title-main">Article Un</p></div></front>
        <body>
          <div>
            <p>Premier appel<note><p>NoteContenuA1</p></note> et second appel<note><p>NoteContenuA2</p></note>.</p>
          </div>
        </body>
      </group>
      <group type="article" data-page-title="Article Deux" xml:id="a2">
        <front><div type="titlePage"><p rend="title-main">Article Deux</p></div></front>
        <body>
          <div>
            <p>Nouvel appel<note><p>NoteContenuB1</p></note>.</p>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def two_contributions_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_footnote_reset")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_TWO_CONTRIBUTIONS_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_contribution_opening_break_resets_footnote_counter() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    break_macro = macros.split(r"\cs_new_protected:Npn \latei_add_contribution_opening_break:")[1].split(
        r"\NewDocumentCommand{\lateiRenderFrontGroup}"
    )[0]
    assert r"\setcounter{footnote}{0}" in break_macro


def test_second_contribution_footnotes_restart_at_one(two_contributions_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not two_contributions_export.latei_pdf_success:
        log = two_contributions_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Two-contributions sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(two_contributions_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    # Contribution A: notes numbered 1, then 2 (continuous within the same contribution).
    assert re.search(r"1\s*NoteContenuA1", text)
    assert re.search(r"2\s*NoteContenuA2", text)

    # Contribution B: numbering restarts at 1 — never continues at 3.
    assert re.search(r"1\s*NoteContenuB1", text)
    assert not re.search(r"3\s*NoteContenuB1", text)
