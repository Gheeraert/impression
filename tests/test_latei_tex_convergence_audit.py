from __future__ import annotations

from pathlib import Path

import pytest

from purh_site.latei_convergence_audit import run_latei_tex_convergence_audit


FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


@pytest.fixture(scope="module")
def tex_audit(tmp_path_factory: pytest.TempPathFactory):
    output_dir = tmp_path_factory.mktemp("latei_tex_convergence")
    return run_latei_tex_convergence_audit(FIXTURE_PATH, output_dir)


def test_latei_tex_convergence_audit_report_is_produced(tex_audit) -> None:
    report = tex_audit.report_path.read_text(encoding="utf-8")

    assert tex_audit.report_path.exists()
    assert "Audit TeX Stable Vs LaTEI Direct" in report
    assert "Stable `book.tex`" in report
    assert "LaTEI main" in report
    assert "LaTEI macros" in report
    assert "LaTEI body" in report


def test_latei_tex_convergence_audit_has_required_sections(tex_audit) -> None:
    report = tex_audit.report_path.read_text(encoding="utf-8")

    assert "## Title page audit" in report
    assert "## Footnote audit" in report
    assert "## Paragraph audit" in report
    assert "## Figure audit" in report
    assert "## Bibliography audit" in report
    assert "## Tables and lists audit" in report
    assert "## Suspected causes to verify before correction" in report


def test_latei_tex_convergence_audit_flags_tei_p_inside_notes(tex_audit) -> None:
    report = tex_audit.report_path.read_text(encoding="utf-8")

    assert "LaTEI notes containing `\\teiP`" in report
    assert "`\\teiP` definition emits `\\par`: `True`" in report
    assert "\\teiNote" in report
    assert "\\teiP" in report
    assert "Potential divergence: `\\teiP` appears inside `\\teiNote`" in report


def test_latei_tex_convergence_audit_is_structural_not_raw_equality(tex_audit) -> None:
    report = tex_audit.report_path.read_text(encoding="utf-8")

    assert "does not compare `book.tex` and `latei_body.tex` as equal text" in report
    assert "final typographic LaTeX" in report
    assert "reversible semantic source" in report
    assert "binary" not in report.lower()
