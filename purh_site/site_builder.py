from __future__ import annotations

import copy
import html
import shutil
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from .config import BuildConfig
from .normalizer import NormalizeReport, TeiNormalizer
from .site_structure import NavItem, PageDef, SiteMeta, SiteStructureBuilder
from .tei_loader import LoadReport, TeiLoader, load_many
from .utils import NSMAP, ensure_dir


@dataclass(slots=True)
class BuildResult:
    output_dir: Path
    html_path: Path
    normalized_tei_path: Path | None
    report_path: Path


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

    def build_from_many(self, xml_files: list[Path], output_root: Path, assets_dir: Path | None = None) -> list[BuildResult]:
        results: list[BuildResult] = []
        for tree, load_report in load_many(xml_files):
            normalize_report = self.normalizer.normalize(tree)
            target_dir = output_root / Path(load_report.master_path).stem
            config = BuildConfig(output_dir=target_dir, assets_dir=assets_dir)
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
        self._write_index_page(config.output_dir, site_meta, nav)
        for page in pages:
            self._write_content_page(config.output_dir, tree, site_meta, nav, page)

        report_path = config.output_dir / "build_report.txt"
        report_lines = [
            load_report.as_text(),
            "Normalisation :",
            *normalize_report.as_lines(),
            "",
            f"Pages générées : {1 + len(pages)}",
        ]
        report_lines.extend(f"- {page.file_name} ← {page.title}" for page in pages)
        report_path.write_text("\n".join(report_lines), encoding="utf-8")

        return BuildResult(
            output_dir=config.output_dir,
            html_path=config.output_dir / "index.html",
            normalized_tei_path=normalized_tei_path,
            report_path=report_path,
        )

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

    def _write_index_page(self, output_dir: Path, site_meta: SiteMeta, nav: list[NavItem]) -> None:
        nav_html = self._render_sidebar(nav, current_file_name=None)
        content = [f'<section class="home-hero"><p class="eyebrow">Livre web PURH</p><h1>{html.escape(site_meta.title)}</h1>']
        if site_meta.subtitle:
            content.append(f'<p class="subtitle">{html.escape(site_meta.subtitle)}</p>')
        if site_meta.creators:
            content.append(f'<p class="meta-line">{html.escape(" · ".join(site_meta.creators))}</p>')
        content.append('</section>')
        content.append('<section class="home-panel"><h2>Sommaire</h2>')
        content.append(self._render_toc(nav))
        content.append('</section>')
        page_html = self._wrap_html(
            page_title=site_meta.title,
            site_meta=site_meta,
            nav_html=nav_html,
            content_html=''.join(content),
        )
        (output_dir / 'index.html').write_text(page_html, encoding='utf-8')

    def _write_content_page(
        self,
        output_dir: Path,
        tree: etree._ElementTree,
        site_meta: SiteMeta,
        nav: list[NavItem],
        page: PageDef,
    ) -> None:
        page_group = self._find_page_group(tree, page.node_id)
        if page_group is None:
            return
        fragment_html = self._render_page_fragment(page_group)
        nav_html = self._render_sidebar(nav, current_file_name=page.file_name)
        page_header = [f'<header class="page-header"><p class="eyebrow">{html.escape(" / ".join(page.section_chain))}</p>' if page.section_chain else '<header class="page-header">']
        page_header.append(f'<h1>{html.escape(page.title)}</h1>')
        if page.subtitle:
            page_header.append(f'<p class="subtitle">{html.escape(page.subtitle)}</p>')
        if page.authors:
            page_header.append(f'<p class="page-authors">{html.escape(" · ".join(page.authors))}</p>')
        page_header.append('</header>')
        credits = self._render_credit_block(page, site_meta)
        pager = self._render_prev_next(page, nav)
        full_content = ''.join(page_header) + fragment_html + credits + pager
        page_html = self._wrap_html(
            page_title=f"{page.title} — {site_meta.title}",
            site_meta=site_meta,
            nav_html=nav_html,
            content_html=full_content,
        )
        (output_dir / page.file_name).write_text(page_html, encoding='utf-8')

    def _find_page_group(self, tree: etree._ElementTree, node_id: str) -> etree._Element | None:
        matches = tree.xpath(f"//*[@xml:id='{node_id}']", namespaces=NSMAP)
        return matches[0] if matches else None

    def _render_page_fragment(self, page_group: etree._Element) -> str:
        cloned = copy.deepcopy(page_group)
        self._renumber_fragment_notes(cloned)
        fragment_tree = etree.ElementTree(cloned)
        result = self.fragment_xslt(fragment_tree, assets_base=etree.XSLT.strparam('assets'))
        return str(result)

    def _renumber_fragment_notes(self, root: etree._Element) -> None:
        for index, note in enumerate(root.xpath('.//tei:note', namespaces=NSMAP), start=1):
            note.set('n', str(index))

    def _render_sidebar(self, nav: list[NavItem], current_file_name: str | None) -> str:
        nav_items = self.structure_builder.build_nav_for_page(nav, current_file_name)
        return (
            '<nav class="sidebar-nav" aria-label="Sommaire du livre">'
            f'<a class="sidebar-home" href="index.html">Accueil</a>{self._render_nav_list(nav_items)}'
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

    def _render_credit_block(self, page: PageDef, site_meta: SiteMeta) -> str:
        if page.page_kind == 'article' and page.authors:
            citation = [html.escape(' ; '.join(page.authors)), f'« {html.escape(page.title)} »', f'dans {html.escape(site_meta.title)}']
            if site_meta.publisher:
                citation.append(html.escape(site_meta.publisher))
            if site_meta.publication_year:
                citation.append(html.escape(site_meta.publication_year))
            citation.append(f'[page {html.escape(page.file_name)}]')
            body = (
                '<section class="credit-box">'
                '<h2>Crédits et citabilité</h2>'
                f'<p><strong>Auteur·rice(s)</strong> : {html.escape(" · ".join(page.authors))}</p>'
                f'<p><strong>Contribution</strong> : {html.escape(page.title)}</p>'
                f'<p><strong>Pour citer cette contribution</strong> : {". ".join(citation)}.</p>'
                '</section>'
            )
            return body

        return (
            '<section class="credit-box">'
            '<h2>Crédits</h2>'
            f'<p><strong>Livre</strong> : {html.escape(site_meta.title)}</p>'
            f'<p><strong>Section</strong> : {html.escape(page.title)}</p>'
            '</section>'
        )

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

    def _wrap_html(self, page_title: str, site_meta: SiteMeta, nav_html: str, content_html: str) -> str:
        site_title = html.escape(site_meta.title)
        subtitle = f'<p class="header-subtitle">{html.escape(site_meta.subtitle)}</p>' if site_meta.subtitle else ''
        return f'''<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>{html.escape(page_title)}</title>
    <link rel="stylesheet" href="assets/site.css"/>
    <script src="assets/app.js" defer="defer"></script>
  </head>
  <body>
    <header class="site-header">
      <div class="site-header__inner">
        <div>
          <a class="brand" href="index.html">{site_title}</a>
          {subtitle}
        </div>
      </div>
    </header>
    <div class="layout">
      <aside class="sidebar">{nav_html}</aside>
      <main class="content-area">{content_html}</main>
    </div>
  </body>
</html>
'''
