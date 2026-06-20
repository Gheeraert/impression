from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from purh_site.gui import (
    format_latei_export_summary,
    missing_latei_package_artifacts,
)


def test_gui_labels_use_latei_vocabulary() -> None:
    source = Path("purh_site/gui.py").read_text(encoding="utf-8")

    assert "Export LaTEI / PDF PURH" in source
    assert "Ne pas générer de paquet LaTEI" in source
    assert "Exporter le paquet LaTEI seul" in source
    assert "Exporter le paquet LaTEI + compiler le PDF" in source
    assert "Exporter un paquet LaTEI réversible" in source
    assert "Le paquet LaTEI contient le corps réversible" in source

    assert "Sorties PDF / LaTeX" not in source
    assert "Générer le LaTeX seul" not in source
    assert "Générer le LaTeX + PDF" not in source
    assert "Tester la réversibilité TEI ↔ LaTeX" not in source
    assert 'add_cascade(label="Outils"' in source
    assert source.index("Exporter un paquet LaTEI réversible") < source.index('add_cascade(label="Outils"')


def test_latei_package_preflight_and_summary_report_expected_artifacts(tmp_path: Path) -> None:
    result = SimpleNamespace(
        latei_body_path=tmp_path / "book.latei_body.tex",
        latei_main_path=tmp_path / "book.latei_main.tex",
        latei_macros_path=tmp_path / "book.latei_macros.tex",
        latei_graphics_map_path=tmp_path / "book.latei_graphics_map.tex",
        latei_assets_dir=tmp_path / "latei_assets",
        latei_copied_images_count=2,
        latei_asset_warnings=["Image not found for LaTEI package: missing.jpg"],
        latei_pdf_path=tmp_path / "book.latei.pdf",
        latei_log_path=tmp_path / "book.latei_build.log",
        latei_pdf_success=False,
        latei_pdf_message="LaTeX engine not found: lualatex",
        roundtrip_xml_path=tmp_path / "book.roundtrip.xml",
        diagnostics_path=tmp_path / "book.roundtrip_diagnostics.txt",
        diagnostics_count=0,
    )
    for path in [
        result.latei_body_path,
        result.latei_main_path,
        result.latei_macros_path,
        result.latei_graphics_map_path,
        result.latei_log_path,
        result.roundtrip_xml_path,
        result.diagnostics_path,
    ]:
        path.write_text("ok", encoding="utf-8")
    result.latei_assets_dir.mkdir()

    assert missing_latei_package_artifacts(result) == []

    summary = format_latei_export_summary(result)
    assert "Export LaTEI terminé." in summary
    assert f"Corps réversible : {result.latei_body_path}" in summary
    assert f"Driver : {result.latei_main_path}" in summary
    assert f"Macros locales : {result.latei_macros_path}" in summary
    assert f"Mapping images : {result.latei_graphics_map_path}" in summary
    assert "Images copiées : 2" in summary
    assert "Warnings images : 1" in summary
    assert "PDF LaTEI : non produit (LaTeX engine not found: lualatex)" in summary
    assert f"XML restauré : {result.roundtrip_xml_path}" in summary
    assert "Diagnostics round-trip : 0" in summary
    assert "Prévol paquet LaTEI : tous les artefacts attendus sont présents." in summary
