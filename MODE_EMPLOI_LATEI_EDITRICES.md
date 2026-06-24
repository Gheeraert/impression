# Mode d'emploi LaTEI — Corrections de mise en page pour les éditrices et éditeurs

## Ce que ce document explique

Après avoir exporté un fichier `.latei.tex` depuis un XML Métopes, le PDF généré peut présenter des problèmes d'apparence : retraits indésirables, espacement, coupures de page. Ces corrections s'effectuent directement dans le fichier `.latei.tex`, en utilisant les commandes `\latei...` prévues à cet effet.

## La règle fondamentale

Il y a deux types de commandes dans un fichier `.latei.tex` :

- Les commandes **`\tei...`** encodent le contenu éditorial du livre : textes, titres, images, notes. Elles sont exportées vers le XML. **Ne les modifiez pas** pour corriger la mise en page.
- Les commandes **`\latei...`** corrigent uniquement l'apparence du PDF. Elles n'affectent pas le XML. C'est sur elles que porte ce guide.

**Ce qu'il ne faut pas faire :** ne jamais écrire directement du LaTeX brut comme `\noindent`, `\vspace`, `\newpage` ou `\clearpage` dans la zone éditoriale. Ces commandes seront rejetées.

## Les corrections ne modifient pas le XML

Si vous corrigez le fichier `.latei.tex` avec des commandes `\latei...` puis demandez une restauration XML, le XML obtenu sera identique à celui que vous auriez obtenu sans ces corrections. Elles servent **uniquement au PDF**.

---

## Supprimer ou ajouter un alinéa

### `\lateiNoIndent{...}` — supprimer le retrait

LaTeX ajoute parfois un retrait de première ligne après un titre, une citation ou un élément spécial. Pour supprimer ce retrait sur un paragraphe précis :

```latex
\lateiNoIndent{\teiP{Ce paragraphe n'a pas de retrait.}}
```

### `\lateiIndent{...}` — forcer le retrait

À l'inverse, LaTeX supprime parfois l'alinéa (par exemple après une équation). Pour le forcer :

```latex
\lateiIndent{\teiP{Ce paragraphe a un retrait.}}
```

---

## Ajouter un blanc vertical

### Entre deux éléments : `\lateiVSpace{taille}`

Pour insérer un blanc vertical entre deux éléments :

```latex
\teiP{Premier paragraphe.}
\lateiVSpace{medium}
\teiP{Second paragraphe avec un peu plus d'espace au-dessus.}
```

### Avant un élément : `\lateiSpaceBefore{taille}{...}`

```latex
\lateiSpaceBefore{small}{\teiP{Ce paragraphe a un petit blanc avant lui.}}
```

### Après un élément : `\lateiSpaceAfter{taille}{...}`

```latex
\lateiSpaceAfter{large}{\teiP{Ce paragraphe a un grand blanc après lui.}}
```

**Tailles disponibles :**

| Valeur | Effet approximatif |
|---|---|
| `small` | un demi-interligne |
| `medium` | un interligne |
| `large` | deux interlignes |

---

## Forcer un saut de page

### `\lateiPageBreak` — saut de page entre deux éléments

```latex
\teiP{Dernier paragraphe de la page.}
\lateiPageBreak
\teiP{Premier paragraphe de la page suivante.}
```

### `\lateiPageBreakBefore{...}` — saut de page avant un élément

```latex
\lateiPageBreakBefore{\teiP{Ce paragraphe commence une nouvelle page.}}
```

### `\lateiPageBreakAfter{...}` — saut de page après un élément

```latex
\lateiPageBreakAfter{\teiP{Ce paragraphe termine la page.}}
```

### `\lateiClearPage` et variantes

`\lateiClearPage` fait de même mais vide aussi les figures en attente (flottants). Utilisez-le en fin de chapitre ou de section pour s'assurer que toutes les images ont été placées avant de tourner la page.

```latex
\lateiClearPage
\lateiClearPageBefore{\teiP{...}}
\lateiClearPageAfter{\teiP{...}}
```

---

## Éviter une coupure de page indésirable

### `\lateiKeepWithNext{...}` — éviter la coupure après

Pour qu'un élément ne soit pas séparé de ce qui le suit :

```latex
\lateiKeepWithNext{\teiHead{Titre de section}}
```

### `\lateiKeepTogether{...}` — maintenir un bloc sur une même page

Pour qu'un ensemble d'éléments reste sur la même page (une courte liste, un titre suivi de son premier paragraphe, etc.) :

```latex
\lateiKeepTogether{%
  \teiHead{Titre}
  \teiP{Premier paragraphe sous le titre.}
}
```

### `\lateiNoPageBreakBefore{...}` — interdire la coupure avant

```latex
\lateiNoPageBreakBefore{\teiP{Ne pas couper juste avant ce paragraphe.}}
```

### `\lateiNoPageBreakAfter{...}` — interdire la coupure après

```latex
\lateiNoPageBreakAfter{\teiP{Ne pas couper juste après ce paragraphe.}}
```

---

## Workflow recommandé

1. Exporter le paquet LaTEI depuis le XML (menu **LaTEI / Exporter un paquet LaTEI depuis un XML**).
2. Compiler le fichier `.latei.tex` pour obtenir un premier PDF.
3. Repérer les problèmes de mise en page dans le PDF.
4. Apporter les corrections avec les commandes `\latei...` dans le fichier `.latei.tex`.
5. Recompiler pour vérifier le résultat.
6. Si une correction du contenu est aussi nécessaire, l'apporter dans le XML d'origine (les corrections `\latei...` ne remplacent pas une correction éditoriale dans le XML).

## Restaurer le XML après correction

Si vous avez apporté des corrections `\latei...` dans le fichier `.latei.tex` et souhaitez restaurer le XML, utilisez le menu **LaTEI / Restaurer un XML Métopes depuis un monofichier LaTEI**. Les commandes `\latei...` seront ignorées lors de la restauration.
