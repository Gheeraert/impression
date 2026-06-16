from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class BuildConfig:
    """Configuration d'un build de site statique."""

    output_dir: Path
    assets_dir: Path | None = None
    write_normalized_tei: bool = True
    site_title_fallback: str = "Livre PURH"

    @property
    def output_assets_dir(self) -> Path:
        return self.output_dir / "assets"
