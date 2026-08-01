# Audit Passe E — Migration du PDF site_builder vers LaTEI

## Résumé exécutif

La migration est faisable mais non triviale. L'obstacle principal est un écart de nommage contractuel : `site_builder.py` expose les artefacts PDF sous des noms fixes (`assets/generated/book.tex`, `assets/generated/book.pdf`) que plusieurs tests vérifient explicitement, tandis que la chaîne LaTEI produit des noms dérivés du stem du fichier source (`{stem}.latei.tex`, `{stem}.latei_mono.pdf`) dans un répertoire de son choix. Un remplacement direct cassera les liens HTML et les tests existants sans travail de remappage. La stratégie la plus sûre est la création d'un adaptateur `site_latei_pdf_export.py` qui appelle `run_reversible_export_for_file` puis copie/renomme les artefacts sous les noms attendus par le site, en conservant les modes stables intacts pendant la transition. Le risque principal est l'ajout de la dépendance `latei_assets/` (répertoire d'images) dans `assets/generated/`, qui n'existe pas dans la chaîne stable et dont le contrôle qualité HTML peut détecter les liens brisés.

---

## Comportement actuel du PDF dans site_builder

La méthode centrale est `_build_pdf_site_artifacts` (lignes 370–410 de `site_builder.py`).

### Mode `pdf_export_mode="none"` (ligne 381)

`_normalized_pdf_export_mode` normalise la valeur et retourne `"none"` si la valeur est inconnue (ligne 413–414). La méthode retourne immédiatement un `PdfSiteArtifacts()` vide : aucun fichier n'est écrit, aucun lien HTML n'est produit.

### Mode `pdf_export_mode="latex"` (lignes 383–410)

- Crée `config.output_assets_dir / "generated"` (soit `<output>/assets/generated/`).
- Si `write_normalized_tei` est `False`, écrit un `book.normalized.xml` dans `generated/` (ligne 387–393).
- Appelle `build_stable_pdf_artifacts(pdf_input_path, generated_dir, compile_pdf=False, …)` (ligne 395–400).
- `PdfBuilder.build_from_normalized_tei` écrit `output_dir / "book.tex"` (ligne 111 de `pdf_builder.py`).
- Retourne `PdfSiteArtifacts(latex_href="assets/generated/book.tex", generated_pdf_href=None)`.
- Le HTML expose un lien de téléchargement LaTeX.

### Mode `pdf_export_mode="latex_pdf"` (lignes 395–410)

- Même chose que `latex` mais `compile_pdf=True`.
- `PdfBuilder` écrit `book.tex`, `book.pdf`, `latex_build.log`, `pdf_build_report.txt` dans `assets/generated/`.
- Retourne `PdfSiteArtifacts(latex_href="assets/generated/book.tex", generated_pdf_href="assets/generated/book.pdf")` si la compilation a réussi ; `generated_pdf_href=None` sinon (ligne 404–409).
- En cas d'échec LuaLaTeX, le rapport mentionne `"Voir : assets/generated/pdf_build_report.txt"` (ligne 432).

### Désactivation par PDF éditeur (lignes 378–379)

Si `theme_assets.pdf_href` est défini (PDF éditeur trouvé dans `assets/pdf/`), la génération est court-circuitée quel que soit le mode demandé.

**Noms produits :**
- `assets/generated/book.tex` (LaTeX stable)
- `assets/generated/book.pdf` (PDF stable, si compilation réussie)
- `assets/generated/book.normalized.xml` (si `write_normalized_tei=False`)
- `assets/generated/pdf_build_report.txt` (rapport PDF builder)
- `assets/generated/latex_build.log` (log LaTeX)

---

## Sorties attendues par le site HTML

### Liens contractuels dans le HTML

Les chemins `"assets/generated/book.tex"` et `"assets/generated/book.pdf"` sont des chaînes littérales codées en dur dans `site_builder.py` (lignes 403 et 405). Ils sont passés directement aux fonctions de rendu HTML `_write_index_page` (ligne 318–319) et `_render_home_downloads` (lignes 756–785). Ces chaînes constituent des noms contractuels : toute migration doit les respecter ou modifier le code HTML de rendu.

### Tests qui vérifient ces chemins (test_smoke.py)

| Ligne | Assertion |
|-------|-----------|
| 327–328 | `assets/generated/book.tex` et `book.pdf` n'existent pas quand un PDF éditeur est présent |
| 352, 354 | `assets/generated/book.pdf` absent du HTML quand un PDF éditeur est présent |
| 369 | `(tmp_path / 'site' / 'assets' / 'generated' / 'book.tex').exists()` |
| 371 | `'href="assets/generated/book.tex"' in index_html` |
| 373 | `book.pdf` absent du site en mode `latex` seul |
| 374 | `'LaTeX généré : assets/generated/book.tex' in report` |
| 387, 389, 390 | idem pour la vérification `citation_pdf_url` absent |
| 410 | `book.tex` existe en mode `latex_pdf` même si LuaLaTeX absent |
| 415 | `'Voir : assets/generated/pdf_build_report.txt' in report` |
| 436 | `book.tex` existe même si `write_normalized_tei=False` |

Ces tests sont nombreux, précis et forment un filet de sécurité dense autour des noms `book.tex` et `book.pdf`.

