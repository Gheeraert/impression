# Audit technique complet du dépôt Impressions

Date de l'audit : 12 juillet 2026  
Branche auditée : `main` (`08beae6 Nettoyage`)  
État Git initial : propre (`git status --short` vide)

## 1. Verdict global

Le dépôt contient une base réelle et déjà utile pour produire un site statique depuis du TEI Métopes : les modules sont lisibles, la chaîne HTML fonctionne sur un gros fixture réel, le normaliseur vérifie désormais des points d'intégrité importants, et la projection LaTEI conserve beaucoup mieux le contenu XML que les anciennes chaînes PDF appauvrissantes.

Le niveau de confiance reste toutefois moyen pour un vrai livre éditorial complet. Le site généré est exploitable comme prévisualisation structurée, mais la stratégie de ressources n'est pas encore assez robuste pour garantir la publication autonome d'un volume iconographique. La chaîne PDF est prometteuse, mais elle ne doit pas être considérée comme une mise en page éditoriale fiable : elle compile, mais avec images absentes, avertissements typographiques nombreux, une seule passe LaTeX, et une table des matières placée après le corps.

Le principal risque n'est pas une architecture inutilement complexe ; c'est plutôt l'existence de plusieurs couches partiellement convergentes : TEI normalisé, XSLT HTML, modèle LaTEI réversible, packaging LaTEI, adaptation site/PDF, GUI. Ces couches ont chacune des tests, mais les tests donnent parfois une impression trop rassurante parce qu'ils valident surtout les artefacts produits, pas leur complétude éditoriale ni les logs.

En l'état, le dépôt peut servir à générer des prototypes et des sorties de travail. Il n'est pas encore assez fiable pour produire sans contrôle humain un livre Métopes complet avec HTML, XML, LaTEI et PDF éditorialement satisfaisants.

Points forts :

- code Python globalement simple, sans base de données ni infrastructure inutile ;
- séparation assez nette entre chargement TEI, normalisation, structure du site, rendu HTML, LaTEI/PDF et GUI ;
- normaliseur récent plus sérieux sur les `xml:id` et les références locales ;
- projection réversible qui préserve `text`, `tail`, ordre des enfants, attributs et éléments inconnus ;
- génération réelle du fixture Métopes `heraldique_ii.book.normalized.xml` réussie : 17 pages HTML, LaTEI, PDF, round-trip sans diagnostic.

Principaux risques :

- images et assets non garantis dans les sorties finales ;
- PDF considéré comme réussi alors que les images sont absentes et que les logs signalent des défauts ;
- XInclude manuel sans protection contre cycles, `xpointer`, fallback ni conservation complète du contexte de fichier ;
- GUI synchrone : génération longue dans le thread Tk principal ;
- packaging absent (`pyproject.toml` inexistant, `requirements.txt` minimal) malgré l'objectif wheel/Nuitka ;
- tests massifs mais fragiles à l'environnement temporaire et parfois trop permissifs.

## 2. Commandes et vérifications réalisées

Commandes d'inventaire :

```powershell
Get-ChildItem -Force
git status --short
git status --branch --short
rg --files
Get-Content requirements.txt
Get-Content README.md
Get-ChildItem purh_site -Recurse -File
git log --oneline --decorate -n 12 --stat
where.exe lualatex
where.exe pandoc
```

Résultats clés :

- branche `main...origin/main`, état initial propre ;
- `lualatex` disponible : `C:\texlive\2025\bin\windows\lualatex.exe` ;
- `pandoc` disponible : `C:\Program Files\Pandoc\pandoc.exe` ;
- pas de `pyproject.toml` ;
- `requirements.txt` contient seulement `lxml>=5.0` ;
- de nombreux `.pyc` existent pour des modules qui ne sont plus présents en source (`pdf_builder`, `semantic_model`, `tei_to_model`, `latex_renderer`, etc.).

Tests lancés :

```powershell
python -m pytest tests/ -q
python -m pytest tests/ -q --basetemp tests/_runtime/pytest-audit-codex -p no:cacheprovider
python -m pytest tests/test_reversible_roundtrip.py tests/test_reversible_table_elements.py tests/test_french_typography.py -q -p no:cacheprovider
python -m pytest tests/test_latei_rend_macro_rendering.py -q -p no:cacheprovider
python -m pytest tests/test_normalizer_integrity.py -q --basetemp tests/_runtime/pytest-normalizer-audit -p no:cacheprovider
```

Bilan tests :

- suite complète sans `--basetemp` : `287 passed, 2 warnings, 251 errors`, erreurs dues au `PermissionError` sur `C:\Users\Blais\AppData\Local\Temp\pytest-of-Blais` ;
- suite complète avec `--basetemp` sous `tests/_runtime` : même volume d'erreurs, puis `PermissionError` au nettoyage/scandir du basetemp ; résultat non utilisable comme verdict fonctionnel ;
- tests ciblés `test_reversible_roundtrip.py`, `test_reversible_table_elements.py`, `test_french_typography.py` : 26 tests passés, 1 erreur d'environnement sur le seul test utilisant `tmp_path` ;
- `test_latei_rend_macro_rendering.py` : 3 tests passés, 3 erreurs d'environnement sur `tmp_path_factory` ;
- `test_normalizer_integrity.py` : 20 tests passés avant erreurs/arrêt de session lié au basetemp.

