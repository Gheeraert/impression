# Audit complet Impressions / impression2

**Date** : 2026-06-17  
**Auditeur** : Claude Sonnet 4.6  
**Branche** : `dev`  
**Tests** : 147 passés, 2 skippés (LuaLaTeX optionnel), 0 échoués  
**Fichiers modifiés** : aucun — seul ce fichier est créé.

---

## 1. Résumé exécutif

Le projet est en bonne santé générale. La philosophie de sobriété technique est tenue : le code est lisible, les passes sont testées, la séparation HTML/PDF est saine. Le modèle sémantique reste raisonnable pour une V1.

Deux bugs réels sont identifiés dans la chaîne PDF : les liens inline utilisent `_escape_text` au lieu de `_escape_url` pour les cibles d'URL, et `_escape_url` n'échappe pas `&`. Ces deux défauts ne cassent pas le build (LuaLaTeX tolère souvent les sous-caractères mal encodés), mais peuvent produire des liens silencieusement invalides sur des TEI Métopes réels.

Le risque éditorial le plus sérieux est le traitement silencieux des notes `place="end"` : elles sont ignorées sans warning. Dans un livre PURH avec des notes de fin, la totalité des appels de notes serait perdue.

Aucun refactoring structurel n'est urgent. Les fonctions longues sont du LaTeX en chaîne Python (acceptable) ou de la coordination éditoriale (acceptable). Le vrai bénéfice viendrait d'une extraction de `_render_credit_block` et `_render_zotero_meta` hors de `SiteBuilder`, mais c'est une amélioration de maintenabilité, pas un bug.

---

## 2. Points solides

- **Architecture HTML/PDF clairement séparée** : `SiteBuilder` ne connaît pas `PdfBuilder`, aucune dépendance croisée.
- **Pivot TEI normalisé bien exploité** : `PdfBuilder` part du `book.normalized.xml`, pas du TEI brut. La normalisation est donc déjà appliquée.
- **Modèle sémantique stable** : `semantic_model.py` est propre, bien typé, tous les champs ont des valeurs par défaut sensées. `slots=True` partout.
- **Gestion des images robuste** : `_absolutize_figure_paths` convertit tous les chemins en absolus avant la compilation, `\detokenize{}` protège les espaces dans les noms de fichiers, le fallback vers l'image alternative est bien implémenté.
- **Bibliographie PDF sans biblatex** : le rendu TEI → LaTeX natif est cohérent avec la philosophie du projet. La passe 13C couvre les trois cas (monographie, contribution, article) avec une gestion propre de la ponctuation orpheline.
- **Tests orientés cas éditoriaux réels** : les tests de bibliographie vérifient les sorties texte complètes, pas seulement des fragments. Les tests de non-régression sur `<bibl>` simple sont présents.
- **Isolation correcte des tests LuaLaTeX** : variable d'environnement, `pytestmark`, nettoyage avec retry sur Windows. Le PNG synthétique évite toute dépendance binaire externe.
- **Rapport PDF utile** : timing, stats, warnings, commandes exécutées — tout ce qu'il faut pour déboguer un build.

---

## 3. Risques critiques

| # | Sévérité | Fichier / Fonction | Description |
|---|----------|-------------------|-------------|
| R1 | **Bug réel** | `latex_renderer.py:1047` | Liens inline : `_escape_text` au lieu de `_escape_url` pour la cible |
| R2 | **Bug réel** | `latex_renderer.py:1115` | `_escape_url` n'échappe pas `&` |
| R3 | **Perte silencieuse** | `tei_to_model.py:1042` | Notes `place="end"` ignorées sans warning |
| R4 | **Données perdues** | `pdf_builder.py:279` | Images dans les notes non absolutisées |
| R5 | **Rendu décalé** | `latex_renderer.py:969` | Tableaux avec `cols>1`/`rows>1` non rendus (fusions ignorées) |

---

## 4. Audit architecture

### 4.1 Cohérence générale

L'architecture respecte le principe annoncé : TEI → normalisé → modèle → rendu.

```
TEI brut
  └─ TeiLoader + TeiNormalizer
       └─ book.normalized.xml
            ├─ SiteBuilder (XSLT → HTML pages)
            └─ TeiToModelParser → Book → LatexRenderer → .tex → LuaLaTeX → .pdf
```

