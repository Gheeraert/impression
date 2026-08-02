from __future__ import annotations

"""M3/M4 — editorial workflow and compilation tests for the LaTEI monofile.

Proves that a corrected monofile produces a corrected XML, and that
modifications outside the lateiDocument zone are invisible to the parser.
M4 adds: the corrected monofile remains compilable to PDF.
"""

import shutil
from pathlib import Path

import pytest
from lxml import etree

from purh_site.latei_driver import compile_latei_pdf
from purh_site.reversible import (
    compare_tei_elements,
    read_tei_element,
    write_latex,
    write_tei_element,
)
from purh_site.reversible.latex_reader import extract_latei_document_zone, read_latex_document
from purh_site.reversible_integration import (
    restore_xml_from_latei_monofile,
    run_reversible_export_for_file,
)

TEI_NS = "http://www.tei-c.org/ns/1.0"

MINI_XML = f"""<TEI xmlns="{TEI_NS}">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Livre test</title>
      </titleStmt>
      <publicationStmt>
        <p>Publication test</p>
      </publicationStmt>
      <sourceDesc>
        <p>Source test</p>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="chapter" xml:id="chap1">
        <head>Chapitre test</head>
        <p>Texte avant correction.</p>
      </div>
    </body>
  </text>
</TEI>"""


