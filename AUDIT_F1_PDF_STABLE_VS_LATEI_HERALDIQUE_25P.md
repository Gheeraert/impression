# Audit F1 — PDF stable vs PDF LaTEI  
## Héraldique et papauté II — 25 premières pages utiles

**Date :** 2026-06-23  
**Branche :** integrate-reversible-core  
**PDFs audités :**
- Stable : `.audit_f1/stable/book.pdf` (1 345 582 o, 351 pages) — chaîne `PdfBuilder`
- LaTEI  : `.audit_f1/latei/heraldique_ii.book.normalized.latei_mono.pdf` (1 214 030 o, 355 pages) — monofile LaTEI

**Périmètre :** pages 1–30 (extractées via `pdftotext -layout`) couvrant couverture, remerciements, table des abréviations, introduction (Loskoutoff), chapitre 1 (Doulkaridou-Ramantani) et début chapitre 2 (Loskoutoff).

**Contrainte :** audit pur — aucun fichier de production modifié.

---

## 1. Synthèse des écarts

| # | Catégorie | Gravité | Stable | LaTEI | Cause identifiée |
|---|-----------|---------|--------|-------|------------------|
| E1 | Attribution d'auteur | **BLOQUANT** | Présente (bloc centré) | **Absente** | `data-page-authors` ignoré par `\latei_extract_options:n` |
| E2 | Numérotation liminaire | Éditorial majeur | Arabes continus | Romains (ii–viii) | `\lateiEnsureFrontMatter` → `\frontmatter` |
| E3 | En-tête verso | Éditorial majeur | Titre de l'ouvrage | Titre du chapitre | `\fancyhead[LO,RE]` écrase `[RE]` du préambule |
| E4 | Têtes courantes débordantes | Éditorial notable | Tronquées à "…" | Deux lignes | Titre long non abrégé dans la carte des titres |
| E5 | Figures : image de remplacement | Bénin | Centré, espacé | Boîte fbox compacte | Style `\latei_figure_fallback:` vs stable |

---

## 2. Écart E1 — Attribution d'auteur complètement absente (BLOQUANT)

### Observation

**Stable** — Introduction (page 3) :
```
Introduction

   Yvan Loskoutoff

   Ce deuxième volume d'Héraldique et papauté...
```

**LaTEI** — Introduction (page ii) :
```
Introduction

   Ce deuxième volume d'Héraldique et papauté...
```

**Stable** — Chapitre 1 (page 11) :
```
Aspects ludiques dans l'appareil héraldique des manuscrits de Léon X
(1513-1521)

   Elli Doulkaridou-Ramantani

   À l'occasion de ce deuxième volet...
```

**LaTEI** — Chapitre 1 (démarrage) :
```
Aspects ludiques dans l'appareil héraldique des manuscrits de Léon X
(1513-1521)

   À l'occasion de ce deuxième volet...
```

Même constat sur les 13 chapitres de l'ouvrage (12 articles + 1 introduction).

### Cause

Dans le LaTeX réversible (`.reversible.tex`), chaque groupe-chapitre stocke l'attribut `data-page-authors` :

```latex
\begin{teiElement}[name={group},type={introduction},
  data-page-title={Introduction},
  data-page-authors={Yvan Loskoutoff},   ← porteur de l'information
  data-include-href={Ch01_Introduction.xml},xmlid={introduction-001}]
```

La macro `\latei_extract_options:n` dans `latei_macros.tex` (lignes 148–157) définit les clés connues :

```latex
\keys_define:nn { latei / options }
  {
    type .tl_set:N = \l_latei_option_type_tl,
    data-page-title .tl_set:N = \l_latei_option_page_title_tl,
    target .tl_set:N = ...
    url .tl_set:N = ...
    n .tl_set:N = ...
    rend .tl_set:N = ...
    unknown .code:n = {},   ← data-page-authors tombe ici et est silencieusement ignoré
  }
```

`data-page-authors` n'est pas déclaré → `unknown .code:n = {}` → silencieusement ignoré. Aucune macro ne rend le nom après le titre du chapitre.

### Correction proposée (passe F2)

Dans `latei_macros.tex` :
1. Ajouter `data-page-authors .tl_set:N = \l_latei_option_page_authors_tl` dans `\keys_define`.
2. Ajouter une nouvelle commande `\latei_render_page_authors:` qui insère un bloc centré si `\l_latei_option_page_authors_tl` n'est pas vide.
3. L'appeler dans `\lateiRenderFrontGroup` et `\lateiRenderChapterGroup` après l'ajout du chapitre.

