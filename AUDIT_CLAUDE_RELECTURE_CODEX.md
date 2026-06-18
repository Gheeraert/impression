# Relecture Codex du rapport Claude

## Résumé exécutif

Le rapport `AUDIT_CLAUDE_COMPLET.md` était globalement juste au moment de son écriture, mais il est maintenant partiellement dépassé par les passes récentes sur la chaîne PDF. Les corrections effectuées depuis couvrent plusieurs points que Claude classait comme bugs réels : échappement des URL LaTeX, esperluette dans `\href`, figures dans les notes, signalement des cellules fusionnées, déduplication des DOI et style bibliographique PURH.

État constaté au 18 juin 2026 :

* Points déjà corrigés : 9
* Points encore pertinents et prioritaires : 1
* Points encore pertinents mais non prioritaires : 7
* Points à discuter / ambigus : 3
* Points obsolètes depuis les dernières passes : 4
* Points déconseillés ou dangereux : 3

La suite actuelle passe :

```text
C:\Python314\python.exe -m pytest -q
158 passed, 2 skipped
```

## Tableau de synthèse

| Point Claude | État actuel | Priorité | Fichiers | Action recommandée |
| ------------ | ----------- | -------- | -------- | ------------------ |
| Liens inline PDF utilisent `_escape_text` au lieu de `_escape_url` | Déjà corrigé | P0 résolu | `purh_site/latex_renderer.py`, `tests/test_pdf_latex.py` | Ne rien faire |
| `_escape_url` n’échappe pas `&` | Déjà corrigé | P0 résolu | `purh_site/latex_renderer.py`, `tests/test_pdf_latex.py` | Ne rien faire |
| Notes `place="end"` injectées ou perdues silencieusement | Encore pertinent et prioritaire | P1 | `purh_site/tei_to_model.py`, `purh_site/semantic_model.py`, `purh_site/latex_renderer.py` | Micro-passe dédiée |
| Figures dans les notes non absolutisées | Déjà corrigé | P0 résolu | `purh_site/pdf_builder.py`, `tests/test_pdf_latex.py` | Ne rien faire |
| Tableaux avec `cols` / `rows` ignorés silencieusement | Déjà corrigé pour la traçabilité, support complet restant | P3 | `purh_site/latex_renderer.py`, `tests/test_pdf_latex.py` | Reporter le vrai colspan/rowspan |
| DOI présent en `idno` et `ref` dupliqué | Déjà corrigé | P0 résolu | `purh_site/tei_to_model.py`, `tests/test_pdf_latex.py` | Ne rien faire |
| Bibliographie structurée PDF insuffisante | Obsolète depuis 13C/13C-bis | Résolu V1 | `semantic_model.py`, `tei_to_model.py`, `latex_renderer.py` | Ne rien faire maintenant |
| Style bibliographique PDF perfectible | Déjà corrigé en 13C-bis pour la V1 | Résolu V1 | `latex_renderer.py`, `tests/test_pdf_latex.py` | Affiner seulement sur corpus réel |
| Chaîne PDF sans test LuaLaTeX | Obsolète | Résolu | `tests/test_pdf_latex_compile.py` | Ne rien faire |
| Style PURH encore générique `memoir/polyglossia` | Obsolète | Résolu | `purh_site/latex_renderer.py` | Ne rien faire |
| Divergence ordre site/PDF | Déjà couvert pour cas simples | P2 | `tests/test_pdf_structure.py`, `tei_to_model.py` | Ajouter des fixtures réelles plus tard |
| Divergence HTML/PDF sur familles TEI riches | Encore pertinent mais non prioritaire | P2 | XSLT, `tei_to_model.py`, tests HTML/PDF | Tests croisés ciblés plus tard |
| Titre `level="s"` pouvant être pris comme monographie | Encore pertinent mais non prioritaire | P3 | `purh_site/tei_to_model.py` | Micro-test puis correction limitée si corpus concerné |
| XML malformé / erreur de parsing non couvert | Encore pertinent mais non prioritaire | P3 | `purh_site/pdf_builder.py`, tests PDF | Ajouter test de rapport d’erreur |
| Refactor `_render_credit_block` / `_render_zotero_meta` | Encore pertinent mais non prioritaire | P4 | `purh_site/site_builder.py` | Reporter |
| Refactor profond `SiteBuilder` | Déconseillé ou dangereux | Aucun | `purh_site/site_builder.py` | Ne pas faire maintenant |
| Intégrer PDF dans `SiteBuilder` rapidement | Déconseillé ou dangereux | Aucun | `SiteBuilder`, `BuildConfig`, `PdfBuilder` | Continuer à séparer |
| Extraire préambule PURH en template ou `.cls` maintenant | Déconseillé ou dangereux | Aucun | `latex_renderer.py` | Reporter |
| Pandoc comme architecture principale PDF | Déconseillé ou dangereux | Aucun | Chaîne PDF | Ne pas faire |
| Dépendance TeX système | Encore pertinent mais non prioritaire | P3 | docs/tests | Documenter plus tard |
| Typage de quelques helpers internes | Encore pertinent mais non prioritaire | P4 | `pdf_builder.py`, `tei_to_model.py` | Maintenance ultérieure |

