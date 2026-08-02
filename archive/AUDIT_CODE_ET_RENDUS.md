# Audit code et rendus

Projet audité : générateur de livres statiques à partir de XML-TEI Commons Publishing Métopes.

Date de l'audit : 2026-07-11.

Périmètre effectivement vérifié :

- dépôt local `C:\impression2` ;
- chaîne XML TEI -> normalisation -> HTML/CSS/JS ;
- chaîne XML TEI -> normalisation -> LaTEI/LaTeX -> PDF ;
- fixture réelle utilisée pour génération : `tests/fixtures/metopes/heraldique_ii.book.normalized.xml` ;
- sorties générées dans `_audit_runtime/render_site` ;
- PDF inspecté : `_audit_runtime/render_site/assets/generated/book.pdf` ;
- HTML inspecté via `http://127.0.0.1:8765/index.html` et page de chapitre `04-lheraldique-de-jules-iii-ciocchi-del-monte-1550-1555-dans-lornement-pour-le-livre.html`.

Documents de référence demandés mais non trouvés dans les fichiers inventoriés : `HERALDIQUE_II.pdf`, `doc_table_corresp_commons.pdf`, `Coeur_seul.xml`. Le dépôt contient cependant des fixtures et des artefacts d'audit autour d'`heraldique_ii`, notamment `.audit_f1/latei/heraldique_ii.book.normalized.latei_mono.pdf`. L'évaluation du niveau PURH repose donc sur la fixture Métopes disponible et sur les sorties générées, pas sur une comparaison page à page avec un PDF imprimé officiel.

## A. Verdict général

Le projet est un prototype avancé, déjà capable de produire une édition statique complète sur un XML riche, mais il n'est pas encore un outil éditorial solide ni proche d'une mise en production PURH.

Verdict par axe :

| Axe | Niveau atteint | Verdict critique |
|---|---:|---|
| Qualité du code | Prototype avancé | Architecture globalement lisible, mais trop de logique concentrée dans `SiteBuilder`, règles dispersées et plusieurs chemins critiques insuffisamment verrouillés. |
| Fidélité au XML | Partielle, plutôt bonne pour le corps courant testé | Les notes et figures sont comptées correctement sur la fixture, mais la normalisation modifie des identifiants et numéros, les inclusions peuvent perdre des métadonnées, et certains éléments non reconnus ne sont pas signalés comme lacunes éditoriales. |
| PDF | Non publiable | PDF techniquement généré, polices incorporées, mais squelette éditorial incomplet, table des matières placée à la fin, images absentes acceptées, avertissements LaTeX nombreux, typographie et bibliographie insuffisantes. |
| HTML | Prototype lisible, non institutionnel | Site statique fonctionnel et navigable, mais ergonomie mobile médiocre, images manquantes, sémantique perfectible, notes dupliquées visuellement, métadonnées web faibles. |
| Couverture Commons Publishing Métopes | Partielle | Les structures courantes texte/notes/figures/citations/bibliographie simple sont présentes, mais tableaux, poésie, théâtre, langues, inclusions complexes, métadonnées fines et ressources sont insuffisamment éprouvés. |

Réponse nette : le générateur ne répond pas encore au niveau d'exigence d'une presse universitaire. Il constitue une base technique intéressante, mais il ne peut pas être utilisé comme chaîne de production sans passe de consolidation éditoriale, typographique et de fiabilité.

## B. Points forts

