"""Balises Open Graph et Twitter Card — aperçus de partage social.

Distinct de site_structured_data.py (résultats enrichis de recherche) et de
site_zotero.py (Google Scholar/Zotero) : ce module ne joue aucun rôle dans
le classement des moteurs de recherche, seulement dans l'apparence d'un
lien partagé sur les réseaux sociaux, Slack, WhatsApp, etc.
"""

from __future__ import annotations

import html

from .citation import build_public_asset_url, build_public_page_url, full_volume_title
from .site_structure import PageDef, SiteMeta


def _property_meta_tag(property_name: str, content: str) -> str:
    content = (content or "").strip()
    if not content:
        return ""
    return f'<meta property="{html.escape(property_name, quote=True)}" content="{html.escape(content, quote=True)}">'


def _name_meta_tag(name: str, content: str) -> str:
    content = (content or "").strip()
    if not content:
        return ""
    return f'<meta name="{html.escape(name, quote=True)}" content="{html.escape(content, quote=True)}">'


def render_social_meta(
    site_meta: SiteMeta,
    page: PageDef | None,
    description: str = "",
    cover_href: str | None = None,
) -> str:
    """Open Graph + Twitter Card meta tags, only when an absolute site_url
    is known — a relative og:url/og:image would not resolve for a crawler
    fetching the preview from outside the site, same condition as the
    canonical link and JSON-LD (see site_structured_data.py)."""
    if not site_meta.site_url.strip():
        return ""

    page_url = build_public_page_url(page.file_name if page is not None else "index.html", site_meta)
    title = page.title if page is not None else full_volume_title(site_meta)
    image_url = build_public_asset_url(cover_href, site_meta) if cover_href else ""
    locale = (site_meta.language or "fr").replace("-", "_")
    if "_" not in locale:
        locale = f"{locale}_{locale.upper()}"

    tags = [
        _property_meta_tag("og:type", "article" if page is not None else "website"),
        _property_meta_tag("og:site_name", full_volume_title(site_meta)),
        _property_meta_tag("og:title", title),
        _property_meta_tag("og:url", page_url),
        _property_meta_tag("og:locale", locale),
        _property_meta_tag("og:description", description),
        _property_meta_tag("og:image", image_url),
        _name_meta_tag("twitter:card", "summary_large_image" if image_url else "summary"),
        _name_meta_tag("twitter:title", title),
        _name_meta_tag("twitter:description", description),
        _name_meta_tag("twitter:image", image_url),
    ]
    return "\n  ".join(tag for tag in tags if tag)