## Analyse détaillée

### 1. Échappement des liens inline PDF

* Conseil de Claude : remplacer `_escape_text` par `_escape_url` pour la cible de `\href`.
* État actuel du code : corrigé. Dans `LatexRenderer._render_inline_node`, les `Link` utilisent `target = self._escape_url(node.target)`.
* Diagnostic Codex : `Déjà corrigé`.
* Tests existants : `tests/test_pdf_latex.py::test_inline_ref_target_uses_url_escaping`.
* Risque : faible désormais ; le test couvre `_`, `&` et `#`.
* Action recommandée : aucune.

### 2. Esperluette dans `_escape_url`

* Conseil de Claude : ajouter l’échappement de `&` pour les URL LaTeX.
* État actuel du code : corrigé. `_escape_url` contient `"&": r"\&"`.
* Diagnostic Codex : `Déjà corrigé`.
* Tests existants : `tests/test_pdf_latex.py::test_inline_ref_target_uses_url_escaping` et `test_escape_url_handles_ampersand_in_bibl_identifier`.
* Risque : faible.
* Action recommandée : aucune.

### 3. Notes `place="end"`

* Conseil de Claude : ne pas laisser les notes de fin disparaître ou s’injecter silencieusement dans le flux.
* État actuel du code : encore ouvert. `_is_inline_footnote` accepte `place=""` et `place="foot"`, mais pas `place="end"`. Une note de fin passe donc par le repli récursif de `_parse_inline_element`.
* Diagnostic Codex : `Encore pertinent et prioritaire`.
* Tests existants : tests de notes simples et `place="foot"` dans `tests/test_pdf_latex.py`, mais pas de test `place="end"`.
* Risque : élevé éditorialement. Le build peut réussir avec un PDF faux.
* Action recommandée : micro-passe dédiée. Pour la V1, traiter `place="end"` comme une `Footnote` normale ou créer un marqueur explicite testé. Ne pas construire tout un système d’endnotes maintenant.

### 4. Figures dans les notes

* Conseil de Claude : absolutiser aussi les chemins d’images présents dans les notes.
* État actuel du code : corrigé. `PdfBuilder._absolutize_division_paths` parcourt maintenant `division.notes.values()` et absolutise `note.blocks`.
* Diagnostic Codex : `Déjà corrigé`.
* Tests existants : `tests/test_pdf_latex.py::test_pdf_builder_absolutizes_figure_paths_inside_footnotes`.
* Risque : faible.
* Action recommandée : aucune.

### 5. Tableaux avec cellules fusionnées

* Conseil de Claude : au minimum signaler que `cols` / `rows` ne sont pas rendus.
* État actuel du code : corrigé pour la traçabilité. `_render_table_block` ajoute un commentaire LaTeX `AVERTISSEMENT Impressions` si une cellule a `cols > 1` ou `rows > 1`.
* Diagnostic Codex : `Déjà corrigé` pour l’avertissement ; `Encore pertinent mais non prioritaire` pour le vrai rendu `\multicolumn` / `multirow`.
* Tests existants : `test_table_with_merged_cells_emits_latex_warning_comment` et `test_simple_tei_table_without_merged_cells_has_no_fusion_warning`.
* Risque : moyen seulement sur corpus avec tableaux complexes.
* Action recommandée : ne pas implémenter les fusions maintenant. Reporter à une passe tableaux complexes fondée sur corpus réel.

### 6. DOI dupliqués entre `idno` et `ref`

