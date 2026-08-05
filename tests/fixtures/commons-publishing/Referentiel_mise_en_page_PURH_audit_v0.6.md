# RÉFÉRENTIEL PURH

## Mise en page intérieure — audit du corpus, profils de composition et parité LaTEI

**Version :** 0.6 — mise à jour après réception des INDD de production de *Dissimuler pour mieux régner* et contrôle de la sortie LuaLaTeX du 3 août 2026  
**Date :** 3 août 2026  
**Périmètre :** maquettes actuelles du dossier `CHARTES_GRAPHIQUES`, PDF imprimeurs récents, sorties du générateur Impression/LaTEI ; anciennes maquettes et ancienne charte exclues  
**Objet :** dégager les règles mesurables, distinguer les profils de composition, suivre la convergence du générateur et définir un contrat de validation automatisable  
**Statut :** référentiel probatoire et évolutif ; la section relative au profil de production 155 × 230 peut guider le développement, sans constituer encore une certification complète de production

# Verdict

## Conclusion

Le corpus permet désormais de distinguer avec davantage de sûreté deux ensembles :

1. un profil de maquette actuelle 2026, documenté par l’IDML `UE_155x230` déjà audité ;
2. un profil de production observé en 2025, confirmé par deux livres et, pour *Dissimuler pour mieux régner*, par le PDF imprimeur et deux fichiers INDD natifs de contributions.

La sortie LuaLaTeX actuelle de *Dissimuler* a nettement progressé depuis la version 0.5. Le corps courant, la grille, l’empagement, les italiques, la titraille courante et la logique des titres courants sont maintenant proches du PDF imprimeur. Les anciens écarts de 12 pt, de marges symétriques, d’italiques absentes, de libellés « Chapitre » et de table des matières étrangère ne décrivent plus l’état actuel.

La parité reste incomplète pour :

- les liminaires ;
- la pagination arabe continue ;
- les ouvertures d’articles et de parties ;
- la numérotation et la composition des notes ;
- la table des matières éditoriale ;
- les images ;
- le colophon ;
- la couleur intérieure ;
- l’export réellement destiné à l’imprimeur.

## Statut par format

**CONFIRMÉ / PARTIEL — 155 × 230.** Le noyau UE 2026 reste documenté par IDML, INDD, PDF et fontes. Le profil de production 2025 est maintenant confirmé par les PDF imprimeurs de *Beautés vitales* et *Dissimuler pour mieux régner*, ainsi que par les aperçus et métadonnées de deux INDD de production de *Dissimuler*. Les liminaires et la fin d’ouvrage sont désormais observables dans le PDF de production, mais pas encore certifiables par IDML.

**INVENTAIRE CONFIRMÉ / MESURES PROVISOIRES — 195 × 255.** Onze maquettes INDD et sept fontes sont attestées. Sans IDML ni PDF représentatif, leurs mesures internes ne sont pas normalisées.

**EN QUARANTAINE — 180 × 240.** Le dossier reste contradictoire et ne peut alimenter aucun profil de production.

**NON DOCUMENTÉ — quatrième format.** Aucun corpus actuel suffisant.

## Limitation assumée : absence temporaire d’IDML pour les deux nouveaux INDD

Les fichiers natifs de l’introduction et du premier article de *Dissimuler* ont été reçus, mais leurs exports IDML ne sont pas disponibles. Sarah étant absente et InDesign n’étant pas encore installé localement, l’IDML est reporté.

Cette absence :

- empêche de certifier les héritages internes et certains paramètres de blocs ;
- n’empêche pas de coder les corrections déjà prouvées par le PDF imprimeur ;
- ne doit pas bloquer la structuration des liminaires, la pagination, les ouvertures, les notes, la TDM, les images et le mode imprimeur ;
- devra être comblée ultérieurement comme contre-épreuve et non comme préalable absolu.

# 1. Statut des sources

