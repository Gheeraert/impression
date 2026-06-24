from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from purh_site.config import BuildConfig
from purh_site.gui import (
    format_latei_export_summary,
    latei_monofile_restored_stem,
    missing_latei_package_artifacts,
)


def test_gui_labels_use_latei_vocabulary() -> None:
    source = Path("purh_site/gui.py").read_text(encoding="utf-8")

    assert "Export LaTEI / PDF PURH" in source
    assert "Aucun export PDF/LaTeX" in source
    assert "LaTEI monofichier (.tex)" in source
    assert "LaTEI monofichier + PDF" in source
    assert "Exporter un paquet LaTEI depuis un XML" in source
    assert "Restaurer un XML Métopes depuis un corps LaTEI" in source
    assert "Le paquet LaTEI contient le corps réversible" in source
    assert "Mode d’emploi LaTEI" in source
    assert "À corriger" in source
    assert "À compiler" in source
    assert "À restaurer en XML" in source
    assert "*.latei.tex" in source
    assert "*.latei_body.tex" in source
    assert "*.latei_main.tex" in source
    assert "*.latei_body.tex ne compile pas seul" in source
    assert "*.latei_macros.tex" in source
    assert "*.latei_graphics_map.tex" in source
    assert "latei_assets/" in source

    assert "Sorties PDF / LaTeX" not in source
    assert "Générer le LaTeX seul" not in source
    assert "Générer le LaTeX + PDF" not in source
    assert "Tester la réversibilité TEI ↔ LaTeX" not in source
    assert "Exporter un paquet LaTEI réversible" not in source
    assert 'add_cascade(label="Outils"' in source
    assert source.index("Exporter un paquet LaTEI depuis un XML") < source.index('add_cascade(label="Outils"')
    assert source.index("Restaurer un XML Métopes depuis un corps LaTEI") < source.index('add_cascade(label="Outils"')


def test_gui_exposes_monofile_restore_action() -> None:
    source = Path("purh_site/gui.py").read_text(encoding="utf-8")

    assert "Restaurer un XML Métopes depuis un monofichier LaTEI" in source
    assert "restore_xml_from_latei_monofile" in source
    assert "*.latei.tex" in source
    assert source.index("Restaurer un XML Métopes depuis un monofichier LaTEI") < source.index(
        "Restaurer un XML Métopes depuis un corps LaTEI"
    )
    assert source.index("Restaurer un XML Métopes depuis un monofichier LaTEI") < source.index(
        'add_cascade(label="Outils"'
    )


def test_latei_usage_help_documents_monofile_restore() -> None:
    source = Path("purh_site/gui.py").read_text(encoding="utf-8")

    assert "Restaurer un XML Métopes depuis un monofichier LaTEI" in source
    assert "Ancien format fragmenté (debug/legacy)" in source
    assert "Pour restaurer un XML Métopes après corrections" in source


def test_latei_monofile_restored_stem_strips_latei_suffix() -> None:
    assert latei_monofile_restored_stem(Path("book.latei.tex")) == "book"
    assert latei_monofile_restored_stem(Path("mon_livre.latei.tex")) == "mon_livre"
    assert latei_monofile_restored_stem(Path("notes.tex")) == "notes"


