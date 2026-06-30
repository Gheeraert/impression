from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ManifestEntry:
    """Une ressource copiée ou générée dans le dossier de sortie."""

    output: str
    declared_by: str   # "xml" | "dialog" | "generator"
    role: str          # "image" | "cover_front" | "cover_back" | "editor_pdf" | "latei_pdf" | "css" | "js" | "manifest"
    source: str | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "output": self.output,
            "declared_by": self.declared_by,
            "role": self.role,
        }
        if self.source is not None:
            d["source"] = self.source
        return d


@dataclass
class AssetManifest:
    """Inventaire de toutes les ressources du site généré."""

    images: list[ManifestEntry] = field(default_factory=list)
    covers: list[ManifestEntry] = field(default_factory=list)
    downloads: list[ManifestEntry] = field(default_factory=list)
    static: list[ManifestEntry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def write(self, manifest_path: Path) -> None:
        """Écrit le manifeste JSON dans assets/metadata/manifest.json."""
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "images": [e.to_dict() for e in self.images],
            "covers": [e.to_dict() for e in self.covers],
            "downloads": [e.to_dict() for e in self.downloads],
            "static": [e.to_dict() for e in self.static],
            "warnings": self.warnings,
        }
        manifest_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
