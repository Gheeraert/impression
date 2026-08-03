# Rapport — Fidélité PDF PURH, micropasses 3-4 + limitation des tests LaTeX-PDF

## État des commits

Branche dédiée `purh-fidelite-profil-et-tests`, poussée sur origin :
1. `4337fdf` — Profil de mise en page PURH versionné (micropasse 3).
2. `73c30c9` — Empêche la suite de tests de recompiler des livres entiers (limitation des tests, demande utilisateur explicite).
3. `0484daf` — Pagination arabe continue (micropasse 4) + bug de scope TeX corrigé au passage.
4. `ccb9f91` — Ouvertures de contribution : titre/sous-titre/auteur, sans "Chapitre N" (micropasse 5).
5. `d96f0a6` — Titres courants recto/verso distincts, sans italique forcée (micropasse 6).
6. `579b39b` — Titraille : Josefin Sans Thin, capitales, tailles observées (micropasse 7).
7. `f7b69f0` — Citations et poésie : environnement verse pour <lg>/<l>, retraits observés (micropasse 8).
8. `9c811a1` — Frontières inline et appels de note : verrouillage par tests (micropasse 9, aucun correctif applicatif nécessaire).

**Les 9 micropasses de la consigne d'origine sont maintenant toutes traitées.** Voir la section "Livraison" en
fin de document pour le rapport de synthèse en 9 points.

## Addendum — micropasse 9 (frontières inline et appels de note)

Investigation du défaut décrit ("LouisXIV", "FrançoisIer", espaces parasites avant appel de note) : **non
reproduit** avec le code actuel. `tei_reader.py` traite déjà texte et tail comme des données pures (aucun strip
ni normalisation), préservées telles quelles aux frontières hi/sup/note par le writer. Vérifié avec des motifs
réels extraits du livre Héraldique ("Jules XIII", "début XVIIe siècle", "...Merito</hi><note>...") : round-trip
sans diagnostic, rendu PDF conforme dans tous les cas listés par le référentiel. Vraisemblablement déjà corrigé
par des travaux antérieurs à cette session. Les fixtures de non-régression explicitement demandées par le
référentiel ont été ajoutées (`tests/test_latei_inline_boundaries.py`) sans correctif de code applicatif.

---

# Livraison — synthèse des 9 micropasses (rapport final demandé par la consigne d'origine)

## 1. Fichiers modifiés

- `purh_site/purh_layout_profiles.py` (nouveau) — profils de mise en page versionnés.
- `purh_site/latei_preamble.py` — profil police/marges, polices Josefin Sans (normale + Thin), titraille
  (part/section), citations, en-têtes recto/verso, nettoyage de code mort.
- `purh_site/resources/latei_macros.tex` — pagination continue, ouvertures de contribution, titres courants
  recto/verso, macros titraille de contribution, `\teiLg`/`\teiL` (poésie).
- `purh_site/latei_driver.py` — sélection de profil pour `book.tex`.
- `purh_site/reversible/latex_writer.py` et `latex_reader.py` — vocabulaire sémantique `lg`/`l`.
- `pyproject.toml` — marqueur de test `full_book`.
- 15 fichiers de tests modifiés ou créés (voir commits individuels pour le détail).

## 2. Causes effectivement confirmées

Toutes les causes diagnostiquées par le référentiel v0.5 ont été confirmées par lecture directe du code avant
correction, sauf une (voir point 9) :
- Profil de composition codé en dur (12pt, marges symétriques 23/23mm, notes 9,5/10,5pt) — confirmé.
- `\frontmatter`/`\mainmatter` appelaient `\pagenumbering` de façon non idempotente à cause d'un bug de scope
  TeX (drapeaux `\newif` non globaux) — confirmé et plus grave que diagnostiqué initialement (redémarrage à
  chaque chapitre, pas seulement au passage liminaire/corps).
- `<div type="titlePage">` entièrement supprimé, `\chapter{title}` générique avec libellé "Chapitre N" —
  confirmé.
- `\chaptermark` passait la même valeur des deux côtés de `\markboth` — confirmé.
- Titraille en Chaparral/Josefin Bold ~24,8pt bas de casse au lieu de Josefin Sans Thin 16pt/12pt capitales —
  confirmé.