- La séparation initiale des responsabilités existe : chargement XML dans `purh_site/tei_loader.py`, normalisation dans `purh_site/normalizer.py`, construction dans `purh_site/site_builder.py`, rendu HTML par XSLT dans `purh_site/resources/tei_to_html.xsl`, rendu PDF par LaTEI/LaTeX dans `purh_site/latei_driver.py` et `purh_site/latei_preamble.py`.
- Le parseur XML désactive les entités externes : `purh_site/tei_loader.py:40` utilise `resolve_entities=False`. C'est un bon choix de sécurité.
- Les blancs XML ne sont pas détruits au chargement : `purh_site/tei_loader.py:40` utilise `remove_blank_text=False`.
- Les sorties importantes sont conservées comme artefacts : XML normalisé, HTML, LaTeX, PDF, rapports de génération.
- La fixture `heraldique_ii.book.normalized.xml` est riche : 471 notes, 177 figures, 514 bibliographies simples, 3501 éléments `hi`. Elle permet de détecter des problèmes réels plutôt que seulement des cas jouets.
- Le HTML préserve bien le nombre de notes sur cette fixture : 471 appels de note et 471 entrées d'endnotes ont été comptés dans les pages générées.
- Le PDF incorpore les polices utilisées. Commande exécutée : `pdffonts _audit_runtime/render_site/assets/generated/book.pdf`. Résultat : ChaparralPro, JosefinSans et CMSY10 sont incorporées et sous-ensembles, sans police bitmap détectée.
- Le site est réellement statique : l'inspection des sorties montre des HTML, CSS, JS et ressources locales, sans dépendance applicative serveur.
- Le projet possède déjà une suite de tests volumineuse : commande `python -m pytest tests -q -p no:cacheprovider --basetemp _audit_runtime/pytest`, résultat `498 passed`, `14 failed`, aucun test ignoré signalé.

## C. Problèmes bloquants

### C1. Les tests complets échouent

Catégorie : bug actuellement reproductible.

Commande :

```powershell
python -m pytest tests -q -p no:cacheprovider --basetemp _audit_runtime/pytest
```

Résultat :

```text
14 failed, 498 passed in 2022.90s (0:33:42)
```

Détail :

- `tests/test_latei_direct_book_skeleton.py::test_latei_direct_pdf_is_not_a_tiny_flat_smoke_output` échoue car `pdfinfo.cmd` renvoie `Le chemin d'accès spécifié est introuvable`, alors que le PDF existe et que `C:\texlive\2025\bin\windows\pdfinfo.exe` fonctionne. Problème d'environnement/outillage Windows, pas défaut du XML.
- 13 tests de `tests/test_site_asset_manifest.py` échouent car `assets/metadata/manifest.json` n'est pas généré. Le test attend ce fichier à `tests/test_site_asset_manifest.py:85-93`, mais `SiteBuilder().build_from_master(...)` ne l'écrit pas.

Impact : une chaîne éditoriale ne peut pas être considérée stable si sa suite complète échoue, surtout sur un manifeste censé décrire les ressources.

### C2. Le PDF place la table des matières à la fin du livre

Catégorie : bug actuellement reproductible ; défaut du modèle LaTeX/PDF, pas du XML.

Preuves :

- code : `purh_site/latei_driver.py:81-86` et `purh_site/latei_driver.py:175-188` écrivent le titre, le corps, puis `\cleardoublepage` et `\tableofcontents` juste avant `\end{document}` ;
- rendu : `_audit_runtime/pdf_pages/book_p353.png`, page 353 du PDF généré, affiche seulement `Table des matières` en fin d'ouvrage.

Impact : PDF non publiable. Une table des matières finale peut être un choix éditorial dans certains livres, mais rien dans le modèle ni dans les sorties ne signale un tel choix. Ici, c'est un ordre de compilation codé en dur.

### C3. Les images manquantes n'empêchent pas une génération marquée comme réussie

Catégorie : bug reproductible et risque éditorial majeur.

Commande de génération :

```powershell
python -c "from pathlib import Path; from purh_site.site_builder import SiteBuilder; from purh_site.config import BuildConfig; out=Path('_audit_runtime/render_site'); r=SiteBuilder().build_from_master(Path('tests/fixtures/metopes/heraldique_ii.book.normalized.xml'), BuildConfig(output_dir=out, pdf_export_mode='latei_pdf')); print(r)"
```

Résultat synthétique :

- 17 pages HTML générées ;
- PDF généré : `_audit_runtime/render_site/assets/generated/book.pdf` ;
- rapport : `LaTEI PDF produced successfully` ;
- rapport qualité : 177 images/graphics, toutes les ressources locales d'images de la fixture sont signalées manquantes.

Preuves code :

