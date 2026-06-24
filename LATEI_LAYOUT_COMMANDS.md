# Commandes LaTEI de mise en page (`\latei...`)

## Principe

Les commandes `\latei...` sont des corrections de mise en page PDF **non exportées vers le XML**.

- Les commandes `\tei...` encodent du contenu éditorial réversible (elles produisent des éléments TEI lors de la restauration XML).
- Les commandes `\latei...` enveloppent du contenu `\tei...` pour corriger l'apparence du PDF sans modifier la structure sémantique. Lors de la restauration XML, leur enveloppe est ignorée et leur contenu est parsé normalement.

Ce mécanisme permet d'apporter des corrections typographiques locales dans le fichier `.latei.tex` sans risquer de corrompre la restauration XML.

## Commandes disponibles

### `\lateiNoIndent{...}`

Supprime le retrait de première ligne du contenu enveloppé.

**Usage typique :** corriger l'indentation d'un paragraphe qui suit immédiatement un titre, une citation en retrait, un élément flottant ou un environnement spécial, lorsque LaTeX réintroduit un retrait non souhaité.

**Syntaxe :**

```latex
\lateiNoIndent{\teiP{Texte du paragraphe sans retrait.}}
```

**Comportement PDF :** équivalent à `{\parindent=0pt \teiP{...}}` — le groupe local annule le retrait pour le contenu enveloppé.

**Comportement lors de la restauration XML :** l'enveloppe `\lateiNoIndent{...}` est ignorée ; les nœuds intérieurs (`\teiP`, `\teiHi`, etc.) sont parsés et exportés normalement vers le XML.

**Ce que cette commande ne fait pas :**
- Elle ne modifie pas le XML source.
- Elle ne supprime pas les retraits globalement (ce serait une modification de style, pas une correction locale).
- Elle ne doit pas être utilisée pour reformater un paragraphe entier ; elle est réservée aux corrections ponctuelles.

## Implémentation

### `purh_site/resources/latei_macros.tex`

```latex
\NewDocumentCommand{\lateiNoIndent}{+m}{{\parindent=0pt #1}}
```

Le groupe interne `{{ }}` confine la modification de `\parindent` au seul contenu passé en argument.

### `purh_site/reversible/latex_reader.py`

Les commandes `\latei...` sont déclarées dans `LAYOUT_WRAPPER_MACROS`. Le parseur les reconnaît dans `_controlled_macro_at_pos()` et les traite via `_parse_layout_wrapper()` : le contenu du groupe `{...}` est parsé récursivement et les nœuds résultants sont insérés directement dans la liste parente, sans créer d'élément TEI intermédiaire.

## Ajouter une nouvelle commande `\latei...`

1. Déclarer la macro dans `purh_site/resources/latei_macros.tex` avec `\NewDocumentCommand`.
2. Ajouter le nom (sans `\`) à `LAYOUT_WRAPPER_MACROS` dans `purh_site/reversible/latex_reader.py`.
3. Documenter la commande dans ce fichier.
4. Ajouter des tests dans `tests/test_latei_layout_commands.py`.