def test_latei_package_preflight_and_summary_report_expected_artifacts(tmp_path: Path) -> None:
    result = SimpleNamespace(
        latei_monofile_path=tmp_path / "book.latei.tex",
        latei_monofile_pdf_path=tmp_path / "book.latei_mono.pdf",
        latei_monofile_pdf_success=False,
        latei_monofile_pdf_message="LuaLaTeX non disponible",
        primary_latei_path=tmp_path / "book.latei.tex",
        primary_pdf_path=tmp_path / "book.latei_mono.pdf",
        manifest_path=tmp_path / "book.latei_manifest.json",
        latei_body_path=tmp_path / "book.latei_body.tex",
        latei_main_path=tmp_path / "book.latei_main.tex",
        latei_macros_path=tmp_path / "book.latei_macros.tex",
        latei_graphics_map_path=tmp_path / "book.latei_graphics_map.tex",
        latei_running_titles_map_path=tmp_path / "book.latei_running_titles_map.tex",
        latei_assets_dir=tmp_path / "latei_assets",
        latei_copied_images_count=2,
        latei_short_running_titles_count=3,
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
        result.latei_monofile_path,
        result.manifest_path,
        result.latei_body_path,
        result.latei_main_path,
        result.latei_macros_path,
        result.latei_graphics_map_path,
        result.latei_running_titles_map_path,
        result.latei_log_path,
        result.roundtrip_xml_path,
        result.diagnostics_path,
    ]:
        path.write_text("ok", encoding="utf-8")
    result.latei_assets_dir.mkdir()

    assert missing_latei_package_artifacts(result) == []

    summary = format_latei_export_summary(result)
    assert "Export LaTEI terminé." in summary
    assert f"À corriger : {result.primary_latei_path}" in summary
    assert f"À compiler : {result.primary_latei_path}" in summary
    assert f"À restaurer en XML : {result.primary_latei_path}" in summary
    assert f"Fichier LaTEI éditable : {result.primary_latei_path}" in summary
    assert f"Manifeste : {result.manifest_path}" in summary
    assert "Fragments debug :" in summary
    assert f"Corps réversible à corriger : {result.latei_body_path}" in summary
    assert f"Driver compilable : {result.latei_main_path}" in summary
    assert f"Macros locales : {result.latei_macros_path}" in summary
    assert f"Mapping images : {result.latei_graphics_map_path}" in summary
    assert f"Mapping titres courants : {result.latei_running_titles_map_path}" in summary
    assert "Titres courants abrégés : 3" in summary
    assert "Images copiées : 2" in summary
    assert "Warnings images : 1" in summary
    assert "PDF LaTEI (debug) : non produit (LaTeX engine not found: lualatex)" in summary
    assert f"XML restauré : {result.roundtrip_xml_path}" in summary
    assert "Diagnostics round-trip : 0" in summary
    assert "Prévol paquet LaTEI : tous les artefacts attendus sont présents." in summary


# ---------------------------------------------------------------------------
# Tests E3 — exposition des modes LaTEI dans le GUI
# ---------------------------------------------------------------------------

def test_gui_exposes_latei_pdf_mode_values() -> None:
    source = Path("purh_site/gui.py").read_text(encoding="utf-8")
    assert '"latei"' in source, 'la valeur "latei" doit être dans le source du GUI'
    assert '"latei_pdf"' in source, 'la valeur "latei_pdf" doit être dans le source du GUI'


def test_gui_only_three_pdf_modes_present() -> None:
    source = Path("purh_site/gui.py").read_text(encoding="utf-8")
    for mode in ('"none"', '"latei"', '"latei_pdf"'):
        assert mode in source, f"le mode {mode} doit apparaître dans le source du GUI"
    assert '"latex"' not in source, 'le mode "latex" ne doit plus apparaître dans le GUI (passe E6)'
    assert '"latex_pdf"' not in source, 'le mode "latex_pdf" ne doit plus apparaître dans le GUI (passe E6)'


def test_gui_old_modes_not_offered() -> None:
    source = Path("purh_site/gui.py").read_text(encoding="utf-8")
    assert "Chaîne stable (legacy)" not in source
    assert "Chaîne LaTEI monofichier" not in source
    assert "PDF stable" not in source
    assert "ancienne chaîne" not in source


def test_build_config_accepts_latei_mode() -> None:
    config = BuildConfig(output_dir=Path("."), pdf_export_mode="latei")
    assert config.pdf_export_mode == "latei"


def test_build_config_accepts_latei_pdf_mode() -> None:
    config = BuildConfig(output_dir=Path("."), pdf_export_mode="latei_pdf")
    assert config.pdf_export_mode == "latei_pdf"
