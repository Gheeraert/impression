from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from lxml import etree

from purh_site.reversible import compare_tei_elements
from purh_site.reversible_integration import run_reversible_export_for_file

UNICODE_TEXT = "Avant\u00a0: un test\u202f; encore\u2009? oui\u202f! \u00ab\u202fmot\u202f\u00bb."


def test_latei_unicode_spaces_remain_reversible_and_are_typographically_mapped(tmp_path: Path) -> None:
    xml_path = tmp_path / "unicode_spaces.xml"
    xml_path.write_text(
        f"""<p xmlns="http://www.tei-c.org/ns/1.0">{UNICODE_TEXT}</p>""",
        encoding="utf-8",
    )

    result = run_reversible_export_for_file(xml_path, tmp_path / "out")
    body = result.latei_body_path.read_text(encoding="utf-8")
    macros = result.latei_macros_path.read_text(encoding="utf-8")
    source = etree.parse(str(xml_path)).getroot()
    emitted = etree.parse(str(result.roundtrip_xml_path)).getroot()

    assert "\u00a0" in body
    assert "\u202f" in body
    assert "\u2009" in body
    assert r"\usepackage{newunicodechar}" in macros
    assert "\u00a0" in macros
    assert "\u202f" in macros
    assert "\u2009" in macros
    assert "\u2011" in macros
    assert "\u2033" in macros
    assert result.diagnostics_count == 0
    assert compare_tei_elements(source, emitted) == []

    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    assert result.latei_pdf_success is True, result.latei_pdf_message
    log = result.latei_log_path.read_text(encoding="utf-8", errors="replace")
    for codepoint in ("U+00A0", "U+202F", "U+2009", "U+2011", "U+2033"):
        assert codepoint not in log
    assert "Missing character" not in log
