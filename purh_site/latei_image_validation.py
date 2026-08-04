from __future__ import annotations

"""Diagnostic (jamais correctif silencieux) des ressources image du TEI source.

Référentiel PURH v0.6 §10 (P0 item 6, "restaurer ou diagnostiquer les
images") : chaque figure doit posséder soit une ressource résolue, soit un
statut explicite d'absence accepté — « aucune attente silencieuse ». Si la
TEI ne contient que la légende sans `graphic`, le déficit doit être
diagnostiqué en amont (§10.3) ; il est interdit d'extraire les images du PDF
imprimeur pour contourner le problème. Ce module ne fait donc que signaler
les défauts de source, jamais les réparer ni inventer une ressource — même
doctrine que `latei_metadata_validation.py`.
"""

from pathlib import Path

from lxml import etree

from .reversible import Diagnostic
from .utils import TEI_NS

NS = {"tei": TEI_NS}


def validate_latei_images(root: etree._Element, *, source_xml_path: Path) -> list[Diagnostic]:
    """Report figures without any image resource, or resources that do not
    resolve to an existing file — never mutates the source or the tree."""
    diagnostics: list[Diagnostic] = []
    base_dir = Path(source_xml_path).resolve().parent

    for index, figure in enumerate(root.xpath(".//tei:figure", namespaces=NS), start=1):
        figure_label = figure.get("{http://www.w3.org/XML/1998/namespace}id") or f"figure[{index}]"
        graphics = figure.xpath(".//tei:graphic", namespaces=NS)
        if not graphics:
            diagnostics.append(
                Diagnostic(
                    code="FIGURE_WITHOUT_GRAPHIC",
                    message="Figure without any <graphic> element: a caption may be present but no image resource is declared.",
                    path=f"figure/{figure_label}",
                )
            )
            continue

        for graphic_index, graphic in enumerate(graphics, start=1):
            locator = (graphic.get("url") or graphic.get("target") or graphic.get("n") or "").strip()
            graphic_path = f"figure/{figure_label}/graphic[{graphic_index}]"
            if not locator:
                diagnostics.append(
                    Diagnostic(
                        code="GRAPHIC_WITHOUT_LOCATOR",
                        message="Graphic element has no url, target, or n attribute.",
                        path=graphic_path,
                    )
                )
                continue

            resolved = Path(locator)
            if not resolved.is_absolute():
                resolved = (base_dir / resolved).resolve()
            if not resolved.exists() or not resolved.is_file():
                diagnostics.append(
                    Diagnostic(
                        code="IMAGE_RESOURCE_NOT_FOUND",
                        message=f"Image resource not found on disk: {locator}",
                        path=graphic_path,
                    )
                )

    return diagnostics
