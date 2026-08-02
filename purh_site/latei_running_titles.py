from __future__ import annotations

"""Build non-reversible running-title mappings for the direct LaTEI driver."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from purh_site.latei_typography import _short_running_title
from purh_site.reversible.latex_writer import escape_latex
from purh_site.utils import TEI_NS

NS = {"tei": TEI_NS}


@dataclass(slots=True)
class LateiRunningTitleMapping:
    full_title: str
    short_title: str


@dataclass(slots=True)
class LateiRunningTitlePackage:
    map_path: Path
    mappings: list[LateiRunningTitleMapping] = field(default_factory=list)

    @property
    def shortened_count(self) -> int:
        return len(self.mappings)


def package_latei_running_titles(root: etree._Element, map_path: Path) -> LateiRunningTitlePackage:
    """Write a TeX mapping from full structural titles to stable short marks."""
    package = LateiRunningTitlePackage(map_path=Path(map_path))
    seen: set[str] = set()

    for title in _iter_structural_titles(root):
        if title in seen:
            continue
        seen.add(title)
        short_title = _short_running_title(title)
        if short_title != title:
            package.mappings.append(
                LateiRunningTitleMapping(full_title=title, short_title=short_title)
            )

    _write_running_titles_map(package)
    return package


def _iter_structural_titles(root: etree._Element) -> list[str]:
    titles: list[str] = []
    for element in root.xpath(".//tei:group | .//tei:div", namespaces=NS):
        title = _structural_title(element)
        if title:
            titles.append(title)
    return titles


def _structural_title(element: etree._Element) -> str:
    for attr_name in ("data-page-title", "data-article-title", "n"):
        value = (element.get(attr_name) or "").strip()
        if value:
            return _normalize_space(value)

    direct_head = " ".join(element.xpath("./tei:head[1]//text()", namespaces=NS)).strip()
    if direct_head:
        return _normalize_space(direct_head)

    body_head = " ".join(
        element.xpath("./tei:body/tei:div[1]/tei:head[1]//text()", namespaces=NS)
    ).strip()
    if body_head:
        return _normalize_space(body_head)

    level_head = " ".join(
        element.xpath(".//tei:head[@subtype='level1'][1]//text()", namespaces=NS)
    ).strip()
    return _normalize_space(level_head)


_REGULAR_WS = re.compile(r"[ \t\r\n\f\v]+")


def _normalize_space(value: str) -> str:
    # Normalize only regular whitespace; preserve U+00A0 (non-breaking space) so
    # that running-title map keys contain the same character as the body attributes.
    # LaTeX's \newunicodechar{ }{~} then converts U+00A0 → ~ identically in both
    # the map key and the runtime lookup, allowing \prop_get to find the entry.
    return _REGULAR_WS.sub(" ", value).strip(" \t\r\n\f\v")


def _write_running_titles_map(package: LateiRunningTitlePackage) -> None:
    package.map_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% Experimental LaTEI running-title mapping.",
        "% This file is a compilation artifact, not a reversible source.",
    ]
    for mapping in package.mappings:
        lines.append(
            rf"\lateiDeclareRunningTitle{{{escape_latex(mapping.full_title)}}}{{{escape_latex(mapping.short_title)}}}"
        )
    package.map_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
