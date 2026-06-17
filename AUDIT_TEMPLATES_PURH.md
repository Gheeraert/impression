# Audit comparatif des templates LaTeX PURH

## 1. Résumé exécutif

Les deux fichiers témoins confirment que le futur style PDF PURH minimal doit rester beaucoup plus modeste qu'une reprise directe de template existant. L'information éditoriale complémentaire change toutefois la hiérarchie d'analyse : `theorie_info.tex` doit être considéré comme le témoin typographique principal, car il correspond à un ouvrage réellement mis en page selon les souhaits des éditrices des PURH. Il ne doit pas être repris tel quel, car son préambule contient de nombreuses dépendances scientifiques et macros propres à un livre de théorie de l'information, mais son noyau typographique doit servir de référence prioritaire.

Pour le futur style PDF PURH minimal, `theorie_info.tex` doit donc guider d'abord le format 155 x 230 mm, les marges, la logique recto/verso, les titres courants, les numéros de page extérieurs, les styles de titres, la table des matières, les notes, les légendes et la typographie française générale. `template.tex` devient un témoin secondaire utile : il permet de comparer certains choix éditoriaux, d'identifier des besoins de pages liminaires, de crédits et de placeholders, mais il ne doit pas piloter la passe 12C.

Le LaTeX actuellement généré par `purh_site/latex_renderer.py` est volontairement plus sobre : classe `memoir`, LuaLaTeX, `fontspec`, `polyglossia`, `microtype`, `graphicx`, `csquotes`, `hyperref`, `bookmark`, `caption`, `enumitem`, `verse`, `ragged2e`, `xurl`, format 155 x 230 mm et bibliographie rendue en texte simple. Cette base est saine. Les templates invitent surtout à améliorer, par petites passes, les marges, le recto/verso, les titres courants et le style des titres, sans introduire encore de `.cls`, de template externe actif, de `biblatex`, de `tikz`, de `minted` ou de dépendances lourdes.

Recommandation centrale : définir d'abord un style PURH minimal dans `LatexRenderOptions` ou dans une méthode de préambule dédiée, en extrayant prioritairement le noyau validé dans `theorie_info.tex`. Ce style doit rester limité au format, aux marges, à la pagination, aux en-têtes courants, aux titres, au sommaire, aux notes, aux légendes et aux réglages typographiques français. Le reste doit rester optionnel par type d'ouvrage.

## 2. Nature des fichiers analysés

### `template.tex`

`template.tex` est un modèle de livre PURH antérieur et doit être traité comme témoin secondaire. Il utilise `\documentclass[a5paper,twoside]{book}`, mais redéfinit ensuite le papier avec `geometry` en 155 x 230 mm. Le fichier est conçu comme un template avec variables Pandoc ou assimilées : `$title$`, `$subtitle$`, `$body$`, `$collection_presentation$`, `$isbnprint$`, `$for(authors)$`, `$authors.forname$`, `$authors.surname$`, `$sep$`, `$endfor$`.

Le moteur probable est LuaLaTeX, malgré la présence contradictoire de `fontenc` et `inputenc`, car le fichier charge `fontspec`, `\babelfont`, `crop` avec option `lualatex`, et des fontes système comme Chaparral Pro et Josefin Sans. La logique de mise en page est éditoriale : pages liminaires codées, page de titre, page collection, corps, table des matières en fin, pages de chapitre sans numéro, en-têtes courants par `fancyhdr`, captions personnalisées, notes de bas de page travaillées.

Le fichier contient beaucoup d'éléments spécifiques à un livre d'origine : collection "De Code et de Plomb", personnes créditées, préface/postface nommées, licence, adresse PURH, ISSN, mentions de maquettage, présentation de collection, commandes d'auteur de chapitre, environnement de dédicace. Ces éléments sont utiles comme exemples de besoins éditoriaux, mais ne doivent pas être repris tels quels ni servir de base prioritaire au style 12C.

### `theorie_info.tex`

`theorie_info.tex` est moins un template qu'un fichier source complet d'un livre. Il doit néanmoins être considéré comme le témoin typographique principal, parce qu'il correspond à un ouvrage effectivement composé selon les attentes éditoriales PURH. Il utilise `\documentclass[12pt,titlepage]{book}` et contient à la fois le préambule, les pages liminaires, le texte, les figures TikZ, les exercices, les listings Python, la bibliographie et l'index.

