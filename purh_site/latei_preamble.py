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
    show_contribution_author_macro = (
        r"\lateiShowContributionAuthortrue" if profile.show_contribution_author else r"\lateiShowContributionAuthorfalse"
    )

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
% Référentiel PURH v0.6 §6.2 : « le bandeau généré est situé environ 3,1 mm
% plus bas que dans le PDF imprimeur » — écart de rendu, pas une remise en
% cause de la marge du haut mesurée sur le maître InDesign (profile.
% margin_top_mm, qui reste la source de vérité pour la position du corps de
% texte). \topmargin remonte le bandeau de titre courant de 3,1 mm ;
% \headsep compense d'autant pour que le corps de texte, lui, démarre
% exactement à la même position qu'avant ce correctif.
\addtolength{{\topmargin}}{{-3.1mm}}
\addtolength{{\headsep}}{{3.1mm}}
\raggedbottom

\usepackage{{fontspec}}
\usepackage[french]{{babel}}
\usepackage{{csquotes}}
\usepackage{{amsmath}}
\usepackage{{microtype}}
\usepackage{{indentfirst}}
\usepackage{{emptypage}}
\usepackage[normalem]{{ulem}}
% [table] : nécessaire pour \rowcolor sur les lignes d'entête de tableau
% (référentiel §11.3, "fond foncé noir 30 %") — charge colortbl en plus des
% commandes \color habituelles (compatible avec l'usage \color[gray]{{}}
% déjà en place pour le titre courant).
\usepackage[table]{{xcolor}}

% Référentiel PURH v0.6 §12.1 : « le texte courant du PDF imprimeur
% correspond à un noir process à 90 % [K]. La sortie actuelle utilise du
% noir plein. » CMYK explicite (0,0,0,0.9), pas une valeur de gris RVB :
% "K" désigne le noir process de la quadrichromie, un concept distinct du
% gris \color[gray]{{}} utilisé ailleurs (titre courant) qui n'a pas de sens
% en CMJN. Appliqué globalement dès le début du document.
\definecolor{{PURHBodyBlack}}{{cmyk}}{{0,0,0,0.9}}
\AtBeginDocument{{\color{{PURHBodyBlack}}}}

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
%
% Cinq vérifications humaines successives (2026-08-04/06) ont porté sur ce
% même réglage : la première jugeait le gris trop clair (corrigé en passant
% de \PURHTitreFont, famille Thin, à \PURHTitleFont, famille standard, sans
% \bfseries) ; la seconde a trouvé ce résultat trop noir et visuellement
% gras — le PDF imprimeur, lui, n'a « pas de graisse » — d'où un retour à la
% famille Thin avec un gris explicite (\color[gray]{{0.25}}, approximatif) ;
% la troisième a jugé ce gris encore trop clair, d'où un premier passage au
% même système que le fond d'entête de tableau et le texte courant
% (§11.3/§12.1) — une teinte CMJN noir X % plutôt qu'un gris RVB — à 50 %
% noir ; la quatrième a de nouveau jugé ce résultat trop clair au regard du
% PDF imprimeur, où le titre courant est « presque noir » : remonté à 85 %
% noir. La cinquième vérification, sur une page réelle complète d'un livre
% du corpus (pas seulement les liminaires), a de nouveau jugé le résultat
% trop clair à 85 % — cette fois poussé au maximum possible, 100 % noir
% (K plein), plutôt que de continuer à tâtonner par incréments : la fonte
% Thin elle-même, à traits fins, absorbe visuellement une partie de la
% densité d'encre même à pleine saturation (un trait fin
% couvre moins de surface qu'un trait gras à teinte égale) — sans revenir
% sur la graisse Thin elle-même (toujours demandée telle quelle), 100 % est
% la valeur la plus sombre atteignable par ce seul levier.
\newcommand{{\PURHHeaderFont}}{{\PURHTitreFont\small\color[cmyk]{{0,0,0,1}}}}

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
% Référentiel PURH v0.6 §9 ("Table des matières") : la cible exclut les
% sections internes (intertitres) de la TDM — seuls le niveau des parties
% (\part, niveau -1) et celui des ouvertures de contribution/front matter
% (\addcontentsline{{toc}}{{chapter}}, niveau 0) doivent y figurer. tocdepth=2
% incluait à tort les <div type="section1">/<div type="section2"> (niveaux
% \section=1, \subsection=2), gonflant la TDM à trois pages au lieu de deux.
\setcounter{{tocdepth}}{{0}}

