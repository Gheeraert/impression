"""Rendu des balises meta Zotero / Dublin Core / Google Scholar Citations."""

from __future__ import annotations

import html
import re
from typing import TYPE_CHECKING

from .citation import (
    build_public_asset_url,
    build_public_page_url,
    full_volume_title,
    page_citation_authors,
)
from .site_structure import PageDef, SiteMeta

if TYPE_CHECKING:
    from .site_builder import ThemeAssets


def _strip_html(value: str) -> str:
    text_value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", text_value).strip()


# Google typically displays ~155-160 characters of a meta description before
# truncating with an ellipsis of its own; cutting cleanly at a word boundary
# ourselves beats leaving that to chance mid-word.
_DESCRIPTION_MAX_LENGTH = 160


def _truncate_description(text: str, limit: int = _DESCRIPTION_MAX_LENGTH) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    truncated = text[:limit].rsplit(" ", 1)[0]
    return truncated.rstrip(",;:.") + "…"


def build_page_description(html_content: str) -> str:
    """Plain-text excerpt suitable for a <meta name="description"> tag."""
    return _truncate_description(_strip_html(html_content))


def _meta_tag(name: str, content: str) -> str:
    content = (content or "").strip()
    if not content:
        return ""
    return f'<meta name="{html.escape(name, quote=True)}" content="{html.escape(content, quote=True)}">'


def render_zotero_meta(
    site_meta: SiteMeta,
    theme_assets: ThemeAssets,
    page: PageDef | None = None,
    abstract_html: str | None = None,
    citation_pdf_href: str | None = None,
) -> str:
    tags: list[str] = []
    volume_title = full_volume_title(site_meta)
    description_text = build_page_description(abstract_html) if abstract_html else ""

    page_url = build_public_page_url(page.file_name if page is not None else "index.html", site_meta)
    if page is None:
        citation_title = volume_title
        creator_tag = "citation_editor" if site_meta.creator_role_label.lower().startswith("dir") else "citation_author"
        for creator in site_meta.creators:
            tags.append(_meta_tag(creator_tag, creator))
        tags.extend([
            _meta_tag("citation_title", citation_title),
            _meta_tag("citation_publisher", site_meta.publisher),
            _meta_tag("citation_publication_date", site_meta.publication_year),
            _meta_tag("citation_isbn", site_meta.isbn),
            _meta_tag("citation_issn", site_meta.issn),
            _meta_tag("citation_series_title", site_meta.collection_title),
            _meta_tag("citation_series_number", site_meta.collection_number),
            _meta_tag("citation_doi", site_meta.doi),
            _meta_tag("citation_language", "fr"),
            _meta_tag("citation_pdf_url", build_public_asset_url(citation_pdf_href, site_meta) if citation_pdf_href else ""),
            _meta_tag("citation_abstract_html_url", page_url),
            _meta_tag("DC.Title", citation_title),
            _meta_tag("DC.Type", "book"),
            _meta_tag("DC.Publisher", site_meta.publisher),
            _meta_tag("DC.Date", site_meta.publication_year),
            _meta_tag("DC.Identifier", page_url),
        ])
        for creator in site_meta.creators:
            dc_name = "DC.Contributor" if creator_tag == "citation_editor" else "DC.Creator"
            tags.append(_meta_tag(dc_name, creator))
    else:
        citation_title = page.title if not page.subtitle else f"{page.title}. {page.subtitle}"
        volume_is_edited = site_meta.creator_role_label.lower().startswith("dir")
        chapter_authors = page_citation_authors(page, site_meta)
        for author in chapter_authors:
            tags.append(_meta_tag("citation_author", author))
            tags.append(_meta_tag("DC.Creator", author))
        if site_meta.creators and volume_is_edited:
            for editor in site_meta.creators:
                tags.append(_meta_tag("citation_editor", editor))
                tags.append(_meta_tag("DC.Contributor", editor))
        tags.extend([
            _meta_tag("citation_title", citation_title),
            _meta_tag("citation_book_title", volume_title),
            _meta_tag("citation_publisher", site_meta.publisher),
            _meta_tag("citation_publication_date", site_meta.publication_year),
            _meta_tag("citation_isbn", site_meta.isbn),
            _meta_tag("citation_issn", site_meta.issn),
            _meta_tag("citation_series_title", site_meta.collection_title),
            _meta_tag("citation_series_number", site_meta.collection_number),
            _meta_tag("citation_language", "fr"),
            _meta_tag("citation_abstract_html_url", page_url),
            _meta_tag("DC.Title", citation_title),
            _meta_tag("DC.Type", "bookSection"),
            _meta_tag("DC.Relation", volume_title),
            _meta_tag("DC.Publisher", site_meta.publisher),
            _meta_tag("DC.Date", site_meta.publication_year),
            _meta_tag("DC.Identifier", page_url),
        ])

    if description_text:
        tags.append(_meta_tag("description", description_text))
        tags.append(_meta_tag("DC.Description", description_text))

    return "\n  ".join(tag for tag in tags if tag)
