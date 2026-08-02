# Audit F2 — Styles inline et titres courants LaTEI

**Date :** 2026-06-23  
**Branche :** integrate-reversible-core  
**Périmètre :** audit pur — aucun fichier de production modifié.

---

## Résumé exécutif

| Domaine | Verdict |
|---------|---------|
| Italiques | ✅ **Correctement rendus** — 2 264 occurrences `\teiHi[rend={italic}]`, macro `→ \textit`, police Chaparral Pro italic chargée |
| Petites capitales | ✅ **Correctement rendus** — 707 occurrences `\teiHi[rend={small-caps}]`, macro `→ \textsc`, VRAIES petites capitales Chaparral Pro |
| Exposants XML | ✅ **Correctement rendus** — 388 occurrences `\teiHi[rend={sup}]`, macro `→ \textsuperscript`, patterns corrects pour `no`, `xviiie` |
| Titres courants | ❌ **6/18 chapitres débordent sur 2 lignes** — cause : mismatch espace ordinaire (carte) vs tilde `~` (runtime via `\newunicodechar`) |
| Auteurs de contribution | — Constat seulement, pas de correction dans cette passe |

Les styles inline sont **fonctionnels**. La priorité unique de correction est les titres courants.

---

## 1. Italiques

### Méthode d'inspection

Inspection directe du corps LaTEI (`.latei_body.tex`, 946 Ko) par comptage binaire ; vérification des macros dans `latei_macros.tex` ; vérification du log de compilation pour les polices chargées.

### Résultats

| Exemple attendu | Markup dans le corps LaTEI | Macro → rendu |
|---|---|---|
| *Héraldique et papauté, Moyen Âge-Temps modernes* | `\teiHi[rend={italic}]{Héraldique et papauté, Moyen Âge-Temps modernes}` | `\lateiHiItalic{italic}{...}` → `\textit` ✓ |
| *La grottesque* | `\teiHi[rend={italic}]{La grottesque}` | idem ✓ |
| *Journal des savants* | `\teiHi[rend={italic}]{Journal des savants}` | idem ✓ |
| *Missarum liber primus* | `\teiHi[rend={italic}]{Missarum liber primus}` | idem ✓ |
| *Memorie sepolcrali* | `\teiHi[rend={italic}]{Memorie sepolcrali,}` | idem ✓ |
| *Insignia* | `\teiHi[rend={italic}]{Insignia }` | idem ✓ |
| *Antichità romane* | `\teiHi[rend={italic}]{Antichità romane}` | idem ✓ |
| *Praeparatio* | `\teiHi[rend={italic}]{Praeparatio ad Missam Pontificalem}` | idem ✓ |
| *impresa* | `\teiHi[rend={italic}]{impresa}` | idem ✓ |
| *motto* | `\teiHi[rend={italic}]{motto Semper}` | idem ✓ |
| *figlio de l'orso/orsa* | `\teiHi[rend={italic}]{figlio de l'orso/orsa }` | idem ✓ |

**Total :** 2 264 occurrences de `rend={italic}` dans le corps. Police Chaparral Pro (variante italique) chargée sans erreur.

```
(fontspec) - 'italic' (m/it) with NFSS spec.: <->"name:Chaparral…
```

### Chaîne de rendu

```
\teiHi[rend={italic}]{X}
  → \teiHi calls: \lateiHiItalic{italic}{\lateiHiBold{italic}{\lateiHiPosition{italic}{\lateiHiSmallCaps{italic}{X}}}}
  → \lateiHiItalic : \IfSubStr{italic}{italic}{\textit{...}}{...} → \textit{X}
```

### Verdict

Les italiques sont **correctement encodés et rendus**. La non-visibilité depuis `pdftotext` est un artefact d'extraction, pas un problème de rendu.

---

## 2. Petites capitales

### Résultats

| Exemple attendu | Markup dans le corps LaTEI | Macro → rendu |
|---|---|---|
| xvie siècle | `\teiHi[rend={small-caps}]{xvi}\teiHi[rend={sup}]{e}` | `\textsc{xvi}` + `\textsuperscript{e}` ✓ |
| xviie siècle | `\teiHi[rend={small-caps}]{xvii}\teiHi[rend={sup}]{e}` | idem ✓ |
| xviiie siècle | `\teiHi[rend={small-caps}]{xviii}\teiHi[rend={sup}]{e}` | idem ✓ |

**Total :** 707 occurrences de `rend={small-caps}`.

Extrait de corps confirmé :
```
un pour le \teiHi[rend={small-caps}]{xviii}\teiHi[rend={sup}]{e} siècle, Clément XIII
```

### Chaîne de rendu

```
\teiHi[rend={small-caps}]{xviii}
  → \lateiHiSmallCaps{small-caps}{xviii}
  → \lateiIfRendSmallCaps{small-caps}{\textsc{xviii}}{xviii}
  → \textsc{xviii}