Le moteur probable est aussi LuaLaTeX : usage de `fontspec`, Chaparral Pro, Josefin Sans et Amiri. Le fichier charge néanmoins `babel` plutôt que `polyglossia`. La mise en page est celle d'un ouvrage technique : nombreux environnements mathématiques, `tikz`, `tkz-tab`, `listings`, `biblatex` avec `biber`, index, tableaux longs, paysages, figures rotatives.

Il y a peu de variables génériques. Les titres courants, la bibliographie, les pages liminaires, la pagination initiale, les crédits et l'ensemble des macros d'exercices sont codés pour ce livre. Sa valeur principale pour Impressions est de fournir la référence prioritaire du noyau typographique PURH : `geometry`, `titlesec`, `titletoc`, `fancyhdr`, notes, légendes, réglages français et pagination extérieure. Les éléments scientifiques et pédagogiques doivent être écartés du noyau.

## 3. Dépendances et portabilité

### A. Noyau probablement utile pour un PDF PURH générique

- `geometry` : présent dans les deux témoins. Utile si la classe reste `book`; moins nécessaire avec `memoir`, qui gère déjà le layout. Les valeurs de `geometry` restent une bonne référence.
- `fontspec` : indispensable si la cible officielle est LuaLaTeX.
- Gestion du français : `babel` est présent dans les deux témoins; `latex_renderer.py` utilise actuellement `polyglossia`. Pour LuaLaTeX, les deux sont possibles, mais il faut choisir une seule politique.
- `microtype` : présent dans `template.tex`, commenté dans `theorie_info.tex`, déjà utilisé par `latex_renderer.py`. À garder.
- `csquotes` : présent dans les deux témoins et déjà utilisé. À garder.
- `fancyhdr` : présent dans les deux témoins. Utile si la classe est `book`; avec `memoir`, il faut décider entre les mécanismes natifs de `memoir` et `fancyhdr`. Le modèle logique reste utile.
- `titlesec` : présent dans les deux témoins. Utile pour documenter le style attendu, mais à intégrer avec prudence si la classe reste `memoir`, car `memoir` possède ses propres mécanismes de titres.
- `titletoc` ou alternative : `theorie_info.tex` utilise `titletoc`; `template.tex` utilise `tocloft`; `memoir` offre aussi ses propres réglages. Ne pas rendre obligatoire trop tôt.
- `graphicx` : présent dans les deux témoins et déjà utilisé. À garder.
- `caption` : présent dans les deux témoins et déjà utilisé. À garder.
- `enumitem` : présent dans les deux témoins et déjà utilisé. À garder.
- `longtable` / `tabularx` : présents dans `theorie_info.tex`. Pertinents dès que le modèle sémantique représentera réellement les tableaux.
- `hyperref` / `bookmark` : `template.tex` charge `hyperref`, `latex_renderer.py` charge `hyperref` et `bookmark`. À garder.

### B. Packages utiles seulement pour certains livres

- `amsmath`, `amssymb`, `amsfonts`, `amsthm` et apparentés : nécessaires pour ouvrages mathématiques ou techniques, pas pour le noyau PURH.
- `tikz`, bibliothèques TikZ, `tkz-tab` : utiles pour figures mathématiques ou diagrammes sources, trop lourds pour le noyau.
- `listings` : utile pour code source; `template.tex` utilise plutôt `minted`, qui est plus contraignant.
- `makeidx` : utile si l'index est modélisé, à reporter.
- `biblatex` / `biber` : utile à terme, mais ajoute une passe de build et des conventions bibliographiques fortes.
- `multicol` : utile pour index ou mises en page ponctuelles.
- `rotating`, `lscape`, `float`, `array` : utiles pour cas spécifiques de figures et tableaux.
- `lettrine`, `wrapfig`, `subcaption`, `varioref`, `classics`, `scrextend`, `changepage`, `fancybox`, `needspace`, `afterpage` : à traiter comme besoins spécialisés.

### C. Packages ou choix à éviter ou reporter

