# Architecture — Suppression de l'ancienne chaîne PDF stable

## Décision

L'ancienne chaîne PDF stable a été retirée du code actif (passe E5 radicale, branche `nouvelle-stable`).

Elle n'est pas placée dans un dossier `legacy`, car l'historique Git et les branches/tags V1 jouent ce rôle d'archive.

La chaîne PDF active est désormais LaTEI.

## Modules supprimés

| Module | Rôle dans l'ancienne chaîne |
|---|---|
| `purh_site/pdf_builder.py` | Moteur de compilation PDF (PdfBuilder) |
| `purh_site/latex_renderer.py` | Rendu LaTeX depuis le modèle sémantique |
| `purh_site/semantic_model.py` | Modèle intermédiaire (Book, Division, etc.) |
| `purh_site/tei_to_model.py` | Parseur TEI → modèle intermédiaire |
| `purh_site/stable_pdf_export.py` | Façade exposée à site_builder |
| `purh_site/latei_stable_pdf.py` | Pont LaTEI body → ancienne chaîne |
| `purh_site/latei_convergence_audit.py` | Outil de comparaison inter-chaînes (debug migration) |

## Tests supprimés

Ces fichiers testaient exclusivement l'ancienne chaîne ou ses ponts de transition :

- `tests/test_pdf_latex.py`
- `tests/test_pdf_latex_compile.py`
- `tests/test_pdf_structure.py`
- `tests/test_stable_pdf_export_adapter.py`
- `tests/test_latei_to_stable_pdf.py`
- `tests/test_stable_purh_decisions_contract.py`
- `tests/test_latei_direct_frontmatter_numbering.py`
- `tests/test_latei_direct_title_page.py`
- `tests/test_latei_tex_convergence_audit.py`
- `tests/test_latei_pdf_convergence_audit.py`

## Compatibilité temporaire

Les anciens noms de modes `latex` et `latex_pdf` sont conservés provisoirement comme alias vers `latei` et `latei_pdf`, afin de ne pas modifier le GUI dans cette passe.

La logique dans `site_builder.py._build_pdf_site_artifacts` :

```python
# Compatibility aliases: legacy mode names now route to the LaTEI PDF chain.
if mode in {"latei", "latex"}:
    build_site_latei_pdf_artifacts(..., compile_pdf=False)
else:  # latei_pdf, latex_pdf
    build_site_latei_pdf_artifacts(..., compile_pdf=True)
```

## Architecture cible

```
site_builder → LaTEI uniquement
branches/tags Git V1 → archive de l'ancienne chaîne stable
```

## Modes PDF actifs

Depuis la passe E6, les seuls modes PDF/LaTeX acceptés sont :

- `none` : aucun export PDF/LaTeX ;
- `latei` : export du monofichier LaTEI ;
- `latei_pdf` : export du monofichier LaTEI et compilation PDF.

Les anciens modes `latex` et `latex_pdf` ne sont plus supportés.
Ils appartiennent à l'ancienne chaîne stable, conservée uniquement dans l'historique Git / branches V1.