def parse_xml(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


def make_monofile(latex_body: str) -> str:
    """Wrap a LaTEI body in a minimal monofile with a fake technical zone."""
    return (
        "% fake preamble — zone technique\n"
        "\\documentclass{book}\n"
        "\\begin{titlepage}Titre fictif.\\end{titlepage}\n"
        "\\begin{document}\n"
        "\\begin{lateiDocument}\n"
        + latex_body + "\n"
        + "\\end{lateiDocument}\n"
        "\\end{document}\n"
    )


def replace_inside_latei_document(monofile_text: str, old: str, new: str) -> str:
    """Replace a string only within the lateiDocument zone."""
    begin_marker = "\\begin{lateiDocument}"
    end_marker = "\\end{lateiDocument}"
    begin_pos = monofile_text.find(begin_marker)
    end_pos = monofile_text.find(end_marker)
    before = monofile_text[: begin_pos + len(begin_marker)]
    zone = monofile_text[begin_pos + len(begin_marker) : end_pos]
    after = monofile_text[end_pos:]
    return before + zone.replace(old, new) + after


def restore_from_monofile_text(monofile_text: str) -> etree._Element:
    zone = extract_latei_document_zone(monofile_text)
    return write_tei_element(read_latex_document(zone))


# ---------------------------------------------------------------------------
# Test 1 — correction éditoriale simple (texte brut)
# ---------------------------------------------------------------------------

def test_text_correction_in_zone_reflected_in_restored_xml() -> None:
    element = parse_xml(MINI_XML)
    latex_body = write_latex(read_tei_element(element))
    assert "Texte avant correction." in latex_body

    monofile = make_monofile(latex_body)
    modified = replace_inside_latei_document(
        monofile, "Texte avant correction.", "Texte après correction éditoriale."
    )

    restored = restore_from_monofile_text(modified)
    xml_str = etree.tostring(restored, encoding="unicode")
    assert "Texte après correction éditoriale." in xml_str
    assert "Texte avant correction." not in xml_str


def test_uncorrected_monofile_preserves_original_text() -> None:
    element = parse_xml(MINI_XML)
    latex_body = write_latex(read_tei_element(element))
    monofile = make_monofile(latex_body)

    restored = restore_from_monofile_text(monofile)
    xml_str = etree.tostring(restored, encoding="unicode")
    assert "Texte avant correction." in xml_str


# ---------------------------------------------------------------------------
# Test 2 — correction typographique inline (italique structuré)
# ---------------------------------------------------------------------------

def test_inline_structural_correction_reflected_in_restored_xml() -> None:
    source_xml = f'<p xmlns="{TEI_NS}">Texte simple.</p>'
    element = parse_xml(source_xml)
    latex_body = write_latex(read_tei_element(element))
    assert "Texte simple." in latex_body

    monofile = make_monofile(latex_body)
    modified = replace_inside_latei_document(
        monofile,
        "Texte simple.",
        "Texte avec \\teiHi[rend={italic}]{mot corrigé}.",
    )

    restored = restore_from_monofile_text(modified)
    xml_str = etree.tostring(restored, encoding="unicode")
    assert "mot corrigé" in xml_str
    hi_elements = restored.findall(f".//{{{TEI_NS}}}hi")
    assert any(el.get("rend") == "italic" for el in hi_elements)


def test_inline_note_correction_reflected_in_restored_xml() -> None:
    source_xml = f'<p xmlns="{TEI_NS}">Texte de base.</p>'
    element = parse_xml(source_xml)
    latex_body = write_latex(read_tei_element(element))

    monofile = make_monofile(latex_body)
    modified = replace_inside_latei_document(
        monofile,
        "Texte de base.",
        "Texte\\teiNote{Note ajoutée.} de base.",
    )

    restored = restore_from_monofile_text(modified)
    note_elements = restored.findall(f".//{{{TEI_NS}}}note")
    assert len(note_elements) == 1
    assert note_elements[0].text == "Note ajoutée."


# ---------------------------------------------------------------------------
# Test 3 — modification dans la zone technique → ignorée par le retour XML
# ---------------------------------------------------------------------------

def test_technical_zone_modification_ignored_by_xml_restore() -> None:
    element = parse_xml(MINI_XML)
    latex_body = write_latex(read_tei_element(element))
    monofile = make_monofile(latex_body)

    # Modifier un commentaire et une macro dans la zone technique (hors lateiDocument)
    modified = monofile.replace(
        "% fake preamble — zone technique",
        "% MODIFIÉ PAR L'ÉDITRICE — zone technique non réversible",
    ).replace(
        "\\begin{titlepage}Titre fictif.\\end{titlepage}",
        "\\begin{titlepage}Titre corrigé par l'éditrice.\\end{titlepage}",
    )
    assert "\\begin{lateiDocument}" in modified

    restored_original = restore_from_monofile_text(monofile)
    restored_modified = restore_from_monofile_text(modified)
    assert compare_tei_elements(restored_original, restored_modified) == []


# ---------------------------------------------------------------------------
# Test 4 — modification hors zone éditoriale → XML restauré identique à l'original
# ---------------------------------------------------------------------------

def test_modification_outside_editorial_zone_leaves_xml_unchanged() -> None:
    element = parse_xml(MINI_XML)
    latex_body = write_latex(read_tei_element(element))
    monofile = make_monofile(latex_body)

    # Simuler une éditrice qui a modifié seulement la page de titre
    # (après \end{lateiDocument}, dans la zone non réversible)
    modified = monofile.replace(
        "\\end{document}",
        "% titre modifié dans la page de garde\n\\end{document}",
    )

    restored_original = restore_from_monofile_text(monofile)
    restored_modified = restore_from_monofile_text(modified)

    assert compare_tei_elements(restored_original, restored_modified) == []
    xml_str = etree.tostring(restored_modified, encoding="unicode")
    assert "titre modifié" not in xml_str


# ---------------------------------------------------------------------------
# Test d'intégration — correction sur vrai monofichier généré par le moteur
# ---------------------------------------------------------------------------

def test_editorial_correction_on_real_generated_monofile(tmp_path: Path) -> None:
    xml_path = tmp_path / "mini.xml"
    xml_path.write_text(MINI_XML, encoding="utf-8")

    result = run_reversible_export_for_file(xml_path, tmp_path / "out")
    monofile_text = result.latei_monofile_path.read_text(encoding="utf-8")
    assert "Texte avant correction." in monofile_text

    edited_text = replace_inside_latei_document(
        monofile_text, "Texte avant correction.", "Texte après correction éditoriale."
    )
    edited_path = tmp_path / "edited.latei.tex"
    edited_path.write_text(edited_text, encoding="utf-8")

    restored_xml_path = tmp_path / "restored.xml"
    restore_xml_from_latei_monofile(edited_path, restored_xml_path)

    content = restored_xml_path.read_text(encoding="utf-8")
    assert "Texte après correction éditoriale." in content
    assert "Texte avant correction." not in content


# ---------------------------------------------------------------------------
# Test M4 — monofichier corrigé → PDF + XML depuis le même fichier
# ---------------------------------------------------------------------------

def test_corrected_monofile_compiles_and_restores_xml(tmp_path: Path) -> None:
    xml_path = tmp_path / "mini.xml"
    xml_path.write_text(MINI_XML, encoding="utf-8")

    result = run_reversible_export_for_file(xml_path, tmp_path / "out")
    monofile_text = result.latei_monofile_path.read_text(encoding="utf-8")
    assert "Texte avant correction." in monofile_text

    edited_text = replace_inside_latei_document(
        monofile_text, "Texte avant correction.", "Texte après correction éditoriale."
    )
    edited_path = tmp_path / "edited.latei.tex"
    edited_path.write_text(edited_text, encoding="utf-8")

    # Vérification XML — indépendante de LuaLaTeX
    restored_xml_path = tmp_path / "restored.xml"
    restore_xml_from_latei_monofile(edited_path, restored_xml_path)
    xml_content = restored_xml_path.read_text(encoding="utf-8")
    assert "Texte après correction éditoriale." in xml_content
    assert "Texte avant correction." not in xml_content

    # Compilation PDF — skippée proprement si LuaLaTeX absent
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable — PDF compilation not verified.")

    edited_pdf_path = tmp_path / "edited.latei_mono.pdf"
    edited_log_path = tmp_path / "edited.latei_mono_build.log"
    pdf_result = compile_latei_pdf(edited_path, edited_pdf_path, log_path=edited_log_path)

    if not pdf_result.success:
        log_excerpt = ""
        if edited_log_path.exists():
            log_excerpt = "\n".join(
                edited_log_path.read_text(encoding="utf-8", errors="replace").splitlines()[:160]
            )
        pytest.fail(f"Corrected monofile did not compile.\n{log_excerpt}")

    assert edited_pdf_path.exists()
    assert edited_pdf_path.stat().st_size > 0
    assert edited_log_path.exists()
