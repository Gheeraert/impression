# Audit TeX Stable Vs LaTEI Direct

## Source

- Fixture: `tests\fixtures\metopes\heraldique_ii.book.normalized.xml`
- Stable `book.tex`: `C:\impression2\_latei_tex_audit_runtime\stable_pdf\book.tex`
- LaTEI main: `_latei_tex_audit_runtime\latei_pdf\heraldique_ii.book.normalized.latei_main.tex`
- LaTEI macros: `_latei_tex_audit_runtime\latei_pdf\heraldique_ii.book.normalized.latei_macros.tex`
- LaTEI body: `_latei_tex_audit_runtime\latei_pdf\heraldique_ii.book.normalized.latei_body.tex`

This report does not compare `book.tex` and `latei_body.tex` as equal text.
The stable `book.tex` is final typographic LaTeX, while `latei_body.tex` is the reversible semantic source.
The comparison below is structural and cause-oriented.

## Title page audit

- Stable title extras: `0`
- LaTEI title extras: `0`
- Stable contains `PURH - 2025`: `False`
- LaTEI contains `PURH - 2025`: `True`
- Stable contains print ISBN on title page: `False`
- LaTEI contains print ISBN on title page: `True`
- LaTEI visible experimental marker: `False`

Potential divergence: LaTEI currently prints publication year and print ISBN on the title page, while the stable extracted PDF text reaches front matter immediately after `PURH`.

## Footnote audit

Stable sample:

```latex
\footnotesep}{0.6\baselineskip}

\footnotelayout}{\fontsize{9.5pt}{10.5pt}\selectfont}

\footnote{André Chastel, \textit{La grottesque}, Paris, Le Promeneur, 1988.}
```

LaTEI sample:

```latex
\teiNote[n={1},place={foot},xmlid={ftn1}]{\teiP[xmlid={p-016}]{André Chastel, \teiHi[rend={italic}]{La grottesque}, Paris, Le Promeneur, 1988.}}

\teiNote[n={2},place={foot},xmlid={ftn7}]{\teiP[xmlid={p-017}]{Yvan Loskoutoff, « Le symbolisme des \teiHi[rend={italic}]{palle} médicéennes à la villa Madama », \teiHi[rend={italic}]{Journal des savants}, n\teiHi[rend={sup}]{o} 2, 2001, p. 351-391.}}

\teiNote[n={3},place={foot},xmlid={ftn8}]{\teiP[xmlid={p-020}]{Voir son article, « Un partisan de la France en quête de protection : ce “bon vieux” chevalier Francesco Gualdi et le cardinal Mazarin », dans Yvan Loskoutoff et Patrick Michel (dir.), \teiHi[rend={italic}]{Mazarin, Rome et l’Italie}, Mont-Saint-Aignan, Presses universitaires de Rouen et du Havre, 2021-2022, t. 2, p. 199-238.}}
```

- LaTEI notes containing `\teiP`: `471`
- LaTEI `\teiP` definition emits `\par`: `True`
- LaTEI `\teiP` has note-context inline branch: `True`
- LaTEI note macro has nested-note guard: `True`

LaTEI notes containing `\teiP` samples:

