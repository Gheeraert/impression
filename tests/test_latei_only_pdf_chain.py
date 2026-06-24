from __future__ import annotations

"""Verify that the LaTEI chain is the sole active PDF chain.

Checks:
1. site_builder.py contains no imports from the removed stable-PDF modules.
2. No module under purh_site/ imports the removed stable-PDF modules.
3. Modes latei and latei_pdf are accepted by the site builder.
4. Legacy modes latex and latex_pdf are no longer accepted (fall back to none).
"""

from pathlib import Path

PURH_SITE = Path("purh_site")
REMOVED_SYMBOLS = [
    "stable_pdf_export",
    "pdf_builder",
    "latex_renderer",
    "semantic_model",
    "tei_to_model",
    "latei_stable_pdf",
    "latei_convergence_audit",
    "PdfBuilder",
    "LatexRenderer",
    "LatexRenderOptions",
    "SemanticBook",
    "parse_normalized_tei",
    "build_stable_pdf_artifacts",
]


def test_site_builder_has_no_legacy_imports() -> None:
    import_lines = [
        line
        for line in (PURH_SITE / "site_builder.py").read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith("import ") or line.lstrip().startswith("from ")
    ]
    source = "\n".join(import_lines)
    for pattern in [
        "stable_pdf_export",
        "pdf_builder",
        "latex_renderer",
        "semantic_model",
        "tei_to_model",
        "latei_stable_pdf",
        "latei_convergence_audit",
    ]:
        assert pattern not in source, (
            f"site_builder.py still imports removed module: {pattern!r}"
        )


REMOVED_IMPORT_PATTERNS = [
    "from .stable_pdf_export",
    "from .pdf_builder",
    "from .latex_renderer",
    "from .semantic_model",
    "from .tei_to_model",
    "from .latei_stable_pdf",
    "from .latei_convergence_audit",
    "import stable_pdf_export",
    "import pdf_builder",
    "import latex_renderer",
    "import semantic_model",
    "import tei_to_model",
    "import latei_stable_pdf",
    "import latei_convergence_audit",
]


def test_purh_site_has_no_legacy_imports() -> None:
    for py_file in PURH_SITE.glob("*.py"):
        import_lines = [
            line
            for line in py_file.read_text(encoding="utf-8").splitlines()
            if line.lstrip().startswith("import ") or line.lstrip().startswith("from ")
        ]
        source = "\n".join(import_lines)
        for pattern in REMOVED_IMPORT_PATTERNS:
            assert pattern not in source, (
                f"{py_file.name} still imports removed module via: {pattern!r}"
            )


def test_latei_modes_are_accepted() -> None:
    from purh_site.site_builder import SiteBuilder
    builder = SiteBuilder()
    assert builder._normalized_pdf_export_mode("latei") == "latei"
    assert builder._normalized_pdf_export_mode("latei_pdf") == "latei_pdf"


def test_legacy_modes_fall_back_to_none() -> None:
    from purh_site.site_builder import SiteBuilder
    builder = SiteBuilder()
    assert builder._normalized_pdf_export_mode("latex") == "none"
    assert builder._normalized_pdf_export_mode("latex_pdf") == "none"


def test_none_mode_is_accepted() -> None:
    from purh_site.site_builder import SiteBuilder
    builder = SiteBuilder()
    assert builder._normalized_pdf_export_mode("none") == "none"
    assert builder._normalized_pdf_export_mode("") == "none"
    assert builder._normalized_pdf_export_mode("unknown") == "none"


def test_removed_modules_are_not_importable() -> None:
    import importlib
    removed_modules = [
        "purh_site.pdf_builder",
        "purh_site.latex_renderer",
        "purh_site.semantic_model",
        "purh_site.tei_to_model",
        "purh_site.stable_pdf_export",
        "purh_site.latei_stable_pdf",
        "purh_site.latei_convergence_audit",
    ]
    for module_name in removed_modules:
        try:
            importlib.import_module(module_name)
            raise AssertionError(f"Module {module_name!r} should have been removed but is still importable.")
        except ModuleNotFoundError:
            pass