La séparation est propre. `SiteBuilder` ne connaît pas `PdfBuilder`. Le fait que `PdfBuilder` lise le fichier normalisé (et non le TEI brut directement) est une bonne décision : la normalisation est mutualisée.

### 4.2 Séparation HTML / PDF

Saine. Les deux chaînes ont leurs propres parseurs du TEI normalisé :
- chaîne HTML : XSLT (`tei_to_html.xsl`) pilotée par `SiteBuilder`
- chaîne PDF : `TeiToModelParser` + `LatexRenderer`

**Risque de divergence** : les deux parseurs peuvent interpréter différemment certains cas TEI (bibliographie, figures, inline). Il n'existe pas de test vérifiant que les deux rendus sont cohérents sur le même XML. À surveiller quand les deux chaînes seront intégrées.

### 4.3 Pivot TEI normalisé

Bien utilisé. `TeiToModelParser.parse()` reçoit le chemin du fichier normalisé. La dépendance sur l'état normalisé est assumée et documentée dans le module.

Tension : `TeiToModelParser` utilise `recover=True` dans son `XMLParser`, alors que le XML est supposé être déjà normalisé. Ce choix est défensif et correct pour la V1.

### 4.4 Gonflement du modèle sémantique

Le modèle sémantique (`semantic_model.py`, 454 lignes) est encore raisonnable. `BibliographicEntry` a 13 champs, ce qui est à surveiller. `BibliographyItem` utilise deux champs optionnels mutuellement exclusifs (`content` et `structured`) au lieu d'un type union, ce qui est moins strict mais acceptable.

Le modèle n'a pas encore grossi de façon préoccupante.

### 4.5 Doublons entre les deux chaînes

Les doublons concernent :
- **Bibliographie** : parsée par le XSLT côté HTML et par `_parse_bibl_struct` côté PDF — deux implémentations indépendantes.
- **Figures** : idem.
- **Navigation** : `SiteStructureBuilder` et `TeiToModelParser._iter_group_divisions` couvrent des aspects du même arbre de groupes.

Ces doublons sont **inévitables** à ce stade (deux sorties différentes). Ils deviennent dangereux si les deux rendus divergent sur un même TEI réel. Un test d'intégration croisé (même XML → HTML et PDF → même auteur, même titre, même ponctuation) serait utile à terme.

---

## 5. Audit chaîne PDF

### 5.1 `PdfBuilder.build_from_normalized_tei`

Solide. L'orchestration en 5 étapes est claire. Le `try/except Exception` central est marqué `# pragma: no cover` — acceptable pour un garde-fou de production, mais cela signifie que les erreurs de parsing TEI ne sont pas testées. Si `parse_normalized_tei` lève une exception sur un XML malformé, le comportement n'est pas couvert.

### 5.2 Compilation LaTeX

`_compile_latex` : robuste. Points positifs :
- `shutil.which` pour localiser le moteur.
- `errors="replace"` pour la sortie stdout/stderr sur Windows.
- `timeout=self.timeout_seconds` protège contre les compilations infinies.
- Double passe (par défaut `latex_runs=2`) pour la table des matières.
- Log accumulatif avec `"a"` (append) : correct.

Point faible : si `process.returncode != 0` à la première passe, on retourne `False` immédiatement. La deuxième passe n'est jamais tentée. C'est une décision raisonnable.

### 5.3 Gestion des erreurs

- RuntimeError pour moteur absent → capturé par le `except Exception` → `error_message` dans le résultat. Bien.
- Le rapport est toujours écrit, même en cas d'erreur. Bien.
- Warning pour image manquante : présent et clair.
- **Manquant** : aucun warning pour une note `place="end"` ignorée (voir R3).
- **Manquant** : aucun warning pour un `biblStruct` avec `monogr=None` (cas théoriquement impossible en TEI valide mais défensif).

### 5.4 Comportement sans LuaLaTeX

Correct. `compile_pdf=False` → le `.tex` est généré, `result.success = tex_path.exists()`, un log explicite est écrit. Les tests de la suite principale n'exigent pas LuaLaTeX.

### 5.5 Chemins Windows

- `-output-directory` et le chemin du `.tex` passés en POSIX : correct, LuaLaTeX accepte les deux.
- `\detokenize{}` pour les images avec espaces : correct.
- Cache `.texlive-cache` dans le dossier de sortie : correct pour Windows où `TEXMFVAR` peut être verrouillé en env système.

