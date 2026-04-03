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

Le dossier d'assets choisi dans l'interface est **copié tel quel** dans la sortie sous `assets/`.
Il ne faut donc pas réorganiser les médias au moment du build : **la source de vérité est le XML**.

Exemple d'arborescence de sortie attendue :

```text
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
```

Si le XML contient une référence de type :

```xml
<graphic url="../icono/br/Ch03_Loskoutoff_1/fig10.jpg"/>
```

alors le HTML généré contiendra :

```html
src="assets/images/../icono/br/Ch03_Loskoutoff_1/fig10.jpg"
```

ce qui résout côté navigateur vers :

```text
assets/icono/br/Ch03_Loskoutoff_1/fig10.jpg
```

Conventions encore reconnues pour les éléments de thème :

- **couverture** : noms contenant `cover`, `couverture`, `couv` ;
- **logo université** : noms contenant `universite`, `university` ou `urn` ;
- **logo PURH** : noms contenant `purh` ou `presses`.

Pour des références simples comme :

```xml
<graphic url="figure-1.jpg"/>
```

le générateur produira toujours un chemin relatif à `assets/images/figure-1.jpg`.

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
