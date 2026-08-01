from __future__ import annotations

import copy
import html
import re
import shutil
from dataclasses import dataclass, replace
from pathlib import Path

from lxml import etree
from lxml import html as lxml_html

from .config import BuildConfig
from .normalizer import NormalizeReport, TeiNormalizer
from .site_credits import render_credit_block
from .site_latei_pdf_export import SiteLateiPdfExportResult, build_site_latei_pdf_artifacts
from .site_quality import run_site_quality_checks
from .site_structure import AuthorEntry, NavItem, PageDef, SiteMeta, SiteStructureBuilder
from .site_zotero import render_zotero_meta
from .tei_loader import LoadReport, TeiLoader, load_many
from .utils import NSMAP, ensure_dir


@dataclass(slots=True)
class BuildResult:
    output_dir: Path
    html_path: Path
    normalized_tei_path: Path | None
    report_path: Path

@dataclass(slots=True)
class ThemeAssets:
    cover_href: str | None = None
    university_logo_href: str | None = None
    purh_logo_href: str | None = None
    pdf_href: str | None = None
    footer_logo_href: str | None = None

@dataclass(slots=True)
class PdfSiteArtifacts:
    latex_href: str | None = None
    generated_pdf_href: str | None = None
    build_result: SiteLateiPdfExportResult | None = None
    disabled_by_editor_pdf: bool = False

@dataclass(frozen=True, slots=True)
class AnchorTarget:
    file_name: str
    is_page_root: bool = False


def has_editor_pdf(assets_dir: Path | None) -> bool:
    """Retourne True si un dossier assets contient au moins un PDF éditeur."""

    if not assets_dir or not assets_dir.exists():
        return False
    for child in assets_dir.iterdir():
        if child.is_dir() and child.name.lower() == "pdf":
            return any(path.is_file() and path.suffix.lower() == ".pdf" for path in child.rglob("*"))
    return False

_INLINE_TAGS_PATTERN = r"em|strong|span|sup|sub|i|b"
_PROTECTED_HTML_BLOCK_RE = re.compile(
    r"<(script|style|code|pre)\b[^>]*>.*?</\1>",
    flags=re.DOTALL | re.IGNORECASE,
)
_HTML_TAG_RE = re.compile(r"(<[^>]+>)")
_VISIBLE_URL_RE = re.compile(r"(https?://[^\s<]+|www\.[^\s<]+)")
_HTML_ENTITY_RE = re.compile(r"&(?:#\d+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);")
_SPACE_ENTITY_BEFORE_DOUBLE_PUNCT_RE = re.compile(
    r"(&(?:nbsp|#160|#xA0|#xa0|#8239|#x202f|#x202F);)\u202f([:;?!])"
)
_FRENCH_NARROW_NBSP = "\u202f"


def normalize_inline_html_spacing(html_content: str) -> str:
    """
    Corrige des espacements fautifs autour des balises inline HTML.

    Exemples corrigés :
    - tardive<em> Passio</em>  ->  tardive <em>Passio</em>
    - <em>confessio </em>que   ->  <em>confessio</em> que
    - </em>,n<sup>o</sup>      ->  </em>, n<sup>o</sup>

    La fonction reste volontairement prudente : elle ne modifie pas
    la structure HTML, seulement quelques espaces manifestement fautifs.
    """

    # Évite d'intervenir dans des zones où l'espace peut être significatif.
    protected_blocks: list[str] = []

    def protect(match: re.Match[str]) -> str:
        protected_blocks.append(match.group(0))
        return f"@@IMPRESSION_PROTECTED_BLOCK_{len(protected_blocks) - 1}@@"

    html_content = re.sub(
        r"<(script|style|code|pre)\b[^>]*>.*?</\1>",
        protect,
        html_content,
        flags=re.DOTALL | re.IGNORECASE,
    )

    inline = _INLINE_TAGS_PATTERN
    word_char = r"A-Za-zÀ-ÖØ-öø-ÿ0-9"

    # tardive<em> Passio</em> -> tardive <em>Passio</em>
    html_content = re.sub(
        rf"([{word_char}])<({inline})(\s+[^>]*)?>\s+",
        r"\1 <\2\3>",
        html_content,
    )

    # <em>confessio </em>que -> <em>confessio</em> que
    html_content = re.sub(
        rf"\s+</({inline})>(?=[{word_char}])",
        r"</\1> ",
        html_content,
    )

    # <em>confessio </em>, -> <em>confessio</em>,
    html_content = re.sub(
        rf"\s+</({inline})>(?=[,.;:!?])",
        r"</\1>",
        html_content,
    )

    # </em>,n<sup>o</sup> -> </em>, n<sup>o</sup>
    html_content = re.sub(
        rf"</({inline})>,([{word_char}])",
        r"</\1>, \2",
        html_content,
    )

    # Pas d'espace avant ponctuation après une balise inline.
    html_content = re.sub(
        rf"</({inline})>\s+([,.;:!?])",
        r"</\1>\2",
        html_content,
    )

    def restore(match: re.Match[str]) -> str:
        index = int(match.group(1))
        return protected_blocks[index]

    html_content = re.sub(
        r"@@IMPRESSION_PROTECTED_BLOCK_(\d+)@@",
        restore,
        html_content,
    )

    return html_content