Génération réelle lancée :

```powershell
python -c "from pathlib import Path; from purh_site.site_builder import SiteBuilder; from purh_site.config import BuildConfig; out=Path('tests/_runtime/audit_real_site'); out.mkdir(parents=True, exist_ok=True); r=SiteBuilder().build_from_master(Path('tests/fixtures/metopes/heraldique_ii.book.normalized.xml'), BuildConfig(output_dir=out, pdf_export_mode='latei_pdf')); print(r); print((out/'build_report.txt').read_text(encoding='utf-8')[:4000])"
```

La génération a réussi, puis l'impression console a échoué par `UnicodeEncodeError` CP1252 sur une flèche Unicode du rapport. Artefacts produits :

- `index.html` + 16 pages de contenu ;
- `book.normalized.xml` ;
- `assets/generated/book.tex` ;
- `assets/generated/book.pdf` ;
- artefacts natifs LaTEI : `book.normalized.latei.tex`, `.latei_main.tex`, `.latei_body.tex`, `.latei_mono.pdf`, `.latei_manifest.json`, logs, TOC, AUX ;
- `book.normalized.roundtrip.xml` et diagnostics.

Logs et contrôles inspectés :

```powershell
Get-Content tests/_runtime/audit_real_site/build_report.txt -Encoding UTF8
Get-Content tests/_runtime/audit_real_site/assets/generated/pdf_build_report.txt -Encoding UTF8
Get-Content tests/_runtime/audit_real_site/assets/generated/book.latei_manifest.json -Encoding UTF8
Select-String ... book.normalized.latei_mono_build.log -Pattern ...
```

Limites de l'environnement :

- les tests dépendants de `tmp_path` sont perturbés par des permissions Windows/sandbox ;
- pas de validation visuelle par navigateur ou rendu PDF image page à page ;
- le fixture réel ne contient pas les assets iconographiques associés, donc l'audit vérifie la réaction à leur absence, pas leur rendu final.

## 3. Cartographie de l'architecture

Modules principaux :

- `main.py` : point d'entrée GUI minimal.
- `purh_site/config.py` : dataclass `BuildConfig`.
- `purh_site/tei_loader.py` : lecture XML et résolution XInclude maison.
- `purh_site/normalizer.py` : normalisation légère : ids, fusion de `hi`, références locales, figures.
- `purh_site/site_structure.py` : extraction métadonnées, pages, navigation et slugs.
- `purh_site/site_builder.py` : orchestration complète site statique, XSLT, assets, PDF site, rapport qualité.
- `purh_site/resources/tei_to_html.xsl` : transformation TEI fragmentaire vers HTML.
- `purh_site/resources/site.css` et `app.js` : habillage et interactions.
- `purh_site/reversible/*` : modèle documentaire réversible TEI -> LaTEX contrôlé -> TEI.
- `purh_site/reversible_integration.py` : export applicatif LaTEI, round-trip, manifestes.
- `purh_site/latei_driver.py` : préambule/driver/monofichier et compilation LuaLaTeX.
- `purh_site/latei_assets.py` : packaging images LaTEI.
- `purh_site/site_latei_pdf_export.py` : adaptateur des artefacts LaTEI vers `assets/generated/book.*`.
- `purh_site/gui.py` : interface Tkinter.
- `experiments/circe_spike` : expérimentation séparée.

Relations :

- `SiteBuilder.build_from_master()` appelle `TeiLoader`, puis `TeiNormalizer`, puis `SiteStructureBuilder`, puis XSLT HTML, puis éventuellement `build_site_latei_pdf_artifacts()`.
- `build_site_latei_pdf_artifacts()` appelle `run_reversible_export_for_file()`, qui produit systématiquement LaTEI, round-trip, driver debug et monofichier, puis compile les deux PDF internes.
- HTML et PDF ne partagent pas un modèle éditorial commun : HTML part du XML normalisé + XSLT ; PDF part du modèle réversible LaTEI. C'est raisonnable, mais cela impose des tests de cohérence entre sorties qui ne sont pas encore assez forts.

## 4. Problèmes classés par gravité

### BLOQUANT

#### B1 - Les ressources iconographiques peuvent manquer alors que le build et le PDF sont marqués comme réussis

Fichiers :

- `purh_site/resources/tei_to_html.xsl`, templates `resolved-image-src`, `render-graphic-image`
- `purh_site/latei_assets.py`, fonctions `package_latei_graphics()`, `_resolve_graphic_path()`
- `purh_site/site_builder.py`, `_pdf_site_report_lines()`, `_run_site_quality_checks()`

Description :

Sur le fixture réel, 177 `graphic` sont détectés, mais aucun asset associé n'est fourni. Le site est généré, le PDF est généré, et le rapport indique `PDF généré : assets/generated/book.pdf`. Les avertissements existent, mais ils ne bloquent pas et ne dégradent pas le statut PDF.

Scénario reproductible :