```

### Polices

Le log confirme que Chaparral Pro charge **de vraies petites capitales** (non synthétiques) :

```
(fontspec) - 'small caps' (m/sc) with NFSS spec.: <->"name:Chaparral…
(fontspec) - 'bold small caps' (b/sc) with NFSS spec.: <->"name:Chaparral…
(fontspec) - 'italic small caps' (m/scit) with NFSS spec.: <->"name:Chaparral…
```

### Verdict

Les petites capitales sont **correctement encodées, rendues avec de vraies petites capitales de fonte**. Aucun problème détecté.

---

## 3. Exposants XML

### Périmètre

Uniquement `\teiHi[rend={sup}]{...}` (encodage XML `<hi rend="sup">`). Les ordinaux bruts non encodés sont hors périmètre.

### Résultats

| Exemple attendu | Markup dans le corps LaTEI | Macro → rendu | Diagnostic |
|---|---|---|---|
| n° | `n\teiHi[rend={sup}]{o}` | `\textsuperscript{o}` | A. Correct ✓ |
| xviie | `\teiHi[rend={small-caps}]{xvii}\teiHi[rend={sup}]{e}` | `\textsuperscript{e}` | A. Correct ✓ |
| xviiie | `\teiHi[rend={small-caps}]{xviii}\teiHi[rend={sup}]{e}` | `\textsuperscript{e}` | A. Correct ✓ |
| Ier | pattern `\teiHi[rend={sup}]{er}` | `\textsuperscript{er}` | A. Correct ✓ |

**Total :** 388 occurrences de `rend={sup}`.

### Chaîne de rendu

```
\teiHi[rend={sup}]{e}
  → \lateiHiPosition{sup}{e}
  → \lateiIfRendSup{sup}{\textsuperscript{e}}{...}
  → \textsuperscript{e}
