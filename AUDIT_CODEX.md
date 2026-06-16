# Audit Codex - Impressions

Date : 2026-06-16  
Perimetre : audit du code et des sorties potentielles, sans correction du projet.

## Resume executif

Le projet est sain dans son intention et relativement lisible : il repose sur une chaine simple `TEI -> arbre lxml normalise -> structure de site -> fragments HTML XSLT -> pages statiques + CSS/JS`. Cette sobriete est un bon choix pour une petite equipe editoriale universitaire. Les responsabilites principales sont deja separees en modules comprehensibles : chargement TEI, normalisation, structure, generation HTML, interface graphique, serveur local.

Le niveau actuel est celui d'un prototype avance de generateur web statique, pas encore celui d'un outil robuste de production pour des TEI Metopes riches. Les risques principaux ne viennent pas d'une architecture trop compliquee, mais d'une couverture TEI trop etroite : plusieurs elements savants usuels sont aplatis par le comportement par defaut XSLT, parfois avec perte de sens ou HTML invalide. Les tables, renvois, abreviations/expansions, bibliographies imbriquees, citations inline, index et nombreux paratextes ne sont pas encore traites comme objets editoriaux.

Les tests existants passent (`5 passed`) avec `C:\Python314\python.exe -m pytest -q`, mais ils couvrent seulement le parcours heureux : generation multipage, images, couverture/lightbox, auteurs et quelques aspects CSS. L'environnement virtuel local ne contient pas `pytest`. Les sorties existantes dans `output/` ne contiennent pas de site exploitable au moment de l'audit, seulement un dossier `assets/`. Le depot ne contient pas d'exemple XML Metopes complet hors XML synthetiques dans les tests.

Priorite recommandee : fiabiliser sans refonte. Il faut d'abord verrouiller la chaine actuelle par des fixtures TEI representatives et des tests de sortie HTML, puis elargir progressivement le XSLT et la normalisation typographique. Pour LaTeX/PDF, il serait premature de generer directement depuis le HTML actuel ; il faut conserver le TEI normalise comme source pivot et factoriser les decisions editoriales avant d'ajouter un export LaTeX.

## Architecture actuelle

Arborescence utile :

- `main.py` : point d'entree graphique, appelle `purh_site.gui.run_gui()`.
- `purh_site/config.py` : dataclass `BuildConfig`.
- `purh_site/tei_loader.py` : parsing XML et resolution manuelle des `xi:include`.
- `purh_site/normalizer.py` : attribution d'identifiants, numerotation des notes, fusion de certains `hi`.
- `purh_site/site_structure.py` : extraction des metadonnees de volume, pages, navigation.
- `purh_site/site_builder.py` : orchestration du build, copie des assets, assemblage HTML, metadonnees Zotero/DC, page d'accueil, pages de contenu.
- `purh_site/resources/tei_to_html.xsl` : transformation TEI fragmentaire vers HTML.
- `purh_site/resources/site.css` : habillage web.
- `purh_site/resources/app.js` : dates de consultation, notes marginales, lightbox.
- `purh_site/gui.py` : interface Tkinter.
- `purh_site/local_server.py` : serveur local de previsualisation.
- `convertisseur_tiff.py` : utilitaire separe, non integre a la chaine principale observee.
- `tests/test_smoke.py` : tests de fumee.

La separation generale est bonne : le coeur du build n'est pas melange a Tkinter, le XSLT porte le rendu TEI fin, et les ressources web sont statiques. `site_builder.py` est cependant devenu le module central le plus charge : il assemble les pages, gere les assets, lit la quatrieme, produit les citations, les metadonnees, le HTML de layout et les appels XSLT.

## Chaine de transformation observee

1. `SiteBuilder.build_from_master()` lit le XML maitre via `TeiLoader.load_master()`.
2. `TeiLoader` parse avec `lxml.etree.XMLParser(remove_blank_text=False, resolve_entities=False)`.
3. Les `xi:include` sont resolus manuellement : les enfants de `/TEI/text` du fichier inclus sont copies dans le parent, et quelques metadonnees du fichier inclus sont transferees en attributs `data-page-*`.
4. `TeiNormalizer.normalize()` ajoute des `xml:id`, fusionne certains `hi`, numerote toutes les notes, repere les figures sans media.
5. Le TEI normalise est toujours ecrit dans `book.normalized.xml`.
6. `SiteStructureBuilder.build()` extrait les metadonnees de volume, determine les groupes qui deviennent des pages et construit la navigation.
7. `SiteBuilder` copie `site.css`, `app.js`, puis le dossier d'assets utilisateur.
8. `SiteBuilder` genere `index.html`, puis une page par `PageDef`.
9. Chaque fragment de page est transforme par `resources/tei_to_html.xsl`.
10. `normalize_inline_html_spacing()` applique ensuite quelques corrections regex sur le HTML final.
11. `app.js` ajoute cote client les dates de consultation, les notes marginales et la lightbox.

