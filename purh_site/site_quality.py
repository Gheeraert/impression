"""Contrôle qualité post-génération du site HTML statique (liens, ressources, ids)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from urllib.parse import unquote, urldefrag, urlparse

from lxml import html as lxml_html


def run_site_quality_checks(output_dir: Path) -> list[str]:
    issues: list[str] = []
    html_files = sorted(path for path in output_dir.glob("*.html") if path.is_file())
    parsed_pages: dict[Path, lxml_html.HtmlElement] = {}

    def parse_page(path: Path) -> lxml_html.HtmlElement | None:
        if path in parsed_pages:
            return parsed_pages[path]
        try:
            parsed = lxml_html.fromstring(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - garde-fou de rapport.
            issues.append(f"[WARNING] {path.name} : HTML illisible ({exc})")
            return None
        parsed_pages[path] = parsed
        return parsed

    for html_file in html_files:
        document = parse_page(html_file)
        if document is None:
            continue
        page_ids = _html_ids(document)
        _check_empty_html_attributes(document, html_file.name, issues)
        _check_duplicate_html_ids(page_ids, html_file.name, issues)
        _check_html_links(html_file, document, page_ids, parse_page, issues)
        _check_html_resources(html_file, document, issues)
    return issues


def _html_ids(document: lxml_html.HtmlElement) -> list[str]:
    return [str(value) for value in document.xpath("//*[@id]/@id")]


def _check_empty_html_attributes(document: lxml_html.HtmlElement, file_name: str, issues: list[str]) -> None:
    for attr_name in ("href", "src", "id"):
        for _node in document.xpath(f"//*[@{attr_name}='']"):
            issues.append(f"[WARNING] {file_name} : attribut {attr_name} vide")


def _check_duplicate_html_ids(ids: list[str], file_name: str, issues: list[str]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for html_id in ids:
        if not html_id:
            continue
        if html_id in seen:
            duplicates.add(html_id)
        seen.add(html_id)
    for html_id in sorted(duplicates):
        issues.append(f'[WARNING] {file_name} : id HTML dupliqué "{html_id}"')


def _check_html_links(
    html_file: Path,
    document: lxml_html.HtmlElement,
    page_ids: list[str],
    parse_page: Callable[[Path], lxml_html.HtmlElement | None],
    issues: list[str],
) -> None:
    page_id_set = set(page_ids)
    for link in document.xpath("//a[@href]"):
        href = (link.get("href") or "").strip()
        if not href or href == "#" or _is_external_or_unchecked_url(href):
            continue
        href_without_fragment, fragment = urldefrag(href)
        if not href_without_fragment:
            if fragment and fragment not in page_id_set:
                issues.append(f"[WARNING] {html_file.name} : lien interne cassé vers #{fragment}")
            continue

        target_path = _resolve_quality_local_path(html_file, href_without_fragment)
        if target_path is None:
            continue
        if not target_path.exists():
            issues.append(f"[WARNING] {html_file.name} : fichier HTML local absent {href_without_fragment}")
            continue
        if fragment and target_path.suffix.lower() == ".html":
            target_doc = parse_page(target_path)
            if target_doc is None:
                continue
            target_ids = set(_html_ids(target_doc))
            if fragment not in target_ids:
                issues.append(f"[WARNING] {html_file.name} : cible absente {href_without_fragment}#{fragment}")


def _check_html_resources(html_file: Path, document: lxml_html.HtmlElement, issues: list[str]) -> None:
    resource_refs: list[tuple[str, str]] = []
    resource_refs.extend(("src", value) for value in document.xpath("//img[@src]/@src | //script[@src]/@src | //source[@src]/@src"))
    resource_refs.extend(("href", value) for value in document.xpath("//link[@href]/@href"))
    for _attr_name, value in resource_refs:
        ref = (value or "").strip()
        if not ref or _is_external_or_unchecked_url(ref):
            continue
        ref_without_fragment, _fragment = urldefrag(ref)
        target_path = _resolve_quality_local_path(html_file, ref_without_fragment)
        if target_path is not None and not target_path.exists():
            issues.append(f"[WARNING] {html_file.name} : fichier local absent {ref_without_fragment}")


def _is_external_or_unchecked_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "mailto", "tel", "data", "javascript"}:
        return True
    return bool(parsed.netloc) or value.startswith("/")


def _resolve_quality_local_path(html_file: Path, value: str) -> Path | None:
    if not value:
        return html_file
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or parsed.path.startswith("/"):
        return None
    return (html_file.parent / unquote(parsed.path)).resolve()
