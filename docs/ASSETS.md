# Gestion des ressources matérielles (`assets`)

## 1. Trois catégories de ressources

Le générateur distingue trois origines pour chaque ressource.

| Catégorie | `declared_by` | Description |
|-----------|--------------|-------------|
| Référencée par le XML | `"xml"` | Images, figures, graphiques appelés par `<graphic url="…"/>` dans le XML |
| Déclarée par la boîte de dialogue | `"dialog"` | PDF éditeur, couvertures et autres fichiers fournis par l'utilisateur hors XML |
| Générée automatiquement | `"generator"` | CSS, JS, PDF LaTEI, fichiers LaTeX, manifeste |

Aucune ressource n'est implicite. Un fichier est pris en compte uniquement s'il appartient à l'une de ces trois catégories.

---

## 2. Structure recommandée du dossier source

```text
mon-livre/
├── livre.xml
├── ch_001_intro.xml
├── assets/
│   ├── images/
│   │   ├── fig_001.jpg
│   │   └── fig_002.png
│   ├── couvertures/
│   │   ├── couverture.jpg
│   │   └── quatrieme.jpg
│   ├── pdf/
│   │   └── pdf-editeur.pdf
│   └── logos/
│       ├── purh.png
│       └── universite.png
└── build_config.json
```

Cette structure n'est pas obligatoire, mais elle rend le projet transportable entre machines.

---

## 3. Ressources référencées par le XML (`declared_by: "xml"`)

Les fichiers appelés directement dans le XML via `<graphic url="…"/>` doivent être présents dans le dossier `assets` fourni par l'utilisateur.

### Règle de résolution des chemins

Le XSL applique la règle suivante pour calculer le chemin HTML de chaque image :

- Si `url` commence par `assets/`, `/`, `data:` ou contient `://` → chemin utilisé tel quel
- Sinon → l'image est cherchée sous `assets/images/{url}`

Exemples :

```xml
<graphic url="assets/images/fig_001.jpg"/>
<!-- → HTML : assets/images/fig_001.jpg -->

<graphic url="fig_002.png"/>
<!-- → HTML : assets/images/fig_002.png -->
```

### Vérification et messages

Le générateur vérifie l'existence de chaque image dans le dossier de sortie après la copie des assets. Si une image est introuvable, le rapport de build contient :

```
[RESSOURCE MANQUANTE] Image introuvable : assets/images/fig_004.jpg
```

Si l'image est présente, elle apparaît dans le manifeste avec `declared_by: "xml"`.

---

## 4. Ressources déclarées par la boîte de dialogue (`declared_by: "dialog"`)

### 4.1 Le dossier `assets`

L'utilisateur sélectionne un dossier `assets` dans la boîte de dialogue. Son contenu est copié tel quel dans `sortie/assets/`. La structure interne est préservée.

**Sous-dossiers reconnus automatiquement :**

| Dossier source | Rôle détecté | Condition |
|----------------|-------------|-----------|
| `assets/images/` | Images du livre | Toute image correspondant aux URL XML |
| `assets/pdf/` | PDF éditeur | Tout fichier `.pdf` dans ce sous-dossier |
| `assets/couvertures/` ou `assets/covers/` | Couvertures | Fichier dont le nom contient `couv` ou `cover` |
| `assets/logos/` | Logos institutionnels | Fichier dont le nom contient `purh`, `universite`, `urn` |
| `assets/quatrieme/` | Quatrième de couverture textuelle | Fichier `.md`, `.html`, ou `.txt` |

### 4.2 PDF éditeur

Si le dossier `assets/pdf/` contient au moins un fichier `.pdf`, il est considéré comme le PDF éditeur officiel.

- Il est copié dans `sortie/assets/pdf/` en conservant son nom d'origine.
- Le site affiche un lien **Télécharger le PDF éditeur**.
- Le rapport signale : `PDF éditeur copié vers : assets/pdf/nom-du-fichier.pdf`

**Si un PDF éditeur est présent, la génération LaTEI/PDF est désactivée automatiquement.** Ce comportement évite d'écraser ou de confondre les deux PDF. Le rapport l'indique :

```
Génération LaTeX/PDF : désactivée car un PDF éditeur est disponible.
```

### 4.3 Quatrième de couverture (fichier externe)

Si l'utilisateur sélectionne un fichier de quatrième de couverture dans la boîte de dialogue (champ dédié), ce fichier est lu et son contenu est injecté dans le HTML. Formats acceptés : `.md`, `.markdown`, `.html`, `.htm`, `.txt`.

---

## 5. Ressources générées automatiquement (`declared_by: "generator"`)

| Fichier de sortie | Rôle | Condition |
|-------------------|------|-----------|
| `assets/site.css` | Feuille de style du site | Toujours |
| `assets/app.js` | Script du site | Toujours |
| `assets/metadata/manifest.json` | Manifeste des ressources | Toujours |
| `assets/generated/book.tex` | Fichier LaTeX LaTEI | Si mode ≠ `none` |
| `assets/generated/book.pdf` | PDF généré par LaTEI | Si mode = `latei_pdf` et lualatex disponible |
| `assets/generated/pdf_build_report.txt` | Journal de compilation LaTeX | Si mode ≠ `none` |
| `assets/generated/latei_assets/images/` | Images copiées pour LaTeX | Si mode ≠ `none` et images présentes |
| `book.normalized.xml` | TEI normalisé (à la racine du site) | Si `write_normalized_tei = True` |

Le PDF LaTEI (`assets/generated/book.pdf`) est distinct du PDF éditeur. Ces deux fichiers peuvent coexister uniquement si le PDF éditeur est absent lors de la génération.

---

## 6. Structure du dossier de sortie

