# Architecture — Suppression de l'ancienne chaîne PDF stable

## Décision

L'ancienne chaîne PDF stable a été retirée du code actif (passe E5 radicale, branche `nouvelle-stable`).

Elle n'est pas placée dans un dossier `legacy`, car l'historique Git et les branches/tags V1 jouent ce rôle d'archive.

La chaîne PDF active est désormais LaTEI.

## Modules supprimés

| Module                                 | Rôle dans l'ancienne chaîne                                      |
| -------------------------------------- | ---------------------------------------------------------------- |
| `purh_site/pdf_builder.py`             | Moteur de compilation PDF (`PdfBuilder`)                         |
| `purh_site/latex_renderer.py`          | Rendu LaTeX depuis le modèle sémantique                          |
| `purh_site/semantic_model.py`          | Modèle intermédiaire (`Book`, `Division`, etc.)                  |
| `purh_site/tei_to_model.py`            | Parseur TEI → modèle intermédiaire                               |
| `purh_site/stable_pdf_export.py`       | Façade exposée à `site_builder`                                  |
| `purh_site/latei_stable_pdf.py`        | Pont LaTEI body → ancienne chaîne                                |
| `purh_site/latei_convergence_audit.py` | Outil de comparaison inter-chaînes, utilisé pendant la migration |

## Tests supprimés

Ces fichiers testaient exclusivement l'ancienne chaîne stable ou ses ponts de transition :

* `tests/test_pdf_latex.py`
* `tests/test_pdf_latex_compile.py`
* `tests/test_pdf_structure.py`
* `tests/test_stable_pdf_export_adapter.py`
* `tests/test_latei_to_stable_pdf.py`
* `tests/test_stable_purh_decisions_contract.py`
* `tests/test_latei_tex_convergence_audit.py`
* `tests/test_latei_pdf_convergence_audit.py`

Les tests `tests/test_latei_direct_frontmatter_numbering.py` et `tests/test_latei_direct_title_page.py` ont été restaurés et réécrits comme tests directs de la chaîne LaTEI active, sans dépendance à l'ancienne chaîne stable.

## Absence de compatibilité avec les anciens modes

Depuis la passe E6, les anciens modes `latex` et `latex_pdf` ne sont plus acceptés comme alias.

Toute valeur inconnue de `pdf_export_mode`, y compris `latex` et `latex_pdf`, est normalisée vers `none`.

Cette décision évite de conserver dans le code actif les traces fonctionnelles de l'ancienne chaîne PDF stable.

## Modes PDF actifs

Depuis la passe E6, les seuls modes PDF/LaTeX acceptés sont :

* `none` : aucun export PDF/LaTeX ;
* `latei` : export du monofichier LaTEI ;
* `latei_pdf` : export du monofichier LaTEI et compilation PDF.

## Architecture cible

```text
site_builder → LaTEI uniquement
branches/tags Git V1 → archive de l'ancienne chaîne stable
```

## Interface graphique

Depuis la passe E6, le GUI expose uniquement les modes LaTEI :

* aucun export PDF/LaTeX ;
* LaTEI monofichier (`.tex`) ;
* LaTEI monofichier + PDF.

Les anciens modes `latex` et `latex_pdf` ne sont plus présentés dans l'interface et ne sont plus supportés comme alias internes.

## Principe de maintenance

La chaîne active doit désormais rester unique :

```text
XML Métopes / TEI Commons-Publishing
        ↓
arbre réversible Python
        ↓
monofichier LaTEI
        ↓
PDF
```

L'ancienne chaîne stable n'est plus maintenue dans le code actif. Elle reste disponible uniquement par l'historique Git et les branches/tags V1.

Toute nouvelle correction typographique ou éditoriale doit donc être portée dans la chaîne LaTEI, et non dans une chaîne parallèle.
