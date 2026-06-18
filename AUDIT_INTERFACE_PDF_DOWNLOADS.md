# Audit interface PDF / téléchargements

## Résumé exécutif

Le comportement actuel est déjà partiellement aligné avec la cible :

* Le site copie le dossier d’assets utilisateur dans `output/assets`.
* Il cherche déjà un PDF éditeur dans `output/assets/PDF`.
* S’il trouve un PDF, il le propose en téléchargement sur la page d’accueil.
* Les téléchargements XML/PDF sont déjà rendus sous forme de liens stylés comme des boutons (`<a class="download-button" ...>`), pas comme de simples liens nus.
* La chaîne `PdfBuilder` existe, mais elle n’est pas appelée par `SiteBuilder` ni par l’interface graphique.

Le point principal à conserver est donc clair : le PDF éditeur déjà présent dans les assets doit rester prioritaire. Le point manquant est l’absence totale d’intégration contrôlée du `.tex` / PDF généré dans les sorties web et dans l’interface de téléchargement.

Correction recommandée plus tard : une micro-passe limitée qui n’intègre pas encore toute la compilation PDF au build web, mais prépare proprement le modèle de téléchargements de l’accueil pour XML, LaTeX et PDF, en gardant le PDF éditeur prioritaire.

## 1. PDF éditeur dans les assets

### Où le programme cherche-t-il les assets ?

Le dossier d’assets source vient de `BuildConfig.assets_dir`.

* `purh_site/config.py` définit `assets_dir: Path | None`.
* `purh_site/gui.py` expose un champ “Dossier assets”.
* `SiteBuilder._finalize_build()` crée `config.output_assets_dir`, soit `output/assets`.
* `SiteBuilder._copy_user_assets()` copie chaque enfant du dossier source dans `output/assets`.

Conséquence : si le projet source contient un dossier `PDF`, par exemple :

```text
source_assets/PDF/ouvrage.pdf
```

il est copié tel quel vers :

```text
output/assets/PDF/ouvrage.pdf
```

### Existe-t-il une logique qui repère un PDF dans les assets ?

Oui.

La détection se fait dans :

* `purh_site/site_builder.py`
* `ThemeAssets.pdf_href`
* `SiteBuilder._discover_theme_assets(...)`
* `SiteBuilder._discover_pdf_href(...)`

Le code cherche seulement un dossier de premier niveau dans `output/assets` dont le nom vaut `pdf` sans tenir compte de la casse :

```python
for child in output_assets_dir.iterdir():
    if child.is_dir() and child.name.lower() == "pdf":
        pdf_files = sorted(path for path in child.rglob("*.pdf") if path.is_file())
```

Donc les dossiers suivants fonctionnent :

```text
assets/PDF/
assets/pdf/
assets/Pdf/
```

Mais un PDF placé directement dans `assets/ouvrage.pdf` n’est pas détecté.

### Comment ce PDF est-il choisi ?

S’il y a un dossier `PDF`, le programme prend :

```python
pdf_files[0]
```

après tri alphabétique des fichiers `*.pdf` trouvés récursivement sous ce dossier.

Conséquences :

* plusieurs PDF sont autorisés techniquement ;
* seul le premier par ordre alphabétique est retenu ;
* aucun warning n’indique qu’il y avait plusieurs candidats ;
* les fichiers `.PDF` en majuscules ne sont pas détectés, car `rglob("*.pdf")` est sensible au motif.

### Est-il copié dans le dossier de sortie ?

Oui, indirectement.

La copie est globale : `_copy_user_assets()` copie le dossier `PDF` source vers `output/assets/PDF`. La logique PDF ne fait pas une copie dédiée du fichier choisi ; elle découvre ensuite ce qui a déjà été copié.

### Est-il proposé en téléchargement ?

Oui.

`_discover_pdf_href()` renvoie un chemin relatif de type :

```text
assets/PDF/ouvrage.pdf
```

Ce chemin est stocké dans `theme_assets.pdf_href`, puis transmis à :

```python
_render_home_downloads(normalized_tei_href, theme_assets.pdf_href)
```

Le rendu actuel produit :

```html
<a class="download-button" href="assets/PDF/ouvrage.pdf" download>Télécharger le PDF</a>
```

### Est-il prioritaire sur un PDF généré ?

Dans l’état actuel, la question ne se pose pas encore dans le code : aucun PDF n’est généré par `SiteBuilder`.