---

## 3. Écart E2 — Numérotation de pages du liminaire (Éditorial majeur)

### Observation

| Section | Stable | LaTEI |
|---------|--------|-------|
| Couverture | page 1 (arabe) | page 1 (arabe) |
| Remerciements | non numéroté visible | non numéroté visible |
| Table des abréviations | non numéroté visible | non numéroté visible |
| Introduction p. 1 | **4** (arabe) | **ii** (romain) |
| Introduction p. fin | **9** (arabe) | **vii** (romain) |
| Chapitre 1 p. 1 | **11** (arabe, continuation) | **3** (arabe, remise à zéro) |

Dans le stable, la numérotation est continue en arabes depuis le début. Dans le LaTEI, le liminaire (tout ce qui précède les chapitres numérotés) utilise des chiffres romains en minuscule, puis la numérotation arabe repart à 1 au chapitre 1.

### Cause

Dans `latei_macros.tex` (lignes 66–84), `\lateiRenderFrontGroup` appelle `\lateiEnsureFrontMatter` → `\frontmatter` (classe `book` standard LaTeX). Le `\frontmatter` active automatiquement la numérotation romaine et le `\mainmatter` appelé par `\lateiRenderChapterGroup` repart à zéro en arabes. C'est un comportement standard de la classe `book`.

La chaîne stable (`PdfBuilder`) n'utilise pas ce mécanisme : elle produit une numérotation arabe continue depuis le début, conformément à la convention éditoriale PURH.

### Correction proposée (passe F2)

Supprimer les appels à `\frontmatter` / `\mainmatter` / `\backmatter` dans `latei_macros.tex`, ou les conditionner à un drapeau explicitement activable, et configurer la numérotation arabe continue dès le début.

---

## 4. Écart E3 — En-tête verso : titre de l'ouvrage absent (Éditorial majeur)

### Observation

**Stable** (page 4, verso) :
```
4  Héraldique et papauté. Moyen Âge-Temps modernes. II
```
Page verso : numéro à gauche, **titre de l'ouvrage** à droite.

**LaTEI** (page ii, verso) :
```
ii  Introduction
```
Page verso : numéro à gauche, **titre du chapitre courant** à droite.

Le titre de l'ouvrage n'apparaît dans aucune en-tête du PDF LaTEI.

### Cause

Le préambule LaTEI (`latei_preamble.py` lignes 182–185) définit correctement les quatre zones :

```latex
\fancyhead[LE]{\PURHHeaderFont\thepage}                    % verso : numéro
\fancyhead[RE]{\PURHHeaderFont\nouppercase{\PURHBookTitle}} % verso : TITRE OUVRAGE ✓
\fancyhead[LO]{\PURHHeaderFont\nouppercase{\leftmark}}     % recto : titre chapitre
\fancyhead[RO]{\PURHHeaderFont\thepage}                    % recto : numéro
```

Mais `latei_macros.tex` (lignes 17–18) **écrase** la zone `[RE]` :

```latex
\fancyhead[LO,RE]{\PURHHeaderFont\nouppercase{\lateiCurrentRunningTitle}}
```

Cette commande redéfinit simultanément `[LO]` (recto gauche, normal) **et** `[RE]` (verso droit), écrasant la définition `\PURHBookTitle` du préambule. Résultat : les deux côtés affichent le titre courant du chapitre, et le titre de l'ouvrage disparaît.

### Correction proposée (passe F2)

Dans `latei_macros.tex`, remplacer :
```latex
\fancyhead[LO,RE]{\PURHHeaderFont\nouppercase{\lateiCurrentRunningTitle}}
```
par :
```latex
\fancyhead[LO]{\PURHHeaderFont\nouppercase{\lateiCurrentRunningTitle}}
```
(laisser `[RE]` tel que défini dans le préambule, avec `\PURHBookTitle`).

---

## 5. Écart E4 — Têtes courantes en deux lignes (Éditorial notable)

### Observation

**Stable** (recto, chapitre 1) :
```
Aspects ludiques dans l'appareil héraldique...  13
```
Titre tronqué sur une ligne.

**LaTEI** (recto, chapitre 1) :
```
Aspects ludiques dans l'appareil héraldique des manuscrits de
Léon X (1513-1521)  17
```
Titre complet, débordant sur deux lignes — la zone d'en-tête est agrandie et décale tout le contenu de la page.

Idem chapitre 2 :