```latex
\teiNote[n={1},place={foot},xmlid={ftn1}]{\teiP[xmlid={p-016}]{André Chastel, \teiHi[rend={italic}]{La grottesque}, Paris, Le Promeneur, 1988.}}

\teiNote[n={2},place={foot},xmlid={ftn7}]{\teiP[xmlid={p-017}]{Yvan Loskoutoff, « Le symbolisme des \teiHi[rend={italic}]{palle} médicéennes à la villa Madama », \teiHi[rend={italic}]{Journal des savants}, n\teiHi[rend={sup}]{o} 2, 2001, p. 351-391.}}

\teiNote[n={3},place={foot},xmlid={ftn8}]{\teiP[xmlid={p-020}]{Voir son article, « Un partisan de la France en quête de protection : ce “bon vieux” chevalier Francesco Gualdi et le cardinal Mazarin », dans Yvan Loskoutoff et Patrick Michel (dir.), \teiHi[rend={italic}]{Mazarin, Rome et l’Italie}, Mont-Saint-Aignan, Presses universitaires de Rouen et du Havre, 2021-2022, t. 2, p. 199-238.}}

\teiNote[n={4},place={foot},xmlid={ftn9}]{\teiP[xmlid={p-025}]{Principaux ouvrages : Bernard Guenée et Françoise Lehoux, \teiHi[rend={italic}]{Les entrées royales de 1328 à 1515}, Paris, CNRS, 1968 ; Christian Desplat et Paul Mironneau (dir.), \teiHi[rend={italic}]{Les entrées : gloire et déclin d’un cérémonial}, actes du colloque de Pau, Biarritz, Société Henri IV, 1997 ; Daniel Vaillancourt et Marie-France Wagner (dir.), \teiHi[rend={italic}]{Dix-septième siècle}, numéro spécial : \teiHi[rend={italic}]{Les entrées royales}, n\teiHi[rend={sup}]{o} 3, 2001. Le GRES (Groupe de recherche sur les entrées solennelles, université Concordia, Canada) publie des \teiHi[rend={italic}]{Cahiers}.}}

\teiNote[n={5},place={foot},xmlid={ftn10}]{\teiP[xmlid={p-026}]{Certains témoignages écrits signalent pourtant sa présence au \teiHi[rend={small-caps}]{xvi}\teiHi[rend={sup}]{e} siècle sur le caparaçon de la jument, voir Yvan Loskoutoff, « Introduction », dans Yvan Loskoutoff (dir.), \teiHi[rend={italic}]{Héraldique et papauté, Moyen Âge-Temps modernes}, Mont-Saint-Aignan, PURH, 2020, p. 16.}}
```

Macro definitions involved:

```latex
\NewDocumentCommand{\lateiRenderParagraph}{O{} +m}{%
  \iflateiinfootnote
    #2\unskip\space
  \else
    \IfStrEq{\lateiHeadContext}{figure}{%
      \IfSubStr{#1}{rend={caption}}{\par\small #2\par}{%
        \IfSubStr{#1}{rend={credits}}{\par\footnotesize #2\par}{\par #2\par}%
      }%
    }{\par #2\par}%
  \fi
}
\NewDocumentCommand{\teiP}{O{} +m}{\lateiRenderParagraph[#1]{#2}}

% Nested footnotes are not valid LaTeX. If a teiNote appears inside another
% note, render a visible symbolic marker and inline parenthesized content.

% Nested footnotes are not valid LaTeX. If a teiNote appears inside another
% note, render a visible symbolic marker and inline parenthesized content.
\newif\iflateiinfootnote
\lateiinfootnotefalse
\NewDocumentCommand{\teiNote}{O{} +m}{%
  \iflateiinfootnote
    \textsuperscript{*}%
  \else
    \begingroup
      \lateiinfootnotetrue
      \footnote{#2}%
    \endgroup
  \fi
}
\NewDocumentCommand{\teiRef}{O{} +m}{\lateiRenderRef[#1]{#2}}
\NewDocumentCommand{\teiTitle}{O{} +m}{%
  \IfSubStr{#1}{level={m}}{\textit{#2}}{%
    \IfSubStr{#1}{level={j}}{\textit{#2}}{%
      \IfSubStr{#1}{level={a}}{\enquote{#2}}{#2}%
```

Resolved local cause: `\teiP` still appears inside `\teiNote`, but it now has a note-context branch that renders inline before the normal paragraph branch can emit `\par`.

## Paragraph audit

- Stable explicit paragraph breaks (`\par`): `877`
- LaTEI body paragraph macros (`\teiP`): `1081`
- LaTEI macro paragraph breaks (`\par` in macros): `23`
- Contexts audited: normal, note, figure, bibliography.

## Figure audit

- Stable missing-image fallback occurrences: `177`
- LaTEI missing-image fallback defined: `True`
- LaTEI graphics in body: `177`
- LaTEI image include width policy present: `True`

Stable figure/fallback sample:

