from __future__ import annotations

"""Experimental PURH driver for controlled reversible LaTEI bodies.

The body file remains the reversible artifact read by
``purh_site.reversible.latex_reader``. The main file generated here is a
compilable wrapper and must not be used as a reversible source.
"""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .latei_metadata import LateiMetadata
from .latei_preamble import PurhPreambleData, render_purh_latex_preamble
from .purh_layout_profiles import DEFAULT_LAYOUT_PROFILE_NAME, get_layout_profile

LATEI_MACROS_PATH = Path(__file__).resolve().parent / "resources" / "latei_macros.tex"


@dataclass(slots=True)
class LateiPdfResult:
    pdf_path: Path
    log_path: Path | None
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
    layout_profile_name: str = DEFAULT_LAYOUT_PROFILE_NAME,
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
            profile=get_layout_profile(layout_profile_name),
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
            _front_matter_sequence(metadata),
            rf"\input{{{body_input}}}",
            r"\cleardoublepage",
            r"\pagestyle{plain}",
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
    layout_profile_name: str = DEFAULT_LAYOUT_PROFILE_NAME,
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
        layout_profile_name=layout_profile_name,
    )
    monofile_path.write_text(content, encoding="utf-8")
    return monofile_path


def _monofile_content(
    *,
    body_latex: str,
    metadata: LateiMetadata,
    graphics_map_content: str | None,
    running_titles_map_content: str | None,
    layout_profile_name: str = DEFAULT_LAYOUT_PROFILE_NAME,
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
        profile=get_layout_profile(layout_profile_name),
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

    title_page = _front_matter_sequence(metadata)

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
        r"\pagestyle{plain}",
        # \tableofcontents compose son propre titre via \chapter*{\contentsname},
        # qui suit par défaut le même \titleformat{\chapter} raggedright que
        # les vrais chapitres (référentiel PURH v0.6 §9.1, "table des matières
        # centrée" — vérification humaine directe, 2026-08-04). Redéfini ici
        # sans restauration ensuite : \tableofcontents est le tout dernier
        # contenu du document, aucun \chapter ne suit.
        r"\titleformat{\chapter}[display]{\PURHTitleFont\bfseries\fontsize{16pt}{19pt}\selectfont\centering}{}{10pt}{\MakeUppercase}",
        r"\tableofcontents",
        "",
        r"\end{document}",
    ])

    return "\n".join(parts) + "\n"


def _monofile_section(label: str) -> str:
    bar = "=" * 60
    return f"% {bar}\n% {label}\n% {bar}"


# Every family of auxiliary file a LuaLaTeX run for this jobname could have
# left behind — including from a *previous, unrelated* document that
# happened to compile under the same jobname/output directory before.
_LATEI_AUX_SUFFIXES = (
    ".aux", ".toc", ".out", ".lof", ".lot", ".bbl", ".bcf", ".fls",
    ".fdb_latexmk", ".synctex.gz", ".run.xml", ".idx", ".ilg", ".ind",
)

_RERUN_HINT = "Rerun to get"


def _purge_stale_latei_aux_files(output_dir: Path, jobname: str) -> None:
    """Delete this jobname's own leftover aux-family files before compiling.

    \\tableofcontents (and hyperref's bookmarks/cross-references) are
    resolved from whatever *.toc/*.aux already sits on disk when a pass
    starts, not from the current document's own content — that file is
    only overwritten at the very end of a pass. A single \\halt-on-error
    LuaLaTeX pass never runs long enough to reach that point if anything
    goes wrong, so a stale file from an earlier, different document under
    the same jobname can survive indefinitely and get silently bundled
    into a PDF that otherwise looks like a successful, fresh build (real
    case: a Beautés vitales table of contents appearing inside a Dissimuler
    pour mieux régner PDF). Removing them here makes every compile start
    from a genuinely clean slate regardless of history.
    """
    for suffix in _LATEI_AUX_SUFFIXES:
        stale = output_dir / f"{jobname}{suffix}"
        if stale.exists():
            stale.unlink()


