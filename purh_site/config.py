from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class BuildConfig:
    """Configuration d'un build de site statique."""

    output_dir: Path
    assets_dir: Path | None = None
    back_cover_path: Path | None = None
    collection_title: str = ""
    collection_number: str = ""
    collection_issn: str = ""
    write_normalized_tei: bool = True
    site_title_fallback: str = "Livre PURH"
    pdf_export_mode: str = "none"
    latex_engine: str = "lualatex"
    # Colophon LaTEI (référentiel PURH v0.6 §8.1, 2026-08-04) : sans
    # équivalent dans le XML, fournis via la boîte de dialogue optionnelle
    # du GUI — omis du colophon si laissés vides.
    cover_designer: str = ""
    editorial_contact: str = ""
    # Page de titre (référentiel PURH v0.7, 2026-08-04) : correction manuelle
    # des "sous la direction de" quand le TEI/Métopes source ne les distingue
    # pas fiablement d'un autre rôle (ex. compositeur/trice) — voir
    # reversible_integration.run_reversible_export_for_file. Vide = on garde
    # l'extraction TEI telle quelle.
    directors_override: str = ""

    @property
    def output_assets_dir(self) -> Path:
        return self.output_dir / "assets"