- `minted` : à éviter dans le noyau, car dépend de Pygments et requiert généralement `-shell-escape`.
- `svg` avec conversion Inkscape : à éviter dans le noyau, car dépend d'un outil externe.
- Fontes commerciales ou système non garanties : Chaparral Pro et certaines variantes Josefin Sans ne doivent pas être des dépendances immédiates.
- Macros d'ouvrage : `\exercice`, `\Probleme`, `\Theorem`, `\Definition`, `\auteur`, environnements de dédicace et macros de classiques doivent rester hors noyau.
- Réglages répétés ou contradictoires : `theorie_info.tex` charge `indentfirst` deux fois, `tikz` deux fois, redéfinit `baselinestretch`, commente des alternatives anciennes; `template.tex` combine `inputenc`/`fontenc` avec `fontspec`.

## 4. Format, marges et mise en page

Les deux témoins convergent vers un format papier PURH de 155 x 230 mm. La référence prioritaire doit être `theorie_info.tex`, puisque ce fichier reflète une composition validée éditorialement. `template.tex` confirme le même format, mais son option initiale `a5paper` est ensuite contredite par `geometry`.

`template.tex` :

- classe `book`, option `twoside`;
- `paperwidth=155mm`, `paperheight=230mm`;
- `margin=23mm`, puis `left=20mm`, `right=30mm`, `top=30mm`, `bottom=19mm`;
- pas de `inner` / `outer` explicites malgré `twoside`;
- `crop` activé avec `center,a4,cam,lualatex`, donc repères de coupe et placement sur A4;
- `headsep=27pt`;
- pages de chapitre en style `empty`;
- deux pages blanches initiales et pages liminaires codées.

`theorie_info.tex` :

- classe `book`, option `titlepage`, taille 12 pt;
- `paperwidth=155mm`, `paperheight=230mm`;
- `top=30mm`, `bottom=19mm`, `inner=23mm`, `outer=23mm`;
- `headheight=14pt`, `headsep=8mm`, `footskip=10mm`;
- crop commenté;
- recto/verso implicite par la classe `book`;
- suppression ponctuelle des pages blanches avec `\let\cleardoublepage\clearpage`;
- pagination arabe réinitialisée à 11 après liminaires.

`latex_renderer.py` :

- classe `memoir`, 11 pt par défaut;
- `paper_width_mm=155`, `paper_height_mm=230`;
- `oneside=True`, `openany=True`;
- marges : inner 23 mm, outer 22 mm, upper 24 mm, lower 22 mm;
- layout via `\setstocksize`, `\settrimmedsize`, `\setlrmarginsandblock`, `\setulmarginsandblock`, `\checkandfixthelayout`;
- pas de repères de coupe;
- pas encore de politique explicite d'en-têtes courants.

Proposition de base pour Impressions, à extraire en priorité de `theorie_info.tex` :

- format par défaut : 155 x 230 mm;
- moteur : LuaLaTeX;
- recto/verso à prévoir pour le style PURH, même si le mode actuel `oneside` reste utile pour les tests;
- marges initiales recommandées : inner 23 mm, outer 23 mm, top 30 mm, bottom 19 mm, headheight environ 14 pt, headsep 8 mm, footskip 10 mm;
- crop et repères de coupe : option de production future, pas dans le style minimal;
- options configurables plus tard : `oneside/twoside`, `openany/openright`, marges, présence des crop marks, taille de fonte.

## 5. Titres, sommaire et hiérarchie

`template.tex` donne un style de chapitre centré, en Josefin Sans Bold, avec nom de chapitre et numéro en petites capitales ou capitales, puis titre en capitales. Les sections sont également centrées et plutôt compactes. La table des matières est personnalisée avec `tocloft`, points de conduite, espacement avant/après titre et titre "TABLE DES MATIÈRES" centré. Ces choix restent utiles en comparaison, mais ils sont secondaires pour la passe 12C.

`theorie_info.tex` donne le style de référence prioritaire : chapitre en display, très grand, Josefin Sans, aligné à gauche; sections et sous-sections en blocs alignés à gauche; espacements précis par `\titlespacing`; `secnumdepth=0`, ce qui désactive la numérotation des sections et sous-sections malgré des formats prévus avec `\thesection`. La table des matières passe par `titletoc`, avec chapitres en gras Josefin Sans. Pour 12C, c'est cette logique qu'il faut simplifier et traduire dans le style PURH minimal.