---

## Sorties actuelles de la chaîne LaTEI

La fonction `run_reversible_export_for_file(xml_path, output_dir)` de `reversible_integration.py` produit les artefacts suivants (ligne 402–422 de `reversible_integration.py`), tous dérivés du stem du fichier source (`stem = source_path.stem`) :

| Artefact | Chemin |
|----------|--------|
| Corps réversible | `{output_dir}/{stem}.reversible.tex` (aussi écrit dans `{stem}.latei_body.tex`) |
| Corps LaTEI (body) | `{output_dir}/{stem}.latei_body.tex` |
| Driver compilable | `{output_dir}/{stem}.latei_main.tex` |
| Macros | `{output_dir}/{stem}.latei_macros.tex` |
| Mapping graphiques | `{output_dir}/{stem}.latei_graphics_map.tex` |
| Mapping titres courants | `{output_dir}/{stem}.latei_running_titles_map.tex` |
| **Monofichier LaTEI (artefact principal)** | `{output_dir}/{stem}.latei.tex` |
| PDF du driver (debug) | `{output_dir}/{stem}.latei.pdf` |
| Log du driver | `{output_dir}/{stem}.latei_build.log` |
| **PDF du monofichier (artefact principal)** | `{output_dir}/{stem}.latei_mono.pdf` |
| Log du monofichier | `{output_dir}/{stem}.latei_mono_build.log` |
| Round-trip XML | `{output_dir}/{stem}.roundtrip.xml` |
| Diagnostics | `{output_dir}/{stem}.roundtrip_diagnostics.txt` |
| Manifeste | `{output_dir}/{stem}.latei_manifest.json` |
| **Répertoire images** | `{output_dir}/latei_assets/images/` |
| Cache TeX | `{output_dir}/latei_tex_cache/` |

**Nommage des images :** Dans `latei_assets.py` (lignes 56, 78–80), les images sont copiées dans `{output_dir}/latei_assets/images/` avec un nom synthétique de la forme `{sha1_12char}-{safe-stem}{ext}`. Le mapping graphique `.tex` contient des chemins relatifs de la forme `latei_assets/images/{hash}-{stem}{ext}` (ligne 80 de `latei_assets.py`).

**Chemins dans le .tex :** Le monofichier n'utilise pas de `\input{}` (garanti par le test `test_monofile_has_no_input_body`). Les chemins d'images sont résolus via `\lateiDeclareGraphic` et doivent être relatifs au répertoire de compilation LuaLaTeX. En mode monofichier, LuaLaTeX est lancé depuis `pdf_path.parent` (ligne 249 de `latei_driver.py`), donc les chemins `latei_assets/images/…` sont relatifs à `output_dir`.

**Artefact primaire :** `primary_latei_path` retourne `latei_monofile_path` (ligne 58 de `reversible_integration.py`) et `primary_pdf_path` retourne `latei_monofile_pdf_path` (ligne 63).

---

## Écarts fonctionnels PDF stable / PDF LaTEI

| Point | PDF stable actuel | PDF LaTEI actuel | Risque migration | Test existant | Test manquant |
|-------|-------------------|------------------|------------------|---------------|---------------|
| **Nom fichier .tex** | `book.tex` (fixe) | `{stem}.latei.tex` (dérivé du XML) | **Fort** — lien HTML cassé | test_smoke.py l.369, 371 | Test vérifiant le nom LaTEI dans le HTML |
| **Nom fichier .pdf** | `book.pdf` (fixe) | `{stem}.latei_mono.pdf` (dérivé du XML) | **Fort** — lien HTML cassé | test_smoke.py l.352, 354 | Test vérifiant le nom PDF LaTEI dans le HTML |
| **Répertoire de sortie** | `assets/generated/` | Libre (passé par appelant) | **Moyen** — à adapter | Indirect | Test qui vérifie le placement dans `assets/generated/` |
| **Mode LaTeX seul (sans PDF)** | `compile_pdf=False` dans `PdfBuilder` | Non prévu : `compile_latei_pdf` est toujours appelé | **Moyen** — la chaîne LaTEI compile toujours le PDF si LuaLaTeX est disponible | test_smoke.py l.373 | Test mode `latex` isolé pour LaTEI |
| **LuaLaTeX absent** | `PdfBuilder` retourne `success=False` gracieusement ; `.tex` toujours produit | `compile_latei_pdf` produit un log et retourne `success=False` gracieusement ; monofichier `.tex` toujours produit | **Faible** — les deux gèrent bien | test_smoke.py l.410, 415 | Test LaTEI avec moteur absent dans contexte site |
| **Images** | Absolues dans le `.tex` (l.124 `pdf_builder.py` appelle `_absolutize_figure_paths`) | Relatives via `latei_assets/images/` dans `output_dir` | **Fort** — si `output_dir` n'est pas le dossier de compilation, les images seront introuvables | Indirect via tests monofichier | Test copie images dans `assets/generated/latei_assets/` |
| **Log de compilation** | `assets/generated/latex_build.log` (fixe) | `{stem}.latei_mono_build.log` | **Moyen** — le rapport site référence `pdf_build_report.txt` non `latei_mono_build.log` | test_smoke.py l.415 | Test nom log dans rapport site |
| **Rapport PDF** | `assets/generated/pdf_build_report.txt` (rapport structuré) | Pas d'équivalent : log brut uniquement | **Moyen** — le rapport site référence `pdf_build_report.txt` | test_smoke.py l.415 | Test présence rapport LaTEI dans rapport site |
| **Métadonnées** | Extraites du XML normalisé par `parse_normalized_tei` | Extraites par `extract_latei_metadata` depuis le `teiHeader` | **Faible** — les deux utilisent le même XML | test_latei_real_metopes_fixture.py | — |
| **Table des matières** | Via LaTeX (paquets standard) | `\tableofcontents` dans le monofichier (l.87 `latei_driver.py`) | **Faible** — les deux l'incluent | test_monofile_has_table_of_contents | — |
| **Page de titre** | Via le style PURH | `_title_page` dans `latei_driver.py` (l.304) | **Faible** — les deux ont une page de titre | Indirect | Test contenu page de titre dans PDF |
| **Titres courants** | Via style LaTeX | Via `latei_running_titles_map.tex` | **Faible** — géré | test_latei_monofile.py (indirect) | — |
| **Notes** | Via `\footnote` standard | Via `\teiNote` (macros LaTEI) | **Faible** | test_latei_monofile.py (structure) | — |
| **Bibliographie** | Via modèle sémantique | Via LaTEI réversible | **Moyen** — couverture incomplète connue | test_real_metopes fixtures | Test bibliographie complète |
| **Tableaux** | Via modèle sémantique | Via LaTEI réversible | **Moyen** — idem | test_real_metopes fixtures | Test tableaux complets |
| **Liens internes** | Pas résolus en PDF (pas de `\hyperref`) | Via macros LaTEI | **Faible** | — | — |
| **Citation PDF URL (meta Zotero)** | Renseignée avec `assets/generated/book.pdf` | Doit pointer vers le nouveau chemin | **Fort** | test_smoke.py l.352 | Test citation_pdf_url avec chemin LaTEI |