- `purh_site/site_builder.py:553-564` ajoute seulement des avertissements pour les images locales manquantes ;
- `purh_site/latei_assets.py:73-76` ignore l'image manquante après avertissement ;
- `purh_site/resources/latei_macros.tex:221-233` rend une boîte de substitution `Image absente ou non fournie`.

Preuves HTML :

- page `04-lheraldique-de-jules-iii-ciocchi-del-monte-1550-1555-dans-lornement-pour-le-livre.html`, ligne 80 : nombreuses images vers `assets/images/../icono/br/...` ;
- inspection navigateur : 177 images HTML, `naturalWidth = 0` pour les images inspectées.

Impact : résultat trompeur pour l'utilisateur. En mode production, une génération avec 177 images absentes ne doit pas être considérée éditorialement réussie.

### C4. Les XInclude ne sont pas suffisamment contrôlés

Catégorie : risque architectural et risque de sécurité/fiabilité.

Preuves code :

- `purh_site/tei_loader.py:47` et `purh_site/tei_loader.py:74` résolvent `href` par `(master_path.parent / unquote(href)).resolve()` sans vérifier que le chemin reste dans le dossier du projet ;
- `purh_site/tei_loader.py:75` signale un fichier inclus manquant puis continue ;
- `purh_site/tei_loader.py:123-129` sélectionne, pour un fichier TEI inclus, les enfants de `<text>` et non l'ensemble documentaire.

Conséquences :

- une inclusion locale peut sortir du dossier attendu ;
- un include manquant peut produire un ouvrage apparemment généré mais incomplet ;
- les métadonnées fines d'un fichier inclus peuvent disparaître si elles ne sont pas explicitement recopiées ailleurs.

Ce n'est pas un défaut du XML source : c'est une politique de résolution et de validation trop permissive.

### C5. Le PDF comporte de nombreuses destinations PDF dupliquées

Catégorie : bug technique du PDF, défaut LaTeX/modèle.

Commande :

```powershell
Select-String -Path _audit_runtime/render_site/assets/generated/book.normalized.latei_mono_build.log -Pattern "duplicate destination|Underfull|headheight|Token not allowed|Font Warning"
```

Résultats observés :

- nombreux avertissements `warning (pdf backend): ignoring duplicate destination with the name 'page.i'`, puis `page.ii`, `page.1`, etc. ;
- nombreux `Package fancyhdr Warning: \headheight is too small (14.0pt)` ;
- avertissements `Package hyperref Warning: Token not allowed in a PDF string (Unicode)` ;
- `LaTeX Font Warning: Font shape ... size <5.5> not available`.

Impact : signets, destinations internes, titres courants et métadonnées PDF ne sont pas fiables. Ce n'est pas nécessairement visible sur toutes les pages, mais c'est incompatible avec une chaîne professionnelle.

## D. Problèmes majeurs

### D1. La normalisation modifie silencieusement des identifiants et les numéros de notes

Catégorie : risque de fidélité au XML.

Preuves code :

- `purh_site/normalizer.py:109-140` ajoute ou remplace des identifiants, y compris lorsque des `xml:id` sont dupliqués ;
- `purh_site/normalizer.py:142-145` réécrit `@n` sur toutes les notes avec une numérotation globale.

Impact : si le XML source porte une numérotation éditoriale significative, un identifiant stable utilisé ailleurs, ou des références externes, la sortie peut devenir divergente sans message clair. La correction doit être dans la normalisation commune : conserver les valeurs source, signaler les collisions, et distinguer identifiant technique de numérotation éditoriale.

### D2. Le PDF n'a pas un squelette éditorial de livre universitaire

Catégorie : défaut du modèle LaTeX/PDF.

Preuves visuelles :

- `_audit_runtime/pdf_pages/book_p001.png` : page de titre très sommaire, titre centré et `PURH` en bas, sans page de faux-titre, page de copyright, ISBN, collection, direction scientifique, mentions légales ou maquette éditoriale identifiable ;
- `_audit_runtime/pdf_pages/book_p353.png` : table des matières placée en fin ;
- `pdfinfo` : auteur vide malgré titre présent.

Commande :

