from __future__ import annotations

"""Tests d'intégration pour les modes pdf_export_mode="latei" et "latei_pdf" dans SiteBuilder.

Passe E2 — ces tests vérifient que les nouveaux modes LaTEI sont branchés dans
site_builder.py sans régresser les modes stables existants.
"""

from pathlib import Path

from purh_site.config import BuildConfig
from purh_site.site_builder import SiteBuilder


TEI_SAMPLE = """<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0'>
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type='main'>Livre LaTEI test</title>
      </titleStmt>
      <publicationStmt><p/></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type='book'>
      <group type='chapter' data-page-title='Chapitre test'>
        <body>
          <div type='section1'>
            <head>Section test</head>
            <p>Texte de test LaTEI.</p>
          </div>
        </body>
      </group>
    </group>
  </text>
</TEI>
"""


# ---------------------------------------------------------------------------
# Test 1 — mode latei produit book.tex, manifeste, rapport
# ---------------------------------------------------------------------------

def test_latei_mode_produces_book_tex_manifest_and_report(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / "site", pdf_export_mode="latei"),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    index_html = result.html_path.read_text(encoding="utf-8")
    build_report = result.report_path.read_text(encoding="utf-8")

    assert (generated / "book.tex").exists(), "book.tex doit exister"
    assert (generated / "book.latei_manifest.json").exists(), "manifeste doit exister"
    assert (generated / "pdf_build_report.txt").exists(), "pdf_build_report.txt doit exister"

    assert 'href="assets/generated/book.tex"' in index_html, "lien LaTeX dans le HTML"
    assert "Télécharger le LaTeX" in index_html

    assert "LaTeX généré : assets/generated/book.tex" in build_report


# ---------------------------------------------------------------------------
# Test 2 — book.tex est un monofichier LaTEI (pas de \input{)
# ---------------------------------------------------------------------------

def test_latei_mode_book_tex_is_monofile(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / "site", pdf_export_mode="latei"),
    )

    book_tex = tmp_path / "site" / "assets" / "generated" / "book.tex"
    content = book_tex.read_text(encoding="utf-8")

    assert r"\begin{lateiDocument}" in content
    assert r"\input{" not in content


# ---------------------------------------------------------------------------
# Test 3 — mode latei_pdf robuste avec ou sans LuaLaTeX
# ---------------------------------------------------------------------------

def test_latei_pdf_mode_is_robust_with_or_without_lualatex(tmp_path: Path) -> None:
    """Vérifie le comportement de latei_pdf selon que LuaLaTeX est présent ou non.

    Contrairement à la chaîne stable, la chaîne LaTEI gère son propre moteur
    LaTeX et n'honore pas encore le paramètre latex_engine de BuildConfig.
    Ce test est donc adaptatif : il observe ce que la chaîne a produit et
    vérifie les invariants correspondant au résultat réel.
    """
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / "site", pdf_export_mode="latei_pdf"),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    build_report = result.report_path.read_text(encoding="utf-8")
    book_pdf = generated / "book.pdf"

    # Invariants communs, quelle que soit la disponibilité de LuaLaTeX
    assert result.html_path.exists(), "le site HTML doit être produit"
    assert (generated / "book.tex").exists(), "book.tex doit exister"
    assert (generated / "pdf_build_report.txt").exists(), "pdf_build_report.txt doit exister"

    if book_pdf.exists():
        # LuaLaTeX était disponible
        assert "PDF généré : assets/generated/book.pdf" in build_report
        assert book_pdf.stat().st_size > 0, "book.pdf ne doit pas être vide"
    else:
        # LuaLaTeX était absent
        assert "[WARNING] PDF non généré" in build_report
        assert "Voir : assets/generated/pdf_build_report.txt" in build_report


# ---------------------------------------------------------------------------
# Test 4 — modes stables inchangés après E2
# ---------------------------------------------------------------------------

def test_stable_latex_mode_still_works(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / "site", pdf_export_mode="latex"),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    assert (generated / "book.tex").exists()
    assert 'href="assets/generated/book.tex"' in result.html_path.read_text(encoding="utf-8")
    assert "LaTeX généré : assets/generated/book.tex" in result.report_path.read_text(encoding="utf-8")


def test_stable_none_mode_still_works(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / "site", pdf_export_mode="none"),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    assert not (generated / "book.tex").exists()
    assert not (generated / "book.pdf").exists()


# ---------------------------------------------------------------------------
# Test 5 — PDF éditeur court-circuite les modes LaTEI
# ---------------------------------------------------------------------------

def test_editor_pdf_disables_latei_mode(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    assets_dir = tmp_path / "source_assets"
    editor_pdf = assets_dir / "PDF" / "ouvrage.pdf"
    editor_pdf.parent.mkdir(parents=True)
    editor_pdf.write_bytes(b"%PDF-editor")

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(
            output_dir=tmp_path / "site",
            assets_dir=assets_dir,
            pdf_export_mode="latei_pdf",
        ),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    index_html = result.html_path.read_text(encoding="utf-8")
    build_report = result.report_path.read_text(encoding="utf-8")

    assert not (generated / "book.tex").exists()
    assert not (generated / "book.pdf").exists()
    assert "Génération LaTeX/PDF : désactivée car un PDF éditeur est disponible." in build_report
    assert "Télécharger le PDF éditeur" in index_html
    assert "Télécharger le LaTeX" not in index_html
