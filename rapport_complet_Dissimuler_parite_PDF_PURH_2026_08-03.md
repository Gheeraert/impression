# Rapport complet — *Dissimuler pour mieux régner*

## Parité entre le PDF généré par la chaîne Impression/LaTEI et le PDF imprimeur des PURH

**Date :** 3 août 2026  
**Statut :** rapport de reprise du chantier  
**Objet :** préciser la marche à suivre pour faire tendre le générateur de livres vers la qualité et la structure du PDF imprimeur des PURH  
**Contrainte actuelle :** les deux fichiers InDesign natifs sont disponibles, mais pas leurs exports IDML. Cette absence ne bloque pas les corrections immédiates ; l’IDML servira plus tard à préciser les héritages de styles et les paramètres internes.

## 1. Corpus examiné

- `Dissimuler_PDF_genere.pdf` — sortie LuaLaTeX actuelle du générateur ;
- `Dissimuler_PDF_imprimeur.pdf` — PDF de production exporté depuis Adobe InDesign 20.5 ;
- `dissimuer_indesign_chap1.indd` — fichier natif de l’introduction ;
- `dissimuer_indesign_chap2.indd` — fichier natif de l’article « Les espaces du secret à Clarens » ;
- `Referentiel_mise_en_page_PURH_audit_v0.5.docx` — référentiel probatoire antérieur.

Les fichiers INDD ont pu être exploités de façon limitée mais utile : métadonnées XMP, aperçus incorporés, chaînes de styles, titres, noms d’auteurs et chemins des XML liés. Ils ne permettent pas, sans InDesign ou export IDML, de certifier les valeurs internes et les héritages de styles. Les aperçus confirment néanmoins les choix visibles du PDF imprimeur.

## 2. Conclusion générale

Il ne faut pas recommencer le chantier ni retoucher aveuglément le corps du livre. La sortie actuelle a déjà franchi un seuil important : **la composition des pages courantes est désormais très proche du PDF imprimeur**.

Les écarts dominants ne concernent plus le corps courant, mais :

1. la structure des liminaires et de la fin d’ouvrage ;
2. l’état de pagination ;
3. les gabarits d’ouverture de partie et de contribution ;
4. la politique de numérotation des notes ;
5. la table des matières ;
6. le passage des images dans la chaîne ;
7. certains détails typographiques encore mesurables ;
8. le mode d’export réellement destiné à l’imprimeur.

Le bon changement de méthode est donc le suivant : **cesser de régler un PDF générique et formaliser des gabarits éditoriaux PURH sémantiques, versionnés et testables**.

## 3. État technique objectif des deux PDF

### 3.1. PDF généré

- 207 pages ;
- page physique : 155 × 230 mm ;
- MediaBox, CropBox, BleedBox, TrimBox et ArtBox toutes identiques à 155 × 230 mm ;
- producteur : LuaLaTeX ;
- polices incorporées :
  - Chaparral Pro Regular ;
  - Chaparral Pro Italic ;
  - Chaparral Pro Semibold ;
  - Chaparral Pro Semibold Italic ;
  - Josefin Sans Thin ;
  - Josefin Sans Bold ;
  - Josefin Sans Bold Italic.

Le défaut antérieur d’absence d’italique visible est donc **résolu**. Il ne faut plus modifier le writer LaTEI comme si les commandes d’italique avaient disparu.

### 3.2. PDF imprimeur

- 208 pages ;
- PDF exporté depuis Adobe InDesign 20.5 ;
- MediaBox : environ 169,8 × 244,8 mm ;
- TrimBox : 155 × 230 mm ;
- BleedBox : 165 × 240 mm, soit 5 mm autour du format fini ;
- traits de coupe présents ;
- texte courant imprimé en noir process à 90 % ;
- deux images incorporées :
  - page 165 : image CMJN, 332 ppp ;
  - page 166 : image CMJN, 300 ppp.