```powershell
C:\texlive\2025\bin\windows\pdfinfo.exe _audit_runtime/render_site/assets/generated/book.pdf
```

Résultats utiles :

```text
Title:           Héraldique et papauté. Moyen Âge-Temps modernes. II
Subject:         PURH
Author:
Creator:         Impressions
Tagged:          no
Pages:           353
Page size:       439.37 x 651.968 pts
```

Impact : même si le corps est lisible, le PDF ne peut pas être envoyé comme épreuve éditoriale professionnelle.

### D3. La bibliographie PDF n'a pas une composition professionnelle

Catégorie : défaut typographique PDF.

Preuve visuelle : `_audit_runtime/pdf_pages/book_p300.png`.

Observation : les références apparaissent comme des paragraphes centrés ou alignés de façon instable, sans véritable retrait suspendu professionnel ni rythme bibliographique net. Pour un ouvrage savant, c'est un défaut majeur.

Correction : macros LaTeX bibliographiques et transformation commune des `bibl`; ajouter tests de rendu PDF par image et extraction.

### D4. La navigation mobile HTML place le lecteur devant un long menu avant le texte

Catégorie : défaut HTML/CSS/UX.

Preuves :

- CSS : `_audit_runtime/render_site/assets/site.css:843-851` passe la grille à une colonne mais garde la sidebar dans le flux avant le contenu ;
- HTML wrapper : `purh_site/site_builder.py:1310-1328` injecte `aside.sidebar` avant `main.content` ;
- inspection à 390 x 844 : pas de débordement horizontal, mais le premier écran du chapitre est dominé par l'en-tête et la navigation, le contenu est repoussé loin sous le menu.

Impact : sur téléphone, le site ressemble plus à un index technique qu'à un livre numérique lisible. Correction côté HTML/CSS : lien d'évitement, navigation repliable, ordre mobile privilégiant `main`.

### D5. Les notes HTML sont dupliquées entre endnotes et marges

Catégorie : choix UX non documenté, risque accessibilité/sémantique.

Preuves :

- XSLT : `purh_site/resources/tei_to_html.xsl:19-31` génère une section `endnotes` ;
- JS : `_audit_runtime/render_site/assets/app.js:28-107` clone ces notes en notes marginales ;
- HTML : la page de chapitre contient à la fois la section d'endnotes et l'`aside.margin-notes`.

Impact : ce peut être acceptable si c'est un choix éditorial explicite, mais le comportement actuel crée deux représentations du même contenu, avec risque de confusion pour lecteurs d'écran, recherche plein texte et impression.

### D6. Les sorties HTML n'ont pas encore le niveau sémantique d'une édition numérique savante

Catégorie : problème sémantique HTML.

Preuves navigateur sur la page de chapitre :

- `header = 1`, `nav = 1`, `main = 1`, `section = 3`, `aside = 2`, mais `article = 0` ;
- les titres H1-H4 sont présents et ordonnés sur la page inspectée, mais le contenu principal n'est pas encapsulé comme article de chapitre ;
- la page d'accueil contient un visuel de couverture de substitution sans vraie image exploitable.

Impact : le HTML est consultable, mais encore en dessous d'un équivalent statique d'OpenEdition Books.

### D7. Les tests contrôlent trop souvent des chaînes, pas des rendus

Catégorie : dette de test.

Exemples :

- `tests/test_latei_direct_book_skeleton.py` vérifie la présence de `\tableofcontents`, mais pas sa position réelle ; le bug de table des matières finale passe donc le filet ;
- plusieurs tests HTML/LaTeX s'arrêtent à `assert "... " in output`, sans validation DOM approfondie, sans image de rendu, sans PDF visuel.

Impact : la suite peut être importante en volume tout en laissant passer des défauts éditoriaux visibles.

## E. Problèmes moyens

### E1. `SiteBuilder` concentre trop de responsabilités

Catégorie : dette technique/maintenance.

Preuves :

- `purh_site/site_builder.py` orchestre lecture, génération, qualité, copie de ressources, HTML wrapper, rapports, PDF ;
- les lignes `290-361` mélangent normalisation, sérialisation XML, transformation, génération PDF et rapport ;
- les lignes `472-578` font des contrôles qualité et de résolution de chemins.

