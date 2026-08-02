"""Construction du manifeste des ressources (assets/metadata/manifest.json).

Voir docs/ASSETS.md pour la spécification complète des trois catégories de
ressources (xml / dialog / generator) et la structure du manifeste.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from lxml import etree

from .asset_manifest import AssetManifest, ManifestEntry
from .utils import NSMAP

if TYPE_CHECKING:
    from .site_builder import PdfSiteArtifacts, ThemeAssets

MANIFEST_RELATIVE_PATH = "assets/metadata/manifest.json"

_ABSOLUTE_OR_EXTERNAL_PREFIXES = ("assets/", "/", "data:")


def _resolve_image_output(url: str) -> str:
    """Reproduit exactement la règle de resolved-asset-src dans tei_to_html.xsl.

    "assets/images" est préfixé normalement, sauf si l'URL répète déjà
    littéralement le segment "images/" (ex. url="images/fig.jpg"), auquel
    cas ce segment n'est pas dupliqué. Les chemins du type
    "../autre-dossier/fig.jpg", destinés à naviguer depuis assets/images
    vers un dossier voisin sous assets/, restent inchangés.
    """

    if "://" in url or url.startswith(_ABSOLUTE_OR_EXTERNAL_PREFIXES):
        return url
    if url.startswith("images/"):
        return f"assets/{url}"
    return f"assets/images/{url}"


def _collect_xml_images(
    output_dir: Path,
    tree: etree._ElementTree,
) -> tuple[list[ManifestEntry], list[str]]:
    entries: list[ManifestEntry] = []
    missing: list[str] = []
    seen: set[str] = set()

    for graphic in tree.xpath("//tei:graphic[normalize-space(@url) != '']", namespaces=NSMAP):
        url = (graphic.get("url") or "").strip()
        output = _resolve_image_output(url)
        if output in seen:
            continue
        seen.add(output)
        if (output_dir / output).exists():
            entries.append(ManifestEntry(output=output, declared_by="xml", role="image", source=output))
        else:
            missing.append(output)

    return entries, missing


def build_asset_manifest(
    output_dir: Path,
    tree: etree._ElementTree,
    theme_assets: ThemeAssets,
    pdf_artifacts: PdfSiteArtifacts,
) -> AssetManifest:
    images, missing_images = _collect_xml_images(output_dir, tree)
    warnings = [f"Image introuvable : {output}" for output in missing_images]

    covers: list[ManifestEntry] = []
    if theme_assets.cover_href:
        covers.append(ManifestEntry(output=theme_assets.cover_href, declared_by="dialog", role="cover_front"))

    downloads: list[ManifestEntry] = []
    if theme_assets.pdf_href:
        downloads.append(ManifestEntry(output=theme_assets.pdf_href, declared_by="dialog", role="editor_pdf"))
    if pdf_artifacts.generated_pdf_href:
        downloads.append(
            ManifestEntry(output=pdf_artifacts.generated_pdf_href, declared_by="generator", role="latei_pdf")
        )

    static = [
        ManifestEntry(output="assets/site.css", declared_by="generator", role="css"),
        ManifestEntry(output="assets/app.js", declared_by="generator", role="js"),
        ManifestEntry(output=MANIFEST_RELATIVE_PATH, declared_by="generator", role="manifest"),
    ]

    return AssetManifest(images=images, covers=covers, downloads=downloads, static=static, warnings=warnings)


def write_asset_manifest(output_dir: Path, manifest: AssetManifest) -> list[str]:
    """Écrit le manifeste et retourne les lignes à ajouter au rapport de build."""

    manifest.write(output_dir / MANIFEST_RELATIVE_PATH)

    report_lines = [f"[RESSOURCE MANQUANTE] {warning}" for warning in manifest.warnings]
    report_lines.append(f"Manifeste des ressources généré : {MANIFEST_RELATIVE_PATH}")
    return report_lines