### 5.6 Bug R1 : Liens inline avec `_escape_text`

**Fichier** : `latex_renderer.py`, ligne 1047.

```python
# Code actuel — PROBLÈME
target = self._escape_text(node.target)
return rf"\href{{{target}}}{{{label}}}"
```

`_escape_text` transforme `_` en `\_`, `%` en `\%`, `#` en `\#`, etc. Ces substitutions sont correctes dans le texte courant mais peuvent produire un lien cassé dans `\href{}`. Il faut utiliser `_escape_url` pour le target.

Exemple concret : un lien TEI `<ref target="https://doi.org/10.4000/test_doc">` produirait `\href{https://doi.org/10.4000/test\_doc}{...}` — LuaLaTeX tolérera parfois ce cas mais il s'agit d'un encodage incorrect.

**Action** : remplacer `self._escape_text(node.target)` par `self._escape_url(node.target)` dans `_render_inline_node` pour le cas `Link`.

### 5.7 Bug R2 : `_escape_url` n'échappe pas `&`

**Fichier** : `latex_renderer.py`, méthode `_escape_url` (ligne 1115).

```python
replacements = {
    "\\": "/",
    "{": r"\{",
    "}": r"\}",
    "%": r"\%",
    "#": r"\#",
    "_": r"\_",
}
```

`&` est absent. Une URL `https://example.org/page?a=1&b=2` dans `\href{}` produira une erreur LaTeX (`&` est le séparateur de colonnes en mode tabular et une commande actif sous babel/french). Dans des URL de DOI/OpenEdition, le `&` est rare mais possible dans les URLs de redirections.

**Action** : ajouter `"&": r"\&"` dans le dictionnaire de `_escape_url`.

---

## 6. Audit bibliographie

### 6.1 Modèle bibliographique

Bien dimensionné. Les trois cas (monographie, contribution, article) correspondent aux cas Métopes réels. La détection par `(analytic_title, journal_title)` dans `_parse_bibl_struct` est correcte.

### 6.2 Parsing de `biblStruct`

Solide. `_parse_bibl_people` accepte le texte direct ET la structure `<persName>`. `_parse_bibl_title` gère le fallback vers `<title>` sans niveau pour les monographies.

**Risque** : `_parse_bibl_title` pour level `"m"` prend n'importe quel `<title>` non-`j`, ce qui inclut `level="s"` (titre de série). Un `biblStruct` avec `<title level="s">Bibliothèque de la Pléiade</title>` (sans titre de monographie séparé) produirait un titre de série rendu comme titre de livre.

### 6.3 Rendu monographie

`_render_monograph_entry` → `_join_bibl_parts([authors, title, pub_place, publisher, date])`.

La ponctuation orpheline est correctement évitée par `_join_bibl_parts` qui filtre les parties vides. Le test `test_biblstruct_with_missing_fields_has_no_orphan_punctuation` le couvre bien.

### 6.4 Rendu contribution

`_render_contribution_entry` : la chaîne `dans {editors} (dir.), {titre}, {lieu}, {éditeur}, {date}, {pages}` est correcte. Le test vérifie l'absence de `(dir.), ,` et de `dans (dir.)`. Bon.

**Légère fragilité** : si le volume collectif a une date mais pas de lieu ni d'éditeur, on obtient `dans (dir.), Titre, 2020, pages.` — la virgule avant `2020` est normale mais produit un `", 2020"` qui peut sembler orphelin selon les normes. Non critique.

### 6.5 Rendu article

`_render_journal_article_entry` : auteurs, titre analytique, titre de revue, vol, no, date, pages. Correct.

**Particularité** : `_prefixed_bibl_value("vol.", entry.volume)` ne préfixe que si la valeur ne commence pas déjà par "vol.". Correct.

### 6.6 Auteurs et directeurs multiples

`_join_readable_names` : "A et B" (2), "A, B et C" (3+). Conforme aux normes françaises.
`_format_editors` : ajoute `(dir.)` une seule fois. Bien vérifié par le test `test_biblstruct_multiple_editors_get_single_dir_marker`.

### 6.7 DOI et URI