`latex_renderer.py` s'appuie pour l'instant sur le style par défaut de `memoir`, avec `\setsecnumdepth{subsection}` et `\settocdepth{subsection}`. Il génère `\chapter`, `\chapter*`, `\section`, `\subsection`, `\subsubsection`, avec ajout manuel au sommaire pour les chapitres non numérotés.

Ce qui peut nourrir `LatexRenderer` maintenant :

- distinction claire entre titres numérotés du corps et titres non numérotés des liminaires/postliminaires;
- style de chapitre plus éditorial mais sobre;
- réglage des espacements de titres;
- table des matières avec profondeur maîtrisée;
- absence d'en-tête sur les premières pages de chapitre.

Ce qui devrait aller plus tard dans un template ou une classe :

- design complet de page de titre;
- table des matières très dessinée;
- styles alternatifs par collection;
- macros spécifiques aux auteurs, préfaces, postfaces et collections.

## 6. En-têtes courants et pagination

`template.tex` configure `fancyhdr` avec plusieurs styles. Le style principal place le titre du livre sur les pages paires (`RE`) et le titre courant de chapitre sur les pages impaires (`LO`), avec le numéro de page à l'extérieur (`LE,RO`). Le titre du livre est stocké dans `\booktitle`, initialisé depuis `$title$`. Les marques de chapitre sont simplifiées avec :

```tex
\renewcommand{\chaptermark}[1]{\markboth{#1}{}}
```

Le fichier définit aussi des styles `author` et `noauthor`, mais ils semblent spécifiques à des configurations éditoriales particulières.

`theorie_info.tex` est la référence prioritaire pour la stratégie demandée :

```tex
\fancyhead[LE]{\thepage}
\fancyhead[RE]{\small\itshape Introduction à la théorie de l'information}
\fancyhead[LO]{\small\itshape\nouppercase{\leftmark}}
\fancyhead[RO]{\thepage}
\renewcommand{\chaptermark}[1]{\markboth{#1}{}}
\fancypagestyle{plain}{...}
```

Les numéros sont bien placés à l'extérieur : gauche sur pages paires, droite sur pages impaires. Le titre courant pair est cependant codé en dur. Le titre courant impair vient de `\leftmark`, donc du chapitre. Le style `plain` vide les en-têtes des premières pages de chapitre.

Ce qui pourrait devenir générique :

- `\leftmark` comme titre de chapitre;
- une macro de titre de volume alimentée par les métadonnées;
- `\chaptermark` pour éviter les formes automatiques trop verbeuses;
- numéro extérieur;
- `plain` sans en-tête.

Stratégie simple pour Impressions, dérivée d'abord de `theorie_info.tex` :

- pages paires : numéro extérieur à gauche, titre du volume à droite;
- pages impaires : titre du chapitre à gauche, numéro extérieur à droite;
- pas d'en-tête ni de pied sur la première page de chapitre;
- pas de filet d'en-tête dans la première version;
- avec `memoir`, privilégier les pagestyles natifs de `memoir` si possible, pour éviter un conflit inutile avec `fancyhdr`.

## 7. Langues, typographie française et césure

`template.tex` charge `babel` avec plusieurs langues : grec ancien, latin classique, italien, anglais, britannique, français. Il utilise `\babelfont` pour le grec ancien, désactive `AutoSpacePunctuation`, configure les notes françaises avec `FrenchFootnotes=false` et `AutoSpaceFootnotes=false`, et charge `csquotes`. Il contient aussi un bloc vide `\begin{hyphenrules}{french}`.

`theorie_info.tex` charge `babel` en français, `indentfirst`, `csquotes` et `\MakeOuterQuote{"}`. Il règle les pénalités de césure, veuves et orphelines :

- `\pretolerance=100`;
- `\tolerance=500`;
- `\hyphenpenalty=500`;
- `\exhyphenpenalty=500`;
- `\emergencystretch=3em`;
- `\clubpenalty=10000`;
- `\widowpenalty=10000`;
- `\displaywidowpenalty=10000`.

