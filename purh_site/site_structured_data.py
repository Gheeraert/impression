"""Lien canonique et données structurées schema.org (JSON-LD) pour le <head>.

Distinct de site_zotero.py : les balises Highwire Press / Dublin Core y
visent Google Scholar et Zotero, tandis que ce module vise les résultats
enrichis de la recherche web grand public (rich snippets) — deux mécanismes
indépendants qui peuvent coexister sans se dupliquer.
"""

from __future__ import annotations

import html
import json
from typing import TYPE_CHECKING

from .citation import build_public_page_url, full_volume_title, normalize_doi_url, page_citation_authors
from .site_structure import PageDef, SiteMeta

if TYPE_CHECKING:
    pass


def render_canonical_link(site_meta: SiteMeta, page: PageDef | None) -> str:
    """<link rel="canonical">, only when an absolute site_url is known.

    A relative canonical is technically legal but defeats the point (guard
    against duplicate content across mirrors/domains) — same condition
    under which the sitemap is skipped, see site_sitemap.py.
    """
    if not site_meta.site_url.strip():
        return ""
    page_url = build_public_page_url(page.file_name if page is not None else "index.html", site_meta)
    return f'<link rel="canonical" href="{html.escape(page_url, quote=True)}">'


def render_json_ld(site_meta: SiteMeta, page: PageDef | None, description: str = "") -> str:
    """<script type="application/ld+json"> describing the book or chapter."""
    if not site_meta.site_url.strip():
        return ""

    page_url = build_public_page_url(page.file_name if page is not None else "index.html", site_meta)
    volume_title = full_volume_title(site_meta)

    if page is None:
        data: dict[str, object] = {
            "@context": "https://schema.org",
            "@type": "Book",
            "name": volume_title,
            "url": page_url,
        }
        if site_meta.creators:
            role = "editor" if site_meta.creator_role_label.lower().startswith("dir") else "author"
            data[role] = [{"@type": "Person", "name": name} for name in site_meta.creators]
        if site_meta.publisher:
            data["publisher"] = {"@type": "Organization", "name": site_meta.publisher}
        if site_meta.publication_year:
            data["datePublished"] = site_meta.publication_year
        if site_meta.isbn:
            data["isbn"] = site_meta.isbn
        if site_meta.doi:
            data["sameAs"] = normalize_doi_url(site_meta.doi)
    else:
        chapter_title = page.title if not page.subtitle else f"{page.title}. {page.subtitle}"
        data = {
            "@context": "https://schema.org",
            "@type": "Chapter",
            "name": chapter_title,
            "url": page_url,
            "isPartOf": {
                "@type": "Book",
                "name": volume_title,
                "url": build_public_page_url("index.html", site_meta),
            },
        }
        chapter_authors = page_citation_authors(page, site_meta)
        if chapter_authors:
            data["author"] = [{"@type": "Person", "name": name} for name in chapter_authors]

    if description:
        data["description"] = description

    payload = json.dumps(data, ensure_ascii=False)
    # </script> can never appear literally inside a JSON string value here
    # (json.dumps escapes control characters, not forward slashes) — the
    # replace is defense in depth against a title/author containing that
    # exact substring, which would otherwise close the script element early.
    payload = payload.replace("</", "<\\/")
    return f'<script type="application/ld+json">{payload}</script>'
