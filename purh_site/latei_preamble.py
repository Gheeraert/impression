from __future__ import annotations

"""Autonomous PURH LaTeX preamble renderer for the LaTEI production chain.

Deliberately independent of LatexRenderer, LatexRenderOptions, semantic_model,
tei_to_model, and pdf_builder. Depends only on the Python standard library.
"""

from dataclasses import dataclass, field

from .purh_layout_profiles import DEFAULT_LAYOUT_PROFILE_NAME, PurhLayoutProfile, get_layout_profile


@dataclass(frozen=True, slots=True)
class PurhPreambleData:
    """Plain-data container for PURH preamble rendering.

    All fields are plain strings, except ``profile`` which selects the
    versioned page-layout profile (format, margins, body/note grid) defined
    in ``purh_layout_profiles``. The caller resolves model-level choices
    (e.g. isbn_pdf vs isbn_print, contributors list) before constructing
    this object. Fields unused by the template (collection, issn) are
    intentionally absent.
    """

    title: str = "LaTEI PURH"
    subtitle: str = ""
    authors: tuple[str, ...] = ()
    publisher: str = "Presses universitaires de Rouen et du Havre"
    year: str = ""
    doi: str = ""
    isbn: str = ""
    profile: PurhLayoutProfile = field(
        default_factory=lambda: get_layout_profile(DEFAULT_LAYOUT_PROFILE_NAME)
    )


def _pt(value: float) -> str:
    """Format a point size without a spurious trailing ``.0`` (11 -> "11pt")."""
    return f"{value:g}pt"


def _mm(value: float) -> str:
    """Format a millimeter dimension without a spurious trailing ``.0``."""
    return f"{value:g}mm"