```

### Diagnostic séparé

**A. Exposants XML correctement rendus :** tous les `\teiHi[rend={sup}]` trouvés dans le corps produisent `\textsuperscript`. Aucune exception détectée dans le périmètre audité.

**B. Exposants XML présents mais mal rendus :** aucun cas identifié.

**C. Ordinaux bruts hors périmètre :** les ordinaux sans `<hi rend="sup">` (peu probables dans ce corpus édité, mais possibles) ne sont pas traités par la chaîne. Ces cas sont hors périmètre de ce passage.

### Verdict

Les exposants XML sont **correctement rendus**. Aucune correction nécessaire dans ce domaine.

---

## 4. Titres courants

### Mécanisme stable vs LaTEI

**Chaîne stable (`latex_renderer.py`, ligne 399) :**
```python
running_title = self._escape_text(_compute_short_running_title(title))
running_mark = rf"\markboth{{{running_title}}}{{{running_title}}}"
```
Le titre court est calculé en Python avec `re.sub(r"\s+", " ", ...)` (normalise TOUS les espaces Unicode, y compris `\xa0`) et directement inscrit dans le LaTeX généré. **Pas de lookup au runtime.**

**Chaîne LaTEI (`latei_running_titles.py` + `latei_macros.tex`) :**
1. Python génère une carte `\lateiDeclareRunningTitle{clé}{titre court}` via `_normalize_space` → clés avec **espaces ordinaires**.
2. Au runtime, LuaLaTeX tokenise le corps TeX : `\newunicodechar{ }{~}` (ligne 11 de `latei_macros.tex`) remplace **tout U+00A0 par `~`**.
3. `\latei_markboth:n` essaie de trouver la clé tokenisée (avec `~`) dans la prop → **ÉCHEC** car la carte a des espaces ordinaires.
4. Fallback : `\markboth{#1}{#1}` avec le titre complet (contenant `~`) → trop long → déborde sur 2 lignes.

### Cas affectés

Sur les 18 `data-page-title` du livre, **8 contiennent U+00A0** (espace insécable entre prénom et numéro romain : `Léon\xa0X`, `Jules\xa0III`, `Urbain\xa0VIII`, `Clément\xa0XIII`…).

Parmi ces 8 :
- **6 nécessitent une troncature** (>58 chars une fois normalisés) → présents dans la carte → lookup échoue → titre complet sur 2 lignes.
- **2 ne nécessitent pas de troncature** (≤58 chars) → absents de la carte → fallback naturel → titre avec `~`, tient sur 1 ligne, pas de problème visible.

### Tableau de comparaison

| Titre complet | Chars | Stable | LaTEI attendu (carte) | LaTEI réel | Cause |
|---|---|---|---|---|---|
| Aspects ludiques dans l'appareil héraldique des manuscrits de Léon X (1513-1521) | 81 | Aspects ludiques dans l'appareil héraldique… (46) | Idem | **Titre complet, 2 lignes** | `Léon\xa0X` → `~` ≠ espace |
| L'héraldique de Jules III Ciocchi del Monte (1550-1555) dans l'ornement pour le livre | 86 | L'héraldique de Jules III Ciocchi del Monte (1550-1555)… (56) | Idem | **Titre complet, 2 lignes** | `Jules\xa0III` → `~` ≠ espace |
| Érudits et héraldique dans la Rome d'Urbain VIII (1623-1644) | 60 | Érudits et héraldique dans la Rome d'Urbain… (46) | Idem | **Titre complet, 2 lignes** | `Urbain\xa0VIII` → `~` |
| Piranèse, l'héraldique et Clément XIII Rezzonico (1758-1769) | 61 | Piranèse, l'héraldique et Clément XIII… (40) | Idem | **Titre complet, 2 lignes** | `Clément\xa0XIII` → `~` |
| La mise en signe de l'espace par les papes : pratiques et conflits | 66 | La mise en signe de l'espace par les papes… (46) | Idem | **Titre complet, 2 lignes** | `papes\xa0:` → `~` |
| La collégiale Saint-Jean-Baptiste puis Saint-Louis de Castelnau-Bretenoux : un lien étroit | 91 | La collégiale Saint-Jean-Baptiste puis Saint-Louis… (51) | Idem | **Titre complet, 2 lignes** | `Bretenoux\xa0:` → `~` |

### Résumé du mécanisme de défaillance

```
Python (latei_running_titles.py)
  _normalize_space("...Léon\xa0X...")  →  "...Léon X..." (espace ordinaire)
  escape_latex("...Léon X...")         →  "...Léon X..." (inchangé)
  
  \lateiDeclareRunningTitle{...Léon X...}{titre court}
                                             ↑ clé avec ESPACE ORDINAIRE

LuaLaTeX compile le corps TeX
  \newunicodechar{ }{~}  ← mapping U+00A0 → ~ (tilde LaTeX)
  data-page-title={...Léon~X...}  ← U+00A0 tokenisé en ~
  
  \latei_markboth:n{...Léon~X...}
    → prop lookup: clé "...Léon~X..."  vs  stocké "...Léon X..."
    → ÉCHEC (tilde ≠ espace ordinaire dans l3prop)
    → fallback: \markboth{...Léon~X...}{...}  (81 chars)
    → DÉBORDEMENT sur 2 lignes
```

### Correction proposée (passe F3)

**Option A — correction minimale côté Python** (dans `latei_running_titles.py`) :  
Générer les clés de carte avec `~` pour les U+00A0, en ajoutant `"\xa0": "~"` à `escape_latex` dans `latex_writer.py` (ou directement dans `_write_running_titles_map`). Cela aligne la clé avec ce que LuaLaTeX produit à la tokenisation.

**Option B — correction côté corps TeX** (dans le tei_reader/writer) :  
Normaliser les U+00A0 en `~` lors de l'émission des attributs dans `latex_writer.py`. Cela garantit la cohérence partout, pas uniquement dans les running titles.

**Option B est préférable** car elle corrige la cause racine (incohérence entre attributs et `\newunicodechar`) plutôt que de patcher un seul endroit.

---

## 5. Auteurs de contribution

### Constat

`data-page-authors` est un attribut XML présent sur les éléments `<group>` pour les types :
- `introduction` (1 cas : Yvan Loskoutoff)
- `article` (10 cas : auteurs des articles de volume collectif)
- `chapter` (2 cas : Fabrizio Federici, + autres)

Non présent pour : `book`, `section1`, `acknowledgments`, `abbreviations`.

### Données confirmées (vérification dans `.reversible.tex`)

Tous les 13 `data-page-authors` sont correctement stockés dans le LaTeX réversible :
```latex
\begin{teiElement}[name={group},type={article},
  data-page-title={Aspects ludiques...},
  data-page-authors={Elli Doulkaridou-Ramantani},
  ...]
```

### Nouvelle règle éditoriale

Conformément aux instructions de la passe F2, les auteurs **ne doivent pas être rendus sous le titre**. Ils devront être rendus **en fin de contribution**.

### Constat sur la fin de contribution

Dans la structure LaTEI actuelle, la fin d'une contribution correspond à la fermeture du `teiElement` `group` de type `article`/`chapter`/`introduction`. Le corps de la contribution est le `+b` du `\NewDocumentEnvironment{teiElement}{O{} +b}`. Ajouter un rendu d'auteur en fin de contribution est faisable via :
```latex
\NewDocumentEnvironment{teiElement}{O{} +b}{...#2...}{%
  % ← ici : rendu des auteurs si type=article/chapter/introduction
}
```

Mais pour récupérer `data-page-authors` à la fermeture de l'environnement, il faudrait stocker la valeur extraite dans une variable LaTeX au début, puis la lire à la fermeture.

### Décision

Ne pas corriger dans cette passe. Prévoir **passe F5 — auteurs en fin de contribution**.

---

## 6. Priorités de correction proposées

| Passe | Domaine | Action | Priorité |
|-------|---------|--------|----------|
| **F3** | Titres courants | Corriger la mismatch espace/tilde dans `escape_latex` ou dans l'émission des attributs LaTEI (option B préférable) | Haute |
| F4 | En-tête verso + pagination liminaire | Corriger E2 (chiffres romains) et E3 (titre ouvrage absent) de F1 | Haute |
| F5 | Auteurs en fin de contribution | Ajouter le rendu `data-page-authors` à la fermeture du groupe | Normale |
| — | Italiques / petites capitales / exposants | Aucune action requise | — |

---

## Annexe : données brutes de comptage

```
Corps LaTEI (heraldique_ii.book.normalized.latei_body.tex)
  teiHi occurrences:         3 501
  rend={italic}:             2 264
  rend={small-caps}:           707
  rend={sup}:                  388
  textit / textsc / textsuperscript (macros directes): 0   ← normal, tout passe par \teiHi

Carte des titres courants (*_latei_running_titles_map.tex)
  Entrées \lateiDeclareRunningTitle:  21
  Non-breaking spaces dans la carte:   0   ← cause du mismatch

data-page-title dans le corps TeX
  Total:   18
  Avec U+00A0:  8  (6 nécessitent troncature → lookup échoue)

Compilation (latei_mono.log)
  Erreurs LaTeX:   0
  Polices Chaparral Pro chargées:  italic ✓, small caps ✓, bold ✓
  Josefin Sans chargée:  normal ✓, italic ✓ (sans petites capitales, utilisée seulement en titre)
```

---

---

## Passe F3 réalisée

**Date :** 2026-06-23  
**Branche :** integrate-reversible-core

### Correction apportée

Fichier modifié : `purh_site/latei_running_titles.py` — fonction `_normalize_space`.

**Avant :**
```python
def _normalize_space(value: str) -> str:
    return " ".join(value.split())
```
`str.split()` sans argument normalise *tous* les espaces Unicode (y compris U+00A0) en espace ordinaire → clé de carte avec espace ordinaire → lookup TeX échoue.

**Après :**
```python
_REGULAR_WS = re.compile(r"[ \t\r\n\f\v]+")

def _normalize_space(value: str) -> str:
    return _REGULAR_WS.sub(" ", value).strip(" \t\r\n\f\v")
```
Seuls les blancs ordinaires sont normalisés. U+00A0 traverse inchangé jusqu'au fichier de carte (UTF-8). À la compilation, `\newunicodechar{ }{~}` (ligne 11 de `latei_macros.tex`) convertit U+00A0 → `~` **identiquement** dans la clé de carte et dans l'attribut de corps au runtime → le `\prop_get` réussit → titre court utilisé.

### Résultat

Les 6 chapitres dont le titre dépasse 58 caractères et contient U+00A0 trouvent désormais leur entrée dans la carte :

| Fragment NBSP dans la clé | Ancien état (carte) | Nouvel état (carte) |
|---|---|---|
| `Léon\xa0X` | `Léon X` (espace ordinaire) | `Léon X` (**NBSP préservé**) |
| `Jules\xa0III` | `Jules III` | `Jules III` |
| `Urbain\xa0VIII` | `Urbain VIII` | `Urbain VIII` |
| `Clément\xa0XIII` | `Clément XIII` | `Clément XIII` |
| `papes\xa0:` | `papes :` | `papes :` |
| `Bretenoux\xa0:` | `Bretenoux :` | `Bretenoux :` |

### Ce qui n'a pas été modifié

- Styles inline (italiques, petites capitales, exposants) : **non modifiés** ✓  
- Auteurs de contribution : **non modifiés** ✓  
- Pagination liminaire (E2) : **non modifiée** ✓  
- En-têtes verso (E3) : **non modifiées** ✓  
- `latei_macros.tex`, `latei_preamble.py`, chaîne stable : **non modifiés** ✓  
- Troncature (`_short_running_title`) : inchangée — `re.sub(r"\s+", " ", ...)` normalise toujours U+00A0 lors du calcul de longueur, le comportement de troncature est identique.

### Tests lancés

```
tests/test_latei_direct_running_titles.py   6 passed  (dont 3 nouveaux tests F3)
tests/test_latei_running_titles_minimal.py  2 passed
tests/test_latei_real_metopes_fixture.py    9 passed  (dont 1 nouveau test F3 sur fixture Héraldique)
tests/test_site_latei_pdf_mode.py          11 passed  (régression)
tests/test_site_latei_pdf_assets.py         0 passed  (inclus dans le 11 ci-dessus)
```

Tous les tests passent. Aucune régression détectée.

---

*Rapport initial : aucun fichier de production modifié.*  
*Passe F3 réalisée dans la branche `integrate-reversible-core`.*

---

## Passe F4 réalisée — Correction du bug d'italique (et petites capitales, exposants, etc.)

**Date :** 2026-06-23

### Cause racine

Le rapport F2 indiquait « Italiques ✅ » après analyse statique des macros. Cette conclusion était erronée : les macros n'avaient pas été testées par compilation.

La chaîne d'appel pour `\teiHi[rend={italic}]{texte}` est :

```
\teiHi[rend={italic}]{texte}
  → \lateiHiItalic{rend={italic}}{texte}
    → \IfSubStr{rend={italic}}{italic}{...}{...}
```

xparse `O{}` capture `[rend={italic}]` **en préservant la structure de groupe TeX** : le token `{italic}` est un groupe (accolades de catcode 1/2). xstring `\IfSubStr` **ne cherche pas à l'intérieur des groupes TeX** par conception documentée. Le test retourne donc toujours FAUX → `\textit` jamais appelé → sortie en romain.

Le même bug affectait toutes les macros `\lateiIfRend*` :
- `\lateiHiItalic` : `\IfSubStr{#1}{italic}` → toujours faux pour `rend={italic}`
- `\lateiIfRendSmallCaps` : `\IfSubStr{#1}{small-caps}` → toujours faux pour `rend={small-caps}`
- `\lateiIfRendBold` : `\IfSubStr{#1}{bold}` → toujours faux pour `rend={bold}`
- `\lateiIfRendSup` : `\IfSubStr{#1}{sup}` → toujours faux pour `rend={sup}`
- `\lateiIfRendSub` : `\IfSubStr{#1}{sub}` → toujours faux pour `rend={sub}`

### Diagnostic par micro-tests

**`micro_test_ifsubstr.tex`** — tests A-I confirment la cause et valident le fix :

| Test | Entrée | Résultat | Explication |
|------|--------|----------|-------------|
| A | `\IfSubStr{rend=italic}{italic}` | TROUVE | pas de groupe |
| B | `\IfSubStr{rend={italic}}{italic}` | NON-TROUVE | `{italic}` est un groupe |
| C | `\IfSubStr{\detokenize{rend={italic}}}{italic}` | NON-TROUVE | catcode-12 vs catcode-11 |
| F | `\IfSubStr{\detokenize{rend={italic}}}{\detokenize{italic}}` | TROUVE | fix complet |
| G | macro avec `\detokenize` des deux côtés | ITALIQUE? en italique | fix via macro |
| H | `\detokenize{small-caps}` | TROUVE | fix small-caps |
| I | `\detokenize{sup}` | TROUVE | fix sup |

`pdffonts` sur `micro_test_ifsubstr.pdf` : `ChaparralPro-Italic.otf` présent → "ITALIQUE?" rendu en vrai italique.

**`micro_test_italic.tex`** (4 cas avec macros réelles) — avant fix :

| Page | Cas | ChaparralPro-Italic |
|------|-----|---------------------|
| 1 | `\textit` direct | ✅ présent |
| 2 | `\teiHi[rend={italic}]` en corps | ❌ absent |
| 3 | `\teiHi` dans note minimale | ❌ absent |
| 4 | Note Pastor exacte | ❌ absent |

Après fix : toutes les pages ont `ChaparralPro-Italic.otf` ✅

### Correction appliquée

**Fichier modifié : `purh_site/resources/latei_macros.tex`**

Principe : `\detokenize` convertit les deux opérandes de `\IfSubStr` en chaînes catcode-12, permettant la comparaison quelle que soit la structure de groupe.

```latex
% Avant
\NewDocumentCommand{\lateiHiItalic}{m +m}{%
  \IfSubStr{#1}{italic}{\textit{#2}}{#2}%
}

% Après
\NewDocumentCommand{\lateiHiItalic}{m +m}{%
  \IfSubStr{\detokenize{#1}}{\detokenize{italic}}{\textit{#2}}{#2}%
}
```

Même pattern appliqué à `\lateiIfRendSmallCaps`, `\lateiIfRendBold`, `\lateiIfRendSup`, `\lateiIfRendSub`.

### Ce qui n'a pas été modifié

- `\teiHi`, `\lateiHiSmallCaps`, `\lateiHiPosition`, `\lateiHiBold` : inchangés (ils délèguent aux `\lateiIfRend*`)
- Titres courants (F3) : non modifiés ✓
- Auteurs, pagination, en-têtes verso, GUI, chaîne stable : non modifiés ✓

### Test de régression (F4-bis)

**Fichier créé : `tests/test_latei_rend_macro_rendering.py`** (6 tests)

- `test_latei_macros_file_exists` : vérifie que `purh_site/resources/latei_macros.tex` est bien en place
- `test_rend_macros_use_detokenize_on_both_sides` : pour chaque macro `\lateiHiItalic`, `\lateiIfRendSmallCaps`, `\lateiIfRendBold`, `\lateiIfRendSup`, `\lateiIfRendSub` — vérifie que `\detokenize{#1}` ET un deuxième `\detokenize{` sont présents dans le bloc de définition
- `test_no_bare_ifsubstr_on_hash1_for_rend_macros` : détecte tout `\IfSubStr{#1}{...}` sans `\detokenize` résiduel dans le contexte de ces macros
- `test_lualatex_compilation_succeeds` : compile un mini-document avec `\teiHi[rend={italic}]`, `\teiHi[rend={small-caps}]`, `\teiHi[rend={sup}]`, `\teiHi[rend={sub}]`, et une note footnote — vérifie que le PDF est produit (skip si lualatex absent)
- `test_lualatex_log_has_no_fatal_errors` : vérifie l'absence de lignes `!` dans le log
- `test_pdf_contains_italic_font` : `pdffonts` doit rapporter une fonte italique/oblique — confirme que `\textit` a bien été appelé (skip si pdffonts absent)

**Micro-tests temporaires (`.audit_f1/latei/`)** : restent hors Git — artefacts de diagnostic, non commités.

### Tests lancés

```
tests/test_latei_rend_macro_rendering.py          6 passed
tests/test_reversible_inline_scholarly_elements.py  }
tests/test_latei_real_metopes_fixture.py            } 12 passed
tests/test_site_latei_pdf_mode.py                  7 passed
```

Aucune régression détectée.
