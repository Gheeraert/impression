from __future__ import annotations

"""Experimental PURH driver for controlled reversible LaTEI bodies.

The body file remains the reversible artifact read by
``purh_site.reversible.latex_reader``. The main file generated here is a
compilable wrapper and must not be used as a reversible source.
"""

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

from .latex_renderer import render_purh_preamble_for_latei


LATEI_MACROS_PATH = Path(__file__).resolve().parent / "resources" / "latei_macros.tex"


@dataclass(slots=True)
class LateiPdfResult:
    pdf_path: Path
    success: bool
    message: str


def build_latei_driver(
    body_tex_path: Path,
    main_tex_path: Path,
    *,
    title: str | None = None,
) -> Path:
    """Write a PURH LaTEI main file that inputs the reversible body file."""
    body_tex_path = Path(body_tex_path)
    main_tex_path = Path(main_tex_path)
    main_tex_path.parent.mkdir(parents=True, exist_ok=True)

    body_input = _latex_input_path(body_tex_path, relative_to=main_tex_path.parent)
    macros_input = _latex_input_path(LATEI_MACROS_PATH, relative_to=main_tex_path.parent)
    document_title = _latex_text(title or "LaTEI PURH")

    content = "\n\n".join(
        [
            render_purh_preamble_for_latei(title=title or "LaTEI PURH"),
            rf"\input{{{macros_input}}}",
            r"\begin{document}",
            _title_page(document_title),
            r"\mainmatter",
            rf"\input{{{body_input}}}",
            r"\end{document}",
        ]
    )
    main_tex_path.write_text(content + "\n", encoding="utf-8")
    return main_tex_path


def compile_latei_pdf(
    main_tex_path: Path,
    pdf_path: Path,
    *,
    latex_engine: str = "lualatex",
    timeout_seconds: int = 120,
) -> LateiPdfResult:
    """Compile an experimental LaTEI driver if the configured engine exists."""
    main_tex_path = Path(main_tex_path)
    pdf_path = Path(pdf_path)
    engine_path = shutil.which(latex_engine)
    if engine_path is None:
        return LateiPdfResult(
            pdf_path=pdf_path,
            success=False,
            message=f"LaTEI PDF not produced: LaTeX engine not found: {latex_engine}.",
        )

    command = [
        engine_path,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        f"-jobname={pdf_path.stem}",
        f"-output-directory={pdf_path.parent.as_posix()}",
        main_tex_path.as_posix(),
    ]
    process = subprocess.run(
        command,
        cwd=pdf_path.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    if process.returncode != 0:
        return LateiPdfResult(
            pdf_path=pdf_path,
            success=False,
            message="LaTEI PDF compilation failed; see the LaTeX console output.",
        )
    if not pdf_path.exists():
        return LateiPdfResult(
            pdf_path=pdf_path,
            success=False,
            message="LaTEI PDF compilation finished but the expected PDF was not created.",
        )
    return LateiPdfResult(
        pdf_path=pdf_path,
        success=True,
        message="LaTEI PDF produced successfully.",
    )


def _title_page(title: str) -> str:
    return "\n".join(
        [
            r"\begin{titlepage}",
            r"\thispagestyle{empty}",
            r"\centering",
            r"\vspace*{0.15\textheight}",
            rf"{{\Huge\bfseries {title}\par}}",
            r"\vfill",
            r"{\small Document LaTEI PURH experimental\par}",
            r"\end{titlepage}",
            r"\clearpage",
        ]
    )


def _latex_input_path(path: Path, *, relative_to: Path) -> str:
    resolved = Path(path).resolve()
    base = Path(relative_to).resolve()
    try:
        value = resolved.relative_to(base).as_posix()
    except ValueError:
        value = resolved.as_posix()
    return value.replace("}", r"\}")


def _latex_text(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(char, char) for char in value)
