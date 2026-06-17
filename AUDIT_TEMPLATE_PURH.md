# Audit du template LaTeX PURH

## 1. Résumé exécutif

Le fichier `template.tex` annoncé pour cette passe n’est pas présent dans le workspace actuel `C:\impression2`. L’audit technique du template lui-même ne peut donc pas être réalisé sans risquer d’inventer des informations sur son contenu.

Vérifications effectuées :

- recherche de `template.tex` à la racine du projet ;
- recherche de tout fichier `*.tex` dans le workspace ;
- recherche ciblée dans `.codex` ;
- inspection de la racine du dépôt.

Résultat : aucun fichier `.tex` exploitable n’a été trouvé.

Ce rapport documente donc :

- l’état réel observable ;
- la grille d’analyse à appliquer dès que `template.tex` sera disponible ;
- les points de comparaison déjà certains avec `purh_site/latex_renderer.py` ;
- la stratégie d’intégration prudente recommandée, sans brancher quoi que ce soit.

## 2. Nature du template fourni

Le template n’a pas pu être inspecté, car le fichier `template.tex` est absent du dépôt au moment de l’audit.

État observable :

- aucun `template.tex` à la racine ;
- aucun fichier `.tex` trouvé par `rg --files -g "*.tex"` ;
- aucun `template.tex` trouvé dans `.codex`.

Conséquence :

- impossible de confirmer le moteur attendu ;
- impossible de lister les packages réellement utilisés ;
- impossible d’identifier les contenus codés en dur ;
- impossible de savoir si les variables de type `$title$`, `$body$`, `$for(authors)$` relèvent d’un template Pandoc, d’un vestige ou d’un mécanisme maison.

## 3. Dépendances et portabilité

### État vérifiable

Le template n’étant pas disponible, aucune dépendance propre à celui-ci ne peut être validée.

### Points à auditer dès disponibilité du fichier

Il faudra relever précisément :

- `\documentclass`;
- moteur implicite ou explicite ;
- packages ;
- polices ;
- appels à des programmes externes ;
- chemins locaux ;
- images ou SVG ;
- code source ou listings.

Attention particulière à porter sur :

- `minted` : dépend de Pygments et nécessite généralement `-shell-escape`;
- `svg` : peut dépendre d’Inkscape et de conversions externes ;
- `fontspec` : impose XeLaTeX ou LuaLaTeX ;
- `inputenc` / `fontenc` : plutôt liés à pdfLaTeX, souvent inutiles ou problématiques avec LuaLaTeX ;
- `babel` : peut coexister avec LuaLaTeX, mais le renderer actuel utilise `polyglossia`;
- `crop` : utile pour imprimeur, mais à rendre optionnel ;
- `classics`, `scrextend`, `titlesec`, `fancyhdr` : à vérifier selon disponibilité TeX Live et compatibilité avec `memoir`.

### Comparaison certaine avec l’existant

`purh_site/latex_renderer.py` utilise déjà :

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

Le moteur attendu par l’existant PDF est `lualatex`, piloté par `purh_site/pdf_builder.py`.

## 4. Contenus codés en dur

Le fichier étant absent, aucun contenu codé en dur ne peut être listé factuellement.

Dès que le template sera disponible, il faudra relever tout contenu propre à un livre antérieur, notamment :

- nom de collection ;
- direction de collection ;
- présentation de collection ;
- crédits éditoriaux ;
- noms de préfacier, postfacier, directeur ou auteur ;
- année ;
- ISBN ;
- ISSN ;
- licence ;
- URL ;
- DOI ;
- crédits image ;
- mentions d’imprimeur ;
- noms propres propres au livre source ;
- chemins de fichiers locaux ;
- titres et sous-titres particuliers.

Politique recommandée :

- tout contenu propre à un livre doit sortir du template générique ;
- les métadonnées doivent venir du modèle sémantique ou d’options explicites ;
- les mentions éditoriales stables peuvent devenir des paramètres, pas du texte figé.

## 5. Éléments typographiques réutilisables

Comme le template n’est pas inspectable, les éléments suivants ne peuvent pas être validés. Ils constituent toutefois la grille de récupération à appliquer.

### Format papier

À comparer avec l’existant :

- `LatexRenderOptions.paper_width_mm = 155`;
- `LatexRenderOptions.paper_height_mm = 230`;
- marges internes et externes dans le renderer actuel.

Décision probable : adapter ou rendre configurable.

### Marges

Le renderer utilise déjà `memoir` :

- `\setstocksize`;
- `\settrimmedsize`;
- `\setlrmarginsandblock`;
- `\setulmarginsandblock`;
- `\checkandfixthelayout`.

Si le template PURH contient des marges plus proches d’un ouvrage imprimé réel, elles pourront nourrir `LatexRenderOptions`.

Décision probable : adapter dans les options, pas copier brutalement.

### Repères de coupe

Si le template utilise `crop`, il faudra rendre ce comportement optionnel.

