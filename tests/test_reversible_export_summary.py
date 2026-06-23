from __future__ import annotations

"""M6 — format_latei_export_summary places monofile first, fragments as debug."""

from pathlib import Path
from types import SimpleNamespace

from purh_site.gui import format_latei_export_summary


def _make_result(tmp_path: Path, *, with_primary: bool = True) -> SimpleNamespace:
    ns = SimpleNamespace(
        latei_body_path=tmp_path / "stem.latei_body.tex",
        latei_main_path=tmp_path / "stem.latei_main.tex",
        latei_macros_path=tmp_path / "stem.latei_macros.tex",
        latei_graphics_map_path=tmp_path / "stem.latei_graphics_map.tex",
        latei_running_titles_map_path=tmp_path / "stem.latei_running_titles_map.tex",
        latei_assets_dir=tmp_path / "latei_assets",
        latei_copied_images_count=0,
        latei_short_running_titles_count=0,
        latei_asset_warnings=[],
        latei_pdf_path=tmp_path / "stem.latei.pdf",
        latei_log_path=tmp_path / "stem.latei_build.log",
        latei_pdf_success=False,
        latei_pdf_message="lualatex absent",
        roundtrip_xml_path=tmp_path / "stem.roundtrip.xml",
        diagnostics_path=tmp_path / "stem.roundtrip_diagnostics.txt",
        diagnostics_count=0,
    )
    if with_primary:
        ns.primary_latei_path = tmp_path / "stem.latei.tex"
        ns.primary_pdf_path = tmp_path / "stem.latei_mono.pdf"
        ns.latei_monofile_path = tmp_path / "stem.latei.tex"
        ns.latei_monofile_pdf_path = tmp_path / "stem.latei_mono.pdf"
        ns.latei_monofile_pdf_success = False
        ns.latei_monofile_pdf_message = "lualatex absent"
        ns.manifest_path = tmp_path / "stem.latei_manifest.json"
    return ns


def test_summary_shows_primary_latei_first(tmp_path: Path) -> None:
    result = _make_result(tmp_path)
    summary = format_latei_export_summary(result, missing_artifacts=[])

    monofile_pos = summary.index(str(result.primary_latei_path))
    body_pos = summary.index(str(result.latei_body_path))
    assert monofile_pos < body_pos, "Monofile must appear before body fragment in summary"


def test_summary_body_not_labeled_as_primary(tmp_path: Path) -> None:
    result = _make_result(tmp_path)
    summary = format_latei_export_summary(result, missing_artifacts=[])

    assert f"Fichier LaTEI éditable : {result.primary_latei_path}" in summary
    assert f"Fichier LaTEI éditable : {result.latei_body_path}" not in summary


def test_summary_fragments_grouped_under_debug_header(tmp_path: Path) -> None:
    result = _make_result(tmp_path)
    summary = format_latei_export_summary(result, missing_artifacts=[])

    assert "Fragments debug :" in summary
    debug_pos = summary.index("Fragments debug :")
    body_pos = summary.index(str(result.latei_body_path))
    main_pos = summary.index(str(result.latei_main_path))
    assert debug_pos < body_pos
    assert debug_pos < main_pos


def test_summary_manifest_path_present(tmp_path: Path) -> None:
    result = _make_result(tmp_path)
    summary = format_latei_export_summary(result, missing_artifacts=[])

    assert f"Manifeste : {result.manifest_path}" in summary


def test_summary_pdf_debug_label(tmp_path: Path) -> None:
    result = _make_result(tmp_path)
    summary = format_latei_export_summary(result, missing_artifacts=[])

    assert "PDF LaTEI (debug) :" in summary
    assert "PDF LaTEI :" not in summary.replace("PDF LaTEI (debug) :", "")


def test_summary_without_primary_fields_still_works(tmp_path: Path) -> None:
    result = _make_result(tmp_path, with_primary=False)
    summary = format_latei_export_summary(result, missing_artifacts=[])

    assert "Export LaTEI terminé." in summary
    assert f"Corps réversible à corriger : {result.latei_body_path}" in summary
