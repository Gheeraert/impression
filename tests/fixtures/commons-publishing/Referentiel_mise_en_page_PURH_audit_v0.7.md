# RÉFÉRENTIEL PURH

## Mise en page intérieure — chantier de parité v0.6 → v0.7 (profil `purh_155x230_production_2025`)

Version 0.7 — 2026-08-04, complétée le 2026-08-05 (TDM §9, titre courant
§2.5, colophon §7.4, page de titre §4.2-§4.4, bugs LaTeX §11)

---

# 0. Objet de cette version

La v0.6 fixait la cible et l'état des lieux. Depuis, un chantier de parité
visuelle a comparé systématiquement le PDF généré aux PDF imprimeur réels de
*Dissimuler pour mieux régner* et *Beautés vitales* (vérification humaine
directe, page à page, jamais une mesure automatisée seule) et a corrigé
quatorze commits de défauts constatés. Cette version 0.7 :

1. **ne remplace pas** la v0.6 comme document de méthode (hiérarchie des
   preuves, statut des profils, architecture LaTEI) — elle en est un
   **journal de modifications**, à lire à sa suite ;
2. documente **chaque valeur exacte** (police, graisse, corps, interligne,
   couleur CMJN, marge, macro LaTeX) telle qu'elle est *implémentée
   aujourd'hui* dans le code, avec sa justification et, si elle contredit un
   passage antérieur du référentiel, la raison de cette contradiction ;
3. est écrite pour qu'une personne qui n'a pas suivi le chantier puisse
   **reproduire le même travail sur un autre format** (195 × 255, 180 × 240)
   sans redécouvrir par tâtonnement les mêmes pièges.

**Portée** : uniquement le profil `purh_155x230_production_2025` (155 × 230
mm), seul format actuellement implémenté. Le profil `purh_155x230_current_2026`
existe toujours dans `purh_layout_profiles.py` mais n'a pas reçu les mêmes
correctifs de titraille/couleur (ceux-ci sont dans les macros et le
préambule, communs à tous les profils — seules les dimensions géométriques
sont propres au profil, voir §12).

**Méthode suivie sur tout le chantier, à respecter pour les prochains
formats** : quand une observation humaine directe sur le PDF généré
face au PDF imprimeur contredit un passage antérieur du référentiel, c'est
l'observation directe qui l'emporte, et l'écart est documenté dans un
commentaire de code à l'endroit corrigé (jamais silencieusement). Ce
document reproduit ces commentaires en substance pour ne pas les laisser
dispersés dans onze fichiers.

---

# 1. Résumé exécutif des changements depuis la v0.6