Décision probable : reporter ou rendre configurable, car les repères imprimeur ne doivent pas être actifs dans tous les PDF.

### Polices

Le renderer actuel utilise :

- TeX Gyre Pagella ;
- TeX Gyre Heros ;
- Latin Modern Mono.

Si le template utilise des polices commerciales ou locales, elles ne doivent pas devenir obligatoires.

Décision probable : proposer des alternatives libres par défaut, rendre les fontes configurables plus tard.

### Styles de titres

Le renderer actuel s’appuie surtout sur les styles `memoir` par défaut et quelques macros maison.

Si le template contient une hiérarchie PURH intéressante, elle peut inspirer :

- styles de parties ;
- styles de chapitres ;
- styles de sections ;
- profondeurs de table des matières.

Décision probable : adapter progressivement, idéalement dans un préambule PURH minimal ou une future classe.

### En-têtes courants

Le renderer actuel ne semble pas encore porter une politique avancée d’en-têtes courants.

Si le template utilise `fancyhdr`, il faudra vérifier la compatibilité avec `memoir`, qui possède déjà ses propres mécanismes de pagestyle.

Décision probable : adapter avec les outils `memoir` plutôt que multiplier les packages.

### Notes de bas de page

Le renderer possède déjà une sortie `\footnote`.

Si le template contient des réglages robustes de notes, ils peuvent être repris prudemment :

- espacements ;
- largeur de marque ;
- style d’appel ;
- taille.

Décision probable : adapter après tests de notes simples et notes riches.

### Citations

Le renderer utilise `csquotes` et un environnement `PurhBlockQuote`.

Si le template a une mise en forme de citation plus éditoriale, elle pourra remplacer ou nourrir cet environnement.

Décision probable : adapter.

### Figures

Le renderer rend actuellement les figures en bloc centré avec `\includegraphics`, sans vrai flottant ni `\caption`.

Si le template contient une bonne politique de figures, elle sera utile, mais il faudra d’abord améliorer le modèle sémantique côté figures.

Décision probable : reporter après consolidation des figures TEI.

### Table des matières

Le renderer produit `\tableofcontents`.

Si le template ajuste la profondeur, les espacements ou le style, ces réglages peuvent migrer.

Décision probable : adapter après tests de structure PDF.

### Page de titre, page crédits, page collection

Ce sont probablement les éléments les plus intéressants d’un template PURH antérieur, mais aussi les plus susceptibles de contenir du texte codé en dur.

Décision probable :

- reprendre l’inspiration visuelle ;
- rendre tous les contenus dynamiques ;
- ne pas copier le texte brut du livre source.

## 6. Éléments à éviter ou reporter

À éviter tant que le template n’a pas été nettoyé :

- dépendance obligatoire à `minted`;
- dépendance obligatoire à `svg`;
- obligation de `-shell-escape`;
- chemins locaux ;
- polices commerciales non disponibles ;
- contenus éditoriaux codés en dur ;
- réglages incompatibles avec `memoir`;
- mélange `inputenc` / `fontenc` avec `fontspec` sans nécessité ;
- intégration massive dans `LatexRenderer`.

À reporter :

- classe `.cls` PURH ;
- gestion imprimeur complète avec traits de coupe ;
- template externe actif ;
- système de variables riche ;
- compilation PDF par défaut ;
- intégration au build web.

## 7. Comparaison avec latex_renderer.py

### Ce que le renderer possède déjà

`purh_site/latex_renderer.py` fournit déjà :

- document complet ;
- classe `memoir`;
- options de format ;
- fontes configurables ;
- LuaLaTeX via `fontspec`;
- langue française via `polyglossia`;
- `microtype`;
- `graphicx`;
- `csquotes`;
- `hyperref`;
- `bookmark`;
- `caption`;
- `enumitem`;
- `verse`;
- `ragged2e`;
- `xurl`;
- page de titre simple ;
- frontmatter / mainmatter / backmatter ;
- table des matières ;
- rendus de divisions, sections, paragraphes, citations, figures, listes, vers, bibliographie simple, notes.

### Ce qui manque probablement par rapport à un vrai template PURH

Même sans inspecter `template.tex`, les manques probables du renderer sont clairs :

- style éditorial des pages de titre ;
- page de collection ;
- page de crédits ;
- en-têtes courants ;
- réglages typographiques fins des titres ;
- vrais flottants figures avec légendes ;
- politique de notes plus complète ;
- réglages imprimeur ;
- gabarit PURH stable.

### Où placer les futurs réglages

Dans `LatexRenderOptions` :

- format papier ;
- marges ;
- fontes ;
- moteur ;
- activation traits de coupe ;
- profondeur de table des matières.

Dans un futur template externe :

- préambule PURH ;
- macros éditoriales ;
- mise en page de titre ;
- pages de crédits ;
- styles de chapitres.

Dans le modèle sémantique :

- données nécessaires aux pages de titre ;
- crédits ;
- collection ;
- figures enrichies ;
- bibliographies structurées ;
- références.