| Source | Nature | Date / producteur | Confiance | Portée |
|---|---|---|---|---|
| `UE_155x230.idml`, INDD, PDF et fontes | maquette actuelle | paquet 2026 déjà audité | élevée | géométrie, grille, styles, notes, tableaux, titres courants |
| `Dissimuler_PDF_imprimeur.pdf` | PDF de production | Adobe InDesign 20.5, 11 septembre 2025 | élevée | réalisation concrète complète, boîtes, fontes, pages, images, liminaires, TDM |
| `Dissimuler_PDF_genere.pdf` | sortie actuelle | LuaLaTeX, 3 août 2026 | élevée | état réel de la chaîne, comparaison métrique et structurelle |
| `dissimuer_indesign_chap1.indd` | INDD de l’introduction | dernière date XMP repérée : 9 septembre 2025, 14:07:03 | moyenne à élevée pour l’aperçu et les métadonnées ; faible pour les paramètres internes | aperçu de production, styles nommés, chemins XML, structure visible |
| `dissimuer_indesign_chap2.indd` | INDD de l’article | dernière date XMP repérée : 9 septembre 2025, 14:24:17 | moyenne à élevée pour l’aperçu et les métadonnées ; faible pour les paramètres internes | ouverture d’article, notes, styles nommés, chemins XML |
| `Referentiel_mise_en_page_PURH_audit_v0.5.docx` | référentiel antérieur | 2 août 2026 | historique | mesures confirmées du noyau 2026 et registre des anciens défauts |
| `195x255.zip` | onze INDD + sept fontes | 9 avril 2026 | élevée pour l’inventaire, faible pour la géométrie | gamme fonctionnelle et contrat de fontes |
| `180x240.zip` | deux INDD suspects | juin 2026 | nulle pour la géométrie | quarantaine documentaire |
| `ANCIENNES_MAQUETTES` | corpus ancien | divers | exclue | aucune règle actuelle |

# 2. Hiérarchie des preuves

## 2.1. Règle générale actuelle

L’IDML `UE_155x230` de 2026 reste la meilleure preuve pour la maquette générale actuelle et les propriétés internes accessibles : grille, styles, notes, tableaux et gabarits.

## 2.2. Profil de production observé

Le PDF imprimeur est la meilleure preuve de la réalisation effectivement envoyée à l’impression. La convergence de *Beautés vitales* et de *Dissimuler pour mieux régner* justifie un profil distinct :

```text
purh_155x230_production_2025
```

Ce profil ne doit pas être fusionné par moyenne avec :

```text
purh_155x230_current_2026
```

Les divergences doivent rester explicites jusqu’à une décision éditoriale.

## 2.3. Fichiers INDD sans IDML

Les chaînes et aperçus incorporés peuvent confirmer :

- l’identité du document ;
- le titre ;
- l’auteur ;
- la disposition visible ;
- la présence de noms de styles ;
- le logiciel et les dates XMP ;
- les chemins de ressources textuelles.

Ils ne suffisent pas à certifier :

- les héritages de styles ;
- les valeurs exactes des propriétés ;
- les gabarits réellement appliqués ;
- les chaînages de blocs ;
- les liens graphiques ;
- les surcharges locales.

# 3. Profils 155 × 230

## 3.1. Profil `purh_155x230_current_2026`

Statut : **confirmé pour le noyau UE, incomplet pour le livre entier**.

### Géométrie générale

| Paramètre | Valeur |
|---|---:|
| Format fini | 155 × 230 mm |
| Pages | vis-à-vis, reliure gauche |
| Colonnage | une colonne |
| Largeur courante | 107 mm |
| Marge haute | 30 mm |
| Marge basse | 19 mm |
| Marge intérieure | 25 mm |
| Marge extérieure | 23 mm |
| Empagement | 107 × 181 mm |
| Grille | 13,5 pt |
| Page d’ouverture | largeur utile 109 mm, sans titre courant ni folio |

### Corps

- Chaparral Pro Regular 11 pt ;
- interligne effectif 13,5 pt ;
- justification complète, dernière ligne à gauche ;
- retrait d’alinéa 5 mm ;
- texte à 90 % K ;
- césure active et contrôlée ;
- veuves et orphelines : au moins deux lignes.

### Divergence à conserver

La maquette 2026 utilise des marges 25/23 mm, tandis que les livres de production 2025 observés utilisent environ 20/30 mm. Ne pas créer de valeur moyenne.

## 3.2. Profil `purh_155x230_production_2025`

Statut : **provisoire mais fortement confirmé par observation**.

### Géométrie courante

