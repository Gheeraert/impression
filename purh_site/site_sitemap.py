"""Génère sitemap.xml et robots.txt pour le site publié."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from .citation import build_public_page_url
from .site_structure import PageDef, SiteMeta

SITEMAP_FILE_NAME = "sitemap.xml"
ROBOTS_FILE_NAME = "robots.txt"


def write_sitemap_and_robots(output_dir: Path, site_meta: SiteMeta, pages: list[PageDef]) -> list[str]:
    """Write sitemap.xml and robots.txt to output_dir. Returns lines for the build report.

    Both need absolute URLs, which requires site_meta.site_url — silently
    skipped (with a report line explaining why) when it is not set. This is
    the same condition under which the Zotero/Dublin Core citation URLs
    already degrade to relative paths (see citation.build_public_page_url).
    """
    if not site_meta.site_url.strip():
        return [
            f"{SITEMAP_FILE_NAME} et {ROBOTS_FILE_NAME} non générés : site_url absent des métadonnées TEI "
            "(les URLs de citation Zotero/Dublin Core restent, elles aussi, relatives dans ce cas)."
        ]

    urls = [build_public_page_url("index.html", site_meta)]
    urls.extend(build_public_page_url(page.file_name, site_meta) for page in pages)

    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    sitemap_lines.extend(f"  <url><loc>{escape(url)}</loc></url>" for url in urls)
    sitemap_lines.append("</urlset>")
    (output_dir / SITEMAP_FILE_NAME).write_text("\n".join(sitemap_lines) + "\n", encoding="utf-8")

    sitemap_url = build_public_page_url(SITEMAP_FILE_NAME, site_meta)
    robots_lines = ["User-agent: *", "Allow: /", "", f"Sitemap: {sitemap_url}"]
    (output_dir / ROBOTS_FILE_NAME).write_text("\n".join(robots_lines) + "\n", encoding="utf-8")

    return [
        f"{SITEMAP_FILE_NAME} : {len(urls)} URL(s).",
        f"{ROBOTS_FILE_NAME} : généré, référence {sitemap_url}.",
    ]