Mais si une génération PDF est ajoutée plus tard, le comportement actuel implique une règle naturelle à conserver :

```text
si theme_assets.pdf_href existe déjà, ne pas générer automatiquement un autre PDF pour le site
```

### Que se passe-t-il s’il y a plusieurs PDF dans les assets ?

Le premier PDF par tri alphabétique est choisi.

Exemple probable :

```text
assets/PDF/01-editeur.pdf
assets/PDF/02-annexe.pdf
```

Le site proposera `01-editeur.pdf`.

Limite : aucun message dans le rapport ne signale les autres PDF ignorés.

### Que se passe-t-il s’il n’y a aucun PDF dans les assets ?

`theme_assets.pdf_href` vaut `None`.

Conséquences :

* aucun bouton PDF n’est rendu dans `_render_home_downloads()`;
* aucun PDF n’est généré ;
* aucun `.tex` n’est généré ;
* le rapport de build ne mentionne pas de PDF détecté.

## 2. Génération LaTeX/PDF actuelle

### `PdfBuilder` est-il appelé depuis `SiteBuilder` ?

Non.

`SiteBuilder` n’importe pas `PdfBuilder`, et aucun appel à `build_pdf_from_normalized_tei()` n’existe dans la chaîne web.

La séparation est actuellement stricte :

```text
SiteBuilder : TEI -> HTML statique
PdfBuilder  : TEI normalisée -> LaTeX -> PDF optionnel
```

### La génération LaTeX/PDF est-elle branchée dans l’interface ?

Non.

`purh_site/gui.py` expose :

* fichier maître XML ;
* fichiers XML indépendants ;
* dossier de sortie ;
* dossier assets ;
* quatrième de couverture ;
* champs collection ;
* prévisualisation.

Il n’expose pas :

* générer LaTeX ;
* générer PDF ;
* choisir le moteur LaTeX ;
* activer/désactiver la compilation ;
* consulter un rapport PDF.

### Quels fichiers seraient concernés pour l’ajouter proprement ?

Pour une intégration future minimale :

* `purh_site/config.py` : options explicites, par exemple `write_latex`, `build_pdf`, `latex_engine`.
* `purh_site/site_builder.py` : orchestration légère après écriture du `book.normalized.xml`, sans absorber la logique PDF.
* `purh_site/gui.py` : cases à cocher ou options simples.
* `tests/test_smoke.py` ou nouveau test web : comportement côté site.
* `tests/test_pdf_latex.py` : comportement `PdfBuilder` déjà largement couvert.

À ne pas faire : déplacer la logique de `PdfBuilder` dans `SiteBuilder`.

### Où faudrait-il écrire le `.tex` généré ?

Le meilleur emplacement minimal serait dans le dossier de sortie du site, mais séparé des assets éditeur :

```text
output/pdf/book.tex
```

ou, si on veut le proposer en téléchargement public :

```text
output/assets/pdf-generated/book.tex
```

Recommandation Codex : commencer par `output/pdf/book.tex`, puis décider explicitement si le `.tex` doit être exposé publiquement. Le comportement cible demande un téléchargement LaTeX ; dans ce cas, une copie ou une sortie directe sous `output/assets/generated/` serait plus cohérente pour les liens HTML.

### Où faudrait-il écrire le PDF généré ?

Le `PdfBuilder` écrit actuellement :

```text
output_pdf_dir/book.tex
output_pdf_dir/book.pdf
output_pdf_dir/latex_build.log
output_pdf_dir/pdf_build_report.txt
```

Pour le site, il faut éviter de mélanger PDF éditeur et PDF généré. Une option saine :

```text
output/assets/generated/book.tex
output/assets/generated/book.pdf
output/assets/generated/pdf_build_report.txt
```

Mais seulement si aucun PDF éditeur n’est détecté.

### Comment éviter de rendre LuaLaTeX obligatoire ?

Le code existant le permet déjà :

* `PdfBuilder(compile_pdf=False)` écrit seulement le `.tex`.
* Si `compile_pdf=True` et moteur absent, le résultat est un échec contrôlé avec log et rapport.
* Les tests normaux ne compilent pas réellement.
* Les tests LuaLaTeX sont optionnels via `IMPRESSIONS_RUN_LATEX_INTEGRATION=1`.

Comportement futur recommandé :

