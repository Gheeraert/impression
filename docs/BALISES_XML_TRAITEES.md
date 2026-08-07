# Balises XML TEI traitées par Impression

Ce document recense les balises XML TEI (Métopes / Commons-Publishing) que
l'application **Impression** (paquet `purh_site`) reconnaît explicitement,
avec la fonctionnalité associée et le type de traitement (site **HTML**,
**PDF LaTEI**, ou les deux). Il complète, sans les dupliquer, les documents
plus détaillés déjà présents dans le dépôt :

- `purh_site/reversible/TEI_COVERAGE.md` — couverture élément par élément de
  la chaîne réversible LaTEI (source de vérité pour la chaîne PDF).
- `METOPES_COMMONS_LATEI_CONTRACT.md` — contrat de métadonnées Commons-Publishing/Métopes.
- `AUDIT_ARCHITECTURE_CHAINES_XML_HTML_LATEI.md` — architecture des deux chaînes.

Deux chaînes de traitement coexistent, à partir du même XML TEI source :

- **Chaîne HTML** : `TeiLoader` → `TeiNormalizer` → `SiteStructureBuilder` →
  XSLT `purh_site/resources/tei_to_html.xsl` → `SiteBuilder` (site statique
  multi-pages).
- **Chaîne PDF (LaTEI)** : `reversible_integration.run_reversible_export_for_file`
  → `purh_site/reversible/` (lecteur/écrivain TEI ↔ LaTeX contrôlé) →
  `latei_driver.py` → compilation LuaLaTeX (`*.latei_mono.pdf`).

  Notes :
  - La colonne **Traitement** indique HTML, PDF, ou HTML + PDF.
  - Pour PDF, seule la chaîne LaTEI est active (la chaîne "PDF stable" décrite
    dans certains audits — `semantic_model.py`, `tei_to_model.py`,
    `latex_renderer.py`, `pdf_builder.py` — a depuis été retirée du dépôt ;
    seule la chaîne LaTEI produit du PDF aujourd'hui).

## 1. Métadonnées (`teiHeader`)

Lues par `purh_site/latei_metadata.py` (métadonnées du driver PDF) et
`purh_site/site_structure.py` / `purh_site/site_zotero.py` (métadonnées du
site et de l'export Zotero/COinS).

| Balise / XPath | Fonctionnalité | Traitement |
| --- | --- | --- |
| `teiHeader` | Conservé intégralement dans le corps réversible (`teiElement[name=teiHeader]`) | PDF (conservation round-trip) |
| `fileDesc/titleStmt/title[@type='main']` | Titre principal du livre | HTML (`<title>`, en-tête de page) + PDF (`\PURHBookTitle`, page de titre) |
| `fileDesc/titleStmt/title[@type='sub']` | Sous-titre | HTML + PDF (`\PURHBookSubtitle`) |
| `fileDesc/titleStmt/title[@type='collection']` | Titre de collection (page d'accueil) | HTML |
| `fileDesc/titleStmt/author` (hors `@role='pbd'`) | Auteur(s) | HTML (liste auteurs, JSON-LD) + PDF |
| `fileDesc/titleStmt/author[@role='pbd']` | Directeur(s) de publication | HTML + PDF |
| `fileDesc/titleStmt/editor` | Éditeur(s) scientifique(s) | HTML + PDF (`teiEditor`) |
| `fileDesc/publicationStmt/publisher` | Éditeur commercial | PDF (`\PURHPublisher`) |
| `fileDesc/publicationStmt/pubPlace` | Lieu de publication | PDF (extrait, non imprimé actuellement) |
| `fileDesc/publicationStmt/date[@type='publishing']` (ou `date` générique) | Année/date de publication | HTML (métadonnées Zotero) + PDF (`\PURHYear`) |
| `fileDesc/publicationStmt/ab[@type='book']//idno[@type='ISBN'/'ISBN-13']` | ISBN papier | HTML (Zotero) + PDF (page de titre, repli ISBN) |
| `fileDesc/publicationStmt/ab[@type='digital_download'][@subtype='PDF']//idno` | ISBN / DOI du PDF | PDF (`\PURHISBN`, `\PURHDOI`) |
| `fileDesc/publicationStmt/ab[@type='digital_download'][@subtype='EPUB']//idno` | ISBN de l'ePub | Conservation round-trip uniquement |
| `fileDesc/publicationStmt/ab[@type='digital_online']//ref[@type='site']` | URL du site de diffusion | HTML |
| `fileDesc/publicationStmt//idno[@type='DOI']`, `ref[@type='DOI']` | DOI | HTML + PDF (`\PURHDOI`) |
| `fileDesc/seriesStmt/title[@level='s']` | Titre de collection (préambule) | PDF |
| `fileDesc/seriesStmt/biblScope[@unit='volume'/'number'/'issue']` | Numéro de collection | PDF |
| `fileDesc/seriesStmt//idno[@type='ISSN']` | ISSN de collection | HTML (Zotero) + PDF |
| `fileDesc/publicationStmt/ab[@type='book']//idno[@type='ISSN']` | ISSN du livre | HTML (Zotero) + PDF |
| `fileDesc/editionStmt` | Mention d'édition | Extrait par `latei_metadata.py` |
| `profileDesc/langUsage/language/@ident` | Langue du document | Extrait (non imprimé actuellement) |
| `profileDesc/abstract[@rend='resume'\|'abstract']/p` | Résumé | Extrait (non imprimé actuellement) |
| `respStmt/name` | Responsabilité (ex. numérisation) | Extrait |
| `titleStmt//persName`, `titleStmt//name` | Décomposition nom/prénom des contributeurs | HTML (affichage crédits) |
| mots-clés (non balisé identifié) | — | Non déterminé / conservé par repli générique |
| droits / licence (`availability`, `licence`) | — | Conservé par le repli générique `teiElement`, non extrait comme métadonnée |

## 2. Structure du document (`text`, `front`, `body`, `back`, `div`, `group`)

Traitées principalement par `purh_site/site_structure.py` (pagination et
navigation du site) et le gabarit XSLT (rendu HTML), ainsi que par
`purh_site/reversible/` pour la sérialisation LaTeX réversible.

| Balise | Fonctionnalité | Traitement |
| --- | --- | --- |
| `text` | Racine du contenu ; unité de recherche de titre/auteur pour la page correspondante | HTML |
| `group` (`@type='book'`, `@type='chapter'`…) | Regroupement de sous-documents (livre multi-fichiers) ; détermine la pagination (une page HTML par groupe navigable) | HTML |
| `front` | Partie liminaire (avant-propos, préface…) — classée **front-matter** | HTML (rendu de section, sans découpage éditorial spécifique du `head` de `front`) + PDF (zone réversible) |
| `body` | Corps principal du texte — classé **corps** | HTML + PDF |
| `back` | Arrière-texte (annexes, index…) — classé **back-matter** | HTML (rendu de section) + PDF (zone réversible) |
| `div` (avec `@type`: `chapter`, `part`, `section`/`section1`, `section2`, `section3`…) | Division éditoriale ; génère une `<section>` HTML avec titre `h2`/`h3`/`h4` selon la profondeur d'imbrication ; `\chapter`/`\section`/`\subsection`/`\subsubsection` en PDF selon le contexte | HTML + PDF |
| `titlePage` | Page de titre | HTML (`<section class="title-page">`) + PDF (page de titre dédiée) |
| `head` | Titre de division/figure/table/bibliographie | HTML (converti en `h2`/`h3`/`h4` ou légende, jamais rendu tel quel) + PDF (`teiHead`/`\chapter{…}` etc. selon contexte, cf. tableau contextuel ci-dessous) |

### Rendu contextuel de `head` (contrat LaTEI)

| Contexte | Sens | Rendu PDF |
| --- | --- | --- |
| `div[@type='chapter']/head` | Titre de chapitre | `\chapter{...}` |
| `div[@type='part']/head` | Titre de partie | Non déterminé, repli sobre |
| `div[@type='section'\|'section1']/head` | Section niveau 1 | `\section{...}` |
| `div[@type='section2']/head` | Section niveau 2 | `\subsection{...}` |
| `div[@type='section3']/head` | Section niveau 3 | `\subsubsection{...}` |
| `front/head`, `back/head` | Titre de division liminaire/arrière-texte | Non déterminé, repli sobre |
| `figure/head` | Légende de figure | Titre discret en gras |
| `table/head` | Titre de tableau | Titre discret en gras |
| `listBibl/head` | Titre de bibliographie | Repli générique |

## 3. Corps de texte — blocs (body / front / back)

| Balise | Fonctionnalité | Traitement |
| --- | --- | --- |
| `p` | Paragraphe | HTML (`<p>` implicite via bloc) + PDF (`teiP`) |
| `list` (`@type='ordered'`) | Liste (à puces ou numérotée) | HTML (`<ul>`/`<ol>`) + PDF (`teiList`) |
| `item` | Élément de liste | HTML (`<li>`) + PDF (`teiItem`) |
| `table` | Tableau | HTML (`<table>`) + PDF (`teiTable`, sérialisation sémantique, pas typographique) |
| `row` | Ligne de tableau | HTML (`<tr>`) + PDF (`teiRow`) |
| `cell` | Cellule de tableau | HTML (`<td>`) + PDF (`teiCell`) |
| `figure` | Figure (image/audio/vidéo + légende) | HTML (`<figure>` avec lightbox) + PDF (`teiFigure`) |
| `graphic` (`@url`) | Image de la figure | HTML (`<img>` + déclencheur de zoom) + PDF (`teiGraphic`, packaging via `latei_assets.py`) |
| `media` (`@mimeType` image/audio/vidéo) | Média alternatif (image/audio/vidéo) | HTML (`<img>`/`<audio>`/`<video>`) — non couvert par la chaîne réversible LaTEI |
| `formula` | Formule | HTML (bloc dédié) |
| `epigraph` | Épigraphe | HTML (bloc dédié) |
| `quote` | Citation longue en bloc | HTML (`<blockquote>` selon contexte) + PDF (`teiQuote`) |
| `q` | Citation courte en ligne | HTML (`<q>`) + PDF (`teiQ`) |
| `cit` | Citation structurée (quote + bibl) | HTML (bloc combiné) + PDF (`teiCit`) |
| `said` | Discours rapporté | PDF (`teiSaid`, conserve `@who`) |
| `sp`, `speaker`, `stage` | Texte théâtral (répliques, indications scéniques) | HTML |
| `lg`, `l`, `caesura` | Vers, ligne de vers, césure (poésie) | HTML |
| `note` (`@place`) | Note de bas de page / fin | HTML (appel de note + section "Notes" en fin de groupe/fragment) + PDF (`teiNote`) |
| `anchor` | Point d'ancrage technique | HTML (ancre invisible) |
| `lb` | Saut de ligne | HTML (`<br/>`) + PDF (`teiLb`, milestone vide) |
| `pb` | Saut de page | HTML (marqueur) + PDF (`teiPb`, milestone vide) |
| `choice`, `abbr`, `expan` | Abréviation / forme développée | HTML (rendu de la forme choisie) |

## 4. Texte en ligne (inline / niveau caractère)

| Balise | Fonctionnalité | Traitement |
| --- | --- | --- |
| `hi` (`@rend`) | Mise en forme typographique (italique, gras, petites capitales, exposant…) | HTML (classe CSS dérivée de `@rend`) + PDF (`teiHi`, conserve `@rend`) |
| `emph` | Emphase | HTML |
| `foreign` (`@xml:lang`) | Terme en langue étrangère | HTML (`<span lang>`) + PDF (`teiForeign`) |
| `term` | Terme technique/glossaire | HTML + PDF (`teiTerm`) |
| `name` | Nom générique | HTML + PDF (`teiName`) |
| `persName` | Nom de personne | HTML (crédits, métadonnées) + PDF (`teiPersName`) |
| `placeName` | Nom de lieu | HTML + PDF (`teiPlaceName`) |
| `orgName` | Nom d'organisation | HTML + PDF (`teiOrgName`) |
| `forename`, `surname` | Composants du nom (prénom/nom) | HTML (recomposition affichage) — repli générique en PDF |
| `date` (`@when`) | Date en ligne | HTML + PDF (`teiDate`) |
| `num` (`@type`) | Nombre | HTML + PDF (`teiNum`) |
| `label` (`@n`) | Étiquette | HTML + PDF (`teiLabel`) |
| `title` (`@level`, `@type`) | Titre d'œuvre cité | HTML (`<cite>`, ou `<span>` dans une `bibl`) + PDF (`teiTitle`) |
| `ref` (`@target`) | Lien/renvoi | HTML (`<a>` externe ou `<span>` interne) + PDF (`teiRef`) |
| `ptr` (`@target`) | Pointeur/lien direct | HTML (`<a>`) + PDF (`teiPtr`, milestone) |
| `seg` | Segment générique | PDF (repli générique `teiElement`) |

## 5. Bibliographie

| Balise | Fonctionnalité | Traitement |
| --- | --- | --- |
| `listBibl` | Liste bibliographique | HTML (liste formatée) |
| `bibl` | Notice bibliographique non structurée | HTML (rendu de la chaîne telle quelle) + PDF (`teiBibl`, sérialisation conservatrice) |
| `biblStruct` | Notice bibliographique structurée | HTML (mode `bibl-structured` : recompose auteur/titre/éditeur/date/cote) |
| `analytic`, `monogr`, `imprint` (dans `biblStruct`) | Niveaux analytique / monographique / mentions d'édition | HTML (mode `bibl-structured`) |
| `author`, `editor` (dans `biblStruct`) | Auteur/éditeur de la référence | HTML + PDF (`teiAuthor`, `teiEditor`) |
| `publisher` (dans `biblStruct`) | Éditeur de la référence | HTML + PDF (`teiPublisher`) |
| `pubPlace` (dans `biblStruct`) | Lieu de publication de la référence | HTML |
| `biblScope` | Portée bibliographique (pages, volume…) | HTML + PDF (`teiBiblScope`) |
| `idno` | Identifiant (ISBN, DOI, ISSN…) | HTML + PDF (`teiIdno`) |

## 6. Balises non spécialisées (repli générique)

Ces éléments ne disposent pas de gabarit XSLT ou de macro LaTeX dédiés :

- Côté **HTML** : tout élément TEI sans `xsl:template` explicite est
  simplement traversé (ses enfants sont rendus, sans balise conteneur
  spécifique) via le comportement par défaut de la XSLT.
- Côté **PDF (LaTEI)** : tout élément TEI inconnu (`forename`, `surname`,
  `affiliation`, `address`, `availability`, `licence`, etc.) traverse la
  chaîne réversible via l'environnement générique `teiElement`, qui préserve
  le nom, les attributs, les enfants et le contenu mixte sans interprétation
  sémantique — garantissant qu'aucune information n'est perdue au
  round-trip XML → LaTeX → XML même sans support dédié.

## 7. Attributs transversaux conservés (chaîne PDF réversible)

`xml:id`, `xml:lang`, `type`, `subtype`, `rend`, `place`, `target`, `n`,
`role`, `ref`, `key`, `when`, `from`, `to`, `notBefore`, `notAfter`,
`calendar`, `level`, `source`, `corresp`, `resp`, `who`, `cert`, `ed`,
`facs`, `rendition`, `rows`, `cols`, `unit`, ainsi que tout attribut
inconnu simple (préservé comme option LaTeX si possible).

Côté HTML, `@rendition` a un traitement dédié : il est résolu contre les
déclarations `tagsDecl/rendition[@scheme='css']` du document pour produire
un attribut `style="…"` sur l'élément concerné (`tei_to_html.xsl`, gabarit
nommé `rendition-style-attr`).

## 8. Références des modules sources

| Module | Rôle |
| --- | --- |
| `purh_site/tei_loader.py` | Chargement XML + résolution XInclude |
| `purh_site/normalizer.py` | Normalisation in-place (titres, auteurs, figures, renumérotation des notes) |
| `purh_site/site_structure.py` | Construction de la pagination/navigation depuis `group`/`div`/`text` |
| `purh_site/latei_metadata.py` | Extraction des métadonnées `teiHeader` pour le driver PDF LaTEI |
| `purh_site/resources/tei_to_html.xsl` | Transformation XSLT TEI → fragment HTML |
| `purh_site/reversible/tei_reader.py`, `tei_writer.py` | Lecture/écriture de l'arbre TEI réversible |
| `purh_site/reversible/latex_writer.py`, `latex_reader.py` | Sérialisation TEI ↔ LaTeX sémantique contrôlé (LaTEI) |
| `purh_site/reversible/TEI_COVERAGE.md` | Table de couverture exhaustive de la chaîne réversible |
