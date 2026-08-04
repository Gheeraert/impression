from __future__ import annotations

"""Référentiel PURH v0.6 §10 (P0 item 6, "restaurer ou diagnostiquer les
images") : chaque figure doit posséder soit une ressource résolue, soit un
statut explicite d'absence accepté — jamais d'attente silencieuse. Si la TEI
ne contient que la légende sans `graphic`, le déficit doit être diagnostiqué
en amont (§10.3). Ce module ne fait que signaler, jamais réparer : les
images de test ci-dessous sont de simples PNG 1x1 factices, jamais extraites
d'un PDF imprimeur (interdit par le référentiel)."""

import struct
import zlib
from pathlib import Path

from lxml import etree

from purh_site.latei_image_validation import validate_latei_images
from purh_site.reversible_integration import run_reversible_export_for_file


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


def _parse(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


def test_figure_without_graphic_is_diagnosed() -> None:
    root = _parse(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
        '<figure xml:id="fig1"><head>Titre</head><p rend="caption">Légende sans image.</p></figure>'
        "</body></text></TEI>"
    )
    diagnostics = validate_latei_images(root, source_xml_path=Path("book.xml"))

    codes = [d.code for d in diagnostics]
    assert "FIGURE_WITHOUT_GRAPHIC" in codes
    diag = next(d for d in diagnostics if d.code == "FIGURE_WITHOUT_GRAPHIC")
    assert diag.path == "figure/fig1"


def test_graphic_without_locator_is_diagnosed() -> None:
    root = _parse(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
        '<figure xml:id="fig1"><graphic/></figure>'
        "</body></text></TEI>"
    )
    diagnostics = validate_latei_images(root, source_xml_path=Path("book.xml"))

    assert any(d.code == "GRAPHIC_WITHOUT_LOCATOR" for d in diagnostics)


def test_missing_image_resource_is_diagnosed(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    root = _parse(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
        '<figure xml:id="fig1"><graphic url="icono/absente.jpg"/></figure>'
        "</body></text></TEI>"
    )
    diagnostics = validate_latei_images(root, source_xml_path=xml_path)

    codes = [d.code for d in diagnostics]
    assert "IMAGE_RESOURCE_NOT_FOUND" in codes
    diag = next(d for d in diagnostics if d.code == "IMAGE_RESOURCE_NOT_FOUND")
    assert "icono/absente.jpg" in diag.message


def test_resolved_image_resource_raises_no_diagnostic(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    image_dir = tmp_path / "icono"
    image_dir.mkdir()
    (image_dir / "presente.png").write_bytes(_png_1x1())
    root = _parse(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
        '<figure xml:id="fig1"><graphic url="icono/presente.png"/></figure>'
        "</body></text></TEI>"
    )
    diagnostics = validate_latei_images(root, source_xml_path=xml_path)

    assert diagnostics == []


def test_validation_does_not_mutate_the_tree(tmp_path: Path) -> None:
    root = _parse(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
        '<figure xml:id="fig1"><p rend="caption">Sans image.</p></figure>'
        "</body></text></TEI>"
    )
    before = etree.tostring(root)
    validate_latei_images(root, source_xml_path=tmp_path / "book.xml")

    assert etree.tostring(root) == before


def test_export_writes_image_diagnostics_without_failing_the_build(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    image_dir = tmp_path / "icono"
    image_dir.mkdir()
    (image_dir / "presente.png").write_bytes(_png_1x1())
    xml_path.write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Livre</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text><body>
    <figure xml:id="fig_ok"><graphic url="icono/presente.png"/><p rend="caption">Légende avec image.</p></figure>
    <figure xml:id="fig_manquante"><p rend="caption">Légende seule, aucune graphic.</p></figure>
  </body></text>
</TEI>""",
        encoding="utf-8",
    )
    result = run_reversible_export_for_file(xml_path, tmp_path / "out", compile_pdf=False)

    assert result.image_diagnostics_count == 1
    assert result.image_diagnostics_path.exists()
    content = result.image_diagnostics_path.read_text(encoding="utf-8")
    assert "FIGURE_WITHOUT_GRAPHIC" in content
    assert "fig_manquante" in content
    assert "fig_ok" not in content
    # Image diagnostics are a separate, non-blocking channel: the
    # round-trip export itself is unaffected by an unresolved image.
    assert result.success is True
    assert result.diagnostics_count == 0