```powershell
python -c "from pathlib import Path; from purh_site.site_builder import SiteBuilder; from purh_site.config import BuildConfig; SiteBuilder().build_from_master(Path('tests/fixtures/metopes/heraldique_ii.book.normalized.xml'), BuildConfig(output_dir=Path('tests/_runtime/audit_real_site'), pdf_export_mode='latei_pdf'))"
```

Impact :

Un livre riche en figures peut être livré avec un PDF et un site où les images sont absentes. C'est une sortie éditorialement inutilisable, mais présentée comme produite avec succès.

Preuves observées :

- `build_report.txt` : `177 figure(s), 177 graphic(s)`, puis nombreuses lignes `fichier local absent assets/images/../icono/...`.
- `book.normalized.latei_graphics_map.tex` : `declare 0`, `warnings 177`, avec `Image not found for LaTEI package`.
- `pdf_build_report.txt` : `Succès export : True`, `Message PDF monofichier : LaTEI PDF produced successfully`.

Correction recommandée :

Introduire un statut d'intégrité des assets. Pour un mode publication/PDF, l'absence d'une image locale référencée doit au minimum rendre le statut global non publiable. Distinguer `build technique OK` et `sortie éditoriale complète OK`.

Tests à ajouter :

- fixture avec une figure locale manquante : le rapport doit classer la sortie `non publiable` ;
- fixture avec image présente : l'image est copiée, référencée dans HTML et présente dans LaTEI/PDF ;
- test site + LaTEI sur URL avec `%20`, casse différente et `../icono`.

#### B2 - La résolution XInclude maison n'a pas de garde anti-cycle ni de support `xpointer`

Fichier : `purh_site/tei_loader.py`, lignes 68-93.

Description :

`_resolve_xincludes()` parcourt récursivement les `xi:include`, parse chaque cible, puis insère des enfants sélectionnés. Aucun ensemble `visited` ou pile d'inclusion ne prévient les cycles. `xpointer`, `parse`, fallback XInclude et diagnostics structurés ne sont pas traités. Les inclusions manquantes sont seulement ignorées après warning.

Scénario reproductible :

Créer deux fichiers TEI qui s'incluent mutuellement via `xi:include`. Le chargeur récursif réentrera jusqu'à erreur de récursion ou épuisement. Avec `xpointer`, le chargeur ignore la sélection demandée et insère `/TEI/text/*`.

Impact :

Un volume Métopes multi-fichiers peut planter, insérer trop de contenu, perdre la relation exacte fichier/source, ou produire un XML normalisé qui ne correspond pas à la composition voulue.

Preuves observées :

- code récursif sans `visited` ;
- `_collect_include_hrefs()` ne collecte que les includes du fichier initial ;
- `_select_included_nodes()` retourne les enfants de `/tei:TEI/tei:text`, sans `xpointer`.

Correction recommandée :

Utiliser `lxml` XInclude sécurisé si possible, ou conserver l'implémentation maison avec pile d'inclusion, détection de cycle, support explicite ou rejet clair de `xpointer`, conservation de la provenance, et erreur contrôlée sur fichier manquant selon le mode.

Tests à ajouter :

- inclusion locale simple ;
- inclusion imbriquée ;
- inclusion cyclique ;
- `xpointer` explicitement supporté ou explicitement refusé ;
- fichier inclus manquant avec message bloquant en mode publication.

### CRITIQUE

#### C1 - Le mode `latei` compile quand même des PDF internes

Fichiers :

- `purh_site/site_builder.py`, `_build_pdf_site_artifacts()`, lignes 413-434
- `purh_site/site_latei_pdf_export.py`, lignes 55-68
- `purh_site/reversible_integration.py`, lignes 252-273

Description :

`SiteBuilder` passe `compile_pdf=(mode == "latei_pdf")` à l'adaptateur, mais l'adaptateur appelle toujours `run_reversible_export_for_file()`. Cette fonction compile toujours `latei_main` et le monofichier via `compile_latei_pdf()`, quel que soit le mode site.

Scénario reproductible :

Demander `BuildConfig(pdf_export_mode='latei')` sur un gros volume avec LuaLaTeX disponible. Le site ne copie pas `book.pdf`, mais l'export interne compile quand même les deux PDF natifs.

Impact :

Le mode supposé "LaTEX seulement" devient lent, dépendant de LuaLaTeX, et peut bloquer la GUI inutilement. En environnement sans LaTeX, il génère des logs d'échec PDF même si l'utilisateur n'a pas demandé de PDF.

Preuves observées :

- génération du fixture réel a duré plusieurs minutes et produit `.latei.pdf` et `.latei_mono.pdf` en plus de `book.pdf`.
- code `run_reversible_export_for_file()` n'a pas de paramètre `compile_pdf`.

Correction recommandée :

Ajouter un paramètre `compile_pdf: bool` à `run_reversible_export_for_file()`. En mode `latei`, produire LaTEI, manifestes et round-trip, mais ne pas appeler LuaLaTeX.

Tests à ajouter :

- monkeypatch de `compile_latei_pdf()` pour vérifier qu'il n'est pas appelé en mode `latei` ;
- test GUI/preflight indiquant clairement les dépendances selon le mode.