def compile_latei_pdf(
    main_tex_path: Path,
    pdf_path: Path,
    *,
    log_path: Path | None = None,
    latex_engine: str = "lualatex",
    timeout_seconds: int = 120,
    passes: int = 2,
) -> LateiPdfResult:
    """Compile an experimental LaTEI driver if the configured engine exists.

    Runs at least twice: \\tableofcontents and hyperref's cross-references/
    bookmarks are only correct once a pass can read a .toc/.aux file this
    same compilation itself just wrote — a single pass can only ever show
    whatever was on disk *before* it started (nothing, or a stale file from
    an earlier document; see _purge_stale_latei_aux_files). A further pass
    is added, up to `passes`, if LaTeX's own rerunfilecheck reports it is
    still not converged.
    """
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

    _purge_stale_latei_aux_files(pdf_path.parent, pdf_path.stem)

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
    # luaotfload keeps its own persistent font-name database inside this
    # cache (rebuilt from the system's currently installed fonts only the
    # first time it is used) — reusing an old one from an earlier compile
    # in the same output directory means a font installed *after* that
    # first compile (real case: Chaparral Pro's italic face) stays
    # invisible to fontspec's automatic \setmainfont shape lookup, with no
    # error — \textit silently falls back to upright instead of failing
    # loudly. Deleting it before every compile forces a fresh scan.
    shutil.rmtree(tex_cache_dir, ignore_errors=True)
    tex_cache_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    tex_cache_path = str(tex_cache_dir.resolve())
    env["TEXMFVAR"] = tex_cache_path
    env["TEXMFCACHE"] = tex_cache_path

    passes = max(passes, 1)
    process: subprocess.CompletedProcess[str] | None = None
    pass_number = 0
    while pass_number < passes:
        pass_number += 1
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
            message = f"LaTEI PDF compilation timed out after {timeout_seconds} seconds (pass {pass_number}/{passes})."
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

        if process.returncode != 0:
            _write_latei_log(
                log_path,
                command=command,
                stdout=process.stdout,
                stderr=process.stderr,
                returncode=process.returncode,
                message=f"LaTEI PDF compilation failed (pass {pass_number}/{passes}).",
            )
            return LateiPdfResult(
                pdf_path=pdf_path,
                log_path=log_path,
                success=False,
                message=f"LaTEI PDF compilation failed; see log: {log_path}.",
            )

        if pass_number == passes and passes < 4 and _RERUN_HINT in process.stdout:
            passes += 1

    assert process is not None
    _write_latei_log(
        log_path,
        command=command,
        stdout=process.stdout,
        stderr=process.stderr,
        returncode=process.returncode,
        message=f"LaTEI PDF compilation finished ({passes} pass(es)).",
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


def _front_matter_sequence(metadata: LateiMetadata) -> str:
    """Séquence complète des liminaires (référentiel PURH v0.6 §8.1) : deux
    pages blanches, faux-titre, crédits, page de titre, page blanche —
    bâtie uniquement depuis les métadonnées déjà extraites, jamais depuis
    le corps LaTEI réversible. Initialise la pagination arabe continue
    avant tout contenu, pour que ces six pages soient comptées (sans folio
    visible, \\PURH*Page étant toutes en pagestyle empty) avant que
    l'introduction ne devienne la première page numérotée visible.
    """
    parts = [
        r"\lateiEnsureContinuousArabicPagination",
        r"\PURHBlankPage",
        r"\PURHBlankPage",
        _false_title(metadata),
        _credits_page(metadata),
        _full_title_page(metadata),
        r"\PURHBlankPage",
    ]
    return "\n".join(part for part in parts if part)


def _false_title(metadata: LateiMetadata) -> str:
    return rf"\PURHFalseTitle{{{_latex_text(metadata.title)}}}"


# Nom complet, adresse et URL institutionnels PURH : dictés tels quels par
# l'utilisateur (colophon, 2026-08-04), fixes pour tout livre PURH — pas
# des métadonnées par livre (le TEI/Métopes source contient parfois le sigle
# abrégé "PURH" à la place, cf. _full_title_page ci-dessous), donc jamais lus
# depuis LateiMetadata.
_PURH_FULL_NAME = "Presses universitaires de Rouen et du Havre"
_PURH_ADDRESS_LINE = "2 place Émile Blondel – 76821 Mont-Saint-Aignan Cedex"
_PURH_URL = "http://purh.univ-rouen.fr"


def _colophon_production_lines(metadata: LateiMetadata) -> list[str]:
    """Couverture/mise en pages et suivi éditorial : sans équivalent dans
    la source TEI/Métopes, renseignés par l'éditrice via la boîte de
    dialogue optionnelle du GUI (cover_designer/editorial_contact sur
    LateiMetadata) — omis tant qu'ils ne sont pas fournis, jamais un
    "[Prénom Nom]" littéral imprimé faute de valeur réelle."""
    lines: list[str] = []
    if metadata.cover_designer:
        lines.append(_latex_text(f"Couverture et mise en pages : {metadata.cover_designer}"))
    if metadata.editorial_contact:
        lines.append(_latex_text(f"Suivi éditorial : {metadata.editorial_contact}"))
    return lines


def _colophon_institutional_lines(metadata: LateiMetadata) -> list[str]:
    """Mentions légales et coordonnées : la ligne de copyright et l'adresse/
    URL institutionnelles sont fixes et TOUJOURS présentes (vérification
    humaine directe, 2026-08-04 : « (c) Presses universitaires de Rouen et
    du Havre » doit toujours figurer, juste au-dessus de l'adresse — pas
    seulement quand une année de publication est disponible). Seule l'année,
    elle, reste une métadonnée du livre : ajoutée à la suite du nom de
    l'éditeur quand elle est connue, simplement omise sinon (jamais un
    espace réservé littéral). L'ISBN suit la même règle d'omission."""
    lines: list[str] = []
    year_suffix = f", {metadata.publication_year}" if metadata.publication_year else ""
    lines.append(_latex_text(f"© {_PURH_FULL_NAME}{year_suffix}."))
    lines.append(_latex_text(_PURH_ADDRESS_LINE))
    lines.append(rf"\url{{{_PURH_URL}}}")
    if metadata.preferred_isbn:
        lines.append(_latex_text(f"ISBN : {metadata.preferred_isbn}"))
    return lines


def _credits_page(metadata: LateiMetadata) -> str:
    # Interlignage resserré (vérification humaine directe, 2026-08-04) :
    # 0.4/1\baselineskip entre les lignes donnait un colophon trop aéré.
    blocks = [
        block
        for block in (_colophon_production_lines(metadata), _colophon_institutional_lines(metadata))
        if block
    ]
    if not blocks:
        return ""
    block_bodies = [
        r"\vspace{0.1\baselineskip}".join(rf"{line}\par" for line in block) for block in blocks
    ]
    body = r"\vspace{0.5\baselineskip}".join(block_bodies)
    return rf"\PURHCreditsPage{{{body}}}"


def _title_page_responsibility_lines(metadata: LateiMetadata) -> str:
    """« sous la direction de » sur sa propre ligne puis les noms sur la
    suivante, pour un ouvrage collectif dirigé (exemple concret donné par
    l'utilisateur : *Beautés vitales*, dirigé par deux personnes) — ce
    préfixe ne s'applique qu'aux volumes dirigés ; à défaut de directeurs,
    seuls les noms des auteurs sont affichés, sans lui."""
    if metadata.directors:
        names = _latex_text(" et ".join(metadata.directors))
        return "sous la direction de\\\\" + names
    if metadata.authors:
        return _latex_text(" et ".join(metadata.authors))
    return ""


_ROMAN_CENTURY_NUMERALS = (
    "XXI", "XX", "XIX", "XVIII", "XVII", "XVI", "XV", "XIV", "XIII", "XII", "XI",
    "X", "IX", "VIII", "VII", "VI", "V", "IV", "III", "II", "I",
)
_CENTURY_NUMERAL_RE = re.compile(r"\b(" + "|".join(_ROMAN_CENTURY_NUMERALS) + r")(e|er|re)?\b")


def _small_caps_century_numerals(escaped_text: str) -> str:
    """Petites capitales sur les chiffres romains de siècle (vérification
    humaine directe, 2026-08-04, sur *Dissimuler pour mieux régner* :
    "XVIIe-XIXe siècles" apparaissait en grandes capitales, identiques au
    reste du sous-titre, faute de tout balisage <hi rend="small-caps">
    autour d'eux dans le TEI source — convention typographique française
    appliquée ici mécaniquement, faute de marquage source à lire. Attend un
    texte déjà échappé par _latex_text (le remplacement injecte un
    \\textsc{{...}} littéral, qui serait lui-même cassé si _latex_text
    s'exécutait après). Portée volontairement étroite au seul sous-titre de
    la page de titre — pas une règle appliquée à tout le corps de texte."""
    return _CENTURY_NUMERAL_RE.sub(
        lambda m: rf"\textsc{{{m.group(1)}}}{m.group(2) or ''}", escaped_text
    )


def _full_title_page(metadata: LateiMetadata) -> str:
    lines = [rf"\PurhTitleMain{{{_latex_text(metadata.title)}}}"]
    if metadata.subtitle:
        subtitle = _small_caps_century_numerals(_latex_text(metadata.subtitle))
        lines.append(rf"\PurhSubtitle{{{subtitle}}}")
    responsibility = _title_page_responsibility_lines(metadata)
    if responsibility:
        lines.append(r"\vspace{2\baselineskip}")
        lines.append(rf"\PurhContributors{{{responsibility}}}")
    # Mention finale : toujours le nom complet PURH, fixe (référentiel v0.7,
    # 2026-08-04) — le TEI/Métopes source contient parfois le sigle "PURH"
    # à la place (constaté sur *Dissimuler pour mieux régner*), jamais
    # affiché tel quel ici ; calée en bas de page comme le colophon
    # (\vspace*{\fill}, voir _credits_page pour le même mécanisme et son
    # piège documenté : étoilé, jamais un \vfill nu).
    lines.append(r"\vspace*{\fill}")
    lines.append(rf"\PurhPublisherMention{{{_latex_text(_PURH_FULL_NAME)}}}")
    body = "\n".join(lines)
    return rf"\PURHTitlePage{{{body}}}"


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