`latex_renderer.py` utilise `polyglossia`, `\setmainlanguage{french}`, `csquotes` et `microtype`, mais ne règle pas encore explicitement `indentfirst`, les veuves/orphelines ou les espaces françaises.

Politique recommandée avec LuaLaTeX :

- choisir une seule pile linguistique : soit `polyglossia`, déjà en place, soit `babel` moderne avec LuaLaTeX;
- conserver `csquotes` et générer les citations inline avec `\enquote`;
- conserver `microtype`;
- ajouter une politique simple de veuves/orphelines et d'`emergencystretch`;
- ajouter `indentfirst` ou équivalent si la typographie PURH l'exige;
- éviter `\MakeOuterQuote{"}` dans un renderer automatique, car cela modifie globalement le sens du caractère guillemet et peut perturber du contenu généré.

## 8. Polices

`template.tex` utilise :

- Chaparral Pro comme fonte principale;
- Chaparral Pro Bold;
- Josefin Sans, Josefin Sans Light, Josefin Sans Bold pour titres et en-têtes;
- Latin Modern Mono et DejaVu Sans Mono pour monospace;
- Old Standard pour grec ancien.

`theorie_info.tex` utilise :

- Chaparral Pro comme fonte principale;
- Josefin Sans pour titres;
- Amiri pour arabe;
- police monospace par défaut de `listings`.

`latex_renderer.py` utilise actuellement des fontes libres et disponibles dans TeX Live :

- TeX Gyre Pagella;
- TeX Gyre Heros;
- Latin Modern Mono.

Recommandation :

- ne pas dépendre immédiatement de Chaparral Pro;
- conserver des fontes libres par défaut, par exemple TeX Gyre Pagella pour le texte et TeX Gyre Heros ou Source Sans 3 si disponible pour les titres;
- rendre les fontes configurables plus tard dans `LatexRenderOptions`;
- traiter Chaparral Pro et Josefin Sans comme un profil éditorial optionnel, activable seulement sur des postes où les fontes sont installées;
- prévoir un fallback stable pour la compilation CI et les tests.

## 9. Notes, figures et tableaux

`template.tex` travaille fortement les notes de bas de page avec `scrextend`, `\deffootnote`, taille 9.5/10.5 pt, réinitialisation à chaque chapitre et réglages de notes françaises. Il personnalise aussi les captions avec `caption`, en 9/11 pt, séparateur point, label formaté, et prend en charge `graphicx`, `subcaption`, `wrapfig`, `svg`. Ces éléments sont précieux pour repérer des besoins éditoriaux, mais ils ne sont pas la source prioritaire de 12C.

`theorie_info.tex` contient beaucoup de figures TikZ et d'images, `graphicx`, `caption`, `float`, `rotating`, `lscape`, `longtable`, `tabularx`, `array`. Les captions restent plus simples : `labelfont=normalfont`, `textfont=normalfont`. Pour le style minimal, il faut reprendre l'esprit sobre des légendes et non les dépendances spécialisées. Les tableaux, figures rotatives et paysages font partie du besoin d'un livre technique, mais pas d'un noyau minimal.

`latex_renderer.py` rend les figures dans un environnement `center`, avec `\includegraphics` si le chemin existe, un fallback encadré sinon, et une légende en `\small`. Il n'utilise pas encore l'environnement `figure` ni `\caption`, même si le package `caption` est chargé. Les notes sont générées en `\footnote{...}` depuis le modèle sémantique.

Améliorations rapides possibles sans refonte :

- définir un style `caption` cohérent avec PURH;
- basculer progressivement les figures vers `figure` + `\caption` si le modèle sémantique doit produire une liste des figures;
- régler taille et indentation des notes de bas de page;
- garder `longtable` et `tabularx` pour une future passe tableaux, seulement quand le modèle sémantique représentera les tableaux;
- ne pas introduire `svg`, `wrapfig`, `subcaption`, `rotating` ou `lscape` dans le noyau.

## 10. Bibliographie et index

`template.tex` contient des macros CSL/Pandoc (`CSLReferences`, `\citeproc`, `\CSLBlock`, etc.) et une bibliographie plutôt conçue pour recevoir du LaTeX généré par Pandoc. Il ne charge pas `biblatex`.