* Conseil de Claude : dédupliquer les identifiants bibliographiques.
* État actuel du code : corrigé. `TeiToModelParser._parse_bibl_identifiers` appelle `_deduplicate_identifiers`.
* Diagnostic Codex : `Déjà corrigé`.
* Tests existants : `tests/test_pdf_latex.py::test_biblstruct_duplicate_doi_identifiers_are_deduplicated`.
* Risque : faible.
* Action recommandée : aucune.

### 7. Bibliographies structurées PDF

* Conseil de Claude : ajouter le rendu `biblStruct` sans `biblatex`.
* État actuel du code : largement corrigé par 13C. Le modèle contient `BibliographicEntry`, `BibliographicPerson`, `BibliographicTitle`, `BibliographicIdentifier`. Le parseur et le renderer couvrent monographie, contribution, article, auteurs/directeurs multiples, DOI, URI, `biblStruct` en note.
* Diagnostic Codex : `Obsolète depuis les dernières passes`.
* Tests existants : `test_biblstruct_monograph_is_parsed_and_rendered_to_latex`, `test_biblstruct_contribution_in_edited_volume_is_rendered_to_latex`, `test_biblstruct_journal_article_is_rendered_to_latex`, `test_biblstruct_in_footnote_is_rendered_without_breaking_footnote`, `test_simple_bibl_rendering_is_not_regressed`.
* Risque : faible pour le périmètre V1, moyen sur cas TEI rares.
* Action recommandée : ne pas ajouter CSL/biblatex. Tester sur corpus réel avant d’étendre.

### 8. Style bibliographique PURH

* Conseil de Claude : améliorer la ponctuation et éviter les segments orphelins.
* État actuel du code : amélioré par 13C-bis. Les pages sont normalisées en `p.~`, les volumes en `vol.~`, les numéros en `n\textsuperscript{o}~`, les DOI/URI évitent les doubles points et doubles préfixes.
* Diagnostic Codex : `Déjà corrigé` pour le style minimal.
* Tests existants : `test_biblstruct_pages_are_normalized_in_purh_style`, `test_biblstruct_journal_volume_and_issue_use_french_latex_style`, `test_biblstruct_missing_publication_parts_do_not_leave_orphan_punctuation`, `test_biblstruct_identifiers_do_not_duplicate_periods_or_doi_prefix`.
* Risque : faible en V1.
* Action recommandée : ne plus raffiner sans exemples éditoriaux réels.

### 9. Chaîne PDF optionnelle et compilation LuaLaTeX

* Conseil de Claude : garder la compilation optionnelle et ne pas rendre TeX Live obligatoire.
* État actuel du code : respecté. Les tests normaux passent sans compilation réelle ; `tests/test_pdf_latex_compile.py` est sauté sauf `IMPRESSIONS_RUN_LATEX_INTEGRATION=1` et présence de `lualatex`.
* Diagnostic Codex : `Déjà corrigé`.
* Tests existants : suite normale `158 passed, 2 skipped`; test optionnel déjà présent.
* Risque : faible.
* Action recommandée : aucune sur le code. Documenter le prérequis TeX plus tard.

### 10. Style PURH `book + geometry + babel`

* Conseil de Claude : stabiliser le style PDF sans reprendre un template externe.
* État actuel du code : corrigé. `style="purh"` produit `\documentclass[12pt,twoside,openany]{book}`, `geometry`, `babel[french]`, `titlesec`, `titletoc`, `fancyhdr`.
* Diagnostic Codex : `Obsolète depuis les dernières passes`.
* Tests existants : tests `purh` dans `tests/test_pdf_latex.py`, dont vérification `book`, `geometry`, `babel`, en-têtes et dépendances interdites.
* Risque : faible.
* Action recommandée : ne pas créer de `.cls` maintenant.

### 11. Alignement de l’ordre PDF avec la structure du site

* Conseil de Claude : éviter que `tei_to_model.py` produise un ordre différent de `SiteStructureBuilder`.
* État actuel du code : couvert pour les cas simples par les tests de 12D.
* Diagnostic Codex : `Déjà corrigé` sur le périmètre de base ; `Encore pertinent mais non prioritaire` pour des corpus complexes.
* Tests existants : `tests/test_pdf_structure.py::test_pdf_structure_matches_site_order_for_two_simple_chapters`, `test_pdf_structure_keeps_part_before_nested_chapters`, `test_pdf_structure_order_is_identical_with_purh_style`.
* Risque : moyen sur structures Métopes réelles complexes.
* Action recommandée : ajouter plus tard une fixture réaliste contenant parties, contributions, front/back et cas de titre atypique.