def render_purh_latex_preamble(data: PurhPreambleData) -> str:
    """Return the full PURH LaTeX preamble string."""
    title = _escape(data.title)
    subtitle = _escape(data.subtitle)
    author = _escape(" ; ".join(a for a in data.authors if a.strip()))
    publisher = _escape(data.publisher or "Presses universitaires de Rouen et du Havre")
    year = _escape(data.year)
    doi = _escape(data.doi)
    isbn = _escape(data.isbn)
    profile = data.profile
    body_class_pt = _pt(profile.body_font_size_pt)
    body_leading = _pt(profile.body_leading_pt)
    note_font_size = _pt(profile.note_font_size_pt)
    note_leading = _pt(profile.note_leading_pt)

    return rf"""
\documentclass[{body_class_pt},twoside,openany]{{book}}

\usepackage[
  paperwidth={_mm(profile.paper_width_mm)},
  paperheight={_mm(profile.paper_height_mm)},
  top={_mm(profile.margin_top_mm)},
  bottom={_mm(profile.margin_bottom_mm)},
  inner={_mm(profile.margin_inner_mm)},
  outer={_mm(profile.margin_outer_mm)},
  headheight=14pt,
  headsep=8mm,
  footskip=10mm
]{{geometry}}
\raggedbottom

\usepackage{{fontspec}}
\usepackage[french]{{babel}}
\usepackage{{csquotes}}
\usepackage{{amsmath}}
\usepackage{{microtype}}
\usepackage{{indentfirst}}
\usepackage{{emptypage}}
\usepackage[normalem]{{ulem}}

\IfFontExistsTF{{Chaparral Pro}}
  {{\setmainfont{{Chaparral Pro}}}}
  {{\setmainfont{{TeX Gyre Pagella}}}}

\IfFontExistsTF{{Josefin Sans}}
  {{\newfontfamily\PURHTitleFont{{Josefin Sans}}}}
  {{\newfontfamily\PURHTitleFont{{TeX Gyre Heros}}}}

% Titraille PURH (référentiel §2.3-§2.5) : partie, article et section
% observés en Josefin Sans Thin, capitales, distinct du \PURHTitleFont
% "normal weight" ci-dessus utilisé ailleurs. Chargée comme famille à part
% (et non via \bfseries sur \PURHTitleFont) car "Thin" n'est pas une série
% NFSS standard que fontspec puisse sélectionner automatiquement — "Josefin
% Sans Thin" existe en revanche comme nom de famille indépendant portant
% elle-même ses propres graisses Thin (romain) et Thin Italic.
\IfFontExistsTF{{Josefin Sans Thin}}
  {{\newfontfamily\PURHTitreFont{{Josefin Sans Thin}}}}
  {{\newfontfamily\PURHTitreFont{{TeX Gyre Heros}}}}

\IfFontExistsTF{{Latin Modern Mono}}
  {{\setmonofont{{Latin Modern Mono}}}}
  {{\setmonofont{{TeX Gyre Cursor}}}}

% Romain, pas italique (référentiel PURH §2.3 : titres courants "Josefin
% Sans Thin/Light, 10 pt, romain" — l'italique systématique précédente était
% un défaut confirmé, pas un choix).
\newcommand{{\PURHHeaderFont}}{{\PURHTitreFont\small}}

% Le corps et son pas de ligne sont fixés explicitement au lieu de dépendre
% de la table de tailles du \documentclass{{book}} choisi : elle donne un
% pas voisin mais pas identique au pas de grille cible (référentiel PURH
% §2.4, §5.3 : corps 11 pt sur une grille de 13,5 pt).
\renewcommand{{\normalsize}}{{\fontsize{{{body_class_pt}}}{{{body_leading}}}\selectfont}}
\normalsize

\newcommand{{\PURHBookTitle}}{{{title}}}
\newcommand{{\PURHBookSubtitle}}{{{subtitle}}}
\newcommand{{\PURHBookAuthor}}{{{author}}}
\newcommand{{\PURHPublisher}}{{{publisher}}}
\newcommand{{\PURHYear}}{{{year}}}
\newcommand{{\PURHDOI}}{{{doi}}}
\newcommand{{\PURHISBN}}{{{isbn}}}

\title{{\PURHBookTitle}}
\author{{\PURHBookAuthor}}
\date{{\PURHYear}}

\setlength{{\parindent}}{{5mm}}
\setlength{{\parskip}}{{0pt}}
\linespread{{1.0}}
\pretolerance=100
\tolerance=500
\hyphenpenalty=500
\exhyphenpenalty=500
\emergencystretch=3em
\clubpenalty=10000
\widowpenalty=10000
\displaywidowpenalty=10000

\usepackage{{enumitem}}

\setlist[itemize,1]{{
  label=\textendash,
  leftmargin=1.5em,
  itemsep=0.2\baselineskip,
  topsep=0.4\baselineskip
}}

\setlist[enumerate,1]{{
  leftmargin=1.8em,
  itemsep=0.2\baselineskip,
  topsep=0.4\baselineskip
}}

\usepackage[nobottomtitles*]{{titlesec}}
\usepackage{{titletoc}}

\setcounter{{secnumdepth}}{{0}}
\setcounter{{tocdepth}}{{2}}

\titleformat{{\chapter}}[display]
  {{\PURHTitleFont\huge\bfseries\raggedright}}
  {{\chaptertitlename~\thechapter}}
  {{10pt}}
  {{}}

% Titre de partie observé : Josefin Sans Thin 16 pt, capitales, centré
% (référentiel PURH §2.5, §5.3). Toujours \part* (pas de numéro affiché) :
% le label reste vide plutôt que d'exposer un numéro de partie non requis.
\titleformat{{\part}}[display]
  {{\PURHTitreFont\fontsize{{16pt}}{{19pt}}\selectfont\centering}}
  {{}}
  {{0pt}}
  {{\MakeUppercase}}

% Titre de section observé : Josefin Sans Thin 12 pt, capitales (référentiel
% §2.5). Alignement et espacement non chiffrés par le référentiel pour ce
% niveau : conservés tels quels (raggedright, séparations existantes).
\titleformat{{\section}}[block]
  {{\PURHTitreFont\fontsize{{12pt}}{{14pt}}\selectfont\raggedright}}
  {{}}
  {{0pt}}
  {{\MakeUppercase}}

\titleformat{{\subsection}}[block]
  {{\PURHTitleFont\large\bfseries\raggedright}}
  {{}}
  {{0pt}}
  {{}}

\titleformat{{\subsubsection}}[block]
  {{\PURHTitleFont\normalsize\bfseries\raggedright}}
  {{}}
  {{0pt}}
  {{}}

\titlespacing*{{\part}}{{0pt}}{{0pt}}{{30pt}}
\titlespacing*{{\chapter}}{{0pt}}{{20pt}}{{18pt}}
\titlespacing*{{\section}}{{0pt}}{{18pt}}{{10pt}}
\titlespacing*{{\subsection}}{{0pt}}{{14pt}}{{8pt}}
\titlespacing*{{\subsubsection}}{{0pt}}{{12pt}}{{6pt}}

\addto\captionsfrench{{
  \renewcommand{{\contentsname}}{{Table des matières}}
}}

\titlecontents{{chapter}}
  [0pt]
  {{\addvspace{{8pt}}\PURHTitleFont\bfseries}}
  {{}}
  {{}}
  {{\hfill\contentspage}}
  [\smallskip]

\titlecontents{{section}}
  [1.5em]
  {{}}
  {{}}
  {{}}
  {{\titlerule*[0.5pc]{{.}}\contentspage}}

\titlecontents{{subsection}}
  [3em]
  {{\small}}
  {{}}
  {{}}
  {{\titlerule*[0.5pc]{{.}}\contentspage}}

\usepackage{{fancyhdr}}

\pagestyle{{fancy}}
\fancyhf{{}}
% Folios à l'extérieur (référentiel PURH §2.3) : LE (verso) et RO (recto).
% Les titres courants intérieurs (RE, LO) et \chaptermark sont pris en
% charge par latei_macros.tex, qui distingue verso (livre/partie) et recto
% (contribution en cours) — les définir ici aussi serait dupliqué et, pire,
% écrasé silencieusement puisque ce fichier est \input après ce préambule.
\fancyhead[LE]{{\PURHHeaderFont\thepage}}
\fancyhead[RO]{{\PURHHeaderFont\thepage}}
\renewcommand{{\headrulewidth}}{{0pt}}
\renewcommand{{\footrulewidth}}{{0pt}}

\fancypagestyle{{plain}}{{%
  \fancyhf{{}}%
  \renewcommand{{\headrulewidth}}{{0pt}}%
  \renewcommand{{\footrulewidth}}{{0pt}}%
}}

\usepackage[hang,flushmargin]{{footmisc}}

\setlength{{\footnotesep}}{{0.6\baselineskip}}
\setlength{{\skip\footins}}{{1.2\baselineskip}}
\renewcommand{{\footnotelayout}}{{\fontsize{{{note_font_size}}}{{{note_leading}}}\selectfont}}

\usepackage{{etoolbox}}

% Citations observées : 9/11 pt, retrait gauche 10 mm (pas de retrait
% droit), ~4 mm avant/après (référentiel PURH §5.3 ; état antérieur :
% 11/14 pt, retraits gauche ET droit ≈1,5em, 8pt avant/après).
\renewenvironment{{quote}}
  {{%
    \par\begingroup
    \fontsize{{9pt}}{{11pt}}\selectfont
    \list{{}}{{\leftmargin=10mm\rightmargin=0pt}}%
    \item\relax
  }}
  {{%
    \endlist
    \endgroup
  }}

\AtBeginEnvironment{{quote}}{{\vspace*{{4mm plus 1pt minus 1pt}}}}
\AtEndEnvironment{{quote}}{{\vspace*{{4mm plus 1pt minus 1pt}}}}

\usepackage{{graphicx}}
\usepackage{{caption}}

\graphicspath{{{{media/}}{{images/}}{{assets/images/}}}}

\captionsetup{{
  font=small,
  labelfont=bf,
  labelsep=period,
  skip=11pt
}}

\addto\captionsfrench{{
  \renewcommand{{\figurename}}{{Figure}}
  \renewcommand{{\tablename}}{{Tableau}}
}}

\usepackage{{array}}
\usepackage{{longtable}}
\usepackage{{tabularx}}
\usepackage{{booktabs}}

\usepackage{{verse}}
\usepackage{{ragged2e}}
\usepackage{{xurl}}
\urlstyle{{same}}

\usepackage[
  unicode=true,
  hidelinks,
  pdfusetitle
]{{hyperref}}

\usepackage{{bookmark}}

\hypersetup{{
  pdftitle={{\PURHBookTitle}},
  pdfauthor={{\PURHBookAuthor}},
  pdfsubject={{\PURHPublisher}},
  pdfcreator={{Impressions}},
  pdfproducer={{LuaLaTeX}}
}}

% -----------------------------------------------------------------
% Macros utilitaires PURH
% -----------------------------------------------------------------
\newcommand{{\PURHSeparator}}{{%
  \par\addvspace{{1.5\baselineskip}}%
  \noindent\rule{{5cm}}{{0.4pt}}%
  \par\addvspace{{1.5\baselineskip}}%
}}

\newcommand{{\PurhSubtitle}}[1]{{%
  \par\vspace{{0.4\baselineskip}}%
  {{\large\itshape #1\par}}%
  \vspace{{0.6\baselineskip}}%
}}

\newcommand{{\PurhContributors}}[1]{{%
  \par\vspace{{0.5\baselineskip}}%
  {{\normalsize\scshape #1\par}}%
  \vspace{{0.6\baselineskip}}%
}}

\newcommand{{\PurhTitleExtra}}[1]{{%
  {{\small #1\par}}%
}}

\newenvironment{{PurhBlockQuote}}
  {{%
    \begin{{quote}}
  }}
  {{%
    \end{{quote}}
  }}

\newenvironment{{PurhBibliography}}
  {{%
    \par
    \setlength{{\parindent}}{{0pt}}%
    \setlength{{\leftskip}}{{0pt}}%
  }}
  {{%
    \par
  }}""".strip()


def _escape(value: str | None) -> str:
    """Escape LaTeX special characters in plain text."""
    if value is None:
        return ""
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
