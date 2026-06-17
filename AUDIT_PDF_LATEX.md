# Audit PDF / LaTeX — Impressions

## 1. Résumé exécutif

La branche contient déjà une chaîne TEI normalisée -> modèle sémantique Python -> LaTeX -> PDF. Elle est réelle, lisible et séparée du générateur HTML, mais elle n’est pas encore intégrée au build principal du site statique. Elle ressemble davantage à un prototype avancé qu’à une fonctionnalité prête pour une production éditoriale PURH.

Les trois modules centraux sont :

- `purh_site/tei_to_model.py` : parse une TEI normalisée vers un modèle interne.
- `purh_site/semantic_model.py` : définit ce modèle pivot.
- `purh_site/latex_renderer.py` : rend le modèle en LaTeX.
- `purh_site/pdf_builder.py` : orchestre l’écriture du `.tex` et, optionnellement, la compilation par `lualatex`.

Le point le plus positif est architectural : le PDF n’est pas tenté depuis le HTML généré, et le rendu LaTeX passe déjà par un modèle sémantique. C’est une base saine pour éviter une simple conversion HTML -> PDF médiocre. Le point le plus fragile est l’écart croissant entre la couverture HTML stabilisée dans les dernières passes et la couverture du modèle LaTeX : notes, figures, bibliographies structurées, tableaux, références internes, titres de pages, métadonnées fines et éléments Métopes récents ne sont pas encore alignés.

Recommandation principale : ne pas brancher immédiatement la compilation PDF dans `SiteBuilder`. Il faut d’abord tester et stabiliser l’existant TEI -> modèle -> LaTeX, produire un `.tex` vérifiable de manière optionnelle, puis seulement ajouter une compilation PDF optionnelle. La bonne trajectoire semble être : conserver `PdfBuilder` séparé, partir de la TEI normalisée, réutiliser autant que possible l’ordre et les définitions de pages de `SiteStructureBuilder`, et éviter toute duplication incontrôlée des règles HTML/XSLT.

## 2. Cartographie de l’existant

### Modules principaux du site web

Le site statique HTML repose principalement sur :

- `purh_site/site_builder.py` : orchestration du build HTML statique, génération des pages, assets, métadonnées, crédits, navigation, rapports.
- `purh_site/site_structure.py` : extraction de la structure éditoriale en pages, navigation, définitions de pages.
- `purh_site/resources/tei_to_html.xsl` : transformation TEI -> fragments HTML.
- `purh_site/gui.py` et `main.py` : points d’entrée utilisateur.

La chaîne HTML actuellement stabilisée suit globalement ce chemin :

1. XML TEI source.
2. Résolution et normalisation éventuelle.
3. Construction de la structure de site par `SiteStructureBuilder`.
4. Transformation TEI -> HTML par XSLT.
5. Post-traitements Python : liens internes, typographie française HTML, métadonnées, navigation, crédits, contrôle qualité.
6. Écriture de pages HTML, CSS, JS et ressources locales.

`SiteBuilder` reste le centre du build web. Il ne génère pas aujourd’hui de PDF ; il détecte seulement un PDF existant dans les assets pour proposer un lien de téléchargement.

### Tests HTML et structure

La branche contient une suite de tests assez fournie sur la partie web :

- rendu Métopes courant ;
- objets inline ;
- notes ;
- figures ;
- bibliographies ;
- références internes ;
- métadonnées Zotero/Dublin Core ;
- navigation et structure ;
- contrôle qualité ;
- typographie française ;
- smoke tests.

Ces tests documentent désormais une couverture HTML nettement plus large que la couverture LaTeX.

### Dépendances

`requirements.txt` ne déclare que :

```text
lxml>=5.0
```

La génération PDF dépend toutefois implicitement d’un environnement système TeX, au minimum :

- `lualatex`;
- une distribution TeX contenant `memoir`, `fontspec`, `polyglossia`, `microtype`, `graphicx`, `csquotes`, `hyperref`, `bookmark`, `caption`, `enumitem`, `verse`, `ragged2e`, `xurl`;
- les polices configurées, notamment TeX Gyre Pagella, TeX Gyre Heros et Latin Modern Mono.

Ces dépendances ne sont pas installables par `pip` et ne sont pas vérifiées dans une configuration projet dédiée.

## 3. Existant TEI → LaTeX