### 12. Divergence HTML/PDF sur les familles TEI riches

* Conseil de Claude : surveiller les divergences entre XSLT HTML et modèle PDF.
* État actuel du code : encore pertinent. Les passes PDF ont réduit l’écart sur tableaux, figures, bibliographies, structure, mais les deux chaînes restent indépendantes.
* Diagnostic Codex : `Encore pertinent mais non prioritaire`.
* Tests existants : tests HTML par familles (`test_metopes_*`) et tests PDF séparés ; peu de tests croisés HTML/PDF sur la même fixture.
* Risque : moyen.
* Action recommandée : micro-passe future de tests croisés sur 2 ou 3 objets seulement, sans refonte.

### 13. Titre bibliographique `level="s"`

* Conseil de Claude : `_parse_bibl_title(..., "m")` peut prendre un titre de série comme titre de monographie.
* État actuel du code : encore possible. Le fallback prend le premier `<title>` non `level="j"`, donc `level="s"` peut être retenu si aucun titre monographique n’existe.
* Diagnostic Codex : `Encore pertinent mais non prioritaire`.
* Tests existants : pas de test ciblé `level="s"`.
* Risque : faible à moyen selon corpus.
* Action recommandée : micro-passe très limitée si un corpus réel expose ce cas : ignorer `level="s"` pour le titre monographique et ajouter un test.

### 14. XML malformé et rapport d’erreur `PdfBuilder`

* Conseil de Claude : tester le comportement du builder quand le parsing échoue.
* État actuel du code : `PdfBuilder.build_from_normalized_tei` capture les exceptions et écrit un log, mais le cas XML malformé n’est pas explicitement testé.
* Diagnostic Codex : `Encore pertinent mais non prioritaire`.
* Tests existants : `test_pdf_builder_reports_missing_latex_engine_without_real_tex_dependency` couvre un moteur absent, pas un XML cassé.
* Risque : faible en fonctionnement normal, utile pour robustesse diagnostic.
* Action recommandée : ajouter un test de rapport d’erreur sur XML invalide ou structure non TEI, sans changer l’architecture.

### 15. BuildConfig et GUI multi-fichiers

* Conseil de Claude dans l’audit antérieur Codex, et point connexe au rapport : les options GUI/config doivent être réellement raccordées.
* État actuel du code : corrigé. `build_from_many` accepte `config_overrides`, `write_normalized_tei` est respecté, `site_title_fallback`, collection et `back_cover_path` sont appliqués.
* Diagnostic Codex : `Déjà corrigé`.
* Tests existants : `tests/test_smoke.py::test_build_from_many_accepts_gui_style_config_overrides`, `test_write_normalized_tei_false_skips_export_and_download_link`, `test_build_config_fallbacks_are_used_when_xml_is_silent`, `test_external_back_cover_path_is_used_as_fallback`.
* Risque : faible.
* Action recommandée : aucune.

### 16. Refactor de `SiteBuilder`

* Conseil de Claude : extraire éventuellement `_render_credit_block` et `_render_zotero_meta`.
* État actuel du code : encore potentiellement utile, mais sans urgence. Les tests couvrent la sortie ; la classe est longue mais stable.
* Diagnostic Codex : `Encore pertinent mais non prioritaire`.
* Tests existants : nombreux tests smoke, Zotero, qualité site.
* Risque : refactor prématuré plus risqué que bénéfique.
* Action recommandée : reporter. Extraire seulement si une nouvelle fonctionnalité touche directement ces blocs.

### 17. Intégration PDF dans `SiteBuilder`

* Conseil de Claude : ne pas intégrer brutalement ; conserver `PdfBuilder` séparé.
* État actuel du code : respecté. `SiteBuilder` ne déclenche pas `PdfBuilder`.
* Diagnostic Codex : `Déconseillé ou dangereux` si fait maintenant sans demande explicite.
* Tests existants : tests PDF séparés, tests web séparés.
* Risque : élevé de mélanger deux chaînes qui ont volontairement des cycles de validation différents.
* Action recommandée : ne rien brancher maintenant.