% Josefin Sans Bold, 16 pt, capitales — le référentiel indiquait Josefin
% Sans Thin (§2.5, §5.3, §4.3), contredit par vérification humaine directe
% du PDF généré face au PDF imprimeur : les titres de partie y sont noirs et
% gras, alors que le Thin rendait un texte maigre et grisâtre, peu lisible.
% Observation directe suivie ici, comme pour le séparateur de note de bas de
% page défini plus bas dans ce même préambule. \PURHTitleFont (pas
% \PURHTitreFont, qui ne charge que la graisse Thin et ne peut donc pas
% produire de \bfseries réel) charge la famille Josefin Sans complète, dont
% fontspec sélectionne automatiquement la graisse Bold via NFSS.
\titleformat{{\chapter}}[display]
  {{\PURHTitleFont\bfseries\fontsize{{16pt}}{{19pt}}\selectfont\raggedright}}
  {{\chaptertitlename~\thechapter}}
  {{10pt}}
  {{\MakeUppercase}}

% Titre de partie : même correctif Bold que \chapter ci-dessus. Toujours
% \part* (pas de numéro affiché) : le label reste vide plutôt que d'exposer
% un numéro de partie non requis.
\titleformat{{\part}}[display]
  {{\PURHTitleFont\bfseries\fontsize{{16pt}}{{19pt}}\selectfont\centering}}
  {{}}
  {{0pt}}
  {{\MakeUppercase}}

% Titre de section (intertitre), 12 pt, capitales. Le référentiel §2.5
% indiquait Josefin Sans Thin ; corrigé en Bold (même correctif que la
% titraille partie/chapitre/contribution ci-dessus) après vérification
% humaine directe du PDF généré face au PDF imprimeur : les intertitres y
% apparaissent noirs et gras, pas maigres (chantier de parité v0.6,
% 2026-08-04). Alignement et espacement non chiffrés par le référentiel pour
% ce niveau : conservés tels quels (raggedright, séparations existantes).
\titleformat{{\section}}[block]
  {{\PURHTitleFont\bfseries\fontsize{{12pt}}{{14pt}}\selectfont\raggedright}}
  {{}}
  {{0pt}}
  {{\MakeUppercase}}