```text
write_latex=True par défaut seulement si pas de PDF éditeur
build_pdf=False par défaut
build_pdf=True seulement si option explicite
```

### Quel comportement adopter si LuaLaTeX est absent ?

Si aucune option de compilation n’est activée :

* produire le `.tex`;
* ne pas signaler d’erreur.

Si `build_pdf=True` et `lualatex` absent :

* conserver le `.tex`;
* ne pas faire échouer le build HTML complet ;
* écrire un warning dans le rapport web ;
* ne pas rendre de bouton PDF généré ;
* rendre éventuellement le bouton LaTeX généré.

## 3. Interface et liens de téléchargement actuels

### Où sont construits les liens de téléchargement ?

Dans Python, pas dans un template externe ni dans le JavaScript :

```python
SiteBuilder._render_home_downloads(...)
```

Cette fonction est appelée depuis `_write_index_page()`.

### Quels fichiers sont actuellement proposés ?

Deux types seulement :

1. XML normalisé, si `normalized_tei_href` est présent.
2. PDF éditeur détecté dans les assets, si `theme_assets.pdf_href` est présent.

Le XML normalisé est proposé sous le nom :

```text
book.normalized.xml
```

Le PDF vient de :

```text
assets/PDF/*.pdf
```

ou équivalent selon le nom réel du dossier `PDF`.

### XML normalisé ?

Oui, si `BuildConfig.write_normalized_tei` vaut `True`.

Si `write_normalized_tei=False` :

* `book.normalized.xml` n’est pas écrit ;
* le bouton XML n’est pas rendu.

Ce comportement est déjà testé par :

```text
tests/test_smoke.py::test_write_normalized_tei_false_skips_export_and_download_link
```

### PDF ?

Oui, uniquement si un PDF existe dans `output/assets/PDF` après copie des assets.

Il n’existe pas encore de test dédié au cas PDF éditeur détecté et rendu comme bouton de téléchargement.

### Autre chose ?

Dans la page d’accueil : non.

Dans la lightbox des figures, le JavaScript crée aussi un lien :

```html
<a class="lightbox-download" href="#" download>Télécharger l’original</a>
```

Ce lien concerne les images, pas le XML/LaTeX/PDF du livre.

### Les liens sont-ils produits dans un template HTML, Python ou JS ?

* Téléchargements de l’accueil : Python (`site_builder.py`).
* Style des boutons : CSS (`site.css`).
* Téléchargement des originaux de figures : JavaScript (`app.js`).

### Sont-ils déjà des boutons ?

Oui, visuellement.

Le HTML utilise des ancres avec classe :

```html
<a class="download-button" ...>
```

Et `site.css` définit :

```css
.download-button {
  display: inline-flex;
  ...
  border-radius: 999px;
  ...
}
```

Techniquement ce sont des liens, ce qui est correct pour un téléchargement. Visuellement ce sont déjà des boutons.

La plus petite correction future ne serait donc pas “transformer des liens en boutons”, mais :

* clarifier les libellés ;
* ajouter le bouton LaTeX quand disponible ;
* différencier “PDF éditeur” et “PDF généré” ;
* ajouter des tests.

## 4. Écart avec le comportement cible

### Ce qui marche déjà

```text
Si assets contient un PDF éditeur dans un dossier PDF :
    copier ce PDF dans output/assets/PDF/
    proposer ce PDF en téléchargement
```

Ce comportement doit être conservé.

### Ce qui manque

```text
Si aucun PDF éditeur n’existe :
    générer le LaTeX
    proposer le LaTeX en téléchargement
    générer éventuellement le PDF si option activée
    proposer le PDF généré si disponible
```

Rien de cela n’est branché dans `SiteBuilder` ou dans la GUI.

### Comportement cible minimal ajusté à l’état réel du code

```text
Pendant le build web :
    copier les assets comme aujourd’hui
    détecter un PDF éditeur comme aujourd’hui

    si PDF éditeur détecté :
        utiliser theme_assets.pdf_href
        afficher "Télécharger le PDF éditeur"
        ne pas générer automatiquement de LaTeX/PDF

    sinon, si option write_latex activée :
        écrire book.tex via PdfBuilder(..., compile_pdf=False)
        placer le .tex dans un emplacement téléchargeable connu
        afficher "Télécharger le LaTeX"

        si option build_pdf activée :
            tenter PdfBuilder(..., compile_pdf=True)
            si succès :
                afficher "Télécharger le PDF généré"
            sinon :
                conserver le bouton LaTeX
                inscrire l’échec dans le rapport

    sinon :
        afficher seulement les téléchargements déjà disponibles
```

