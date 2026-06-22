# Audit imports ancienne chaîne PDF

## Résumé

La cartographie ci-dessous identifie **18 points d'import** vers les modules de
l'ancienne chaîne PDF stable, répartis en quatre catégories :

| Catégorie | Fichiers concernés | Imports recensés |
|---|---|---|
| Code de production (non-LaTEI) | `site_builder.py` | 2 symboles |
| Code de production (chaîne LaTEI active) | `latei_driver.py`, `latei_running_titles.py` | 3 symboles dont **2 bloquants** |
| Modules de transition | `latei_stable_pdf.py`, `latei_convergence_audit.py` | 4 symboles |
| Tests | 9 fichiers | multiples |

**Symboles bloquants pour la Passe B :**
- `_short_running_title` — importé depuis `latex_renderer.py` par `latei_running_titles.py`
  et 3 fichiers de test LaTEI
- `RUNNING_TITLE_STOPWORDS` — importé depuis `latex_renderer.py` par 1 fichier de test LaTEI
- `render_purh_preamble_for_latei` — importé depuis `latex_renderer.py` par `latei_driver.py`

Ces trois symboles empêchent le déplacement de `latex_renderer.py` en `legacy/`. Ils
doivent être extraits dans un module neutre avant toute migration.

---

## Imports depuis le code de production

### `purh_site/site_builder.py`

```python
from .latex_renderer import LatexRenderOptions          # ligne 14
from .pdf_builder import PdfBuildResult, PdfBuilder     # ligne 16
```

Utilisation : `SiteBuilder._generate_pdf_site_artifacts()` (ligne 396) construit
`PdfBuilder(latex_options=LatexRenderOptions(style="purh"), ...)` et l'appelle quand
`config.pdf_export_mode ∈ {"latex", "latex_pdf"}`.

**Statut :** Import production actif. Sera supprimé en Passe E (basculement GUI vers
LaTEI). Rien à faire avant que LaTEI direct soit validé.

---

## Imports depuis la chaîne LaTEI active

### `purh_site/latei_driver.py`

```python
from .latex_renderer import render_purh_preamble_for_latei    # ligne 16
```

Utilisation : `build_latei_driver()` appelle `render_purh_preamble_for_latei(...)` à
la ligne 64 pour construire le préambule PURH du driver compilable.

**Statut :** Import bloquant. `latei_driver.py` est un module de production LaTEI
actif. Tant que `render_purh_preamble_for_latei` reste dans `latex_renderer.py`, ce
module dépend de la chaîne stable.

---

### `purh_site/latei_running_titles.py`

```python
from purh_site.latex_renderer import _short_running_title    # ligne 10
```

Utilisation : `_short_running_title(title)` à la ligne 43, appelé pour chaque titre
long à abréger dans le mapping des titres courants LaTEI.

**Statut :** Import bloquant. `latei_running_titles.py` est un module de production
LaTEI actif.

---

## Imports depuis les modules de transition

### `purh_site/latei_stable_pdf.py`

```python
from .latex_renderer import LatexRenderOptions       # ligne 15
from .pdf_builder import PdfBuildResult, PdfBuilder  # ligne 16
```

Utilisation : `build_stable_pdf_from_latei_body()` (ligne 74) appelle `PdfBuilder()`
pour produire un PDF stable à partir d'un corps LaTEI restauré.

**Statut :** Module de transition explicite (docstring : « this module deliberately
does not render PDF from LaTEI macros »). Ces imports disparaîtront avec le module
en Passe I.

---

### `purh_site/latei_convergence_audit.py`

```python
from .latex_renderer import LatexRenderOptions              # ligne 11
from .pdf_builder import PdfBuildResult, PdfBuilder         # ligne 12
```

Utilisation : `run_latei_pdf_convergence_audit()` (ligne 59) et
`run_latei_tex_convergence_audit()` (ligne 104) appellent chacun `PdfBuilder()` pour
produire le PDF stable de comparaison.

**Statut :** Outil de comparaison, non-production. Ces imports disparaîtront avec le
module en Passe I.

---

## Imports depuis les tests

### Tests 100% ancienne chaîne (candidats `tests/legacy/`)