`_doi_target` : gère le cas `doi` déjà en forme http. Correct.
`_bibl_identifier_link` : produit `\href{url}{label}`. Correct.

**Risque de duplication** : `_parse_bibl_identifiers` extrait à la fois les `<idno>` et les `<ref>`. Si un XML Métopes a :
```xml
<idno type="DOI">10.4000/foo</idno>
<ref type="DOI" target="https://doi.org/10.4000/foo">texte</ref>
```
→ deux entrées DOI seront produites dans le rendu. Aucun test ne vérifie ce cas.

### 6.8 Bibliographie en note

`_render_bibliography_block` avec `_in_footnote=True` : les entrées sont séparées par `"; "` et rendues sans environnement. Bien. Testé dans les deux suites (HTML et PDF).

### 6.9 Non-régression de `<bibl>` simple

Correctement testée : `test_simple_bibl_rendering_is_not_regressed` (PDF) et `test_simple_bibl_still_avoids_nested_cites` (HTML).

### 6.10 Titres déjà guillemetés

`_format_bibl_title` : si le texte commence par `«` et se termine par `»`, on n'ajoute pas `\enquote{}`. Testé côté PDF et HTML. Correct.

---

## 7. Audit tableaux et figures

### 7.1 Tableaux simples

**Rendu** : `tabularx` avec colonnes `X` (largeur égale et flexible). Correct pour un tableau 2-4 colonnes.

**`\midrule` après la première ligne** : conditionnel sur `role="label"` dans les cellules de la première ligne. Bien. Testé.

**Cellules `role="label"` en gras** : `\textbf{}` appliqué. Correct.

### 7.2 Risque R5 : Fusion de cellules ignorée

`cols` et `rows` sont stockés dans `TableCell` mais `_render_table_cell` et `_render_table_block` les ignorent totalement. Dans un tableau Métopes réel avec `<cell cols="2">`, les colonnes ne seront pas fusionnées. Le rendu sera décalé (une cellule occupe l'espace d'une colonne au lieu de deux), produisant un tableau bancal.

**Action urgente** : documenter explicitement dans le code que le colspan/rowspan n'est pas géré, et ajouter un warning dans `_render_table_block` si `cell.cols > 1 or cell.rows > 1`.

### 7.3 Lignes de longueur variable

`_render_table_block` : les lignes courtes sont complétées avec des `""` pour atteindre `column_count`. Cela évite les erreurs LaTeX mais produit des cellules vides sans visual alignment. Acceptable pour la V1.

### 7.4 Chemins d'images relatifs

`_parse_figure_block` dans `tei_to_model.py` : le chemin est extrait de `@url`, `@target`, ou `@n`. L'attribut `@n` comme fallback est improbable dans un contexte image mais ne casse rien.

`_absolutize_figure_paths` dans `pdf_builder.py` : convertit correctement en chemins absolus. Gère les espaces dans les noms via `\detokenize{}`.

**Risque R4** : `_absolutize_blocks_paths` est appelé sur `division.blocks` et récursivement sur les sections, mais **pas** sur `division.notes`. Si une figure se trouve dans une note de bas de page, son chemin ne sera pas absolutisé. Le test suivant manque :

```python
# Figure dans une note → chemin absolutisé
```

### 7.5 Image principale / alternative

`_select_figure_image_path` : teste l'existence du fichier sur disque pour décider quelle image utiliser. Correct.

**Dépendance implicite** : cette méthode suppose que `_absolutize_figure_paths` a été appelée. Si on utilise `LatexRenderer.render_book()` directement sans passer par `PdfBuilder`, les chemins relatifs ne seront jamais résolus et toutes les images apparaîtront comme manquantes (fallback `\fbox{}`). Aucune erreur explicite n'est levée.

**Suggestion** : ajouter une note dans le docstring de `LatexRenderer.render_book` indiquant que les chemins d'images doivent être absolus.

### 7.6 Fallback image manquante

```latex
\fbox{\parbox{0.8\linewidth}{\centering\footnotesize Image absente ou non fournie}}
```

Correct et visuellement distinct. Warning présent dans le rapport. Bien.

### 7.7 Où devrait vivre la logique image ?

Actuellement : `_absolutize_figure_paths` est dans `PdfBuilder`, `_select_figure_image_path` est dans `LatexRenderer`. Cette coupure est logique (absolutisation = étape de build, sélection = étape de rendu) et doit rester ainsi.