| Paramètre | Valeur cible | Niveau de preuve |
|---|---:|---|
| Format fini | 155 × 230 mm | confirmé par TrimBox |
| Pages | vis-à-vis | confirmé visuellement |
| Corps | Chaparral Pro Regular 11 pt | confirmé par fontes et extraction |
| Interligne | 13,5 pt | confirmé par mesure des lignes |
| Marge haute du corps courant | environ 30 mm | confirmé |
| Marge basse | environ 19 mm | confirmé |
| Marge intérieure | environ 20 mm | confirmé |
| Marge extérieure | environ 30 mm | confirmé |
| Largeur utile | environ 106 mm | confirmé |
| Texte | 90 % K | confirmé par PDF et colophon |

### Contrôle de la sortie actuelle

La sortie LuaLaTeX du 3 août 2026 reproduit déjà presque exactement cette géométrie :

| Mesure sur pages courantes homologues | Généré | Imprimeur | Statut |
|---|---:|---:|---|
| Corps | environ 11 pt | 11 pt | conforme |
| Pas médian | environ 13,45 pt | 13,5 pt | conforme |
| Marge gauche verso | 29,9 mm | 30,0 mm | conforme |
| Marge droite verso | 19,4 mm | 19,1 mm | proche |
| Marge gauche recto | 19,9 mm | 20,0 mm | conforme |
| Marge droite recto | 29,4 mm | 29,1 mm | proche |

**Règle.** Le corps et l’empagement actuels doivent être protégés par des tests de régression. Ils ne doivent pas être retouchés pour résoudre un problème local d’ouverture.

# 4. Système typographique

## 4.1. Contrat de fontes

Les paquets 155 × 230 et 195 × 255 contiennent :

- Chaparral Pro Regular ;
- Chaparral Pro Italic ;
- Chaparral Pro Semibold ;
- Chaparral Pro Semibold Italic ;
- Chaparral Pro Bold ;
- Josefin Sans variable romaine ;
- Josefin Sans variable italique.

Aucun Chaparral Pro Bold Italic n’est livré.

### État de la sortie actuelle

Le PDF généré incorpore désormais :

- Chaparral Pro Regular ;
- Chaparral Pro Italic ;
- Chaparral Pro Semibold ;
- Chaparral Pro Semibold Italic ;
- Josefin Sans Thin ;
- Josefin Sans Bold ;
- Josefin Sans Bold Italic.

L’ancien défaut d’italique absent est **résolu**. Le contrôle doit désormais porter sur les variantes réellement demandées, non sur un quartet théorique.

## 4.2. Styles de paragraphe confirmés par le noyau 2026

| Style | Police | Corps / interligne | Alignement | Retraits et remarques |
|---|---|---:|---|---|
| `T_2_Partie` | Josefin Sans Bold | 18 pt | centré | sans césure ; lignes solidaires |
| `T_Surtitre` | Josefin Sans Bold | 12 pt hérité | centré | capitales ; après 2 mm |
| `T_3_Article` | Josefin Sans Bold | 16/18 pt | centré | capitales ; après 2 mm |
| `T_SousTitre` | Josefin Sans Bold | 12 pt hérité | centré | après 2 mm |
| `T_a_premier` | Josefin Sans Bold | 12 pt | justifié | capitales ; avant/après 2 mm |
| `T_a` | Josefin Sans Bold | 12 pt | justifié | capitales ; avant/après 2 mm |
| `T_b` | Josefin Sans Bold | 12 pt | justifié | avant 3 mm ; après 2 mm |
| `T_c` | Josefin Sans Bold Italic | 10 pt | justifié | avant/après 2 mm |
| `T_d` | Josefin Sans Regular | 8 pt | hérité | capitales |
| `txt_Normal` | Chaparral Pro Regular | 11/13,5 pt | justifié | retrait 5 mm ; 90 % K |
| `premierPara` | hérite de `txt_Normal` | 11/13,5 pt | justifié | retrait 5 mm dans la maquette observée ; statut à arbitrer |
| `txt_Note` | Chaparral Pro Regular | 8,5/10,2 pt | justifié | hors grille |
| `txt_auteur` | Chaparral Pro Bold | 10 pt | centré | après 20 pt |
| `txt_Citation` | Chaparral Pro Regular | 9/11 pt | justifié | retrait gauche 10 mm ; avant/après 4 mm |
| `txt_Bibliographie` | Chaparral Pro Regular | 10 pt | justifié | retrait suspendu 5 mm |
| `txt_Epigraphe` | Chaparral Pro Regular | 9/10,8 pt | droite | retrait gauche 40 mm |
| `enc__titreEnc` | Josefin Sans Bold | 9 pt | hérité | retrait gauche 10 mm |
| `enc__txt_Normal` | Josefin Sans Light | 9/11 pt | justifié | gauche 10 mm ; droite 5 mm |
| `txt_Replique` | Chaparral Pro | 9/10,8 pt | justifié | retrait gauche 10 mm |
| `texte-tab` | Chaparral Pro | 8/9,5 pt | centré | cellules ; 90 % K |
| `titre_Tableau` | Chaparral Pro | 9/11 pt | centré | 10 mm avant ; 3,5 mm après |