`theorie_info.tex` charge `biblatex` avec `backend=biber`, `style=authoryear`, `bibliographie.bib`, personnalise l'environnement de bibliographie en liste numérotée, puis appelle `\nocite{*}` et `\printbibliography`. Il utilise aussi `makeidx`, `\makeindex`, `\index{...}` et `\printindex`.

`pdf_builder.py` indique explicitement que la V1 n'utilise pas `biber` : les bibliographies sont déjà formulées dans le XML et rendues comme texte. `latex_renderer.py` rend un `BibliographyBlock` avec `\section*`, `\addcontentsline` et un environnement `PurhBibliography` à indentation suspendue.

Recommandation :

- reporter `biblatex` et `biber`;
- commencer par rendre correctement `listBibl` et `biblStruct` en LaTeX simple depuis le modèle sémantique;
- garder la bibliographie sous forme textuelle tant que les métadonnées TEI ne sont pas stabilisées;
- reporter l'index à une étape dédiée, car il suppose un balisage TEI, une stratégie de tri, `makeindex` ou `xindy`, et une passe de build supplémentaire;
- ne pas faire dépendre le style PURH minimal de `biblatex`, `makeidx` ou `biber`.

## 11. Contenus codés en dur

`template.tex` contient des éléments éditoriaux PURH et livre :

- collection "De Code et de Plomb";
- noms de responsables éditoriaux, maquettage et design;
- mentions de préface et postface;
- adresse, licence, ISBN/ISSN;
- texte sur la version augmentée en accès libre;
- pages blanches initiales;
- table des matières placée après le corps;
- macros d'auteur de chapitre.

`theorie_info.tex` contient presque tout le livre :

- titre courant pair "Introduction à la théorie de l'information";
- dédicace, remerciements, préface;
- pagination démarrant à 11;
- bibliographie `bibliographie.bib`;
- photo auteur `photo_khadir.png`;
- macros d'exercices, corrigés, théorèmes, définitions, TP;
- contenus TikZ et listings Python;
- chapitres, figures et index propres à l'ouvrage.

Ces contenus ne doivent pas entrer dans `LatexRenderer`. Ils peuvent inspirer une future distinction entre métadonnées de volume, liminaires, corps, postliminaires et collections, mais pas une intégration directe.

## 12. Comparaison avec `latex_renderer.py`

Ce qui existe déjà :

- chaîne LuaLaTeX;
- format 155 x 230 mm;
- fontes configurables dans `LatexRenderOptions`;
- `fontspec`, `polyglossia`, `microtype`, `graphicx`, `csquotes`, `hyperref`, `bookmark`, `caption`, `enumitem`, `xurl`;
- rendu des titres de volume, contributeurs, divisions, sections, citations, notes, listes, vers, figures et bibliographie simple;
- séparation entre rendu LaTeX et compilation PDF;
- tests possibles sur le `.tex` sans compilation obligatoire.

Ce qui manque par rapport aux témoins :

- style explicite d'en-têtes courants;
- stratégie recto/verso PURH;
- pages de chapitre sans en-tête;
- style de titres proche PURH;
- style de table des matières;
- réglage plus précis des notes;
- réglage des captions;
- politique française sur veuves/orphelines et indentation après titre;
- options de crop ou production imprimée, à reporter.

Ce qui doit être remplacé ou ajusté :

- les marges actuelles `upper=24`, `lower=22` sont plus prudentes mais moins alignées avec les témoins que `top=30`, `bottom=19`;
- `oneside=True` est utile en V1, mais le style PURH devrait proposer `twoside`;
- la génération de figures en `center` peut rester robuste, mais devra évoluer si l'on veut des captions LaTeX et listes de figures;
- les styles par défaut de `memoir` sont sobres mais pas encore PURH.

Ce qui doit rester optionnel :

- mathématiques avancées;
- `tikz`, `tkz-tab`;
- code source (`listings` ou autre);
- bibliographie `biblatex`;
- index;
- fontes commerciales;
- crop marks;
- tableaux longs et paysages;
- pages liminaires de collection.

