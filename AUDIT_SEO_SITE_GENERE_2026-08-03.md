# Audit SEO du site généré — 2026-08-03

**Périmètre** : le site HTML statique produit par `purh_site/site_builder.py` (+ `site_zotero.py`,
`resources/tei_to_html.xsl`, `resources/app.js`). Analyse par lecture directe du code générateur, pas d'un
site déployé — les constats ci-dessous décrivent ce que le générateur produit structurellement, pour n'importe
quel livre.

## Ce qui est déjà bien fait

- **Contenu server-side, pas de dépendance JS pour l'indexation.** `<h1>`, texte, images sont injectés
  directement dans le HTML généré (`_wrap_html`/`_render_*` dans `site_builder.py`) ; `app.js` ne sert qu'à des
  améliorations progressives (notes marginales, lightbox), jamais au rendu du contenu principal. Un robot qui
  ne exécute pas JavaScript voit exactement le même contenu qu'un navigateur.
- **Hiérarchie de titres correcte.** Un seul `<h1>` par page (titre du livre en accueil, titre de la
  contribution en page de chapitre) — pas de doublon ni d'absence.
- **Métadonnées scientifiques déjà solides** (`site_zotero.py`) : balises Highwire Press (`citation_title`,
  `citation_author`, `citation_publisher`, `citation_doi`, `citation_pdf_url`...) reconnues par Google Scholar
  et Zotero, plus un jeu Dublin Core (`DC.Title`, `DC.Creator`, `DC.Identifier`...) — bien au-delà de ce que la
  plupart des sites éditoriaux académiques proposent. Distinction correcte page de volume / page de chapitre
  (`DC.Type` = `book` vs `bookSection`, `DC.Relation` vers le volume parent).
- **Images accessibles et dimensionnées.** `alt` et `width`/`height` fournis par la XSLT
  (`render-graphic-image`/`render-media-image`) — bon pour l'accessibilité et pour éviter les décalages de
  mise en page (CLS, un facteur Core Web Vitals que Google utilise comme signal de classement).
- **URLs lisibles.** Chaque page est nommée `{numéro}-{slug-du-titre}.html` (`slugify()` dans
  `site_structure.py`) — un slug sémantique, pas un identifiant opaque.
- **Liens externes correctement attribués** (`rel="noopener"` sur les liens sortants du pied de page).

## Lacunes concrètes, par ordre d'impact probable

### 1. Aucune balise `<meta name="description">` sur les pages de chapitre
`render_zotero_meta` ne génère une `description` (+ `DC.Description`) que sur la page d'accueil, et seulement
si un résumé (`abstract_html`) existe. Les pages de chapitre n'ont **aucune** meta-description. Conséquence :
Google compose lui-même un extrait en piochant du texte de la page — résultat aléatoire dans les résultats de
recherche, alors qu'un extrait choisi (ex. les premières phrases du chapitre, ou un `<abstract>` si le TEI en
porte un au niveau contribution) serait un gain rapide et peu coûteux.

### 2. Aucune donnée structurée schema.org (JSON-LD)
Rien ne déclare `Book`/`Chapter`/`ScholarlyArticle`/`BreadcrumbList` en JSON-LD. C'est ce qui permet à Google
d'afficher des résultats enrichis (auteur, date de publication, fil d'Ariane dans les SERP). Les balises
Highwire/Dublin Core déjà en place couvrent Google Scholar mais **pas** les extraits enrichis de la recherche
web grand public — c'est un mécanisme distinct. Ajout à coût modéré : les données existent déjà dans
`SiteMeta`/`PageDef`, il s'agit surtout de les sérialiser une deuxième fois en JSON-LD.

### 3. Pas de `sitemap.xml`, pas de `robots.txt`
Aucun des deux fichiers n'est généré par le build. Sans sitemap, un moteur découvre les pages uniquement par
les liens internes (fonctionne, mais plus lentement, et sans signal de fraîcheur `lastmod`). Sans `robots.txt`,
rien n'indique explicitement où trouver le sitemap ni ne bloque le crawl de éventuels dossiers techniques
(`assets/pdf/`, caches). Les deux sont des fichiers statiques triviaux à générer une fois que `site_url` et la
liste des pages sont connues — déjà toutes deux disponibles dans `SiteMeta`/`PageDef`.

### 4. Pas de lien `rel="canonical"`
Si un même livre est un jour accessible par plusieurs chemins (aperçu, domaine de test, redéploiement avec
une URL légèrement différente), rien n'indique à Google quelle version est la référence — risque de contenu
dupliqué dilué entre plusieurs URLs. Coût de correction quasi nul (`<link rel="canonical" href="...">` à partir
de `build_public_page_url`, déjà utilisé pour les balises Zotero).