#### C2 - La chaîne PDF ne fait qu'une passe LaTeX et ne valide pas les logs

Fichier : `purh_site/latei_driver.py`, `compile_latei_pdf()`, lignes 199-302.

Description :

La compilation appelle LuaLaTeX une seule fois. Le succès est défini par `returncode == 0` et existence du PDF. Les warnings `fancyhdr`, `hyperref`, `Underfull`, `Rerun` ne changent pas le statut.

Scénario reproductible :

Génération réelle du fixture : `Return code: 0`, PDF produit, mais logs avec 44 `Underfull \hbox`, 32 warnings `fancyhdr`, 9 warnings `hyperref`.

Impact :

TOC, références, bookmarks et mise en page peuvent être incomplets ou instables. Le projet peut livrer un PDF compilé mais typographiquement non validé.

Preuves observées :

- `book.normalized.latei_mono_build.log` : 44 underfull, 32 `\headheight is too small`, 9 `Token not allowed in a PDF string`.
- aucune analyse de log dans `compile_latei_pdf()`.

Correction recommandée :

Compiler deux passes par défaut pour les vrais PDF, avec option configurable. Ajouter un analyseur de log minimal : erreurs fatales, images manquantes, references undefined, rerun demandé, overfull sévères, warnings hyperref dans bookmarks.

Tests à ajouter :

- test qui force `Rerun to get cross-references right` et vérifie une seconde passe ;
- test log contenant `Package hyperref Warning` classé warning PDF ;
- test `Overfull \hbox` au-dessus d'un seuil.

#### C3 - La table des matières PDF est placée après le corps

Fichier : `purh_site/latei_driver.py`, `build_latei_driver()` lignes 74-86 et `_monofile_content()` lignes 173-180.

Description :

Le driver et le monofichier insèrent `\tableofcontents` après `\input{body}` ou après `lateiDocument`. Pour un livre éditorial, la table des matières est normalement dans le front matter, avant le corps, sauf décision explicite.

Scénario reproductible :

Lire `book.tex` généré : `\begin{lateiDocument}` puis corps, `\end{lateiDocument}`, `\cleardoublepage`, `\tableofcontents`, `\end{document}`.

Impact :

PDF éditorialement non conforme pour une monographie/volume collectif. Les tests actuels vérifient surtout la présence de la TOC, pas sa position éditoriale.

Preuves observées :

- code cité ;
- `book.tex` généré contient la TOC après le corps.

Correction recommandée :

Placer la TOC après page de titre/front matter et avant le corps, ou rendre l'ordre configurable avec un défaut PURH explicite.

Tests à ajouter :

- test sur l'ordre `titlepage` -> `tableofcontents` -> corps ;
- test PDF minimal vérifiant que la première page de contenu vient après la TOC.

#### C4 - La GUI bloque le thread principal pendant les générations longues

Fichier : `purh_site/gui.py`, `_build()` lignes 624-632, `_run_build_after_dialog_is_drawn()` lignes 634-674.

Description :

La boîte d'attente est affichée puis `_run_build_after_dialog_is_drawn()` est appelée via `after(100)`. Le build se déroule ensuite dans le thread Tk principal. Il n'y a pas de worker thread ni de queue de messages.

Scénario reproductible :

Lancer depuis la GUI une génération `latei_pdf` sur le fixture réel. L'appel en CLI a duré plusieurs minutes. Dans Tk, pendant ce temps, l'event loop ne traite plus les interactions.

Impact :

Fenêtre figée, impossibilité d'annuler, impression de crash, logs non progressifs. La boîte "Génération en cours" s'affiche probablement avant le lancement, mais ne reste pas réellement interactive.

Preuves observées :

- `_build()` utilise `after`, pas `Thread`.
- aucune occurrence utile de `Thread` dans `gui.py`.

Correction recommandée :

Déplacer le build dans un worker thread ou processus, avec queue de messages vers le thread principal. Ne jamais appeler Tk depuis le worker. Ajouter annulation douce ou au minimum bouton désactivé avec progression textuelle.

Tests à ajouter :

- test unitaire de l'état bouton/dialogue sur exception ;
- test manuel documenté sur génération longue ;
- si possible test Tk avec fake builder lent et vérification que `update()` continue.

#### C5 - `pyproject.toml` absent et dépendances déclarées insuffisantes

Fichiers : absence de `pyproject.toml`, `requirements.txt`.

Description :

Le dépôt vise wheel/Nuitka/Windows, mais il ne déclare ni métadonnées de package, ni package data, ni console/gui scripts, ni dépendances de test, ni inclusion des ressources `resources/*.xsl`, `.css`, `.js`, `.tex`.

Scénario reproductible :

`Get-Content pyproject.toml` échoue : fichier absent. `requirements.txt` contient seulement `lxml>=5.0`.

Impact :

Le projet fonctionne en dépôt de développement, mais pas de façon fiable en wheel ou application packagée. Les tests utilisent `pytest`; la chaîne PDF dépend de LuaLaTeX ; des tests utilisent `lxml.html`, subprocess, etc. Les ressources sont chargées via `Path(__file__)`, fragile en packaging selon le mode.

