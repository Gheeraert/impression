from __future__ import annotations

import shutil
import struct
import zlib
from pathlib import Path

import pytest
from lxml import etree

from purh_site.reversible import compare_tei_elements, read_latex_document, write_tei_element
from purh_site.reversible_integration import ReversibleExportResult, run_reversible_export_for_file

FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


def write_xml(path: Path, xml: str) -> Path:
    path.write_text(xml, encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def missing_figure_export(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    tmp_path = tmp_path_factory.mktemp("latei_direct_missing_figure")
    xml_path = write_xml(
        tmp_path / "figure.xml",
        '<figure xmlns="http://www.tei-c.org/ns/1.0" xml:id="fig_001">'
        "<head>Figure test</head>"
        '<graphic url="missing/path_with_spaces/figure_001.jpg"/>'
        '<p rend="caption">Une légende avec <hi rend="italic">italique</hi>.</p>'
        '<p rend="credits">Crédit image.</p>'
        "</figure>",
    )
    return run_reversible_export_for_file(xml_path, tmp_path)


@pytest.fixture(scope="module")
def existing_figure_export(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    tmp_path = tmp_path_factory.mktemp("latei_direct_existing_figure")
    image_dir = tmp_path / "icono"
    image_dir.mkdir()
    (image_dir / "test image_001.png").write_bytes(_png_1x1())
    xml_path = write_xml(
        tmp_path / "figure_existing.xml",
        '<figure xmlns="http://www.tei-c.org/ns/1.0" xml:id="fig_existing">'
        "<head>Figure avec image</head>"
        '<graphic url="icono/test image_001.png"/>'
        '<p rend="caption">Image locale copiée.</p>'
        "</figure>",
    )
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def _png_1x1() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    raw_rgba_scanline = b"\x00\xff\xff\xff\xff"
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw_rgba_scanline)) + chunk(b"IEND", b"")


@pytest.fixture(scope="module")
def fixture_export(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    output_dir = tmp_path_factory.mktemp("latei_direct_real_figures")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir)


def test_latei_direct_figure_body_remains_reversible(missing_figure_export: ReversibleExportResult) -> None:
    source = etree.parse(str(missing_figure_export.source_path)).getroot()
    body = missing_figure_export.latei_body_path.read_text(encoding="utf-8")
    emitted = write_tei_element(read_latex_document(body))

    assert missing_figure_export.success is True
    assert missing_figure_export.diagnostics_count == 0
    assert r"\begin{teiFigure}[xmlid={fig_001}]" in body
    assert r"\teiHead{Figure test}" in body
    assert r"\teiGraphic[url={missing/path\_with\_spaces/figure\_001.jpg}]" in body
    assert r"\teiP[rend={caption}]" in body
    assert r"\teiP[rend={credits}]" in body
    assert compare_tei_elements(source, emitted) == []


def test_latei_direct_existing_image_is_copied_and_mapped(
    existing_figure_export: ReversibleExportResult,
) -> None:
    body = existing_figure_export.latei_body_path.read_text(encoding="utf-8")
    main = existing_figure_export.latei_main_path.read_text(encoding="utf-8")
    graphics_map = existing_figure_export.latei_graphics_map_path.read_text(encoding="utf-8")
    copied_images = list((existing_figure_export.latei_assets_dir / "images").glob("*.png"))

    assert existing_figure_export.success is True
    assert existing_figure_export.diagnostics_count == 0
    assert existing_figure_export.latei_graphics_map_path.exists()
    assert existing_figure_export.latei_assets_dir.exists()
    assert existing_figure_export.latei_copied_images_count == 1
    assert existing_figure_export.latei_asset_warnings == []
    assert len(copied_images) == 1
    assert copied_images[0].read_bytes().startswith(b"\x89PNG")
    assert r"\teiGraphic[url={icono/test image\_001.png}]" in body
    assert r"\lateiDeclareGraphic{icono/test image\_001.png}" in graphics_map
    assert copied_images[0].relative_to(existing_figure_export.output_dir).as_posix() in graphics_map
    assert rf'\input{{"{existing_figure_export.latei_graphics_map_path.name}"}}' in main
    assert main.index(existing_figure_export.latei_macros_path.name) < main.index(existing_figure_export.latei_graphics_map_path.name)
    assert main.index(existing_figure_export.latei_graphics_map_path.name) < main.index(existing_figure_export.latei_body_path.name)


def test_latei_direct_existing_image_body_stays_reversible(
    existing_figure_export: ReversibleExportResult,
) -> None:
    source = etree.parse(str(existing_figure_export.source_path)).getroot()
    body = existing_figure_export.latei_body_path.read_text(encoding="utf-8")
    emitted = write_tei_element(read_latex_document(body))

    assert compare_tei_elements(source, emitted) == []


def test_latei_direct_existing_image_compiles_when_lualatex_is_available(
    existing_figure_export: ReversibleExportResult,
) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not existing_figure_export.latei_pdf_success:
        log = existing_figure_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:140])
        pytest.fail(f"Direct LaTEI figure sample did not compile with copied local image.\n{excerpt}")

    assert existing_figure_export.latei_pdf_path.exists()
    assert existing_figure_export.latei_pdf_path.stat().st_size > 0


def test_latei_direct_figure_macros_follow_stable_fallback_contract(
    missing_figure_export: ReversibleExportResult,
) -> None:
    macros = missing_figure_export.latei_macros_path.read_text(encoding="utf-8")

    assert r"\includegraphics" in macros
    assert r"\IfFileExists" in macros
    assert r"\detokenize" in macros
    assert r"\lateiDeclareGraphic" in macros
    assert "Image absente ou non fournie" in macros
    assert "url .tl_set:N" in macros
    assert "target .tl_set:N" in macros
    assert "n .tl_set:N" in macros
    assert r"\lateiSetHeadContext{figure}" in macros
    assert r"\IfStrEq{\lateiHeadContext}{figure}" in macros
    assert "rend={caption}" in macros
    assert "rend={credits}" in macros


def test_latei_direct_figure_with_missing_image_compiles_when_lualatex_is_available(
    missing_figure_export: ReversibleExportResult,
) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not missing_figure_export.latei_pdf_success:
        log = missing_figure_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:140])
        pytest.fail(f"Direct LaTEI figure sample did not compile with missing image fallback.\n{excerpt}")

    assert missing_figure_export.latei_pdf_path.exists()
    assert missing_figure_export.latei_pdf_path.stat().st_size > 0


@pytest.mark.full_book
def test_latei_direct_real_fixture_figures_still_round_trip_and_compile(
    fixture_export: ReversibleExportResult,
) -> None:
    body = fixture_export.latei_body_path.read_text(encoding="utf-8")

    assert fixture_export.success is True
    assert fixture_export.diagnostics_count == 0
    assert fixture_export.latei_graphics_map_path.exists()
    assert r"\begin{teiFigure}[xmlid={figure01}]" in body
    assert r"\teiGraphic[url={../icono/br/Ch02\_Doulkaridou/fig1.jpg}]" in body
    assert fixture_export.latei_copied_images_count >= 0

    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not fixture_export.latei_pdf_success:
        log = fixture_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:160])
        pytest.fail(f"Direct LaTEI PDF failed on the real Metopes fixture.\n{excerpt}")

    assert fixture_export.latei_pdf_path.exists()
    assert fixture_export.latei_pdf_path.stat().st_size > 0