**Stable** : `L'héraldique de Jules III Ciocchi del Monte (1550-1555)...  29`  
**LaTEI** : `L'héraldique de Jules III Ciocchi del Monte (1550-1555) dans\nl'ornement pour le livre  21`

### Cause

La carte des titres courants (`*_running_titles_map.tex`) déclare les versions abrégées via `\lateiDeclareRunningTitle`. Lorsqu'aucune version abrégée n'est trouvée, `\latei_markboth:n` utilise le titre complet (branche `\tl_gset:Nn \g_latei_current_running_title_tl { #1 }`, lignes 121–123 de `latei_macros.tex`). Les titres complets sont trop longs pour la hauteur d'en-tête fixée à `headheight=14pt`.

Cette situation survient quand `latei_running_titles.py` génère des titres abrégés encore trop longs, ou n'en génère pas pour certains chapitres.

### Correction proposée (passe F2)

Réviser `latei_running_titles.py` pour garantir que tous les titres abrégés tiennent sur une seule ligne à `headheight=14pt` (approximativement ≤ 60 caractères pour la police courante). Ajouter un test de régression sur la longueur maximale.

---

## 6. Écart E5 — Image de remplacement (Bénin)

### Observation

Quand les images source sont absentes, les deux chaînes produisent un placeholder :

**Stable** :
```
                         Image absente ou non fournie
```
Texte centré, espacé, sur fond blanc.

**LaTEI** :
```
                          Imageabsenteounonfournie
```
Même texte (les espaces sont fusionnés par `pdftotext` lors de l'extraction depuis une `\fbox`) dans un cadre visible.

### Cause

Différence de style pur : la chaîne stable produit un texte centré sans encadrement ; la chaîne LaTEI utilise `\fbox{\parbox{...}{\centering\footnotesize Image absente...}}` (`latei_macros.tex` ligne 223). Les espaces collés dans l'extraction sont un artefact `pdftotext`, le PDF réel affiche le texte correctement espacé.

Cet écart est purement visuel et n'affecte pas la lisibilité éditoriale.

---

## 7. Points non évaluables depuis pdftotext

Les éléments suivants ne peuvent pas être vérifiés depuis la sortie texte brute :

- **Italiques** (`\textit`, `\teiForeign`, `\teiTitle`) — macros définies, présumées fonctionnelles
- **Petites capitales** (`\textsc`, `\teiHi[rend={small-caps}]`) — macros définies, présumées fonctionnelles
- **Microtypographie** — `\usepackage{microtype}` présent dans les deux chaînes ; césures et espacement inter-mots à vérifier visuellement
- **Polices** — LaTEI utilise Chaparral Pro / Josefin Sans (avec repli TeX Gyre) identiques à la chaîne stable ; à confirmer visuellement si la police installée est celle de production

---

## 8. Différence de pagination totale

| Métrique | Stable | LaTEI |
|----------|--------|-------|
| Pages totales | 351 | 355 |
| Écart | — | +4 pages |

Les 4 pages supplémentaires dans le LaTEI s'expliquent par :
- Les têtes courantes débordantes (E4) qui élargissent la zone d'en-tête, réduisant la zone texte et poussant du contenu sur des pages supplémentaires
- La numérotation romaine du liminaire (E2) crée un comptage séparé mais n'ajoute pas de pages physiques

---

## 9. Verdict et feuille de route

### Verdict

Le PDF LaTEI est **techniquement compilable et lisible**, mais présente **3 écarts éditoriaux bloquants ou majeurs** qui empêchent toute utilisation en production :

1. L'absence des 14 attributions d'auteur (E1) est un écart **bloquant** pour la publication.
2. La numérotation romaine du liminaire (E2) est contraire à la convention éditoriale PURH.
3. La disparition du titre de l'ouvrage en en-tête verso (E3) est contraire aux règles typographiques de la collection.

L'écart E4 (têtes courantes en deux lignes) est sévère mais secondaire par rapport à E1–E3.

### Passes proposées

| Passe | Périmètre | Priorité |
|-------|-----------|----------|
| **F2** | Corriger E1, E3, E4 dans `latei_macros.tex` | Haute |
| **F3** | Corriger E2 (pagination liminaire arabe) dans `latei_macros.tex` | Haute |
| **F4** | Améliorer `latei_running_titles.py` (longueur garantie ≤ 60 chars) | Moyenne |
| **F5** | Vérification visuelle des italiques, petites capitales et microtype | Basse |

---

*Rapport généré dans la branche `integrate-reversible-core`.*  
*Aucun fichier de production n'a été modifié au cours de cet audit.*