- Citations 11/14pt retraits symétriques 1,5em au lieu de 9/11pt retrait gauche seul 10mm — confirmé.
- Poésie sans support `<lg>/<l>` dédié, passant par un bloc de citation avec `\linebreak` — confirmé.
- Frontières inline (espaces autour de hi/sup/note) — **non confirmé** : le défaut ne s'est pas reproduit avec
  le code actuel dans cette session (voir point 9).

## 3. Corrections réalisées

Neuf micropasses, chacune committée séparément et testée avant de passer à la suivante :
1. *(déjà faite avant cette session, commit `0fa2d32`)* compilation isolée, contrôle des fontes.
2. *(déjà faite avant cette session)* variantes typographiques.
3. Profil de mise en page versionné (`purh_155x230_production_2025` / `_current_2026`), profil/marges/corps/
   notes appliqués depuis une configuration structurée plutôt que des valeurs éparses.
4. Pagination arabe continue, sans redémarrage — et correction d'un bug de scope TeX plus profond que prévu.
5. Ouvertures de contribution : titre/sous-titre/auteur/traducteur depuis `titlePage`, plus de libellé
   "Chapitre N".
6. Titres courants recto (contribution) / verso (livre ou partie) distincts, romains (plus d'italique forcée).
7. Titraille : Josefin Sans Thin, capitales, tailles observées pour partie/article/section.
8. Citations recalibrées ; poésie routée vers un environnement `verse` dédié via un nouveau vocabulaire
   sémantique `<lg>/<l>`.
9. Frontières inline : aucun correctif nécessaire, comportement déjà correct — verrouillé par des tests.

## 4. Tests ajoutés et résultat

9 nouveaux fichiers de tests (profils, préambule, pagination, ouvertures de contribution, titres courants,
titraille, citations/poésie, frontières inline) plus mises à jour de tests existants dont les assertions
reflétaient l'ancien comportement défectueux. Suite complète par défaut (`pytest tests/`, livres entiers
exclus) : **658 passed, 1 skipped, 0 failed**, ~9-12 minutes. Les tests `full_book` (compilation du vrai livre
Héraldique complet) ont été exécutés ponctuellement à chaque micropasse touchant les macros/préambule partagés
(dernière vérification : micropasse 6, 8/8 passed, ~20 minutes) mais pas systématiquement à chaque micropasse
suivante, sur demande explicite de l'utilisateur de ne plus les jouer par défaut dans cette session.

## 5. Mesures du PDF obtenu et profil sélectionné

Profil sélectionné par défaut : `purh_155x230_production_2025` (155×230mm, corps 11/13,5pt, notes 8,5/10,2pt,
marges 30/19/20/30mm). Vérifié par compilation réelle à plusieurs micropasses : `pdfinfo` confirme le format
exact 439,37×651,97pt = 155×230mm. Mesures fines du corps/interligne/marges dans le PDF final non ré-instrumentées
au-delà de la génération LaTeX elle-même (pas d'outil d'inspection de boîtes de texte disponible en session).

## 6. Fontes incorporées et utilisées

Chaparral Pro **absente** de cette machine de développement (`fc-list` ne la trouve pas) — la chaîne retombe
sur TeX Gyre Pagella via le mécanisme de repli déjà existant (`\IfFontExistsTF`), non lié à cette série de
passes. Josefin Sans (normale) et Josefin Sans Thin (romain + italique) confirmées disponibles et utilisées
pour la titraille et les titres courants. La question des variantes Chaparral manquantes en production (italique
notamment) relève de la micropasse 2, déjà traitée avant cette session — non ré-auditée ici.

## 7. Écarts restant avec le PDF imprimeur

