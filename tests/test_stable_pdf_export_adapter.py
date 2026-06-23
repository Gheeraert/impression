from __future__ import annotations

from pathlib import Path


def test_site_builder_does_not_import_pdf_builder_directly() -> None:
    source = Path("purh_site/site_builder.py").read_text(encoding="utf-8")
    assert "PdfBuilder" not in source
    assert "LatexRenderOptions" not in source
    assert "from .pdf_builder" not in source
    assert "from .latex_renderer" not in source


def test_stable_pdf_export_is_gateway_to_pdf_builder() -> None:
    source = Path("purh_site/stable_pdf_export.py").read_text(encoding="utf-8")
    assert "PdfBuilder" in source
    assert "LatexRenderOptions" in source
    assert "build_stable_pdf_artifacts" in source


def test_build_stable_pdf_artifacts_is_importable_and_callable() -> None:
    from purh_site.stable_pdf_export import build_stable_pdf_artifacts
    assert callable(build_stable_pdf_artifacts)


def test_pdf_build_result_re_exported_from_adapter() -> None:
    from purh_site.stable_pdf_export import PdfBuildResult
    assert PdfBuildResult is not None