## 4. Ce qui est désormais proche ou conforme

### 4.1. Corps courant et grille

Sur les pages homologues générée 20 / imprimeur 24 :

| Mesure | PDF généré | PDF imprimeur après retrait de la marge de coupe | Diagnostic |
|---|---:|---:|---|
| Corps courant | environ 11 pt | 11 pt | conforme |
| Pas de ligne médian | environ 13,45 pt | 13,5 pt | conforme dans la tolérance |
| Marge gauche, page verso | environ 29,9 mm | 30,0 mm | conforme |
| Marge droite, page verso | environ 19,4 mm | 19,1 mm | très proche |
| Marge gauche, page recto | environ 19,9 mm | 20,0 mm | conforme |
| Marge droite, page recto | environ 29,4 mm | 29,1 mm | très proche |

La géométrie courante reproduit donc déjà le profil de production observé en 2025, avec des marges alternées proches de 20/30 mm. **Il faut geler provisoirement ces valeurs** et empêcher qu’une correction structurelle ne les dégrade.

### 4.2. Titraille courante

- les titres de section utilisent désormais Josefin Sans Thin autour de 12 pt, comme dans le PDF imprimeur ;
- les titres de partie et de contribution utilisent désormais Josefin Sans Thin autour de 16 pt ;
- le libellé automatique « Chapitre 1 », autrefois présent, a disparu ;
- les sous-titres peuvent être rendus en Josefin Sans autour de 12 pt ;
- les titres courants emploient désormais Josefin Sans Thin 10 pt, en romain ;
- le verso porte la partie et le recto le titre de contribution, comme dans l’étalon.

Ces points doivent être marqués **résolus depuis la version 0.5**.

### 4.3. Ouverture à droite

La première partie apparaît sur une page recto, suivie d’un blanc technique, puis la première contribution apparaît à nouveau sur une page recto. La logique d’ouverture à droite est donc déjà active dans ce cas. Elle doit être testée et généralisée, non réécrite sans preuve.

### 4.4. Compilation et table des matières obsolète

La table des matières actuelle appartient bien à *Dissimuler pour mieux régner* ; les entrées étrangères observées auparavant ont disparu. Le problème de réutilisation d’un ancien `.toc` paraît donc résolu. La compilation en environnement propre doit néanmoins rester une obligation et un test de non-régression.

## 5. Écarts encore bloquants

## 5.1. Liminaires incomplets et métadonnées erronées

Le PDF généré commence par une page générique qui présente plusieurs défauts :

- la chaîne `<em>…</em>` est imprimée littéralement ;
- « Anaïs Lebreton » est dupliquée comme autrice ;
- la véritable direction scientifique — Floriane Daguisé et Florence Fix — n’est pas correctement rendue ;
- le faux-titre manque ;
- la page de crédits manque ;
- la page de titre complète manque ;
- les blancs techniques des liminaires manquent ;
- le colophon écologique et matériel de fin d’ouvrage manque.

Le PDF imprimeur suit au contraire cette séquence :

1. deux pages blanches ;
2. faux-titre, page 3 ;
3. crédits, page 4 ;
4. page de titre complète, page 5 ;
5. page blanche, page 6 ;
6. introduction, page 7.

Il faut donc créer un véritable modèle de **liminaires de monographie collective**, fondé sur des métadonnées structurées et une séquence déclarative, non sur une macro générique improvisée.

### Décision d’architecture

Les informations de contenu doivent rester dans la TEI ou dans les métadonnées du livre ; le profil de composition décide seulement :

- de leur ordre ;
- de leur visibilité ;
- de leur gabarit ;
- de la création éventuelle de pages blanches.

Aucune balise XML sérialisée ne doit pouvoir devenir du texte visible.

## 5.2. Pagination arabe continue

Dans le PDF imprimeur, les premières pages sont comptées, même lorsque leur folio n’est pas affiché :