```text
sortie/
├── index.html
├── chapitre-1.html
├── chapitre-2.html
├── book.normalized.xml
└── assets/
    ├── site.css              ← generator
    ├── app.js                ← generator
    ├── images/               ← dialog (contenu du dossier assets source)
    │   ├── fig_001.jpg
    │   └── fig_002.png
    ├── couvertures/          ← dialog (si présent dans assets source)
    │   └── couverture.jpg
    ├── pdf/                  ← dialog (si présent dans assets source)
    │   └── pdf-editeur.pdf
    ├── logos/                ← dialog (si présent dans assets source)
    │   ├── purh.png
    │   └── universite.png
    ├── generated/            ← generator (si mode LaTEI activé)
    │   ├── book.tex
    │   ├── book.pdf
    │   ├── pdf_build_report.txt
    │   └── latei_assets/
    │       └── images/
    │           └── <sha1>-fig_001.png
    └── metadata/             ← generator
        └── manifest.json
```

**Sous-dossiers absents si inutiles :**

- `assets/pdf/` → absent si aucun PDF n'est fourni dans le dossier `assets` source
- `assets/generated/` → absent si le mode LaTEI est désactivé (`pdf_export_mode = "none"`)
- `assets/generated/latei_assets/` → absent si le livre ne contient aucune image

---

## 7. Règles de priorité

### 7.1 Quatrième de couverture

1. **XML** (`<abstract rend="4e-couv">`) → priorité maximale
2. Fichier sélectionné dans la boîte de dialogue → priorité si XML absent
3. Fichier `assets/quatrieme/*.md|html|txt` → priorité si les deux précédents sont absents

Si aucune quatrième de couverture n'est trouvée, le rapport signale :

```
Aucune quatrième de couverture déclarée. Le générateur utilisera le résumé XML si disponible.
```

### 7.2 PDF

- **Le PDF éditeur ne peut jamais être écrasé par le PDF LaTEI** : si un PDF éditeur est présent dans `assets/pdf/`, la génération LaTEI est désactivée.
- Si aucun PDF éditeur n'est présent, la génération LaTEI peut produire `assets/generated/book.pdf`.
- Les deux ne coexistent que si le PDF éditeur est ajouté manuellement *après* une génération LaTEI.

### 7.3 Source sémantique

Le XML reste la source sémantique principale. Les fichiers déclarés dans la boîte de dialogue complètent ou remplacent uniquement les éléments matériels (PDF, couverture image) ; ils ne modifient jamais le texte du livre.

---

## 8. Manifeste des ressources

Le générateur produit toujours le fichier :

```
assets/metadata/manifest.json
```

Ce fichier liste toutes les ressources copiées ou générées, avec leur origine et leur rôle.

### Structure

```json
{
  "version": 1,
  "images": [
    {
      "source": "assets/images/fig_001.jpg",
      "output": "assets/images/fig_001.jpg",
      "declared_by": "xml",
      "role": "image"
    }
  ],
  "covers": [
    {
      "output": "assets/couvertures/couverture.jpg",
      "declared_by": "dialog",
      "role": "cover_front"
    }
  ],
  "downloads": [
    {
      "output": "assets/pdf/pdf-editeur.pdf",
      "declared_by": "dialog",
      "role": "editor_pdf"
    },
    {
      "output": "assets/generated/book.pdf",
      "declared_by": "generator",
      "role": "latei_pdf"
    }
  ],
  "static": [
    { "output": "assets/site.css", "declared_by": "generator", "role": "css" },
    { "output": "assets/app.js",   "declared_by": "generator", "role": "js" },
    { "output": "assets/metadata/manifest.json", "declared_by": "generator", "role": "manifest" }
  ],
  "warnings": []
}
```

### Champs par entrée

| Champ | Signification |
|-------|--------------|
| `output` | Chemin relatif depuis la racine du site |
| `declared_by` | Origine : `"xml"`, `"dialog"` ou `"generator"` |
| `role` | Rôle fonctionnel de la ressource |
| `source` | Chemin source d'origine (présent uniquement pour les images XML) |

### Rôles reconnus

| `role` | Description |
|--------|-------------|
| `image` | Image référencée par le XML |
| `cover_front` | Couverture première de couverture |
| `cover_back` | Quatrième de couverture image |
| `editor_pdf` | PDF fourni par l'éditeur |
| `latei_pdf` | PDF généré par LaTEI/LaTeX |
| `css` | Feuille de style du site |
| `js` | Script JavaScript du site |
| `manifest` | Ce fichier manifeste lui-même |

---

## 9. Messages utilisateur dans le rapport de build

Le rapport (`build_report.txt`) contient les messages suivants liés aux ressources :

```
Couverture détectée : assets/couvertures/couverture.jpg
Logo université : assets/logos/universite.png
Logo PURH : assets/logos/purh.png
PDF éditeur copié vers : assets/pdf/pdf-editeur.pdf
Génération LaTeX/PDF : désactivée car un PDF éditeur est disponible.
PDF généré : assets/generated/book.pdf
Quatrième de couverture : XML (abstract rend="4e-couv")
Aucune quatrième de couverture déclarée. Le générateur utilisera le résumé XML si disponible.
[RESSOURCE MANQUANTE] Image introuvable : assets/images/fig_004.jpg
Manifeste des ressources généré : assets/metadata/manifest.json
```

---

## 10. Règle d'or

Le dossier `assets` ne doit jamais être une poubelle.

Chaque fichier présent dans `sortie/assets/` a une origine traçable (XML, boîte de dialogue ou générateur) et un rôle identifié dans le manifeste. Si un fichier ne correspond à aucune de ces catégories, il ne doit pas être présent.