Impact : toute correction éditoriale risque de toucher un fichier central volumineux. Il faudrait extraire préflight, manifeste, wrappers HTML, génération rapports.

### E2. La logique de rendu est dupliquée entre HTML, LaTeX et normalisation

Catégorie : risque architectural.

Preuves :

- HTML : `purh_site/resources/tei_to_html.xsl` ;
- PDF : `purh_site/resources/latei_macros.tex`, `purh_site/latei_driver.py`, `purh_site/latei_preamble.py` ;
- normalisation : `purh_site/normalizer.py`.

Impact : notes, figures, bibliographie, typographie française et identifiants peuvent diverger entre PDF et HTML. La correction n'est pas une réécriture générale, mais il faut centraliser les décisions communes : identifiants, numéros, chemins, métadonnées, typographie contextuelle.

### E3. Les chemins de ressources ne sont pas suffisamment bornés

Catégorie : risque sécurité/portabilité.

Preuves :

- `purh_site/latei_assets.py:98-102` accepte et résout les chemins absolus ;
- `purh_site/site_builder.py:566-578` résout des chemins locaux pour contrôle qualité sans politique stricte de racine ;
- les sorties HTML produisent des chemins de type `assets/images/../icono/br/...`, signe que la normalisation des chemins visibles n'est pas propre.

Impact : risque de chemins non portables, de ressources hors projet, et de liens cassés une fois le site déplacé.

### E4. Le PDF n'est pas balisé

Catégorie : qualité technique/accessibilité PDF.

Preuve : `pdfinfo` indique `Tagged: no`.

Impact : ce n'est pas bloquant pour une impression papier, mais c'est une limite importante pour diffusion numérique institutionnelle.

### E5. Le modèle de page PDF génère des avertissements de hauteur d'en-tête

Catégorie : défaut LaTeX visible ou latent.

Preuves :

- `purh_site/latei_preamble.py:44-54` fixe `headheight=14pt` ;
- log LaTeX : avertissements répétés `\headheight is too small`.

Impact : risque de positionnement instable des en-têtes, en particulier avec titres courants longs.

### E6. Les métadonnées TEI fines sont peu exploitées dans HTML/PDF

Catégorie : couverture Métopes/TEI partielle.

Méthode : comparaison des tags présents dans la fixture avec les templates explicites XSLT.

Tags présents sans template explicite principalement côté header : `abstract`, `availability`, `licence`, `editionStmt`, `publicationStmt`, `profileDesc`, `revisionDesc`, `sourceDesc`, `textClass`, `keywords`, `language`, `dimensions`, `measure`, `sponsor`, etc.

Impact : ce n'est pas toujours une perte de corps textuel, mais c'est une perte de richesse bibliographique et documentaire pour HTML, PDF et métadonnées.

### E7. Le comportement hors JavaScript n'est que partiellement vérifié

Catégorie : robustesse HTML.

Le contenu principal et les endnotes existent dans le HTML, donc le site n'est pas dépendant de JS pour lire le texte. En revanche les notes marginales, la lightbox et certains comportements de confort dépendent de `_audit_runtime/render_site/assets/app.js`. L'audit n'a pas trouvé de mécanisme équivalent complet sans JS pour les enrichissements.

## F. Problèmes mineurs

- La page d'accueil affiche une couverture de substitution plutôt qu'une vraie couverture issue du XML ou d'un gabarit éditorial : `_audit_runtime/render_site/index.html:30`.
- L'état courant de la navigation de l'accueil paraît trop large : `_audit_runtime/render_site/index.html:25` marque plusieurs groupes comme `is-current`.
- Le bandeau HTML peut rogner visuellement le badge/texte institutionnel à droite sur écran large ou étroit : `_audit_runtime/render_site/assets/site.css:27-40` et `899-940`.
- Les titres courants PDF sont parfois abrégés par ellipse : visible sur `_audit_runtime/pdf_pages/book_p040.png`. Cela peut être acceptable, mais devrait être contrôlé éditorialement.
- Le site ne fournit pas, dans les sorties inspectées, de `sitemap.xml`, `robots.txt`, Open Graph ou données structurées bibliographiques. Ce n'est pas nécessaire pour un prototype, mais insuffisant pour une publication institutionnelle.

