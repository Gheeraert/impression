from __future__ import annotations

from pathlib import Path

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder, normalize_french_typography_html


def test_french_typography_normalizes_double_punctuation() -> None:
    source = "<p>Mot : suite ; encore ? oui ! fin.</p>"
    result = normalize_french_typography_html(source)

    assert "Mot\u202f: suite\u202f; encore\u202f? oui\u202f! fin." in result


def test_french_typography_normalizes_french_quotes_and_apostrophes() -> None:
    source = "<p>Il dit « texte » puis l'homme répond d'abord qu'il vient.</p>"
    result = normalize_french_typography_html(source)

    assert "«\u202ftexte\u202f»" in result
    assert "l’homme" in result
    assert "d’abord" in result
    assert "qu’il" in result


def test_french_typography_superscripts_simple_centuries() -> None:
    source = "<p>Le XVIIe siècle répond au XIXe siècle.</p>"
    result = normalize_french_typography_html(source)

    assert "XVII<sup>e</sup> siècle" in result
    assert "XIX<sup>e</sup> siècle" in result


def test_french_typography_does_not_touch_html_attributes() -> None:
    source = (
        '<p data-title="mot : suite">'
        'Mot : suite <a href="https://example.org?a=b:c">lien : visible</a>'
        "</p>"
    )
    result = normalize_french_typography_html(source)

    assert 'data-title="mot : suite"' in result
    assert 'href="https://example.org?a=b:c"' in result
    assert "Mot\u202f: suite" in result
    assert "lien\u202f: visible" in result


def test_french_typography_protects_code_and_pre() -> None:
    source = (
        "<p>Texte : corrigé.</p>"
        "<code>code : intact et l'homme</code>"
        "<pre>pre : intact et qu'il</pre>"
    )
    result = normalize_french_typography_html(source)

    assert "<p>Texte\u202f: corrigé.</p>" in result
    assert "<code>code : intact et l'homme</code>" in result
    assert "<pre>pre : intact et qu'il</pre>" in result


def test_site_builder_applies_french_typography_to_generated_pages(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt><title type='main'>Livre typo</title></titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre typo'>
        <body>
          <div type='section1'>
            <head>Section</head>
            <p>l'homme dit « bonjour » : XVIIe siècle !</p>
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
    page_html = (result.output_dir / "01-chapitre-typo.html").read_text(encoding="utf-8")

    assert "l’homme dit «\u202fbonjour\u202f»\u202f: XVII<sup>e</sup> siècle\u202f!" in page_html


def test_french_typography_preserves_named_html_entities() -> None:
    source = "<p>Racine &amp; Shakespeare&nbsp;: exemple</p>"
    result = normalize_french_typography_html(source)

    assert "&amp;" in result
    assert "&nbsp;" in result
    assert "&amp\u202f;" not in result
    assert "&nbsp\u202f;" not in result
    assert "&nbsp;\u202f:" not in result
    assert "Shakespeare&nbsp;: exemple" in result


def test_french_typography_preserves_numeric_html_entities() -> None:
    source = "<p>XVII&#160;siècle &lt; texte &gt;</p>"
    result = normalize_french_typography_html(source)

    assert "&#160;" in result
    assert "&lt;" in result
    assert "&gt;" in result
    assert "&#160\u202f;" not in result


def test_french_typography_still_works_around_entities() -> None:
    source = "<p>Racine &amp; Shakespeare : suite</p>"
    result = normalize_french_typography_html(source)

    assert "Racine &amp; Shakespeare\u202f: suite" in result


def test_french_typography_does_not_duplicate_spacing_after_numeric_nbsp_entity() -> None:
    source = "<p>XVII&#160;: exemple</p>"
    result = normalize_french_typography_html(source)

    assert "XVII&#160;: exemple" in result
    assert "&#160;\u202f:" not in result
