from __future__ import annotations

"""Tests d'intégration pour les modes pdf_export_mode="latei" et "latei_pdf" dans SiteBuilder.

Passe E6 — LaTEI est l'unique chaîne PDF/LaTeX active.
Les seuls modes valides sont : none, latei, latei_pdf.
"""

from pathlib import Path

import pytest

from purh_site.config import BuildConfig
import purh_site.reversible_integration as reversible_integration
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

def test_latei_mode_produces_book_tex_manifest_and_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    def forbidden_compile(*args, **kwargs):
        raise AssertionError("compile_latei_pdf must not be called in latei mode")

    monkeypatch.setattr(reversible_integration, "compile_latei_pdf", forbidden_compile)

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(
            output_dir=tmp_path / "site",
            pdf_export_mode="latei",
            latex_engine="moteur-latei-introuvable",
        ),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    index_html = result.html_path.read_text(encoding="utf-8")
    build_report = result.report_path.read_text(encoding="utf-8")

    assert (generated / "book.tex").exists(), "book.tex doit exister"
    assert (generated / "book.latei_manifest.json").exists(), "manifeste doit exister"
    assert (generated / "pdf_build_report.txt").exists(), "pdf_build_report.txt doit exister"
    assert not (generated / "book.pdf").exists(), "book.pdf ne doit pas exister en mode latei"
    assert not list(generated.glob("*.pdf")), "aucun PDF ne doit etre produit en mode latei"
    assert not list(generated.glob("*_build.log")), "aucun log LuaLaTeX ne doit etre produit en mode latei"

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
# Test 3 — mode latei_pdf sans LuaLaTeX (déterministe via faux moteur)
# ---------------------------------------------------------------------------

def test_latei_pdf_mode_is_robust_without_lualatex(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(
            output_dir=tmp_path / "site",
            pdf_export_mode="latei_pdf",
            latex_engine="moteur-latei-inexistant",
        ),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    build_report = result.report_path.read_text(encoding="utf-8")

    assert result.html_path.exists(), "le site HTML doit être produit même sans LuaLaTeX"
    assert (generated / "book.tex").exists(), "book.tex doit exister même sans LuaLaTeX"
    assert (generated / "pdf_build_report.txt").exists()
    assert not (generated / "book.pdf").exists(), "book.pdf ne doit pas exister si le moteur est absent"
    assert "[WARNING] PDF non généré" in build_report
    assert "Voir : assets/generated/pdf_build_report.txt" in build_report


def test_latei_pdf_mode_invokes_compilation_and_copies_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")
    calls: list[Path] = []

    def fake_compile(main_tex_path, pdf_path, *, log_path=None, latex_engine="lualatex", **kwargs):
        pdf_path = Path(pdf_path)
        log_path = Path(log_path) if log_path is not None else pdf_path.with_name(f"{pdf_path.stem}_build.log")
        calls.append(Path(main_tex_path))
        pdf_path.write_bytes(b"%PDF fake")
        log_path.write_text("fake compile", encoding="utf-8")
        return reversible_integration.LateiPdfResult(
            pdf_path=pdf_path,
            log_path=log_path,
            success=True,
            message="fake compiled",
        )

    monkeypatch.setattr(reversible_integration, "compile_latei_pdf", fake_compile)

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(
            output_dir=tmp_path / "site",
            pdf_export_mode="latei_pdf",
            latex_engine="fake-lualatex",
        ),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    build_report = result.report_path.read_text(encoding="utf-8")

    assert len(calls) == 2
    assert (generated / "book.tex").exists()
    assert (generated / "book.pdf").exists()
    assert (generated / "book.pdf").read_bytes() == b"%PDF fake"
    assert "assets/generated/book.pdf" in build_report


def test_latei_pdf_mode_produces_pdf_when_lualatex_available(tmp_path: Path) -> None:
    import shutil as _shutil
    if _shutil.which("lualatex") is None:
        import pytest
        pytest.skip("lualatex absent sur cette machine")

    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / "site", pdf_export_mode="latei_pdf"),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    book_pdf = generated / "book.pdf"
    build_report = result.report_path.read_text(encoding="utf-8")

    assert (generated / "book.tex").exists()
    assert book_pdf.exists(), "book.pdf doit exister si lualatex est disponible"
    assert book_pdf.stat().st_size > 0
    assert "assets/generated/book.pdf" in build_report


# ---------------------------------------------------------------------------
# Test 4 — modes legacy ignorés après E6
# ---------------------------------------------------------------------------

def test_legacy_latex_mode_falls_back_to_none(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / "site", pdf_export_mode="latex"),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    assert not (generated / "book.tex").exists(), "latex mode doit être traité comme none (E6)"
    assert not (generated / "book.pdf").exists()


def test_legacy_latex_pdf_mode_falls_back_to_none(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    result = SiteBuilder().build_from_master(
        xml_path,
        BuildConfig(output_dir=tmp_path / "site", pdf_export_mode="latex_pdf"),
    )

    generated = tmp_path / "site" / "assets" / "generated"
    assert not (generated / "book.tex").exists(), "latex_pdf mode doit être traité comme none (E6)"
    assert not (generated / "book.pdf").exists()


def test_none_mode_produces_no_artifacts(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(TEI_SAMPLE, encoding="utf-8")

    SiteBuilder().build_from_master(
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