Ce qui est trop spécifique :

- macros CSL Pandoc de `template.tex`;
- `minted` et `svg`;
- macros d'exercices de `theorie_info.tex`;
- titres courants codés en dur;
- crédits, adresses, personnes, collection;
- bibliographie `bibliographie.bib`;
- commandes multilingues grec/latin/arabe dans le noyau.

## 13. Recommandation d’architecture

Ne pas intégrer massivement les templates. La bonne trajectoire est de garder `LatexRenderer` comme générateur sémantique et de définir un profil de style minimal paramétrable. Ce profil doit être prioritairement dérivé de `theorie_info.tex`, car c'est le témoin typographique validé par les éditrices, puis contrôlé par comparaison avec `template.tex`.

Architecture recommandée :

- conserver `PdfBuilder` séparé;
- ne pas modifier `BuildConfig` ni `SiteBuilder` pour l'instant;
- ne pas créer encore de classe `.cls`;
- ne pas créer de template externe actif;
- ajouter plus tard une option comme `style="purh"` dans `LatexRenderOptions`, ou une méthode dédiée de préambule PURH, en prenant `theorie_info.tex` comme source typographique principale;
- garder le style par défaut actuel pour les tests et la robustesse;
- introduire seulement les packages du noyau quand ils servent un rendu réellement généré;
- continuer à tester le `.tex` produit sans exiger une compilation LaTeX complète en CI.

Dans une future passe, si la logique typographique grossit, il sera raisonnable d'extraire une classe ou un fichier de style. Mais ce serait prématuré tant que le renderer ne sait pas encore générer toutes les structures typographiques concernées.

## 14. Plan d’intégration par petites passes

### Passe 12C recommandée

Ajouter une option expérimentale `style="purh"` dans `LatexRenderOptions`, sans intégration au build web, en extrayant d'abord le noyau typographique validé dans `theorie_info.tex`. La passe doit rester limitée à ces sujets :

- format et marges 155 x 230 mm avec profil recto/verso;
- en-têtes courants : titre du volume sur pages paires, titre du chapitre sur pages impaires, numéro extérieur;
- style `plain` sans en-tête sur premières pages de chapitre;
- styles de titres et table des matières dans une version simplifiée;
- réglages typographiques simples : français, `microtype`, veuves/orphelines, captions et notes.

Cette passe devrait rester testable par inspection du `.tex` généré. Elle ne doit pas encore compiler obligatoirement le PDF. Elle ne doit pas importer les macros scientifiques, les environnements mathématiques, les listings, les figures spécialisées ni les dépendances propres à `theorie_info.tex`.

### Passes ultérieures possibles

- 12D : style de titres et table des matières, en choisissant soit les outils `memoir`, soit une bascule explicite vers `book` + `titlesec`.
- 12E : amélioration des figures avec `figure`, `caption`, labels éventuels et liste des figures si le modèle le justifie.
- 12F : rendu bibliographique TEI simple plus riche, sans `biblatex`.
- 12G : tableaux TEI avec `longtable` ou `tabularx`.
- 12H : index, uniquement après stabilisation du balisage source et de la chaîne de compilation.
- Plus tard : classe `.cls` ou template externe si plusieurs styles PURH deviennent nécessaires.

## 15. Conclusion

Les deux témoins valident un socle PURH cohérent : LuaLaTeX, format 155 x 230 mm, composition recto/verso, fontes éditoriales configurables, titres travaillés, captions sobres, notes lisibles, en-têtes courants avec numéro extérieur. La priorité doit maintenant être explicite : `theorie_info.tex` est le témoin typographique principal pour la passe 12C, car il reflète une mise en page réellement validée selon les souhaits éditoriaux des PURH. `template.tex` reste un témoin secondaire pour comparer les choix éditoriaux et documenter les besoins de liminaires, crédits et placeholders.

La chaîne actuelle d'Impressions est déjà placée au bon niveau d'abstraction : TEI normalisée, modèle sémantique Python, LaTeX généré, PDF construit séparément. La prochaine étape ne doit pas être une reprise de template, mais une petite couche de style PURH minimal, testée par le LaTeX produit et gardée optionnelle tant qu'elle n'est pas stabilisée.