| Fichier | Imports |
|---|---|
| `tests/test_pdf_latex.py` | `LatexRenderer`, `LatexRenderOptions`, `_short_running_title`, `PdfBuilder`, types `semantic_model`, `parse_normalized_tei` |
| `tests/test_pdf_structure.py` | `LatexRenderer`, `LatexRenderOptions`, `Division`, `parse_normalized_tei` |
| `tests/test_pdf_latex_compile.py` | `LatexRenderOptions`, `PdfBuilder` |
| `tests/test_stable_purh_decisions_contract.py` | `LatexRenderOptions`, `PdfBuilder`, `parse_normalized_tei` |

Ces quatre fichiers testent exclusivement la chaîne stable. Ils constituent l'oracle
typographique de référence. À déplacer en `tests/legacy/` en Passe G, en conservant
`test_stable_purh_decisions_contract.py` comme oracle à long terme.

---

### Tests LaTEI qui importent encore depuis la chaîne stable

| Fichier | Import problématique | Usage |
|---|---|---|
| `tests/test_latei_direct_running_titles.py` | `RUNNING_TITLE_STOPWORDS`, `_short_running_title` from `latex_renderer` | Vérifie que le raccourcissement LaTEI est cohérent avec la logique stable |
| `tests/test_latei_running_titles_minimal.py` | `_short_running_title` from `latex_renderer` | Idem, fixture minimale |
| `tests/test_latei_direct_title_page.py` | `LatexRenderOptions`, `PdfBuilder` | Comparaison page de titre LaTEI vs stable |
| `tests/test_latei_direct_frontmatter_numbering.py` | `LatexRenderOptions`, `PdfBuilder` | Comparaison numérotation frontmatter |
| `tests/test_latei_to_stable_pdf.py` | `latei_stable_pdf`, `LatexRenderOptions`, `PdfBuilder` | Test du pont de validation |
| `tests/test_latei_pdf_convergence_audit.py` | `run_latei_pdf_convergence_audit` | Audit complet des deux chaînes |
| `tests/test_latei_tex_convergence_audit.py` | `run_latei_tex_convergence_audit` | Idem, TeX seul |

Ces sept fichiers dépendent encore de la chaîne stable mais testent des
comportements LaTEI. Après la Passe B, les trois fichiers `running_titles` pourront
pointer vers le nouveau module neutre. Les quatre autres passeront en `tests/legacy/`
en Passe G.

---

### Script CLI racine

| Fichier | Import |
|---|---|
| `test_pdf_build.py` (racine) | `from purh_site.pdf_builder import PdfBuilder` |

Script de build manuel. Passe en `legacy/` en Passe H.

---

## Fonctions partagées à extraire avant migration

Trois symboles dans `purh_site/latex_renderer.py` sont importés par des modules de
production LaTEI. Ce sont les **seules dépendances actives** de la chaîne LaTEI vers
la chaîne stable. Leur extraction est le prérequis de toute migration.

### 1. `_short_running_title(title, max_chars=58)`

Définie à `latex_renderer.py:102`.

Importée par :
- `purh_site/latei_running_titles.py:10` (production LaTEI)
- `tests/test_latei_direct_running_titles.py:5` (test LaTEI)
- `tests/test_latei_running_titles_minimal.py:9` (test LaTEI)
- `tests/test_pdf_latex.py:5` (test stable — restera dans legacy)

### 2. `RUNNING_TITLE_STOPWORDS`

Définie à `latex_renderer.py:67` (constante de module).

Importée par :
- `tests/test_latei_direct_running_titles.py:5` (test LaTEI)

### 3. `render_purh_preamble_for_latei(...)`

Définie à `latex_renderer.py:1283`.

Importée par :
- `purh_site/latei_driver.py:16` (production LaTEI)

**Module cible recommandé :** `purh_site/latei/preamble.py` ou
`purh_site/latei_preamble.py` (selon si le sous-paquet `latei/` est créé maintenant
ou plus tard). Les trois symboles y sont cohérents : logique de mise en page PURH
partagée entre le driver et les titres courants.

Après l'extraction, `latex_renderer.py` ne sera plus importé par aucun module de
la chaîne LaTEI active, et pourra être déplacé en `legacy/` en Passe H sans risque.