## 4.3. Titraille du profil de production 2025

Le PDF imprimeur utilise visiblement Josefin Sans Thin plutôt que les graisses Bold nommées dans plusieurs styles 2026.

| Rôle | Cible observée 2025 |
|---|---|
| Faux-titre | Josefin Sans Thin 14 pt environ |
| Titre principal | Josefin Sans Thin 18 pt |
| Sous-titre du livre | Josefin Sans Thin Italic 16 pt |
| Partie | Josefin Sans Thin 16 pt, capitales |
| Contribution | Josefin Sans Thin 16 pt, capitales |
| Sous-titre de contribution | Josefin Sans Thin Italic 12 pt |
| Section | Josefin Sans Thin 12 pt, capitales |
| Titres courants | Josefin Sans Thin 10 pt, romain |

**Décision.** Ces valeurs appartiennent au profil 2025 et ne remplacent pas silencieusement les styles 2026.

# 5. Notes de bas de page

## 5.1. Règle cible

| Élément | Valeur cible |
|---|---|
| Appel | exposant natif |
| Numérotation | repart à 1 par contribution |
| Séparateur après numéro | point + U+2002 |
| Texte | Chaparral Pro 8,5/10,2 pt |
| Justification | justifié, hors grille |
| Filet | 0,25 pt |
| Longueur du filet | 72 pt = 25,4 mm |
| Espace avant notes | 3 mm |
| Fractionnement | autorisé |

## 5.2. État actuel

| Élément | Généré actuel | Cible | Statut |
|---|---:|---:|---|
| Corps | environ 9 pt | 8,5 pt | à corriger |
| Interligne | environ 11 pt | 10,2 pt | à corriger |
| Filet | environ 0,40 pt | 0,25 pt | à corriger |
| Longueur | environ 42 mm | 25,4 mm | à corriger |
| Compteur de la première contribution | 33 | 1 | bloquant |

# 6. Titres courants et folios

## 6.1. Règle cible

| Page | Folio | Titre courant |
|---|---|---|
| Verso | extérieur gauche | partie / livre, aligné à droite |
| Recto | extérieur droit | titre court de contribution, aligné à gauche |

- Josefin Sans Thin ou Light 10 pt ;
- romain ;
- aucun titre courant ni folio sur les ouvertures et pages spéciales.

## 6.2. État actuel

Le contenu, la graisse, le corps et la distinction recto/verso sont maintenant corrects. Le bandeau généré est situé environ 3,1 mm plus bas que dans le PDF imprimeur.

**Statut :** correction mineure mais mesurable.

# 7. Gabarits d’ouverture

## 7.1. Ouverture de partie

### Cible observée

- recto ;
- page de style vide ;
- Josefin Sans Thin 16 pt ;
- trois lignes explicites ;
- titre placé vers 42-63 mm depuis le haut du format fini ;
- filet oblique ;
- motif gris terminal ;
- blanc technique au verso.

### État actuel

- recto et blanc technique : résolus ;
- police et corps : proches ;
- titre en deux lignes au lieu de trois ;
- position environ 6,5 mm trop haute ;
- décor absent.

## 7.2. Ouverture de contribution

### Cible observée sur la page 23

- recto ;
- aucun en-tête ni folio ;
- titre Josefin Sans Thin 16 pt ;
- lignes explicites : `LES ESPACES DU SECRET` / `À CLARENS` ;
- sous-titre Josefin Sans Thin Italic 12 pt ;
- auteur et affiliation non imprimés ;
- corps commençant vers 74 mm depuis le haut du format fini ;
- notes repartant à 1.

