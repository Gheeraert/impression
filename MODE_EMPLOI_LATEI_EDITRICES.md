# Mode d'emploi LaTEI — Corrections de mise en page pour les éditrices

## Contexte

Après avoir exporté un fichier `.latei.tex` depuis un XML Métopes, il est possible que le PDF généré présente des problèmes d'apparence : retraits indésirables, espacement, coupures de page. Ces corrections s'effectuent **directement dans le fichier `.latei.tex`**, en utilisant les commandes `\latei...` prévues à cet effet.

Ces corrections sont **non destructives** : elles n'affectent pas la restauration du XML d'origine. Si vous corrigez le fichier `.latei.tex` puis demandez une restauration XML, le XML obtenu sera identique à celui que vous auriez obtenu sans les corrections de mise en page.

## Ce qu'il ne faut pas modifier

Ne modifiez pas les commandes `\tei...` — elles encodent la structure éditoriale du texte et sont exportées vers le XML. Toute modification d'une commande `\tei...` se retrouvera dans le XML restauré.

## Commandes de correction disponibles

### Supprimer le retrait de première ligne : `\lateiNoIndent{...}`

LaTeX ajoute parfois un retrait de première ligne après un titre, une citation ou un élément spécial. Pour supprimer ce retrait sur un paragraphe précis :

**Avant correction :**
```latex
\teiP{Ce paragraphe a un retrait indésirable après le titre.}
```

**Après correction :**
```latex
\lateiNoIndent{\teiP{Ce paragraphe n'a plus de retrait.}}
```

Il suffit d'entourer la commande concernée avec `\lateiNoIndent{...}`. La correction est purement visuelle et n'affecte pas le XML.

## Workflow recommandé

1. Exporter le paquet LaTEI depuis le XML (menu **LaTEI / Exporter un paquet LaTEI depuis un XML**).
2. Compiler le fichier `.latei.tex` pour obtenir un premier PDF.
3. Repérer les problèmes de mise en page dans le PDF.
4. Apporter les corrections avec les commandes `\latei...` dans le fichier `.latei.tex`.
5. Recompiler pour vérifier le résultat.
6. Une fois satisfaite, si une correction du XML source est aussi nécessaire, l'apporter dans le XML d'origine (les corrections `\latei...` ne remplacent pas une correction éditoriale dans le XML).

## Restaurer le XML après correction

Si vous avez apporté des corrections `\latei...` dans le fichier `.latei.tex` et souhaitez restaurer le XML, utilisez le menu **LaTEI / Restaurer un XML Métopes depuis un monofichier LaTEI**. Les commandes `\latei...` seront ignorées lors de la restauration.