## G. Matrice de couverture Métopes

Comptages sur `tests/fixtures/metopes/heraldique_ii.book.normalized.xml` :

| Élément | XML source | HTML généré / observation | Niveau |
|---|---:|---|---|
| `group`, `text`, `div` | 21 groupes, 107 `div` | 17 pages HTML, sections générées | Correct sur la fixture |
| `head` | 268 | H1-H4 présents, hiérarchie correcte sur chapitre inspecté | Correct mais titres courants PDF à surveiller |
| `p` | 1079 | 928 paragraphes HTML ; différence probablement liée aux contextes notes/biblio/figures | Partiel, à contrôler par diff structurel |
| `note` | 471 | 471 appels et 471 endnotes | Correct en comptage, UX/sémantique perfectibles |
| `figure` / `graphic` | 177 / 177 | 177 figures HTML, mais 177 images manquantes | Structure correcte, ressources bloquantes |
| `figDesc`, légendes | présentes via figures | `alt` souvent dérivé de la légende | Partiel, dépend des images et de la qualité des textes |
| `quote`, `cit` | 23 / 23 | 24 `blockquote` HTML | Globalement pris en charge |
| `bibl` | 514 | bibliographies rendues, PDF peu professionnel | Partiel |
| `list`, `item` | 2 listes, 9 items | nombreuses listes HTML, y compris navigation/endnotes | Partiel, listes imbriquées non éprouvées |
| `table`, `row`, `cell` | 0 dans la fixture | non vérifiable sur l'ouvrage réel | Non testé sur cas réel |
| `hi` | 3501 | rendu HTML/PDF existant selon `rend` | Partiel, combinaisons et petites capitales à vérifier visuellement |
| `ref` | 27 | liens HTML générés ; caractères spéciaux non testés ici | Partiel |
| `ptr` | 0 dans la fixture | template existe ; sans target donne un span vide | Risque de perte de sens |
| `xml:id` | présent | IDs normalisés/mutés si collision | Risque de divergence |
| `xml:lang`, `foreign` | 0 `foreign` dans la fixture | non vérifiable sur ouvrage réel | Non testé |
| `lg`, `l`, `sp`, `stage` | 0 | poésie/théâtre non éprouvés | Non testé |
| métadonnées header | nombreuses | exploitation limitée en sorties | Partiel à faible |
| XInclude | logique présente | pas assez testée en production riche | Risque architectural |

Éléments correctement pris en charge sur la fixture : structure générale, chapitres, titres courants de section, paragraphes, notes en comptage, figures comme blocs, citations, bibliographie simple, export LaTeX/PDF, export statique HTML.

Éléments partiellement pris en charge : notes comme expérience de lecture, figures avec ressources, bibliographie, métadonnées, chemins, identifiants, titres courants, ref/ptr, typographie française contextuelle.

Éléments ignorés volontairement ou explicitement : `teiHeader` dans le rendu LaTEI est neutralisé par `purh_site/resources/latei_macros.tex:397-415`.

Éléments ignorés silencieusement ou susceptibles de perte : métadonnées fines du header, certains `ptr`, certains éléments inconnus rendus seulement par leur texte sans sémantique, headers des TEI inclus.

Éléments non encore testés sur ouvrage réel : tableaux complexes, listes imbriquées riches, poésie, théâtre, entretiens, exemples linguistiques, passages multilingues, liens contenant `%`, `#`, `&`, `_`, caractères non ASCII dans URL, ressources absentes en mode bloquant, XInclude multi-fichiers avec métadonnées.

## H. Plan de correction recommandé

### Passe 1. Stabiliser les tests et les artefacts

Objectif : retrouver une suite verte et fiable.

Fichiers concernés : `purh_site/site_builder.py`, classe de manifeste existante, tests `tests/test_site_asset_manifest.py`, tests PDF outillés.

Tests à ajouter :