Correction recommandée :

Créer un `pyproject.toml` minimal avec dépendances runtime/test, package data, entry point GUI, et stratégie `importlib.resources` pour ressources.

Tests à ajouter :

- test d'import depuis wheel locale ;
- test `importlib.resources.files('purh_site.resources')` ;
- smoke Nuitka vérifiant présence XSL/CSS/JS/macros.

### IMPORTANT

#### I1 - La stratégie d'assets HTML préfixe `assets/images/` devant des chemins Métopes déjà relatifs

Fichier : `purh_site/resources/tei_to_html.xsl`, `resolved-image-src`.

Description :

Un `graphic url="../icono/br/.../fig1.jpg"` devient `assets/images/../icono/br/...`. Cette URL peut fonctionner si les assets sont copiés dans une topologie précise, mais elle est peu claire, produit des warnings et complique les chemins avec espaces encodés.

Impact :

Déploiement statique fragile, publication difficile à déplacer, confusion entre chemin documentaire et chemin publié.

Correction recommandée :

Centraliser une résolution/copie d'assets depuis le XML vers un manifest, puis réécrire les URL vers des chemins publiés stables sans `..`.

#### I2 - Copie des assets utilisateur par suppression de dossier destination

Fichier : `purh_site/site_builder.py`, `_copy_user_assets()` lignes 460-470.

Description :

Si un dossier de même nom existe dans `output/assets`, il est supprimé par `shutil.rmtree(dst)` puis recopié. Sans garde explicite que `dst` est bien sous `output_assets_dir`, cette opération reste risquée si la configuration est mauvaise ou si des chemins sont symlinkés.

Impact :

Risque d'effacement inattendu dans un dossier de sortie choisi par l'utilisateur, surtout si une éditrice pointe vers un dossier existant.

Correction recommandée :

Résoudre et vérifier `dst.relative_to(output_assets_dir.resolve())`, écrire dans un dossier temporaire puis swap, ou refuser de supprimer sans option claire.

#### I3 - Le chargeur XInclude perd la granularité de provenance

Fichier : `purh_site/tei_loader.py`, lignes 84-93, 103-128.

Description :

Le parent du `xi:include` reçoit `data-include-href`, `data-page-title`, `data-page-authors`, mais les noeuds insérés ne portent pas leur fichier source. Plusieurs inclusions dans le même parent peuvent écraser ces attributs.

Impact :

Collisions de métadonnées, difficulté à retrouver les assets associés au fichier inclus, diagnostics peu actionnables.

Correction recommandée :

Attacher la provenance à un wrapper éditorial stable ou aux racines insérées, pas au parent commun ; conserver une table d'inclusion dans le rapport.

#### I4 - XSLT HTML appauvrit certains éléments TEI non couverts

Fichier : `purh_site/resources/tei_to_html.xsl`.

Description :

Le XSLT couvre beaucoup d'éléments courants, mais tout élément sans template explicite tombe sur les templates par défaut XSLT : texte rendu, balise/attributs perdus. C'est acceptable pour un rendu visuel minimal, mais dangereux si le site est présenté comme préservant la sémantique.

Impact :

`anchor`, `floatingText`, théâtre (`sp`, `speaker`, `stage`), formules MathML, certains crédits/sources de figures et attributs TEI peuvent disparaître sémantiquement du HTML sans warning.

Correction recommandée :

Ajouter un mode fallback HTML visible : wrapper `span/div data-tei="localName"` pour familles non supportées ou au minimum rapporter les éléments non rendus explicitement.

#### I5 - Le modèle réversible préserve les noeuds mais simplifie les noms d'attributs namespacés en LaTEX

Fichiers : `purh_site/reversible/latex_writer.py` lignes 134-145, `latex_reader.py` lignes 412-417.

Description :

`xml:id` et `xml:lang` sont traités, mais les autres attributs namespacés sont sérialisés avec le localname seul. Pour les éléments génériques, le namespace de l'élément est conservé, mais les namespaces d'attributs autres que XML ne le sont pas dans le nom LaTEX.

Impact :

Attributs `xlink:*`, `aid:*`, `rendition` namespacés ou extensions Métopes peuvent être perdus ou collisionner en round-trip LaTEI.

Correction recommandée :

Sérialiser les attributs namespacés de manière réversible (`attrns__hash__local` ou option structurée) et ajouter tests avec `xlink:href` et attributs Adobe/Métopes.

#### I6 - Les logs de build HTML/PDF ne distinguent pas assez les statuts

Fichiers : `site_builder.py`, `site_latei_pdf_export.py`, `latei_driver.py`.

Description :

Les rapports mélangent informations, warnings et succès. `build_report.txt` peut contenir beaucoup d'images absentes après avoir annoncé le PDF généré.

Impact :

Une petite équipe éditoriale risque de ne pas voir les problèmes critiques dans un rapport très long.

Correction recommandée :

Ajouter un résumé de statut en tête : `OK`, `OK avec avertissements`, `NON PUBLIABLE`, `ÉCHEC`, avec compteurs.

#### I7 - La console Windows échoue à imprimer certains rapports Unicode

Scénario observé :