---

## 8. Audit tests

### 8.1 Qualité générale

147 tests, bien nommés, orientés comportements éditoriaux réels. La majorité des tests créent leur propre XML dans `tmp_path`. Bonne isolation, légère duplication des helpers.

### 8.2 Fonctions helpers dupliquées

`write_tei()` existe dans `test_pdf_latex.py` et `write_structure_tei()` dans `test_pdf_structure.py`. Ces deux fonctions font essentiellement la même chose avec des variations mineures. Un conftest.py plus riche réduirait cette duplication, mais elle est actuellement acceptable (les tests restent lisibles sans se référer à des fixtures externes).

### 8.3 Tests trop couplés aux chaînes exactes

Certains tests vérifient une chaîne LaTeX exacte sur plusieurs tokens :
```python
assert r"Blaise Pascal, \textit{Pensées}, Paris, Gallimard, 1976. ISBN 9782070100010." in latex
```
Ce niveau de précision est approprié pour une bibliographie (l'ordre des champs a une signification éditoriale) mais fragile si l'espacement autour des séparateurs change. À noter mais pas à modifier maintenant.

### 8.4 Tests manquants prioritaires

Les tests suivants font défaut :

| # | Description | Fichier concerné |
|---|-------------|-----------------|
| T1 | Tableau avec `cols="2"` → warning généré | `latex_renderer.py`, `test_pdf_latex.py` |
| T2 | URL avec `&` dans un lien inline | `latex_renderer.py`, `test_pdf_latex.py` |
| T3 | Note `place="end"` → ignorée avec warning | `tei_to_model.py`, `test_pdf_latex.py` |
| T4 | Figure dans une note → absolutisation | `pdf_builder.py`, `test_pdf_latex.py` |
| T5 | `biblStruct` avec DOI dans `idno` et `ref` simultanément | `tei_to_model.py`, `test_pdf_latex.py` |
| T6 | `build_from_normalized_tei` avec XML malformé → rapport cohérent | `pdf_builder.py`, `test_pdf_latex.py` |
| T7 | `VerseBlock` dans une compilation complète | `latex_renderer.py` |
| T8 | Division `appendix` dans la chaîne PDF complète | `latex_renderer.py`, `test_pdf_structure.py` |

### 8.5 Tests optionnels LuaLaTeX

Bien isolés. La variable `IMPRESSIONS_RUN_LATEX_INTEGRATION` est propre. `write_one_pixel_png` est une vraie astuce : elle génère un PNG valide au niveau binaire sans dépendance externe. Le retry Windows (`cleanup_runtime_dir` avec 3 essais) est correct.

Le test `test_purh_style_realistic_metopes_sample_compiles_with_lualatex` est un test d'intégration complet bien écrit : il vérifie l'ordre des divisions, les contributeurs locaux, les images réelles, les tableaux, et l'absence de "None" et "Sans titre" dans le rendu final.

### 8.6 Risques de lenteur ou fragilité Windows

- `test_pdf_latex_compile.py` : dossier de travail `.latex-integration-runtime/` dans `Path.cwd()`. Sur Windows, le verrouillage de fichiers par lualatex peut provoquer des erreurs de nettoyage. Le retry est présent mais peut échouer si lualatex garde un fichier ouvert.
- Les tests non-LuaLaTeX sont rapides (< 3 secondes total). Pas de risque.

---

## 9. Audit qualité Python

### 9.1 `site_builder.py` (1188 lignes)

**Trop long**, mais la complexité est réelle. La classe `SiteBuilder` gère :
- orchestration du build (→ `_finalize_build`)
- rendu HTML des pages (→ `_write_index_page`, `_write_content_page`)
- navigation (→ `_render_sidebar`, `_render_nav_list`)
- typographie française (→ fonctions module-level)
- qualité du site (→ `_run_site_quality_checks` et ses méthodes)
- couverture et assets (→ `_discover_theme_assets`, `_pick_asset`)
- métadonnées Zotero (→ `_render_zotero_meta`)
- bloc de citation (→ `_render_credit_block`)

`_render_credit_block` (~60 lignes) et `_render_zotero_meta` (~65 lignes) sont les méthodes les plus longues hors préambule LaTeX. Elles restent lisibles mais commencent à diluer la responsabilité de la classe.

### 9.2 `tei_to_model.py` (1161 lignes)

Long mais justifié par la richesse du TEI. La structure en sections commentées est claire. `_parse_bibl_struct` (~30 lignes) et `_parse_bibl_identifiers` (~20 lignes) sont les méthodes bibliographiques les plus complexes — acceptables.

Petit problème stylistique : les sections de commentaires (`# -------`) sont bien utilisées pour découper le fichier mais la classe TeiToModelParser a des méthodes définies **après** la clôture visuelle de la section API publique (les méthodes `_parse_book_metadata` etc. sont définies avant `# API publique` dans l'indentation de la classe mais après les commentaires de module). Pas de bug, légère incohérence de présentation.

### 9.3 `latex_renderer.py` (1161 lignes)

`_render_purh_preamble` fait ~260 lignes de texte LaTeX embarqué dans un f-string. C'est long mais il n'y a pas de meilleure solution architecturale pour la V1 : extraire dans un fichier `.tex` template serait une dépendance supplémentaire. Acceptable.

`_render_bibliographic_entry` dispatche vers 3 méthodes spécialisées. Propre.

**Incohérence nomenclature** : `_escape_url` et `_escape_text` sont bien distincts, mais `_render_inline_node` oublie cette distinction pour les liens (voir R1).

### 9.4 `pdf_builder.py` (442 lignes)

Bien dimensionné. Les traversals récursifs `_absolutize_*` sont verbeux mais explicites. Lisibles.

**`_collect_stats`** : appelle `_count_figures_in_division` qui appelle `_count_figures_in_blocks`, qui lui-même est aussi appelé par `_count_figures_in_section`. Légère duplication d'orchestration mais très lisible.

### 9.5 `semantic_model.py` (454 lignes)

Modèle propre. `BibliographyItem` avec deux champs optionnels mutuellement exclusifs (`content` et `structured`) : pas idéal théoriquement, mais acceptable pour la V1. Le pattern `Optional[X]` est plus lisible qu'un union type ici.

La fonction utilitaire `paragraph_from_text()` est bien placée en bas du fichier.

### 9.6 Typage

Le typage est généralement correct. Quelques points :

- `_absolutize_blocks_paths(self, blocks, ...)` dans `pdf_builder.py` : le paramètre `blocks` n'est pas typé. Il devrait être `list[BlockNode]`.
- `_parse_front_special_blocks` retourne `list` non typé. Il devrait être `list[BlockNode]`.
- Ces absences ne causent pas d'erreurs mais réduisent la vérifiabilité statique.

---

## 10. Risques éditoriaux

### 10.1 Notes de fin (`place="end"`) — R3

**Critique**. `_is_inline_footnote` (`tei_to_model.py:1042`) :

```python
def _is_inline_footnote(self, note_el: ET._Element) -> bool:
    place = (note_el.get("place") or "").strip().lower()
    note_type = (note_el.get("type") or "").strip().lower()
    return place in {"", "foot"} and note_type in {"", "standard"}
```

Les notes avec `place="end"` (notes de fin de chapitre, courantes dans les livres PURH) tombent dans la branche `_parse_inline_element` → repli récursif → les enfants de la note sont inclus directement dans le texte courant **sans aucun appel de note, sans numérotation, sans séparation**. Le texte de la note s'injecte silencieusement dans le paragraphe.

Ce n'est pas un bug de crash : le build réussit. Mais le PDF sera éditorialement faux.

**Action minimale** : dans `_parse_inline_element`, si `local == "note"` et que la note n'est pas inline (`_is_inline_footnote` retourne False), ignorer l'élément et émettre un warning (via un mécanisme à définir, ou en retournant un `TextRun` avec un marqueur visible `[NOTE IGNORÉE]`).

### 10.2 Notes imbriquées

`_parse_footnote` (`tei_to_model.py:896`) passe `notes_store={}` vide :
```python
blocks = self._parse_container_blocks(note_el, notes_store={})
```

Les notes dans les notes ne seront jamais enregistrées. Si une note TEI contient elle-même un appel de note (rare mais légal en TEI), la note imbriquée sera silencieusement perdue.

### 10.3 Tableaux avec fusions — R5

Un tableau Métopes réel avec `<cell cols="2">Valeur fusionnée</cell>` produira un tableau LaTeX décalé. Le modèle stocke `cols` et `rows` mais le renderer les ignore. L'auteur du livre verra un tableau avec des colonnes incorrectes.

### 10.4 Figures dans les notes — R4

Non absolutisées → rendu avec `\fbox{}` → visible dans le PDF mais sans warning explicite pour indiquer où chercher le problème.

### 10.5 Titre de série pris comme titre de monographie

`_parse_bibl_title` avec level `"m"` prend le premier `<title>` non-`j`. Si une entrée `biblStruct` Métopes a :
```xml
<monogr>
  <title level="s">Collection XYZ</title>
  <imprint>...</imprint>
</monogr>
```
sans titre de monographie proprement dit, le titre de série sera rendu comme le titre de l'ouvrage.

### 10.6 Éléments éditoriaux encore absents

Les éléments suivants n'ont pas encore de rendu PDF :

| Élément TEI | Impact |
|------------|--------|
| `<note place="end">` | Perte totale des notes de fin |
| `<cell cols>` / `<cell rows>` | Tableaux fusionnés |
| `<lg>` avec groupes imbriqués | Strophes complexes aplaties |
| `<div type="glossary">` | Glossaires non reconnus |
| Pages de titre structurées (page de titre avec institutions, résumés) | Rendu aplati |
| Tableaux dans des notes | Non testé |

### 10.7 Ce qui est acceptable pour une V1

- Pas de colonnes `twoside` avec miroir : le style `purh` est en `twoside`, correct.
- Pas de numérotation de lignes de vers : stocké dans le modèle mais non rendu. Acceptable.
- Pas de `colspan`/`rowspan` : documenté comme limitation.
- Pas de `<pb/>` (sauts de page forcés) : silencieusement ignoré. Acceptable.
- Sections niveau > 3 toutes en `\subsubsection` : acceptable.

---

## 11. Feuille de route priorisée

### A. À corriger tout de suite (micro-passes)

**A1. Bug Link URL dans le renderer PDF**  
- **Problème** : `_render_inline_node` pour `Link` utilise `_escape_text` pour la cible URL, ce qui peut casser les liens avec `_`, `%`, `#`.  
- **Fichier** : `latex_renderer.py:1047`  
- **Action** : remplacer `self._escape_text(node.target)` par `self._escape_url(node.target)`.  
- **Effort** : micro-passe (1 ligne + 1 test).

**A2. `_escape_url` manque `&`**  
- **Problème** : les URLs avec `&` (query strings) ne sont pas correctement échappées pour LaTeX.  
- **Fichier** : `latex_renderer.py:1115`  
- **Action** : ajouter `"&": r"\&"` dans `_escape_url`. Ajouter un test avec une URL contenant `&`.  
- **Effort** : micro-passe (1 ligne + 1 test).

**A3. Warning pour tableaux avec fusions**  
- **Problème** : `cols>1` ou `rows>1` ignorés silencieusement.  
- **Fichier** : `latex_renderer.py:969`  
- **Action** : dans `_render_table_block`, si une cellule a `cols > 1` ou `rows > 1`, ajouter un commentaire LaTeX `% [FUSION IGNORÉE]` et émettre un `% WARNING` dans le rendu. Pas de changement de comportement, juste de la traçabilité.  
- **Effort** : micro-passe (5 lignes + 1 test).

---

### B. À faire bientôt (passes normales)

**B1. Notes `place="end"` : gestion explicite**  
- **Problème** : notes de fin silencieusement perdues dans le flux du texte (R3).  
- **Fichier** : `tei_to_model.py:1042`, `latex_renderer.py`  
- **Action** : détecter les notes `place="end"` dans `_parse_inline_element`, les traiter comme footnotes (au moins pour la V1), ou les ignorer proprement avec un warning collecté.  
- **Effort** : passe normale. Nécessite de décider si les endnotes sont rendues comme footnotes ou omises.

**B2. Absolutisation des figures dans les notes**  
- **Problème** : `_absolutize_figure_paths` ne traverse pas `division.notes` (R4).  
- **Fichier** : `pdf_builder.py:253`  
- **Action** : dans `_absolutize_division_paths`, itérer sur `division.notes.values()` et appeler `_absolutize_blocks_paths(note.blocks, ...)`.  
- **Effort** : micro-passe (5 lignes + 1 test).

**B3. Tests manquants T1–T6**  
- **Action** : ajouter les 6 tests identifiés en section 8.4.  
- **Effort** : passe normale.

**B4. Duplication DOI dans `_parse_bibl_identifiers`**  
- **Problème** : un `biblStruct` avec `idno[@type=DOI]` et `ref[@type=DOI]` peut produire deux entrées DOI.  
- **Fichier** : `tei_to_model.py:738`  
- **Action** : après collecte, dédupliquer les identifiants par `(type, value)`.  
- **Effort** : micro-passe (3 lignes + 1 test).

---

### C. À surveiller

**C1. Divergence bibliographie HTML/PDF**  
Les deux parseurs (XSLT et TeiToModelParser) peuvent interpréter différemment certains cas TEI. Surveiller en testant sur des corpus réels.

**C2. `SiteBuilder` : extraction progressive**  
`_render_credit_block` et `_render_zotero_meta` pourraient migrer vers des classes dédiées. À faire quand le besoin de réutilisation se pose.

**C3. Typage des paramètres `blocks`**  
`pdf_builder.py:279` : `blocks` non typé. Annoter `list[BlockNode]` lors d'un passage de maintenance.

**C4. `_parse_bibl_title` avec `level="s"`**  
Risque éditorial faible à ce stade (les corpus Métopes ont généralement des monographies bien structurées), mais à corriger si des cas réels se présentent.

---

### D. À repousser volontairement

**D1. Gestion du colspan/rowspan dans les tableaux**  
Nécessite `\multicolumn{}{}{}` et `\multirow{}{}{}` LaTeX. Non trivial. À traiter quand des corpus réels exigent des tableaux complexes.

**D2. Endnotes comme section distincte**  
Rendu des notes de fin en section séparée en bas de chapitre (avec `\endnote{}` ou une implémentation manuelle). Complexité élevée.

**D3. Refactoring profond de `SiteBuilder`**  
La classe est longue mais cohérente. Aucun besoin urgent de découpage.

**D4. Abstraction du renderer**  
Un protocole Python pour les renderers (HTML, LaTeX, potentiellement EPUB) serait utile si un troisième format sort. À ne pas anticiper.

**D5. `_render_purh_preamble` dans un fichier template**  
Réduirait la longueur du renderer mais ajouterait une dépendance sur des fichiers `.tex.jinja2` ou similaires. Non justifié pour la V1.

---

## 12. Recommandations concrètes de prochaines passes

### Passe 14A — Bugs d'URL dans le renderer PDF
**Périmètre** : `latex_renderer.py`, 2 corrections, 2 nouveaux tests.  
Corriger R1 (`_escape_text` → `_escape_url` pour les liens inline) et R2 (`&` manquant dans `_escape_url`). Ajouter les tests T2.  
**Effort estimé** : 30 minutes.

### Passe 14B — Traçabilité des limitations actuelles
**Périmètre** : `latex_renderer.py` (tableaux), `tei_to_model.py` (notes de fin).  
Ajouter des commentaires LaTeX et/ou warnings pour les cas non gérés (fusions de cellules, notes `place="end"`). Les utilisateurs voient un PDF qui peut être partiellement faux — au moins que ce soit visible.  
**Effort estimé** : 1 heure.

### Passe 14C — Absolutisation des figures dans les notes
**Périmètre** : `pdf_builder.py`, 5 lignes + 1 test.  
Corriger R4.  
**Effort estimé** : 30 minutes.

### Passe 14D — Tests manquants T1–T6
**Périmètre** : `test_pdf_latex.py`, 6 nouveaux tests.  
Couvrir les cas tableau avec cols>1, URL avec &, note end, figure dans note, DOI dupliqué, XML malformé.  
**Effort estimé** : 2 heures.

---

*Rapport produit à partir de la lecture complète de `site_builder.py`, `site_structure.py`, `tei_to_model.py`, `semantic_model.py`, `latex_renderer.py`, `pdf_builder.py`, `tests/test_pdf_latex.py`, `tests/test_pdf_structure.py`, `tests/test_pdf_latex_compile.py`, `tests/test_metopes_bibliography.py`, `tests/conftest.py`. Aucun fichier de code modifié.*