- test d'existence et contenu de `assets/metadata/manifest.json` ;
- test Windows direct de l'outil `pdfinfo` utilisé ;
- séparation tests rapides/lents PDF.

Risque de régression : faible.

Critères de fin :

- `python -m pytest tests -q -p no:cacheprovider --basetemp _audit_runtime/pytest` passe ;
- le manifeste liste les HTML, PDF, CSS, JS, XML, images attendues et signale clairement les ressources absentes.

### Passe 2. Rendre les ressources et chemins non ambigus

Objectif : empêcher les sorties faussement réussies lorsque les images ou inclusions éditoriales manquent.

Fichiers concernés : `purh_site/tei_loader.py`, `purh_site/latei_assets.py`, `purh_site/site_builder.py`, rapports qualité.

Tests à ajouter :

- image manquante en mode brouillon : avertissement ;
- image manquante en mode production : échec ;
- inclusion sortant du dossier projet : rejet ;
- include manquant : échec contrôlé ou diagnostic bloquant selon mode.

Risque de régression : moyen, car des fixtures actuelles acceptent peut-être des absences.

Critères de fin :

- les chemins HTML ne contiennent plus `assets/images/../...` ;
- le rapport distingue image absente, image externe, image volontairement omise ;
- aucun chemin inclus ou ressource locale ne sort silencieusement de la racine autorisée.

### Passe 3. Refaire le squelette PDF sans réécrire tout le moteur

Objectif : obtenir un PDF d'épreuve éditoriale crédible.

Fichiers concernés : `purh_site/latei_driver.py`, `purh_site/latei_preamble.py`, `purh_site/resources/latei_macros.tex`.

Tests à ajouter :

- test PDF vérifiant l'ordre faux-titre/titre/copyright/sommaire/introduction ;
- test image rendu de pages types ;
- test absence de destinations dupliquées ;
- test métadonnées PDF auteur/titre/langue.

Risque de régression : moyen à élevé sur pagination et signets.

Critères de fin :

- table des matières placée selon le modèle éditorial choisi ;
- plus d'avertissements `duplicate destination` ni `headheight is too small` ;
- auteur, titre, langue et signets PDF cohérents ;
- pages liminaires minimales présentes ou explicitement désactivées par configuration.

### Passe 4. Traiter notes, bibliographie et typographie française comme objets éditoriaux

Objectif : passer d'un rendu techniquement lisible à une composition savante.

Fichiers concernés : normalisation typographique commune, XSLT HTML, macros LaTeX notes/bibliographie, CSS.

Tests à ajouter :

- appels de note avant/après ponctuation selon règles françaises et politique PURH ;
- espaces insécables avant `: ; ? !`, guillemets français, apostrophe typographique, siècles, pourcentages ;
- bibliographie avec retrait suspendu PDF et HTML ;
- citations imbriquées et notes longues.

Risque de régression : élevé sur textes existants si les transformations sont trop globales.

Critères de fin :

- les corrections ne modifient pas URL, chemins, identifiants ou fragments de code ;
- les règles sont centralisées et documentées ;
- rendu PDF et HTML vérifié visuellement sur pages avec notes, citations et bibliographie.

### Passe 5. Améliorer HTML comme livre numérique

Objectif : rendre le site publiable comme édition numérique institutionnelle statique.

Fichiers concernés : `purh_site/site_builder.py`, `purh_site/resources/tei_to_html.xsl`, `site.css`, `app.js`.

Tests à ajouter :

- navigation clavier ;
- focus visible ;
- zoom 200 % ;
- page de chapitre mobile où le texte apparaît avant ou immédiatement après une navigation compacte ;
- liens note/retour note ;
- absence d'IDs dupliqués ;
- liens internes cassés.

Risque de régression : moyen.

Critères de fin :

- `main/article` correctement structuré ;
- navigation mobile repliable ou déplacée après contenu principal avec lien d'accès ;
- notes marginales accessibles sans duplication confuse ;
- métadonnées HTML minimales : title, description, auteur, langue, canonical si nécessaire.

### Passe 6. Consolider la fidélité XML

Objectif : conserver un XML unique comme source de vérité.