### `purh_site/semantic_model.py`

Ce module définit une représentation pivot indépendante du HTML et du LaTeX. C’est le meilleur élément réutilisable de l’existant PDF.

Il modélise :

- métadonnées du livre ;
- contributeurs ;
- informations de publication ;
- divisions éditoriales ;
- sections ;
- paragraphes ;
- citations longues ;
- figures ;
- listes ;
- vers ;
- bibliographies simples ;
- notes de bas de page ;
- éléments inline : texte, italique, gras, petites capitales, exposants, indices, liens, citations inline, appels de notes.

Le modèle est sobre et compréhensible. Il est adapté à une petite équipe éditoriale, à condition de ne pas l’étendre trop vite dans toutes les directions.

Limites actuelles :

- pas de modèle de tableau ;
- pas de bibliographie structurée de type `biblStruct` ;
- pas de modèle explicite pour `choice/abbr/expan` ;
- pas de modèle explicite pour `foreign`, `term`, `persName`, `placeName`, `orgName`, `date`, `num`, `label`;
- pas de modèle d’ancre ou de référence interne stabilisée ;
- pas de modèle d’index ;
- pas de distinction avancée entre figures, légendes, descriptions alternatives, crédits et sources.

### `purh_site/tei_to_model.py`

Ce module parse la TEI normalisée vers `semantic_model.Book`.

Il utilise `lxml.etree`, pas des regex, ce qui est un bon point. Les expressions régulières servent surtout à reconnaître des valeurs de `@rend`, des niveaux de section ou des types.

Rôle :

- lire un fichier TEI normalisé ;
- extraire les métadonnées principales ;
- extraire les divisions front/body/back ;
- convertir les blocs TEI en blocs sémantiques ;
- convertir les éléments inline TEI en inline sémantiques ;
- collecter des notes de bas de page.

Hypothèse de départ :

- le module part d’une TEI déjà normalisée, typiquement `book.normalized.xml`;
- il ne semble pas destiné à parser directement toute la variété du XML Métopes brut.

Maturité :

- claire et lisible ;
- réelle, pas seulement esquissée ;
- mais partielle, et non alignée avec toutes les corrections HTML récentes.

Éléments bien pris en charge :

- divisions front/body/back ;
- quelques types de divisions : préface, introduction, chapitre, conclusion, bibliographie, appendice, partie ;
- sections de type `section1`, `section2`, etc. ;
- paragraphes ;
- `hi` avec rendus courants : italique, gras, petites capitales, exposants, indices ;
- liens simples `ref`;
- notes si `place="foot"` ou `type="standard"`;
- citations inline simples ;
- citations blocs ;
- listes simples ;
- vers ;
- figures simples ;
- bibliographies simples `listBibl/bibl`.

Éléments fragiles ou ignorés :

- notes sans `@place` ni `@type`, alors que les exemples TEI/HTML utilisent souvent `<note>` simple ;
- tableaux TEI ;
- bibliographies structurées `biblStruct` ;
- `choice/abbr/expan` ;
- `foreign`;
- noms savants structurés ;
- `ptr`;
- `pb` et `lb` au-delà d’une simplification ;
- `date`, `num`, `label` comme éléments sémantiques ;
- références internes entre pages ;
- `xml:id` comme ancres LaTeX ;
- `figDesc` comme alternative textuelle ;
- multiples `graphic` dans une même figure ;
- titres et auteurs de page issus de `data-page-title`, `data-page-subtitle`, `data-page-authors`.

Risque de duplication :

Le parseur reproduit une partie des décisions portées par le XSLT HTML, mais avec une couverture différente. Cela peut devenir un problème si les deux chemins divergent. Par exemple, le HTML sait maintenant rendre tableaux, bibliographies structurées, figures plus riches, citations contextuelles et objets inline savants ; le modèle LaTeX ne les reflète pas encore.

### `purh_site/latex_renderer.py`

Ce module transforme le modèle sémantique en document LaTeX complet.

Il produit :

- un préambule complet ;
- une page de titre ;
- `frontmatter`, `mainmatter`, `backmatter`;
- une table des matières optionnelle ;
- des divisions et sections ;
- des paragraphes ;
- des citations longues ;
- des figures ;
- des listes ;
- des vers ;
- des bibliographies simples ;
- des notes en `\footnote`.

Points positifs :

