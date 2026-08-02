# Audit LaTEI PDF - Heraldique et papaute

Date de l'audit : 2026-06-20

## Source

- Fixture utilisee : `tests/fixtures/metopes/heraldique_ii.book.normalized.xml`
- Source : XML Metopes / Commons-Publishing normalise par la chaine Impressions/PURH.
- Generation stable : `PdfBuilder(..., latex_options=LatexRenderOptions(style="purh"), compile_pdf=True, latex_engine="lualatex")`.
- Generation LaTEI experimentale : `run_reversible_export_for_file(FIXTURE_PATH, output_dir)`.
- Moteur LaTeX observe : `C:\texlive\2025\bin\windows\lualatex.exe`.
- Dossier temporaire utilise pendant l'audit : `.codex_tmp/audit_latei_pdf_heraldique/`.

Fichiers generes pendant l'audit :

- PDF PURH stable : `.codex_tmp/audit_latei_pdf_heraldique/stable_purh/book.pdf`
- Log PURH stable : `.codex_tmp/audit_latei_pdf_heraldique/stable_purh/latex_build.log`
- PDF LaTEI : `.codex_tmp/audit_latei_pdf_heraldique/latei/heraldique_ii.book.normalized.latei.pdf`
- Log LaTEI : `.codex_tmp/audit_latei_pdf_heraldique/latei/heraldique_ii.book.normalized.latei_build.log`
- Corps LaTEI : `.codex_tmp/audit_latei_pdf_heraldique/latei/heraldique_ii.book.normalized.latei_body.tex`
- Driver LaTEI : `.codex_tmp/audit_latei_pdf_heraldique/latei/heraldique_ii.book.normalized.latei_main.tex`
- Macros LaTEI locales : `.codex_tmp/audit_latei_pdf_heraldique/latei/heraldique_ii.book.normalized.latei_macros.tex`

Ces fichiers sont des artefacts temporaires non versionnes.

## Resultat de compilation

### PDF stable PURH

- Compilation : succes.
- Pages : 351.
- Taille : 1 345 582 octets.
- Format : 439.37 x 651.968 pts.
- Warnings notables : images manquantes signalees par le builder stable, warnings `fancyhdr` sur `\headheight`, quelques caracteres absents dans la fonte courante, boites sous-remplies.
- Le builder stable a signale 177 warnings, principalement des images introuvables sous `tests/fixtures/icono/...`.

### PDF LaTEI experimental

- Compilation : succes.
- Diagnostics round-trip : 0.
- Pages : 350.
- Taille : 1 198 819 octets.
- Format : 439.37 x 651.968 pts.
- Le `latei_body.tex` conserve `teiHeader`, `teiDiv`, `teiHead`, `teiFigure`, `teiGraphic[url={...}]`.
- Le `latei_main.tex` inclut le corps et la copie locale des macros LaTEI.
- Warnings notables : destinations PDF dupliquees `page.1` / `page.2`, warnings `fancyhdr`, nombreux `Missing character` pour U+2009, U+2011 et ponctuellement U+2033, boites sous-remplies.

## Comparaison typographique avec le PDF stable

### Page de titre

Le PDF stable affiche une page de titre tres sobre : titre centre et mention `PURH` en bas de page.

Le PDF LaTEI reprend le titre reel et les metadonnees extraites, mais ajoute actuellement :

- `PURH - 2025`
- `ISBN imprime 979-10-240-1855-3`
- `Document LaTEI PURH experimental`

Cette page compile et exploite bien les metadonnees, mais elle n'est pas encore strictement equivalente a la page stable.

### Table des matieres

Aucune table des matieres equivalente n'a ete observee dans les premieres pages du PDF LaTEI. La chaine stable gere deja mieux la structure de livre et les pages liminaires.

### Titres `section1`, `section2`, `section3`

Le corps LaTEI contient bien des divisions Metopes reelles, par exemple `teiDiv[type={section1}]` avec `\teiHead`. Le rendu LaTEI reste toutefois trop general : les premieres structures de front matter sont enchainees sans les ruptures et niveaux typographiques du PDF stable.

### Paragraphes

Les paragraphes sont presents, lisibles et dans l'ordre documentaire. Le gris typographique et les espacements ne sont pas encore au niveau stable, notamment parce que la structure livre/front matter n'est pas encore assez interpretee.

### Notes

Les notes compilent et ne detruisent pas le contenu. Leur rendu differe cependant du PDF stable : les appels et les contenus de notes sont moins bien integres, notamment lorsque le contenu TEI de note contient lui-meme des structures paragraphiques.

### Figures et legendes

Le corps LaTEI conserve les figures et les `graphic @url`, par exemple `\teiGraphic[url={../icono/br/Ch02_Doulkaridou/fig1.jpg}]`.

Les figures ne sont pas encore traitees au niveau typographique stable. Le PDF stable signale aussi des images manquantes dans les fixtures d'iconographie, ce qui limite la comparaison visuelle. LaTEI compile sans casser sur ces ressources, mais la politique figure/image reste a durcir.

### References

Les references sont conservees et le texte visible compile. Le comportement typographique/hyperlien reste encore experimental par rapport a la chaine stable.

### Italiques, petites capitales, exposants

Les cas simples sont rendus par les macros LaTEI. Les logs montrent toutefois des caracteres absents dans la fonte courante pour certaines espaces fines, traits d'union inseparables et signes secondes. C'est un sujet de normalisation typographique LaTeX, pas une perte documentaire.