- introduction : page 7 ;
- première partie : page 21 ;
- première contribution : page 23 ;
- table des matières : pages 207-208.

Dans le PDF généré, la pagination visible redémarre à 1 à l’introduction. La première contribution apparaît avec le folio 17 sur la page physique 19.

La correction n’est pas d’ajouter arbitrairement 6 aux numéros. Il faut :

1. ajouter la séquence réelle des liminaires ;
2. commencer le compteur arabe à la première page physique du livre ;
3. ne pas remettre le compteur à zéro à l’introduction ni au passage au corps ;
4. masquer seulement l’impression du folio sur les pages qui ne doivent pas le montrer.

Le profil `purh_155x230_production_2025` doit donc employer une **pagination arabe continue dès la première page physique**.

## 5.3. Ouverture d’une contribution

Comparaison de la première contribution :

### PDF généré, page 19

- titre courant et folio visibles ;
- titre sur une seule ligne ;
- sous-titre présent ;
- auteur visible ;
- affiliation visible ;
- corps de l’article commençant vers 56 mm depuis le haut de la page ;
- notes poursuivant la numérotation de l’introduction : 33, 34, 35 ;
- notes proches de 9 pt.

### PDF imprimeur, page 23

- aucun titre courant ni folio visible ;
- titre coupé éditorialement sur deux lignes :
  - « LES ESPACES DU SECRET » ;
  - « À CLARENS » ;
- sous-titre en Josefin Sans Thin Italic 12 pt ;
- auteur et affiliation non imprimés sur cette page ;
- corps de l’article commençant vers 74 mm depuis le haut du format fini ;
- notes repartant à 1 ;
- notes en Chaparral Pro 8,5 pt.

### Correctifs nécessaires

- appliquer un style de page sans en-tête ni folio aux ouvertures ;
- distinguer métadonnées conservées et métadonnées visibles ;
- permettre une coupure éditoriale explicite du titre ;
- supprimer l’auteur et l’affiliation pour ce profil, sans supprimer les données ;
- imposer l’espace vertical propre à l’ouverture ;
- remettre le compteur de notes à 1 au début de chaque contribution ;
- conserver la pagination du livre sans remise à zéro.

La coupure du titre ne doit pas être obtenue par une largeur arbitrairement réduite. Il faut accepter un titre typographique structuré, par exemple une liste de lignes ou un marqueur de coupure explicite.

## 5.4. Ouverture de partie

Le générateur possède déjà une ouverture isolée sur recto et un blanc technique au verso. Les écarts restants sont visuels :

- le titre généré occupe deux lignes, contre trois dans l’étalon ;
- il est placé environ 6,5 mm trop haut ;
- le filet oblique manque ;
- le motif gris terminal manque.

Il faut créer une macro sémantique `PURHPartOpening`, avec :

- lignes de titre explicitables ;
- position verticale paramétrée ;
- décor vectoriel propre au profil ;
- aucune dépendance à une image bitmap si le motif peut être décrit en TikZ ou en primitives PDF ;
- style de page vide ;
- ouverture obligatoirement à droite.

## 5.5. Notes de bas de page

Le rendu courant reste proche mais non conforme :

| Élément | PDF généré | PDF imprimeur | Cible |
|---|---:|---:|---:|
| Corps | environ 9 pt | 8,5 pt | 8,5 pt |
| Interligne | environ 11 pt | environ 10,2 pt | 10,2 pt |
| Filet | environ 0,40 pt | 0,25 pt | 0,25 pt |
| Longueur du filet | environ 42 mm | 25,4 mm | 25,4 mm |
| Numérotation | continue entre contributions | repart à 1 | repart à 1 par contribution |

La réduction des notes devrait également améliorer la pagination globale sans toucher au corps courant.

## 5.6. Titres courants et folios

Le contenu, la police et le corps sont désormais corrects. Leur bandeau est toutefois situé environ 3,1 mm plus bas que dans le PDF imprimeur.