- rendu LaTeX centralisé ;
- échappement des caractères LaTeX spéciaux ;
- utilisation de LuaLaTeX via `fontspec` et `polyglossia`;
- recours à `microtype`, `csquotes`, `hyperref`, `bookmark`;
- options de rendu regroupées dans `LatexRenderOptions`;
- séparation nette entre parseur TEI, modèle sémantique et rendu LaTeX.

Limites :

- pas de rendu de tableaux ;
- pas de rendu bibliographique structuré ;
- pas de `\label` / `\ref` pour les références internes ;
- pas de stratégie d’index ;
- figures rendues en bloc centré plutôt qu’en flottants LaTeX structurés ;
- légendes de figures rendues comme paragraphes plutôt qu’avec `\caption`;
- pas de classe `.cls` PURH ;
- pas de template LaTeX externe ;
- pas de biber/biblatex ;
- pas de tests automatisés.

Le LaTeX produit peut être compilable dans les cas simples, mais ne doit pas encore être considéré comme une sortie éditoriale finale.

### `purh_site/pdf_builder.py`

Ce module orchestre la génération PDF.

Fonctionnalités :

- lit une TEI normalisée ;
- parse vers le modèle sémantique ;
- absolutise certains chemins de figures ;
- écrit `book.tex`;
- compile optionnellement avec `lualatex`;
- écrit `latex_build.log`;
- écrit `pdf_build_report.txt`;
- retourne un `PdfBuildResult`.

Le builder est robuste dans son principe :

- il ne plante pas brutalement en cas d’erreur ;
- il signale les warnings ;
- il permet `compile_pdf=False`;
- il détecte l’absence du moteur LaTeX via `shutil.which`;
- il encapsule statistiques, chemins, commandes et messages d’erreur.

Mais il est actuellement séparé du build principal :

- `SiteBuilder` ne l’appelle pas ;
- `BuildConfig` ne semble pas exposer `write_latex` ou `build_pdf`;
- il n’y a pas de workflow utilisateur intégré ;
- il n’y a pas de tests pytest associés.

### `test_pdf_build.py`

Ce fichier racine est un script manuel de test :

```powershell
python test_pdf_build.py XML SORTIE --no-compile
```

Il est utile pour expérimenter, mais ce n’est pas un test automatisé de la suite `pytest`.

Il permet :

- de choisir le moteur ;
- de désactiver la compilation ;
- d’afficher chemins, statistiques et warnings ;
- de retourner un code non nul en cas d’échec.

Il peut servir de base pour documenter l’usage manuel, mais il ne remplace pas des tests unitaires et d’intégration.

## 4. Existant PDF

La génération PDF existante est autonome et expérimentale.

Elle produit :

- `book.tex`;
- éventuellement `book.pdf`;
- `latex_build.log`;
- `pdf_build_report.txt`.

Moteur prévu :

- `lualatex` par défaut.

Dépendances LaTeX :

- `memoir`;
- `fontspec`;
- `polyglossia`;
- `microtype`;
- `graphicx`;
- `csquotes`;
- `hyperref`;
- `bookmark`;
- `caption`;
- `enumitem`;
- `verse`;
- `ragged2e`;
- `xurl`.

Il n’y a pas d’usage repéré de :

- Pandoc ;
- WeasyPrint ;
- ReportLab ;
- wkhtmltopdf ;
- template `.tex` externe ;
- classe `.cls` projet ;
- fichier `.bib` ;
- BibTeX ou biber.

La seule mention PDF côté site web concerne surtout la présence d’un PDF déjà existant comme ressource téléchargeable. Ce n’est pas une génération PDF.

Code non appelé par le build principal :

- `PdfBuilder`;
- `build_pdf_from_normalized_tei`;
- `LatexRenderer`;
- `TeiToModelParser`.

Ces éléments ne sont pas du code mort au sens strict : ils forment une chaîne cohérente. Mais ils sont aujourd’hui hors du chemin utilisateur standard.

## 5. Couverture TEI actuelle

### Divisions et titres

Couverture partielle.

Le parseur reconnaît plusieurs types de divisions et génère des chapitres, parties ou sections LaTeX. En revanche, il ne semble pas utiliser la même logique que `SiteStructureBuilder`, notamment pour :