### 18. Classe `.cls` ou template LaTeX externe

* Conseil de Claude : envisager plus tard.
* État actuel du code : le style PURH est généré par `LatexRenderer`, sans template externe.
* Diagnostic Codex : `Déconseillé ou dangereux` maintenant ; pertinent plus tard.
* Tests existants : tests par inspection de chaîne du préambule.
* Risque : ajouterait une dépendance de fichiers et compliquerait les tests.
* Action recommandée : reporter après validation éditoriale sur plusieurs PDF réels.

### 19. Pandoc ou PDF depuis HTML

* Conseil de Claude : ne pas faire du HTML → PDF la voie principale.
* État actuel du code : respecté. La chaîne PDF part du TEI normalisé et du modèle sémantique.
* Diagnostic Codex : `Déconseillé ou dangereux`.
* Tests existants : toute la suite PDF vérifie TEI → modèle → LaTeX.
* Risque : perte de distinctions TEI et typographie livre médiocre.
* Action recommandée : ne pas changer d’architecture.

### 20. Dépendance système TeX

* Conseil de Claude : garder optionnel et documenter.
* État actuel du code : optionnel et testé. La documentation utilisateur pourrait encore être précisée.
* Diagnostic Codex : `Encore pertinent mais non prioritaire`.
* Tests existants : skip conditionnel dans `test_pdf_latex_compile.py`, test moteur absent.
* Risque : faible pour CI, moyen pour utilisateurs.
* Action recommandée : documentation plus tard, pas de code.

### 21. Typage de helpers internes

* Conseil de Claude : typer des paramètres comme `blocks`.
* État actuel du code : certains helpers restent peu typés, par exemple `_absolutize_blocks_paths(self, blocks, ...)`.
* Diagnostic Codex : `Encore pertinent mais non prioritaire`.
* Tests existants : comportement largement couvert.
* Risque : faible.
* Action recommandée : maintenance opportuniste seulement.

## Micro-passes proposées

### 1. Notes `place="end"` PDF

Périmètre : `tei_to_model.py`, `latex_renderer.py` si nécessaire, `tests/test_pdf_latex.py`.

Objectif : garantir qu’une note `place="end"` ne s’injecte pas silencieusement dans le texte. Pour la V1, la solution la plus simple est de la rendre comme une `\footnote{...}` ordinaire, avec test dédié.

### 2. Test d’erreur XML dans `PdfBuilder`

Périmètre : `tests/test_pdf_latex.py`, éventuellement aucun code.

Objectif : créer un XML invalide ou non TEI, appeler `PdfBuilder(compile_pdf=False)`, vérifier `result.success is False`, `error_message`, `log_path` et `report_path`.

### 3. Test/correction `title level="s"` dans `biblStruct`

Périmètre : `tei_to_model.py`, `tests/test_pdf_latex.py`.

Objectif : s’assurer qu’un titre de série `level="s"` n’est pas rendu comme titre de monographie si aucun `level="m"` n’existe. Correction très locale.

### 4. Fixture croisée HTML/PDF minimale

Périmètre : tests seulement dans un premier temps.

Objectif : même TEI normalisée réaliste → vérifier que HTML et PDF conservent au moins les mêmes titres, auteurs locaux, figures et bibliographie structurée. Ne pas chercher l’identité typographique.

### 5. Documentation TeX optionnel

Périmètre : README ou documentation projet.

Objectif : expliquer que la suite normale ne requiert pas TeX Live, que `IMPRESSIONS_RUN_LATEX_INTEGRATION=1` active la compilation optionnelle, et que `lualatex` doit être présent.

## Conclusion

À faire maintenant : traiter les notes `place="end"`, car c’est le seul point du rapport Claude qui reste à la fois ouvert, éditorialement risqué et assez petit pour une micro-passe sûre.

À reporter : cas bibliographiques rares, titre de série `level="s"`, XML malformé, tests croisés HTML/PDF, documentation TeX. Ces points sont utiles mais ne bloquent pas la chaîne actuelle.

À ne pas faire : refonte de `SiteBuilder`, intégration PDF dans le build web, template externe actif, classe `.cls`, Pandoc ou génération PDF depuis HTML. Ces pistes augmenteraient la complexité alors que la chaîne actuelle est stable, testée et volontairement séparée.