def normalize_french_typography_html(html_content: str) -> str:
    """Normalise prudemment la typographie francaise dans le texte visible HTML."""

    parts: list[str] = []
    last_end = 0
    for match in _PROTECTED_HTML_BLOCK_RE.finditer(html_content):
        parts.append(_normalize_french_typography_unprotected_html(html_content[last_end:match.start()]))
        parts.append(match.group(0))
        last_end = match.end()
    parts.append(_normalize_french_typography_unprotected_html(html_content[last_end:]))
    return "".join(parts)


def rewrite_internal_links(html_content: str, current_file_name: str, anchor_index: dict[str, AnchorTarget]) -> str:
    """Rattache les liens #xml-id aux pages HTML statiques qui portent l'ancre."""

    if not anchor_index:
        return html_content

    document = lxml_html.fromstring(html_content)
    changed = False
    for link in document.xpath("//a[@href]"):
        href = link.get("href") or ""
        if not href.startswith("#") or len(href) <= 1:
            continue
        anchor_id = href[1:]
        target = anchor_index.get(anchor_id)
        if not target or target.file_name == current_file_name:
            continue
        if target.is_page_root:
            link.set("href", target.file_name)
        else:
            link.set("href", f"{target.file_name}#{anchor_id}")
        changed = True

    if not changed:
        return html_content
    return lxml_html.tostring(document, encoding="unicode", method="html", doctype="<!DOCTYPE html>")


def _normalize_french_typography_unprotected_html(html_content: str) -> str:
    parts: list[str] = []
    for part in _HTML_TAG_RE.split(html_content):
        if not part:
            continue
        if part.startswith("<") and part.endswith(">"):
            parts.append(part)
        else:
            parts.append(_normalize_french_typography_text(part))
    return "".join(parts)


def _normalize_french_typography_text(text: str) -> str:
    parts: list[str] = []
    last_end = 0
    for match in _VISIBLE_URL_RE.finditer(text):
        parts.append(_normalize_french_typography_text_without_urls(text[last_end:match.start()]))
        parts.append(match.group(0))
        last_end = match.end()
    parts.append(_normalize_french_typography_text_without_urls(text[last_end:]))
    return "".join(parts)


def _normalize_french_typography_text_without_urls(text: str) -> str:
    parts: list[str] = []
    last_end = 0
    for match in _HTML_ENTITY_RE.finditer(text):
        parts.append(_normalize_french_typography_plain_text(text[last_end:match.start()]))
        parts.append(match.group(0))
        last_end = match.end()
    parts.append(_normalize_french_typography_plain_text(text[last_end:]))
    normalized = "".join(parts)
    return _SPACE_ENTITY_BEFORE_DOUBLE_PUNCT_RE.sub(r"\1\2", normalized)


def _normalize_french_typography_plain_text(text: str) -> str:
    if not text:
        return text

    text = re.sub(
        r"\b([cCdDjJlLmMnNsStT]|[qQ]u|[jJ]usqu|[lL]orsqu|[pP]uisqu)'(?=[A-Za-zÀ-ÖØ-öø-ÿ])",
        r"\1’",
        text,
    )
    text = re.sub(r"«[\s\u00a0\u202f]*", f"«{_FRENCH_NARROW_NBSP}", text)
    text = re.sub(r"[\s\u00a0\u202f]*»", f"{_FRENCH_NARROW_NBSP}»", text)
    text = re.sub(r"[\s\u00a0\u202f]*([:;?!])", f"{_FRENCH_NARROW_NBSP}\\1", text)
    text = re.sub(
        r"\b([IVXLCDM]{2,})e(\s+siècle)",
        r"\1<sup>e</sup>\2",
        text,
        flags=re.IGNORECASE,
    )
    return text