- `data-page-title`;
- `data-page-subtitle`;
- `data-page-authors`;
- ordre et découpage exacts des pages web ;
- contributions ou pages collectives telles que stabilisées côté HTML.

Risque : le PDF peut ne pas avoir le même découpage éditorial que le site.

### Paragraphes

Couverture correcte pour les paragraphes simples.

Certains `@rend` produisent des effets :

- signature ;
- lead ;
- break.

La couverture reste sobre, mais suffisante pour un premier `.tex`.

### Emphases, italique, gras, petites capitales, exposants, indices

Couverture raisonnable.

`hi rend="italic"`, `bold`, petites capitales, exposants et indices sont rendus vers des commandes LaTeX. C’est une base utile pour les petits objets typographiques.

### Citations

Couverture partielle.

Le modèle distingue :

- citations inline ;
- citations longues.

Le rendu utilise `\enquote{...}` pour l’inline et un environnement maison pour les citations blocs.

Limites :

- pas de traitement approfondi de `cit/quote/bibl`;
- pas de contexte bibliographique riche ;
- pas de politique spécifique pour les citations dans les notes ou listes au niveau du modèle.

### Listes

Couverture simple.

Les listes ordonnées et non ordonnées sont rendues en `enumerate` ou `itemize`. Les listes complexes ou imbriquées restent à tester.

### Tableaux

Non pris en charge dans le modèle actuel.

C’est une différence importante avec le HTML, qui possède déjà un rendu minimal de `table`, `row`, `cell`.

### Figures

Couverture simple.

Le parseur prend en charge une figure avec une image principale, un titre, une légende et des crédits dans certains cas.

Limites importantes :

- `figDesc` n’est pas exploité comme description alternative ;
- plusieurs `graphic` ne sont pas vraiment modélisés ;
- les attributs de dimensions ne semblent pas au centre du modèle ;
- les figures sont rendues en environnement centré plutôt qu’en flottant avec `\caption`;
- les chemins sont absolutisés par `PdfBuilder`, ce qui aide la compilation mais peut compliquer la portabilité des sources `.tex`.

### Notes

Couverture fragile.

Les notes peuvent devenir des `\footnote`, mais seulement si elles correspondent aux conditions du parseur, notamment `place="foot"` ou `type="standard"`.

Risque majeur : des notes TEI simples `<note>...</note>` peuvent ne pas devenir des notes de bas de page dans le PDF, alors qu’elles sont prises en charge côté HTML.

Les notes riches avec paragraphes, listes, bibliographies ou citations ne sont pas garanties.

### Bibliographie simple

Couverture partielle.

`listBibl/bibl` peut produire un bloc bibliographique textuel. C’est utile pour une bibliographie déjà formulée dans la TEI.

### Bibliographie structurée

Non prise en charge sérieusement.

Le HTML a maintenant une logique pour `biblStruct`, auteurs multiples, directeurs, DOI, URI, ponctuation. Le chemin LaTeX ne semble pas en bénéficier.

### Références internes

Couverture faible.

`ref` devient un lien, mais il n’y a pas de stratégie complète :

- pas d’index global d’ancres ;
- pas de `\label`;
- pas de résolution inter-pages ;
- pas d’adaptation au passage web -> livre imprimé ;
- pas de distinction claire entre URL externe, référence interne et note.

### Métadonnées

Couverture partielle.

Le modèle extrait quelques métadonnées livre : titre, sous-titre, contributeurs, publication, ISBN, ISSN, DOI, résumé.

Mais il ne reprend pas toute la logique Zotero/Dublin Core stabilisée côté HTML :

- page de chapitre ;
- rôle auteur/directeur ;
- volume collectif ;
- URL publique ;
- DOI normalisé ;
- crédits et citabilité.

### Page de titre

Couverture existante.

`latex_renderer.py` produit une page de titre. Elle peut servir de base, mais elle n’est pas encore une page de titre PURH.

### Sommaire

Couverture existante.

Le renderer produit une table des matières LaTeX optionnelle.

À vérifier :

- niveau de profondeur ;
- cohérence avec le découpage HTML ;
- parties et chapitres non numérotés ;
- entrées front/back.

### Crédits

Couverture faible.

Le PDF n’intègre pas encore la logique récente du bloc visible “Crédits et citabilité”.

### Index

Non repéré.

## 6. Qualité typographique potentielle

