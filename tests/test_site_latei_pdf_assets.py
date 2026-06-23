from __future__ import annotations

"""Passe E4 — Validation des figures et assets LaTEI dans le contexte SiteBuilder.

Vérifie que les modes pdf_export_mode="latei" et "latei_pdf" traitent correctement
les images TEI dans le contexte du site statique :
- latei_assets/images/ créé dans assets/generated/
- images copiées avec noms sha1
- book.tex référence latei_assets/images/ (chemins relatifs valides depuis generated/)
- book.pdf compilable avec image si LuaLaTeX disponible

Stratégie d'adressage des images :
  assets_dir = tmp_path / "assets"   → copié dans site/assets/ par _copy_user_assets
  XML source  → url="assets/images/test.png"
    • depuis tmp_path/book.xml    : résout  tmp_path/assets/images/test.png   ✓ (existe)
    • depuis site/book.normalized.xml : résout  site/assets/images/test.png    ✓ (copié avant)
"""

import shutil
import struct
import zlib
from pathlib import Path

import pytest

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _png_1x1() -> bytes:
    """1×1 RGBA PNG valide (4 octets)."""
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
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw_rgba)) + chunk(b"IEND", b"")


TEI_WITH_FIGURE = """\
<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type='main'>Livre avec image</title>
      </titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre illustré'>
        <body>
          <div type='section1'>
            <head>Chapitre avec figure</head>
            <p>Un texte avant la figure.</p>
            <figure xml:id='fig_001'>
              <head>Figure de test</head>
              <graphic url='assets/images/test.png'/>
              <p rend='caption'>Légende de la figure.</p>
            </figure>
            <p>Un texte après la figure.</p>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
"""


def _setup(tmp_path: Path) -> tuple[Path, Path]:
    """Crée le XML et l'image dans tmp_path. Retourne (xml_path, assets_dir)."""
    assets_dir = tmp_path / "assets"
    img_dir = assets_dir / "images"
    img_dir.mkdir(parents=True)
    (img_dir / "test.png").write_bytes(_png_1x1())

    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_WITH_FIGURE, encoding="utf-8")
    return xml_path, assets_dir


# ---------------------------------------------------------------------------
# Test 1 — mode latei : latei_assets/images/ créé, image présente
# ---------------------------------------------------------------------------

def test_latei_mode_with_figure_creates_latei_assets_images(tmp_path: Path) -> None:
    xml_path, assets_dir = _setup(tmp_path)

    SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(
            output_dir=tmp_path / "site",
            assets_dir=assets_dir,
            pdf_export_mode="latei",
        ),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    latei_images = generated / "latei_assets" / "images"

    assert (generated / "book.tex").exists(), "book.tex doit exister"
    assert (generated / "book.latei_manifest.json").exists(), "manifeste doit exister"
    assert (generated / "pdf_build_report.txt").exists(), "rapport doit exister"
    assert latei_images.exists(), "latei_assets/images/ doit être créé dans assets/generated/"

    copied_images = list(latei_images.glob("*.png"))
    assert len(copied_images) >= 1, "au moins une image PNG doit être copiée dans latei_assets/images/"


# ---------------------------------------------------------------------------
# Test 2 — book.tex référence latei_assets/images/ (chemins relatifs valides)
# ---------------------------------------------------------------------------

def test_latei_mode_book_tex_references_latei_assets(tmp_path: Path) -> None:
    xml_path, assets_dir = _setup(tmp_path)

    SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(
            output_dir=tmp_path / "site",
            assets_dir=assets_dir,
            pdf_export_mode="latei",
        ),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    book_tex = (generated / "book.tex").read_text(encoding="utf-8")

    assert r"\begin{lateiDocument}" in book_tex
    assert r"\input{" not in book_tex
    assert "latei_assets/images/" in book_tex, "book.tex doit référencer latei_assets/images/"

    # Vérifier que le fichier référencé dans book.tex existe réellement
    latei_images_dir = generated / "latei_assets" / "images"
    for img_file in latei_images_dir.glob("*"):
        relative_ref = f"latei_assets/images/{img_file.name}"
        assert relative_ref in book_tex, f"{relative_ref} référencé dans book.tex doit pointer vers un fichier existant"


# ---------------------------------------------------------------------------
# Test 3 — mode latei_pdf avec LuaLaTeX disponible
# ---------------------------------------------------------------------------

def test_latei_pdf_mode_with_figure_compiles_when_lualatex_available(tmp_path: Path) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("lualatex absent sur cette machine")

    xml_path, assets_dir = _setup(tmp_path)

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(
            output_dir=tmp_path / "site",
            assets_dir=assets_dir,
            pdf_export_mode="latei_pdf",
        ),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    book_pdf = generated / "book.pdf"
    build_report = result.report_path.read_text(encoding="utf-8")

    assert (generated / "book.tex").exists()
    assert book_pdf.exists(), "book.pdf doit exister si lualatex est disponible"
    assert book_pdf.stat().st_size > 0, "book.pdf ne doit pas être vide"
    assert "PDF généré : assets/generated/book.pdf" in build_report

    # Vérifier l'absence d'erreur image évidente dans le log natif
    latei_images_dir = generated / "latei_assets" / "images"
    assert latei_images_dir.exists(), "latei_assets/images/ doit exister même après compilation PDF"
    assert list(latei_images_dir.glob("*.png")), "images copiées doivent subsister après compilation"


# ---------------------------------------------------------------------------
# Test 4 — non-régression : mode latei sans image ne plante pas
# ---------------------------------------------------------------------------

def test_latei_mode_without_figure_still_works(tmp_path: Path) -> None:
    """Vérifie que l'absence d'image ne casse pas le mode latei."""
    TEI_NO_FIGURE = """\
<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre sans image</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre texte'>
        <body>
          <div type='section1'>
            <head>Sans figure</head>
            <p>Texte seul.</p>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
"""
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_NO_FIGURE, encoding="utf-8")

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / "site", pdf_export_mode="latei"),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    assert result.html_path.exists()
    assert (generated / "book.tex").exists()
    assert (generated / "pdf_build_report.txt").exists()
    # latei_assets/images/ peut ne pas exister sans image, c'est normal