% Sous-section (référentiel v0.6 §4.3 : seul le niveau "section" — c'est-à-
% dire section1 — est chiffré ; aucune valeur propre à section2/section3
% n'est fournie). Un correctif antérieur avait délibérément retiré le gras
% à ce niveau (confirmé alors sur le livre réel — <div type="section2"> y
% porte de vrais sous-titres phrastiques, jamais des libellés courts) ; la
% vérification humaine directe du 2026-08-04 demande au contraire le même
% traitement noir et gras que les autres intertitres, suivie ici. Capitales
% non demandées à ce niveau, contrairement à \section : inchangé. Tailles
% conservées telles quelles (\large/\normalsize) faute de mesure référentiel.
\titleformat{{\subsection}}[block]
  {{\PURHTitleFont\bfseries\large\raggedright}}
  {{}}
  {{0pt}}
  {{}}

\titleformat{{\subsubsection}}[block]
  {{\PURHTitleFont\bfseries\normalsize\raggedright}}
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

% Entrées de contribution/front matter (référentiel PURH v0.6 §9.1,
% vérification humaine directe du 2026-08-04) : « titre de la communication
% sans graisse, bas de casse, Chaparral, calé à gauche, série de points
% puis numéro de ligne ». Chaparral Pro reste la fonte ambiante (aucune
% famille à sélectionner) : \PURHTitleFont\bfseries retiré, \hfill remplacé
% par le même filet pointillé que \section ci-dessous. \addvspace{{8pt}}
% inconditionnel retiré : « pas de saut de ligne entre les références sauf
% changement de section » — l'espacement avant une nouvelle partie vient
% désormais du bloc \part ci-dessous, pas d'ici.
%
% Filet pointillé + numéro de page : laissés dans ce 4e argument dédié (pas
% déplacés dans le texte de l'entrée transmis à \addcontentsline). Une
% première tentative avait déplacé \titlerule*/\contentspage dans ce texte
% pour les faire tomber sur la ligne du titre plutôt que sur celle de
% l'auteur (vérification humaine directe du 2026-08-04 : « les points de
% suite doivent être au niveau du titre, pas de l'auteur ») — abandonnée :
% le paquet bookmark, qui construit automatiquement les signets PDF depuis
% CE MÊME texte d'entrée, ne tolère pas \contentspage/\\ dans cet argument
% ("Token not allowed in a PDF string", puis désynchronisation de
% titlesec — bug réel constaté par compilation). Solution retenue : le nom
% d'auteur n'est plus concaténé DANS le texte de l'entrée de chapitre du
% tout — voir \latei_finish_contribution_toc_entry: (latei_macros.tex), qui
% l'écrit désormais comme une ligne de TDM séparée, via \addtocontents
% (jamais capturée par le mécanisme de signets de bookmark, qui n'observe
% que \addcontentsline/\contentsline).
\titlecontents{{chapter}}
  [0pt]
  {{}}
  {{}}
  {{}}
  {{\titlerule*[0.5pc]{{.}}\contentspage}}

% Entrées de partie (le référentiel dit « titres de section », mais
% désigne bien ici le niveau \part de ce document — les véritables
% intertitres/sections sont exclus de la TDM depuis §9/tocdepth=0) : Josefin
% Sans Bold, capitales (vérification humaine directe du 2026-08-04 : à la
% différence du nom d'auteur sous chaque entrée de contribution, qui doit
% rester bas de casse — voir \lateiTocAuthorLine dans latei_macros.tex —
% les titres de ce niveau doivent au contraire être en petites capitales).
% \scshape ici n'a AUCUN effet sur \PURHTitleFont (Josefin Sans, qui n'a pas
% de véritables petites capitales OpenType — confirmé par compilation
% isolée, "Font shape .../b/sc undefined", substitution silencieuse) : la
% mise en majuscules se fait donc en amont, à la source du texte, via
% \MakeUppercase{{#1}} dans \lateiRenderHead (latei_macros.tex) — seul le
% corps réduit ici (12 pt contre 16 pt sur la page de la partie elle-même)
% distingue ce niveau de véritables grandes capitales.
\titlecontents{{part}}
  [0pt]
  {{\addvspace{{1\baselineskip}}\PURHTitleFont\bfseries\fontsize{{12pt}}{{14pt}}\selectfont\centering}}
  {{}}
  {{}}
  {{}}
  [\addvspace{{1\baselineskip}}]

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

\usepackage[flushmargin]{{footmisc}}

\setlength{{\footnotesep}}{{0.6\baselineskip}}
% Espace avant les notes (référentiel §5.1 : 3 mm) : \skip\footins régit
% l'espace entre la fin du corps de texte et le début de la zone de notes
% (filet inclus) — 1,2\baselineskip (~5,7 mm à 11/13,5 pt) en donnait trop.
\setlength{{\skip\footins}}{{3mm}}
% Filet de notes (référentiel §5.1 : 0,25 pt de large sur 72 pt = 25,4 mm de
% long). \footnoterule par défaut de book.cls fait 0,4 pt sur
% 0,4\columnwidth (~42 mm sur l'empagement de ce profil) — les deux
% constats "environ 0,40 pt" / "environ 42 mm" du §5.2 correspondent très
% exactement à cette valeur par défaut, jamais personnalisée jusqu'ici.
\renewcommand{{\footnoterule}}{{%
  \kern-3pt
  \hrule width 72pt height 0.25pt
  \kern 2.6pt
}}
% \footnotelayout (footmisc) n'a plus d'effet : la redéfinition plus bas du
% texte de note pour le retrait négatif de première ligne applique
% directement \fontsize{{{note_font_size}}}{{{note_leading}}} et court-circuite
% le mécanisme normal de footmisc qui l'invoque.

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

% Référentiel PURH v0.6 §11.3 : titre de tableau 9/11 pt, centré, 10 mm
% avant, 3,5 mm après — réglage propre aux tableaux (\captionsetup[table]),
% distinct du réglage générique ci-dessus qui reste seul à s'appliquer aux
% figures (aucune cible équivalente donnée pour elles dans le référentiel).
\DeclareCaptionFont{{PURHTableCaptionFont}}{{\fontsize{{9pt}}{{11pt}}\selectfont}}
\captionsetup[table]{{
  font=PURHTableCaptionFont,
  labelfont=bf,
  labelsep=period,
  justification=centering,
  aboveskip=10mm,
  belowskip=3.5mm
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

% Numéro calé à gauche avec retrait négatif de première ligne (observé
% directement sur le PDF imprimeur — le référentiel indiquait un point
% après le numéro, contredit par cette observation directe, suivie ici) :
% \leftskip aligne toutes les lignes de la note sur la même marge gauche ;
% \parindent négatif ramène uniquement la première ligne (celle du numéro)
% en deçà de cette marge, jusqu'au bord. \@thefnmark seul, sans point.
% Surtout PAS de \noindent ici : \noindent annule précisément l'effet du
% \parindent négatif qu'il est censé appliquer à la première ligne — bug
% réel constaté après vérification humaine du PDF généré (la première ligne
% restait alignée sur \leftskip comme les suivantes, aucun retrait négatif
% visible) ; laisser LaTeX indenter naturellement la première ligne de
% \parindent (donc la ramener à 0, à la marge) est ce qui produit le retrait
% négatif recherché.
% \AtBeginDocument, pas une simple redéfinition de préambule : hyperref/
% bookmark redéfinissent eux-mêmes \@makefntext pour y ajouter leurs
% ancres, mais le font via leur propre \AtBeginDocument — un
% \renewcommand direct ici, même placé après leur \usepackage, se faisait
% donc encore écraser au début du document (bug réel rencontré et vérifié :
% le correctif n'avait aucun effet tant qu'il n'était pas, lui aussi,
% différé). Étant chargés plus haut, leur crochet s'exécute avant celui-ci.
% \fontsize{{{note_font_size}}}{{{note_leading}}} explicite ici, pas laissé au
% \footnotelayout de footmisc (référentiel §5.1 : Chaparral Pro 8,5/10,2 pt) :
% cette redéfinition complète de \@makefntext remplace celle de footmisc et
% n'appelle donc plus \footnotelayout — la taille du corps du texte de note
% retombait silencieusement sur celle ambiante (~9/11 pt observés, cf. §5.2)
% tant que ce défaut n'était pas identifié.
\makeatletter
\AtBeginDocument{{%
  \renewcommand{{\@makefntext}}[1]{{%
    \fontsize{{{note_font_size}}}{{{note_leading}}}\selectfont
    \setlength{{\leftskip}}{{1.2em}}%
    \setlength{{\parindent}}{{-1.2em}}%
    \@thefnmark\enskip#1%
  }}%
}}
\makeatother

% -----------------------------------------------------------------
% Macros utilitaires PURH
% -----------------------------------------------------------------
% Visibilité auteur/affiliation sur l'ouverture de contribution (référentiel
% PURH v0.6 §7.2/§17 P1 item 3) : piloté par le profil de mise en page, pas
% par une valeur fixe — « le profil doit distinguer conservation des
% métadonnées et visibilité sur la page ». Doit être déclaré ici, avant que
% les macros LaTEI ne soient chargées : elles lisent ce drapeau dans
% \lateiContributionAuthor / \lateiContributionAffiliation mais ne le
% déclarent pas elles-mêmes.
\newif\iflateiShowContributionAuthor
{show_contribution_author_macro}

\newcommand{{\PURHSeparator}}{{%
  \par\addvspace{{1.5\baselineskip}}%
  \noindent\rule{{5cm}}{{0.4pt}}%
  \par\addvspace{{1.5\baselineskip}}%
}}

% Titre principal de la page de titre (référentiel PURH v0.6 §8.1,
% vérification humaine directe du 2026-08-04) : même hauteur de départ que
% le faux-titre (\PURHTitlePage partage désormais \vspace*{{0.25\textheight}}
% avec \PURHFalseTitle), mais corps plus grand — Josefin Sans Bold
% capitales, comme le faux-titre, juste agrandi. Aucune mesure
% millimétrique donnée par l'utilisateur pour ce corps précis : 22/26 pt
% choisi pour rester nettement plus grand que les 12/14 pt du faux-titre.
\newcommand{{\PurhTitleMain}}[1]{{%
  {{\PURHTitleFont\bfseries\fontsize{{22pt}}{{26pt}}\selectfont\centering\MakeUppercase{{#1}}\par}}
}}

% Sous-titre : Josefin Sans Bold bas de casse (pas de \MakeUppercase, à la
% différence du titre), un peu plus petit, centré sur deux lignes — largeur
% de boîte pour forcer le retour à la ligne, même principe que
% \PURHContributionTitleWidth pour les titres d'ouverture de contribution
% (référentiel §7.3 : reproduire la coupure plutôt que l'exiger en dur).
\newcommand{{\PurhSubtitle}}[1]{{%
  \par\vspace{{0.6\baselineskip}}%
  \begin{{center}}
  \parbox{{88mm}}{{\PURHTitleFont\bfseries\fontsize{{15pt}}{{18pt}}\selectfont\centering #1}}
  \end{{center}}
  \vspace{{0.4\baselineskip}}%
}}

% Responsabilité éditoriale : Chaparral Pro (fonte principale, aucun
% changement de famille) gras bas de casse, plus petit que le sous-titre,
% sur deux lignes explicites — « sous la direction de » toujours seul sur
% sa propre ligne, puis les noms sur la suivante (référentiel §8.1,
% vérification humaine directe du 2026-08-04). #1 est déjà le texte complet
% des deux lignes, séparées par \\ côté appelant (latei_driver.py), pas
% reconstruites ici : cette macro ne fait que les mettre en forme.
\newcommand{{\PurhContributors}}[1]{{%
  \par\vspace{{0.5\baselineskip}}%
  {{\bfseries\fontsize{{11pt}}{{13pt}}\selectfont\centering #1\par}}%
  \vspace{{0.6\baselineskip}}%
}}

% Mention finale de la page de titre (référentiel v0.7, vérification
% humaine directe du 2026-08-04, complétée le 2026-08-05) : nom complet de
% l'éditeur, majuscules grasses, sur UNE SEULE ligne, Chaparral (fonte
% principale, aucun changement de famille) — pas \PURHTitleFont/Josefin,
% contrairement à toute la titraille (§2.4/§3 du référentiel v0.7) : cette
% mention n'est pas un niveau de titraille, c'est une mention
% institutionnelle calée en bas de page.
%
% \resizebox{{0.95\linewidth}}{{!}}{{...}} plutôt qu'une simple
% \fontsize{{14pt}}{{16pt}} fixe (première version, abandonnée le
% 2026-08-05) : à 14 pt, « PRESSES UNIVERSITAIRES DE ROUEN ET DU HAVRE »
% (44 caractères) ne tenait pas sur une seule ligne à la largeur
% d'empagement de ce profil (~105 mm) et retombait sur deux lignes — bug
% réel constaté par vérification humaine directe du PDF généré.
% \resizebox emballe le texte dans une boîte horizontale non coupable
% (empêchant tout retour à la ligne, contrairement à un simple changement
% de \fontsize) puis la met à l'échelle pour occuper exactement 95 % de la
% largeur de la page — garantit à la fois la ligne unique et le remplissage
% « une bonne partie de la largeur de la page » quel que soit le nom
% affiché ou le profil, sans avoir à calculer un corps de police à la main.
\newcommand{{\PurhPublisherMention}}[1]{{%
  \noindent\resizebox{{0.95\linewidth}}{{!}}{{\bfseries\MakeUppercase{{#1}}}}\par
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
  }}

% -----------------------------------------------------------------
% Liminaires PURH (référentiel v0.6 §8.1, P0 — "construire la séquence
% complète des liminaires") : pages blanches, faux-titre, crédits, page de
% titre. Construites depuis les métadonnées du livre par latei_driver.py,
% jamais depuis le corps LaTEI réversible. Toutes en pagestyle empty (ni
% folio ni titre courant), mais comptées dans la pagination — jamais
% \begin{{titlepage}} (dont le mode de compatibilité LaTeX 2.09 remet parfois
% \c@page à 1, un risque inutile ici où le compte doit au contraire
% continuer sans interruption depuis la toute première page physique).
% -----------------------------------------------------------------
\newcommand{{\PURHBlankPage}}{{%
  \clearpage
  \thispagestyle{{empty}}%
  \mbox{{}}%
  \clearpage
}}

% Vérification humaine directe du 2026-08-04 (faux-titre) :
% remonté sur la page (0.35\textheight -> 0.25\textheight, approximatif —
% « un peu plus haut », aucune mesure millimétrique donnée) et repassé en
% Josefin Sans Bold capitales, même corps que les titres de section
% (\titleformat{{\section}}, 12/14 pt) — le référentiel ne donnait aucune
% cible pour ce niveau spécifique, seule cette vérification fait foi ici,
% comme pour les autres corrections de graisse de ce chantier.
\newcommand{{\PURHFalseTitle}}[1]{{%
  \clearpage
  \thispagestyle{{empty}}%
  \begin{{center}}
  \vspace*{{0.25\textheight}}
  {{\PURHTitleFont\bfseries\fontsize{{12pt}}{{14pt}}\selectfont\MakeUppercase{{#1}}\par}}
  \end{{center}}
  \clearpage
}}

% Chaparral Pro (fonte principale du document, aucun changement de famille
% nécessaire) 10 pt — vérification humaine directe du 2026-08-04 : \small
% ne correspond pas nécessairement à 10 pt exactement (dépend de l'échelle
% de tailles du \documentclass), remplacé par une taille explicite.
% \vspace*{{\fill}} (pas \vspace*{{0.3\textheight}}, ni un \vfill non étoilé)
% : deuxième vérification humaine directe — le colophon doit être calé en
% bas de page, pas centré verticalement. Un \vfill nu en tout début de page
% est silencieusement absorbé par l'algorithme de coupure de page de TeX
% (jamais visible, confirmé par reproduction : le contenu restait centré
% près du haut) — surtout avec \raggedbottom actif dans ce document, qui
% autorise justement les pages à ne pas s'étirer jusqu'à \textheight.
% \vspace* (étoilé) protège la glue même en tête de page.
\newcommand{{\PURHCreditsPage}}[1]{{%
  \clearpage
  \thispagestyle{{empty}}%
  \begin{{center}}
  \vspace*{{\fill}}
  \fontsize{{10pt}}{{11.5pt}}\selectfont
  #1
  \end{{center}}
  \clearpage
}}

% Vérification humaine directe du 2026-08-04 : même hauteur de départ que
% le faux-titre (0.25\textheight, pas 0.15) — seul le corps du titre change
% entre les deux pages, pas sa position verticale.
\newcommand{{\PURHTitlePage}}[1]{{%
  \clearpage
  \thispagestyle{{empty}}%
  \begin{{center}}
  \vspace*{{0.25\textheight}}
  #1
  \end{{center}}
  \clearpage
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