---

## Modules candidats legacy

Par ordre de déplacement recommandé :

| Priorité | Module | Dépendances actives côté LaTEI | Condition préalable |
|---|---|---|---|
| 1 | `purh_site/latei_convergence_audit.py` | aucune | Passe I seulement |
| 2 | `purh_site/latei_stable_pdf.py` | aucune | Passe I seulement |
| 3 | `purh_site/semantic_model.py` | aucune | Passe H (après pdf_builder) |
| 4 | `purh_site/tei_to_model.py` | aucune | Passe H (après pdf_builder) |
| 5 | `purh_site/pdf_builder.py` | aucune (indirect via site_builder) | Passe E d'abord |
| 6 | `purh_site/latex_renderer.py` | 3 symboles (voir ci-dessus) | **Passe B d'abord** |

---

## Modules à ne pas déplacer encore

| Module | Raison |
|---|---|
| `purh_site/latex_renderer.py` | Contient encore `render_purh_preamble_for_latei` (Cas B, voir Passe B) + re-exports de compatibilité pour tests legacy |
| `purh_site/pdf_builder.py` | `site_builder.py:396` l'appelle en production si `pdf_export_mode != "none"` |
| `purh_site/latei_convergence_audit.py` | Oracle actif de comparaison structurelle — utile jusqu'en Passe I |
| `purh_site/latei_stable_pdf.py` | Outil de validation du roundtrip — utile jusqu'en Passe I |

---

## Passe B réalisée

**Date :** 2026-06-22

### Symboles extraits

- `RUNNING_TITLE_STOPWORDS` (constante de module)
- `_short_running_title(title, max_chars=58)`

Déplacés dans le nouveau module **`purh_site/latei_typography.py`**, qui n'importe
ni `LatexRenderer`, ni `semantic_model`, ni aucun autre module de la chaîne stable.
Il n'utilise que `re` (bibliothèque standard).

### Imports mis à jour

| Fichier | Changement |
|---|---|
| `purh_site/latei_running_titles.py:10` | `latex_renderer` → `latei_typography` |
| `tests/test_latei_direct_running_titles.py:5` | `latex_renderer` → `latei_typography` |
| `tests/test_latei_running_titles_minimal.py:9` | `latex_renderer` → `latei_typography` |

### Re-export de compatibilité dans `latex_renderer.py`

La ligne suivante remplace les définitions originales (ligne 67) :

```python
from .latei_typography import RUNNING_TITLE_STOPWORDS, _short_running_title  # re-exports
```

Les tests legacy (`test_pdf_latex.py`) continuent à importer depuis `latex_renderer`
sans modification. `LatexRenderer._render_chapter_section_head()` (ligne 655) utilise
`_short_running_title` via le re-export, sans régression.

### Cas B — `render_purh_preamble_for_latei` non extrait

`render_purh_preamble_for_latei` (`latex_renderer.py:1283`) **ne peut pas être
extrait sans traîner `LatexRenderer`**. La fonction instancie explicitement
`LatexRenderer(options=LatexRenderOptions(style="purh"))` et appelle
`renderer._render_purh_preamble(book)`. Elle dépend aussi de `Book`, `BookMetadata`,
`Contributor`, `PublicationInfo` depuis `semantic_model.py`.

`latei_driver.py:16` importe encore `render_purh_preamble_for_latei` depuis
`latex_renderer.py`. Cette dépendance nécessite une **passe séparée** où
`_render_purh_preamble` sera extraite de la classe `LatexRenderer` en fonction
autonome, indépendante du modèle sémantique.

### Tests ciblés — résultats

| Test | Résultat |
|---|---|
| `tests/test_latei_direct_running_titles.py` | ✓ 2 passés |
| `tests/test_latei_running_titles_minimal.py` | ✓ 1 passé |
| `tests/test_latei_direct_title_page.py` | ✓ 3 passés |
| `tests/test_latei_real_metopes_fixture.py` | ✓ 8 passés |

### État après Passe B

La chaîne LaTEI des titres courants (`latei_running_titles.py`) n'importe plus
`_short_running_title` ni `RUNNING_TITLE_STOPWORDS` depuis `latex_renderer.py`.

