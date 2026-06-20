from __future__ import annotations

"""Package image assets for the experimental direct LaTEI driver.

The reversible LaTEI body keeps the documentary TEI graphic attributes. This
module only creates compilation artifacts: copied local images and a TeX mapping
from documentary paths to local package paths.
"""

from dataclasses import dataclass, field
from hashlib import sha1
from pathlib import Path
import re
import shutil

from lxml import etree

from purh_site.reversible.latex_writer import escape_latex
from purh_site.utils import TEI_NS


NS = {"tei": TEI_NS}


@dataclass(slots=True)
class LateiGraphicMapping:
    documentary_path: str
    local_latex_path: str
    source_path: Path
    copied_path: Path


@dataclass(slots=True)
class LateiAssetPackage:
    assets_dir: Path
    graphics_map_path: Path
    mappings: list[LateiGraphicMapping] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def copied_count(self) -> int:
        return len(self.mappings)


def package_latei_graphics(
    root: etree._Element,
    *,
    source_xml_path: Path,
    output_dir: Path,
    graphics_map_path: Path,
) -> LateiAssetPackage:
    """Copy existing TEI graphic assets and write a LaTEI TeX mapping file."""
    output_dir = Path(output_dir)
    source_xml_path = Path(source_xml_path)
    graphics_map_path = Path(graphics_map_path)
    assets_dir = output_dir / "latei_assets" / "images"
    assets_dir.mkdir(parents=True, exist_ok=True)

    package = LateiAssetPackage(
        assets_dir=assets_dir.parent,
        graphics_map_path=graphics_map_path,
    )
    seen: dict[str, LateiGraphicMapping] = {}

    for graphic in root.xpath(".//tei:graphic", namespaces=NS):
        documentary_path = _graphic_documentary_path(graphic)
        if not documentary_path:
            package.warnings.append("Graphic without url, target, or n attribute.")
            continue
        if documentary_path in seen:
            continue

        resolved = _resolve_graphic_path(documentary_path, source_xml_path.parent)
        if not resolved.exists() or not resolved.is_file():
            package.warnings.append(f"Image not found for LaTEI package: {documentary_path}")
            continue

        copied_path = assets_dir / _package_file_name(documentary_path, resolved)
        shutil.copy2(resolved, copied_path)
        local_latex_path = copied_path.relative_to(output_dir).as_posix()
        mapping = LateiGraphicMapping(
            documentary_path=documentary_path,
            local_latex_path=local_latex_path,
            source_path=resolved,
            copied_path=copied_path,
        )
        seen[documentary_path] = mapping
        package.mappings.append(mapping)

    _write_graphics_map(package)
    return package


def _graphic_documentary_path(graphic: etree._Element) -> str:
    return (graphic.get("url") or graphic.get("target") or graphic.get("n") or "").strip()


def _resolve_graphic_path(raw_path: str, base_dir: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (base_dir / path).resolve()


def _package_file_name(documentary_path: str, source_path: Path) -> str:
    suffix = source_path.suffix
    stem = source_path.stem or "graphic"
    safe_stem = re.sub(r"[^A-Za-z0-9]+", "-", stem).strip("-") or "graphic"
    digest = sha1(documentary_path.encode("utf-8")).hexdigest()[:12]
    return f"{digest}-{safe_stem}{suffix}"


def _write_graphics_map(package: LateiAssetPackage) -> None:
    package.graphics_map_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% Experimental LaTEI graphic mapping.",
        "% This file is a compilation artifact, not a reversible source.",
    ]
    for mapping in package.mappings:
        lines.append(
            rf"\lateiDeclareGraphic{{{escape_latex(mapping.documentary_path)}}}{{{mapping.local_latex_path}}}"
        )
    for warning in package.warnings:
        lines.append(f"% WARNING: {warning}")
    package.graphics_map_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