| # | Sujet | Changement |
|---|---|---|
| 1 | Titraille (parties, chapitres, sections, sous-sections, sous-sous-sections) | Passage de Josefin Sans **Thin** à **Bold**, sur tous les niveaux — le référentiel v0.6 prescrivait Thin, contredit par observation directe |
| 2 | Sous-titre d'ouverture de contribution | Thin Italic → **Bold Italic**, bas de casse |
| 3 | Titre courant (running title) | Quatre réglages successifs (dont un le 2026-08-05) ; valeur finale : famille Thin + couleur CMJN noir **85 %** explicite (pas de changement de graisse) |
| 4 | Texte courant | Couleur CMJN noir 90 % appliquée globalement (`\AtBeginDocument{\color{PURHBodyBlack}}`) |
| 5 | Table des matières | Refonte complète : entrées de contribution non grasses/bas de casse/Chaparral/alignées à gauche avec points de conduite **au niveau du titre** (jamais de l'auteur), entrées de partie centrées Josefin Bold **capitales** (fausses petites capitales, `\MakeUppercase` — `\scshape` inerte sur cette fonte), auteur en gras **bas de casse** sous chaque entrée de contribution (ligne de TDM séparée, voir §9.2/§9.3) |
| 6 | Signature de fin d'article | Nouveau mécanisme : auteur + affiliation réapparaissent à la fin du corps de la contribution, calés à droite, Chaparral 10 pt |
| 7 | Page de titre | Refonte complète : titre principal 22/26 pt, sous-titre 15/18 pt sur 2 lignes calibrées (numéros de siècle en petites capitales, §4.3), responsabilité éditoriale (« sous la direction de », corrigible via GUI/config, §4.4) sur 2 lignes, mention finale PURH en toutes lettres, sur une seule ligne (`\resizebox`), calée en bas de page (§4.2) |
| 8 | Faux-titre | Remonté (0,35 → 0,25 `\textheight`), repassé en Bold capitales 12/14 pt |
| 9 | Colophon (page de crédits) | Calé en bas de page (pas centré verticalement), interlignage resserré, ligne copyright **toujours affichée** (§7.4), ISBN précédé de « ISBN : » ou omis si absent, adresse/URL PURH fixes ajoutées |
| 10 | Coupures de ligne du titre d'ouverture de contribution | Largeur de boîte calibrée empiriquement à 104 mm (vérifiée contre 7 titres réels) |
| 11 | Tableaux : fond des lignes d'en-tête | `\rowcolor{black!30}` généré directement par le writer Python, reconnu et neutralisé par le reader |
| 12 | Ouverture de contribution/partie | `\thispagestyle{empty}` forcé sur la première page (déjà partiellement en place, complété) |
| 13 | Auteur/affiliation sur l'ouverture de contribution | Confirmé masqué par défaut (`show_contribution_author=False`), donnée conservée dans le corps réversible |
| 14 | Liste des auteurs en fin d'ouvrage (item séparé par ligne blanche) | **Non implémenté** — voir §13, aucun marqueur TEI générique disponible |
| 15 | Éditeurs scientifiques mal attribués (page de titre) | Nouveau champ GUI/config `directors_override` pour corriger un TEI source qui ne distingue pas fiablement un `role="pbd"` de compositeur/trice des vrais éditeurs scientifiques (§4.4) |

Le détail de chaque point, avec valeurs exactes et code source, suit dans
les sections thématiques ci-dessous. Six correctifs supplémentaires ont été
apportés le 2026-08-05 (points de suite/casse en TDM §9.2-§9.3, titre
courant §2.5, colophon §7.4, page de titre §4.2-§4.4) ; deux nouveaux
pièges LaTeX rencontrés en les développant sont ajoutés au tableau du §11.

---

# 2. Système typographique — état exact au 2026-08-04

## 2.1. Fontes chargées

```latex
\IfFontExistsTF{Chaparral Pro}
  {\setmainfont{Chaparral Pro}}
  {\setmainfont{TeX Gyre Pagella}}

\IfFontExistsTF{Josefin Sans}
  {\newfontfamily\PURHTitleFont{Josefin Sans}}
  {\newfontfamily\PURHTitleFont{TeX Gyre Heros}}

\IfFontExistsTF{Josefin Sans Thin}
  {\newfontfamily\PURHTitreFont{Josefin Sans Thin}}
  {\newfontfamily\PURHTitreFont{TeX Gyre Heros}}

\IfFontExistsTF{Latin Modern Mono}
  {\setmonofont{Latin Modern Mono}}
  {\setmonofont{TeX Gyre Cursor}}
```

Deux familles Josefin Sans distinctes coexistent, et c'est volontaire :

- **`\PURHTitleFont`** charge la famille Josefin Sans complète (toutes
  graisses NFSS : régulière, **Bold**, italique…). C'est elle qu'il faut
  utiliser partout où un `\bfseries` réel est requis.
- **`\PURHTitreFont`** charge uniquement **Josefin Sans Thin** comme famille
  indépendante (elle porte ses propres graisses Thin romain/italique, mais
  aucune graisse « Bold » véritable au sens NFSS — un `\bfseries` sur cette
  famille ne produirait rien de fiable). Elle ne sert plus, après ce
  chantier, qu'au titre courant (`\PURHHeaderFont`, voir §4).

**Piège à éviter sur un autre format** : ne jamais utiliser
`\PURHTitreFont\bfseries` en espérant un résultat gras — la police Thin
correspondante n'existe simplement pas dans cette famille NFSS. Utiliser
`\PURHTitleFont\bfseries` à la place.

## 2.2. Couleur du texte courant

```latex
\definecolor{PURHBodyBlack}{cmyk}{0,0,0,0.9}
\AtBeginDocument{\color{PURHBodyBlack}}
```

Le référentiel v0.6 (§12.1) constatait que « le texte courant du PDF
imprimeur correspond à un noir process à 90 % [K] » contre un noir plein
dans la sortie générée. Corrigé par une teinte CMJN explicite (et non un
gris RVB, qui n'a pas de sens en quadrichromie), appliquée globalement dès
le début du document.

## 2.3. Corps de texte

```latex
\renewcommand{\normalsize}{\fontsize{11pt}{13.5pt}\selectfont}
\normalsize
```

Fixé explicitement (11/13,5 pt) plutôt que de dépendre de la table de
tailles native de `\documentclass{book}`, qui donne un pas voisin mais pas
identique.

## 2.4. Graisse des titres — la correction centrale du chantier

**Constat commun à tous les niveaux de titraille** (parties, chapitres,
sections, sous-sections, sous-sous-sections, titre et sous-titre d'ouverture
de contribution) : le référentiel v0.6 prescrivait la famille **Thin**
(§2.5, §4.3, §5.3), mais la vérification humaine directe du PDF généré face
au PDF imprimeur montre que **tous ces niveaux sont noirs et gras** dans
l'imprimé réel — le rendu Thin, lui, produisait un texte maigre et grisâtre,
peu lisible. C'est cette observation directe qui a été suivie, pas le texte
du référentiel.

Le correctif technique est le même partout : remplacer
`\PURHTitreFont` (famille Thin seule) par `\PURHTitleFont\bfseries` (famille
complète + graisse Bold via NFSS).

## 2.5. Titre courant (running title) — traité à part, quatre vérifications (dont trois le même jour)

Le titre courant est le **seul niveau typographique qui n'a PAS reçu le
correctif Bold ci-dessus** : la couleur, pas la graisse, était le problème
réel ici, et il a fallu quatre allers-retours pour le comprendre.

1. **1ʳᵉ vérification** : gris jugé trop clair → tentative de passer de
   `\PURHTitreFont` (Thin) à `\PURHTitleFont` (famille standard) sans
   `\bfseries`. Sans effet suffisant.
2. **2ᵉ vérification** : ce résultat jugé trop noir et visuellement gras —
   le PDF imprimeur, lui, « n'a pas de graisse » à ce niveau. Retour à la
   famille Thin (`\PURHTitreFont`), avec un gris RVB explicite
   (`\color[gray]{0.25}`, valeur approximative) en remplacement.
3. **3ᵉ vérification** : ce gris encore jugé trop clair. Passage au même
   système que le fond d'en-tête de tableau et le texte courant — une teinte
   **CMJN noir X %** plutôt qu'un gris RVB — à **50 % noir**, valeur donnée
   explicitement par l'utilisateur (pas une estimation à recalibrer).
4. **4ᵉ vérification (2026-08-05)** : ce 50 % à nouveau jugé trop clair au
   regard du PDF imprimeur, où le titre courant est décrit comme
   « presque noir ». Remonté à **85 % noir**, sans changer de famille ni de
   graisse (toujours Thin — seule la teinte a de nouveau bougé, comme aux
   trois vérifications précédentes).

Valeur finale :

```latex
\newcommand{\PURHHeaderFont}{\PURHTitreFont\small\color[cmyk]{0,0,0,0.85}}
```

**Leçon méthodologique pour un autre format** : face à un écart de rendu
signalé plusieurs fois de suite sur le même élément, vérifier si graisse et
couleur sont bien traitées comme deux leviers indépendants avant de
re-changer de famille de police à chaque itération — c'est la confusion des
deux qui a coûté les deux premiers essais ici. Le quatrième essai confirme
aussi qu'une valeur « donnée explicitement par l'utilisateur » n'est pas
forcément définitive : revérifier contre le PDF imprimeur reste nécessaire
même après un réglage qui semblait tranché.

---

# 3. Titraille — valeurs exactes par niveau

| Niveau | Fonte | Graisse | Corps/interligne | Casse | Alignement |
|---|---|---|---|---|---|
| Partie (`\part`) | `\PURHTitleFont` | Bold | 16/19 pt | MAJUSCULES | centré |
| Chapitre/contribution (`\chapter`) | `\PURHTitleFont` | Bold | 16/19 pt | MAJUSCULES | `\raggedright` |
| Section (intertitre, `\section`) | `\PURHTitleFont` | Bold | 12/14 pt | MAJUSCULES | `\raggedright` |
| Sous-section (`\subsection`) | `\PURHTitleFont` | Bold | `\large` | bas de casse | `\raggedright` |
| Sous-sous-section (`\subsubsection`) | `\PURHTitleFont` | Bold | `\normalsize` | bas de casse | `\raggedright` |
| Titre d'ouverture de contribution | `\PURHTitleFont` | Bold | 16/19 pt | MAJUSCULES | centré, boîte 104 mm |
| Sous-titre d'ouverture de contribution | `\PURHTitleFont` | Bold italique | 12/14 pt | bas de casse | centré |

Note sur les sous-sections : le référentiel v0.6 §4.3 ne chiffrait que le
niveau « section » (section1) ; aucune taille n'est donc imposée par une
source externe pour section2/section3 — `\large`/`\normalsize` sont
conservés tels quels, seule la graisse a été alignée sur le reste de la
titraille. Un correctif antérieur au chantier avait délibérément retiré le
gras à ce niveau (au motif que `<div type="section2">` porte de vrais
sous-titres phrastiques, pas des libellés courts) ; la vérification directe
du 2026-08-04 est revenue sur ce choix.

```latex
\titleformat{\chapter}[display]
  {\PURHTitleFont\bfseries\fontsize{16pt}{19pt}\selectfont\raggedright}
  {\chaptertitlename~\thechapter}{10pt}{\MakeUppercase}

\titleformat{\part}[display]
  {\PURHTitleFont\bfseries\fontsize{16pt}{19pt}\selectfont\centering}
  {}{0pt}{\MakeUppercase}

\titleformat{\section}[block]
  {\PURHTitleFont\bfseries\fontsize{12pt}{14pt}\selectfont\raggedright}
  {}{0pt}{\MakeUppercase}

\titleformat{\subsection}[block]
  {\PURHTitleFont\bfseries\large\raggedright}{}{0pt}{}

\titleformat{\subsubsection}[block]
  {\PURHTitleFont\bfseries\normalsize\raggedright}{}{0pt}{}

\titlespacing*{\part}{0pt}{0pt}{30pt}
\titlespacing*{\chapter}{0pt}{20pt}{18pt}
\titlespacing*{\section}{0pt}{18pt}{10pt}
\titlespacing*{\subsection}{0pt}{14pt}{8pt}
\titlespacing*{\subsubsection}{0pt}{12pt}{6pt}
```

Vérification objective complémentaire à la lecture humaine : `pdffonts`
sur le PDF généré doit lister au moins une police portant « Bold »/« Bd » —
un `pdftotext` seul ne peut pas détecter la graisse (aucune notion de
graisse dans le texte extrait), donc ne suffit pas à valider ce correctif
(voir `tests/test_latei_titraille.py::test_part_and_contribution_titles_embed_a_bold_font`).

---

# 4. Titre et sous-titre de la page de titre (page de titre pleine, distincte du titre d'ouverture de contribution)

Ne pas confondre avec la titraille de contribution du §3 : la page de
titre du livre (§7 ci-dessous) a son propre jeu de tailles, plus grand,
défini par des macros séparées (`\PurhTitleMain`, `\PurhSubtitle`,
`\PurhContributors`, `\PurhPublisherMention`), toutes dans
`latei_preamble.py`. `\PurhTitleExtra` (mention finale, version antérieure
à la 2026-08-05) a été **retirée**, remplacée par `\PurhPublisherMention` —
voir §4.2.

```latex
\newcommand{\PurhTitleMain}[1]{%
  {\PURHTitleFont\bfseries\fontsize{22pt}{26pt}\selectfont\centering\MakeUppercase{#1}\par}
}

\newcommand{\PurhSubtitle}[1]{%
  \par\vspace{0.6\baselineskip}%
  \begin{center}
  \parbox{88mm}{\PURHTitleFont\bfseries\fontsize{15pt}{18pt}\selectfont\centering #1}
  \end{center}
  \vspace{0.4\baselineskip}%
}

\newcommand{\PurhContributors}[1]{%
  \par\vspace{0.5\baselineskip}%
  {\bfseries\fontsize{11pt}{13pt}\selectfont\centering #1\par}%
  \vspace{0.6\baselineskip}%
}

\newcommand{\PurhPublisherMention}[1]{%
  {\fontsize{14pt}{16pt}\selectfont\bfseries\MakeUppercase{#1}\par}%
}
```

- **Titre principal** : 22/26 pt, Bold, MAJUSCULES, centré. Corps choisi
  sans mesure millimétrique donnée par l'utilisateur : la seule contrainte
  exprimée était « nettement plus grand que le faux-titre » (12/14 pt) ; à
  recalibrer avec une vraie mesure si elle devient disponible pour un autre
  format.
- **Sous-titre** : 15/18 pt, Bold Italique **non** — Bold droit, bas de
  casse (pas de `\MakeUppercase`, à la différence du titre), sur deux lignes
  forcées par une boîte de 88 mm (voir §4.1 ci-dessous pour la méthode de
  calibrage) ; les numéros de siècle romains y sont en petites capitales
  depuis le 2026-08-05 (§4.3).
- **Responsabilité éditoriale** (« sous la direction de » + noms) : Chaparral
  (fonte principale, aucun changement de famille), Bold bas de casse,
  11/13 pt — plus petit que le sous-titre ; corrigible manuellement via
  `directors_override` depuis le 2026-08-05 (§4.4).
- **Mention finale** (éditeur) : depuis le 2026-08-05, toujours le nom
  complet PURH fixe, en majuscules grasses 14/16 pt, calée en bas de page
  (§4.2) — plus le sigle éventuellement abrégé du champ `<publisher>` XML.

## 4.1. Calibrage de la largeur de boîte du sous-titre (88 mm)

Objectif : reproduire exactement la coupure de ligne réelle du PDF
imprimeur pour le sous-titre de *Beautés vitales*, « Pour une approche
contemporaine de la beauté », qui casse en :

```
Pour une approche contemporaine
de la beauté
```

Méthode : simple `\parbox` de largeur fixe, laissant l'algorithme
Knuth-Plass de LaTeX faire la coupure — pas de `\\` inséré à la main. La
largeur a été resserrée itérativement (rendu → export PNG → lecture
visuelle) de 95 mm jusqu'à 88 mm, valeur à laquelle la coupure obtenue
correspond exactement à celle du PDF imprimeur.

**Reproductibilité pour un autre titre/format** : cette valeur (88 mm) est
calibrée sur **ce texte précis**, pas une constante universelle du profil de
page. Pour un autre ouvrage dirigé avec un sous-titre différent, revérifier
visuellement contre le PDF imprimeur réel et réajuster la largeur si
nécessaire — ne pas supposer que 88 mm convient à un autre sous-titre sans
vérification.

## 4.2. Mention finale : nom complet PURH, calée en bas de page (2026-08-05)

Vérification humaine directe sur le PDF généré de *Dissimuler pour mieux
régner* : le champ `<publisher>` du TEI/Métopes source y contient
littéralement le sigle abrégé `PURH`, jamais le nom complet — c'est ce
sigle qui apparaissait donc juste sous les éditeurs scientifiques.
Corrigé : la mention finale de la page de titre utilise désormais
**toujours** une constante fixe, jamais `metadata.publisher` :

```python
_PURH_FULL_NAME = "Presses universitaires de Rouen et du Havre"  # latei_driver.py

def _full_title_page(metadata):
    ...
    lines.append(r"\vspace*{\fill}")
    lines.append(rf"\PurhPublisherMention{{{_latex_text(_PURH_FULL_NAME)}}}")
    ...
```

`\vspace*{\fill}` (étoilé, jamais un `\vfill` nu) : même mécanisme et même
piège que pour le colophon (§7.4) — cette fois le risque de la glue
« absorbée en tête de page » ne s'applique pas puisque du contenu (titre,
sous-titre, responsabilité éditoriale) précède déjà cette ligne sur la même
page, mais l'étoile est conservée par cohérence et prudence.

`\PurhPublisherMention` : Chaparral (fonte ambiante, pas
`\PURHTitleFont`/Josefin — cette mention n'est pas un niveau de titraille),
majuscules grasses, **sur une seule ligne quelle que soit la longueur du
nom affiché** (précision du 2026-08-05) :

```latex
\newcommand{\PurhPublisherMention}[1]{%
  \noindent\resizebox{0.95\linewidth}{!}{\bfseries\MakeUppercase{#1}}\par
}
```

**Piège rencontré (2026-08-05)** : la première version fixait un corps
absolu (`\fontsize{14pt}{16pt}`). À cette taille, « PRESSES UNIVERSITAIRES
DE ROUEN ET DU HAVRE » (44 caractères) ne tenait pas sur une seule ligne à
la largeur d'empagement de ce profil (~105 mm) et retombait sur deux lignes
— bug réel constaté par vérification humaine directe du PDF généré, pas par
les tests automatisés (qui ne mesurent pas la largeur du rendu). Corrigé
avec `\resizebox{0.95\linewidth}{!}{...}` (déjà chargé via `graphicx`,
§préambule) : le contenu est d'abord emballé dans une boîte horizontale non
coupable (aucun retour à la ligne possible, contrairement à un simple
changement de `\fontsize`), puis mis à l'échelle pour occuper exactement
95 % de la largeur de la page — garantit à la fois la ligne unique et le
remplissage « une bonne partie de la largeur de la page » quel que soit le
nom affiché ou le profil, sans avoir à calculer un corps de police à la
main pour chaque cas.

## 4.3. Numéros de siècle en petites capitales (2026-08-05)

Vérification humaine directe sur *Dissimuler pour mieux régner* : le
sous-titre « […] en littérature (XVIIe-XIXe siècles) » affichait les
numéros de siècle en grandes capitales, identiques au reste du texte,
faute de tout balisage `<hi rend="small-caps">` autour d'eux dans le TEI
source (convention typographique française absente du balisage, pas un bug
de rendu). Corrigé par une transformation mécanique appliquée côté Python,
au texte déjà échappé du sous-titre :

```python
_ROMAN_CENTURY_NUMERALS = (
    "XXI", "XX", "XIX", "XVIII", "XVII", "XVI", "XV", "XIV", "XIII", "XII", "XI",
    "X", "IX", "VIII", "VII", "VI", "V", "IV", "III", "II", "I",
)  # du plus long au plus court : ordre requis pour que l'alternation regex matche XIX avant XI
_CENTURY_NUMERAL_RE = re.compile(r"\b(" + "|".join(_ROMAN_CENTURY_NUMERALS) + r")(e|er|re)?\b")

def _small_caps_century_numerals(escaped_text):
    return _CENTURY_NUMERAL_RE.sub(
        lambda m: rf"\textsc{{{m.group(1)}}}{m.group(2) or ''}", escaped_text
    )
```

Appliqué **uniquement** au sous-titre de la page de titre (`_full_title_page`,
`_small_caps_century_numerals(_latex_text(metadata.subtitle))`), pas comme
règle générale sur tout le corps de texte — portée volontairement étroite.
La liste de numéraux romains valides (I à XXI) évite les faux positifs sur
des mots ordinaires qui ressembleraient à un numéral (contrairement à un
motif regex générique du type `[IVXLCDM]+`) ; l'ordre du plus long au plus
court dans l'alternation garantit que "XIX" matche avant que "XI" soit
essayé en premier.

Doit être exécuté **après** l'échappement LaTeX (`_latex_text`), jamais
avant : la substitution injecte un `\textsc{...}` littéral, qui serait
lui-même cassé (le `\` échappé en `\textbackslash{}`) si `_latex_text`
s'exécutait après elle.

## 4.4. Correction manuelle des éditeurs scientifiques (`directors_override`, 2026-08-05)

Constaté sur *Dissimuler pour mieux régner* : le seul `<author role="pbd">`
du TEI/Métopes source y désigne en réalité la compositrice ("Anaïs
Lebreton"), pas les éditrices scientifiques de l'ouvrage ("sous la
direction de Floriane Daguisé et Florence Fix" attendu) — un défaut du
balisage source, pas de l'extraction (`role="pbd"` est le code MARC
"Publishing director", correctement lu par `latei_metadata.py`). Sans
marqueur fiable pour distinguer les deux rôles dans ce TEI, la correction
se fait par **saisie explicite**, jamais en devinant depuis le contenu —
même doctrine que `cover_designer`/`editorial_contact` (§7.4) : un nouveau
champ optionnel, vide par défaut, plombé de bout en bout comme eux
(`BuildConfig.directors_override` → GUI → `site_latei_pdf_export` →
`run_reversible_export_for_file`) :

```python
# reversible_integration.py
if directors_override:
    metadata.directors = [
        name.strip()
        for name in re.split(r"\s+et\s+|[,;]", directors_override)
        if name.strip()
    ]
```

Une chaîne " et "/`,`/`;`-séparée qui, si fournie, **remplace entièrement**
`metadata.directors` (donc la ligne « sous la direction de » du §7.3) — vide
(comportement par défaut), l'extraction TEI normale reste inchangée. Dans
le GUI, ce champ vit dans la même boîte de dialogue optionnelle que le
colophon (« Sous la direction de (correction) »), avec la même règle : une
valeur non fournie ne change rien au comportement existant.

---

# 5. Coupures de ligne du titre d'ouverture de contribution (104 mm)

`\PURHContributionTitleWidth` fixe la largeur du `\parbox` du titre affiché
en tête de chaque contribution (`\lateiContributionTitle`) :

```latex
\newcommand{\PURHContributionTitleWidth}{104mm}
```

Le référentiel v0.5/v0.6 (§7.3, « coupures éditoriales ») prévenait
explicitement qu'il ne fallait pas reconstruire ces coupures « par une
largeur de boîte arbitraire ». Une vérification empirique a montré que ce
n'est en fait pas nécessairement le cas :

- **Méthode** : 7 titres réels du PDF imprimeur de *Dissimuler pour mieux
  régner* ont été mesurés (longueurs environ 7, 9, 15, 27, 26, 51, 191
  caractères), et une largeur de boîte a été recherchée par approche
  itérative jusqu'à faire correspondre les coupures obtenues à celles du
  PDF imprimeur.
- **Résultat** : 104 mm calculé correspond de très près à 103,4 mm mesuré
  indépendamment par analyse de pixels sur le rendu réel, et à l'empagement
  du profil 155×230 (105 mm de largeur de texte). Ce n'est donc pas une
  coïncidence arbitraire : la largeur du bloc de titre suit visiblement la
  largeur d'empagement du corps de texte.
- **Vérification positive** : sur un titre de 4 lignes (« Les lieux de la
  conjuration : société secrète et hétérotopie dans la littérature
  romantique »), le nombre de lignes et la coupure obtenus avec cette
  largeur sont **identiques** au PDF imprimeur.
- **Limite documentée** : sur d'autres titres, la coupure diffère du PDF
  imprimeur d'un mot. Exemple : « Les espaces du secret à Clarens » casse en
  « LES ESPACES DU SECRET À » / « CLARENS » avec cette méthode, contre
  « LES ESPACES DU SECRET » / « À CLARENS » dans le PDF imprimeur. Écart
  probablement dû à une règle InDesign de conservation des mots courts
  (« à », « de »…) avec la ligne suivante, que l'algorithme Knuth-Plass de
  LaTeX ne reproduit pas nativement.

**Pour un autre format** : recommencer la même méthode empirique (mesurer
un échantillon de titres réels du PDF imprimeur cible, chercher la largeur
de boîte qui reproduit le plus grand nombre de coupures identiques,
documenter le taux de réussite et les cas résiduels) plutôt que de
réutiliser 104 mm tel quel — cette valeur est spécifique à l'empagement du
profil 155×230 et à ce corpus de titres.

---

# 6. Ouvertures de partie et de contribution

## 6.1. Pagestyle vide

Référentiel v0.6 §7.1/§7.2, P1 items 1 et 2 : « aucun en-tête ni folio » sur
la première page d'une partie ou d'une contribution.

```latex
% Rupture d'ouverture de contribution
\thispagestyle{empty}
% Rupture d'ouverture de partie
\thispagestyle{empty}
```

`\thispagestyle` (et non `\pagestyle`) : seule la première page bascule en
style vide, les pages suivantes de la même contribution/partie reprennent
le titre courant normalement.

## 6.2. Réinitialisation des notes de bas de page

Référentiel v0.6 §5/§17 : « notes remise à 1 par contribution ».

```latex
\setcounter{footnote}{0}
```

Exécuté à chaque rupture d'ouverture (front matter, chapitre/article,
back matter) — chaque ouverture redémarre sa propre numérotation plutôt que
de poursuivre celle de la contribution précédente sur tout le livre.

## 6.3. Auteur et affiliation masqués sur l'ouverture, réversibilité préservée

Référentiel v0.6 §7.2/§17, P1 item 3 : « auteur et affiliation non
imprimés » sur l'ouverture de contribution, mais « le profil doit
distinguer conservation des métadonnées et visibilité sur la page ».

```latex
% purh_layout_profiles.py
show_contribution_author: bool  # False sur les deux profils actuels

% latei_preamble.py
\newif\iflateiShowContributionAuthor
\lateiShowContributionAuthorfalse  % ou …true selon profile.show_contribution_author
```

Le contenu réversible (`\teiP[rend={author-aut}]…`,
`\teiP[rend={authority\_affiliation}]…`) reste **inchangé** dans le corps
LaTEI, quel que soit l'état du drapeau : seul l'affichage PDF bascule.
Vérifié par `tests/test_latei_opening_templates.py::
test_contribution_body_stays_reversible_even_when_author_is_hidden`.

---

# 7. Liminaires et fin d'ouvrage

## 7.1. Séquence complète (référentiel v0.6 §8.1)

```
\lateiEnsureContinuousArabicPagination
\PURHBlankPage      % page blanche technique
\PURHBlankPage      % page blanche technique
\PURHFalseTitle{…}  % faux-titre
\PURHCreditsPage{…} % colophon
\PURHTitlePage{…}   % page de titre
\PURHBlankPage      % page blanche technique
```

Construite uniquement depuis les métadonnées déjà extraites
(`LateiMetadata`), jamais depuis le corps LaTEI réversible. La pagination
arabe continue est initialisée **avant** cette séquence, pour que ces six
pages soient comptées (sans folio visible, toutes en pagestyle empty) avant
que le contenu principal ne devienne la première page numérotée visible.

Aucune de ces pages n'utilise `\begin{titlepage}…\end{titlepage}` : ce mode
de compatibilité LaTeX 2.09 remet parfois `\c@page` à 1, ce qui casserait la
continuité de la pagination — chaque page liminaire utilise
`\clearpage…\thispagestyle{empty}…\clearpage` à la place.

## 7.2. Faux-titre

```latex
\newcommand{\PURHFalseTitle}[1]{%
  \clearpage
  \thispagestyle{empty}%
  \begin{center}
  \vspace*{0.25\textheight}
  {\PURHTitleFont\bfseries\fontsize{12pt}{14pt}\selectfont\MakeUppercase{#1}\par}
  \end{center}
  \clearpage
}
```

Position remontée (0,35 → 0,25 `\textheight` — approximatif, « un peu plus
haut », aucune mesure millimétrique donnée par l'utilisateur) et graisse
repassée en Bold capitales, même corps que les titres de section (12/14
pt). Le référentiel v0.6 ne donnait aucune cible chiffrée pour ce niveau
précis ; seule la vérification humaine directe fait foi ici.

## 7.3. Page de titre

```latex
\newcommand{\PURHTitlePage}[1]{%
  \clearpage
  \thispagestyle{empty}%
  \begin{center}
  \vspace*{0.25\textheight}
  #1
  \end{center}
  \clearpage
}
```

**Même hauteur de départ que le faux-titre** (0,25 `\textheight`, valeur
partagée volontairement) — seul le corps du texte change entre les deux
pages, pas sa position verticale. Contenu (assemblé par
`_full_title_page()` dans `latei_driver.py`) :

```python
lines = [rf"\PurhTitleMain{{{title}}}"]
if subtitle:
    subtitle = _small_caps_century_numerals(_latex_text(subtitle))  # §4.3
    lines.append(rf"\PurhSubtitle{{{subtitle}}}")
if responsibility:          # "sous la direction de" + noms, ou juste les noms
    lines.append(r"\vspace{2\baselineskip}")
    lines.append(rf"\PurhContributors{{{responsibility}}}")
# Mention finale : toujours le nom complet PURH fixe, jamais metadata.publisher
# (parfois le sigle abrégé "PURH" côté TEI source) — voir §4.2.
lines.append(r"\vspace*{\fill}")
lines.append(rf"\PurhPublisherMention{{{_PURH_FULL_NAME}}}")
```

### Logique de la responsabilité éditoriale (« sous la direction de »)

```python
def _title_page_responsibility_lines(metadata):
    if metadata.directors:
        names = " et ".join(metadata.directors)
        return "sous la direction de\\\\" + names
    if metadata.authors:
        return " et ".join(metadata.authors)
    return ""
```

« sous la direction de » sur sa propre ligne, puis les noms sur la
suivante — deux lignes explicites (`\\` inséré côté Python, pas dans la
macro) — s'applique **uniquement** aux volumes dirigés (exemple concret
donné par l'utilisateur : *Beautés vitales*, dirigé par deux personnes). À
défaut de directeurs déclarés, seuls les noms des auteurs sont affichés,
sans ce préfixe.

## 7.4. Colophon (page de crédits)

```latex
\newcommand{\PURHCreditsPage}[1]{%
  \clearpage
  \thispagestyle{empty}%
  \begin{center}
  \vspace*{\fill}
  \fontsize{10pt}{11.5pt}\selectfont
  #1
  \end{center}
  \clearpage
}
```

**Point le plus délicat du chantier** : `\vspace*{\fill}`, pas
`\vspace*{0.3\textheight}` ni un `\vfill` non étoilé.

- Le colophon doit être **calé en bas de page**, pas centré verticalement
  (deuxième vérification humaine directe — la première tentative avec une
  hauteur fixe approximative ne le calait pas correctement selon la
  longueur variable du contenu).
- Un `\vfill` **non étoilé** placé en tout début de page (rien au-dessus)
  est **silencieusement absorbé** par l'algorithme de coupure de page de
  TeX — bug réel constaté par compilation : le contenu restait centré
  près du haut malgré le `\vfill`, sans aucun message d'erreur. Ce risque
  est renforcé par `\raggedbottom`, actif dans tout ce document (référentiel
  §2, autorise justement les pages à ne pas s'étirer jusqu'à `\textheight`).
- `\vspace*` (étoilé) protège la glue même en tête de page — c'est ce qui
  résout le problème.

Corps fixé explicitement à 10 pt (`\fontsize{10pt}{11.5pt}`, pas `\small`) :
`\small` ne correspond pas nécessairement à 10 pt exactement, cela dépend de
l'échelle de tailles du `\documentclass` choisi — une deuxième vérification
humaine directe a demandé une taille absolue plutôt que relative.

Interlignage resserré à `0.1\baselineskip`/`0.5\baselineskip` entre lignes
et blocs (vérification humaine directe : `0.4`/`1\baselineskip` rendait un
colophon trop aéré) :

```python
def _credits_page(metadata):
    blocks = [b for b in (_colophon_production_lines(metadata),
                           _colophon_institutional_lines(metadata)) if b]
    block_bodies = [
        r"\vspace{0.1\baselineskip}".join(f"{line}\\par" for line in block)
        for block in blocks
    ]
    body = r"\vspace{0.5\baselineskip}".join(block_bodies)
    return rf"\PURHCreditsPage{{{body}}}"
```

### Contenu du colophon

Deux blocs, dans cet ordre : production (facultatif) puis mentions
institutionnelles (fixes + métadonnées du livre).

```python
_PURH_FULL_NAME = "Presses universitaires de Rouen et du Havre"
_PURH_ADDRESS_LINE = "2 place Émile Blondel – 76821 Mont-Saint-Aignan Cedex"
_PURH_URL = "http://purh.univ-rouen.fr"

def _colophon_production_lines(metadata):
    # cover_designer / editorial_contact : sans équivalent dans la source
    # TEI/Métopes, renseignés par l'éditrice via la boîte de dialogue
    # optionnelle du GUI. Omis tant qu'ils ne sont pas fournis — jamais un
    # "[Prénom Nom]" littéral imprimé faute de valeur réelle.
    lines = []
    if metadata.cover_designer:
        lines.append(f"Couverture et mise en pages : {metadata.cover_designer}")
    if metadata.editorial_contact:
        lines.append(f"Suivi éditorial : {metadata.editorial_contact}")
    return lines

def _colophon_institutional_lines(metadata):
    # Vérification humaine directe, 2026-08-05 : la ligne de copyright doit
    # TOUJOURS figurer, pas seulement quand une année de publication est
    # connue (comportement précédent, corrigé ici) — seule l'année, elle,
    # reste une métadonnée du livre, ajoutée à la suite quand connue.
    lines = []
    year_suffix = f", {metadata.publication_year}" if metadata.publication_year else ""
    lines.append(f"© {_PURH_FULL_NAME}{year_suffix}.")
    lines.append(_PURH_ADDRESS_LINE)          # toujours présent, fixe
    lines.append(rf"\url{{{_PURH_URL}}}")      # toujours présent, fixe
    if metadata.preferred_isbn:
        # "ISBN : " devant le numéro (vérification humaine directe, 2026-08-05).
        lines.append(f"ISBN : {metadata.preferred_isbn}")
    return lines
```

Règle de fabrication commune à **tout** le colophon (et confirmée cette
session comme correcte à conserver) : **une métadonnée absente donne une
ligne omise, jamais une valeur générique ou un espace réservé littéral**.
En particulier :

- l'adresse postale, l'URL et désormais la ligne de copyright PURH sont des
  constantes fixes pour tout livre PURH (dictées telles quelles par
  l'utilisateur), donc jamais lues depuis `LateiMetadata` — ne pas les faire
  dériver d'une métadonnée par livre pour un autre format ;
- la ligne de copyright s'affiche **toujours**, avec ou sans année connue
  (seul le suffixe `, {année}` est conditionnel), et reste dans tous les cas
  la ligne juste **au-dessus** de l'adresse, y compris quand les lignes de
  production (couverture/suivi éditorial) sont absentes — c'est le
  regroupement en deux blocs distincts (`production` puis `institutionnel`),
  chacun réduit à ses lignes effectivement présentes, qui garantit cet ordre
  sans jamais laisser un bloc vide créer un blanc superflu.

---

# 8. Signature de fin d'article

Référentiel v0.6 §8/§17, vérification humaine directe du 2026-08-04 :
« les articles sont signés à la fin », calés à droite — un emplacement
**distinct** de l'ouverture de contribution (où auteur/affiliation restent
masqués par défaut, §6.3).

## 8.1. Mécanisme : capture globale, émission différée

Le problème technique : au moment où l'ouverture de la contribution est
rendue (`\lateiContributionAuthor`, `\lateiContributionAffiliation`),
l'auteur est déjà connu, mais l'endroit où il doit être **affiché** (la fin
du corps de la contribution) n'a pas encore été atteint. La solution capture
la valeur dans des macros globales au moment où elle est connue, et
l'émet plus tard via une macro appelée après le corps.

```latex
\newcommand{\lateiSignatureEmpty}{}
\newcommand{\lateiSignatureAuthor}{}
\newcommand{\lateiSignatureAffiliation}{}

\newcommand{\lateiResetContributionSignature}{%
  \global\let\lateiSignatureAuthor\lateiSignatureEmpty
  \global\let\lateiSignatureAffiliation\lateiSignatureEmpty
}

\newcommand{\lateiContributionAuthor}[1]{%
  \global\def\lateiSignatureAuthor{#1}%
  \iflateiShowContributionAuthor
    {\normalsize\bfseries\centering #1\par}\vspace{0.3\baselineskip}%
  \fi
}
\newcommand{\lateiContributionAffiliation}[1]{%
  \global\def\lateiSignatureAffiliation{#1}%
  \iflateiShowContributionAuthor
    {\small\centering #1\par}\vspace{0.3\baselineskip}%
  \fi
}

\newcommand{\lateiRenderContributionSignature}{%
  \ifx\lateiSignatureAuthor\lateiSignatureEmpty\else
    \par\vspace{0.8\baselineskip}%
    {\fontsize{10pt}{12pt}\selectfont\raggedleft\lateiSignatureAuthor\par}%
    \ifx\lateiSignatureAffiliation\lateiSignatureEmpty\else
      {\fontsize{10pt}{12pt}\selectfont\raggedleft\lateiSignatureAffiliation\par}%
    \fi
  \fi
}
```

Câblage (`\lateiRenderFrontGroup`/`\lateiRenderChapterGroup`) :

```latex
\lateiResetContributionSignature   % vide la signature de la contribution précédente
\latei_add_contribution_opening_break:
#2                                  % le corps ; c'est ici que \lateiContributionAuthor
                                     % capture la valeur, si elle est présente
\latei_finish_contribution_toc_entry:
\lateiRenderContributionSignature  % émission différée, après le corps
```

**Point critique, non optionnel** : `\lateiResetContributionSignature` doit
être appelé **avant** chaque contribution, y compris celles qui n'ont pas de
signature — sinon la signature d'une contribution signée « fuit » vers la
suivante qui n'en a pas. C'est un `\global\let`, pas un `\let` local, car
chaque groupe s'exécute dans son propre groupe TeX (argument `+b` de
`xparse`) et un `\let` local serait annulé à la fermeture de ce groupe avant
même que la signature ait pu être lue plus loin.

## 8.2. Mise en forme

Chaparral Pro (fonte principale, aucun changement de famille), **sans
graisse**, corps légèrement plus petit que le corps du texte (11 → 10 pt),
calé à droite (`\raggedleft`). Le prénom en bas de casse et le nom en
petites capitales viennent déjà tels quels du balisage source
(`<p rend="author-aut">Prénom <hi rend="small-caps">Nom</hi></p>`, déjà
routé vers `\teiHi[rend={small-caps}]` ailleurs dans la chaîne) : le contenu
n'a besoin d'aucune reformulation, seulement de ce nouvel habillage.

Ligne suivante (toujours calée à droite) : l'affiliation, `\small`, sans
graisse.

## 8.3. Piège rencontré : `\@empty` hors `\makeatletter`

`\@empty` (le sentinelle vide standard du noyau LaTeX) exige la catégorie de
code 11 pour le caractère `@`, active seulement entre `\makeatletter` et
`\makeatother`. `latei_macros.tex` n'ouvre pas ce bloc à cet endroit du
fichier : `\@empty` y aurait été tokenisé comme le caractère isolé `\@`
suivi du texte ordinaire « empty », qui se serait imprimé littéralement —
bug réel constaté par compilation (« empty empty » visible sur la page).
Corrigé en définissant un sentinelle propre, sans `@` :
`\lateiSignatureEmpty`, comparé par `\ifx` (comparaison de macro, pas de
chaîne).

---

# 9. Table des matières

Référentiel v0.6 §9.1, vérification humaine directe du 2026-08-04.

## 9.1. Profondeur

```latex
\setcounter{secnumdepth}{0}
\setcounter{tocdepth}{0}
```

`tocdepth=2` incluait à tort les intertitres (`\section`=1, `\subsection`=2)
dans la TDM, la gonflant à trois pages au lieu de deux. Cible confirmée :
seuls le niveau des parties (`\part`, niveau -1) et celui des ouvertures de
contribution/front matter (`\addcontentsline{toc}{chapter}{…}`, niveau 0)
doivent y figurer.

## 9.2. Entrées de contribution

Cible : « titre de la communication sans graisse, bas de casse, Chaparral,
calé à gauche, série de points puis numéro de ligne », prénom et nom de
l'auteur en gras **bas de casse** sur la ligne suivante, en retrait — les
points de suite et le numéro de page devant rester au niveau du **titre**,
jamais de l'auteur (vérification humaine directe, 2026-08-05 : deux pièges
rencontrés en corrigeant ce point sont détaillés au §11).

```latex
\titlecontents{chapter}
  [0pt]
  {}
  {}
  {}
  {\titlerule*[0.5pc]{.}\contentspage}
```

Chaparral Pro reste la fonte ambiante (aucune famille à sélectionner
explicitement dans ce bloc) — le réglage antérieur `\PURHTitleFont\bfseries`
a été retiré ici précisément, puisque ce niveau doit être sans graisse,
contrairement à tous les autres niveaux de titraille corrigés en Bold dans
ce même chantier (§2.4). Ne pas confondre les deux : le titre affiché en
tête de contribution (§3, `\lateiContributionTitle`) et son entrée de TDM
(ce bloc) ont des règles de graisse opposées.

`\hfill` a été remplacé par le même filet pointillé que `\section`
(`\titlerule*[0.5pc]{.}\contentspage`) pour la série de points de
conduite + numéro de page. **Ce 4e argument n'a plus bougé depuis** : une
tentative du 2026-08-05 de le vider et de déplacer le filet dans le texte
de l'entrée elle-même (pour le garantir sur la ligne du titre) a cassé les
signets PDF automatiques du paquet `bookmark` — voir §11 pour le détail du
bug et la solution finalement retenue (une ligne de TDM séparée pour
l'auteur, ci-dessous).

Espacement entre entrées : « pas de saut de ligne entre les références sauf
changement de section » — un `\addvspace{8pt}` inconditionnel antérieur a
été retiré ; l'espacement avant une nouvelle partie vient désormais
uniquement de `\titlecontents{part}` (§9.3), pas de ce bloc.

### Ligne d'auteur séparée, bas de casse (mécanisme définitif, stabilisé le 2026-08-05)

```latex
\newcommand{\lateiTocAuthorLine}[1]{%
  \par\noindent\hspace*{1em}%
  {\bfseries\renewcommand{\textsc}[1]{##1}#1\par}%
}
\newcommand{\lateiContributionAuthor}[1]{%
  \global\def\lateiSignatureAuthor{#1}%
  \iflateiShowContributionAuthor
    {\normalsize\bfseries\centering #1\par}
    \vspace{0.3\baselineskip}
  \fi
}
```

Le nom d'auteur est écrit comme une entrée de TDM **entièrement séparée**,
via `\addtocontents` plutôt que `\addcontentsline` — raison détaillée au
§11 (compatibilité avec les signets PDF automatiques du paquet `bookmark`,
qui n'observe que `\addcontentsline`/`\contentsline`) — et référence
directement `\lateiSignatureAuthor` telle quelle, **sans capture
intermédiaire**.

Le nom de famille de l'auteur est en petites capitales (`\textsc{Nom}`,
via `<hi rend="small-caps">` routé par `\teiHi`) dans la signature de fin
d'article (§8), mais doit rester bas de casse dans la TDM (vérification
humaine directe, 2026-08-05). Neutraliser `\textsc` **au bon moment** s'est
révélé plus délicat que prévu — deux tentatives ont échoué avant la
solution ci-dessus, détaillées au §11 :

1. Une première tentative redéfinissait `\textsc` directement dans
   l'argument de `\addcontentsline` — `\addcontentsline` écrit son
   argument via un `\edef`, qui ne peut pas *exécuter* les primitives que
   `\renewcommand` appelle en interne, seulement les recopier telles
   quelles : le fichier `.toc` en ressortait corrompu.
2. Une deuxième tentative capturait une copie "texte brut" **en amont**, au
   moment de `\lateiContributionAuthor`, via `\protected@xdef` + un
   `\textsc` local — plausible en apparence, mais `\teiHi` (comme toute
   commande définie par `\NewDocumentCommand` de xparse) est `\protected`
   au sens eTeX, donc **jamais développée** par un `\edef`/`\xdef` quel que
   soit l'état de `\textsc` au même moment : la copie obtenue contenait
   encore `\teiHi[rend={small-caps}]{Nom}` tel quel, et le rendu restait en
   petites capitales dans le PDF malgré la capture (bug réel constaté :
   invisible dans les tests automatisés, qui ne voient que le texte extrait
   par `pdftotext`, identique avec ou sans petites capitales — seule une
   inspection visuelle du PDF l'a révélé).

La solution retenue place le `\renewcommand{\textsc}` **dans le corps de
`\lateiTocAuthorLine` elle-même** : ce bloc ne s'exécute pas dans un
argument `\edef`, mais normalement, au moment où `\tableofcontents`
`\input` le fichier `.toc` et exécute réellement `\lateiTocAuthorLine{...}`
— un contexte où `\teiHi` peut s'exécuter pour de vrai (pas seulement se
développer) et appeler ce `\textsc` local, correctement redéfini à ce
moment précis. Fonctionne car la redéfinition et son usage sont dans le
**même acte d'exécution**, pas séparés par un `\edef` intermédiaire.

### Émission différée de l'entrée de TDM

Le titre de la contribution est connu dès le début (option
`data-page-title`), mais l'auteur — nécessaire pour composer la ligne
séparée en gras dessous — n'est capturé qu'au moment où
`\lateiContributionAuthor` s'exécute, **à l'intérieur** de `#2`, donc
**après** que la rupture d'ouverture (qui déclenchait auparavant
`\addcontentsline` immédiatement) s'est produite. Solution : stocker le
titre en attente, écrire l'entrée réelle seulement après `#2` :

```latex
\tl_new:N \g_latei_pending_toc_title_tl

\cs_new_protected:Npn \latei_add_contribution_opening_break: {
  \tl_if_empty:NF \l_latei_option_page_title_tl {
    \cleardoublepage
    \thispagestyle{empty}
    \phantomsection
    \tl_gset_eq:NN \g_latei_pending_toc_title_tl \l_latei_option_page_title_tl
    \exp_args:NV \latei_markboth_recto:n \l_latei_option_page_title_tl
    \setcounter{footnote}{0}
  }
}

\cs_new_protected:Npn \latei_finish_contribution_toc_entry: {
  \tl_if_empty:NF \g_latei_pending_toc_title_tl {
    % Titre seul ici : filet pointillé + numéro de page restent gérés par
    % le 4e argument de \titlecontents{chapter} ci-dessus, comme avant —
    % l'auteur, lui, est écrit séparément, jamais concaténé dans ce texte
    % (voir \lateiTocAuthorLine plus haut).
    \addcontentsline{toc}{chapter}{\tl_use:N \g_latei_pending_toc_title_tl}
    \ifx\lateiSignatureAuthor\lateiSignatureEmpty\else
      \addtocontents{toc}{\protect\lateiTocAuthorLine{\lateiSignatureAuthor}}
    \fi
    \tl_gclear:N \g_latei_pending_toc_title_tl
  }
}
```

Appelé après `#2` dans `\lateiRenderFrontGroup`/`\lateiRenderChapterGroup`,
au même moment que `\lateiRenderContributionSignature` (§8.1) — les deux
fonctionnalités (signature de fin d'article, auteur en TDM) partagent
exactement le même mécanisme de capture/émission différée, pour la même
raison structurelle.

## 9.3. Entrées de partie

Le référentiel dit « titres de section », mais désigne en réalité ici le
niveau `\part` de ce document (les véritables intertitres/sections sont
exclus de la TDM depuis `tocdepth=0`, §9.1). Josefin Sans **Bold,
capitales** (vérification humaine directe, 2026-08-05), un peu plus grand
que le corps (12 pt contre 11 pt), centré, ligne vide avant et après, sans
numéro de page (une partie est un intitulé structurant la liste, pas une
entrée cherchable en soi) :

```latex
\titlecontents{part}
  [0pt]
  {\addvspace{1\baselineskip}\PURHTitleFont\bfseries\fontsize{12pt}{14pt}\selectfont\centering}
  {}
  {}
  {}
  [\addvspace{1\baselineskip}]
```

**Piège rencontré (2026-08-05)** : une première tentative ajoutait
`\scshape` à ce bloc, en croyant qu'il fonctionnerait comme `\textsc`
ailleurs dans ce document (§8.2) — puisque `\PURHTitleFont` est chargé via
fontspec (`\newfontfamily`), qui relie normalement les formes NFSS aux
fonctionnalités OpenType de la fonte quand elle les propose. Mais
**Josefin Sans n'a pas de véritables petites capitales OpenType** :
confirmé par compilation isolée d'un exemple minimal, dont le journal
LaTeX rapporte explicitement `Font shape .../b/sc undefined`, avec
substitution silencieuse par la forme normale — aucune erreur bloquante,
donc invisible sans consulter le journal (et invisible aussi dans les
tests automatisés : `pdftotext` ne détecte pas les graisses/formes de
police). Résultat concret : le texte restait affiché en bas de casse dans
le PDF, comme si `\scshape` n'avait jamais été écrit.

**Solution retenue** : à défaut de petites capitales réelles, `\MakeUppercase`
appliqué **à la source du texte**, dans `\lateiRenderHead`
(`latei_macros.tex`) — pas ici, dans `\titlecontents{part}`, qui ne reçoit
jamais le texte de l'entrée en argument direct (ses hooks ne sont que des
changements de police appliqués *avant* que titlesec/titletoc n'insère le
texte, pas des enveloppes autour de lui) :

```latex
\IfStrEq{\lateiHeadContext}{part}{\part*{\MakeUppercase{#1}}\lateiMarkBothVerso{#1}}{%
```

`\part*` réutilise ce même texte, désormais déjà en capitales, à la fois
pour le titre affiché sur sa propre page ET pour son entrée de TDM
automatique (voir ci-dessous) — appliquer `\MakeUppercase` une seconde fois
via `\titleformat{\part}` (qui l'applique déjà à l'affichage sur la page)
n'a aucun effet indésirable (majuscule d'une majuscule = la même
majuscule). Seul `\lateiMarkBothVerso{#1}` continue d'utiliser le texte
original, non uppercase : le titre courant (verso) doit rester dans sa
casse d'origine (référentiel, "Titres courants").

**Limite assumée** : ce n'est PAS de la véritable petite capitale
typographique (qui réduit la hauteur des lettres à l'origine bas de casse
tout en gardant les majuscules d'origine à taille pleine) — seulement des
capitales pleines, à un corps réduit (12 pt) par rapport au titre affiché
sur sa propre page (16 pt), qui les distingue visuellement des autres
niveaux de la TDM sans reproduire l'effet exact. À reconsidérer si un
autre format charge une fonte de titraille disposant de vraies petites
capitales OpenType.

`\part*` (jamais `\part{}` numéroté) ajoute déjà lui-même son entrée de TDM
via le shape `[display]` de `\titleformat{\part}` (vérifié empiriquement) :
ajouter en plus un `\addcontentsline{toc}{part}{…}` manuel produirait un
doublon, pas un renfort.

---

# 10. Tableaux — fond des lignes d'en-tête

Référentiel §11.3 : « fond foncé noir 30 % » sur les lignes d'en-tête/de
label.

## 10.1. Deux contraintes en tension

1. `\rowcolor{…}` (package `colortbl`, chargé via `\usepackage[table]{xcolor}`)
   doit être le **premier token** de la ligne d'un tableau — comme
   `\multicolumn`, il ne peut pas être émis depuis l'intérieur d'un `\if…`
   conditionnel dans la macro `\teiRow` sans provoquer une erreur
   « Misplaced \noalign ».
2. Le corps LaTEI réversible ne doit **jamais** contenir de LaTeX brut
   (doctrine de réversibilité, `latex_writer.py`/`latex_reader.py`) —
   `\rowcolor{black!30}` ne peut donc pas apparaître tel quel dans le corps
   `\teiRow{…}` généré.

## 10.2. Solution retenue

`\rowcolor{black!30}` est écrit **littéralement et sans enrobage**, par
`_write_row()` côté Python (`latex_writer.py`), **immédiatement avant**
l'appel `\teiRow{…}` — jamais à l'intérieur de la macro elle-même :

```python
if node.get_attr("role") in ("label", "header"):
    # \rowcolor{black!30} littéral, émis avant \teiRow — jamais imbriqué
    # dans la macro (contrainte "premier token de la ligne").
    lines.append(r"\rowcolor{black!30}")
lines.append(rf"\teiRow{{...}}")
```

Le lecteur réversible (`latex_reader.py`) doit reconnaître ce
`\rowcolor{black!30}` généré et le **neutraliser sans erreur** — ni
l'accepter silencieusement comme du contenu réversible normal, ni le
rejeter avec une erreur « Unknown macro or escape » (ce qui s'est produit
avant ce correctif : le lecteur strict n'avait aucune tolérance pour du
LaTeX généré arbitraire). Solution : une catégorie dédiée de macros
reconnues-et-écartées, distincte du reste du vocabulaire réversible :

```python
LAYOUT_UNVALIDATED_STANDALONE_MACROS = {"rowcolor"}
```

consommée par une méthode dédiée `_consume_layout_unvalidated_standalone()`,
enregistrée dans `_controlled_macro_at_pos()` et `parse_nodes()`.

**Principe généralisable pour d'autres artefacts de présentation générés
par le writer Python** (pas seulement `\rowcolor`) : si un futur format
nécessite un autre effet visuel qui, par contrainte LaTeX, doit être émis en
dehors d'une macro contrôlée, suivre le même patron — écrire le littéral
côté writer, ajouter son nom à une liste d'allow-list dédiée côté reader,
jamais l'un sans l'autre (sinon soit une erreur de compilation, soit une
erreur de relecture réversible).

---

# 11. Bugs rencontrés et méthode de résolution (récapitulatif transversal)

Cette section rassemble, pour référence rapide, les pièges LaTeX rencontrés
ce chantier qui ne sont pas spécifiques à un seul élément visuel et qui
peuvent resurgir sur un autre format.

| Bug | Symptôme | Cause | Correctif |
|---|---|---|---|
| `\@empty` hors `\makeatletter` | « empty empty » imprimé littéralement | `@` n'a la catégorie de code 11 qu'entre `\makeatletter`/`\makeatother` | Sentinelle propre sans `@` (`\lateiSignatureEmpty`), comparaison par `\ifx` |
| `\vfill` non étoilé en tête de page | Contenu resté centré en haut malgré le `\vfill` | Absorbé silencieusement par l'algorithme de coupure de page de TeX, surtout sous `\raggedbottom` | `\vspace*{\fill}` (étoilé) |
| `\noindent` avant `\@thefnmark` | Retrait négatif de 1ʳᵉ ligne des notes totalement annulé | Le mécanisme dépend de l'indentation naturelle de LaTeX (`\parindent` négatif) ; `\noindent` la supprime | Retirer le `\noindent` |
| Redéfinition de `\@makefntext` silencieusement écrasée | Le correctif de mise en forme des notes n'avait aucun effet | `hyperref`/`bookmark` redéfinissent `\@makefntext` eux-mêmes via leur propre `\AtBeginDocument`, qui l'emporte sur un `\renewcommand` de préambule quel que soit l'ordre textuel | Différer aussi la redéfinition via `\AtBeginDocument`, placée textuellement après leurs `\usepackage` |
| `\footnotelayout` (footmisc) sans effet | La taille des notes ne changeait jamais | La redéfinition complète de `\@makefntext` ci-dessus n'appelle plus `\footnotelayout` | Intégrer `\fontsize{…}\selectfont` directement dans le `\@makefntext` personnalisé |
| `\footnoterule` par défaut de `book.cls` | Deux « défauts » du référentiel (épaisseur/largeur du filet) en fait jamais custom | Jamais touché avant ce chantier — ses valeurs par défaut (0,4 pt / 0,4×`\columnwidth` ≈ 42 mm) correspondaient exactement aux deux constats du référentiel | Redéfinir explicitement (0,25 pt / 72 pt) |
| `\rowcolor` dans un conditionnel imbriqué | « Misplaced \noalign » | Même contrainte de premier-token que `\multicolumn` | Émission littérale côté Python, hors macro (§10) |
| Lecteur réversible rejetant `\rowcolor` généré | « Unknown macro or escape » | Aucune tolérance pour du LaTeX généré arbitraire | Catégorie `LAYOUT_UNVALIDATED_STANDALONE_MACROS` dédiée (§10) |
| `font=…` de `caption` avec un nom non déclaré | Erreur de compilation | `font=<nom>` exige `\DeclareCaptionFont`, pas un simple `\newcommand` | `\DeclareCaptionFont{PURHTableCaptionFont}{…}` |
| `\renewcommand{\textsc}[1]{#1}` placé DANS un argument `\addcontentsline` (2026-08-05, tentative 1) | Fichier `.toc` corrompu : erreurs `\textsc has an extra }` ou `You can't use a prefix...` ailleurs dans le document, bien après le point réellement fautif | `\addcontentsline` écrit son argument via `\protected@write`, qui `\edef`-développe le texte ; un `\edef` ne peut pas EXÉCUTER les primitives non désarmables (`\def`, `\global`…) que `\renewcommand` appelle en interne — il les recopie telles quelles au lieu de les exécuter | Abandonné — voir la ligne `\protected@xdef` ci-dessous, elle-même abandonnée à son tour ; solution finale au §9.2 |
| `\makeatletter` placé DANS le corps d'une macro `\newcommand` (2026-08-05) | `You can't use a prefix with the character @` sur un `\protected@xdef` pourtant précédé d'un `\makeatletter` dans le même bloc | Le corps d'un `\newcommand`/`\def` est **tokenisé une fois pour toutes à la lecture du fichier** (à `\input`), pas à chaque invocation ultérieure — un `\makeatletter` exécuté seulement à l'usage arrive trop tard, la catégorie de code de `@` était déjà figée à 12 (« autre ») quand `\protected@xdef` a été lu | Placer `\makeatletter`/`\makeatother` AUTOUR de toute la définition de la macro, au niveau du fichier, pas à l'intérieur de son corps |
| `\contentspage`/`\\` insérés dans le texte d'une entrée `\addcontentsline` déjà utilisée par `bookmark` (2026-08-05) | `Package hyperref Warning: Token not allowed in a PDF string`, puis `Use of \ttl@row@i doesn't match its definition` (désynchronisation de titlesec) | Le paquet `bookmark` construit automatiquement les signets PDF depuis CE MÊME texte d'entrée ; il ne tolère pas des macros de mise en forme (filet, retour à la ligne) qui ne produisent pas une chaîne PDF valide | Ne jamais enrichir le texte transmis à `\addcontentsline` au-delà d'un titre simple ; toute information additionnelle (ex. auteur) doit être écrite comme un `\addtocontents` séparé, jamais capturé par `bookmark` |
| `\protected@xdef` + `\textsc` local pour capturer un "texte brut" (2026-08-05, tentative 2) | Aucune erreur de compilation — mais le rendu restait en petites capitales dans le PDF malgré la capture ; bug invisible dans les tests automatisés (`pdftotext` ne distingue pas `\textsc{Nom}` de `Nom`, seul un rendu visuel le révèle) | `\teiHi` (comme toute commande définie par `\NewDocumentCommand` de xparse) est `\protected` au sens eTeX : un `\edef`/`\xdef`/`\protected@xdef` ne la développe donc JAMAIS, quel que soit l'état de `\textsc` au même moment — elle est recopiée telle quelle, non exécutée | Ne pas essayer de "capturer" un texte contenant des commandes protégées via `\edef` ; neutraliser la commande responsable (`\textsc`) au moment de l'EXÉCUTION réelle du texte, pas de son expansion — voir §9.2 pour le mécanisme final (`\renewcommand` dans le corps de `\lateiTocAuthorLine`) |
| `\scshape` sur une fonte sans petites capitales OpenType (2026-08-05) | Aucune erreur de compilation, aucun avertissement visible sans consulter le journal complet — le texte reste silencieusement affiché dans sa forme normale (ici, bas de casse) | Josefin Sans n'a pas de forme NFSS "sc" ; LaTeX répond par une substitution de police silencieuse (`Font shape .../b/sc undefined`, journal uniquement, pas de warning console) | Vérifier la disponibilité réelle d'une fonctionnalité de police avant de s'y fier (ici, par une compilation isolée minimale) ; à défaut, approximer avec `\MakeUppercase` à corps réduit plutôt que d'utiliser une commande qui échoue silencieusement — voir §9.3 |
| Corps de police fixe pour un texte de longueur variable (2026-08-05) | La mention finale de la page de titre retombait sur deux lignes selon la longueur du nom affiché | `\fontsize{14pt}{16pt}` fixe ne garantit rien sur la largeur réelle du texte rendu, qui dépend du nombre de caractères | `\resizebox{0.95\linewidth}{!}{...}` : emballe le texte dans une boîte non coupable puis la met à l'échelle pour occuper une largeur cible fixe, garantissant la ligne unique quel que soit le texte — voir §4.2 |

**Leçon transversale la plus générale** : plusieurs de ces bugs
(`\@makefntext`, `\footnotelayout`) viennent du même phénomène — un paquet
tiers (`hyperref`, `bookmark`, `footmisc`) redéfinit lui-même, via son
propre hook `\AtBeginDocument`, une commande que le préambule PURH tente
aussi de redéfinir. L'ordre d'exécution des hooks `\AtBeginDocument` suit
l'ordre de **chargement des paquets**, pas l'ordre textuel des
`\renewcommand`. Si un futur format rencontre un comportement similaire
(un réglage qui ne « prend » pas malgré un `\renewcommand` syntaxiquement
correct), soupçonner en premier un paquet chargé plus tard qui écrase la
même commande via son propre hook différé.

**Deuxième leçon transversale (2026-08-05)** : deux catégories bien
distinctes de « moment d'exécution » piègent régulièrement ce genre de
correctifs, et les trois bugs ajoutés cette date en sont chacun un exemple :

1. **Tokenisation vs exécution.** Le corps d'une macro (`\newcommand`,
   `\def`) est tokenisé une seule fois, à la lecture du fichier — les
   catégories de code (comme celle de `@`) actives à CE moment-là sont
   celles qui comptent, pas celles actives quand la macro s'exécute plus
   tard. Un `\makeatletter` à l'intérieur du corps arrive toujours trop
   tard pour ce corps lui-même.
2. **Écriture différée (`\addcontentsline`/`\addtocontents`) vs exécution
   immédiate.** Le texte passé à ces commandes est écrit dans un fichier
   auxiliaire via `\protected@write` (un `\edef`), pour être **réexécuté
   plus tard** quand ce fichier est `\input`. Un `\edef` ne peut développer
   que des tokens développables : une macro à effets de bord comme
   `\renewcommand` ne s'y « exécute » pas vraiment, elle y laisse une trace
   partiellement développée et potentiellement corrompue. Et ce texte est
   aussi lu par d'autres mécanismes indépendants (ici, les signets PDF de
   `bookmark`), qui imposent leurs propres contraintes (une chaîne PDF
   valide) sur le même contenu.

Face à un comportement qui ne « prend » pas ou casse silencieusement des
dizaines de lignes plus loin dans le document, se demander d'abord *à quel
moment* le code en cause s'exécute réellement, plutôt que de supposer qu'il
s'exécute là où il est textuellement écrit.

**Troisième leçon transversale (2026-08-05)** : les deux bugs les plus
difficiles à diagnostiquer de ce chantier (`\protected@xdef` face à
`\teiHi`, `\scshape` face à Josefin Sans) partagent un même trait — **aucun
message d'erreur**. LaTeX substitue silencieusement (police de repli pour
une forme NFSS absente) ou recopie silencieusement (une commande protégée
non développée par un `\edef`) plutôt que d'échouer bruyamment. Les deux
étaient invisibles dans les tests automatisés existants, qui vérifient soit
la présence de certaines commandes dans le code source, soit le texte
extrait par `pdftotext` — un canal qui ne voit ni les graisses, ni les
formes de police, ni les petites capitales. Dans les deux cas, c'est
seulement le rendu visuel du PDF généré, comparé au PDF imprimeur, qui a
révélé le défaut. Pour un prochain format : quand une propriété
typographique fine (graisse, casse, forme) est en jeu et que les tests
automatisés passent malgré tout, ne pas conclure trop vite à une réussite
— une vérification visuelle directe reste nécessaire, en particulier après
avoir introduit une nouvelle fonctionnalité de police (`\scshape`,
`\textsc`, une fonctionnalité OpenType) sur une fonte qui n'a jamais été
vérifiée pour cette fonctionnalité précise.

---

# 12. Rappel — ce qui est propre au profil de page vs commun à tous les formats

Distinction essentielle pour appliquer ce travail à 195×255 ou 180×240 :

**Propre au profil (`purh_layout_profiles.py`, à redéfinir par format)** :
- dimensions papier, marges (haut/bas/intérieure/extérieure)
- corps et interligne du texte courant et des notes (actuellement identiques
  sur les deux profils existants : 11/13,5 pt corps, 8,5/10,2 pt notes — pas
  garanti qu'un futur format partage ces valeurs, à vérifier contre son
  propre maître InDesign)
- `show_contribution_author`

**Commun à tous les profils (préambule et macros, indépendant du format)** :
- toutes les graisses/casse de titraille (§2.4, §3)
- la couleur du texte courant et du titre courant (§2.2, §2.5)
- le mécanisme de signature de fin d'article et d'entrée de TDM avec auteur
  (§8, §9)
- le colophon calé en bas de page, la structure de la page de titre (§7)
- les corrections de bugs LaTeX du §11

**Ce qui doit être recalibré empiriquement pour chaque nouveau format,
même si le mécanisme reste identique** :
- la largeur de boîte des titres à coupure de ligne forcée (§4.1, §5) —
  ces valeurs (88 mm, 104 mm) sont dérivées de l'empagement du profil
  155×230 et d'un corpus de titres précis, pas transposables telles quelles ;
- le décalage vertical du bandeau de titre courant
  (`\addtolength{\topmargin}{-3.1mm}` / `\addtolength{\headsep}{3.1mm}`,
  référentiel §6.2) — spécifique à un écart de rendu observé sur CE profil,
  à revérifier sur le PDF généré du nouveau format avant de réutiliser
  3,1 mm ;
- la position verticale du bloc de titre (`0.25\textheight` pour faux-titre
  et page de titre) et l'espace entre le bloc de titre d'ouverture de
  contribution et le début du corps (`\PURHContributionBodyGap`, 105 pt,
  estimé à 5,5 lignes de titre — voir `latei_macros.tex`) : ces deux valeurs
  sont explicitement documentées dans le code comme des estimations
  visuelles, pas des mesures millimétriques du référentiel — donc à
  recalibrer par vérification humaine directe sur le nouveau format, pas à
  copier.

---

# 13. Limitation connue et volontairement non implémentée

## 13.1. Liste des auteurs séparée par une ligne blanche (fin d'ouvrage)

Demande initiale : dans un chapitre de fin d'ouvrage listant les auteurs
(ex. « Présentation des auteurs »), chaque auteur devrait être séparé du
précédent par une ligne blanche.

**Non implémenté**, après vérification sur la source réelle
(`Ch21_presentation_auteurs.xml`) : ce chapitre n'a, dans la structure TEI,
**aucun marqueur générique** qui le distingue d'un chapitre de contenu
ordinaire (pas de `type` ou `rend` dédié identifiable indépendamment du
titre du chapitre). Une implémentation générale (applicable à tout livre,
pas seulement à celui-ci) exigerait soit :

- de détecter ce cas par le **texte du titre du chapitre** (ex. « Auteurs »,
  « Présentation des auteurs »…) — rejeté, car cela reviendrait à coder en
  dur une valeur propre à un livre particulier dans une macro générale, ce
  qui contredit la doctrine de ce chantier (ne jamais hardcoder de contenu
  spécifique à un livre dans le code générique) ;
- ou d'introduire une nouvelle convention d'encodage source (un attribut ou
  un `rend` dédié dans le TEI/Métopes en amont) pour marquer explicitement
  ce type de liste — **décision qui appartient à l'équipe éditoriale/
  encodage**, pas à ce chantier de mise en page.

**Pour reprendre ce point** : si une convention d'encodage est validée en
amont (par exemple `<div type="authorList">` ou un `rend` dédié sur chaque
entrée), le mécanisme de rendu lui-même serait trivial à ajouter (un
`\vspace` entre entrées consécutives du même type, sur le modèle des
macros déjà en place dans `latei_macros.tex`) — la difficulté n'est
jamais technique, elle est dans l'absence de marqueur source.

---

# 14. Journal des commits (branche `dissimuler-parite-v0.6`, depuis la v0.6)

Dix-huit commits, du plus ancien au plus récent (`main..HEAD` sur cette
branche à la date de ce document) :

1. `8db3364` — Corrige les deux défauts signalés : sous-sections en gras,
   notes avec point
2. TDM : exclut les intertitres, style vide sur toutes ses pages
3. Remonte le bandeau de titre courant de 3,1 mm (référentiel v0.6 §6.2)
4. P2 microtypographie : notes, bibliographie, tableaux, couleur du texte
5. `352b91b` — Titre courant à 50 % K, faux-titre remonté/gras, colophon
   complet, GUI
6. `c979fbe` — Colophon en bas de page, page de titre redessinée, signature
   de fin d'article, TDM avec auteur sous chaque entrée
7. `19c81bd` — Rédige la v0.7 du référentiel PURH (mise en page/mise en
   forme, md + docx)
8. `aafa4a1` — Corrige TDM (points de suite, casse auteur/section), titre
   courant, colophon et page de titre : les six correctifs détaillés dans
   cette version du référentiel (§2.5, §4.2-§4.4, §7.4, §9.2-§9.3, §11)
9. `3da636f` — Met à jour le référentiel v0.7 avec les six correctifs du
   2026-08-05
10. `d2080e4` — Corrige TDM (auteurs/parties), préfixe ISBN et mention
    finale sur une ligne : quatre correctifs supplémentaires, découverts
    en recompilant réellement le monofile régénéré de *Dissimuler pour
    mieux régner* plutôt qu'en se fiant aux seuls tests automatisés (§9.2,
    §9.3, §7.4, §4.2, §11)

(liste condensée aux commits repères disposant d'un message significatif
dans `git log` ; le détail technique de chaque changement est repris par
sujet dans les sections 1 à 13 ci-dessus, qui constituent la référence
faisant foi — ce journal n'est qu'un index de traçabilité vers l'historique
Git).

Pour retrouver l'état exact d'un fichier à un commit donné :

```bash
git log --oneline main..dissimuler-parite-v0.6
git show <hash> -- purh_site/latei_preamble.py
```

---

# 15. Suite recommandée

1. Pour un nouveau format (195×255 ou 180×240) : créer un nouveau
   `PurhLayoutProfile` dans `purh_layout_profiles.py` avec les dimensions
   propres à ce format (voir §12 pour ce qui doit être mesuré vs réutilisé),
   puis suivre la méthode de calibrage empirique du §4.1/§5 pour les
   largeurs de boîte à coupure de ligne forcée, contre un corpus réel de
   titres de ce format s'il devient disponible.
2. Reprendre le point du §13.1 (liste d'auteurs) si/quand une convention
   d'encodage source dédiée est validée par l'équipe éditoriale.
3. Faire tourner la suite de tests complète
   (`pytest -m "not full_book"` puis, ponctuellement, la suite complète
   avec `full_book`) avant tout nouveau travail sur cette base — elle
   couvre déjà l'ensemble des points ci-dessus (782 tests passants au
   dernier relevé de ce chantier) et sert de garde-fou contre toute
   régression involontaire sur les valeurs documentées ici.