Il n'y a pas, a ce stade, de sortie LaTeX/PDF generee par le code principal. Le PDF est seulement detecte dans `assets/PDF` et propose au telechargement.

## Modules responsables par domaine

| Domaine | Module actuel | Commentaire |
| --- | --- | --- |
| Parsing XML | `tei_loader.py` | Simple et lisible, sans validation schema. |
| Inclusions | `tei_loader.py:_resolve_xincludes` | Resolution maison, partielle, sans `xpointer`, `parse`, `fallback`, `xml:base`. |
| Modele interne | `site_structure.py` | Dataclasses `SiteMeta`, `PageDef`, `NavItem`, pas de modele editorial complet. |
| Generation HTML | `site_builder.py` + `tei_to_html.xsl` | Layout en Python, contenu TEI en XSLT. |
| Table des matieres | `site_structure.py`, rendu dans `site_builder.py:_render_nav_list` | Clair et stable pour `group`. |
| Metadonnees | `site_structure.py:_extract_site_meta`, `site_builder.py:_render_zotero_meta` | Zotero/DC presents, Open Graph annonce mais absent. |
| Notes | `normalizer.py:_number_notes`, `site_builder.py:_renumber_fragment_notes`, `tei_to_html.xsl` | Fonctionnel mais fragile pour notes riches et numerotation globale/page. |
| Figures | `normalizer.py:_resolve_figure_media`, `tei_to_html.xsl`, `app.js` | Bonne base lightbox, alt et chemins a renforcer. |
| Tableaux | Aucun traitement dedie | Risque majeur : contenu aplati. |
| Citations | `tei_to_html.xsl` pour `cit`, `quote`, `epigraph` | `quote` toujours bloc, `q` non gere. |
| Bibliographie | `tei_to_html.xsl:listBibl/bibl` | Minimal, peut produire HTML invalide dans les notes. |
| Typographie locale | `normalizer.py:_merge_adjacent_hi`, `site_builder.normalize_inline_html_spacing`, XSLT `hi` | Utile mais insuffisant pour typographie francaise. |
| LaTeX/PDF | Aucun module dedie | Strategie a definir plus tard. |

## Forces du projet

- Architecture sobre, comprehensible et adaptee a un outil editorial leger.
- Dependances minimales : `lxml>=5.0` seulement pour l'application.
- Sortie statique autonome : HTML, CSS, JS, assets locaux.
- Separation partielle entre structure de site, transformation TEI et presentation web.
- Dataclasses claires pour `BuildConfig`, `SiteMeta`, `PageDef`, `NavItem`.
- Bonne intuition editoriale : pages multipages, sommaire, page d'accueil, citabilite, notes, lightbox, XML normalise exporte.
- Tests de fumee presents et verts.
- Gestion prudente de `resolve_entities=False` au parsing XML.
- L'interface graphique garde le coeur de generation reutilisable.

## Fragilites generales

- Le XSLT est trop minimal pour un TEI Metopes scientifique riche.
- L'absence de fixtures Metopes reelles empeche de mesurer la couverture editoriale.
- Plusieurs champs de configuration exposes par la GUI ne sont pas effectivement utilises.
- Le module `site_builder.py` concentre beaucoup de logique HTML, metadata, assets et citation.
- La normalisation typographique est post-HTML et regex, donc difficile a etendre proprement.
- Les erreurs de parsing/build remontent surtout comme exceptions globales dans la GUI, avec peu de diagnostics editoriaux exploitables.
- Il n'y a pas de validation TEI, ni de rapport de couverture des elements TEI non traites.

## Problemes importants

### P0 - Le mode GUI multi-fichiers est casse