À éviter dans le renderer :

- gros blocs de texte éditorial codés en dur ;
- chemins locaux ;
- logique de compilation ;
- dépendances à `shell-escape`.

## 8. Recommandation d’architecture

La recommandation centrale reste : ne pas intégrer massivement le template.

Étapes prudentes :

1. Ajouter le fichier `template.tex` au dépôt ou le placer explicitement dans un chemin auditable.
2. Refaire cet audit avec contenu réel.
3. Extraire seulement les décisions typographiques génériques.
4. Conserver `LatexRenderer` comme générateur complet pour l’instant.
5. Introduire plus tard un template externe minimal, si le besoin devient clair.

### Faut-il extraire un préambule PURH minimal ?

Oui, mais pas avant d’avoir audité le fichier réel.

Le bon premier préambule PURH serait petit :

- format ;
- marges ;
- fontes libres ou configurables ;
- langue française ;
- microtype ;
- hyperref ;
- styles simples.

### Faut-il créer `purh_site/resources/purh_book_template.tex` ?

Pas dans cette passe.

Cela peut être pertinent plus tard, mais seulement après nettoyage du template fourni et identification des placeholders nécessaires.

### Faut-il créer une classe `.cls` ?

Pas maintenant.

Une classe `.cls` PURH peut devenir la bonne solution éditoriale à moyen terme, mais elle doit arriver après stabilisation :

- du modèle sémantique ;
- des fixtures TEI ;
- du rendu `.tex`;
- des besoins réels de mise en page.

### Faut-il garder `LatexRenderer` ?

Oui.

`LatexRenderer` est aujourd’hui le point de génération le plus simple à tester. Le remplacer trop tôt par un template externe augmenterait le risque.

### Placeholders : Jinja, `string.Template` ou maison ?

À court terme, éviter Jinja si les besoins restent simples.

Options recommandées :

- `string.Template` pour quelques blocs bien identifiés ;
- ou assemblage Python explicite, comme aujourd’hui.

Jinja ne devient intéressant que si le template externe devient riche, avec conditions et boucles nombreuses.

### Faut-il éviter Pandoc ?

Oui pour l’architecture principale actuelle.

La présence éventuelle de variables `$title$`, `$body$`, `$for(authors)$` indiquerait peut-être un héritage Pandoc, mais Impressions possède déjà une chaîne TEI -> modèle -> LaTeX. Passer par Pandoc maintenant risquerait :

- de dupliquer la chaîne ;
- de perdre le contrôle éditorial fin ;
- d’introduire une dépendance système ;
- de contourner les tests déjà ajoutés sur le renderer.

Pandoc peut rester une référence ou un outil d’expérimentation, pas le cœur de la génération PDF.

## 9. Plan d’intégration par petites passes

### Passe 12B-bis — Audit réel du fichier fourni

À faire dès que `template.tex` est présent :

- lister packages ;
- lister polices ;
- lister contenus codés en dur ;
- lister dépendances système ;
- repérer les variables ;
- comparer ligne à ligne avec le préambule actuel.

### Passe 13A — Test de style LaTeX minimal

Ajouter un test de rendu `.tex` vérifiant :

- format ;
- marges ;
- fontes ;
- absence de `None`;
- absence de contenus codés en dur.

Sans compilation.

### Passe 13B — Options de page et fontes

Étendre prudemment `LatexRenderOptions` si nécessaire :

- formats PURH ;
- marges PURH ;
- fonte principale ;
- fonte sans ;
- fonte mono.

### Passe 14 — Préambule PURH minimal

Créer une méthode ou ressource dédiée au préambule, mais rester testable sans TeX.

Objectif :

- ne pas brancher tout le template ;
- reprendre seulement les réglages validés.

### Passe 15 — Pages liminaires

Travailler la page de titre, les crédits et la page collection à partir des métadonnées, sans texte codé en dur.

### Passe 16 — Figures, notes, tableaux

Adapter la mise en page aux objets TEI stabilisés.

### Passe 17 — Classe `.cls` ou template externe

Décider seulement après plusieurs PDF générés et relus.

## 10. Conclusion

L’audit complet de `template.tex` est bloqué par l’absence du fichier dans le workspace actuel. Aucun diagnostic précis sur ses packages, fontes, contenus codés en dur ou dépendances ne peut être donné sans l’inspecter.

Ce qui est certain, en revanche :

- la chaîne LaTeX actuelle d’Impressions est déjà structurée ;
- elle utilise LuaLaTeX, `memoir`, `fontspec`, `polyglossia` et `microtype`;
- elle doit rester séparée du build web ;
- un template PURH antérieur doit être audité, nettoyé et réduit avant toute intégration ;
- la prochaine passe réaliste est un audit réel du fichier dès qu’il est disponible, puis une extraction très limitée de réglages typographiques génériques.

Aucun code ne doit être modifié tant que le contenu réel de `template.tex` n’a pas été analysé.
