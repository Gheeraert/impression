"""Fonctions de citation partagées entre les crédits de page et les métadonnées Zotero."""

from __future__ import annotations

from urllib.parse import urljoin

from .site_structure import PageDef, SiteMeta


def build_public_page_url(file_name: str, site_meta: SiteMeta) -> str:
    base = site_meta.site_url.strip()
    if not base:
        return file_name
    if base.endswith(".html"):
        return urljoin(base, file_name)
    return urljoin(base.rstrip("/") + "/", file_name)


def build_public_asset_url(asset_href: str, site_meta: SiteMeta) -> str:
    base = site_meta.site_url.strip()
    if not base:
        return asset_href
    if base.endswith(".html"):
        return urljoin(base, asset_href)
    return urljoin(base.rstrip("/") + "/", asset_href)


def normalize_doi_url(doi: str) -> str:
    if not doi:
        return ""
    if doi.startswith("http://") or doi.startswith("https://"):
        return doi
    return f"https://doi.org/{doi}"


def full_volume_title(site_meta: SiteMeta) -> str:
    if site_meta.subtitle:
        return f"{site_meta.title}. {site_meta.subtitle}"
    return site_meta.title


def page_citation_authors(page: PageDef, site_meta: SiteMeta) -> list[str]:
    volume_is_edited = site_meta.creator_role_label.lower().startswith("dir")
    if page.authors:
        return page.authors
    if volume_is_edited:
        return []
    return site_meta.creators