- Fichier : `purh_site/gui.py:301-305`, `purh_site/site_builder.py:130`.
- Zone : appel `self.builder.build_from_many(..., config_overrides=config)`.
- Symptome : `build_from_many()` n'accepte pas l'argument `config_overrides`; le build de plusieurs XML independants echouera par `TypeError`.
- Cause probable : evolution de l'API non reportee dans la GUI.
- Gravite : bloquante pour le workflow multi-fichiers depuis l'interface.
- Correction recommandee : soit supprimer l'argument, soit ajouter un parametre `config_overrides` explicite a `build_from_many()` et documenter les champs repris.
- Tests a ajouter : test unitaire ou integration GUI-light appelant `SiteBuilder.build_from_many()` avec les memes arguments que la GUI.

### P0 - Plusieurs elements TEI riches sont aplatis ou degradent le HTML

- Fichier : `purh_site/resources/tei_to_html.xsl:57-229`.
- Zone : templates XSLT manquants, comportement par defaut XSLT.
- Symptome observe par build cible : `table/row/cell` devient `AB`, `ptr` devient vide, `choice/abbr/expan` devient `M.Monsieur`, `bibl` dans une note devient un `<li>` imbrique dans le `<li>` de note.
- Cause probable : XSLT volontairement minimal ; templates generiques absents pour objets editoriaux importants.
- Gravite : bloquante pour une production universitaire structurée.
- Correction recommandee : ajouter par priorite des templates pour `table/row/cell`, `ptr`, `choice`, `abbr`, `expan`, `q`, `title`, `foreign`, `name/persName/placeName`, `label`, `list` typee, et distinguer `bibl` selon contexte.
- Tests a ajouter : fixtures TEI pour chaque famille, assertions sur HTML semantique et validite des imbrications.

### P1 - Les champs de configuration sont partiellement ignores

- Fichier : `purh_site/config.py:13-18`, `purh_site/site_builder.py:151-161`, `purh_site/site_structure.py:199-248`.
- Zone : `BuildConfig.back_cover_path`, `collection_title`, `collection_number`, `collection_issn`, `write_normalized_tei`, `site_title_fallback`.
- Symptome : la GUI expose une quatrieme externe et des champs collection, mais le build lit seulement le XML puis `assets/quatrieme`; les valeurs de repli GUI ne sont pas injectees dans `SiteMeta`. `write_normalized_tei` est ignore car `book.normalized.xml` est toujours ecrit. `site_title_fallback` est ignore au profit de `"Livre PURH"` dans `SiteStructureBuilder`.
- Cause probable : configuration ajoutee avant raccordement complet au coeur.
- Gravite : forte pour la confiance utilisateur.
- Correction recommandee : appliquer explicitement les replis de `BuildConfig` apres extraction TEI, et respecter `write_normalized_tei`.
- Tests a ajouter : absence de `seriesStmt` dans le TEI + champs GUI/config renseignes ; `back_cover_path` externe ; `write_normalized_tei=False`.

### P1 - Resolution XInclude maison trop partielle

- Fichier : `purh_site/tei_loader.py:68-129`.
- Zone : `_resolve_xincludes()`, `_select_included_nodes()`.
- Symptome : seuls les `href` simples vers fichiers existants sont integres ; les includes manquants restent silencieusement dans l'arbre apres avertissement initial ; `xpointer`, `parse`, `fallback`, `xml:base` et certains cas de chemins ne sont pas pris en charge.
- Cause probable : resolution pragmatique pour le cas courant Metopes.
- Gravite : forte si les corpus Commons Publishing utilisent des variantes XInclude.
- Correction recommandee : soit utiliser le support XInclude de lxml avec controles, soit formaliser la resolution maison et produire des erreurs bloquantes lorsque le contenu requis manque.
- Tests a ajouter : include imbrique, include manquant, include avec sous-dossier, include avec `xpointer` si attendu dans les corpus.

### P1 - Les notes fonctionnent pour les cas simples mais restent fragiles

- Fichier : `purh_site/normalizer.py:142-145`, `purh_site/site_builder.py:315-317`, `purh_site/resources/tei_to_html.xsl:21-31` et `:160-162`.
- Zone : numerotation globale puis renumerotation par fragment.
- Symptome : `book.normalized.xml` porte une numerotation globale, tandis que chaque page est renumerotee a partir de 1 ; les notes riches peuvent produire du HTML invalide si elles contiennent des elements comme `bibl`.
- Cause probable : bonne volonte de numerotation par page, mais logique partagee entre normalisation et rendu sans modele de note.
- Gravite : moyenne a forte pour coherence editoriale et citations.
- Correction recommandee : decider explicitement numerotation globale ou par page, conserver l'original si present, et rendre les notes via templates contextuels.
- Tests a ajouter : plusieurs chapitres avec notes, notes contenant paragraphes, bibliographie, liens, italique, citation.