### État actuel sur la page 19

- en-tête et folio visibles ;
- titre sur une ligne ;
- auteur et affiliation imprimés ;
- corps commençant vers 56 mm ;
- notes poursuivant à 33.

**Statut : bloquant.** Le profil doit distinguer conservation des métadonnées et visibilité sur la page.

## 7.3. Coupures éditoriales

Les coupures de titres observées ne doivent pas être reconstruites par une largeur de boîte arbitraire. La source ou une couche de métadonnées typographiques doit pouvoir fournir des lignes explicites.

Représentation possible :

```yaml
display_title_lines:
  - LES ESPACES DU SECRET
  - À CLARENS
```

La version textuelle continue reste disponible pour signets, indexation et exports non paginés.

# 8. Liminaires, fin d’ouvrage et pagination

## 8.1. Séquence observée dans *Dissimuler*

| Page physique | Fonction | Folio visible |
|---:|---|---|
| 1 | blanche | non |
| 2 | blanche | non |
| 3 | faux-titre | non |
| 4 | crédits | non |
| 5 | page de titre | non |
| 6 | blanche | non |
| 7 | introduction | non sur l’ouverture, mais page comptée 7 |

## 8.2. Pagination

Règle du profil 2025 :

- chiffres arabes ;
- comptage dès la première page physique ;
- pas de remise à zéro à l’introduction ;
- pas de remise à zéro au corps ;
- folio seulement masqué sur les pages spéciales.

### État actuel

La sortie redémarre à 1 à l’introduction. La première partie porte le numéro 15 au lieu de 21 et la première contribution 17 au lieu de 23.

**Cause attendue :** remise à zéro du compteur associée à l’introduction ou à un état de type `mainmatter`, combinée à l’absence de quatre pages liminaires.

## 8.3. Métadonnées à corriger

- balise `<em>` imprimée littéralement dans le sous-titre ;
- Anaïs Lebreton dupliquée comme autrice ;
- direction scientifique mal identifiée ;
- crédits et responsabilités non routés vers leur page ;
- colophon absent.

Ces défauts sont mixtes : source, validation des métadonnées et rendu.

# 9. Table des matières

## 9.1. Cible

La TDM du profil 2025 :

- occupe deux pages ;
- contient l’introduction ;
- contient les parties ;
- contient les contributions ;
- affiche l’auteur sous chaque contribution ;
- exclut les sections internes ;
- utilise une page de style spécifique ;
- peut accueillir le colophon au bas de la seconde page.

## 9.2. État actuel

La TDM générée :

- appartient désormais au bon livre ;
- n’est plus contaminée par un ancien `.toc` ;
- occupe trois pages ;
- inclut les intertitres internes ;
- omet les auteurs comme élément typographique distinct ;
- conserve des titres courants ordinaires sur les pages suivantes.

**Statut :** problème sémantique, non simple réglage de `tocdepth`.

# 10. Figures et images

## 10.1. État des PDF

| PDF | Images incorporées |
|---|---:|
| Généré | 0 |
| Imprimeur | 2 |

PDF imprimeur :

- page 165 : image CMJN, 332 ppp ;
- page 166 : image CMJN, 300 ppp.

## 10.2. Règle de chaîne

```text
source et ressources
  -> pivot
  -> TEI
  -> LaTEI
  -> table de chemins
  -> commande graphique
  -> PDF
```

Chaque figure doit posséder :

- une ressource résolue ; ou
- un statut explicite d’absence accepté.

Un PDF de production ne peut être validé avec zéro image lorsque le corpus en attend.

## 10.3. Prudence

Si la TEI ne contient que la légende sans `graphic`, le déficit doit être diagnostiqué en amont. Il est interdit d’extraire les images du PDF imprimeur pour contourner le problème.

# 11. Tableaux, citations, bibliographie, poésie et listes

## 11.1. Citations

- Chaparral Pro 9/11 pt ;
- retrait gauche 10 mm ;
- avant/après 4 mm ;
- pas de justification forcée des vers.

## 11.2. Bibliographie

- Chaparral Pro 10 pt ;
- retrait suspendu 5 mm.