Le choix de LuaLaTeX, `fontspec`, `polyglossia`, `microtype`, `csquotes` et `memoir` est bon pour un futur PDF savant français. C’est nettement préférable à une génération PDF directe depuis HTML pour viser un rendu universitaire propre.

Points favorables :

- UTF-8 naturel avec LuaLaTeX ;
- gestion correcte du français possible via `polyglossia`;
- `csquotes` pour les citations ;
- `microtype` pour la qualité de justification ;
- `memoir` pour une mise en page de livre ;
- hyperliens et métadonnées PDF via `hyperref`.

Points insuffisants pour un PDF PURH :

- pas de classe éditoriale `.cls`;
- pas de template typographique maison ;
- pas de politique de notes complète ;
- pas de vraie stratégie bibliographique ;
- figures et légendes trop simples ;
- tableaux absents ;
- pas de gestion des veuves et orphelines au niveau éditorial ;
- pas de réglage fin des niveaux de titres ;
- pas de politique complète pour espaces insécables, siècles, abréviations savantes et appels de notes ;
- pas de test de compilation automatisé ou optionnel.

Le LaTeX existant peut donc servir de socle technique, mais pas encore de sortie PDF de référence.

## 7. Problèmes et risques

### Risque 1 — Chaîne PDF non intégrée

Symptôme : `SiteBuilder` ne déclenche pas `PdfBuilder`.

Cause probable : la génération PDF a été développée à côté de la chaîne web.

Gravité : moyenne à forte.

Correction recommandée : ne pas intégrer brutalement ; ajouter d’abord une option explicite et testée, probablement en deux temps : `write_latex`, puis `build_pdf`.

Tests à ajouter : build sans PDF, build avec `.tex` seulement, build avec compilation désactivée.

### Risque 2 — Divergence HTML / LaTeX

Symptôme : le HTML prend en charge beaucoup plus de TEI que le modèle LaTeX.

Cause probable : deux chemins de rendu ont évolué séparément.

Gravité : forte.

Correction recommandée : identifier les règles éditoriales communes et les faire remonter progressivement dans le modèle sémantique ou dans des helpers partagés. Ne pas tenter de copier tout le XSLT en Python d’un coup.

Tests à ajouter : mêmes fixtures TEI minimales pour HTML et LaTeX sur notes, figures, tableaux, bibliographies, citations.

### Risque 3 — Découpage éditorial différent

Symptôme : `tei_to_model.py` ne semble pas réutiliser `SiteStructureBuilder`.

Cause probable : le PDF parse directement la TEI selon sa propre logique.

Gravité : forte.

Correction recommandée : réutiliser l’ordre et les définitions de pages de `SiteStructureBuilder`, ou au minimum ajouter des tests garantissant que PDF et HTML parcourent le livre dans le même ordre.

Tests à ajouter : livre avec parties, chapitres, contributions, pages sans titre explicite.

### Risque 4 — Notes incomplètes

Symptôme : les notes simples sans `place` ou `type` risquent de ne pas devenir des `\footnote`.

Cause probable : condition stricte dans le parseur.

Gravité : forte pour un livre universitaire.

Correction recommandée : tester les notes Métopes réelles avant de modifier ; harmoniser avec la politique HTML.

Tests à ajouter : note simple, note riche, note avec bibliographie, note avec citation, note avec plusieurs paragraphes.

### Risque 5 — Bibliographies structurées absentes

Symptôme : `biblStruct` n’est pas couvert comme dans le HTML.

Cause probable : modèle bibliographique trop simple.

Gravité : forte.

Correction recommandée : commencer par rendre lisible `biblStruct` en LaTeX sans CSL complet, en reprenant la politique HTML stabilisée.

Tests à ajouter : monographie, contribution, article, DOI, URI, auteurs/directeurs multiples.

### Risque 6 — Dépendance TeX système

Symptôme : compilation impossible si `lualatex` ou les packages sont absents.

Cause probable : dépendance système non déclarée dans `requirements.txt`.

Gravité : moyenne.

Correction recommandée : rendre la compilation strictement optionnelle ; produire d’abord un `.tex`; signaler clairement l’absence de moteur.

Tests à ajouter : génération `.tex` sans compilation ; comportement si moteur absent.

### Risque 7 — Windows et chemins

Symptôme : figures absolutisées, chemins transmis à LaTeX, moteur externe.