Cible :

- Josefin Sans Thin/Light 10 pt ;
- folio extérieur ;
- partie au verso ;
- titre court de la contribution au recto ;
- sommet du bandeau autour de 14,8 mm depuis le bord du format fini ;
- aucun bandeau sur les ouvertures, pages blanches, pages de titre et autres pages spéciales.

## 5.7. Table des matières

La table générée est propre au livre, mais sa structure éditoriale est incorrecte :

- elle occupe trois pages ;
- elle descend jusqu’aux intertitres internes ;
- elle ne place pas les auteurs sous les titres de contribution ;
- ses pages suivantes conservent des titres courants ordinaires.

Le PDF imprimeur utilise deux pages et ne retient que :

1. l’introduction ;
2. les parties ;
3. les contributions ;
4. le nom de l’auteur sous chaque contribution.

Les subdivisions internes de l’article sont exclues.

La TDM doit donc être produite par une commande sémantique propre aux PURH, et non par le simple niveau hiérarchique standard de LaTeX.

### Cible de structure

```text
Introduction ........................................ 7

CARTOGRAPHIE : SITUER LE SECRET POLITIQUE
Les espaces du secret à Clarens ..................... 23
Henri Portal
...
```

Le colophon doit pouvoir occuper le bas de la deuxième page de table, comme dans le PDF imprimeur.

## 5.8. Images

Le PDF généré ne contient aucune image. Le PDF imprimeur en contient deux, aux pages 165 et 166.

La chaîne doit être vérifiée de bout en bout :

```text
source XML / ressources
    -> arbre pivot
    -> TEI normalisée
    -> LaTEI
    -> table des ressources graphiques
    -> \teiGraphic
    -> PDF
```

Règles impératives :

- ne jamais extraire les images du PDF imprimeur pour masquer un déficit de source ;
- chercher d’abord si les ressources existent dans le dépôt, les DOCX, les XML, les dossiers médias ou les paquets d’entrée ;
- si le XML ne contient que la légende sans `graphic`, produire un diagnostic explicite ;
- interdire l’export de production lorsqu’une image attendue n’a ni fichier résolu ni statut d’absence accepté ;
- conserver dimensions, proportions et légendes ;
- ne pas agrandir systématiquement les figures à 95 % de la largeur.

## 5.9. Couleur et mode imprimeur

Le PDF généré emploie le noir plein. Le PDF imprimeur emploie un noir process à 90 %, visible dans le contenu et confirmé par le colophon.

Deux modes doivent être distingués :

### Mode `screen`

- MediaBox = TrimBox = 155 × 230 mm ;
- aucune marque d’impression ;
- destiné au contrôle et à la lecture.

### Mode `printer`

- TrimBox = 155 × 230 mm ;
- BleedBox = 165 × 240 mm ;
- MediaBox autour de 169,8 × 244,8 mm ;
- traits de coupe ;
- fontes incorporées ;
- texte courant en 90 % K ;
- images contrôlées pour leur résolution et leur espace colorimétrique.

Il ne faut pas mêler les paramètres de composition intérieure et les paramètres de sortie imprimeur.

## 6. Ce que les fichiers InDesign apportent sans IDML

Les deux INDD sont bien des documents de production du livre :

- créateur : Adobe InDesign 20.5 sous Windows ;
- chapitre 1, dernière modification XMP repérée : 9 septembre 2025 à 14 h 07 min 03 s ;
- chapitre 2, dernière modification XMP repérée : 9 septembre 2025 à 14 h 24 min 17 s ;
- chemins liés vers des XML de travail du livre ;
- présence de styles tels que :
  - `T_2_Partie` ;
  - `T_3_Article` ;
  - `T_SousTitre` ;
  - `txt_Normal` ;
  - `txt_Note` ;
  - `txt_Note_Suite` ;
  - `auteur_Institution` ;
  - `enc__txt_Normal`.