## 11.3. Tableaux

| Élément | Valeur |
|---|---|
| Texte | Chaparral Pro 8/9,5 pt |
| Marges internes | 2 mm |
| Filets | 0,25 pt |
| Fond foncé | noir 30 % |
| Titre | 9/11 pt, centré, 10 mm avant, 3,5 mm après |

## 11.4. Poésie

Les lignes de poésie doivent être routées vers un environnement de vers ou vers une structure `lg/l`. Une suite de sauts de ligne dans un bloc justifié produit des blancs excessifs et reste interdite.

## 11.5. Listes

Les puces ne doivent pas dépendre silencieusement de Minion Pro, absente du paquet de fontes. Toute fonte ou tout glyphe de remplacement doit être déclaré par le profil et contrôlé.

# 12. Couleur et export PDF

## 12.1. Composition intérieure

Le texte courant du PDF imprimeur correspond à un noir process à 90 %. La sortie actuelle utilise du noir plein.

## 12.2. Mode écran

| Boîte | Valeur |
|---|---|
| MediaBox | 155 × 230 mm |
| CropBox | 155 × 230 mm |
| BleedBox | 155 × 230 mm |
| TrimBox | 155 × 230 mm |
| Traits de coupe | non |

## 12.3. Mode imprimeur

| Boîte / option | Valeur cible observée |
|---|---|
| TrimBox | 155 × 230 mm |
| BleedBox | 165 × 240 mm |
| MediaBox | environ 169,8 × 244,8 mm |
| Débord autour du TrimBox | environ 7,4 mm |
| Traits de coupe | oui |
| Fontes | incorporées |
| Images | préflight résolution/couleur |
| Texte | 90 % K |

La maquette intérieure et l’export imprimeur doivent rester deux couches séparées.

# 13. État des défauts depuis la version 0.5

| Défaut de la v0.5 | État v0.6 | Commentaire |
|---|---|---|
| Corps autour de 12 pt | résolu | sortie autour de 11 pt |
| Interligne autour de 14,45 pt | résolu | pas mesuré autour de 13,45 pt |
| Marges 23/23 mm | résolu pour le profil 2025 | alternance proche de 20/30 mm |
| Italiques absentes | résolu | Chaparral Italic incorporée et visible |
| Titres de partie en Chaparral 24,8 pt | résolu en grande partie | Josefin Thin 16 pt ; position/décor à corriger |
| Titres d’article en Bold 24,8 pt | résolu en grande partie | Josefin Thin 16 pt ; ouverture à corriger |
| Libellé « Chapitre » | résolu | absent |
| Titres courants identiques et italiques | résolu | marques distinctes, romaines |
| TDM étrangère provenant d’auxiliaires | résolu | TDM du bon livre |
| Ouverture à droite non fiable | résolu sur la fixture observée | à généraliser par tests |
| Pagination romaine / redémarrage | non résolu | introduction à 1 au lieu de 7 |
| Liminaires absents | non résolu | bloquant |
| Images absentes | non résolu | bloquant |
| Notes trop grandes | non résolu | environ 9 pt au lieu de 8,5 |
| Filet de notes incorrect | non résolu | environ 42 mm et 0,40 pt |
| TDM trop profonde | nouveau diagnostic précis | trois pages, intertitres inclus |
| Auteurs/affiliations sur ouverture | nouveau diagnostic précis | données à conserver mais visibilité à paramétrer |
| Décor de partie absent | non résolu | filet et motif gris |
| Mode imprimeur absent | non résolu | boîtes et traits de coupe |

# 14. Architecture LaTEI recommandée

## 14.1. Séparation

- corps LaTEI réversible ;
- profil LaTeX versionné ;
- configuration structurée ;
- métadonnées de livre ;
- préflight PDF ;
- tests dimensionnels et visuels.

## 14.2. Commandes sémantiques

Le writer doit émettre des commandes explicites pour :

- livre ;
- faux-titre ;
- crédits ;
- page de titre ;
- introduction ;
- partie ;
- contribution ;
- annexe ;
- figure ;
- tableau ;
- TDM ;
- colophon.

## 14.3. Source unique

Un fichier YAML ou JSON porte les valeurs du profil. Le générateur, les tests et la documentation doivent lire les mêmes données.