Cause probable : interaction entre chemins Windows, LuaLaTeX et fichiers locaux.

Gravité : moyenne.

Correction recommandée : tester sur Windows avec espaces dans les chemins ; envisager une copie contrôlée des images PDF dans un dossier build plutôt que des chemins absolus.

Tests à ajouter : figure dans chemin relatif, chemin avec espace, image manquante.

### Risque 8 — PDF médiocre si raccourci HTML -> PDF

Symptôme : tentation possible de générer le PDF depuis le HTML stabilisé.

Cause probable : le HTML est plus mature que le LaTeX.

Gravité : forte éditorialement.

Correction recommandée : éviter ce raccourci pour le PDF livre. Le HTML peut inspirer les règles, mais la sortie livre doit rester LaTeX ou passer par un moteur typographique adapté.

## 8. Recommandation d’architecture

### Ne pas brancher immédiatement dans `SiteBuilder`

`SiteBuilder` doit rester le builder web. Il peut orchestrer plus tard un appel optionnel à un builder PDF, mais il ne doit pas absorber la logique LaTeX.

Recommandation :

- conserver `PdfBuilder` comme module séparé ;
- ajouter plus tard une option de configuration explicite ;
- ne pas compiler le PDF par défaut ;
- produire d’abord un `.tex` reproductible.

### Produire un `.tex` avant de produire un PDF

La première cible stable doit être `book.tex`.

Pourquoi :

- testable sans TeX Live ;
- inspectable par une équipe éditoriale ;
- utilisable même si la compilation locale n’est pas disponible ;
- moins fragile en CI.

Options futures possibles :

- `write_latex=True`;
- `build_pdf=False` par défaut ;
- `latex_engine="lualatex"`;
- `latex_runs=2`.

### Partir de la TEI normalisée

C’est cohérent avec l’existant. La TEI normalisée doit rester le point d’entrée PDF, car elle évite de répliquer la résolution d’inclusions et les nettoyages initiaux.

Mais il faut vérifier que la normalisation conserve toutes les informations utiles au PDF :

- `xml:id`;
- titres ;
- auteurs de pages ;
- notes ;
- figures ;
- bibliographies ;
- métadonnées.

### Réutiliser `SiteStructureBuilder`

Le PDF doit suivre le même ordre éditorial que le site web.

Deux options raisonnables :

1. `SiteStructureBuilder` fournit l’ordre des pages et leurs métadonnées, tandis que `tei_to_model.py` parse le contenu.
2. Le modèle sémantique est construit directement à partir d’une structure partagée.

La première option est plus prudente et compatible avec l’existant.

### Garder un modèle pivot, mais l’aligner

`semantic_model.py` est une bonne base. Il faut l’étendre par petites familles TEI :

- tables ;
- bibliographies structurées ;
- figures enrichies ;
- références internes ;
- noms et langues ;
- dates et numéros ;
- ancres.

Il faut éviter de créer une seconde logique concurrente pour les règles déjà stabilisées côté HTML.

### Ne pas adopter Pandoc comme solution principale maintenant

Pandoc pourrait servir ponctuellement, mais l’existant possède déjà une chaîne TEI -> modèle -> LaTeX. Remplacer cela par Pandoc introduirait :

- une dépendance système supplémentaire ;
- des conversions parfois opaques ;
- une difficulté à reproduire les règles éditoriales PURH ;
- un risque de perdre le contrôle fin sur les notes, figures, bibliographies et titres.

Pandoc peut rester une option d’expérimentation, pas l’architecture principale.

### Prévoir une classe ou un template PURH plus tard

La mise en page finale devrait sortir progressivement du code Python :

- soit vers une classe `.cls`;
- soit vers un template `.tex`;
- soit vers une combinaison des deux.

Mais ce n’est pas la première étape. Il faut d’abord stabiliser le contenu sémantique.

## 9. Plan de développement par petites passes

### Passe 12A — Tests de l’existant TEI -> modèle -> LaTeX

Objectif : documenter le comportement actuel sans chercher encore une qualité PDF finale.

À faire :

- créer `tests/test_latex_renderer.py` ou `tests/test_pdf_latex.py`;
- tester `parse_normalized_tei`;
- tester `LatexRenderer.render_book`;
- tester `PdfBuilder` avec `compile_pdf=False`;
- vérifier qu’un `.tex` minimal est écrit.