class SiteBuilder:
    """Orchestre le chargement, la normalisation et le rendu multi-pages."""

    def __init__(self) -> None:
        self.loader = TeiLoader()
        self.normalizer = TeiNormalizer()
        self.structure_builder = SiteStructureBuilder()
        self.resources_dir = Path(__file__).parent / "resources"
        self.fragment_xslt = etree.XSLT(etree.parse(str(self.resources_dir / "tei_to_html.xsl")))

    def build_from_master(self, master_xml: Path, config: BuildConfig) -> BuildResult:
        tree, load_report = self.loader.load_master(master_xml)
        normalize_report = self.normalizer.normalize(tree)
        return self._finalize_build(tree, config, load_report, normalize_report)

    def build_from_many(
        self,
        xml_files: list[Path],
        output_root: Path,
        assets_dir: Path | None = None,
        config_overrides: BuildConfig | None = None,
    ) -> list[BuildResult]:
        results: list[BuildResult] = []
        for tree, load_report in load_many(xml_files):
            normalize_report = self.normalizer.normalize(tree)
            target_dir = output_root / Path(load_report.master_path).stem
            if config_overrides is None:
                config = BuildConfig(output_dir=target_dir, assets_dir=assets_dir)
            else:
                config = replace(
                    config_overrides,
                    output_dir=target_dir,
                    assets_dir=assets_dir if assets_dir is not None else config_overrides.assets_dir,
                )
            results.append(self._finalize_build(tree, config, load_report, normalize_report))
        return results

    def _finalize_build(
        self,
        tree: etree._ElementTree,
        config: BuildConfig,
        load_report: LoadReport,
        normalize_report: NormalizeReport,
    ) -> BuildResult:
        ensure_dir(config.output_dir)
        ensure_dir(config.output_assets_dir)
        self._copy_static_resources(config.output_assets_dir)
        self._copy_user_assets(config.assets_dir, config.output_assets_dir)

        normalized_tei_path: Path | None = None
        if config.write_normalized_tei:
            normalized_tei_path = config.output_dir / "book.normalized.xml"
            tree.write(
                str(normalized_tei_path),
                encoding="utf-8",
                xml_declaration=True,
                pretty_print=True,
            )

        site_meta, pages, nav = self.structure_builder.build(tree)
        self._apply_config_fallbacks(site_meta, config, tree)
        anchor_index = self._collect_anchor_index(tree, pages)
        theme_assets = self._discover_theme_assets(config.output_assets_dir)
        pdf_artifacts = self._build_pdf_site_artifacts(tree, config, normalized_tei_path, theme_assets)
        citation_pdf_href = theme_assets.pdf_href or pdf_artifacts.generated_pdf_href
        back_cover_html, back_cover_source = self._resolve_back_cover_html(tree, config)
        self._write_index_page(
            config.output_dir,
            site_meta,
            nav,
            theme_assets,
            normalized_tei_href=normalized_tei_path.name if normalized_tei_path else None,
            latex_href=pdf_artifacts.latex_href,
            generated_pdf_href=pdf_artifacts.generated_pdf_href,
            citation_pdf_href=citation_pdf_href,
            back_cover_html=back_cover_html,
        )
        for page in pages:
            self._write_content_page(
                config.output_dir,
                tree,
                site_meta,
                nav,
                page,
                theme_assets,
                anchor_index,
                citation_pdf_href=citation_pdf_href,
            )

        report_path = config.output_dir / "build_report.txt"
        report_lines = [
            load_report.as_text(),
            "Normalisation :",
            *normalize_report.as_lines(),
            "",
            f"Pages générées : {1 + len(pages)}",
        ]
        report_lines.extend(f"- {page.file_name} ← {page.title}" for page in pages)
        if theme_assets.cover_href:
            report_lines.append(f"Couverture détectée : {theme_assets.cover_href}")
        if theme_assets.university_logo_href:
            report_lines.append(f"Logo université : {theme_assets.university_logo_href}")
        if theme_assets.purh_logo_href:
            report_lines.append(f"Logo PURH : {theme_assets.purh_logo_href}")
        if theme_assets.pdf_href:
            report_lines.append(f"PDF détecté : {theme_assets.pdf_href}")
        report_lines.extend(self._pdf_site_report_lines(theme_assets, pdf_artifacts))
        if back_cover_source:
            report_lines.append(f"Quatrième de couverture : {back_cover_source}")
        quality_issues = run_site_quality_checks(config.output_dir)
        report_lines.extend(["", "Contrôle qualité du site :"])
        if quality_issues:
            report_lines.extend(f"- {issue}" for issue in quality_issues)
        else:
            report_lines.append("- OK")
        report_path.write_text("\n".join(report_lines), encoding="utf-8")

        return BuildResult(
            output_dir=config.output_dir,
            html_path=config.output_dir / "index.html",
            normalized_tei_path=normalized_tei_path,
            report_path=report_path,
        )

    def _build_pdf_site_artifacts(
        self,
        tree: etree._ElementTree,
        config: BuildConfig,
        normalized_tei_path: Path | None,
        theme_assets: ThemeAssets,
    ) -> PdfSiteArtifacts:
        mode = self._normalized_pdf_export_mode(config.pdf_export_mode)
        if theme_assets.pdf_href:
            return PdfSiteArtifacts(disabled_by_editor_pdf=(mode != "none"))
        if mode == "none":
            return PdfSiteArtifacts()

        generated_dir = config.output_assets_dir / "generated"
        ensure_dir(generated_dir)
        pdf_input_path = normalized_tei_path
        if pdf_input_path is None:
            pdf_input_path = generated_dir / "book.normalized.xml"
            tree.write(
                str(pdf_input_path),
                encoding="utf-8",
                xml_declaration=True,
                pretty_print=True,
            )

        latei_result = build_site_latei_pdf_artifacts(
            pdf_input_path,
            generated_dir,
            compile_pdf=(mode == "latei_pdf"),
            latex_engine=config.latex_engine,
        )

        return PdfSiteArtifacts(
            latex_href=(
                "assets/generated/book.tex" if latei_result.tex_path.exists() else None
            ),
            generated_pdf_href=(
                "assets/generated/book.pdf" if latei_result.pdf_path.exists() else None
            ),
            build_result=latei_result,
        )

    def _normalized_pdf_export_mode(self, value: str) -> str:
        mode = (value or "none").strip().lower()
        return mode if mode in {"none", "latei", "latei_pdf"} else "none"

    def _pdf_site_report_lines(
        self,
        theme_assets: ThemeAssets,
        artifacts: PdfSiteArtifacts,
    ) -> list[str]:
        lines: list[str] = []
        if theme_assets.pdf_href and artifacts.disabled_by_editor_pdf:
            lines.append("Génération LaTeX/PDF : désactivée car un PDF éditeur est disponible.")
        if artifacts.latex_href:
            lines.append(f"LaTeX généré : {artifacts.latex_href}")
        if artifacts.generated_pdf_href:
            lines.append(f"PDF généré : {artifacts.generated_pdf_href}")
        if artifacts.build_result and not artifacts.build_result.success:
            lines.append(
                "[WARNING] PDF non généré : moteur LaTeX indisponible ou compilation échouée."
            )
            lines.append("Voir : assets/generated/pdf_build_report.txt")
        return lines

    def _apply_config_fallbacks(
        self,
        site_meta: SiteMeta,
        config: BuildConfig,
        tree: etree._ElementTree,
    ) -> None:
        title_from_xml = tree.xpath(
            "normalize-space((/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title[@type='main'])[1])",
            namespaces=NSMAP,
        )
        if not title_from_xml and config.site_title_fallback:
            site_meta.title = config.site_title_fallback
        if not site_meta.collection_title:
            site_meta.collection_title = config.collection_title
        if not site_meta.collection_number:
            site_meta.collection_number = config.collection_number
        if not site_meta.collection_issn:
            site_meta.collection_issn = config.collection_issn
        if not site_meta.issn:
            site_meta.issn = config.collection_issn

    def _copy_static_resources(self, output_assets_dir: Path) -> None:
        for name in ("site.css", "app.js"):
            shutil.copy2(self.resources_dir / name, output_assets_dir / name)

    def _copy_user_assets(self, user_assets_dir: Path | None, output_assets_dir: Path) -> None:
        if not user_assets_dir or not user_assets_dir.exists():
            return
        for child in user_assets_dir.iterdir():
            dst = output_assets_dir / child.name
            if child.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(child, dst)
            else:
                shutil.copy2(child, dst)

    def _write_index_page(
            self,
            output_dir: Path,
            site_meta: SiteMeta,
            nav: list[NavItem],
            theme_assets: ThemeAssets,
            normalized_tei_href: str | None,
            latex_href: str | None,
            generated_pdf_href: str | None,
            citation_pdf_href: str | None,
            back_cover_html: str | None,
    ) -> None:
        nav_html = self._render_sidebar(nav, current_file_name=None)
        creators_value = html.escape(" · ".join(site_meta.creators)) if site_meta.creators else ""
        hero_parts = ['<section class="home-hero">', '<div class="home-hero-grid">']
        hero_parts.append('<div class="home-hero-text">')
        hero_parts.append('<p class="eyebrow">Livre web PURH</p>')
        hero_parts.append(f'<h1>{html.escape(site_meta.title)}</h1>')
        if site_meta.subtitle:
            hero_parts.append(f'<p class="subtitle">{html.escape(site_meta.subtitle)}</p>')
        if creators_value:
            hero_parts.append(f'<p class="meta-line">{creators_value}</p>')
        if site_meta.publisher or site_meta.publication_year:
            meta_bits = [bit for bit in (site_meta.publisher, site_meta.publication_year) if bit]
            hero_parts.append(f'<p class="meta-line">{" · ".join(html.escape(bit) for bit in meta_bits)}</p>')
        if back_cover_html:
            hero_parts.append(f'<div class="hero-back-cover">{back_cover_html}</div>')
        hero_parts.append('</div>')
        hero_parts.append(self._render_cover_link(theme_assets, compact=False))
        hero_parts.append('</div></section>')
        hero_parts.append(
            self._render_home_downloads(
                normalized_tei_href,
                theme_assets.pdf_href,
                latex_href=latex_href,
                generated_pdf_href=generated_pdf_href,
            )
        )
        hero_parts.append('<section class="home-panel"><h2>Sommaire</h2>')
        hero_parts.append(self._render_toc(nav))
        hero_parts.append('</section>')
        hero_parts.append(self._render_footer(theme_assets))
        page_html = self._wrap_html(
            page_title=site_meta.title,
            site_meta=site_meta,
            nav_html=nav_html,
            content_html=''.join(hero_parts),
            theme_assets=theme_assets,
            page_grid_class='page-grid page-grid--home',
            abstract_html=back_cover_html,
            citation_pdf_href=citation_pdf_href,
        )
        page_html = normalize_inline_html_spacing(page_html)
        page_html = normalize_french_typography_html(page_html)
        (output_dir / 'index.html').write_text(page_html, encoding='utf-8')

    def _write_content_page(
        self,
        output_dir: Path,
        tree: etree._ElementTree,
        site_meta: SiteMeta,
        nav: list[NavItem],
        page: PageDef,
        theme_assets: ThemeAssets,
        anchor_index: dict[str, AnchorTarget],
        citation_pdf_href: str | None,
    ) -> None:
        page_group = self._find_page_group(tree, page.node_id)
        if page_group is None:
            return
        fragment_html = self._render_page_fragment(page_group)
        nav_html = self._render_sidebar(nav, current_file_name=page.file_name)
        page_header = self._render_page_header(page, theme_assets)
        credits = render_credit_block(page, site_meta)
        pager = self._render_prev_next(page, nav)
        full_content = page_header + fragment_html + credits + pager + self._render_footer(theme_assets)
        page_html = self._wrap_html(
            page_title=f"{page.title} — {site_meta.title}",
            site_meta=site_meta,
            nav_html=nav_html,
            content_html=full_content,
            theme_assets=theme_assets,
            page_grid_class='page-grid',
            page=page,
            citation_pdf_href=citation_pdf_href,
        )
        page_html = normalize_inline_html_spacing(page_html)
        page_html = normalize_french_typography_html(page_html)
        page_html = rewrite_internal_links(page_html, current_file_name=page.file_name, anchor_index=anchor_index)
        (output_dir / page.file_name).write_text(page_html, encoding='utf-8')

    def _collect_anchor_index(self, tree: etree._ElementTree, pages: list[PageDef]) -> dict[str, AnchorTarget]:
        anchor_index: dict[str, AnchorTarget] = {}
        xml_id_attr = "{http://www.w3.org/XML/1998/namespace}id"
        for page in pages:
            page_group = self._find_page_group(tree, page.node_id)
            if page_group is None:
                continue
            page_anchor_id = (page_group.get(xml_id_attr) or "").strip()
            if page_anchor_id and page_anchor_id not in anchor_index:
                anchor_index[page_anchor_id] = AnchorTarget(page.file_name, is_page_root=True)
            for node in page_group.xpath(".//*[@xml:id]", namespaces=NSMAP):
                anchor_id = (node.get(xml_id_attr) or "").strip()
                if anchor_id and anchor_id not in anchor_index:
                    anchor_index[anchor_id] = AnchorTarget(page.file_name)
        return anchor_index

    def _find_page_group(self, tree: etree._ElementTree, node_id: str) -> etree._Element | None:
        matches = tree.xpath(f"//*[@xml:id='{node_id}']", namespaces=NSMAP)
        return matches[0] if matches else None

    def _render_page_fragment(self, page_group: etree._Element) -> str:
        cloned = copy.deepcopy(page_group)
        self._strip_redundant_title_pages(cloned)
        self._renumber_fragment_notes(cloned)
        fragment_tree = etree.ElementTree(cloned)
        result = self.fragment_xslt(
            fragment_tree,
            assets_image_base=etree.XSLT.strparam('assets/images'),
            assets_audio_base=etree.XSLT.strparam('assets/audio'),
            assets_video_base=etree.XSLT.strparam('assets/video'),
        )
        return str(result)

    def _strip_redundant_title_pages(self, root: etree._Element) -> None:
        for title_page in root.xpath(".//tei:front/tei:div[@type='titlePage']", namespaces=NSMAP):
            parent = title_page.getparent()
            if parent is not None:
                parent.remove(title_page)

    def _renumber_fragment_notes(self, root: etree._Element) -> None:
        for index, note in enumerate(root.xpath('.//tei:note', namespaces=NSMAP), start=1):
            note.set('n', str(index))

    def _render_sidebar(self, nav: list[NavItem], current_file_name: str | None) -> str:
        nav_items = self.structure_builder.build_nav_for_page(nav, current_file_name)
        return (
            '<nav class="sidebar-nav" aria-label="Sommaire du livre">'
            '<div class="sidebar-top-links">'
            '<a class="sidebar-back-link" href="https://purh.univ-rouen.fr/" target="_blank" rel="noopener">'
            'Retour au catalogue des PURH'
            '</a>'
            '<a class="sidebar-home" href="index.html">Présentation du volume</a>'
            '</div>'
            f'{self._render_nav_list(nav_items)}'
            '</nav>'
        )

    def _render_nav_list(self, items: list[NavItem]) -> str:
        if not items:
            return ''
        html_parts = ['<ul class="nav-list">']
        for item in items:
            classes = ['nav-item']
            if item.children:
                classes.append('has-children')
            if item.is_current:
                classes.append('is-current')
            html_parts.append(f'<li class="{" ".join(classes)}">')
            if item.href:
                html_parts.append(f'<a href="{html.escape(item.href)}">{html.escape(item.title)}</a>')
            else:
                html_parts.append(f'<span class="nav-label">{html.escape(item.title)}</span>')
            html_parts.append(self._render_nav_list(item.children))
            html_parts.append('</li>')
        html_parts.append('</ul>')
        return ''.join(html_parts)

    def _render_toc(self, nav: list[NavItem]) -> str:
        return self._render_nav_list(nav)

    def _render_home_downloads(
        self,
        normalized_tei_href: str | None,
        editor_pdf_href: str | None,
        *,
        latex_href: str | None = None,
        generated_pdf_href: str | None = None,
    ) -> str:
        parts = ['<section class="home-panel home-panel--downloads">']
        parts.append('<h2>Téléchargements</h2>')
        parts.append('<div class="download-buttons">')
        if normalized_tei_href:
            parts.append(
                f'<a class="download-button" href="{html.escape(normalized_tei_href)}" download>'
                'Télécharger le XML-TEI'
                '</a>'
            )
        if latex_href:
            parts.append(
                f'<a class="download-button" href="{html.escape(latex_href)}" download>'
                'Télécharger le LaTeX'
                '</a>'
            )
        if editor_pdf_href:
            parts.append(
                f'<a class="download-button" href="{html.escape(editor_pdf_href)}" download>'
                'Télécharger le PDF éditeur'
                '</a>'
            )
        elif generated_pdf_href:
            parts.append(
                f'<a class="download-button" href="{html.escape(generated_pdf_href)}" download>'
                'Télécharger le PDF généré'
                '</a>'
            )
        parts.append('</div></section>')
        return ''.join(parts)

    def _resolve_back_cover_html(self, tree: etree._ElementTree, config: BuildConfig) -> tuple[str | None, str | None]:
        xml_html = self._extract_back_cover_from_xml(tree)
        if xml_html:
            return xml_html, 'XML (abstract rend="4e-couv")'
        if config.back_cover_path:
            file_html = self._read_back_cover_file(config.back_cover_path)
            if file_html:
                return file_html, str(config.back_cover_path)
        assets_html = self._read_back_cover_from_assets(config.output_assets_dir)
        if assets_html:
            return assets_html, 'assets/quatrieme'
        return None, None

    def _extract_back_cover_from_xml(self, tree: etree._ElementTree) -> str | None:
        nodes = tree.xpath(
            "/tei:TEI/tei:teiHeader/tei:profileDesc/tei:abstract[@rend='4e-couv']",
            namespaces=NSMAP,
        )
        if not nodes:
            return None

        abstract_node = nodes[0]
        if not ''.join(abstract_node.itertext()).strip():
            return None

        wrapper = etree.Element(f"{{{NSMAP['tei']}}}div", nsmap={'tei': NSMAP['tei']})
        for child in abstract_node:
            wrapper.append(copy.deepcopy(child))

        fragment_tree = etree.ElementTree(wrapper)
        result = self.fragment_xslt(
            fragment_tree,
            assets_image_base=etree.XSLT.strparam('assets/images'),
            assets_audio_base=etree.XSLT.strparam('assets/audio'),
            assets_video_base=etree.XSLT.strparam('assets/video'),
        )
        return str(result)

    def _read_back_cover_from_assets(self, output_assets_dir: Path) -> str | None:
        back_cover_dir = output_assets_dir / 'quatrieme'
        if not back_cover_dir.exists() or not back_cover_dir.is_dir():
            return None

        markdown_files = sorted(
            path for path in back_cover_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {'.md', '.markdown'}
        )
        if markdown_files:
            content = markdown_files[0].read_text(encoding='utf-8').strip()
            return self._render_simple_markdown(content) if content else None

        html_files = sorted(
            path for path in back_cover_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {'.html', '.htm'}
        )
        if html_files:
            content = html_files[0].read_text(encoding='utf-8').strip()
            return content or None

        txt_files = sorted(
            path for path in back_cover_dir.iterdir()
            if path.is_file() and path.suffix.lower() == '.txt'
        )
        if txt_files:
            content = txt_files[0].read_text(encoding='utf-8').strip()
            return self._render_simple_markdown(content) if content else None

        return None

    def _read_back_cover_file(self, path: Path) -> str | None:
        if not path.exists() or not path.is_file():
            return None

        content = path.read_text(encoding='utf-8').strip()
        if not content:
            return None

        suffix = path.suffix.lower()
        if suffix in {'.md', '.markdown', '.txt'}:
            return self._render_simple_markdown(content)
        if suffix in {'.html', '.htm'}:
            return content
        return None

    def _render_simple_markdown(self, source: str) -> str:
        blocks = [block.strip() for block in re.split(r"\n\s*\n", source.strip()) if block.strip()]
        if not blocks:
            return ''

        parts: list[str] = []
        list_buffer: list[str] = []

        def flush_list() -> None:
            nonlocal list_buffer
            if list_buffer:
                items = ''.join(f'<li>{self._render_markdown_inline(item)}</li>' for item in list_buffer)
                parts.append(f'<ul>{items}</ul>')
                list_buffer = []

        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if lines and all(line.startswith(('- ', '* ')) for line in lines):
                list_buffer.extend(line[2:].strip() for line in lines)
                continue

            flush_list()
            merged = ' '.join(lines)
            parts.append(f'<p>{self._render_markdown_inline(merged)}</p>')

        flush_list()
        return ''.join(parts)

    def _render_markdown_inline(self, text: str) -> str:
        rendered = html.escape(text)
        substitutions = (
            (r'(?<!\*)\*\*(.+?)\*\*(?!\*)', r'<strong>\1</strong>'),
            (r'(?<!_)__(.+?)__(?!_)', r'<strong>\1</strong>'),
            (r'(?<!\*)\*(.+?)\*(?!\*)', r'<em>\1</em>'),
            (r'(?<!_)_(.+?)_(?!_)', r'<em>\1</em>'),
        )
        for pattern, replacement in substitutions:
            rendered = re.sub(pattern, replacement, rendered)
        return rendered

    def _render_page_header(self, page: PageDef, theme_assets: ThemeAssets) -> str:
        page_anchor = html.escape(page.node_id, quote=True)
        if page_anchor:
            parts = [f'<header class="page-header" id="{page_anchor}">', '<div class="page-header-grid">']
        else:
            parts = ['<header class="page-header">', '<div class="page-header-grid">']
        parts.append(self._render_cover_link(theme_assets, compact=True))
        parts.append('<div class="page-header-main">')
        if page.section_chain:
            parts.append(f'<p class="eyebrow">{html.escape(" / ".join(page.section_chain))}</p>')
        parts.append(f'<h1>{html.escape(page.title)}</h1>')
        if page.subtitle:
            parts.append(f'<p class="subtitle">{html.escape(page.subtitle)}</p>')
        if page.author_entries:
            parts.append(self._render_author_block(page.author_entries))
        elif page.authors:
            parts.append(f'<p class="page-authors">{html.escape(" · ".join(page.authors))}</p>')
        parts.append('</div></div></header>')
        return ''.join(parts)

    def _render_author_block(self, author_entries: list[AuthorEntry]) -> str:
        parts = ['<div class="page-authors">']
        for entry in author_entries:
            parts.append('<div class="author-card">')
            parts.append(f'<div class="author-name">{html.escape(entry.name)}</div>')
            for affiliation in entry.affiliations:
                parts.append(f'<div class="author-affiliation">{html.escape(affiliation)}</div>')
            parts.append('</div>')
        parts.append('</div>')
        return ''.join(parts)

    def _render_prev_next(self, page: PageDef, nav: list[NavItem]) -> str:
        flat: list[tuple[str, str]] = []
        self._flatten_nav(nav, flat)
        current_index = next((idx for idx, (href, _) in enumerate(flat) if href == page.file_name), None)
        if current_index is None:
            return ''
        previous_item = flat[current_index - 1] if current_index > 0 else None
        next_item = flat[current_index + 1] if current_index + 1 < len(flat) else None
        parts = ['<nav class="pager" aria-label="Navigation entre pages">']
        if previous_item:
            parts.append(f'<a class="pager-link" href="{html.escape(previous_item[0])}">← {html.escape(previous_item[1])}</a>')
        else:
            parts.append('<span></span>')
        if next_item:
            parts.append(f'<a class="pager-link pager-link--next" href="{html.escape(next_item[0])}">{html.escape(next_item[1])} →</a>')
        parts.append('</nav>')
        return ''.join(parts)

    def _flatten_nav(self, items: list[NavItem], flat: list[tuple[str, str]]) -> None:
        for item in items:
            if item.href:
                flat.append((item.href, item.title))
            if item.children:
                self._flatten_nav(item.children, flat)

    def _render_banner(self, site_meta: SiteMeta, theme_assets: ThemeAssets) -> str:
        press_label = 'Presses universitaires de Rouen et du Havre'
        book_label = html.escape(site_meta.title)
        subtitle_label = html.escape(site_meta.subtitle)
        creator_names = ' · '.join(html.escape(name) for name in site_meta.creators if name)

        parts = ['<header class="site-banner">', '<div class="site-banner-inner">']
        parts.append('<a class="site-banner-home" href="index.html" aria-label="Retour au sommaire">')
        if theme_assets.purh_logo_href:
            parts.append(f'<img class="site-logo site-logo--purh" src="{html.escape(theme_assets.purh_logo_href)}" alt="{press_label}">')
        else:
            parts.append('<span class="site-logo-text site-logo-text--dark">PURH</span>')
        parts.append('<div class="site-banner-titles">')
        parts.append(f'<div class="site-banner-label">{press_label}</div>')
        parts.append(f'<div class="site-banner-book">{book_label}</div>')
        if subtitle_label:
            parts.append(f'<div class="site-banner-subtitle">{subtitle_label}</div>')
        if creator_names:
            parts.append('<div class="site-banner-creators">')
            parts.append(f'<span class="site-banner-creators-names">{creator_names}</span>')
            parts.append('</div>')
        parts.append('</div>')
        parts.append('</a>')
        parts.append('<div class="site-banner-spacer"></div>')
        if theme_assets.university_logo_href:
            parts.append(f'<img class="site-logo site-logo--univ" src="{html.escape(theme_assets.university_logo_href)}" alt="Université de Rouen Normandie">')
        else:
            parts.append('<span class="site-logo-text site-logo-text--dark site-logo-text--univ">Université de Rouen Normandie</span>')
        parts.append('</div></header>')
        return ''.join(parts)

    def _render_cover_link(self, theme_assets: ThemeAssets, compact: bool) -> str:
        classes = 'book-cover-link book-cover-link--compact' if compact else 'book-cover-link'
        if theme_assets.cover_href:
            cover_href = html.escape(theme_assets.cover_href)
            return (
                f'<button type="button" class="{classes} book-cover-trigger" '
                f'data-lightbox-src="{cover_href}" '
                'data-lightbox-alt="Couverture de l’ouvrage" '
                'data-lightbox-caption="Couverture de l’ouvrage" '
                'aria-label="Agrandir la couverture">'
                f'<img class="book-cover-image" src="{cover_href}" alt="Couverture de l’ouvrage">'
                '</button>'
            )
        return (
            f'<div class="{classes} book-cover-link--placeholder" aria-hidden="true">'
            '<span class="book-cover-placeholder">Couverture</span>'
            '</div>'
        )

    def _discover_theme_assets(self, output_assets_dir: Path) -> ThemeAssets:
        image_exts = {'.png', '.jpg', '.jpeg', '.svg', '.webp', '.gif'}
        candidates = [
            path.relative_to(output_assets_dir).as_posix()
            for path in output_assets_dir.rglob('*')
            if path.is_file() and path.suffix.lower() in image_exts
        ]
        return ThemeAssets(
            cover_href=self._pick_asset(candidates, [
                ['images', 'cover'],
                ['images', 'couverture'],
                ['cover'],
                ['couverture'],
                ['premiere', 'couv'],
                ['1ere', 'couv'],
                ['couv'],
            ]),
            university_logo_href=self._pick_asset(candidates, [
                ['logos', 'universite'],
                ['logos', 'university'],
                ['logos', 'urn'],
                ['universite'],
                ['university'],
                ['urn'],
            ]),
            purh_logo_href=self._pick_asset(candidates, [
                ['logos', 'purh'],
                ['logos', 'presses'],
                ['purh'],
                ['presses'],
            ]),
            footer_logo_href=self._pick_asset(candidates, [
                ['logos', 'logo_footer'],
                ['logos', 'footer'],
            ]),
            pdf_href=self._discover_pdf_href(output_assets_dir),
        )

    def _pick_asset(self, candidates: list[str], token_sets: list[list[str]]) -> str | None:
        lowered = [(candidate, candidate.lower()) for candidate in candidates]
        for tokens in token_sets:
            for candidate, lower in lowered:
                if all(token in lower for token in tokens):
                    return f'assets/{candidate}'
        return None

    def _discover_pdf_href(self, output_assets_dir: Path) -> str | None:
        for child in output_assets_dir.iterdir():
            if child.is_dir() and child.name.lower() == "pdf":
                pdf_files = sorted(
                    path for path in child.rglob("*")
                    if path.is_file() and path.suffix.lower() == ".pdf"
                )
                if pdf_files:
                    relative = pdf_files[0].relative_to(output_assets_dir).as_posix()
                    return f'assets/{relative}'
        return None


    def _render_footer(self, theme_assets: ThemeAssets) -> str:
        parts = [
            '<footer class="site-footer">',
            '<p>',
            'Livre web créé avec le système ',
            '<a href="https://github.com/Gheeraert/impression" target="_blank" rel="noopener">Impressions</a>. ',
            'Impressions est une création des PURH et de la ',
            '<a href="https://ceen.hypotheses.org/" target="_blank" rel="noopener">chaire d’excellence en édition numérique</a>.',
            '</p>',
        ]
        if theme_assets.footer_logo_href:
            parts.append(
                '<div class="site-footer-logo-wrap">'
                '<a href="https://ceen.hypotheses.org/" target="_blank" rel="noopener">'
                f'<img class="site-footer-logo" src="{html.escape(theme_assets.footer_logo_href)}" '
                'alt="Logo de la chaire d’excellence en édition numérique">'
                '</a>'
                '</div>'
            )
        parts.append('</footer>')
        return ''.join(parts)


    def _wrap_html(
        self,
        page_title: str,
        site_meta: SiteMeta,
        nav_html: str,
        content_html: str,
        theme_assets: ThemeAssets,
        page_grid_class: str = 'page-grid',
        page: PageDef | None = None,
        abstract_html: str | None = None,
        citation_pdf_href: str | None = None,
    ) -> str:
        banner = self._render_banner(site_meta, theme_assets)
        zotero_meta = render_zotero_meta(
            site_meta,
            theme_assets,
            page=page,
            abstract_html=abstract_html,
            citation_pdf_href=citation_pdf_href,
        )
        return f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(page_title)}</title>
  <link rel="stylesheet" href="assets/site.css">
  {zotero_meta}
</head>
<body>
  {banner}
  <div class="layout">
    <aside class="sidebar">
      {nav_html}
    </aside>
    <main class="content">
      <div class="{html.escape(page_grid_class)}">
        <div class="page-main">
          {content_html}
        </div>
        <aside class="margin-notes" id="margin-notes" aria-label="Notes marginales"></aside>
      </div>
    </main>
  </div>
  <script src="assets/app.js"></script>
</body>
</html>
'''