### P1 - Les citations inline et longues ne sont pas distinguees

- Fichier : `purh_site/resources/tei_to_html.xsl:61-67`.
- Zone : `cit`, `quote`; absence de `q`.
- Symptome : `quote` devient toujours `blockquote`, meme en contexte inline ; `q` n'est pas traite et perd les guillemets typographiques.
- Cause probable : pas encore de politique editoriale pour citations courtes/longues.
- Gravite : forte pour qualite savante et typographie francaise.
- Correction recommandee : traiter `q` en inline avec guillemets francais et espaces fines, traiter `quote` selon contexte ou `@rend`, garder `blockquote` pour citations longues.
- Tests a ajouter : `q` dans paragraphe, `quote` dans `p`, `cit/quote/bibl`, citations imbriquees.

### P1 - Absence de traitement des tableaux

- Fichier : `purh_site/resources/tei_to_html.xsl`.
- Zone : aucun template `tei:table`, `tei:row`, `tei:cell`.
- Symptome : perte complete de structure tabulaire.
- Cause probable : famille TEI non encore implementee.
- Gravite : forte pour ouvrages universitaires.
- Correction recommandee : produire `table`, `caption`, `thead/tbody` si possible, `tr`, `th/td`, et CSS accessible.
- Tests a ajouter : table simple, table avec entete, cellule multiline, note dans cellule.

### P2 - Metadonnees Zotero/DC presentes, Open Graph absent

- Fichier : `purh_site/site_builder.py:758-828`, `README.md`.
- Zone : `_render_zotero_meta()`.
- Symptome : le README annonce Open Graph + Dublin Core ; le code produit des meta `citation_*` et `DC.*`, mais pas `og:*`.
- Cause probable : README en avance sur le code.
- Gravite : moyenne.
- Correction recommandee : soit ajuster README, soit ajouter `og:title`, `og:type`, `og:url`, `og:image`, `og:description` lorsque les donnees existent.
- Tests a ajouter : page index avec couverture et site_url ; page chapitre avec metadonnees attendues.

### P2 - Accessibilite perfectible

- Fichier : `site_builder.py`, `tei_to_html.xsl`, `app.js`.
- Zone : navigation, figures, lightbox, notes.
- Symptome : pas de lien d'evitement, pas de `aria-current` sur l'entree courante, alt des figures tire seulement de `head`, pas de fermeture lightbox par piege de focus complet, notes marginales dupliquees visuellement mais pas explicitement masquees aux lecteurs d'ecran.
- Cause probable : base UI fonctionnelle avant audit accessibilite.
- Gravite : moyenne.
- Correction recommandee : ajouter les attributs ARIA necessaires, utiliser `figDesc` pour alt, tester au clavier.
- Tests a ajouter : snapshots HTML et tests DOM sur `aria-current`, alt, role dialog, navigation clavier si test navigateur.

### P2 - Typographie francaise non centralisee

- Fichier : `site_builder.py:38-109`, `resources/tei_to_html.xsl:184-228`, `site.css`.
- Zone : `normalize_inline_html_spacing()` et templates `hi`.
- Symptome : seules quelques corrections d'espacement autour des balises inline existent. Les espaces fines/insecables, guillemets francais, ponctuation double, apostrophes typographiques, siecles en petites capitales, ordinaux, abreviations savantes ne sont pas normalises.
- Cause probable : logique typographique encore embryonnaire.
- Gravite : moyenne a forte selon ambition editoriale.
- Correction recommandee : introduire une passe typographique textuelle controlee sur les noeuds texte, avant rendu ou dans un renderer partage, avec opt-out pour `code/pre`, URLs, attributs.
- Tests a ajouter : corpus de phrases francaises typiques et assertions exactes sur espaces `&nbsp;` / `&#8239;`, guillemets, appels de notes.

### P2 - CSS contient une faute syntaxique mineure