## 14.4. Statut des profils

Valeurs autorisées :

- `validated` ;
- `provisional` ;
- `quarantine` ;
- `undocumented`.

Un export de production doit être refusé par défaut pour un profil en quarantaine.

# 15. Contrat de validation automatisable

| Test | Critère |
|---|---|
| Boîtes écran | toutes les boîtes à 155 × 230 mm, tolérance ±0,05 mm |
| Boîtes imprimeur | Trim 155 × 230 ; Bleed 165 × 240 ; Media conforme au profil |
| Corps | 11 ±0,1 pt |
| Pas courant | 13,5 ±0,1 pt |
| Notes | 8,5 ±0,1 pt ; pas 10,2 ±0,2 pt |
| Empagement | tolérance ±0,5 mm par bord |
| Fontes | variantes requises incorporées ou diagnostic bloquant |
| Liminaires | séquence attendue issue des métadonnées |
| Pagination | arabe continue depuis la première page physique |
| Ouvertures | recto, style vide, titres structurés |
| Notes | remise à 1 par contribution |
| Titres courants | partie verso, contribution recto, position ±0,5 mm |
| TDM | seuls niveaux éditoriaux autorisés ; auteurs présents |
| Images | chaque ressource résolue ou absence acceptée ; aucune attente silencieuse |
| Métadonnées | aucune balise visible, aucun doublon non expliqué |
| Compilation | dossier propre, nombre de passes suffisant, aucun auxiliaire étranger |
| Régression visuelle | pages homologues recadrées sur TrimBox et comparées par zone |

# 16. Pages étalons pour *Dissimuler*

| Fonction | PDF généré avant correction | PDF imprimeur / cible |
|---|---:|---:|
| Page générique | 1 | remplacée par séquence 1-6 |
| Faux-titre | absent | 3 |
| Crédits | absent | 4 |
| Titre | générique 1 | 5 |
| Introduction | 3, folio 1 | 7, folio 7 |
| Partie | 17, folio logique 15 | 21 |
| Blanc technique | 18 | 22 |
| Contribution | 19, folio 17 | 23 |
| Page courante verso | 20 | 24 |
| Section | 21 | 25 |
| Images | absentes | 165-166 |
| TDM | 205-207 | 207-208 |

# 17. Ordre des correctifs

## P0 — structure et intégrité

1. valider les métadonnées ;
2. supprimer toute balise visible ;
3. construire les liminaires ;
4. corriger la pagination ;
5. remettre les notes à 1 par contribution ;
6. restaurer ou diagnostiquer les images ;
7. compiler dans un environnement propre.

## P1 — gabarits

1. ouverture de partie ;
2. ouverture de contribution ;
3. visibilité auteur/affiliation ;
4. coupures éditoriales ;
5. table des matières et colophon ;
6. titres courants remontés.

## P2 — microtypographie

1. notes 8,5/10,2 ;
2. filet de notes ;
3. citations ;
4. bibliographie ;
5. poésie ;
6. tableaux ;
7. listes ;
8. couleur 90 % K.

## P3 — export imprimeur

1. boîtes PDF ;
2. traits de coupe ;
3. contrôle des fontes ;
4. contrôle des images ;
5. rapport de préflight ;
6. manifeste de production.

# 18. Corpus minimal requis pour une version 1.0

## 18.1. 155 × 230

À terme, exporter en IDML et PDF les modèles :

- PDT ;
- PL ;
- INTERCALAIRE ;
- UE_Coll ;
- UE_Auteurs ;
- UE_Resumes ;
- UE_Index ;
- TDM.

Pour les deux INDD de *Dissimuler*, l’export IDML est souhaitable mais reporté. Il ne bloque pas les passes P0-P3 déjà fondées sur le PDF imprimeur.

## 18.2. 195 × 255

Exporter en IDML et PDF au minimum :

- UE ;
- PL ;
- PDT ;
- TDM ;
- auteurs ;
- index ;
- résumés ;
- intercalaire.

Documenter `UE_Coll`, `MOD_PL` et `MOD_TDM`.

## 18.3. 180 × 240

Ouvrir le fichier supposé UE, confirmer son format réel, le renommer et fournir INDD, IDML, PDF et fontes. Le dossier reste en quarantaine jusque-là.

## 18.4. Quatrième format