### Point de décision important

Il faut décider si le `.tex` généré est un artefact public du site ou seulement un artefact de build.

Si téléchargement attendu par l’interface :

```text
output/assets/generated/book.tex
```

est plus logique que :

```text
output/pdf/book.tex
```

car les liens HTML publics pointent déjà vers `assets/...`.

## 5. Proposition de micro-passe future

### Micro-passe proposée : verrouiller et clarifier les téléchargements existants

Ne pas brancher encore `PdfBuilder`.

Objectif : sécuriser le comportement actuel avant d’ajouter LaTeX/PDF généré.

Fichiers à modifier plus tard :

* `purh_site/site_builder.py`
* `tests/test_smoke.py` ou nouveau `tests/test_downloads.py`
* éventuellement `purh_site/resources/site.css` seulement si les libellés ou états demandent un ajustement visuel

Comportement attendu :

* un PDF placé dans `assets/PDF/ouvrage.pdf` est copié vers `output/assets/PDF/ouvrage.pdf`;
* le bouton PDF apparaît sur l’accueil ;
* le libellé devient explicitement `Télécharger le PDF éditeur`;
* le XML normalisé reste proposé si `write_normalized_tei=True`;
* aucun PDF généré n’est créé ;
* aucun appel à `PdfBuilder` depuis `SiteBuilder`.

Tests à ajouter :

```python
test_existing_editor_pdf_is_detected_and_downloaded_from_assets
test_no_pdf_download_button_when_assets_have_no_pdf
test_multiple_editor_pdfs_choose_first_sorted_candidate
test_download_links_are_rendered_as_buttons
```

Risques :

* casser le libellé attendu si des tests existants vérifient `Télécharger le PDF`;
* figer trop tôt une politique de choix du PDF multiple.

Commande pytest :

```powershell
C:\Python314\python.exe -m pytest tests\test_smoke.py -q
C:\Python314\python.exe -m pytest -q
```

## 6. Tests recommandés

Pour la suite, après la micro-passe de verrouillage :

```python
test_existing_editor_pdf_is_preferred_over_generated_pdf
test_latex_is_generated_when_no_editor_pdf_exists
test_pdf_generation_is_optional_when_lualatex_is_missing
test_download_links_are_rendered_as_buttons
test_xml_latex_pdf_download_targets_are_present_when_available
test_generated_pdf_is_not_attempted_when_editor_pdf_exists
test_latex_download_is_present_when_tex_generation_succeeds
test_generated_pdf_download_is_absent_when_lualatex_is_missing
test_pdf_build_failure_does_not_break_html_build
```

Priorité de tests :

1. PDF éditeur détecté et proposé.
2. Absence de PDF éditeur ne génère rien tant que l’option n’existe pas.
3. Boutons XML/PDF actuels stables.
4. Puis seulement génération LaTeX/PDF optionnelle.

## Conclusion

Ce qui marche déjà :

* copie des assets source vers `output/assets`;
* détection d’un PDF éditeur dans `assets/PDF`;
* proposition du PDF éditeur en téléchargement ;
* proposition du XML normalisé si écrit ;
* rendu visuel des téléchargements sous forme de boutons ;
* séparation stricte entre `SiteBuilder` et `PdfBuilder`.

Ce qui doit être conservé :

* priorité implicite au PDF éditeur existant ;
* absence de compilation obligatoire ;
* séparation web/PDF ;
* boutons de téléchargement construits côté Python, testables par inspection HTML.

Ce qui manque :

* tests explicites du PDF éditeur dans les assets ;
* libellé différenciant PDF éditeur et PDF généré ;
* option de génération LaTeX/PDF dans `BuildConfig`;
* affichage du LaTeX généré ;
* intégration contrôlée du rapport PDF au rapport web.

Ce qu’il ne faut surtout pas casser :

* la copie transparente des assets ;
* la détection actuelle de `assets/PDF`;
* `write_normalized_tei=False`;
* la suite normale sans LuaLaTeX ;
* la séparation `SiteBuilder` / `PdfBuilder`;
* le fait qu’un PDF éditeur fourni par les PURH soit utilisé avant toute génération automatique.
