# Prototype PURH — TEI Métopes vers livre web statique

Ce prototype prend comme entrée un **fichier maître TEI Métopes** et construit un **site-livre multi-pages**.

## Ce que fait cette version

- charge un fichier maître XML ;
- résout les `xi:include` ;
- écrit un `book.normalized.xml` ;
- génère **une page HTML par chapitre** pour une monographie ;
- génère **une page HTML par contribution** pour un collectif ;
- construit un **menu latéral arborescent** ;
- prend en charge les médias TEI quand le XML contient `graphic` ou `media` avec `url` ;
- copie un dossier `assets/` utilisateur dans la sortie.

## Convention d'assets

Placez vos fichiers dans un dossier du type :

```text
assets/
  images/
    cover.jpg
    couverture.png
    ... figures du livre ...
  audio/
  video/
  logos/
    universite.svg
    urn.png
    purh.svg
```

Conventions reconnues par le prototype :

- **couverture** : noms contenant `cover`, `couverture`, `couv` ;
- **logo université** : noms contenant `universite`, `university` ou `urn` ;
- **logo PURH** : noms contenant `purh` ou `presses`.

Si un fichier TEI contient par exemple :

```xml
<graphic url="figure-1.jpg"/>
```

le générateur cherchera l'image dans `assets/images/figure-1.jpg`.

## Lancer l'interface

```bash
pip install -r requirements.txt
python main.py
```

## Sortie générée

Le dossier de sortie contient en général :

- `index.html` : page d'accueil du livre ;
- `01-...html`, `02-...html`, etc. : pages des chapitres ou contributions ;
- `assets/` : CSS, JS, médias copiés ;
- `book.normalized.xml` ;
- `build_report.txt`.


## Prévisualisation locale

Après la génération, l'interface peut démarrer automatiquement un petit serveur local et ouvrir le navigateur sur `http://127.0.0.1:8000/index.html` ou, si ce port est occupé, sur `8080` puis sur un port libre.