Les aperçus incorporés confirment :

- l’absence d’auteur et d’affiliation sur l’ouverture de contribution ;
- la coupure du titre sur deux lignes ;
- la remise à 1 des notes ;
- l’absence de folio et de titre courant sur l’ouverture ;
- la disposition du sous-titre ;
- la continuité avec le PDF imprimeur.

### Limite actuelle

Sans IDML, il reste impossible de certifier automatiquement :

- l’héritage exact des styles ;
- les options de justification et de césure propres à ces deux fichiers ;
- les chaînages de blocs ;
- les gabarits appliqués page par page ;
- les liens exacts vers les images ;
- les coupures forcées stockées dans le texte ;
- les paramètres détaillés des notes.

Cette limite doit être enregistrée, mais **elle ne doit pas retarder le chantier**. Le PDF imprimeur est l’étalon visuel et métrique suffisant pour les correctifs immédiats. L’IDML sera une contre-épreuve ultérieure.

## 7. Architecture recommandée

## 7.1. Séparation des responsabilités

- **writer Python / LaTEI :** sérialisation sémantique réversible ;
- **profil LaTeX versionné :** choix de composition ;
- **configuration YAML ou JSON :** source unique des valeurs mesurées ;
- **métadonnées du livre :** contenu des liminaires, titres, auteurs, direction, crédits, colophon ;
- **tests :** validation dimensionnelle, structurelle et visuelle ;
- **exporteur PDF :** boîtes, marques, couleur et contrôles imprimeur.

Le fichier `book.tex` doit sélectionner un profil ; il ne doit pas contenir une seconde copie dispersée de toutes les valeurs.

## 7.2. Commandes sémantiques à prévoir

```tex
\PURHBookFrontMatter{...}
\PURHFalseTitle{...}
\PURHCreditsPage{...}
\PURHTitlePage{...}
\PURHIntroductionOpening{...}
\PURHPartOpening{...}
\PURHArticleOpening{...}
\PURHContributorMetadata{...}
\PURHTableOfContents{...}
\PURHColophon{...}
\PURHGraphic{...}
```

Le writer doit émettre des rôles explicites. Il faut éviter les cascades de tests textuels `IfSubStr` pour décider si un groupe est une partie, une annexe ou une contribution.

## 8. Marche à suivre

## Passe 0 — figer l’état actuel

- créer le profil `purh_155x230_production_2025` ;
- enregistrer les mesures actuelles conformes ;
- produire les rendus de référence ;
- ajouter des tests empêchant toute régression du corps courant ;
- mettre à jour le référentiel en version 0.6 ;
- compiler dans un dossier temporaire vierge.

Pages homologues de référence :

| Fonction | Généré actuel | Imprimeur |
|---|---:|---:|
| Page générique / page de titre | 1 | 3-5 |
| Introduction | 3 | 7 |
| Partie | 17 | 21 |
| Première contribution | 19 | 23 |
| Page courante verso | 20 | 24 |
| Page avec section | 21 | 25 |
| Images | absentes | 165-166 |
| TDM | 205-207 | 207-208 |

## Passe 1 — intégrité et métadonnées

- supprimer l’impression littérale de balises ;
- supprimer les duplications de contributeurs ;
- distinguer auteur, directeur, suivi éditorial et mise en pages ;
- valider les métadonnées avant composition ;
- créer des diagnostics bloquants pour les incohérences.

## Passe 2 — liminaires et pagination

- créer la séquence complète des liminaires ;
- assurer la pagination arabe continue ;
- masquer les folios sans arrêter le compteur ;
- produire les pages blanches demandées par la séquence ;
- ajouter le colophon.

## Passe 3 — ouvertures sémantiques

- partie ;
- introduction ;
- contribution ;
- annexes et groupes éditoriaux ;
- politique de visibilité auteur/affiliation ;
- coupures éditoriales des titres ;
- remise à 1 des notes par contribution ;
- styles de pages vides pour les ouvertures.

