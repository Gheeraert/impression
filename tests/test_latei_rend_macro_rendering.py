r"""Regression tests for \teiHi rend={...} macro rendering.

F4 bug: xparse O{} captures [rend={italic}] preserving {italic} as a TeX group.
xstring \IfSubStr does not search inside groups, so the test was always FALSE.
Fix: \IfSubStr{\detokenize{#1}}{\detokenize{...}} on both operands.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


MACROS_PATH = Path("purh_site/resources/latei_macros.tex")

# ── Macros expected to use \detokenize on both sides ────────────────────────

REND_MACROS = [
    r"\lateiHiItalic",
    r"\lateiIfRendSmallCaps",
    r"\lateiIfRendBold",
    r"\lateiIfRendSup",
    r"\lateiIfRendSub",
]


# ── Source-level tests (fast, no compilation) ────────────────────────────────


def test_latei_macros_file_exists() -> None:
    assert MACROS_PATH.exists(), f"{MACROS_PATH} not found"


def test_rend_macros_use_detokenize_on_both_sides() -> None:
    r"""Every \lateiIfRend* and \lateiHiItalic must use \detokenize on both
    the subject (#1) and the search string to handle rend={...} TeX groups."""
    source = MACROS_PATH.read_text(encoding="utf-8")

    # Locate each macro definition block and verify the pattern inside it.
    for macro in REND_MACROS:
        # Find the block: \NewDocumentCommand{\macroName}{...}{...}
        idx = source.find(macro)
        assert idx >= 0, f"{macro} not found in {MACROS_PATH}"

        # Grab enough text after the name to cover one command definition.
        block = source[idx : idx + 400]

        # Must contain \detokenize{#1} (subject) AND \detokenize{ (search term).
        assert r"\detokenize{#1}" in block, (
            f"{macro}: subject not detokenized — \\IfSubStr will fail for rend={{...}} groups.\n"
            f"Block:\n{block}"
        )
        assert block.count(r"\detokenize{") >= 2, (
            f"{macro}: search string not also detokenized — catcode mismatch.\n"
            f"Block:\n{block}"
        )


def test_no_bare_ifsubstr_on_hash1_for_rend_macros() -> None:
    r"""Ensure no residual bare \IfSubStr{#1}{<keyword>} pattern remains in
    the rend-dispatch macros (the pre-fix form that silently failed)."""
    source = MACROS_PATH.read_text(encoding="utf-8")

    # Pattern: \IfSubStr{#1}{something} NOT preceded by \detokenize
    bare = re.compile(r"\\IfSubStr\s*\{#1\}\s*\{(?!\\detokenize)")

    # Find all bare occurrences and check none are inside our target macros.
    for m in bare.finditer(source):
        context_start = max(0, m.start() - 300)
        context = source[context_start : m.start()]
        for macro in REND_MACROS:
            if macro in context:
                pytest.fail(
                    f"Bare \\IfSubStr{{#1}}{{...}} found in context of {macro} "
                    f"at offset {m.start()} — rend={{...}} groups will not match.\n"
                    f"Context: ...{context[-100:]}..."
                )


# ── Compilation tests (conditional on lualatex + pdffonts) ──────────────────


def _lualatex() -> str | None:
    return shutil.which("lualatex")


def _pdffonts() -> str | None:
    return shutil.which("pdffonts")


def _build_test_tex(macros_path: Path) -> str:
    """Return a minimal LuaLaTeX document that exercises teiHi rend variants."""
    abs_macros = macros_path.resolve().as_posix()
    return textwrap.dedent(rf"""
        \documentclass[12pt,twoside,openany]{{book}}
        \usepackage[paperwidth=155mm,paperheight=230mm,
          top=20mm,bottom=20mm,inner=20mm,outer=20mm,
          headheight=14pt,headsep=6mm]{{geometry}}
        \usepackage{{fontspec}}
        \usepackage{{fancyhdr}}
        \usepackage[hang,flushmargin]{{footmisc}}
        \usepackage{{csquotes}}
        \usepackage{{hyperref}}
        \usepackage{{graphicx}}

        \IfFontExistsTF{{Chaparral Pro}}
          {{\setmainfont{{Chaparral Pro}}}}
          {{\setmainfont{{TeX Gyre Pagella}}}}

        % Stubs required by latei_macros.tex before \input
        \newcommand{{\PURHHeaderFont}}{{}}
        \newcommand{{\PURHBookTitle}}{{Test}}
        \pagestyle{{fancy}}
        \fancyhf{{}}

        \newenvironment{{PurhBlockQuote}}{{\begin{{quote}}}}{{\end{{quote}}}}
        \newenvironment{{PurhBibliography}}{{\par\setlength{{\parindent}}{{0pt}}}}{{\par}}

        \input{{"{abs_macros}"}}

        \begin{{document}}
        \mainmatter

        Romain avant.

        \textit{{ITALIQUE DIRECT}}

        \teiHi[rend={{italic}}]{{ITALIQUE VIA TEIHI}}

        \teiHi[rend={{small-caps}}]{{PETITES CAPITALES VIA TEIHI}}

        n\teiHi[rend={{sup}}]{{o}}\teiHi[rend={{sub}}]{{x}}

        Texte avec note%
        \teiNote[n={{1}},place={{foot}}]{{\teiP{{Note : \teiHi[rend={{italic}}]{{ITALIQUE EN NOTE}}.}}}}%
        . Suite.

        \end{{document}}
    """).strip()


@pytest.fixture(scope="module")
def compiled_pdf(tmp_path_factory: pytest.TempPathFactory):
    """Compile the rend micro-test with lualatex; skip if unavailable."""
    if _lualatex() is None:
        pytest.skip("lualatex is unavailable.")

    work = tmp_path_factory.mktemp("rend_rendering")
    tex_path = work / "rend_test.tex"
    tex_path.write_text(_build_test_tex(MACROS_PATH), encoding="utf-8")

    result = subprocess.run(
        [_lualatex(), "--interaction=nonstopmode", tex_path.name],
        cwd=work,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    pdf_path = work / "rend_test.pdf"
    log_path = work / "rend_test.log"

    return {
        "pdf": pdf_path,
        "log": log_path,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def test_lualatex_compilation_succeeds(compiled_pdf) -> None:
    log_text = compiled_pdf["log"].read_text(encoding="utf-8", errors="replace") if compiled_pdf["log"].exists() else ""
    assert compiled_pdf["pdf"].exists(), (
        f"PDF not produced (rc={compiled_pdf['returncode']}).\n"
        f"Log tail:\n{log_text[-2000:]}"
    )
    assert compiled_pdf["pdf"].stat().st_size > 0


def test_lualatex_log_has_no_fatal_errors(compiled_pdf) -> None:
    if not compiled_pdf["log"].exists():
        pytest.skip("Log file not produced.")
    log = compiled_pdf["log"].read_text(encoding="utf-8", errors="replace")
    fatal = [line for line in log.splitlines() if line.startswith("!")]
    assert not fatal, f"LaTeX fatal errors in log:\n" + "\n".join(fatal[:20])


def test_pdf_contains_italic_font(compiled_pdf) -> None:
    """pdffonts must report an italic/oblique font — confirms \teiHi[rend={italic}]
    actually triggered \textit rather than falling through to roman."""
    if _pdffonts() is None:
        pytest.skip("pdffonts is unavailable.")
    if not compiled_pdf["pdf"].exists():
        pytest.skip("PDF was not produced.")

    result = subprocess.run(
        [_pdffonts(), str(compiled_pdf["pdf"])],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    fonts_output = result.stdout
    italic_present = any(
        token in fonts_output
        for token in ("Italic", "Oblique", "-It", "-Ital", "italic", "oblique")
    )
    assert italic_present, (
        "No italic font found in PDF — \\teiHi[rend={italic}] likely rendered roman.\n"
        f"pdffonts output:\n{fonts_output}"
    )
