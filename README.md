# Impressions — TEI Métopes vers livre web statique

Impressions est un générateur de **livres web statiques** à partir de fichiers **TEI Métopes**.  
Développé en python, utilisable en interface graphique, il produit un site HTML complet, structuré, navigable et directement publiable par simple FTP.

---

## Objectif

À partir d’un **fichier maître TEI**, Impressions construit un **livre numérique multi-pages** :

- sans base de données,
- sans CMS,
- avec une structure éditoriale robuste,
- compatible avec les usages académiques (citabilité, métadonnées, Zotero).

---

## Fonctionnalités

### Traitement TEI
- chargement d’un fichier maître XML ;
- résolution des `xi:include` ;
- normalisation et export d’un `book.normalized.xml` ;
- transformation TEI → HTML via XSLT.

### Génération du livre
- **une page HTML par chapitre** (monographie) ;
- **une page HTML par contribution** (collectif) ;
- génération automatique du **sommaire** ;
- navigation précédente / suivante ;
- menu latéral arborescent.

### 🔹 Métadonnées et édition
- génération de **cartes de citabilité** (chapitre / article) ;
- intégration des :
  - auteurs,
  - directeurs de volume (*Dir.*),
  - ISBN / ISSN,
  - collection (depuis XML ou interface gui) ;
  - quatrième de couverture (embarquée dans le XML ou via interface gui)
- format de citation conforme aux usages PURH.

### Page d’accueil enrichie
- présentation du volume ;
- **quatrième de couverture** :
  - prioritairement depuis le XML ;
  - sinon depuis `assets/quatrieme/` (Markdown, HTML ou TXT) ;
- boutons de téléchargement :
  - XML normalisé ;
  - PDF (si présent dans `assets/PDF`) ;
- affichage de la couverture.

### 🔹 Médias et assets
- prise en charge des balises TEI :
  - `graphic`
  - `media`
- zoom (lightbox) sur les images ;
- bouton de téléchargement des images ;
- copie automatique du dossier `assets/`.

### Interface utilisateur : facilité d'utilisation pour les éditeurs et éditrices
- interface graphique (Tkinter) permettant :
  - sélection du XML ;
  - sélection du dossier `assets` ;
  - configuration des métadonnées complémentaires (collection, ISSN, etc.).

### 🔹 Compatibilité Zotero
- ajout de métadonnées intégrées (Open Graph + Dublin Core) ;
- détection automatique du type (livre / chapitre) ;
- récupération automatique dans Zotero.

### 🔹 Habillage éditorial
- bandeau avec logos de la maison d'édition ;
- sidebar structurée ;
- footer intégré avec crédits :
  - Impressions
  - PURH
  - Chaire d’excellence en édition numérique (CEEN).

---

## 📁 Convention d’assets

Le dossier choisi dans l’interface est **copié tel quel** dans `assets/`. Le XML reste la **source de vérité** pour les chemins.

### Exemple

```
site/
  index.html
  01-chapitre.html
  assets/
    icono/
      br/
        Ch03_Loskoutoff_1/
          fig10.jpg
    logos/
      purh.svg
      universite.svg
      ceen.svg
    quatrieme
```

### Exemple TEI

```
<graphic url="../icono/br/Ch03_Loskoutoff_1/fig10.jpg"/>
```

---

## Conventions automatiques

Détection automatique dans `assets/` :

- **couverture** :
  - `cover`, `couverture`, `couv`
- **logo université** :
  - `universite`, `university`
- **logo maison d'édition** :
  - `logo`, `presses`
- **logo footer (optionnel)** :
  - placé dans `assets/logos/`

---

## Quatrième de couverture

Ordre de priorité :

1. XML (si présent)
2. `assets/quatrieme/` :
   - `.md` (prioritaire)
   - `.html`
   - `.txt`

---

## Collections (mode hybride)

Les informations de collection peuvent provenir :

- du XML (si présentes) ;
- ou de l’interface graphique.

Sont pris en charge :
- nom de collection
- numéro
- ISSN

→ affichage dans :
- page d’accueil
- citations
- sidebar (lien vers la collection)

---

## Librairie requises
- lxml
- re

## Lancer l’application

```
pip install -r requirements.txt
python main.py
```

---

## Sortie générée

```
output/
  index.html
  01-chapitre.html
  02-chapitre.html
  assets/
  book.normalized.xml
  build_report.txt
```

---

## Philosophie

Impressions repose sur quelques principes forts :

- **sobriété technique** (pas de CMS, pas de base de données)
- **pérennité des formats** (TEI comme source)
- **édition savante** (citabilité, structure)
- **séparation stricte contenu / rendu**

---

## Crédits

Impressions est développé par Tony Gheeraert dans le cadre des :

- Presses universitaires de Rouen et du Havre (PURH)
- Chaire d’excellence en édition numérique (CEEN)
  https://ceen.hypotheses.org/

---

## Licence

MIT