---

## Risques techniques

- **Fort — Noms de fichiers contractuels** : Les tests `test_smoke.py` vérifient explicitement `assets/generated/book.tex` et `assets/generated/book.pdf` à 10+ endroits. Un remplacement direct sans renommage casse tous ces tests.
- **Fort — Images et répertoire `latei_assets/`** : Les images LaTEI sont copiées dans `latei_assets/images/` avec des noms SHA1. En contexte site, ce répertoire doit être à l'intérieur de `assets/generated/` pour que LuaLaTeX compile depuis ce dossier. Si on déplace le `.tex`, les chemins relatifs deviennent invalides.
- **Moyen — Mode `latex` sans compilation** : La chaîne LaTEI ne distingue pas nativement "générer le monofichier sans compiler". `compile_latei_pdf` est toujours appelé ; si LuaLaTeX est absent, il retourne `success=False` silencieusement. Il faudrait un flag `compile_pdf=False` équivalent côté LaTEI.
- **Moyen — Rapport de build** : `site_builder.py` référence `assets/generated/pdf_build_report.txt` (ligne 432) dans le rapport textuel. La chaîne LaTEI ne produit pas ce fichier ; elle produit un log brut. Le test `test_smoke.py` ligne 415 vérifie cette référence exacte.
- **Moyen — test_stable_pdf_export_adapter.py** : Ce fichier (test `test_site_builder_does_not_import_pdf_builder_directly`) vérifie que `site_builder.py` n'importe pas directement `PdfBuilder`. Si on y branche LaTEI directement, il faut s'assurer de ne pas briser cette séparation.
- **Faible — LuaLaTeX absent** : Les deux chaînes gèrent gracieusement l'absence de moteur. Pas de risque de régression HTML.
- **Faible — Couverture de tests LaTEI** : Les tests LaTEI (`test_latei_monofile.py`, `test_latei_output_manifest.py`, `test_latei_real_metopes_fixture.py`) couvrent la production d'artefacts mais pas leur intégration dans le contexte `site_builder`. Des tests d'intégration sont manquants.

---

## Stratégies de migration

### Stratégie 1 — Remplacement direct

`site_builder.py` appelle `run_reversible_export_for_file` directement à la place de `build_stable_pdf_artifacts`.

**Avantages :** Simple conceptuellement. Conforme à la doctrine monofichier dès Passe E.

