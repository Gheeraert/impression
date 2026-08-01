"""Rendu du bloc « Crédits et citabilité » affiché en bas de chaque page de contenu."""

from __future__ import annotations

import html

from .citation import build_public_page_url, normalize_doi_url, page_citation_authors
from .site_structure import PageDef, SiteMeta


def render_credit_block(page: PageDef, site_meta: SiteMeta) -> str:
    page_creators = page_citation_authors(page, site_meta)
    volume_title = site_meta.title
    if site_meta.subtitle:
        volume_title = f"{volume_title}. {site_meta.subtitle}"

    volume_creators_text = " ; ".join(site_meta.creators)
    role_label = site_meta.creator_role_label
    public_url = build_public_page_url(page.file_name, site_meta)
    doi_value = site_meta.doi.strip()
    doi_url = normalize_doi_url(doi_value) if doi_value else ""
    cite_heading = {
        "article": "Pour citer cette contribution",
        "chapter": "Pour citer ce chapitre",
    }.get(page.page_kind, "Pour citer cette page")

    suggestion = [html.escape(" ; ".join(page_creators))] if page_creators else []
    title_bit = page.title
    if page.subtitle:
        title_bit += f". {page.subtitle}"
    suggestion.append(f'« {html.escape(title_bit)} »')
    host = f'dans <em>{html.escape(volume_title)}</em>'
    if volume_creators_text and set(page_creators) != set(site_meta.creators):
        host += f', {html.escape(role_label)} : {html.escape(volume_creators_text)}'
    suggestion.append(host)
    if site_meta.publisher:
        suggestion.append(html.escape(site_meta.publisher))
    if site_meta.publication_year:
        suggestion.append(html.escape(site_meta.publication_year))
    if public_url:
        suggestion.append(f'URL : <a href="{html.escape(public_url)}">{html.escape(public_url)}</a>')
    if doi_url:
        suggestion.append(f'DOI : <a href="{html.escape(doi_url)}">{html.escape(doi_value)}</a>')
    suggestion.append('consulté le <time class="consultation-date"></time>')

    lines = ['<section class="credit-box">']
    lines.append('<h2>Crédits et citabilité</h2>')
    lines.append(f'<p class="credit-kicker">{cite_heading}</p>')
    lines.append('<dl class="credit-list">')
    if page_creators:
        lines.append(f'<p class="credit-names">{html.escape(" ; ".join(page_creators))}</p>')
    lines.append(f'<div><dt>{"Contribution" if page.page_kind == "article" else "Chapitre"}</dt><dd>{html.escape(page.title)}</dd></div>')
    if page.subtitle:
        lines.append(f'<div><dt>Sous-titre</dt><dd>{html.escape(page.subtitle)}</dd></div>')
    lines.append(f'<div><dt>Volume</dt><dd><em>{html.escape(site_meta.title)}</em></dd></div>')
    if site_meta.subtitle:
        lines.append(f'<div><dt>Sous-titre du volume</dt><dd>{html.escape(site_meta.subtitle)}</dd></div>')
    if site_meta.publisher:
        lines.append(f'<div><dt>Éditeur</dt><dd>{html.escape(site_meta.publisher)}</dd></div>')
    if site_meta.publication_year:
        lines.append(f'<div><dt>Année</dt><dd>{html.escape(site_meta.publication_year)}</dd></div>')
    if public_url:
        lines.append(f'<div><dt>URL</dt><dd><a href="{html.escape(public_url)}">{html.escape(public_url)}</a></dd></div>')
    if doi_url:
        lines.append(f'<div><dt>DOI</dt><dd><a href="{html.escape(doi_url)}">{html.escape(doi_value)}</a></dd></div>')
    lines.append('<div><dt>Date de consultation</dt><dd><time class="consultation-date"></time></dd></div>')
    lines.append('</dl>')
    lines.append(f'<p class="credit-citation"><strong>Référence suggérée</strong> : {". ".join(suggestion)}.</p>')
    lines.append('</section>')
    return ''.join(lines)
