from __future__ import annotations

"""Canonical LaTeX/PDF smoke test.

Every check that just needs "does the LaTEI -> PDF chain still compile"
must run against this one sample, never against a full real book (Beautés
vitales, Dissimuler pour mieux régner, Héraldique...): those are compiled
separately and deliberately excluded from the default test battery (see the
`full_book` marker), because recompiling an entire book on every test run is
far too slow to run routinely. This file's fixture is the reference sample
that must always compile; problem cases discovered later should be folded
into it rather than added as new full-book fixtures.
"""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import ReversibleExportResult, run_reversible_export_for_file

FIXTURE_PATH = Path("tests/fixtures/commons-publishing/fichier_test.xml")


@pytest.fixture(scope="module")
def sample_export(tmp_path_factory: pytest.TempPathFactory) -> ReversibleExportResult:
    output_dir = tmp_path_factory.mktemp("commons_publishing_sample")
    return run_reversible_export_for_file(FIXTURE_PATH, output_dir, compile_pdf=True)


def test_commons_publishing_sample_fixture_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_commons_publishing_sample_produces_a_latei_body(sample_export: ReversibleExportResult) -> None:
    # Not asserting zero diagnostics here: this reference sample is a
    # hand-authored documentation example, heavy on incidental whitespace,
    # and already carries pre-existing roundtrip diagnostics unrelated to
    # the LaTeX/PDF pipeline this file exists to smoke-test.
    assert sample_export.latei_body_path.exists()
    assert sample_export.latei_body_path.stat().st_size > 0


def test_commons_publishing_sample_compiles_when_lualatex_is_available(
    sample_export: ReversibleExportResult,
) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not sample_export.latei_pdf_success:
        log = sample_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:160])
        pytest.fail(f"Commons-Publishing sample did not compile.\n{excerpt}")

    assert sample_export.latei_pdf_path.exists()
    assert sample_export.latei_pdf_path.stat().st_size > 0