**Problèmes :**
1. Les noms de fichiers produits par LaTEI (`{stem}.latei.tex`, `{stem}.latei_mono.pdf`) ne correspondent pas aux noms attendus par le site (`book.tex`, `book.pdf`). Il faudrait soit modifier `_output_paths` dans `reversible_integration.py` (risque de casser d'autres tests), soit renommer les fichiers après coup dans `site_builder.py`.
2. `run_reversible_export_for_file` ne distingue pas le mode "latex seul" du mode "latex+pdf". Il compile toujours (si LuaLaTeX disponible). Il faut gérer ce cas.
3. Le répertoire `latei_assets/` doit être placé correctement pour que LuaLaTeX trouve les images.
4. `PdfBuildResult` (type retourné actuellement) est remplacé par `ReversibleExportResult` : tous les types dans `PdfSiteArtifacts.build_result` doivent être mis à jour.
5. Les tests `test_stable_pdf_export_adapter.py` vérifient l'isolation ; il faudra les adapter.
6. La ligne 432 du rapport (`pdf_build_report.txt`) n'a plus d'équivalent.

**Verdict :** Stratégie risquée et lourde pour un remplacement direct. Ne pas faire en première passe.

### Stratégie 2 — Adaptateur LaTEI compatible site (`site_latei_pdf_export.py`)

Créer un nouveau module `site_latei_pdf_export.py` qui :
1. Appelle `run_reversible_export_for_file(xml_path, generated_dir)`.
2. Copie/renomme `{stem}.latei.tex` → `book.tex` et `{stem}.latei_mono.pdf` → `book.pdf` dans `generated_dir`.
3. Crée un `pdf_build_report.txt` synthétique à partir des messages LaTEI.
4. Retourne un objet compatible avec ce que `_build_pdf_site_artifacts` attend (ou un nouveau type `LateiPdfSiteResult` adapté).

**Avantages :**
- Préserve tous les noms contractuels attendus par le HTML et les tests.
- N'impose aucune modification à `reversible_integration.py`.
- Isolation propre : `site_builder.py` n'importe qu'un adaptateur, conformément à l'architecture de la Passe D.
- Peut coexister avec `stable_pdf_export.py` pendant la transition.
- Les tests existants continuent de passer sans modification.
- Le répertoire `latei_assets/` peut être conservé dans `assets/generated/` (LuaLaTeX est lancé depuis `generated_dir`).

**Inconvénients :**
- Nécessite une copie de fichiers (légère opération fichier).
- Deux niveaux d'adaptateurs pendant la transition (l'un stable, l'un LaTEI).
- Il faut mettre en legacy `stable_pdf_export.py` explicitement après validation.

**Effort estimé :** Moyen (1 nouveau fichier, 1 modification de `site_builder.py`, mise à jour des tests d'adaptateur).

### Stratégie 3 — Double mode temporaire

Ajouter `pdf_export_mode="latei"` et `pdf_export_mode="latei_pdf"` sans toucher aux modes stables existants dans `site_builder.py` et dans la GUI.

**Avantages :**
- Permet une comparaison côte à côte PDF stable vs PDF LaTEI.
- Transition progressive sans risque de régression.

**Inconvénients :**
- Multiplication des modes dans la GUI (5 options au lieu de 3).
- La logique dans `_normalized_pdf_export_mode` (ligne 412–414) doit gérer 5 valeurs.
- Complexité accrue pour une phase temporaire.
- Risque de laisser des modes morts en production.
- Pertinence éditoriale limitée : l'éditrice n'a pas besoin de choisir entre deux chaînes PDF.

**Verdict :** Utile pour des tests de validation interne, mais ne doit pas aller en production comme interface permanente.

---

## Stratégie recommandée

**Stratégie 2 — Adaptateur LaTEI compatible site (`site_latei_pdf_export.py`).**

**Justification basée sur le code réel :**

1. Les noms `book.tex` et `book.pdf` dans `assets/generated/` sont vérifiés à 10+ endroits dans `test_smoke.py` (lignes 327, 328, 352, 354, 369, 371, 373, 374, 387, 389, 390, 410, 415, 436). Un adaptateur qui recopie sous ces noms préserve l'intégralité du filet de tests sans modification.

2. La Passe D a déjà établi le pattern : `site_builder.py` n'importe que l'adaptateur `stable_pdf_export`, jamais `PdfBuilder` directement (vérifié par `test_stable_pdf_export_adapter.py`). La Passe E doit suivre le même modèle et créer `site_latei_pdf_export.py` comme nouvel adaptateur.

3. Le répertoire `latei_assets/` créé dans `generated_dir` (= `assets/generated/`) sera accessible à LuaLaTeX lors de la compilation puisque `compile_latei_pdf` exécute LuaLaTeX depuis `pdf_path.parent` (ligne 249 de `latei_driver.py`), qui sera `assets/generated/`.

4. La plus sûre pour les liens HTML : aucun changement de chemin dans les templates HTML.

5. La plus propre pour mettre en legacy ensuite : `stable_pdf_export.py` peut passer en legacy dès que l'adaptateur LaTEI est validé, sans modifier `site_builder.py`.

---

## Plan de micro-passes E

### E1 — Créer l'adaptateur `site_latei_pdf_export.py` avec retour compatible

**Objectif :** Créer `purh_site/site_latei_pdf_export.py` qui appelle `run_reversible_export_for_file`, copie les artefacts principaux sous les noms `book.tex` / `book.pdf` et retourne un objet `LateiSitePdfResult` (ou réutilise `PdfBuildResult` comme façade) exploitable par `_build_pdf_site_artifacts`.

**Fichiers :**
- `purh_site/site_latei_pdf_export.py` (à créer)

**Tests :**
- `tests/test_site_latei_pdf_export_adapter.py` (à créer) : vérifie que l'adaptateur copie `book.tex` et `book.pdf`, crée `pdf_build_report.txt`, gère l'absence de LuaLaTeX.

**Critère :** L'adaptateur peut être appelé avec un XML minimal et produit `book.tex` dans le répertoire cible, même sans LuaLaTeX.

**Risque :** Faible — module isolé, aucune modification de code existant.

### E2 — Brancher l'adaptateur dans `site_builder.py` derrière un nouveau mode

**Objectif :** Ajouter le support de `pdf_export_mode="latei"` et `"latei_pdf"` dans `_normalized_pdf_export_mode` et `_build_pdf_site_artifacts`, en déléguant à `site_latei_pdf_export.py`. Laisser les modes `"latex"` et `"latex_pdf"` intacts.

**Fichiers :**
- `purh_site/site_builder.py` (modifier `_normalized_pdf_export_mode` et `_build_pdf_site_artifacts`)
- `purh_site/config.py` (valeurs de mode inchangées, documentation seulement)

**Tests :**
- Nouveaux tests dans `tests/test_smoke.py` ou fichier séparé : mode `"latei"` produit `book.tex` dans `assets/generated/`, mode `"latei_pdf"` produit `book.pdf` si LuaLaTeX disponible.
- Vérifier que les tests existants des modes stables passent toujours.

**Critère :** `SiteBuilder().build_from_master(xml_path, BuildConfig(pdf_export_mode="latei", …))` produit `assets/generated/book.tex` avec le contenu LaTEI monofichier.

**Risque :** Moyen — modification de `site_builder.py`, risque de régresser les modes stables.

### E3 — Mettre à jour la GUI pour exposer les modes LaTEI

**Objectif :** Ajouter les options `"latei"` et `"latei_pdf"` dans la GUI (`gui.py`), ou remplacer les labels existants des modes stables par les modes LaTEI (selon décision éditoriale).

**Fichiers :**
- `purh_site/gui.py` (section `_add_pdf_export_controls`, ligne 195–203)

**Tests :**
- Test fonctionnel GUI (non automatisable facilement) ou test unitaire sur `_make_build_config`.

**Critère :** La GUI permet de sélectionner `"latei"` ou `"latei_pdf"` et le `BuildConfig` transmis contient la bonne valeur.

**Risque :** Faible — interface uniquement, pas de logique métier.

### E4 — Valider la compilation PDF LaTEI dans le contexte site (avec images)

**Objectif :** Tester de bout en bout la compilation LuaLaTeX avec un XML contenant des figures, vérifier que `latei_assets/images/` est correctement placé dans `assets/generated/` et que LuaLaTeX trouve les images.

**Fichiers :**
- `tests/test_smoke_latei_pdf.py` (à créer, marqué `slow` ou `skipif lualatex absent`)

**Tests :**
- Test avec fixture `heraldique_ii.book.normalized.xml` : `pdf_export_mode="latei_pdf"`, vérification existence `book.pdf`, absence d'erreurs image dans le log.

**Critère :** `assets/generated/book.pdf` existe et est non vide, log LuaLaTeX sans erreur d'image manquante.

**Risque :** Moyen — dépendance LuaLaTeX, chemins relatifs images.

### E5 — Mettre en legacy la chaîne PDF stable

**Objectif :** Déplacer `stable_pdf_export.py`, `pdf_builder.py`, `latex_renderer.py`, `semantic_model.py`, `tei_to_model.py` vers `purh_site/legacy/`. Adapter les imports. Vérifier que les tests d'adaptateur passent encore.

**Fichiers :**
- Déplacements dans `purh_site/legacy/`
- Mise à jour des imports dans `site_builder.py` si les modes stables sont conservés en legacy
- Mise à jour de `tests/test_stable_pdf_export_adapter.py`

**Critère :** Les tests des modes `"latex"` et `"latex_pdf"` (stables) passent encore via l'import legacy. Les modes LaTEI sont le chemin principal.

**Risque :** Moyen — risque de casser les tests d'adaptateur et les imports si des modules externes importent directement les anciens chemins.

---

## Tests à créer ou adapter

| Test | Ce qu'il prouve | Dépendance LuaLaTeX | Vitesse |
|------|-----------------|---------------------|---------|
| `test_site_latei_pdf_export_adapter.py::test_adapter_copies_book_tex` | L'adaptateur copie `{stem}.latei.tex` → `book.tex` dans le répertoire cible | Non | Rapide |
| `test_site_latei_pdf_export_adapter.py::test_adapter_creates_pdf_build_report` | `pdf_build_report.txt` est créé même sans LuaLaTeX | Non | Rapide |
| `test_site_latei_pdf_export_adapter.py::test_adapter_returns_tex_path_as_book_tex` | Le chemin `tex_path` retourné est `book.tex` | Non | Rapide |
| `test_site_latei_pdf_export_adapter.py::test_adapter_graceful_without_lualatex` | `success=False`, `book.tex` présent, `book.pdf` absent | Non (simule moteur absent) | Rapide |
| `test_smoke.py::test_latei_mode_generates_book_tex_in_assets_generated` | Mode `"latei"` produit `assets/generated/book.tex` | Non | Rapide |
| `test_smoke.py::test_latei_pdf_mode_generates_book_pdf_when_lualatex_available` | Mode `"latei_pdf"` produit `assets/generated/book.pdf` | Oui | Lent |
| `test_smoke.py::test_latei_mode_html_link_is_correct` | `href="assets/generated/book.tex"` dans le HTML | Non | Rapide |
| `test_smoke.py::test_stable_modes_still_work_after_e2` | Les modes `"latex"` et `"latex_pdf"` stables ne régressent pas | Non | Rapide |
| `test_smoke_latei_pdf.py::test_latei_pdf_with_figures_finds_images` | LuaLaTeX trouve les images dans `latei_assets/images/` | Oui | Lent |
| `test_stable_pdf_export_adapter.py` (à adapter) | Vérifier que le test d'isolation `test_site_builder_does_not_import_pdf_builder_directly` passe encore | Non | Rapide |

---

## Conditions pour mise en legacy de la chaîne PDF stable

### `stable_pdf_export.py`

Peut aller en legacy quand :
- `site_builder.py` n'importe plus `build_stable_pdf_artifacts` ni `PdfBuildResult` depuis ce module.
- Les modes `"latex"` et `"latex_pdf"` dans `_normalized_pdf_export_mode` sont soit supprimés, soit rebranché sur l'adaptateur LaTEI.
- Le test `test_stable_pdf_export_adapter.py::test_site_builder_does_not_import_pdf_builder_directly` passe avec le nouveau chemin.

### `pdf_builder.py`

Peut aller en legacy quand :
- `stable_pdf_export.py` est en legacy ou ne l'importe plus.
- Aucun test hors legacy ne l'importe directement.

### `latex_renderer.py`

Peut aller en legacy quand :
- `pdf_builder.py` est en legacy.
- Aucun import direct depuis le code de production.

### `semantic_model.py`

Peut aller en legacy quand :
- `latex_renderer.py` et `tei_to_model.py` sont en legacy.
- Aucun test de production ne l'importe.

### `tei_to_model.py`

Peut aller en legacy en même temps que `semantic_model.py`.

### Ce qui ne doit PAS partir en legacy après Passe E

- `reversible_integration.py` — c'est le nouveau chemin de production PDF.
- `latei_driver.py`, `latei_assets.py`, `latei_metadata.py`, `latei_preamble.py`, `latei_running_titles.py` — tous nécessaires à la chaîne LaTEI.
- `reversible/` (tout le module) — cœur réversible.
- `site_builder.py` lui-même — il reste le chef d'orchestre du site statique.
- `stable_pdf_export.py` ne peut pas partir en legacy tant que les modes `"latex"` et `"latex_pdf"` sont encore actifs dans le code et utilisés par des utilisateurs ou des tests.

---

## Verdict final

**Faut-il remplacer directement `stable_pdf_export` par LaTEI ?**
Non. Un remplacement direct sans adaptateur casse les noms contractuels (`book.tex`, `book.pdf`) vérifiés par 10+ assertions dans `test_smoke.py` et les liens HTML du site.

**Faut-il créer un adaptateur LaTEI compatible site ?**
Oui. C'est la stratégie recommandée (Stratégie 2). Un module `site_latei_pdf_export.py` copie les artefacts LaTEI sous les noms attendus par le site, sans modifier ni `reversible_integration.py` ni les templates HTML.

**Faut-il conserver temporairement un double mode ?**
Oui, pendant la transition (E2) : les modes `"latex"` / `"latex_pdf"` stables restent actifs ; les modes `"latei"` / `"latei_pdf"` sont ajoutés. La suppression des modes stables intervient en E5 seulement, après validation complète.

**Quelle est la première micro-passe sûre ?**
E1 — Créer `site_latei_pdf_export.py` en isolation totale. Aucun fichier existant n'est modifié. Le risque est nul.

**Qu'est-ce qu'il ne faut surtout pas faire maintenant ?**
- Ne pas modifier `_output_paths` dans `reversible_integration.py` pour renommer les artefacts LaTEI en `book.tex` / `book.pdf` : cela casserait les tests `test_latei_output_manifest.py` et `test_reversible_integration.py` qui vérifient les noms avec `{stem}.latei.tex` et `{stem}.latei_mono.pdf`.
- Ne pas supprimer `stable_pdf_export.py` avant que l'adaptateur LaTEI soit validé en production.
- Ne pas modifier `site_builder.py` avant que l'adaptateur E1 soit stable et testé.
- Ne pas compiler le PDF LaTEI de manière inconditionnelle dans le contexte site sans gérer le mode `"latei"` (sans PDF) séparément du mode `"latei_pdf"` (avec PDF).


---

## Passe E1 réalisée

Date : 2026-06-23

**Nouveau module créé : `purh_site/site_latei_pdf_export.py`**

- Non branché dans `site_builder.py` — le comportement du site n'a pas changé.
- Traduit les artefacts natifs LaTEI vers les noms contractuels du site :
  - `{stem}.latei.tex` → `book.tex`
  - `{stem}.latei_manifest.json` → `book.latei_manifest.json`
  - `{stem}.latei_mono.pdf` → `book.pdf` (seulement si `compile_pdf=True` et PDF produit)
- Écrit toujours `pdf_build_report.txt` avec une synthèse (XML source, chemins natifs, chemins site, message LaTEI).
- Les artefacts natifs LaTEI (`{stem}.latei.tex`, `{stem}.latei_manifest.json`, etc.) restent en place.
- `latei_assets/` n'est pas déplacé.
- Le paramètre `latex_engine` est accepté pour symétrie d'API avec `stable_pdf_export`, mais pas encore transmis à `run_reversible_export_for_file`.

**Nouveau test : `tests/test_site_latei_pdf_export_adapter.py`** (8 tests)

- Test 1 : importabilité
- Test 2 : mode LaTeX seul — `book.tex`, `book.latei_manifest.json`, `pdf_build_report.txt` produits
- Test 3 : `book.tex` contient `\begin{lateiDocument}` et pas de `\input{`
- Test 4 : rapport contient les champs attendus
- Test 5 : cohérence des champs du résultat
- Test 6 : artefacts natifs non supprimés
- Test 7 : mode PDF conditionnel (`compile_pdf=True`) — `book.pdf` copié si produit ; sinon dégradation propre
- Test 8 : `site_builder.py` n'importe pas encore `site_latei_pdf_export`

**Tests lancés :**

- `test_site_latei_pdf_export_adapter.py` : 8 passed (86 s — dépend de la génération LaTEI, pas de lualatex)
- `test_stable_pdf_export_adapter.py`, `test_smoke.py`, `test_site_quality_report.py` : 33 passed

---

## Passe E2 réalisée

Date : 2026-06-23

**Modes LaTEI branchés dans `site_builder.py`**

- `pdf_export_mode="latei"` et `"latei_pdf"` sont désormais acceptés par `_normalized_pdf_export_mode`.
- `_build_pdf_site_artifacts` délègue aux modes LaTEI via `build_site_latei_pdf_artifacts` (adaptateur E1).
- Les modes `"latex"` et `"latex_pdf"` stables restent **inchangés** et continuent de passer.
- Le GUI n'est **pas encore modifié** (prévu en E3).
- `site_builder.py` n'importe **pas** `PdfBuilder` directement : isolation préservée.
- Le site continue d'exposer `assets/generated/book.tex` et `assets/generated/book.pdf` sous les mêmes noms contractuels.

**Modifications apportées :**

- `purh_site/site_latei_pdf_export.py` : champ `success` ajusté — vaut `pdf_copied` quand `compile_pdf=True`, `result.success` sinon. Ceci garantit que `_pdf_site_report_lines` déclenche le WARNING correct lorsque `latei_pdf` a été demandé mais LuaLaTeX était absent.
- `purh_site/site_builder.py` :
  - Import ajouté : `from .site_latei_pdf_export import SiteLateiPdfExportResult, build_site_latei_pdf_artifacts`
  - `PdfSiteArtifacts.build_result` : type étendu à `PdfBuildResult | SiteLateiPdfExportResult | None`
  - `_normalized_pdf_export_mode` : accepte `"latei"` et `"latei_pdf"`
  - `_build_pdf_site_artifacts` : branche LaTEI ajoutée avant la branche stable
- `tests/test_site_latei_pdf_export_adapter.py` : test 8 inversé — vérifie maintenant que `site_builder.py` **importe** `site_latei_pdf_export`

**Note sur `latex_engine` :** La chaîne LaTEI gère son propre moteur et n'honore pas encore le paramètre `latex_engine` de `BuildConfig`. Ce paramètre est transmis pour symétrie d'API mais sans effet sur `run_reversible_export_for_file`. Le test 3 est donc adaptatif (observe le résultat réel plutôt que de simuler l'absence de LuaLaTeX via un faux moteur).

**Nouveau fichier de tests : `tests/test_site_latei_pdf_mode.py`** (6 tests)

- Test 1 : mode `latei` produit `book.tex`, `book.latei_manifest.json`, `pdf_build_report.txt` ; lien HTML correct ; rapport de build correct
- Test 2 : `book.tex` est un monofichier LaTEI (`\begin{lateiDocument}`, pas de `\input{`)
- Test 3 : mode `latei_pdf` — adaptatif selon disponibilité de LuaLaTeX ; invariants communs toujours vérifiés *(remplacé en E2-bis — voir ci-dessous)*
- Test 4a : mode stable `latex` toujours fonctionnel
- Test 4b : mode stable `none` toujours fonctionnel
- Test 5 : PDF éditeur court-circuite les modes LaTEI comme les modes stables

**Tests lancés :**

- `test_site_latei_pdf_mode.py` : 6 passed
- `test_stable_pdf_export_adapter.py` + `test_site_latei_pdf_export_adapter.py` : 12 passed
- `test_smoke.py` : 22 passed
- `test_site_quality_report.py` : 7 passed

---

## Passe E2-bis réalisée

Date : 2026-06-23

**Contexte :** La limite documentée en E2 — `latex_engine` accepté mais non transmis à `run_reversible_export_for_file` — est corrigée. La chaîne LaTEI honore désormais `BuildConfig.latex_engine` de bout en bout.

**Modifications apportées :**

- `purh_site/reversible_integration.py` :
  - Signature de `run_reversible_export_for_file` étendue avec `*, latex_engine: str = "lualatex"` (paramètre keyword-only optionnel, rétrocompatible).
  - Les deux appels à `compile_latei_pdf` transmettent désormais `latex_engine=latex_engine` : compilation debug du driver fragmenté et compilation principale du monofichier.
- `purh_site/site_latei_pdf_export.py` :
  - L'appel à `run_reversible_export_for_file` transmet `latex_engine=latex_engine`.
  - Commentaire "non transmis" supprimé.
- `tests/test_site_latei_pdf_mode.py` :
  - Test adaptatif (Test 3) remplacé par deux tests déterministes :
    - `test_latei_pdf_mode_is_robust_without_lualatex` : utilise `latex_engine="moteur-latei-inexistant"`, vérifie `book.tex` présent, `book.pdf` absent, WARNING dans le rapport.
    - `test_latei_pdf_mode_produces_pdf_when_lualatex_available` : conditionnel (`pytest.skip` si lualatex absent), vérifie `book.pdf` présent et non vide.

**Tests lancés :**

- `test_site_latei_pdf_mode.py` : 7 passed (dont le nouveau test déterministe + le conditionnel lualatex)
- `test_site_latei_pdf_export_adapter.py` + `test_reversible_integration.py` : 20 passed
- `test_latei_monofile.py` + `test_latei_monofile_restore.py` : 25 passed

---

## Passe E3 réalisée

Date : 2026-06-23

**Contexte :** Les modes `"latei"` et `"latei_pdf"` étaient déjà fonctionnels dans `site_builder.py` (E2) et `latex_engine` était correctement transmis (E2-bis). E3 les expose dans le GUI.

**Modifications apportées :**

- `purh_site/gui.py` — `_add_pdf_export_controls` :
  - Layout horizontal (3 options en ligne) → layout vertical en deux sections.
  - Section **"Chaîne stable (legacy) :"** : conserve les 3 modes existants (`none`, `latex`, `latex_pdf`) avec leurs libellés inchangés.
  - Section **"Chaîne LaTEI monofichier :"** : ajoute 2 nouveaux modes :
    - `"Monofichier LaTEI seul (book.tex)"` → `pdf_export_mode="latei"`
    - `"Monofichier LaTEI + PDF compilé (book.tex + book.pdf)"` → `pdf_export_mode="latei_pdf"`
  - Le mode par défaut (`"none"`) est **inchangé**.
  - `_make_build_config` est **inchangé** : lit `self.pdf_export_mode_var.get()` sans filtrage, transmet la valeur telle quelle à `BuildConfig`.

- `tests/test_latei_gui_preflight.py` :
  - Import ajouté : `from purh_site.config import BuildConfig`
  - 4 tests ajoutés :
    - `test_gui_exposes_latei_pdf_mode_values` : vérifie que `"latei"` et `"latei_pdf"` apparaissent dans le source GUI.
    - `test_gui_all_five_pdf_modes_present` : vérifie les 5 valeurs (`none`, `latex`, `latex_pdf`, `latei`, `latei_pdf`).
    - `test_build_config_accepts_latei_mode` : `BuildConfig(pdf_export_mode="latei")` sans erreur.
    - `test_build_config_accepts_latei_pdf_mode` : `BuildConfig(pdf_export_mode="latei_pdf")` sans erreur.

**Tests lancés :**

- `test_latei_gui_preflight.py` : 9 passed (5 existants + 4 nouveaux)
- `test_site_latei_pdf_mode.py` : 7 passed (non-régression)

---

## Passe E4 réalisée

Date : 2026-06-23

**Contexte :** Point le plus fragile identifié par l'audit initial — les chemins d'images relatifs et le répertoire `latei_assets/`. E4 valide que tout fonctionne correctement dans le contexte site avec de vraies images.

**Point technique clé — résolution des chemins images :**

L'adaptateur passe le TEI normalisé (`site/book.normalized.xml`) à `run_reversible_export_for_file`. `latei_assets.py` résout les `graphic/@url` relativement à ce fichier (`base_dir = site/`). La stratégie du test est :

- `assets_dir = tmp_path / "assets"` → copié dans `site/assets/` par `_copy_user_assets` (avant la chaîne LaTEI)
- XML source avec `url="assets/images/test.png"` → résout `tmp_path/assets/images/test.png` depuis le XML source, et `site/assets/images/test.png` depuis le TEI normalisé ✅
- La copie `_copy_user_assets` précède l'appel LaTEI, donc l'image est déjà en place au moment de la résolution ✅

**Résultats confirmés par les tests :**

- `latei_assets/images/` est bien créé dans `assets/generated/` (pas dans `assets/` ni ailleurs)
- Les images sont copiées avec noms sha1 (`{sha1_12char}-{safe-stem}.png`)
- `book.tex` contient `latei_assets/images/{sha1}-{name}.png` — chemins relatifs valides depuis `generated/`
- LuaLaTeX s'exécute depuis `pdf_path.parent` = `generated/`, donc il trouve `latei_assets/images/` ✅
- `book.pdf` compile avec image si LuaLaTeX est disponible
- L'absence d'image ne casse pas le mode `latei` (warning dans le rapport, pas d'erreur)

**Nouveau fichier de tests : `tests/test_site_latei_pdf_assets.py`** (4 tests)

- Test 1 : `latei_assets/images/` créé et image copiée en mode `latei`
- Test 2 : `book.tex` référence `latei_assets/images/` avec chemins valides
- Test 3 : `latei_pdf` compile `book.pdf` non vide avec image (conditionnel lualatex)
- Test 4 : mode `latei` sans image ne plante pas (non-régression)

**Tests lancés :**

- `test_site_latei_pdf_assets.py` : 4 passed
- `test_site_latei_pdf_mode.py` + `test_site_latei_pdf_export_adapter.py` : 15 passed
- `test_site_quality_report.py` : 7 passed
