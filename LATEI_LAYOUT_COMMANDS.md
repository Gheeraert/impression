# Commandes LaTEI de mise en page (`\latei...`)

## Doctrine des trois couches

Le LaTEI repose sur trois couches strictement séparées :

```
\tei...     = contenu éditorial réversible → restauré vers XML/Métopes
\latei...   = corrections locales de mise en page PDF → ignorées au retour XML
LaTeX brut  = réservé au moteur, interdit dans la zone lateiDocument
```

**Règle absolue :** aucune commande LaTeX brute (`\noindent`, `\vspace`, `\newpage`, `\clearpage`, `\nopagebreak`, etc.) n'est autorisée dans la zone `lateiDocument`. Toute commande inconnue du parseur lève `LatexParseError`.

## Comportement du parseur

- **`LAYOUT_WRAPPER_MACROS`** : lit le groupe `{...}`, le parse récursivement, insère les nœuds résultants directement. Aucun élément TEI créé pour l'enveloppe.
- **`LAYOUT_PARAM_WRAPPER_MACROS`** : lit `{size}` (valide : `small`, `medium`, `large`), lit `{...}`, parse et insère les nœuds. Le paramètre est ignoré pour le XML.
- **`LAYOUT_STANDALONE_MACROS`** : consomme la commande, n'ajoute rien au XML.
- **`LAYOUT_PARAM_STANDALONE_MACROS`** : lit `{size}` (valide : `small`, `medium`, `large`), n'ajoute rien au XML.

Les valeurs `12pt`, `1em`, `huge`, etc. sont rejetées avec `LatexParseError`.

## Tableau complet des commandes

| Commande | Type | Effet PDF | Retour XML |
|---|---|---|---|
| `\lateiNoIndent{...}` | enveloppante | supprime l'alinéa de première ligne | conserve le contenu |
| `\lateiIndent{...}` | enveloppante | force l'alinéa de première ligne | conserve le contenu |
| `\lateiSpaceBefore{size}{...}` | enveloppante paramétrée | blanc vertical avant | conserve le contenu |
| `\lateiSpaceAfter{size}{...}` | enveloppante paramétrée | blanc vertical après | conserve le contenu |
| `\lateiPageBreakBefore{...}` | enveloppante | saut de page avant | conserve le contenu |
| `\lateiPageBreakAfter{...}` | enveloppante | saut de page après | conserve le contenu |
| `\lateiClearPageBefore{...}` | enveloppante | nouvelle page + flottants avant | conserve le contenu |
| `\lateiClearPageAfter{...}` | enveloppante | nouvelle page + flottants après | conserve le contenu |
| `\lateiKeepWithNext{...}` | enveloppante | interdit coupure après | conserve le contenu |
| `\lateiKeepTogether{...}` | enveloppante | maintient sur une page | conserve le contenu |
| `\lateiNoPageBreakBefore{...}` | enveloppante | interdit coupure avant | conserve le contenu |
| `\lateiNoPageBreakAfter{...}` | enveloppante | interdit coupure après | conserve le contenu |
| `\lateiVSpace{size}` | autonome paramétrée | blanc vertical | ignorée |
| `\lateiPageBreak` | autonome | saut de page | ignorée |
| `\lateiClearPage` | autonome | nouvelle page + flottants | ignorée |

Tailles valides pour `{size}` : `small` (~0,5 ligne), `medium` (~1 ligne), `large` (~2 lignes).

## Implémentation PDF — `purh_site/resources/latei_macros.tex`

La macro interne `\lateiApplyVSpace{size}` traduit les tailles normalisées :

```latex
\NewDocumentCommand{\lateiApplyVSpace}{m}{%
  \IfStrEqCase{#1}{%
    {small}{\addvspace{0.5\baselineskip}}%
    {medium}{\addvspace{\baselineskip}}%
    {large}{\addvspace{2\baselineskip}}%
  }[...]%
}
```

`\lateiNoIndent` utilise un groupe local pour confiner la modification de `\parindent` :

```latex
\NewDocumentCommand{\lateiNoIndent}{+m}{{\parindent=0pt #1}}
```

`\lateiIndent` sauvegarde le `\parindent` du document à `\AtBeginDocument` :

```latex
\newlength{\lateiParindent}
\AtBeginDocument{\setlength{\lateiParindent}{\parindent}}
\NewDocumentCommand{\lateiIndent}{+m}{{\setlength{\parindent}{\lateiParindent}#1}}
```

## Implémentation parseur — `purh_site/reversible/latex_reader.py`

Quatre sets distincts dans le module :

```python
LAYOUT_WRAPPER_MACROS          # enveloppantes sans paramètre
LAYOUT_PARAM_WRAPPER_MACROS    # enveloppantes avec size
LAYOUT_STANDALONE_MACROS       # autonomes sans paramètre
LAYOUT_PARAM_STANDALONE_MACROS # autonomes avec size
```

`_controlled_macro_at_pos()` inclut tous ces sets. `parse_nodes()` dispatche selon le set.

## Procédure pour ajouter une nouvelle commande `\latei...`

1. **Choisir le type** parmi les quatre familles ci-dessus.
2. **Déclarer la macro PDF** dans `purh_site/resources/latei_macros.tex` avec `\NewDocumentCommand`.
3. **Ajouter le nom** (sans `\`) dans le set correspondant de `latex_reader.py`.
4. **Ajouter des tests** dans `tests/test_latei_layout_commands.py` (le test parametrisé `test_macro_defined_in_latei_macros_tex` s'exécutera automatiquement).
5. **Documenter** la commande dans ce fichier et dans `MODE_EMPLOI_LATEI_EDITRICES.md`.

**Règle : ne jamais ajouter du LaTeX arbitraire.** Chaque commande `\latei...` doit correspondre à un geste éditorial identifiable, pas à une valeur de dimension libre.