- Positions verticales exactes en mm des titres (ex. 44,7mm pour le titre de partie) — non calibrées.
- Sous-niveaux subsection/subsubsection — aucune donnée référentiel, non traités.
- `\titleformat{\chapter}` du chemin `<div type="chapter">` (distinct de l'ouverture de contribution) —
  inchangé, toujours Chaparral/Bold.
- Cas transitoire poésie encodée en `<cit>/<lb>` (sans vrais `<lg>/<l>`) — non traité, référentiel déconseille
  toute heuristique devinée ici.
- Politique d'ouverture à droite (recto) pour parties/articles — mentionnée comme défaut "Majeur" par le
  référentiel mais absente de la liste des 9 micropasses de la consigne d'origine ; jamais traitée.
- Mode d'export imprimeur (fond perdu, TrimBox/MediaBox distincts) — hors périmètre de toute micropasse listée.
- Images (0 actuellement dans le PDF LaTEI vs images réelles attendues) — jamais traité dans cette série.
- Chaparral Pro absente de cet environnement de développement (voir point 6) — impact sur le rendu réel en
  production à vérifier séparément, indépendant du code.

## 8. Points laissés volontairement hors périmètre

Voir chaque addendum de micropasse ci-dessus pour le détail par passe (profils/marges hors grille de base,
manifeste de production, styling exact de l'auteur/traducteur au-delà des données référentiel disponibles,
etc.).

## 9. Prochaine micropasse recommandée

Les 9 micropasses de la consigne d'origine sont closes. Pistes pour une suite éventuelle, par ordre de valeur
probable :
1. Images : 0 actuellement dans le PDF LaTEI malgré des figures réelles attendues (référentiel §5.2, défaut
   "Bloquant") — jamais traité dans cette série de 9 passes, potentiellement le défaut le plus visible restant.
2. Politique d'ouverture à droite (recto) pour parties/articles.
3. Titraille du chemin `<div type="chapter">` restant (Chaparral/Bold), pour cohérence avec la micropasse 7.
4. Vérification/calibrage fin des positions verticales en mm, si un outil d'inspection de boîtes PDF est
   disponible dans une session future.
5. Cas transitoire poésie sans `<lg>/<l>` — nécessite arbitrage éditorial avant toute heuristique.

## Addendum — micropasse 8 (citations et poésie)

`<lg>/<l>` n'avaient aucune prise en charge dédiée (writer ni reader) : la poésie passait par le bloc de
citation avec des `<lb/>`/`\linebreak` manuels dans un paragraphe justifié, produisant des blancs excessifs
(référentiel §"Poésie"). Ajoutés au vocabulaire sémantique contrôlé : `<lg>` → `\teiLg` (environnement `verse`,
aligné à gauche, jamais justifié), `<l>` → `\teiL` (une ligne, `\\`). Citations : 11/14pt retraits 1,5em des
deux côtés → 9/11pt, retrait gauche seul 10mm, ~4mm avant/après (valeurs observées §5.3).

**Hors périmètre** : le cas transitoire (poésie encodée via `<cit>/<lb>` faute de vrais `<lg>/<l>`) — le
référentiel met en garde explicitement contre toute confusion citation/poésie devinée par heuristique, et
aucun exemple réel de ce cas n'a été trouvé dans les fixtures disponibles pour le vérifier correctement.

Vérifié par compilation réelle (prose + `<lg>/<l>` + `<cit>` dans le même article) : chaque vers sur sa propre
ligne PDF, citation et poésie visuellement distinctes, round-trip TEI sans diagnostic (0 diagnostics).

## Addendum — micropasse 7 (titraille)

Titres de partie/contribution en Chaparral/Josefin Bold ~24,8pt bas de casse → Josefin Sans Thin 16pt
capitales centré (référentiel §2.5/§5.3). Titre de section : Bold ~17,2pt → Thin 12pt capitales. Nouvelle
famille `\PURHTitreFont` (Josefin Sans Thin, confirmée disponible via `fc-list` sur cette machine — Chaparral
Pro en revanche absente, la chaîne retombe sur TeX Gyre Pagella comme prévu par le mécanisme de repli existant,
non lié à cette passe). Capitales obtenues via l'idiome titlesec `before-code = \MakeUppercase`, vérifié
empiriquement avant application. Auteur de contribution : corps courant gras centré (style `txt_auteur`), pas
de petites capitales comme avant.

**Hors périmètre** : positions verticales exactes en mm (référentiel donne p. ex. 44,7mm pour le titre de
partie — non calibrées, pas de vérification visuelle fiable disponible) ; sous-niveaux subsection/subsubsection
(aucune valeur référentiel) ; le `\titleformat{\chapter}` historique (chemin `<div type="chapter">` distinct de
l'ouverture de contribution corrigée en micropasse 5, laissé inchangé pour ne pas casser sa couverture de
tests existante).

Vérifié par compilation réelle (partie + article + section) : les trois niveaux de titre s'affichent en
capitales, la ligne d'auteur reste en casse normale, les titres courants (en-têtes, chemin de rendu distinct)
restent en casse normale eux aussi.

Consigne de session en cours : ne pas jouer les tests `full_book` (compilation du vrai livre Héraldique) sauf
demande explicite — seule la batterie par défaut (`pytest tests/`, qui les exclut déjà via `addopts` dans
`pyproject.toml`) est utilisée jusqu'à nouvel ordre.

## Addendum — micropasse 6 (titres courants recto/verso)

`\chaptermark` passait la même valeur des deux côtés de `\markboth`, donc `\fancyhead[LO,RE]` affichait le même
titre en verso comme en recto, en italique forcée (référentiel §"Titres courants"). Deux titres sont
maintenant suivis séparément : `\g_latei_verso_running_title_tl` (verso — titre du livre par défaut, remplacé
par le titre de la partie en cours) et `\g_latei_current_running_title_tl` (recto — titre court de la
contribution). `\PURHHeaderFont` n'impose plus l'italique (romain, cible référentiel — le calibrage Josefin
Sans exact reste micropasse 7). Nettoyage au passage : `\fancyhead[RE]`/`[LO]` et le `\renewcommand{\chaptermark}`
du préambule étaient du code mort (silencieusement écrasés par `latei_macros.tex`, chargé après) — supprimés.

Vérifié par compilation réelle (livre synthétique une partie + un article) : verso = "Premiere Partie" sur
toutes ses pages, jamais le titre de l'article ; recto = titre de l'article, jamais celui de la partie.

## Addendum — micropasse 5 (ouvertures de contribution et métadonnées)

`<div type="titlePage">` (title-main/title-sub/author-aut/editor-trl — schéma confirmé sur le vrai livre
Héraldique) était entièrement supprimé par `teiDiv`, tandis que le groupe parent imprimait un `\chapter{title}`
générique avec libellé "Chapitre N" automatique. `teiDiv` rend maintenant ce contenu sous un contexte de tête
`titlePage` dédié ; `\lateiRenderParagraph` route `title-main`/`title-sub`/`author-aut`/`editor-trl` vers des
macros de mise en forme dédiées (`\lateiContributionTitle` et consorts — styles provisoires, le calibrage
Josefin Sans exact relève de la micropasse titraille, n°7). La rupture de page des groupes
front/chapitre/back ne prend plus de titre en argument : elle ne fait plus que le saut de page, l'entrée de
TDM et le titre courant, pour ne jamais dupliquer ce que titlePage affiche déjà visuellement.

**Affiliations** : aucun exemple réel avec ce rôle trouvé dans les fixtures disponibles (seulement
title-main/title-sub/author-aut/editor-trl observés) — laissé hors périmètre plutôt que deviné sur un schéma
non confirmé.

Vérifié par compilation réelle : échantillon synthétique (titre/sous-titre/auteur/traducteur) — aucun
"Chapitre" dans le texte rendu, TDM correcte — et le vrai livre Héraldique complet (`pytest -m full_book`,
8 passed, ~20 min).

## Addendum — micropasse 4 (pagination arabe continue)

`\lateiEnsureFrontMatter`/`\lateiEnsureMainMatter`/`\lateiEnsureBackMatter` remplacent les appels
`\frontmatter`/`\mainmatter`/`\backmatter` bruts : mêmes effets structurants (cleardoublepage, chapitres
numérotés/non numérotés via `\@mainmatterfalse`/`true`) mais `\pagenumbering` n'est plus appelé qu'une seule
fois pour tout le document, jamais en romain — conforme à la pagination arabe continue exigée par le
référentiel (§5.5/§5.6, P0).

**Bug réel découvert en vérifiant le correctif** (pas seulement hypothétique — reproduit et corrigé) : les
drapeaux `\newif` posés par `\xxxtrue` sans `\global` sont locaux au groupe TeX de la commande en cours
(argument `+b` de l'environnement `teiElement`, branches `IfSubStr`...) — ils étaient donc annulés à la
fermeture de ce groupe. Le garde-fou censé n'autoriser qu'un seul déclenchement se réarmait silencieusement à
chaque chapitre, donc `\cleardoublepage` + la remise à zéro du compteur de page se rejouaient à CHAQUE
chapitre, pas une seule fois pour le livre entier. Corrigé en passant tous ces drapeaux par `\global`.

Vérifié par compilation réelle : livre synthétique à 3 groupes (introduction + 2 chapitres) avec lecture directe
du `.toc` (les pages d'ouverture de chapitre PURH n'affichent aucun folio visible, donc le scraping visuel du
PDF ne peut pas servir de vérification ici) — pages 1 → 3 → 4, sans redémarrage. Et sur le vrai livre
Héraldique complet (`pytest -m full_book`) : 8 passed en ~19 minutes.



## Addendum — la suite de tests ne recompile plus de livres entiers

Suite à une demande explicite de l'utilisateur en cours de session : la suite de tests compilait jusqu'ici un
livre réel entier (`tests/fixtures/metopes/heraldique_ii.book.normalized.xml`, "Héraldique et papauté") à
chaque exécution, dans 9 fichiers de tests différents, chacun via son propre fixture de module — c'est très
probablement la cause, ou l'une des causes, du blocage de 3h de la session précédente.

Changements :
- `run_reversible_export_for_file(..., compile_pdf=...)` : le paramètre existait déjà (comportement inchangé
  par défaut, `True`, pour ne pas casser les appelants de production — `gui.py`, le CLI). Dans les 9 fichiers de
  tests concernés, chaque fixture qui n'a pas besoin du PDF passe maintenant explicitement `compile_pdf=False`.
- Les tests dont le seul but est de vérifier que le livre réel compile intégralement (7 tests, répartis dans
  6 fichiers) sont maintenant marqués `@pytest.mark.full_book` et utilisent une fixture dédiée
  `compile_pdf=True`, séparée de la fixture rapide partagée par les autres tests du même fichier.
- `pyproject.toml` : marqueur `full_book` déclaré, `addopts = "-m 'not full_book'"` — `pytest` seul les exclut
  désormais ; `pytest -m full_book` les exécute explicitement pour les tester séparément, comme demandé.
- Nouveau fichier `tests/test_commons_publishing_sample_pdf.py` : compile
  `tests/fixtures/commons-publishing/fichier_test.xml` (l'échantillon complet fourni par Commons-Publishing,
  jusqu'ici inutilisé par aucun test) — c'est désormais LE test canonique de la chaîne LaTeX-PDF, toujours
  exécuté par défaut. Futurs cas problématiques : à ajouter à ce fichier XML plutôt qu'en tant que nouveau
  livre complet, par cohérence avec la demande de l'utilisateur.
- 2 assertions `\documentclass[12pt,...]` oubliées lors de la micropasse 3 (dans des tests utilisant le livre
  réel) corrigées en `11pt`.

Résultat : suite complète (`pytest tests/`) verte, **634 passed, 1 skipped, 8 deselected, en 8 minutes** (contre
un temps non borné/probablement plusieurs heures avant ce correctif) ; aucune compilation de livre entier dans
la batterie par défaut. `pytest -m full_book` reste disponible pour tester séparément les livres réels.



**Statut : micropasse 3 terminée et testée. Micropasses 4 à 9 non commencées.**
Ce document reste un point de sauvegarde de contexte entre sessions (voir historique ci-dessous), mis à jour
après exécution de la micropasse 3. Rien n'est commité pour l'instant — en attente de décision de l'utilisateur
sur le découpage en branche(s).

## Historique de reprise

Session précédente interrompue après ~3h sans activité visible. Reconstruction faite en lecture seule à partir
du système de fichiers (voir git log, timestamps des fixtures) : diagnostic entièrement fait, aucun code touché.
L'utilisateur a confirmé que le point d'arrêt était la micropasse 3 (« taille des polices et des marges ») et a
demandé de relire le référentiel avant de reprendre. Le référentiel v0.5 (`Referentiel_mise_en_page_PURH_audit_v0.5.docx`,
plus détaillé que le v0.4) a été lu intégralement (extraction texte, 770 lignes) avant toute modification.

## 1. Fichiers modifiés

- `purh_site/purh_layout_profiles.py` — **nouveau**. Dataclass gelée `PurhLayoutProfile` + deux profils
  versionnés (`PURH_155X230_CURRENT_2026`, `PURH_155X230_PRODUCTION_2025`) + `get_layout_profile(name)`.
- `purh_site/latei_preamble.py` — `PurhPreambleData` gagne un champ `profile` (défaut : profil de production
  2025). `render_purh_latex_preamble` utilise ce profil pour la classe de document, la géométrie (marges), le
  `\normalsize` explicite et le corps des notes, au lieu de valeurs codées en dur.
- `purh_site/latei_driver.py` — `build_latei_driver` et `build_latei_monofile` gagnent un paramètre
  `layout_profile_name` (défaut : profil de production 2025), pour que `book.tex` sélectionne le profil au lieu
  de le recevoir implicitement.
- `tests/test_latei_preamble_independent.py` — assertion `12pt` → `11pt` (le changement attendu) + deux
  nouveaux tests (profil par défaut, profil explicite).
- `tests/test_purh_layout_profiles.py` — **nouveau**. Tests dédiés au module de profils.

## 2. Causes confirmées

Toutes confirmées directement par lecture du code avant modification (`purh_site/latei_preamble.py`, version
d'avant ce commit) et par le référentiel v0.5 (§5.5 « Attribution des écarts ») :

- Classe `book` en 12 pt au lieu de 11 pt : codé en dur dans `\documentclass`.
- `\normalsize` hérité de la table de tailles du `\documentclass`, jamais redéfini explicitement — pas de garantie
  d'un pas de 13,5 pt exact (mesuré ≈14,45 pt côté PDF imprimeur comparé, référentiel §5.3).
- Notes à 9,5/10,5 pt au lieu de 8,5/10,2 pt : codé en dur dans `\footnotelayout`.
- Marges intérieure/extérieure symétriques à 23/23 mm, ne correspondant ni au profil 2026 (25/23 mm) ni au
  profil de production 2025 observé (~20/30 mm) : codées en dur dans `\usepackage[...]{geometry}`.
- Aucun profil structuré versionné n'existait ; toutes les valeurs de composition vivaient dans une seule
  f-string du préambule, contrairement à l'architecture demandée (référentiel §5.7 : « déplacer toutes les
  décisions de composition dans un paquet de profil versionné »).

## 3. Corrections réalisées

- Deux profils de mise en page distincts, gelés, versionnés et testés, reprenant les valeurs mesurées dans le
  référentiel v0.5 :
  - `purh_155x230_current_2026` (§2.1, §2.4, §2.6) : marges 30/19/25/23 mm (haut/bas/intérieure/extérieure),
    corps 11/13,5 pt, notes 8,5/10,2 pt.
  - `purh_155x230_production_2025` (§5.4) : marges 30/19/20/30 mm, même grille corps/notes.
  - Le référentiel interdit explicitement de moyenner les deux (§5.1, §5.4) : ils restent deux objets distincts
    dans le registre, jamais fusionnés.
- Le profil de production 2025 est le défaut, car la mission en cours vise à faire converger le PDF généré vers
  le PDF imprimeur réel (référentiel §5.4), pas vers la maquette 2026 nominale.
- `\documentclass`, la géométrie (marges), `\normalsize` (redéfini explicitement en `\fontsize{11pt}{13.5pt}`
  plutôt que de dépendre de la table de tailles standard) et `\footnotelayout` lisent maintenant le profil
  sélectionné au lieu de valeurs codées en dur.
- `book.tex` peut désormais sélectionner un profil par son nom (`layout_profile_name`) au lieu de le recevoir
  implicitement — nom inconnu = `KeyError` explicite listant les profils valides, pas de repli silencieux.

## 4. Tests ajoutés et résultat

- `tests/test_purh_layout_profiles.py` (9 tests, tous verts) : grille corps/notes identique entre profils,
  marges de chaque profil conformes au référentiel, non-fusion des deux profils, largeur d'empagement dérivée
  correcte (107 mm / 105 mm), résolution par nom, erreur explicite sur nom inconnu, immutabilité.
- `tests/test_latei_preamble_independent.py` : assertion `documentclass` mise à jour à 11 pt ; deux tests
  ajoutés vérifiant que le préambule rendu contient bien les marges/corps/notes du profil par défaut et qu'un
  profil explicite change effectivement la sortie.
- Résultat : **17 passed** sur ces deux fichiers (2 échecs préexistants, sans rapport avec ce changement — un
  bug d'ordre de collecte de tests qui suppose `purh_site.latei_preamble` déjà importé ; reproduit à l'identique
  sur `HEAD` avant toute modification, non traité ici, hors périmètre de cette micropasse).
- Vérification de bout en bout hors suite de tests : compilation LuaLaTeX réelle d'un mini-livre via
  `run_reversible_export_for_file`, succès, `pdfinfo -box` confirme `MediaBox = 439,37 × 651,97 pt`, soit
  exactement 155 × 230 mm.
- **Non fait** : suite complète (`pytest tests/`) non exécutée jusqu'au bout — elle compile désormais des livres
  réels entiers (`beautes/`, `dissimuler/`, déposés par la session précédente) et dépasse largement les bornes
  de temps raisonnables en une seule commande ; c'est très probablement une cause, ou la cause, du blocage de
  3h de la session précédente. À investiguer séparément (marquage `@pytest.mark.slow` ou équivalent recommandé).

## 5. Mesures du PDF obtenu et profil sélectionné

- Format : 439,37 × 651,97 pt = 155 × 230 mm exact (mesuré via `pdfinfo -box` sur une compilation réelle).
- Profil sélectionné : `purh_155x230_production_2025` (défaut), non encore enregistré dans un manifeste de
  production (voir « hors périmètre »).
- Corps/interligne et marges non re-mesurés en pixels/points dans le PDF final (pas d'outil d'inspection de
  boîtes de texte disponible dans cette session) — la garantie vient de la génération du LaTeX lui-même
  (`\fontsize{11pt}{13.5pt}`, `geometry[inner=20mm,outer=30mm,...]`), pas d'une mesure a posteriori du rendu.

## 6. Fontes incorporées et utilisées

Non re-vérifié dans cette micropasse (relève de la micropasse 2, déjà traitée par un commit antérieur,
`0fa2d32`). La compilation de test embarque `ChaparralPro-Regular`, `ChaparralPro-Semibold` et
`JosefinSans-Bold` (`pdffonts` sur le mini-livre de vérification) — cohérent avec un corps courant en Chaparral
et des titres en Josefin Sans, mais ce mini-livre ne contient pas d'italique donc ne teste pas la question des
variantes manquantes documentée par le référentiel §2.4/§5.5.

## 7. Écarts restant avec le PDF imprimeur

Tout ce qui n'est pas le profil police/marges reste ouvert (référentiel §5.3, tableau complet) :
- Titraille : Josefin Sans Thin attendu, Chaparral Pro / Josefin Bold actuellement rendu (micropasse 7).
- Citations 9/11 pt attendues, 11/14 pt actuellement (micropasse 8, environnement `quote` non touché ici).
- Pagination, ouvertures de contribution, titres courants recto/verso, poésie, frontières inline, images,
  liminaires, TDM parasite — micropasses 4 à 9, non commencées.
- Mode export imprimeur (fond perdu, TrimBox/MediaBox distincts) — référentiel §5.6 P3, hors périmètre de toute
  micropasse listée par la consigne actuelle.

## 8. Points laissés volontairement hors périmètre

- Enregistrement du profil sélectionné dans le manifeste de production (référentiel §5.8) — relève de
  `site_asset_manifest.py`, non touché ici pour rester sur une seule famille de correctifs.
- Environnement `quote` (citations 11/14 pt) — appartient explicitement à la micropasse 8, pas 3.
- Le bug d'ordre de collecte des deux tests d'indépendance d'import — préexistant, sans rapport.
- La lenteur de la suite complète de tests — signalée mais pas corrigée (pourrait nécessiter un marqueur
  `slow`/`compile` pour permettre de l'exclure par défaut sans dépendre de correspondances de noms fragiles).
- `book.tex` / `book_v2.tex` dans les fixtures : différence entre les deux non élucidée avec certitude (très
  probablement due au XML source utilisé pour chaque génération, pas au code) — non nécessaire pour cette
  micropasse, n'a pas été creusé davantage.

## 9. Prochaine micropasse recommandée

Micropasse 4 (référentiel et consigne originale s'accordent) : pagination arabe continue. Le monofichier
`book.tex` de *Dissimuler* appelle `\frontmatter` puis `\mainmatter` une seule fois chacun — imposant des
chiffres romains aux liminaires puis un redémarrage à 1, sans jamais réinitialiser par contribution. Avant de
toucher à la machine d'état, comparer explicitement : compilation monofichier / compilation de fragments /
assemblage final (la consigne originale insiste sur ce point : ne pas modifier « à l'aveugle »).
