from __future__ import annotations

from pathlib import Path

import pytest

from purh_site.reversible.latex_reader import (
    LAYOUT_PARAM_STANDALONE_MACROS,
    LAYOUT_PARAM_WRAPPER_MACROS,
    LAYOUT_STANDALONE_MACROS,
    LAYOUT_WRAPPER_MACROS,
)

_GUIDE = Path("docs/guide_latei_corrections_editoriales.tex")

_ALL_PUBLIC_MACROS = (
    LAYOUT_WRAPPER_MACROS
    | LAYOUT_PARAM_WRAPPER_MACROS
    | LAYOUT_STANDALONE_MACROS
    | LAYOUT_PARAM_STANDALONE_MACROS
)


def test_guide_exists() -> None:
    assert _GUIDE.exists(), f"{_GUIDE} introuvable"


@pytest.mark.parametrize("macro", sorted(_ALL_PUBLIC_MACROS))
def test_guide_mentions_every_latei_macro(macro: str) -> None:
    source = _GUIDE.read_text(encoding="utf-8")
    assert macro in source, f"\\{macro} absent du guide LaTeX public"


def test_guide_mentions_three_valid_sizes() -> None:
    source = _GUIDE.read_text(encoding="utf-8")
    assert "small" in source
    assert "medium" in source
    assert "large" in source


def test_guide_warns_against_raw_latex() -> None:
    source = _GUIDE.read_text(encoding="utf-8")
    assert "noindent" in source
    assert "vspace" in source
    assert "newpage" in source


def test_guide_explains_xml_transparency() -> None:
    source = _GUIDE.read_text(encoding="utf-8")
    assert "XML" in source
    assert "restaur" in source