La commande de génération a échoué après build sur `UnicodeEncodeError: 'charmap' codec can't encode character '\u2190'`.

Impact :

Scripts CLI et diagnostics peuvent échouer uniquement au moment d'afficher des caractères typographiques.

Correction recommandée :

Configurer l'encodage de sortie dans les scripts CLI (`PYTHONUTF8=1`, `sys.stdout.reconfigure(encoding='utf-8', errors='replace')`) ou éviter les caractères non CP1252 dans logs console.

#### I8 - Les tests dépendent trop de la gestion temporaire implicite de pytest

Fichiers : nombreux tests avec `tmp_path`, `tmp_path_factory`.

Description :

Dans cet environnement Windows, une grande partie de la suite est inexécutable à cause des permissions du temp pytest. Même `--basetemp` a posé problème au nettoyage.

Impact :

La suite est difficile à exécuter de façon reproductible sur Windows/sandbox, précisément la cible de distribution.

Correction recommandée :

Documenter une variable `TMP/TEMP` ou un `--basetemp` connu, créer les parents, et éviter les modes de permissions problématiques si possible. Ajouter une commande test Windows dans README/CI.

### MINEUR

#### M1 - Anciens `.pyc` et artefacts de build dans le dépôt de travail

Fichiers : `purh_site/__pycache__`, `tests/__pycache__`, `dist/Impressions.exe`, `build_nuitka/`.

Impact :

Bruit d'audit, risque de confusion avec modules supprimés.

Correction recommandée :

Nettoyer les caches et décider explicitement si `dist/Impressions.exe` et `build_nuitka` doivent être versionnés.

#### M2 - Quelques commentaires/documentations indiquent une migration non finalisée

Fichier : `purh_site/site_latei_pdf_export.py`, docstring "Il n'est pas encore branché dans site_builder.py" alors qu'il est importé par `site_builder.py`.

Impact :

Documentation interne trompeuse.

Correction recommandée :

Mettre à jour les docstrings après migration.

### INFORMATION

#### N1 - Le normaliseur récent améliore réellement l'intégrité

Fichier : `purh_site/normalizer.py`.

Observation :

Le rejet des `xml:id` dupliqués, la conservation de `note/@n`, les warnings de pointeurs locaux et la séparation entre id source/id généré sont de bonnes décisions.

#### N2 - La projection réversible est conceptuellement solide

Fichiers : `purh_site/reversible/tei_reader.py`, `tei_writer.py`, `nodes.py`.

Observation :

Le passage `text`/`tail` vers `TextNode` ordonnés puis retour vers `text`/`tail` est bien conçu. Les inconnus sont conservés via `ElementNode` générique.

## 5. Régressions probables liées aux modifications récentes

Les commits récents montrent plusieurs zones à surveiller :

- `75ab62a Normalizer XML` et `58027ef Normalizer XML - 2` : changements récents sur ids, notes et références internes. Les tests ajoutés sont utiles, mais la transformation XSLT et le rewriting HTML doivent être vérifiés sur corpus multi-fichiers avec vrais assets.
- `b991c9d Ajoute les tests d'intégrité du normaliseur XML` : bonne couverture nouvelle, mais les tests utilisant `tmp_path` ne sont pas robustes dans l'environnement Windows audité.
- `4433fe5 Amélioration boite d'attente` et branche `doc-asset` : améliore l'affichage initial, mais ne résout pas le blocage du thread principal.
- `08beae6 Nettoyage` : suppression de fichiers Nuitka français dans `build_nuitka`, ajout d'audits ; rien de bloquant observé, mais le dépôt garde une distribution binaire et des caches.
- Migration LaTEI récente : l'adaptateur site est branché, mais sa docstring dit encore le contraire ; surtout, `latei` vs `latei_pdf` ne sépare pas réellement compilation et export.

Régression probable la plus sérieuse : l'impression de succès PDF a été renforcée par le nouvel adaptateur `book.pdf`, alors que les warnings assets/images ne changent pas le statut de succès.

## 6. Analyse des tests

Ce que les tests garantissent vraiment :

- beaucoup de règles LaTEI unitaires et round-trip sur fragments ;
- rendu HTML de familles TEI courantes : notes, figures, bibliographie, inline, navigation ;
- normaliseur : ids, notes, références locales, duplicate ids ;
- adaptateur site/LaTEI : présence des fichiers attendus ;
- quelques tests conditionnels LuaLaTeX.

Ce que les tests ne garantissent pas assez :

- publication complète d'un livre avec assets réels ;
- validation visuelle HTML responsive ;
- validation PDF par inspection de pages ;
- analyse des logs LuaLaTeX ;
- conformité éditoriale de la TOC, front matter, running heads ;
- cohérence contenu HTML/PDF sur le même corpus ;
- XInclude complexe : cycles, nested includes, xpointer, conflits de provenance ;
- packaging wheel/Nuitka ;
- GUI non bloquante.

Tests prioritaires à ajouter :