### 5. `site_url` optionnel — et son absence casse silencieusement les URLs de citation
`SiteMeta.site_url` vaut `""` par défaut si le TEI ne le renseigne pas (`site_structure.py`). Dans ce cas,
`build_public_page_url`/`build_public_asset_url` (`citation.py`) renvoient un chemin **relatif**
(`"01-introduction.html"`) au lieu d'une URL absolue. Or ce chemin relatif est injecté tel quel dans
`citation_abstract_html_url`, `DC.Identifier`, et (dans une future implémentation) `rel="canonical"` — des
champs qui n'ont de sens que sous forme d'URL absolue pour un indexeur externe. Aujourd'hui ce défaut est
silencieux : le build réussit, mais produit des métadonnées de citation inutilisables si `site_url` est oublié.
Vaudrait la peine soit de le rendre obligatoire (avertissement au minimum), soit de vérifier explicitement au
moment du build que ces champs contiennent bien une URL absolue avant publication.

### 6. Langue du document toujours codée en dur `fr`
`site_builder.py:1065` (`<html lang="fr">`) et `site_zotero.py` (`citation_language` = `"fr"` littéral, deux
occurrences) ignorent `LateiMetadata.language` (déjà extrait ailleurs dans le pipeline, ex. `fr-FR` observé sur
la fixture Héraldique réelle). Sans conséquence tant que tous les livres PURH sont en français ; deviendrait un
vrai défaut de référencement (mauvais signal de langue pour les moteurs, lecteurs d'écran mal configurés) dès
qu'un ouvrage multilingue ou en langue étrangère serait publié.

### 7. Pas d'Open Graph ni de Twitter Card
Aucune balise `og:title`/`og:description`/`og:image`/`twitter:card`. Sans effet sur le classement Google
lui-même, mais impact réel sur le partage (aperçus vides ou dégradés sur les réseaux sociaux, Slack, WhatsApp,
messageries académiques). Peu coûteux à ajouter à partir des mêmes données que les balises Zotero, plus
l'image de couverture déjà disponible (`theme_assets.cover_href` / `book-cover-image`).

### 8. Pas de `loading="lazy"` sur les images de contenu
`render-graphic-image`/`render-media-image` (XSLT) ne posent pas cet attribut. Sur un chapitre avec de
nombreuses figures, chaque image se charge dès l'ouverture de la page au lieu d'être différée jusqu'au défilement
— pénalise le temps de chargement initial (signal de performance pris en compte par Google).

## Priorisation recommandée

| Priorité | Action | Effort | Gain |
|---|---|---|---|
| 1 | Meta description par page de chapitre | Faible | Extraits de recherche maîtrisés |
| 1 | `sitemap.xml` + `robots.txt` générés au build | Faible | Découverte/indexation plus rapide et fiable |
| 2 | JSON-LD `Book`/`Chapter` (schema.org) | Moyen | Résultats enrichis Google |
| 2 | `rel="canonical"` | Faible | Anti-duplication |
| 2 | Rendre `site_url` obligatoire ou avertir si absent | Faible | Fiabilise les métadonnées déjà en place |
| 3 | `lang`/`citation_language` depuis les métadonnées réelles | Faible | Robustesse multilingue |
| 3 | Open Graph / Twitter Card | Faible | Partage social soigné |
| 3 | `loading="lazy"` sur les images de contenu | Trivial | Performance de chargement |

## Question posée : une couche DTS (Distributed Text Services) serait-elle pertinente ?

**Non pour le SEO — DTS répond à un besoin différent.** DTS (spécification W3C Community Group) est une API
REST/JSON-LD pour l'accès programmatique à des collections de textes structurés (navigation dans la
hiérarchie documentaire, récupération de fragments TEI) — pensée pour l'interopérabilité entre outils de
recherche en humanités numériques (alignement de corpus, annotation collaborative, outils d'édition
scientifique numérique tiers), pas pour le référencement dans les moteurs de recherche grand public. Un moteur
comme Google n'interroge pas une API DTS et n'en tire aucun bénéfice de classement.

**Pertinence propre, indépendante du SEO :** le projet a une vocation académique explicite (porté par la
chaire d'excellence en édition numérique, PURH) et manipule déjà des documents TEI structurés bout en bout —
c'est exactement le terrain où DTS a du sens *si* l'objectif est de permettre à d'autres outils ou
chercheurs de requêter mécaniquement le corpus (par exemple, un projet tiers qui voudrait aligner du texte,
faire de la fouille de corpus, ou construire une édition savante numérique à partir de plusieurs collections
Commons-Publishing). C'est un investissement d'architecture non négligeable : au minimum un point de
terminaison `Collection` (hiérarchie des livres/parties/contributions) et un point `Document` (le TEI ou un
fragment), avec la sérialisation JSON-LD attendue par la spec.

**Recommandation.** Les deux chantiers sont indépendants et n'entrent pas en concurrence : les corrections SEO
ci-dessus sont peu coûteuses et bénéficient à tous les livres publiés dès maintenant. DTS est un chantier
distinct, à ne considérer que s'il existe un besoin réel identifié (un partenaire ou un outil externe qui
consommerait cette API) — pas quelque chose à construire par anticipation sans consommateur connu. Si ce besoin
existe, ce serait une décision éditoriale/scientifique à discuter avec la chaire d'excellence, pas une simple
passe technique.