### Citations

Les citations sont conservees. Le rendu LaTEI reste plus proche d'un flux conservateur que d'une composition PURH definitive.

### Bibliographie

Les elements bibliographiques sont conserves et les macros dediees existent. La couche typographique bibliographique n'est pas encore equivalente au rendu stable, surtout pour les structures fines ou les listes bibliographiques complexes.

### Blancs et sauts de page

Ecart majeur observe : le PDF stable separe `Remerciements`, `Table des abreviations` et `Introduction` en pages/sections distinctes. Le PDF LaTEI les enchaine actuellement dans le meme flux au debut du document. Cela indique que les wrappers Metopes (`front`, `body`, `group`, `div type=...`) ne sont pas encore convertis en structure de livre PURH suffisamment precise.

### En-tetes courants et bas de page

Les deux PDF utilisent le format de page PURH et rencontrent des warnings `fancyhdr` similaires sur `\headheight`. Le PDF LaTEI affiche des en-tetes/pagination fonctionnels, mais la logique de matiere frontale et de demarrage de sections n'est pas encore alignee sur le stable.

## Problemes classes

### A. Bloquant

Aucun probleme bloquant observe dans cette passe :

- le PDF LaTEI compile ;
- le PDF stable compile ;
- le `teiHeader` n'est pas imprime comme contenu brut ;
- le round-trip documentaire reste a zero diagnostic ;
- aucune structure documentaire n'est detruite dans l'export inspecte.

### B. Important

1. Structure de livre trop plate dans LaTEI.
   Les blocs de front matter, notamment `Remerciements`, `Table des abreviations` et `Introduction`, s'enchainent dans un flux continu au lieu de suivre la structure stable.

2. Contextualisation incomplete de `head`.
   Les `head` dans `div type=section1/section2/section3` existent, mais les contextes Metopes de niveau livre/front/back/group/titlePage ne produisent pas encore les ruptures et niveaux PURH attendus.

3. Figures conservees mais non rendues au niveau stable.
   `graphic @url` est conserve et compile, mais la strategie d'inclusion/copie/resolution des images n'est pas encore equivalente au PDF stable.

4. Notes moins robustes typographiquement.
   Les notes sont presentes, mais appels, placement et contenu structure restent inferieurs au rendu stable.

5. Bibliographie conservee mais pas encore composee comme la chaine stable.
   Les macros reversibles protegent le contenu, mais il manque une couche de rendu bibliographique PURH.

6. Caracteres Unicode typographiques.
   Les logs LaTEI signalent des caracteres absents dans Chaparral Pro, notamment U+2009, U+2011 et U+2033. Certains cas existent aussi dans le stable, mais LaTEI en expose davantage.

### C. Cosmetique

1. Page de titre LaTEI encore trop experimentale.
   Le label `Document LaTEI PURH experimental` est utile en audit, mais pas conforme a une sortie PURH finale.

2. Espacements et densite.
   Le PDF LaTEI est lisible, mais les espacements, ruptures et blancs verticaux ne suivent pas encore la maquette stable.

3. Warnings `fancyhdr`.
   Les deux chaines signalent `\headheight is too small`. Ce n'est pas propre a LaTEI, mais reste a nettoyer a terme.

4. Boites underfull/overfull.
   Les logs LaTEI contiennent de nombreuses boites sous-remplies, souvent liees a la composition encore trop brute du flux.

## Corrections proposees

Ne pas tout corriger dans une seule passe. Proposition de micro-passes ulterieures :

1. Passe 17G - Structure livre Metopes vers structure PURH.
   Interpreter explicitement `TEI/text/front/body/back/group` et les `div type=titlePage`, `section1`, `section2`, `section3`, sans changer la grammaire reversible.

2. Passe 17H - `head` contextuel Metopes complet.
   Etendre la logique de rendu de `head` aux contextes `front`, `back`, `group`, `titlePage`, `figure`, `table`, `listBibl`, avec tests sur la fixture reelle.

3. Passe 17I - Politique figures/images LaTEI.
   Resoudre les chemins `graphic @url`, copier ou localiser les images quand elles existent, conserver un placeholder propre quand elles manquent.

4. Passe 17J - Notes LaTEI.
   Stabiliser le rendu des notes avec contenu structure, appels de note, paragraphes internes et prevention des notes imbriquees.

5. Passe 17K - Bibliographie PURH depuis macros reversibles.
   Ajouter une couche typographique pour `teiBibl`, `teiBiblScope`, `teiAuthor`, `teiEditor`, `teiIdno`, sans appauvrir le corps LaTEI.

6. Passe 17L - Caracteres typographiques et fontes.
   Traiter les espaces fines, traits d'union inseparables et signes speciaux en macros LaTeX robustes ou via une fonte compatible.

## Conclusion

La fixture Metopes reelle valide desormais plus que le seul round-trip documentaire : le paquet LaTEI complet produit un PDF compilable avec zero diagnostic documentaire. Le resultat reste cependant experimental typographiquement.

Le principal ecart avec le PDF stable n'est pas une perte de contenu, mais une interpretation encore trop faible de la structure de livre Metopes. C'est encourageant : le pivot reversible tient, et le travail restant se concentre sur la couche de composition PURH.

Aucune modification HTML n'a ete faite. La chaine PDF stable n'a pas ete remplacee.