Identifier la dimension et fournir un corpus minimal complet.

## 18.5. Code

Le dépôt source du générateur, ses tests, le writer et le profil doivent être contrôlés ensemble. Les correctifs ne doivent jamais être appliqués seulement au `book.tex` généré.

# 19. Règles de gouvernance

**Preuve.** Toute valeur cite un fichier, un PDF daté, un IDML ou une décision éditoriale datée.

**Statut.** Chaque règle est confirmée, provisoire, variante autorisée, en quarantaine ou non documentée.

**Historique.** Une règle devenue fausse ne disparaît pas sans trace : elle est marquée résolue dans le tableau de suivi.

**Séparation.** Couverture, composition intérieure et export imprimeur restent des couches distinctes.

**Machine et humain.** Le référentiel humain possède une représentation structurée. Aucune valeur n’est maintenue manuellement dans plusieurs modules.

**Régression.** Chaque règle implémentée possède un test dimensionnel ou visuel avec tolérance explicite.

**Prudence.** Une absence d’IDML réduit le niveau de preuve interne, mais n’annule pas une mesure certaine du PDF de production.

**Production.** Le terme « PDF imprimeur » ne peut être employé que si le préflight, les fontes, les images, les boîtes et les diagnostics bloquants sont satisfaits.

# Annexe A — inventaire fonctionnel 195 × 255

| Fonction | Fichier | Statut |
|---|---|---|
| Unité éditoriale | `UE_195x255.indd` | présente |
| Auteurs | `UE_Auteurs_195x255.indd` | présente |
| Collection | `UE_Coll_195x255.indd` | présente |
| Index | `UE_Index_195x255.indd` | présente |
| Résumés | `UE_Resumes_195x255.indd` | présente |
| Pages liminaires | `PL_195x255.indd`, `MOD_PL.indd` | articulation non documentée |
| Page de titre | `PDT_195x255.indd` | présente |
| Table des matières | `TDM_195x255.indd`, `MOD_TDM.indd` | articulation non documentée |
| Intercalaire | `INTERCALAIRE.indd` | présent |

Aucune mesure 155 × 230 ne doit être recopiée par défaut vers ce format.

# Annexe B — ambiguïtés encore ouvertes

| Point | Statut |
|---|---|
| Divergence Thin 2025 / Bold 2026 | décision éditoriale attendue ; profils séparés en attendant |
| Premier paragraphe avec retrait 5 mm | à confirmer |
| `txt_Citation_fin` divergent | à corriger ou documenter |
| Légende héritant possiblement du retrait | à contrôler |
| Puce Minion Pro absente | alternative à décider |
| Gabarit C | fonction non documentée |
| Noir importé `Word_R0_G0_B10` | accident probable à arbitrer |
| Rôle des fichiers `MOD_*` | non documenté |
| Format 180 × 240 | quarantaine |
| Liens graphiques des deux INDD | non certifiables sans IDML/InDesign |
| Coupures forcées dans les INDD | confirmées visuellement, stockage interne non certifié |

# Annexe C — portée exacte de la version 0.6

## Inclus

- mesures du noyau UE 155 × 230 actuel ;
- profil de production 2025 observé ;
- comparaison actualisée du PDF généré et du PDF imprimeur de *Dissimuler* ;
- contrôle des boîtes et des fontes ;
- inspection des aperçus et métadonnées des deux INDD ;
- suivi des défauts résolus depuis la version 0.5 ;
- règles pour liminaires, pagination, ouvertures, notes, TDM, images et export imprimeur ;
- contrat de validation automatisable.

## Exclus

- extraction complète des propriétés internes des deux nouveaux INDD ;
- certification du 195 × 255 ;
- normalisation du 180 × 240 ;
- quatrième format ;
- règles de couverture ;
- toute valeur inventée pour combler une source absente.

## Promotion en source de vérité

La version 0.6 peut servir de référence technique provisoire pour développer `purh_155x230_production_2025`. Elle pourra être promue après :

1. implémentation et validation des correctifs P0-P3 ;
2. contrôle du dépôt source ;
3. préflight réussi du PDF ;
4. résolution des images ;
5. arbitrage éditorial des principales divergences ;
6. export IDML ultérieur des deux INDD, utilisé comme contre-épreuve.
