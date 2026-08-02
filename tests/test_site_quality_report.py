from __future__ import annotations

from pathlib import Path

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder
from purh_site.site_quality import run_site_quality_checks


def write_html(path: Path, body: str) -> None:
    path.write_text(f"<!DOCTYPE html><html><head><title>Test</title></head><body>{body}</body></html>", encoding="utf-8")


def test_quality_check_reports_broken_same_page_anchor(tmp_path: Path) -> None:
    write_html(tmp_path / "page.html", '<a href="#absent">lien cassé</a>')

    issues = run_site_quality_checks(tmp_path)

    assert any("page.html" in issue and "#absent" in issue for issue in issues)


def test_quality_check_reports_broken_cross_page_anchor_and_missing_html(tmp_path: Path) -> None:
    write_html(tmp_path / "page.html", '<a href="other.html#missing">section absente</a><a href="missing.html">page absente</a>')
    write_html(tmp_path / "other.html", '<section id="present">Texte</section>')

    issues = run_site_quality_checks(tmp_path)

    assert any("page.html" in issue and "other.html#missing" in issue for issue in issues)
    assert any("page.html" in issue and "missing.html" in issue for issue in issues)


def test_quality_check_reports_missing_local_resources(tmp_path: Path) -> None:
    write_html(
        tmp_path / "page.html",
        '<img src="assets/images/missing.png"><script src="assets/app.js"></script><link rel="stylesheet" href="assets/site.css">',
    )
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("", encoding="utf-8")
    (tmp_path / "assets" / "site.css").write_text("", encoding="utf-8")

    issues = run_site_quality_checks(tmp_path)

    assert any("assets/images/missing.png" in issue for issue in issues)
    assert not any("assets/app.js" in issue for issue in issues)
    assert not any("assets/site.css" in issue for issue in issues)


def test_quality_check_reports_empty_attributes_and_duplicate_ids(tmp_path: Path) -> None:
    write_html(tmp_path / "page.html", '<a href="">vide</a><img src=""><div id=""></div><p id="dup"></p><section id="dup"></section>')

    issues = run_site_quality_checks(tmp_path)

    assert any("attribut href vide" in issue for issue in issues)
    assert any("attribut src vide" in issue for issue in issues)
    assert any("attribut id vide" in issue for issue in issues)
    assert any('id HTML dupliqué "dup"' in issue for issue in issues)


def test_quality_check_ignores_external_and_data_urls(tmp_path: Path) -> None:
    write_html(
        tmp_path / "page.html",
        '<a href="https://example.org">externe</a><a href="mailto:test@example.org">mail</a><img src="data:image/png;base64,AAAA">',
    )

    assert run_site_quality_checks(tmp_path) == []


def test_build_report_contains_quality_ok_for_healthy_site(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    assets_images = tmp_path / "assets" / "images"
    assets_images.mkdir(parents=True)
    (assets_images / "figure.png").write_text("fake", encoding="utf-8")
    xml_path.write_text(
        """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre sain</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group xml:id='chapitre-1' type='chapter' data-page-title='Chapitre 1'>
        <body>
          <div xml:id='section-1' type='section1'>
            <head>Section 1</head>
            <p>Voir <ref target='#section-1'>la section</ref><note>Une note.</note></p>
            <figure><graphic url='figure.png'/><figDesc>Figure présente.</figDesc></figure>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )

    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site", assets_dir=tmp_path / "assets"))
    report = result.report_path.read_text(encoding="utf-8")

    assert "Contrôle qualité du site :" in report
    assert "- OK" in report


def test_build_report_contains_quality_warning_without_failing_build(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre avec alerte</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group xml:id='chapitre-1' type='chapter' data-page-title='Chapitre 1'>
        <body>
          <div type='section1'>
            <head>Section 1</head>
            <p>Voir <ref target='#absent'>une cible absente</ref>.</p>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )

    result = SiteBuilder().build_from_master(xml_path, BuildConfig(output_dir=tmp_path / "site"))
    report = result.report_path.read_text(encoding="utf-8")

    assert result.html_path.exists()
    assert "Contrôle qualité du site :" in report
    assert "[WARNING]" in report
    assert "#absent" in report
