from __future__ import annotations

"""Tests fonctionnels pour la génération du manifeste des ressources (assets/metadata/manifest.json).

Catégories vérifiées :
- génération systématique du manifeste
- structure JSON valide (version, clés attendues)
- images référencées par le XML → entrée declared_by="xml"
- image manquante → avertissement dans le manifeste
- PDF éditeur (assets/pdf/) → entrée declared_by="dialog", role="editor_pdf"
- PDF LaTEI (mode latei) → entrée declared_by="generator", role="latei_pdf"
- priorité PDF éditeur : désactive la génération LaTEI
- absence de téléchargements quand aucun PDF n'est fourni
"""

import json
import struct
import zlib
from pathlib import Path

import pytest

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder

# ---------------------------------------------------------------------------
# Helpers partagés
# ---------------------------------------------------------------------------

def _png_1x1() -> bytes:
    """1×1 RGBA PNG valide."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    raw_rgba = b"\x00\xff\xff\xff\xff"
    return (
        signature
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw_rgba))
        + chunk(b"IEND", b"")
    )


def _minimal_tei(with_graphic: bool = False, graphic_url: str = "assets/images/fig_001.png") -> str:
    graphic_block = f"""
        <figure xml:id="fig1">
          <head>Illustration</head>
          <graphic url="{graphic_url}"/>
        </figure>""" if with_graphic else ""
    return f"""\