La dépendance du driver LaTEI vers `latex_renderer.py` subsiste volontairement :

```
purh_site/latei_driver.py → render_purh_preamble_for_latei → LatexRenderer
```

Ce point n'est pas un oubli de la Passe B — il est reporté à la Passe B2, qui
extraira `_render_purh_preamble` hors de `LatexRenderer`.

---

## Passe B2 réalisée

**Date :** 2026-06-22

### Module créé

**`purh_site/latei_preamble.py`** — indépendant de `LatexRenderer`, `LatexRenderOptions`,
`semantic_model`, `tei_to_model`, `pdf_builder`. Dépend uniquement de la bibliothèque
standard Python (`dataclasses`).

Contient :
- `PurhPreambleData` — dataclass `frozen=True, slots=True` avec 7 champs `str`
  (`title`, `subtitle`, `authors: tuple[str,...]`, `publisher`, `year`, `doi`, `isbn`)
- `render_purh_latex_preamble(data)` — fonction autonome produisant le préambule PURH complet
- `_escape(value)` — fonction interne d'échappement LaTeX

### Imports mis à jour

| Fichier | Changement |
|---|---|
| `purh_site/latei_driver.py:16` | suppression de `from .latex_renderer import render_purh_preamble_for_latei` ; ajout de `from .latei_preamble import PurhPreambleData, render_purh_latex_preamble` |
| `purh_site/latex_renderer.py` : `_render_purh_preamble` | remplacé par délégation à `render_purh_latex_preamble` via import local |
| `purh_site/latex_renderer.py` : `render_purh_preamble_for_latei` | remplacé par wrapper mince vers `render_purh_latex_preamble` |

### `render_purh_preamble_for_latei` dans `latex_renderer.py`

Conservée comme wrapper de compatibilité pour les tests legacy et les modules de
comparaison. Ne construit plus de `Book`/`BookMetadata`/`LatexRenderer` — délègue
directement à `latei_preamble.render_purh_latex_preamble`.

### Garantie d'identité de sortie

`LatexRenderer._render_purh_preamble(book)` et `render_purh_preamble_for_latei(...)`
produisent désormais exactement la même chaîne via le même chemin de code.
Vérifié par `test_latei_preamble_output_matches_latex_renderer_wrapper`.

### Note sur `collection_title`, `collection_number`, `issn`

Ces paramètres de `render_purh_preamble_for_latei` passaient dans `PublicationInfo`
mais n'étaient jamais utilisés dans le template du préambule. Ils sont intentionnellement
absents de `PurhPreambleData`. Le comportement visible est inchangé.

### Tests ciblés — résultats

| Test | Résultat |
|---|---|
| `tests/test_latei_preamble_independent.py` (9 tests) | ✓ 9 passés |
| `tests/test_latei_direct_title_page.py` | ✓ 3 passés |
| `tests/test_latei_real_metopes_fixture.py` | ✓ 8 passés |
| `tests/test_latei_direct_running_titles.py` | ✓ 2 passés |
| `tests/test_latei_running_titles_minimal.py` | ✓ 1 passé |
| **Total** | **23/23** |

### État après Passe B2

La chaîne LaTEI active n'importe plus `purh_site.latex_renderer` depuis aucun de ses
modules de production :

```
purh_site/latei_driver.py          → latei_preamble  (✓ propre)
purh_site/latei_running_titles.py  → latei_typography (✓ propre, Passe B)
purh_site/latei_preamble.py        → stdlib uniquement (✓ propre)
purh_site/latei_typography.py      → stdlib uniquement (✓ propre, Passe B)
purh_site/latei_assets.py          → pas de latex_renderer (✓)
purh_site/latei_metadata.py        → pas de latex_renderer (✓)
purh_site/reversible_integration.py→ pas de latex_renderer (✓)
```

`latex_renderer.py` peut désormais être déplacé en `legacy/` en Passe H sans
casser la chaîne LaTEI de production. Il ne reste plus qu'une seule dépendance
vers `latex_renderer.py` depuis du code de production : `site_builder.py:396`
(`PdfBuilder`) — reportée à la Passe E.