Fichiers concernés : `purh_site/tei_loader.py`, `purh_site/normalizer.py`, tests XML structurels.

Tests à ajouter :

- conservation texte + `tail` sur éléments imbriqués ;
- collisions `xml:id` ;
- notes avec `@n` éditorial ;
- `xml:lang` et passages étrangers ;
- XInclude avec header et chemins relatifs ;
- structures non prises en charge explicitement signalées.

Risque de régression : moyen.

Critères de fin :

- la normalisation produit un journal des mutations ;
- aucune mutation d'identifiant ou de numéro éditorial sans diagnostic ;
- éléments Métopes non couverts listés dans un rapport de couverture.

## I. Verdict final sur les sorties

1. Le PDF peut-il actuellement être envoyé à un auteur ou à une éditrice pour validation ?

Non, pas comme épreuve éditoriale. Il peut être envoyé uniquement comme preuve technique de transformation, avec avertissement explicite : images absentes, table des matières mal placée, liminaires incomplets, bibliographie et notes non finalisées.

2. Le PDF peut-il actuellement être envoyé à l'impression sans reprise manuelle lourde ?

Non. Le PDF est techniquement compilé, mais non imprimable au niveau PURH : squelette éditorial incomplet, table des matières finale, images manquantes, avertissements PDF, bibliographie et typographie insuffisantes.

3. Le HTML peut-il actuellement être publié comme édition numérique institutionnelle ?

Non. Il est utile pour revue interne et démonstration, mais pas encore pour publication institutionnelle : images cassées, expérience mobile faible, sémantique perfectible, notes marginales/endnotes à clarifier, métadonnées web incomplètes.

4. Les cinq corrections qui feraient progresser le plus fortement la qualité éditoriale réelle :

- corriger le squelette PDF : liminaires, table des matières, métadonnées, signets, destinations PDF ;
- rendre les ressources obligatoires en mode production et bloquer les générations avec images manquantes ;
- reprendre notes et bibliographie comme composants typographiques professionnels ;
- refaire la navigation HTML mobile et la sémantique `article`/notes/accessibilité ;
- consolider la normalisation XML : identifiants, numéros de notes, XInclude, journal des transformations et tests de fidélité.

## Annexe. Commandes et artefacts principaux

Commandes principales exécutées :

```powershell
python -m pytest tests -q -p no:cacheprovider --basetemp _audit_runtime/pytest
python -c "from pathlib import Path; from purh_site.site_builder import SiteBuilder; from purh_site.config import BuildConfig; out=Path('_audit_runtime/render_site'); r=SiteBuilder().build_from_master(Path('tests/fixtures/metopes/heraldique_ii.book.normalized.xml'), BuildConfig(output_dir=out, pdf_export_mode='latei_pdf')); print(r)"
C:\texlive\2025\bin\windows\pdfinfo.exe _audit_runtime/render_site/assets/generated/book.pdf
C:\texlive\2025\bin\windows\pdffonts.exe _audit_runtime/render_site/assets/generated/book.pdf
C:\texlive\2025\bin\windows\pdftoppm.exe -png -f 1 -l 1 _audit_runtime/render_site/assets/generated/book.pdf _audit_runtime/pdf_pages/book_p
python -m http.server 8765 --bind 127.0.0.1
```

Artefacts consultables :

- site généré : `_audit_runtime/render_site/index.html` ;
- PDF généré : `_audit_runtime/render_site/assets/generated/book.pdf` ;
- LaTeX généré : `_audit_runtime/render_site/assets/generated/book.tex` ;
- log LaTeX : `_audit_runtime/render_site/assets/generated/book.normalized.latei_mono_build.log` ;
- rapport de build : `_audit_runtime/render_site/build_report.txt` ;
- pages PDF rendues pour inspection : `_audit_runtime/pdf_pages/book_p001.png`, `_audit_runtime/pdf_pages/book_p008.png`, `_audit_runtime/pdf_pages/book_p040.png`, `_audit_runtime/pdf_pages/book_p300.png`, `_audit_runtime/pdf_pages/book_p340.png`, `_audit_runtime/pdf_pages/book_p353.png`.