<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Test manifeste</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre test'>
        <body>
          <div type='section1'>
            <head>Titre test</head>
            <p>Contenu de test.</p>{graphic_block}
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
"""


def _build_site(tmp_path: Path, tei: str, **config_kwargs) -> tuple[Path, dict]:
    """Construit un site et retourne (output_dir, manifest_data)."""
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(tei, encoding="utf-8")

    output_dir = tmp_path / "site"
    config = BuildConfig(output_dir=output_dir, **config_kwargs)
    SiteBuilder().build_from_master(xml_path, config)

    manifest_path = output_dir / "assets" / "metadata" / "manifest.json"
    assert manifest_path.exists(), "assets/metadata/manifest.json doit toujours être généré"
    return output_dir, json.loads(manifest_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Test 1 — le manifeste est toujours généré
# ---------------------------------------------------------------------------

def test_manifest_is_always_generated(tmp_path: Path) -> None:
    output_dir, data = _build_site(tmp_path, _minimal_tei())
    manifest_path = output_dir / "assets" / "metadata" / "manifest.json"
    assert manifest_path.exists()
    assert manifest_path.stat().st_size > 0


# ---------------------------------------------------------------------------
# Test 2 — structure JSON valide
# ---------------------------------------------------------------------------

def test_manifest_has_valid_structure(tmp_path: Path) -> None:
    _, data = _build_site(tmp_path, _minimal_tei())
    assert data["version"] == 1
    for key in ("images", "covers", "downloads", "static", "warnings"):
        assert key in data, f"Clé manquante dans le manifeste : {key}"
        assert isinstance(data[key], list), f"{key} doit être une liste"


# ---------------------------------------------------------------------------
# Test 3 — ressources statiques générateur toujours présentes
# ---------------------------------------------------------------------------

def test_manifest_always_contains_static_resources(tmp_path: Path) -> None:
    _, data = _build_site(tmp_path, _minimal_tei())
    outputs = {e["output"] for e in data["static"]}
    assert "assets/site.css" in outputs
    assert "assets/app.js" in outputs
    assert "assets/metadata/manifest.json" in outputs
    for entry in data["static"]:
        assert entry["declared_by"] == "generator"


# ---------------------------------------------------------------------------
# Test 4 — image référencée par le XML → entrée declared_by="xml"
# ---------------------------------------------------------------------------

def test_manifest_includes_xml_referenced_image(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    (assets_dir / "images").mkdir(parents=True)
    (assets_dir / "images" / "fig_001.png").write_bytes(_png_1x1())

    _, data = _build_site(
        tmp_path,
        _minimal_tei(with_graphic=True, graphic_url="assets/images/fig_001.png"),
        assets_dir=assets_dir,
    )

    assert len(data["images"]) >= 1
    entry = data["images"][0]
    assert entry["declared_by"] == "xml"
    assert entry["role"] == "image"
    assert entry["output"] == "assets/images/fig_001.png"
    assert entry.get("source") == "assets/images/fig_001.png"


# ---------------------------------------------------------------------------
# Test 5 — image absente → avertissement dans le manifeste
# ---------------------------------------------------------------------------

def test_manifest_warns_on_missing_xml_image(tmp_path: Path) -> None:
    _, data = _build_site(
        tmp_path,
        _minimal_tei(with_graphic=True, graphic_url="assets/images/introuvable.png"),
    )

    assert len(data["images"]) == 0, "Aucune entrée image ne doit être ajoutée si le fichier est absent"
    assert any("introuvable.png" in w for w in data["warnings"]), (
        "Un avertissement doit signaler l'image manquante"
    )


# ---------------------------------------------------------------------------
# Test 6 — image sans préfixe assets/ → résolue sous assets/images/
# ---------------------------------------------------------------------------

def test_manifest_image_without_assets_prefix(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    (assets_dir / "images").mkdir(parents=True)
    (assets_dir / "images" / "fig_002.png").write_bytes(_png_1x1())

    _, data = _build_site(
        tmp_path,
        _minimal_tei(with_graphic=True, graphic_url="fig_002.png"),
        assets_dir=assets_dir,
    )

    assert any(e["output"] == "assets/images/fig_002.png" for e in data["images"]), (
        "Une URL sans préfixe assets/ doit être résolue sous assets/images/"
    )


# ---------------------------------------------------------------------------
# Test 7 — PDF éditeur déclaré dans la boîte de dialogue
# ---------------------------------------------------------------------------

def test_manifest_includes_editor_pdf(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    pdf_dir = assets_dir / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "mon-livre.pdf").write_bytes(b"%PDF-1.4 %%EOF")

    _, data = _build_site(tmp_path, _minimal_tei(), assets_dir=assets_dir)

    editor_entries = [e for e in data["downloads"] if e["role"] == "editor_pdf"]
    assert len(editor_entries) == 1
    entry = editor_entries[0]
    assert entry["declared_by"] == "dialog"
    assert "pdf" in entry["output"].lower()


# ---------------------------------------------------------------------------
# Test 8 — PDF LaTEI généré (mode latei) → entrée declared_by="generator"
# ---------------------------------------------------------------------------

def test_manifest_includes_latei_pdf_when_generated(tmp_path: Path) -> None:
    output_dir, data = _build_site(tmp_path, _minimal_tei(), pdf_export_mode="latei")

    generated_dir = output_dir / "assets" / "generated"
    if not (generated_dir / "book.pdf").exists():
        pytest.skip("book.pdf non généré (lualatex absent)")

    latei_entries = [e for e in data["downloads"] if e["role"] == "latei_pdf"]
    assert len(latei_entries) == 1
    assert latei_entries[0]["declared_by"] == "generator"
    assert latei_entries[0]["output"] == "assets/generated/book.pdf"


# ---------------------------------------------------------------------------
# Test 9 — PDF éditeur désactive la génération LaTEI (règle de priorité)
# ---------------------------------------------------------------------------

def test_manifest_editor_pdf_disables_latei_generation(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    pdf_dir = assets_dir / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "editeur.pdf").write_bytes(b"%PDF-1.4 %%EOF")

    output_dir, data = _build_site(
        tmp_path,
        _minimal_tei(),
        assets_dir=assets_dir,
        pdf_export_mode="latei_pdf",
    )

    editor_entries = [e for e in data["downloads"] if e["role"] == "editor_pdf"]
    latei_entries = [e for e in data["downloads"] if e["role"] == "latei_pdf"]

    assert len(editor_entries) == 1, "Le PDF éditeur doit apparaître dans le manifeste"
    assert len(latei_entries) == 0, (
        "La génération LaTEI doit être désactivée quand un PDF éditeur est présent"
    )
    assert not (output_dir / "assets" / "generated" / "book.pdf").exists(), (
        "book.pdf ne doit pas être généré quand un PDF éditeur est disponible"
    )


# ---------------------------------------------------------------------------
# Test 10 — aucun PDF : liste downloads vide
# ---------------------------------------------------------------------------

def test_manifest_no_pdf_means_empty_downloads(tmp_path: Path) -> None:
    _, data = _build_site(tmp_path, _minimal_tei(), pdf_export_mode="none")
    assert data["downloads"] == [], (
        "La liste downloads doit être vide quand aucun PDF n'est fourni ni généré"
    )


# ---------------------------------------------------------------------------
# Test 11 — pas de dossier assets/pdf/ si aucun PDF éditeur fourni
# ---------------------------------------------------------------------------

def test_no_pdf_folder_when_no_editor_pdf_provided(tmp_path: Path) -> None:
    output_dir, _ = _build_site(tmp_path, _minimal_tei())
    assert not (output_dir / "assets" / "pdf").exists(), (
        "Le dossier assets/pdf/ ne doit pas exister si aucun PDF éditeur n'est fourni"
    )


# ---------------------------------------------------------------------------
# Test 12 — rapport de build mentionne le manifeste
# ---------------------------------------------------------------------------

def test_build_report_mentions_manifest(tmp_path: Path) -> None:
    output_dir, _ = _build_site(tmp_path, _minimal_tei())
    report = (output_dir / "build_report.txt").read_text(encoding="utf-8")
    assert "manifest.json" in report


# ---------------------------------------------------------------------------
# Test 13 — rapport mentionne image manquante
# ---------------------------------------------------------------------------

def test_build_report_warns_on_missing_image(tmp_path: Path) -> None:
    output_dir, _ = _build_site(
        tmp_path,
        _minimal_tei(with_graphic=True, graphic_url="assets/images/fantome.png"),
    )
    report = (output_dir / "build_report.txt").read_text(encoding="utf-8")
    assert "fantome.png" in report
    assert "RESSOURCE MANQUANTE" in report