### Passe 12B — Alignement minimal avec la structure du site

Objectif : garantir que le PDF suit le même ordre éditorial que le site.

À faire :

- tests sur livre simple ;
- tests sur parties et chapitres ;
- tests sur contributions ;
- tests sur page sans titre ;
- décider comment réutiliser `SiteStructureBuilder`.

### Passe 13 — Génération `.tex` minimale depuis TEI normalisée

Objectif : rendre une sortie `.tex` fiable, sans compilation obligatoire.

À faire :

- option `write_latex`;
- chemin de sortie documenté ;
- rapport de build ;
- tests sans dépendance TeX.

### Passe 14 — Compilation LuaLaTeX optionnelle

Objectif : compiler seulement si demandé et si le moteur existe.

À faire :

- option `build_pdf`;
- message clair si `lualatex` absent ;
- test avec moteur absent ou mocké ;
- logs propres.

### Passe 15 — Notes, figures, tableaux

Objectif : couvrir les objets universitaires essentiels.

À faire :

- notes simples et riches ;
- figures avec `figDesc`, plusieurs `graphic`, crédits ;
- tableaux simples ;
- images manquantes signalées.

### Passe 16 — Bibliographies structurées et références

Objectif : reprendre la maturité HTML côté LaTeX.

À faire :

- `biblStruct` ;
- auteurs et directeurs multiples ;
- DOI/URI ;
- références internes avec `\label` / `\hyperref`;
- bibliographies dans les notes.

### Passe 17 — Template ou classe PURH

Objectif : sortir du rendu générique.

À faire :

- template `.tex` ou classe `.cls`;
- page de titre ;
- styles de titres ;
- notes ;
- figures ;
- tables ;
- sommaire ;
- métadonnées PDF.

### Passe 18 — Rapport qualité PDF

Objectif : signaler les problèmes PDF sans bloquer le build.

À faire :

- figures manquantes ;
- références non résolues ;
- compilation absente ;
- erreurs LaTeX ;
- warnings importants ;
- log lisible pour l’équipe éditoriale.

## 10. Tests recommandés

Tests prioritaires avant toute modification fonctionnelle :

1. Génération `.tex` minimale sans compilation.
2. Livre avec titre, sous-titre, auteur, éditeur, date.
3. Deux chapitres dans le bon ordre.
4. Partie contenant plusieurs chapitres.
5. Paragraphes et titres.
6. Italique, gras, petites capitales, exposants, indices.
7. Note simple `<note>`.
8. Note riche avec deux paragraphes.
9. Citation inline et citation bloc.
10. Liste simple.
11. Figure avec `graphic`, `head`, `figDesc`.
12. Figure avec image manquante.
13. Tableau simple.
14. Bibliographie simple `listBibl/bibl`.
15. Bibliographie structurée `biblStruct`.
16. DOI et URI dans bibliographie.
17. Référence interne simple.
18. Génération avec `compile_pdf=False`.
19. Compilation demandée mais moteur absent.
20. Compilation échouée avec rapport lisible.

Ces tests doivent d’abord vérifier le `.tex` produit, pas le PDF final. La compilation réelle doit rester optionnelle pour éviter de rendre la suite dépendante de TeX Live.

## 11. Conclusion

La branche possède déjà une base sérieuse pour préparer le PDF : un modèle sémantique, un parseur TEI normalisée, un renderer LaTeX et un builder PDF séparé. C’est une bonne direction.

Mais cette chaîne n’est pas encore alignée avec la maturité du HTML. Elle ne doit pas être branchée trop vite dans le build principal. La priorité est de la rendre observable par tests, de stabiliser la génération `.tex`, puis d’ajouter la compilation PDF comme option explicite.

La stratégie recommandée est donc prudente :

- garder `PdfBuilder` séparé ;
- partir de la TEI normalisée ;
- réutiliser `SiteStructureBuilder` pour l’ordre éditorial ;
- produire d’abord un `.tex`;
- compiler seulement sur demande ;
- étendre la couverture TEI par petites familles ;
- reporter la classe ou le template PURH à une étape ultérieure, une fois le contenu fiable.

La tentation principale à éviter est une intégration rapide qui mélangerait la chaîne web et la chaîne papier. Le projet a désormais une base web solide ; la chaîne PDF doit devenir solide à son tour, mais avec sa propre progression testée.