- Fichier : `purh_site/resources/site.css:969`.
- Zone : `.site-footer-logo`.
- Symptome : `transition: opacity 0.2s ease, transform 0.2s ease;10`.
- Cause probable : caractere residuel.
- Gravite : faible, mais signal de manque de lint CSS.
- Correction recommandee : supprimer `10`.
- Tests a ajouter : lint CSS simple ou verification de ressources statiques.

### P2 - Dependances de test absentes

- Fichier : `requirements.txt`, environnement `.venv`.
- Zone : dependances dev.
- Symptome : `.venv\Scripts\python.exe -m pytest -q` echoue avec `No module named pytest`, alors que `C:\Python314\python.exe -m pytest -q` passe.
- Cause probable : `requirements.txt` ne distingue pas runtime et dev.
- Gravite : moyenne pour maintenabilite.
- Correction recommandee : ajouter un `requirements-dev.txt` ou documenter l'installation de pytest.
- Tests a ajouter : non applicable, mais CI local/documentation.

## Problemes non bloquants et dette technique

- `site_builder.py` depasse le role d'orchestrateur et contient beaucoup de HTML a la main.
- Les chaines HTML sont construites par concatenation ; `html.escape()` est souvent utilise, mais les fragments HTML externes `.html` de quatrieme sont injectes tels quels.
- Les chemins d'images Metopes peuvent produire `assets/images/../icono/...`. Le test l'entérine, mais l'URL reste peu nette.
- Les liens `tei:ref` sont rendus tels quels via `href="{@target}"`, sans conversion de `#xmlid` vers ancre HTML valide si les cibles changent.
- `xsl:strip-space elements="*"` peut modifier des espaces significatifs dans certains contextes litteraires ou poetiques.
- `pb` et `lb` deviennent tous deux `<br/>`, ce qui perd la distinction page break / line break.
- La bibliographie est rendue comme liste ordonnee uniforme ; pas de gestion de DOI, URL, titres, auteurs, dates, editions, ni microdonnees.
- Les index et references croisees ne sont pas traites.
- Il n'y a pas de CLI documentee pour automatiser les builds hors GUI.

## Evaluation editoriale des sorties

### Structure TEI / Metopes

La structure par `group type="book"` puis groupes de page est bien comprise. Les pages sont creees a partir de types connus (`chapter`, `article`, `introduction`, `conclusion`, etc.). En revanche, l'outil depend fortement de conventions `group` et d'attributs `data-page-*` ajoutes lors des inclusions ; il n'y a pas encore de couche de compatibilite Metopes explicitement documentee.

### HTML semantique

Points positifs : `main`, `aside`, `nav`, `figure`, `figcaption`, `blockquote`, `ol` pour bibliographie et notes.  
Risques : tableaux absents, `quote` inline mal rendu, `bibl` contextuel invalide, `pb/lb` confondus, noms propres et titres non marques, appels de notes minimaux.

### Navigation

La navigation multipage et precedent/suivant sont utiles et simples. Il manque `aria-current`, une navigation mobile plus explicite si les livres sont longs, et peut-etre une page de recherche/index plus tard.

### Notes et appels

Bon socle : appel cliquable, notes finales, notes marginales JS. Mais la numerotation doit etre decidée comme politique editoriale stable, et les contenus riches de notes doivent etre rendus proprement.

### Bibliographie

Traitement minimal. Suffisant pour une liste brute, insuffisant pour bibliographies savantes Metopes : pas de typage, pas de structure auteur/titre/date, pas de liens DOI/URL, pas de distinction bibliographie generale / note / reference citee.

### Figures, legendes, credits

Socle interessant avec lightbox et telechargement. Les credits, sources, droits, `figDesc`, alt text, plusieurs graphics/media par figure et chemins d'assets doivent etre consolides.

### Petits elements typographiques

`hi` gere italic, bold, small-caps, sup, sub, underline, strikethrough. C'est une bonne base. Il manque les variantes frequentes de `rend`, les elements semantiques TEI (`title`, `foreign`, `term`, `name`) et la typographie francaise contextuelle.

## Risques typographiques francais

Manques probables a traiter plus tard :

