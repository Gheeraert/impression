from __future__ import annotations

"""Experimental PURH driver for controlled reversible LaTEI bodies.

The body file remains the reversible artifact read by
``purh_site.reversible.latex_reader``. The main file generated here is a
compilable wrapper and must not be used as a reversible source.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .latei_metadata import LateiMetadata
from .latei_preamble import PurhPreambleData, render_purh_latex_preamble

LATEI_MACROS_PATH = Path(__file__).resolve().parent / "resources" / "latei_macros.tex"


@dataclass(slots=True)
class LateiPdfResult:
    pdf_path: Path
    log_path: Path
    success: bool
    message: str


def build_latei_driver(
    body_tex_path: Path,
    main_tex_path: Path,
    *,
    macros_tex_path: Path | None = None,
    graphics_map_tex_path: Path | None = None,
    running_titles_map_tex_path: Path | None = None,
    metadata: LateiMetadata | None = None,
    title: str | None = None,
) -> Path:
    """Write a PURH LaTEI main file that inputs the reversible body file."""
    body_tex_path = Path(body_tex_path)
    main_tex_path = Path(main_tex_path)
    main_tex_path.parent.mkdir(parents=True, exist_ok=True)
    local_macros_path = Path(macros_tex_path) if macros_tex_path is not None else main_tex_path.with_name("latei_macros.tex")
    local_macros_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(LATEI_MACROS_PATH, local_macros_path)

    body_input = _latex_input_path(body_tex_path, relative_to=main_tex_path.parent)
    macros_input = _latex_input_path(local_macros_path, relative_to=main_tex_path.parent)
    graphics_map_input = (
        _latex_input_path(graphics_map_tex_path, relative_to=main_tex_path.parent)
        if graphics_map_tex_path is not None and Path(graphics_map_tex_path).exists()
        else None
    )
    running_titles_map_input = (
        _latex_input_path(running_titles_map_tex_path, relative_to=main_tex_path.parent)
        if running_titles_map_tex_path is not None and Path(running_titles_map_tex_path).exists()
        else None
    )
    metadata = metadata or LateiMetadata(title=title or "LaTEI PURH")

    parts = [
        render_purh_latex_preamble(PurhPreambleData(
            title=metadata.title or title or "LaTEI PURH",
            subtitle=metadata.subtitle or "",
            authors=tuple(metadata.contributors),
            publisher=metadata.publisher or "Presses universitaires de Rouen et du Havre",
            year=metadata.publication_year or "",
            doi=metadata.doi or "",
            isbn=metadata.isbn_pdf or metadata.isbn_print or "",
        )),
        rf"\input{{{macros_input}}}",
    ]
    if graphics_map_input is not None:
        parts.append(rf"\input{{{graphics_map_input}}}")
    if running_titles_map_input is not None:
        parts.append(rf"\input{{{running_titles_map_input}}}")
    parts.extend(
        [
            r"\begin{document}",
            _title_page(metadata),
            rf"\input{{{body_input}}}",
            r"\cleardoublepage",
            r"\tableofcontents",
            r"\end{document}",
        ]
    )
    content = "\n\n".join(parts)
    main_tex_path.write_text(content + "\n", encoding="utf-8")
    return main_tex_path


_MONOFILE_FILE_HEADER = """\
% !TeX program = lualatex
% Fichier LaTEI généré depuis XML-TEI Métopes / Commons-Publishing.
% Zone technique (préambule, macros, mappings) : régénérable depuis le XML source.
% NE PAS MODIFIER la zone technique — elle sera écrasée à la prochaine génération.
% Zone éditoriale réversible : l'environnement lateiDocument dans ce fichier.
% Corriger uniquement dans la zone réversible.\
"""


def build_latei_monofile(
    body_latex: str,
    monofile_path: Path,
    *,
    graphics_map_content: str | None = None,
    running_titles_map_content: str | None = None,
    metadata: LateiMetadata | None = None,
    title: str | None = None,
) -> Path:
    """Write a single compilable LaTEI file with everything inline (no \\input{})."""
    monofile_path = Path(monofile_path)
    monofile_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = metadata or LateiMetadata(title=title or "LaTEI PURH")
    content = _monofile_content(
        body_latex=body_latex,
        metadata=metadata,
        graphics_map_content=graphics_map_content,
        running_titles_map_content=running_titles_map_content,
    )
    monofile_path.write_text(content, encoding="utf-8")
    return monofile_path


def _monofile_content(
    *,
    body_latex: str,
    metadata: LateiMetadata,
    graphics_map_content: str | None,
    running_titles_map_content: str | None,
) -> str:
    macros_content = LATEI_MACROS_PATH.read_text(encoding="utf-8")
    preamble = render_purh_latex_preamble(PurhPreambleData(
        title=metadata.title or "LaTEI PURH",
        subtitle=metadata.subtitle or "",
        authors=tuple(metadata.contributors),
        publisher=metadata.publisher or "Presses universitaires de Rouen et du Havre",
        year=metadata.publication_year or "",
        doi=metadata.doi or "",
        isbn=metadata.isbn_pdf or metadata.isbn_print or "",
    ))

    parts: list[str] = [
        _MONOFILE_FILE_HEADER,
        "",
        preamble,
        "",
        _monofile_section("Macros LaTEI — régénérables, ne pas modifier"),
        "",
        macros_content.rstrip(),
    ]

    if graphics_map_content:
        parts.extend([
            "",
            _monofile_section("Mappings graphiques — régénérables, ne pas modifier"),
            "",
            graphics_map_content.rstrip(),
        ])

    if running_titles_map_content:
        parts.extend([
            "",
            _monofile_section("Mappings titres courants — régénérables, ne pas modifier"),
            "",
            running_titles_map_content.rstrip(),
        ])

    title_page = _title_page(metadata)

    parts.extend([
        "",
        r"\begin{document}",
        "",
        title_page,
        "",
        _monofile_section("Zone éditoriale réversible — corrections autorisées ici"),
        "",
        r"\begin{lateiDocument}",
        body_latex.rstrip(),
        r"\end{lateiDocument}",
        "",
        r"\cleardoublepage",
        r"\tableofcontents",
        "",
        r"\end{document}",
    ])

    return "\n".join(parts) + "\n"


def _monofile_section(label: str) -> str:
    bar = "=" * 60
    return f"% {bar}\n% {label}\n% {bar}"


def compile_latei_pdf(
    main_tex_path: Path,
    pdf_path: Path,
    *,
    log_path: Path | None = None,
    latex_engine: str = "lualatex",
    timeout_seconds: int = 120,
) -> LateiPdfResult:
    """Compile an experimental LaTEI driver if the configured engine exists."""
    main_tex_path = Path(main_tex_path)
    pdf_path = Path(pdf_path)
    log_path = Path(log_path) if log_path is not None else pdf_path.with_name(f"{pdf_path.stem}_build.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    engine_path = shutil.which(latex_engine)
    if engine_path is None:
        message = f"LaTEI PDF not produced: LaTeX engine not found: {latex_engine}."
        _write_latei_log(
            log_path,
            command=[latex_engine],
            stdout="",
            stderr="",
            returncode=None,
            message=message,
        )
        return LateiPdfResult(
            pdf_path=pdf_path,
            log_path=log_path,
            success=False,
            message=message,
        )

    command = [
        engine_path,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        f"-jobname={pdf_path.stem}",
        f"-output-directory={pdf_path.parent.resolve().as_posix()}",
        main_tex_path.resolve().as_posix(),
    ]
    tex_cache_dir = pdf_path.parent / "latei_tex_cache"
    tex_cache_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    tex_cache_path = str(tex_cache_dir.resolve())
    env["TEXMFVAR"] = tex_cache_path
    env["TEXMFCACHE"] = tex_cache_path
    try:
        process = subprocess.run(
            command,
            cwd=pdf_path.parent,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        message = f"LaTEI PDF compilation timed out after {timeout_seconds} seconds."
        _write_latei_log(
            log_path,
            command=command,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            returncode=None,
            message=message,
        )
        return LateiPdfResult(
            pdf_path=pdf_path,
            log_path=log_path,
            success=False,
            message=message,
        )

    _write_latei_log(
        log_path,
        command=command,
        stdout=process.stdout,
        stderr=process.stderr,
        returncode=process.returncode,
        message="LaTEI PDF compilation finished.",
    )
    if process.returncode != 0:
        return LateiPdfResult(
            pdf_path=pdf_path,
            log_path=log_path,
            success=False,
            message=f"LaTEI PDF compilation failed; see log: {log_path}.",
        )
    if not pdf_path.exists():
        return LateiPdfResult(
            pdf_path=pdf_path,
            log_path=log_path,
            success=False,
            message=f"LaTEI PDF compilation finished but the expected PDF was not created; see log: {log_path}.",
        )
    return LateiPdfResult(
        pdf_path=pdf_path,
        log_path=log_path,
        success=True,
        message="LaTEI PDF produced successfully.",
    )


def _title_page(metadata: LateiMetadata) -> str:
    lines = [
        r"\begin{titlepage}",
        r"\thispagestyle{empty}",
        r"\centering",
        r"\vspace*{0.15\textheight}",
        r"{\Huge\bfseries \PURHBookTitle\par}",
    ]
    if metadata.subtitle:
        lines.append(r"\PurhSubtitle{\PURHBookSubtitle}")
    if metadata.contributor_line:
        lines.append(r"\PurhContributors{\PURHBookAuthor}")
    lines.append(r"\vfill")
    if metadata.publisher:
        lines.append(rf"\PurhTitleExtra{{{_latex_text(metadata.publisher)}}}")
    lines.extend(
        [
            r"\end{titlepage}",
            r"\clearpage",
        ]
    )
    return "\n".join(lines)


def _latex_input_path(path: Path, *, relative_to: Path) -> str:
    resolved = Path(path).resolve()
    base = Path(relative_to).resolve()
    try:
        value = resolved.relative_to(base).as_posix()
    except ValueError:
        value = resolved.as_posix()
    safe_value = value.replace('"', "").replace("}", r"\}")
    return f'"{safe_value}"'


def _write_latei_log(
    path: Path,
    *,
    command: list[str],
    stdout: str | bytes | None,
    stderr: str | bytes | None,
    returncode: int | None,
    message: str,
) -> None:
    def as_text(value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    lines = [
        "LaTEI build log",
        "=" * 15,
        "",
        f"Message: {message}",
        f"Return code: {returncode if returncode is not None else 'not available'}",
        "Command:",
        " ".join(command),
        "",
        "STDOUT:",
        as_text(stdout),
        "",
        "STDERR:",
        as_text(stderr),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


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