```latex
De ce point de vue, étudier l’héraldique dans les livres enluminés ayant appartenu aux papes s’avère un instrument précieux pour obtenir des résultats plus intimes, plus précis, sur les équilibres politiques des réseaux de pouvoir de la période.

\begin{center}
\fbox{\parbox{0.8\linewidth}{\centering\footnotesize Image absente ou non fournie}}
\par\small \textbf{Figure 1. \textit{Antiphonaire de Léon X}, Rome, BAV, ms. Capp.Sist.10 : Amico Aspertini, fol. 66v (détail).}
\end{center}

\begin{center}
\fbox{\parbox{0.8\linewidth}{\centering\footnotesize Image absente ou non fournie}}
\par\small \textbf{Figure 2. \textit{Praeparatio ad missam pontificalem}, New York, The Pierpont Morgan Library, ms. H.6 : Attavante degli Attavanti, fol. Iv-IIr.}
```

LaTEI figure macro sample:

```latex
#2%
  \IfSubStr{#1}{type={ordered}}{\end{enumerate}}{\end{itemize}}%
  \endgroup
}{}
\NewDocumentCommand{\teiItem}{O{} +m}{\item #2}
\NewDocumentEnvironment{teiQuote}{O{} +b}{\begin{PurhBlockQuote}#2\end{PurhBlockQuote}}{}
\NewDocumentEnvironment{teiFigure}{O{} +b}{%
  \begingroup
  \lateiSetHeadContext{figure}%
  \begin{center}#2\end{center}%
  \endgroup
}{}
\NewDocumentEnvironment{teiCit}{O{} +b}{#2}{}
\NewDocumentEnvironment{teiBibl}{O{} +b}{\lateiBibliographyEntry{#2}}{}
\NewDocumentEnvironment{teiTable}{O{} +b}{%
```

## Bibliography audit

- Stable `PurhBibliography` block present: `True`
- LaTEI `PurhBibliography` block present in macros: `True`
- Stable hanging entries: `506`
- LaTEI hanging-entry policy present: `True`
- LaTEI `biblStruct` fallback in body: `0`

Stable bibliography sample:

```latex
\subsection{Avignon}

\begin{PurhBibliography}
\noindent\hangindent=1.5em\hangafter=1 Archives municipales : \textsc{CC468} (Comptes de Gaspard Droin, dépenses extraordinaires, non numéroté).\par
\noindent\hangindent=1.5em\hangafter=1 Bibliothèque municipale : ms. 2384 (Recueil de statuts et de privilèges de la ville d’Avignon) ; ms. 5712 (Pierre Pansier, \textit{Les peintres d’Avignon au }\textit{\textsc{xvi}}\textit{\textsuperscript{e}}\textit{ siècle. Biographies et documents}).\par
\end{PurhBibliography}

\subsection{Bologne}

\begin{PurhBibliography}
\noindent\hangindent=1.5em\hangafter=1 Archivio di Stato : \textit{Insignia degli Anziani consoli}, vol. \textsc{VIII}.\par
```

LaTEI bibliography macro sample:

```latex
\ExplSyntaxOff

\NewDocumentCommand{\lateiBibliographyEntry}{+m}{%
  \par\noindent\hangindent=1.5em\hangafter=1 #1\par
}
\NewDocumentCommand{\lateiBibliographyBlock}{+m}{%
  \par
  \begingroup
    \lateiinbibliographytrue
    \begin{PurhBibliography}
    #1%
    \end{PurhBibliography}
  \endgroup
  \par
}
```

## Tables and lists audit

- Stable tabular environments: `0`
- LaTEI table environments in body: `0`
- Stable itemize environments: `1`
- LaTEI list environments in body: `2`

Probable impact: tables/lists are not yet proven visually equivalent and can contribute to page-count drift, but the footnote paragraph pattern is the clearest localized note-layout suspect.

## Suspected causes to verify before correction

1. Footnote paragraph breaks were localized to `\teiP` inside `\teiNote`; the macro layer now suppresses the initial paragraph break in note context.
2. LaTEI title-page extras currently print more metadata than the stable title-page extracted text.
3. Figures and bibliography are readable but still macro-level approximations of the stable renderer.
4. Tables/lists are not yet migrated to visual parity.