1. Volume multi-fichiers avec `xi:include`, images, notes, références croisées.
2. Asset présent/manquant/collision de nom avec statut non publiable si manquant.
3. PDF deux passes + analyse log.
4. Comparaison texte structuré HTML/PDF/TEI normalisé sur corpus minimal.
5. XInclude cyclique et `xpointer` refusé/supporté explicitement.
6. Round-trip LaTEI avec attribut namespacé non XML.
7. GUI fake builder lent, sans blocage du mainloop.
8. Test packaging ressources via `importlib.resources`.

## 7. Analyse des sorties HTML

Validité :

- Les pages sont générées et le contrôle qualité interne détecte liens/ressources locaux absents.
- Le HTML est construit avec échappements `html.escape` côté templates Python et XSLT côté XML.
- Risque : la post-normalisation par regex (`normalize_inline_html_spacing`, `normalize_french_typography_html`) agit sur du HTML sérialisé. Elle protège `script/style/code/pre`, mais reste fragile sur cas HTML complexes.

Accessibilité :

- Les figures utilisent `figDesc` ou `head` comme `alt` quand disponible.
- Navigation avec `aria-label`, notes avec liens retour.
- Risque : images sans `figDesc/head` peuvent avoir `alt` absent ; les boutons de zoom autour des images exigent JS pour l'interaction enrichie, même si l'image reste visible.

Contenu :

- Beaucoup d'éléments Métopes courants sont rendus.
- Les éléments non couverts peuvent perdre leur sémantique TEI sans warning.

Navigation :

- Pages, sidebar et prev/next sont générés correctement sur le fixture réel.
- Les slugs sont lisibles et déterministes.

Rendu visuel :

- Non vérifié par navigateur dans cet audit.
- Le site réel signale surtout les images absentes.

Référencement :

- Métadonnées Zotero/Dublin Core présentes dans le code et couvertes par tests.
- Pas de données structurées JSON-LD observées.

Robustesse :

- Hébergement statique simple OK pour HTML/CSS/JS.
- Publication déplaçable compromise si les ressources XML restent en chemins `../icono`.

## 8. Analyse de la chaîne PDF

Production LaTEX :

- Le monofichier `book.tex` est volumineux mais complet : préambule, macros, mapping, zone réversible, corps.
- La zone réversible est claire pour les éditrices.

Compilation :

- LuaLaTeX trouvé et utilisé.
- Compilation réelle réussie sur le fixture : `Return code: 0`, PDF produit.
- Deux PDF internes sont produits : driver debug et monofichier.

Logs :

- Logs non analysés fonctionnellement.
- Observé : 44 `Underfull \hbox`, 32 warnings `fancyhdr`, 9 warnings `hyperref`.

Références :

- Une seule passe peut laisser TOC/bookmarks/références instables.

Contenu :

- Round-trip documentaire sans diagnostic sur fixture réel.
- Images absentes : 177 warnings dans le mapping LaTEI, mais PDF quand même "réussi".

Typographie et mise en page :

- Les warnings `fancyhdr` indiquent une configuration de tête trop courte.
- Les warnings `hyperref` indiquent des macros TEI dans des chaînes PDF/bookmarks.
- TOC après le corps, éditorialement suspect.

Images :

- `book.tex` contient `includegraphics`, mais aucun mapping image réel sur le fixture faute d'assets.

Portabilité :

- Dépendance LuaLaTeX externe à découvrir dans `PATH`.
- Fonts `Chaparral Pro`/`Josefin Sans` optionnelles avec fallback, bon point.
- Ressources chargées via `Path(__file__)`, à sécuriser pour wheel/Nuitka.

## 9. Analyse de la GUI

Points satisfaisants :

- validation minimale des chemins ;
- bouton désactivé pendant la génération ;
- boîte d'attente affichée avant lancement via `after(100)` ;
- exceptions affichées par `messagebox.showerror` ;
- bouton réactivé dans `finally`.

Défauts :

- génération synchrone dans le thread Tk principal ;
- pas d'annulation ;
- pas de progression réelle ;
- logs non alimentés pendant le travail long ;
- les actions LaTEI du menu (`_run_reversible_export`, restore) sont aussi synchrones ;
- exceptions génériques, utiles pour ne pas crasher, mais messages parfois trop globaux.

Conclusion GUI :

La correction récente améliore l'apparition de la boîte, mais pas la réactivité pendant la génération. Pour `latei_pdf` sur vrai livre, c'est un défaut utilisateur critique.

## 10. Packaging et portabilité

Risques wheel :

- absence de `pyproject.toml` ;
- ressources non déclarées comme package data ;
- imports par chemin `Path(__file__)` ;
- dépendances test/dev non déclarées.

Risques Nuitka :

- `resources/tei_to_html.xsl`, `site.css`, `app.js`, `latei_macros.tex` doivent être inclus explicitement ;
- Tk/Tcl files présents dans `build_nuitka`, mais état de versionnement confus ;
- `dist/Impressions.exe` versionné sans recette reproductible claire.

Windows :

- encodage console CP1252 peut casser les scripts ;
- permissions temporaires pytest problématiques ;
- chemins avec espaces/PATH Pandoc OK observé.

Linux :

- chemins et casse d'images (`Fig50.JPG` vs `.jpg`) doivent être testés ;
- dépendance LuaLaTeX/Pandoc à documenter séparément.

À embarquer :