- espaces insecables avant `: ; ? !` et autour des guillemets francais ;
- espaces fines insecables (`U+202F`) pour ponctuation double et guillemets, selon politique retenue ;
- transformation ou preservation controlee des guillemets anglais en guillemets francais ;
- apostrophes typographiques ;
- tirets d'incise et espaces associees ;
- siecles en petites capitales (`XIXe`, `XVIIe`) ;
- ordinaux (`1er`, `2e`, `no`, `nos`) ;
- abreviations savantes (`M.`, `MM.`, `vol.`, `p.`, `fol.`, `ms.`) ;
- appels de notes avant/apres ponctuation selon regle editoriale ;
- capitales accentuees ;
- césures HTML/PDF, veuves et orphelines pour PDF ;
- coherence des memes regles entre HTML, CSS et LaTeX.

## Strategie LaTeX/PDF recommandee

Ne pas generer LaTeX depuis le HTML actuel : il est deja une projection web et perd certaines distinctions TEI. Ne pas lancer non plus une reecriture totale.

Strategie sobre :

1. Garder le TEI normalise comme source pivot.
2. Stabiliser une petite couche "edition normalisee" : ids, notes, pages, figures, bibliographie, titres, typographie textuelle.
3. Pour HTML, continuer XSLT ou renderer dedie, mais avec templates plus complets.
4. Pour PDF, preferer un export LaTeX depuis le TEI normalise ou depuis une representation intermediaire explicite.
5. Utiliser un template LaTeX maison pour l'identite editoriale : `babel`/francais, `csquotes`, `microtype`, gestion des notes, figures, tables, bibliographie.
6. Pandoc peut servir de pont exploratoire ou pour certains fragments, mais il ne doit pas devenir une boite noire si les exigences Metopes/PURH sont fines.
7. Placer les regles typographiques dans une couche partagee avant les renderers, pas dans deux sorties separees HTML et LaTeX.

Le risque principal est la duplication : si les notes, citations, figures et bibliographie sont corrigees une fois dans le XSLT HTML puis recodees differemment pour LaTeX, les divergences seront inevitables. Il faut d'abord nommer les decisions editoriales dans des tests et fonctions partagees.

## Feuille de route proposee

### Etape 1 - Audit / fiabilisation

Objectif : rendre la chaine actuelle fiable sans changer sa philosophie.

- Ajouter 3 a 5 fixtures TEI Metopes representatives : monographie, collectif, notes riches, figures/tables, bibliographie.
- Ajouter des tests HTML de non-regression sur les elements critiques.
- Corriger le bug GUI `build_from_many`.
- Raccorder les champs `BuildConfig` deja exposes.
- Ajouter un rapport de build listant les elements TEI non traites ou aplatis.
- Decider numerotation des notes : globale, par chapitre, ou preservee depuis TEI.
- Documenter les conventions Metopes attendues.
- Ajouter `requirements-dev.txt` ou documentation pytest.

### Etape 2 - Amelioration typographique HTML

Objectif : obtenir une sortie web savante et typographiquement credible.

- Completer le XSLT pour tables, citations, `q`, `choice`, `ptr/ref`, noms propres, titres, bibliographie contextuelle.
- Introduire une passe typographique francaise testee, avec politique explicite.
- Ameliorer accessibilite : `aria-current`, skip link, alt depuis `figDesc`, lightbox clavier.
- Consolider figures : credits, droits, multiples images, chemins propres.
- Ameliorer metadata : Open Graph ou correction du README, Zotero plus complet.
- Ajouter lint HTML/CSS minimal sur les sorties generees.

### Etape 3 - Amelioration LaTeX/PDF

Objectif : produire un PDF de qualite sans dupliquer la logique editoriale.

- Definir le pivot : TEI normalise enrichi ou dataclasses editoriales.
- Prototyper un export LaTeX sur 1 fixture riche.
- Creer un template LaTeX maison avec typographie francaise, notes, figures, tables.
- Comparer option directe LaTeX vs Pandoc sur la meme fixture.
- Factoriser les transformations communes : notes, citations, bibliographie, typographie.
- Ajouter tests de compilation LaTeX optionnels et snapshots PDF/texte.

## Conclusion

Impressions a une base prometteuse : le projet est petit, lisible, et son architecture sert bien l'objectif statique. Il ne faut pas le reecrire. Il faut maintenant le durcir avec des corpus reels, des tests editoriaux, et une extension progressive du XSLT/normaliseur. La priorite n'est pas la modernisation technique, mais la fidelite TEI, la robustesse des sorties et la formalisation des decisions typographiques.
