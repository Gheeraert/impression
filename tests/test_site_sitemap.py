from __future__ import annotations

from pathlib import Path

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder

_TITLE_STMT = "<title type='main'>Livre sitemap</title><author>Auteur, Une</author>"

_ONE_CHAPTER = """
<group xml:id='chapitre' type='chapter' data-page-title='Chapitre un'>
  <body>
    <div type='section1'>
      <head>Chapitre un</head>
      <p>Texte.</p>
    </div>
  </body>
</group>
"""


def _build_site(tmp_path: Path, publication_stmt: str) -> Path:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>{_TITLE_STMT}</titleStmt>
      <publicationStmt>{publication_stmt}</publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      {_ONE_CHAPTER}
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))
    return result.output_dir


_PUBLICATION_STMT_WITH_SITE_URL = """
<publisher>PURH</publisher>
<date when='2024'>2024</date>
<ab type='digital_online'>
  <ref type='site' target='https://example.org/livre/'/>
</ab>
"""

_PUBLICATION_STMT_WITHOUT_SITE_URL = "<publisher>PURH</publisher><date when='2024'>2024</date>"


def test_sitemap_and_robots_are_generated_when_site_url_is_known(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITH_SITE_URL)

    sitemap_path = output_dir / "sitemap.xml"
    robots_path = output_dir / "robots.txt"
    assert sitemap_path.exists()
    assert robots_path.exists()

    sitemap = sitemap_path.read_text(encoding="utf-8")
    assert "<urlset" in sitemap
    assert "<loc>https://example.org/livre/index.html</loc>" in sitemap
    assert "<loc>https://example.org/livre/01-chapitre-un.html</loc>" in sitemap

    robots = robots_path.read_text(encoding="utf-8")
    assert "User-agent: *" in robots
    assert "Allow: /" in robots
    assert "Sitemap: https://example.org/livre/sitemap.xml" in robots


def test_sitemap_and_robots_are_skipped_without_site_url(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITHOUT_SITE_URL)

    assert not (output_dir / "sitemap.xml").exists()
    assert not (output_dir / "robots.txt").exists()

    report = (output_dir / "build_report.txt").read_text(encoding="utf-8")
    assert "sitemap.xml et robots.txt non générés" in report
    assert "site_url absent" in report


def test_sitemap_lists_exactly_one_url_per_page(tmp_path: Path) -> None:
    output_dir = _build_site(tmp_path, _PUBLICATION_STMT_WITH_SITE_URL)
    sitemap = (output_dir / "sitemap.xml").read_text(encoding="utf-8")

    # Home page + the one chapter defined above.
    assert sitemap.count("<url>") == 2
    assert sitemap.count("</url>") == 2
