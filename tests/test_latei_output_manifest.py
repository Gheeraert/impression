from __future__ import annotations

import json
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file


TEI_NS = "http://www.tei-c.org/ns/1.0"

MINI_XML = f"""<TEI xmlns="{TEI_NS}">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Test manifeste</title></titleStmt>
      <publicationStmt><p>Pub test</p></publicationStmt>
      <sourceDesc><p>Src test</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="chapter" xml:id="ch1">
        <head>Titre</head>
        <p>Contenu.</p>
      </div>
    </body>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def manifest_result(tmp_path_factory: pytest.TempPathFactory):
    out = tmp_path_factory.mktemp("manifest_out")
    xml_path = out / "mini.xml"
    xml_path.write_text(MINI_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, out / "export")


@pytest.fixture(scope="module")
def manifest_data(manifest_result):
    return json.loads(manifest_result.manifest_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Test 1 — manifeste créé
# ---------------------------------------------------------------------------

def test_manifest_file_is_created(manifest_result) -> None:
    assert manifest_result.manifest_path.exists()
    assert manifest_result.manifest_path.stat().st_size > 0
    assert manifest_result.manifest_path.suffix == ".json"


def test_manifest_is_valid_json(manifest_result) -> None:
    data = json.loads(manifest_result.manifest_path.read_text(encoding="utf-8"))
    assert data["version"] == 1


# ---------------------------------------------------------------------------
# Test 2 — monofichier déclaré comme primary
# ---------------------------------------------------------------------------

def test_manifest_primary_latei_matches_primary_latei_path(manifest_result, manifest_data) -> None:
    manifest_dir = manifest_result.manifest_path.parent
    declared = (manifest_dir / manifest_data["primary"]["latei"]).resolve()
    assert declared == manifest_result.primary_latei_path.resolve()


def test_manifest_primary_latei_ends_with_latei_tex(manifest_data) -> None:
    assert manifest_data["primary"]["latei"].endswith(".latei.tex")


def test_manifest_xml_restore_supported_is_true(manifest_data) -> None:
    assert manifest_data["primary"]["xml_restore_supported"] is True


def test_primary_latei_path_property_is_monofile(manifest_result) -> None:
    assert manifest_result.primary_latei_path == manifest_result.latei_monofile_path


def test_primary_pdf_path_property_is_monofile_pdf(manifest_result) -> None:
    assert manifest_result.primary_pdf_path == manifest_result.latei_monofile_pdf_path


# ---------------------------------------------------------------------------
# Test 3 — fragments déclarés comme debug et existants
# ---------------------------------------------------------------------------

def test_manifest_debug_keys_all_present(manifest_data) -> None:
    debug = manifest_data["debug"]
    for key in ("latei_body", "latei_main", "latei_macros", "graphics_map", "running_titles_map"):
        assert key in debug, f"Missing debug key: {key}"


def test_manifest_debug_files_exist(manifest_result, manifest_data) -> None:
    manifest_dir = manifest_result.manifest_path.parent
    for key in ("latei_body", "latei_main", "latei_macros", "graphics_map", "running_titles_map"):
        path = (manifest_dir / manifest_data["debug"][key]).resolve()
        assert path.exists(), f"Debug file declared in manifest but missing on disk: {key} → {path}"


def test_debug_latei_paths_property_matches_individual_fields(manifest_result) -> None:
    debug = manifest_result.debug_latei_paths
    assert manifest_result.latei_body_path in debug
    assert manifest_result.latei_main_path in debug
    assert manifest_result.latei_macros_path in debug
    assert manifest_result.latei_graphics_map_path in debug
    assert manifest_result.latei_running_titles_map_path in debug


# ---------------------------------------------------------------------------
# Test 4 — messages PDF présents même sans LuaLaTeX
# ---------------------------------------------------------------------------

def test_manifest_pdf_messages_always_present(manifest_data) -> None:
    messages = manifest_data["messages"]
    assert "latei_pdf" in messages
    assert "latei_monofile_pdf" in messages
    assert isinstance(messages["latei_pdf"], str)
    assert isinstance(messages["latei_monofile_pdf"], str)
    assert len(messages["latei_pdf"]) > 0
    assert len(messages["latei_monofile_pdf"]) > 0


def test_manifest_roundtrip_diagnostics_count_is_integer(manifest_data) -> None:
    assert isinstance(manifest_data["roundtrip"]["diagnostics_count"], int)


# ---------------------------------------------------------------------------
# Test 5 — early return sur XML absent
# ---------------------------------------------------------------------------

def test_manifest_written_on_missing_xml(tmp_path: Path) -> None:
    result = run_reversible_export_for_file(
        tmp_path / "does_not_exist.xml",
        tmp_path / "out",
    )
    assert not result.success
    assert result.manifest_path.exists()
    data = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert "error" in data
    assert "primary" in data
    assert data["primary"]["xml_restore_supported"] is False
    assert data["roundtrip"]["diagnostics_count"] == result.diagnostics_count
    assert data["messages"]["latei_pdf"] == "not produced"
    assert data["messages"]["latei_monofile_pdf"] == "not produced"