- code Python ;
- XSLT/CSS/JS/macros LaTEX ;
- éventuellement assets de charte graphique par défaut.

À installer séparément :

- distribution TeX/LuaLaTeX ;
- Pandoc si réellement utilisé dans les workflows ;
- fonts propriétaires si nécessaires, avec fallbacks.

À découvrir/configurer :

- chemin LuaLaTeX ;
- chemin Pandoc ;
- dossier assets/source ;
- dossier sortie.

## 11. Éléments satisfaisants

- Architecture sobre et compréhensible.
- Pas d'usage observé de `shell=True` dans le code applicatif.
- `subprocess.run()` passe une liste d'arguments à LuaLaTeX.
- `resolve_entities=False` dans le chargeur TEI.
- Normaliseur récent bien orienté intégrité.
- Modèle réversible préserve l'ordre, `text`, `tail`, attributs courants et inconnus.
- Tests nombreux, avec intention éditoriale réelle.
- Rapports de build écrits et lisibles en UTF-8.
- Fallback fonts dans le préambule LaTEX.
- Génération réelle d'un gros fixture sans diagnostic round-trip.

## 12. Plan de correction proposé

### 1. Corrections bloquantes

Objectif : empêcher les faux succès.

- Ajouter un statut global `publishable`.
- Rendre manquants les assets locaux bloquants en mode publication/PDF.
- Faire remonter `latei_asset_warnings` dans `pdf_build_report.txt` et `build_report.txt` en tête.
- Critère : fixture sans images => build technique possible, statut `NON PUBLIABLE`.

### 2. Fiabilisation XML et assets

- Ajouter garde anti-cycle XInclude.
- Supporter ou refuser clairement `xpointer`.
- Conserver provenance des fichiers inclus.
- Introduire un manifest assets XML -> sortie publiée.
- Critère : volume multi-fichiers avec images copiées et chemins publiés sans `..`.

### 3. Fiabilisation HTML

- Ajouter fallback explicite pour éléments TEI non supportés ou rapport d'éléments ignorés.
- Ajouter tests d'accessibilité de base : alt, heading order, notes.
- Critère : aucun élément TEI non rendu sans warning.

### 4. Fiabilisation LaTeX/PDF

- Séparer `latei` et `latei_pdf`.
- Compiler deux passes en mode PDF.
- Analyser logs et classer warnings.
- Déplacer TOC avant corps ou configurer l'ordre.
- Critère : PDF fixture sans `fancyhdr` répété, log résumé, statut cohérent.

### 5. GUI

- Worker thread/process pour génération.
- Queue vers Tk pour logs/progression.
- Bouton annuler ou message "génération non annulable".
- Critère : fenêtre reste responsive pendant fake build long.

### 6. Packaging

- Ajouter `pyproject.toml`.
- Déclarer package data.
- Utiliser `importlib.resources`.
- Documenter dépendances externes.
- Critère : wheel locale installée puis génération smoke.

### 7. Amélioration des tests

- Créer un corpus intégration multi-fichiers réaliste mais petit.
- Ajouter tests de logs PDF.
- Ajouter tests assets présents/manquants.
- Ajouter test Windows temp documenté.

### 8. Dette technique non urgente

- Nettoyer caches `.pyc`.
- Clarifier versionnement de `dist/` et `build_nuitka/`.
- Mettre à jour docstrings obsolètes.
- Réduire progressivement la taille de `site_builder.py` seulement si une extraction améliore les tests.

## 13. Les dix priorités absolues

| Priorité | Action | Gravité | Difficulté | Risque de régression | Bénéfice attendu |
|---:|---|---|---|---|---|
| 1 | Statut non publiable si images/assets locaux manquent | BLOQUANT | Moyenne | Moyen | Empêche les faux succès éditoriaux |
| 2 | Séparer export `latei` et compilation `latei_pdf` | CRITIQUE | Moyenne | Moyen | Réduit lenteur, dépendances et blocage GUI |
| 3 | Deux passes LuaLaTeX + analyse minimale des logs | CRITIQUE | Moyenne | Faible | PDF plus fiable et diagnostics utiles |
| 4 | Garde anti-cycle XInclude + politique `xpointer` | BLOQUANT | Moyenne | Moyen | Sécurise les vrais volumes multi-fichiers |
| 5 | Manifest/réécriture assets sans `../` | IMPORTANT | Moyenne | Moyen | Site déplaçable et publiable |
| 6 | Worker GUI pour génération longue | CRITIQUE | Moyenne | Moyen | Interface utilisable sur vrais livres |
| 7 | Déplacer/configurer la table des matières PDF | CRITIQUE | Faible | Faible | Conformité éditoriale immédiate |
| 8 | `pyproject.toml` + package data + `importlib.resources` | CRITIQUE | Moyenne | Moyen | Prépare wheel/Nuitka proprement |
| 9 | Tests intégration corpus multi-fichiers avec assets | IMPORTANT | Moyenne | Faible | Couvre le risque principal réel |
| 10 | Rapport en tête avec compteurs erreurs/warnings | IMPORTANT | Faible | Faible | Rend les problèmes visibles pour l'équipe éditoriale |