## Passe 4 — table des matières

- limiter les niveaux ;
- ajouter les auteurs ;
- gérer la suite sur deux pages ;
- supprimer les titres courants ordinaires ;
- intégrer le colophon sur la dernière page si le profil le demande.

## Passe 5 — images

- restaurer le routage des `graphic` ;
- résoudre les chemins ;
- ajouter les diagnostics de ressources manquantes ;
- couvrir le pipeline par des fixtures ;
- reproduire les deux images de *Dissimuler* seulement si les ressources sources existent.

## Passe 6 — réglages typographiques fins

- notes 8,5/10,2 pt ;
- filet 0,25 pt sur 25,4 mm ;
- bandeau courant remonté d’environ 3,1 mm ;
- ouverture d’article descendue à la position de l’étalon ;
- décor de partie ;
- texte courant 90 % K ;
- autres styles spécialisés : citations, bibliographie, poésie, tableaux, légendes et listes.

## Passe 7 — export imprimeur et préflight

- boîtes PDF ;
- traits de coupe ;
- polices ;
- couleur ;
- résolution et CMJN des images ;
- manifeste de production ;
- rapport de préflight ;
- refus de l’export en cas d’erreur bloquante.

## 9. Contrat minimal de validation

### Structure

- aucune chaîne `<em>` ou `[rend=...]` visible ;
- aucun contributeur dupliqué ;
- faux-titre, crédits, titre, blancs et colophon présents ;
- introduction à la page 7 ;
- première partie à la page 21 ;
- première contribution à la page 23 ;
- ouvertures sans folio ni titre courant ;
- parties et contributions sur recto ;
- notes repartant à 1 par contribution ;
- TDM limitée aux niveaux éditoriaux autorisés ;
- auteurs visibles dans la TDM.

### Typographie

- corps courant : 11 ± 0,1 pt ;
- pas : 13,5 ± 0,1 pt ;
- notes : 8,5 ± 0,1 pt ;
- pas des notes : 10,2 ± 0,2 pt ;
- titres courants : Josefin Sans Thin/Light 10 pt ;
- titre de contribution : Josefin Sans Thin 16 pt ;
- sous-titre : Josefin Sans Thin Italic 12 pt ;
- filet de notes : 0,25 pt, 25,4 mm.

### PDF

- mode écran : toutes les boîtes à 155 × 230 mm ;
- mode imprimeur : TrimBox 155 × 230, BleedBox 165 × 240, MediaBox conforme au profil ;
- polices requises incorporées ;
- aucune image attendue non résolue ;
- compilation propre et reproductible ;
- aucune entrée étrangère dans la TDM ou les signets.

## 10. Priorité réelle

Ordre recommandé :

1. métadonnées et liminaires ;
2. pagination ;
3. ouvertures et notes ;
4. table des matières ;
5. images ;
6. détails typographiques ;
7. export imprimeur.

Il faut résister à la tentation de commencer par les traits de coupe ou le décor de partie. Tant que la structure du livre n’est pas correcte, une ressemblance visuelle ponctuelle ne constitue pas une sortie de production fiable.

## 11. Verdict final

La chaîne n’est pas encore prête pour produire sans contrôle humain un PDF imprimeur PURH. Elle est toutefois beaucoup plus avancée que ne le laissait penser le référentiel 0.5 : **le noyau des pages courantes est désormais suffisamment fidèle pour être conservé**.

Le chantier est maintenant circonscrit et peut être conduit par passes atomiques. L’absence temporaire d’IDML ne constitue pas un obstacle : les PDF et les aperçus INDD suffisent pour implémenter la structure, la pagination, les ouvertures, les notes, la TDM, les diagnostics d’images et le mode imprimeur. L’IDML permettra plus tard de documenter finement les héritages internes, mais il ne doit pas devenir un prétexte pour ajourner les corrections déjà certaines.
