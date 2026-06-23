from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from purh_site.site_latei_pdf_export import (
    SiteLateiPdfExportResult,
    build_site_latei_pdf_artifacts,
)


MINIMAL_TEI = (
    '<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_001">'
    "Un <hi rend=\"italic\">mot</hi>."
    "</p>"
)


def write_xml(path: Path, xml: str) -> Path:
    path.write_text(xml, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Test 1 — Importabilité
# ---------------------------------------------------------------------------

def test_build_site_latei_pdf_artifacts_is_importable_and_callable() -> None:
    assert callable(build_site_latei_pdf_artifacts)
    assert SiteLateiPdfExportResult is not None


# ---------------------------------------------------------------------------
# Test 2 — Mode LaTeX seul (compile_pdf=False)
# ---------------------------------------------------------------------------

def test_latex_only_mode_produces_book_tex_manifest_and_report(tmp_path: Path) -> None:
    xml_path = write_xml(tmp_path / "livre.xml", MINIMAL_TEI)

    result = build_site_latei_pdf_artifacts(xml_path, tmp_path, compile_pdf=False)

    assert result.tex_path.exists(), "book.tex doit exister"
    assert result.tex_path.stat().st_size > 0

    assert result.manifest_path.exists(), "book.latei_manifest.json doit exister"
    assert result.report_path.exists(), "pdf_build_report.txt doit exister"

    # book.pdf n'est PAS requis en mode compile_pdf=False
    # (même si LaTEI a pu produire le PDF natif en interne)
    # result.pdf_path peut exister ou non selon la disponibilité de lualatex — on ne le teste pas ici

    assert result.source_latei_path.exists(), "artefact natif {stem}.latei.tex doit exister"
    assert result.source_manifest_path.exists(), "manifeste natif doit exister"


# ---------------------------------------------------------------------------
# Test 3 — book.tex est bien un monofichier LaTEI
# ---------------------------------------------------------------------------

def test_book_tex_is_latei_monofile(tmp_path: Path) -> None:
    xml_path = write_xml(tmp_path / "livre.xml", MINIMAL_TEI)

    result = build_site_latei_pdf_artifacts(xml_path, tmp_path, compile_pdf=False)

    content = result.tex_path.read_text(encoding="utf-8")

    assert r"\begin{lateiDocument}" in content, r"book.tex doit contenir \begin{lateiDocument}"
    assert r"\input{" not in content, r"book.tex ne doit pas contenir \input{ (ce n'est pas un driver fragmenté)"


# ---------------------------------------------------------------------------
# Test 4 — Rapport de synthèse
# ---------------------------------------------------------------------------

def test_report_contains_expected_fields(tmp_path: Path) -> None:
    xml_path = write_xml(tmp_path / "livre.xml", MINIMAL_TEI)

    result = build_site_latei_pdf_artifacts(xml_path, tmp_path, compile_pdf=False)

    report = result.report_path.read_text(encoding="utf-8")

    assert "book.tex" in report
    assert "book.latei_manifest.json" in report
    # le chemin natif {stem}.latei.tex doit apparaître
    assert ".latei.tex" in report
    # le message de résultat LaTEI doit apparaître
    assert "Message" in report
    assert str(xml_path) in report


# ---------------------------------------------------------------------------
# Test 5 — Résultat est un SiteLateiPdfExportResult cohérent
# ---------------------------------------------------------------------------

def test_result_fields_are_consistent(tmp_path: Path) -> None:
    xml_path = write_xml(tmp_path / "livre.xml", MINIMAL_TEI)

    result = build_site_latei_pdf_artifacts(xml_path, tmp_path, compile_pdf=False)

    assert result.tex_path == tmp_path / "book.tex"
    assert result.pdf_path == tmp_path / "book.pdf"
    assert result.manifest_path == tmp_path / "book.latei_manifest.json"
    assert result.report_path == tmp_path / "pdf_build_report.txt"

    # source_latei_path est le natif produit par LaTEI
    assert result.source_latei_path.name.endswith(".latei.tex")
    assert result.source_latei_path != result.tex_path

    # source_manifest_path est le natif
    assert result.source_manifest_path.name.endswith("_manifest.json")
    assert result.source_manifest_path != result.manifest_path


# ---------------------------------------------------------------------------
# Test 6 — Natifs LaTEI non supprimés
# ---------------------------------------------------------------------------

def test_native_latei_artifacts_are_preserved(tmp_path: Path) -> None:
    xml_path = write_xml(tmp_path / "livre.xml", MINIMAL_TEI)

    result = build_site_latei_pdf_artifacts(xml_path, tmp_path, compile_pdf=False)

    assert result.source_latei_path.exists(), "Le monofichier natif doit rester en place"
    assert result.source_manifest_path.exists(), "Le manifeste natif doit rester en place"


# ---------------------------------------------------------------------------
# Test 7 — Mode PDF conditionnel (compile_pdf=True, sans exiger lualatex)
# ---------------------------------------------------------------------------

def test_pdf_mode_copies_pdf_when_produced(tmp_path: Path) -> None:
    xml_path = write_xml(tmp_path / "livre.xml", MINIMAL_TEI)

    result = build_site_latei_pdf_artifacts(xml_path, tmp_path, compile_pdf=True)

    # Si LuaLaTeX est disponible, book.pdf doit exister et n'être pas vide
    # Si LuaLaTeX est absent, book.tex et pdf_build_report.txt doivent quand même exister
    assert result.tex_path.exists(), "book.tex doit exister quel que soit l'état de lualatex"
    assert result.report_path.exists(), "pdf_build_report.txt doit exister quel que soit l'état de lualatex"

    if result.source_pdf_path.exists():
        # lualatex était disponible → book.pdf doit avoir été copié
        assert result.pdf_path.exists(), "book.pdf doit exister si le PDF natif a été produit"
        assert result.pdf_path.stat().st_size > 0
    else:
        # lualatex absent → book.pdf n'est pas requis
        report = result.report_path.read_text(encoding="utf-8")
        assert "non produit" in report


# ---------------------------------------------------------------------------
# Test 8 — Non-branchement dans site_builder
# ---------------------------------------------------------------------------

def test_site_builder_does_not_import_site_latei_pdf_export() -> None:
    source = Path("purh_site/site_builder.py").read_text(encoding="utf-8")
    assert "site_latei_pdf_export" not in source
    assert "build_site_latei_pdf_artifacts" not in source
