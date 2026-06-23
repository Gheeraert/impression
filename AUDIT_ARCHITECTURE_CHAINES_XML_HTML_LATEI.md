# Audit architectural des chaînes XML → HTML/site et XML ↔ LaTEI/PDF

---

## Résumé exécutif

L'architecture est globalement cohérente et les deux chaînes éditoriales sont opérationnelles. La chaîne XML → HTML/site statique est mature et bien isolée. La chaîne XML → LaTEI monofichier est correctement installée : `*.latei.tex` est déclaré artefact principal dans le manifeste, dans `ReversibleExportResult.primary_latei_path`, dans `LATEI_USAGE_HELP` et dans `format_latei_export_summary`. Les fragments (`latei_body`, `latei_main`, etc.) sont clairement qualifiés de « debug » dans le GUI, le CLI et les tests. Le principal risque résiduel est que `site_builder.py` continue d'appeler `PdfBuilder` (ancienne chaîne PDF stable) pour le mode `latex_pdf`, et que `latex_renderer.py` ré-exporte `_short_running_title` et `RUNNING_TITLE_STOPWORDS` — ces deux faits empêchent d'isoler l'ancienne chaîne en `legacy/` sans casser des dépendances. La prochaine passe la plus sûre consiste à finaliser l'extraction de `_short_running_title` et `RUNNING_TITLE_STOPWORDS` vers `latei_typography.py` (déjà commencée) et à mettre à jour les deux tests de running titles qui importent encore depuis `latex_renderer`.

---

## Carte des chaînes actuelles

```
XML TEI Métopes
│
├─── CHAÎNE HTML ───────────────────────────────────────────────────────────┐
│    TeiLoader → TeiNormalizer → SiteStructureBuilder                       │
│    → XSL tei_to_html.xsl (fragment_xslt)                                 │
│    → SiteBuilder._write_index_page / _write_content_page                  │
│    → normalize_inline_html_spacing / normalize_french_typography_html      │
│    → rewrite_internal_links                                                │
│    [optionnel] → PdfBuilder (mode latex/latex_pdf)                        │
│                → LatexRenderOptions → LatexRenderer → semantic_model       │
│                → tei_to_model → LaTeX → LuaLaTeX → book.pdf               │
│    Sortie : index.html + pages/*.html + assets/                            │
│                                                                            │
├─── CHAÎNE LATEI ──────────────────────────────────────────────────────────┤
│    reversible.read_tei_element                                             │
│    → reversible.write_latex (latex_writer.py)                             │
│    → reversible.run_tei_latex_tei_roundtrip (roundtrip.py)               │
│    → latei_assets.package_latei_graphics                                  │
│    → latei_running_titles.package_latei_running_titles                    │
│    → latei_driver.build_latei_driver     (fragments : latei_main.tex)     │
│    → latei_driver.build_latei_monofile  (principal : *.latei.tex)        │
│    → latei_driver.compile_latei_pdf     (PDF debug : *.latei.pdf)        │
│    → latei_driver.compile_latei_pdf     (PDF principal : *.latei_mono.pdf)│
│    → _write_manifest (*.latei_manifest.json)                              │
│    Sortie principale : *.latei.tex + *.latei_mono.pdf + manifest          │
│    Sorties debug : *.latei_body.tex *.latei_main.tex *.latei_macros.tex  │
│                    *.latei_graphics_map.tex *.latei_running_titles_map.tex │
│                    latei_assets/ *.latei.pdf *.latei_build.log            │
│    Round-trip : *.roundtrip.xml + *.roundtrip_diagnostics.txt            │
│                                                                            │
└─── CHAÎNE RETOUR XML (LaTEI → XML) ───────────────────────────────────┐  │
     extract_latei_document_zone (*.latei.tex)                           │  │
     → read_latex_document → write_tei_element                          │  │
     Sortie : *.roundtrip.xml (ou fichier restauré nommé par GUI)       │  │
     Chemin alternatif legacy : restore_xml_from_latei_body (*.latei_body.tex) │
```

---

## Chaîne XML → HTML/site statique

### Modules impliqués

- `purh_site/site_builder.py` : orchestrateur principal (`SiteBuilder`)
- `purh_site/config.py` : `BuildConfig` (dataclass, paramètres du build)
- `purh_site/normalizer.py` : `TeiNormalizer` (normalisation XML in-place)
- `purh_site/tei_loader.py` : `TeiLoader`, `load_many` (chargement/XInclude)
- `purh_site/site_structure.py` : `SiteStructureBuilder`, `PageDef`, `NavItem`
- `purh_site/resources/tei_to_html.xsl` : transformation XSL fragment par fragment
- `purh_site/gui.py` : frontend Tkinter qui appelle `SiteBuilder.build_from_master` / `build_from_many`

### Flux de transformation XSL

La transformation XSLT est initialisée une fois dans `SiteBuilder.__init__` (ligne 255) via `etree.XSLT(etree.parse(...tei_to_html.xsl))`. Elle est appliquée fragment par fragment dans `_render_page_fragment` (ligne 691) : chaque `<group>` ou `<div>` est cloné, ses notes renumérotées, puis passé à `fragment_xslt(...)`. Il n'y a pas de transformation XSL globale sur tout le document.

### Post-traitements HTML

Après rendu XSL, chaque page subit (lignes 632–669) :
1. `normalize_inline_html_spacing` — correction des espaces autour des balises inline
2. `normalize_french_typography_html` — typographie française (guillemets, espaces insécables)
3. `rewrite_internal_links` — rattachement des ancres XML aux pages HTML multi-fichiers

### Dépendances vers PDF stable et LaTEI

`site_builder.py` importe (lignes 14–16) :
```python
from .latex_renderer import LatexRenderOptions
from .pdf_builder import PdfBuildResult, PdfBuilder
```

Ces imports sont utilisés dans `_build_pdf_site_artifacts` (ligne 371) qui instancie `PdfBuilder(latex_options=LatexRenderOptions(style="purh"), ...)` quand `config.pdf_export_mode ∈ {"latex", "latex_pdf"}`. La valeur par défaut de `pdf_export_mode` est `"none"` (ligne 19 de `config.py`), donc aucune génération PDF n'est déclenchée par défaut.

**`site_builder.py` n'appelle pas du tout la chaîne LaTEI.** Les exports LaTEI passent uniquement par `run_reversible_export_for_file` déclenché depuis le GUI (menu Outils) ou la CLI de `reversible_integration.py`.

### Statut de la chaîne HTML

La chaîne est autonome et mature. Elle ne dépend de `PdfBuilder` et `LatexRenderer` qu'en mode optionnel (`pdf_export_mode != "none"`), ce qui constitue la seule impureté résiduelle.

---

## Chaîne XML → LaTEI monofichier → PDF

### Flux complet

Le point d'entrée est `run_reversible_export_for_file` dans `reversible_integration.py`.

1. **Parsing XML** (ligne 186) : `etree.parse(source_path).getroot()`
2. **Extraction métadonnées** (ligne 227) : `extract_latei_metadata(element)` → `LateiMetadata`
3. **Roundtrip TEI → LaTeX → TEI** (ligne 228) : `run_tei_latex_tei_roundtrip(element)` qui appelle :
   - `reversible/tei_reader.py::read_tei_element` — lit le TEI et construit l'arbre de nœuds sémantiques
   - `reversible/latex_writer.py::write_latex_document` — sérialise en LaTEI sémantique contrôlé
   - `reversible/tei_writer.py::write_tei_element` — re-sérialise les nœuds en XML TEI (vérification)
4. **Écriture corps réversible** (lignes 231–232) : `latei_body_path.write_text(result.latex, ...)`
5. **Packaging images** (ligne 233) : `package_latei_graphics(element, ...)` → `LateiAssetPackage` + `*.latei_graphics_map.tex`
6. **Packaging titres courants** (ligne 239) : `package_latei_running_titles(element, ...)` → `*.latei_running_titles_map.tex`
7. **Construction driver fragmenté** (ligne 243) : `build_latei_driver(...)` → `*.latei_main.tex` + copie `latei_macros.tex`
8. **Compilation PDF debug** (ligne 251) : `compile_latei_pdf(latei_main_path, ...)` → `*.latei.pdf` + `*.latei_build.log`
9. **Construction monofichier** (ligne 259) : `build_latei_monofile(result.latex, ...)` → `*.latei.tex` (tout inline, sans `\input{}`)
10. **Compilation PDF principal** (ligne 266) : `compile_latei_pdf(latei_monofile_path, ...)` → `*.latei_mono.pdf`
11. **Écriture XML roundtrip** (ligne 272) : `roundtrip_xml_path.write_text(...)`
12. **Écriture manifeste** (ligne 287) : `_write_manifest(manifest_path, {...})` — avec sections `"primary"` et `"debug"` distinctes

### Structure du monofichier `*.latei.tex`

Le monofichier (`build_latei_monofile` dans `latei_driver.py`, ligne 104) contient dans l'ordre :
- commentaire d'en-tête avec avertissements (`_MONOFILE_FILE_HEADER`, ligne 94)
- préambule PURH inline (via `render_purh_latex_preamble`)
- macros LaTEI inline (contenu de `resources/latei_macros.tex`)
- mappings graphiques inline (contenu de `*.latei_graphics_map.tex`)
- mappings titres courants inline
- `\begin{document}` + page de titre
- **zone éditoriale réversible** : `\begin{lateiDocument}` ... `\end{lateiDocument}`
- `\cleardoublepage` + `\tableofcontents` + `\end{document}`

### Le monofichier comme artefact principal

`ReversibleExportResult.primary_latei_path` (ligne 56–58) retourne `self.latei_monofile_path`. Le manifeste JSON (ligne 291–293) place le monofichier sous la clé `"primary"` et les fragments sous la clé `"debug"`. La propriété `debug_latei_paths` (ligne 66–74) regroupe les 5 fragments.

---

## Chaîne LaTEI monofichier corrigé → XML

### Deux fonctions de restauration

**Depuis le monofichier** (`restore_xml_from_latei_monofile`, ligne 365) :
1. Lit `*.latei.tex`
2. Appelle `extract_latei_document_zone(monofile_text)` → extrait le contenu entre `\begin{lateiDocument}` et `\end{lateiDocument}`, en excluant tout le préambule, les macros et les mappings
3. Appelle `read_latex_document(zone)` → parse le LaTEI sémantique contrôlé
4. Appelle `write_tei_element(...)` → produit l'élément XML TEI
5. Écrit le fichier XML de sortie

**Depuis le corps fragmenté** (`restore_xml_from_latei_body`, ligne 344) :
1. Lit `*.latei_body.tex` directement (le corps est déjà le LaTEI sémantique pur)
2. Appelle `read_latex_document(latex)` → `write_tei_element(...)` → écrit XML

### Strictesse du parser

Le parser (`reversible/latex_reader.py`, classe `_Parser`) est **strict par conception** : toute macro inconnue lève `LatexParseError` (ligne 120 : `raise LatexParseError(f"Unknown macro or escape at offset {self.pos}.")`). Seules les macros de `MACRO_TO_ELEMENT`, `EMPTY_MACRO_TO_ELEMENT` et `ENVIRONMENT_TO_ELEMENT` sont reconnues. Ceci garantit que les corrections éditoriales restent dans le sous-ensemble sémantique contrôlé.

### Zone `lateiDocument`

La fonction `extract_latei_document_zone` (exportée dans `reversible/__init__.py` ligne 42) extrait précisément le contenu entre les balises `\begin{lateiDocument}` et `\end{lateiDocument}`. Le test `test_extract_latei_document_zone_excludes_preamble` (ligne 47 de `test_latei_monofile_restore.py`) vérifie explicitement que le préambule, les packages et `\begin{document}` ne sont pas transmis au parser.

### Autonomie du retour XML

La restauration depuis le monofichier est **autonome** : elle ne dépend pas du XML original. L'information portée par la zone `lateiDocument` suffit à reconstruire le TEI. Cependant, le `\begin{lateiDocument}` commence par `\begin{teiElement}[name={teiHeader}]` (comme prouvé par `test_monofile_zone_contains_body_content`, ligne 45), ce qui signifie que le teiHeader complet est dans la zone réversible.

---

## Ancienne chaîne PDF stable

### Les quatre modules

| Module | Rôle | Lignes |
|--------|------|--------|
| `purh_site/tei_to_model.py` | Parse le XML TEI normalisé → modèle sémantique `Book` | ~80+ lignes de parseur XPath |
| `purh_site/semantic_model.py` | Définit les dataclasses du modèle sémantique (`Book`, `Division`, `Section`, `Paragraph`, `FigureBlock`, etc.) | ~400+ lignes de dataclasses |
| `purh_site/latex_renderer.py` | Convertit le `Book` en LaTeX complet (préambule, corps, inline) | ~998 lignes |
| `purh_site/pdf_builder.py` | Orchestre les trois étages + compilation LuaLaTeX + rapport | ~444 lignes |

### Qui appelle quoi

**Depuis la production :**
- `site_builder.py` (lignes 14–16) importe `LatexRenderOptions` et `PdfBuilder` — utilisés en mode `pdf_export_mode ∈ {"latex","latex_pdf"}`. Ces imports sont **actifs** mais conditionnels.
- `latei_stable_pdf.py` importe `LatexRenderOptions`, `PdfBuilder` — module de transition (ponte LaTEI → stable PDF). Actif uniquement si appelé explicitement.
- `latei_convergence_audit.py` importe `LatexRenderOptions`, `PdfBuilder` — outil de comparaison, non appelé en production.

**Depuis les tests :**
- `test_pdf_latex.py`, `test_pdf_structure.py`, `test_pdf_latex_compile.py`, `test_stable_purh_decisions_contract.py` — testent exclusivement la chaîne stable.
- `test_latei_direct_title_page.py`, `test_latei_direct_frontmatter_numbering.py` — testent des comportements LaTEI mais comparent contre la chaîne stable.
- `test_latei_to_stable_pdf.py` — teste le pont `latei_stable_pdf.py`.

**Important :** `latex_renderer.py` ligne 67 ré-exporte depuis `latei_typography.py` :
```python
from .latei_typography import RUNNING_TITLE_STOPWORDS, _short_running_title  # re-exports
```
Ces ré-exports permettent aux tests legacy (`test_pdf_latex.py`) de continuer d'importer depuis `latex_renderer` sans modification.

### Classifications

| Module | Classification |
|--------|---------------|
| `tei_to_model.py` | **ACTIF_PRODUIT** — appelé par `PdfBuilder` qui est lui-même appelé par `site_builder.py` et `latei_stable_pdf.py` |
| `semantic_model.py` | **ACTIF_PRODUIT** — importé par `tei_to_model.py`, `latex_renderer.py`, `pdf_builder.py` |
| `latex_renderer.py` | **ACTIF_PRODUIT** (via `site_builder`) + **ACTIF_LATEI** (ré-exports `_short_running_title`, wrapper `render_purh_preamble_for_latei`) |
| `pdf_builder.py` | **ACTIF_PRODUIT** (via `site_builder`) + **ACTIF_LATEI** (via `latei_stable_pdf.py`, tests de convergence) |
| `latei_stable_pdf.py` | **DEBUG** — pont de validation LaTEI → stable PDF, non intégré dans le workflow éditorial |
| `latei_convergence_audit.py` | **DEBUG** — outil de comparaison des deux chaînes, non production |

---

## Artefacts produits et statut

### Artefacts de la chaîne LaTEI

| Artefact | Nomenclature | Statut | Destinataire | Nécessaire PDF | Nécessaire retour XML | Nécessaire tests | Peut aller en debug | GUI |
|----------|-------------|--------|-------------|---------------|----------------------|-----------------|--------------------|----|
| `*.latei.tex` | `latei_monofile_path` / `primary_latei_path` | **PRINCIPAL** | Éditrice | Oui (compil directe) | Oui (via `extract_latei_document_zone`) | Oui | Non | Affiché en tête |
| `*.latei_mono.pdf` | `latei_monofile_pdf_path` / `primary_pdf_path` | **PRINCIPAL** | Éditrice | — | Non | Oui | Non | Affiché en tête |
| `*.latei_manifest.json` | `manifest_path` | PRINCIPAL | Outillage | Non | Non | Oui | Non | Affiché |
| `*.latei_body.tex` | `latei_body_path` | DEBUG | Développeurs | Non (ne compile pas seul) | Oui (restauration legacy) | Oui | Plus tard | Sous « Fragments debug » |
| `*.latei_main.tex` | `latei_main_path` | DEBUG | Développeurs | Oui (compilation debug) | Non | Oui | Plus tard | Sous « Fragments debug » |
| `*.latei_macros.tex` | `latei_macros_path` | DEBUG | Développeurs | Via `latei_main` | Non | Oui | Plus tard | Sous « Fragments debug » |
| `*.latei_graphics_map.tex` | `latei_graphics_map_path` | DEBUG | Développeurs | Via `latei_main` | Non | Oui | Plus tard | Sous « Fragments debug » |
| `*.latei_running_titles_map.tex` | `latei_running_titles_map_path` | DEBUG | Développeurs | Via `latei_main` | Non | Oui | Plus tard | Sous « Fragments debug » |
| `latei_assets/` | `latei_assets_dir` | AUXILIAIRE | Compilation | Oui (images) | Non | Oui | Plus tard | Affiché |
| `*.latei.pdf` | `latei_pdf_path` | DEBUG | Développeurs | — | Non | Oui | Plus tard | « PDF LaTEI (debug) » |
| `*.latei_build.log` | `latei_log_path` | DEBUG | Développeurs | Non | Non | Oui | Plus tard | Affiché |
| `*.latei_mono_build.log` | `latei_monofile_log_path` | DEBUG | Développeurs | Non | Non | Oui | Plus tard | Non affiché |
| `*.roundtrip.xml` | `roundtrip_xml_path` | ROUND-TRIP | Qualité | Non | Non | Oui | Non | Affiché |
| `*.roundtrip_diagnostics.txt` | `diagnostics_path` | ROUND-TRIP | Qualité | Non | Non | Oui | Non | Affiché |
| `*.reversible.tex` | `latex_path` | LEGACY | Développeurs | Non | Identique à `latei_body` | Oui (tests anciens) | Oui | Non affiché |

### Artefacts de la chaîne HTML

| Artefact | Statut | Note |
|----------|--------|------|
| `index.html` + pages | PRODUCTION | Site statique multi-pages |
| `assets/site.css`, `assets/app.js` | PRODUCTION | Ressources statiques copiées depuis `resources/` |
| `book.normalized.xml` | PRODUCTION optionnel | Ecrit si `write_normalized_tei=True` |
| `assets/generated/book.tex` | DEBUG (mode latex) | Via `PdfBuilder`, déclenché uniquement si `pdf_export_mode="latex"` |
| `assets/generated/book.pdf` | DEBUG (mode latex_pdf) | Via `PdfBuilder` + LuaLaTeX |
| `build_report.txt` | QUALITÉ | Rapport du build HTML |

---

## GUI et CLI

### `LATEI_USAGE_HELP` (gui.py lignes 21–46)

Le texte définit correctement `*.latei.tex` comme « fichier éditorial principal » avec la mention explicite « l'éditrice corrige uniquement la zone lateiDocument ». Les fragments sont listés sous « Fragments techniques (debug) — à ne pas corriger directement » avec la note que `*.latei_body.tex` ne compile pas seul. La mention « ancien driver de compilation fragmenté » qualifie `*.latei_main.tex`. La constante `LATEI_PACKAGE_HELP` (ligne 15) résume le paquet pour le widget d'aide dans l'interface.

**Bémol :** `LATEI_USAGE_HELP` documente encore une action de restauration depuis le corps fragmenté (`Outils → Restaurer un XML Métopes depuis un corps LaTEI…`) comme « format legacy », mais ne documente pas l'action équivalente depuis le monofichier — il n'y a pas encore de bouton GUI dédié pour `restore_xml_from_latei_monofile`.

### `format_latei_export_summary` (gui.py lignes 646–706)

La fonction place correctement le monofichier en tête (lignes 663–677) et regroupe les fragments sous « Fragments debug : » (ligne 680). La propriété `primary_latei_path` est lue via `getattr` (ligne 650) pour robustesse. Le PDF issu du driver fragmenté est explicitement étiqueté « PDF LaTEI (debug) » (ligne 695). Le manifeste est affiché (ligne 677).

**Impureté I1** (voir section Impuretés) : ligne 688 contient une chaîne encodée incorrectement : `"Titres courants abrÃ©gÃ©s"` au lieu de `"Titres courants abrégés"` — ceci est une corruption UTF-8 visible dans le résumé GUI/CLI.

### `expected_latei_package_artifacts` (gui.py lignes 615–638)

Liste dans l'ordre : `primary_latei_path`, `latei_body_path`, `latei_main_path`, `latei_macros_path`, `latei_graphics_map_path`, `latei_running_titles_map_path`, `latei_assets_dir`, `roundtrip_xml_path`, `diagnostics_path`, `manifest_path`, puis optionnellement le log et le PDF si `latei_pdf_success`. Cette liste inclut tous les artefacts requis pour un « préol paquet LaTEI ».

### `missing_latei_package_artifacts` (gui.py ligne 641–643)

Filtre les chemins absents sur disque. Le test `test_latei_package_preflight_and_summary_report_expected_artifacts` (gui_preflight ligne 85) valide que la liste est vide quand tous les fichiers existent.

### Actions GUI LaTEI

- **Menu Outils → "Exporter un paquet LaTEI depuis un XML…"** : appelle `run_reversible_export_for_file` puis affiche le résumé.
- **Menu Outils → "Restaurer un XML Métopes depuis un corps LaTEI…"** : appelle `restore_xml_from_latei_body` avec un sélecteur de fichier filtré sur `*.latei_body.tex`. **Il n'existe pas encore d'action GUI pour `restore_xml_from_latei_monofile`** (restauration depuis `*.latei.tex`).
- **Menu Aide → "Mode d'emploi LaTEI…"** : affiche `LATEI_USAGE_HELP`.

### CLI (`reversible_integration.py::main`, lignes 497–550)

Le CLI affiche correctement `primary_latei_path` en tête, qualifie le PDF fragmenté de « debug » (ligne 538 : `"PDF LaTEI (debug) : ..."`), et affiche les fragments sous « Fragments debug : » (ligne 527).

---

## Tests et couverture

### Cartographie par groupe

| Groupe | Fichiers principaux | Ce qu'il prouve | Ce qu'il ne prouve pas | Dépend LuaLaTeX | Vitesse | Suite normale |
|--------|-------------------|-----------------|------------------------|-----------------|---------|---------------|
| **HTML/site** | `test_smoke.py`, `test_site_structure_navigation.py`, `test_site_quality_report.py`, `test_zotero_metadata.py`, `test_internal_references.py`, `test_french_typography.py`, `test_metopes_*.py` | Build multi-pages, navigation, métadonnées Zotero, typographie française, figures, notes, bibliographie HTML | Rendu XSL complet sur fixture réelle grande | Non | Rapide | Oui |
| **Reversible core** | `test_reversible_core.py`, `test_reversible_contract.py`, `test_reversible_roundtrip.py`, `test_reversible_realistic_tei.py`, `test_reversible_real_metopes_fragments.py`, `test_reversible_*_elements.py`, `test_reversible_mixed_content.py`, `test_reversible_public_api.py` | Lecteur/éditeur LaTEI sémantique, roundtrip TEI↔LaTeX, contenu mixte, éléments spécialisés | Compilation réelle du LaTEI produit | Non | Rapide | Oui |
| **LaTEI monofichier** | `test_latei_monofile.py` | Création `*.latei.tex`, structure zone `lateiDocument`, préambule inline, macros inline | Compilation réelle (nécessite LuaLaTeX) | Non (teste la structure, pas la compilation) | Rapide | Oui |
| **LaTEI retour XML** | `test_latei_monofile_restore.py`, `test_latei_restore_from_body.py` | Extraction zone, exclusion préambule, restauration complète depuis monofichier et body | Que le XML restauré est sémantiquement équivalent à l'original sur fixture complexe | Non | Rapide | Oui |
| **Workflow éditorial** | `test_latei_monofile_editorial_workflow.py` | Correction dans zone `lateiDocument` → XML corrigé ; hors zone → invisible au parser | Compilation du monofichier corrigé (nécessite LuaLaTeX, marqué `pytest.mark.skip` ou conditionnel) | Optionnel | Moyen | Oui (sans compilation) |
| **PDF monofichier** | Partie de `test_latei_real_metopes_fixture.py`, `test_latei_monofile.py` | Création fichiers PDF, paths corrects | Qualité typographique du PDF | Oui (si disponible) | Lent (skip si absent) | Conditionnel |
| **PDF stable legacy** | `test_pdf_latex.py`, `test_pdf_structure.py`, `test_pdf_latex_compile.py`, `test_stable_purh_decisions_contract.py` | Rendu LaTeX stable complet, structure du livre, compilation, décisions PURH | Nouvelle chaîne LaTEI | Optionnel (`test_pdf_latex_compile.py`) | Moyen | Oui (oracle) |
| **GUI/preflight** | `test_latei_gui_preflight.py`, `test_reversible_export_summary.py` | Labels GUI corrects, hiérarchie monofichier/fragments, préflight artefacts, format résumé | Fenêtre Tkinter réelle | Non | Rapide | Oui |
| **Manifeste** | `test_latei_output_manifest.py` | JSON valide, section `primary`/`debug`, chemins relatifs, support XML restore | Non | Non | Rapide | Oui |
| **Fixtures Métopes réelles** | `test_latei_real_metopes_fixture.py`, `test_reversible_real_metopes_fragments.py` | Roundtrip sans diagnostic sur `heraldique_ii.book.normalized.xml`, métadonnées | Compilation PDF complète en CI sans LuaLaTeX | Conditionnel | Moyen | Oui |
| **Integration** | `test_reversible_integration.py` | Tous les chemins `_output_paths`, body==latex, main a `\documentclass` et `\input` | Non | Non | Rapide | Oui |
| **Pont LaTEI→stable** | `test_latei_to_stable_pdf.py` | Restauration XML et build stable depuis `latei_body` | PDF réel sans LuaLaTeX | Conditionnel | Lent | Conditionnel |
| **Audit convergence** | `test_latei_pdf_convergence_audit.py`, `test_latei_tex_convergence_audit.py` | Rapport markdown de convergence entre les deux chaînes | | Oui (pour PDF) | Très lent | Non (hors CI) |
| **Preamble independence** | `test_latei_preamble_independent.py` | `latei_preamble` et `latei_driver` n'importent pas `latex_renderer` | | Non | Rapide | Oui |

---

## Impuretés restantes

### Impureté I1 — Corruption UTF-8 dans `format_latei_export_summary`

**Gravité :** faible  
**Modules :** `purh_site/gui.py` ligne 688  
**Symptôme :** La chaîne `"Titres courants abrÃ©gÃ©s"` contient une corruption UTF-8 (`é` encodé en latin-1 interprété comme UTF-8). Visible dans le résumé GUI et CLI.  
**Risque :** Affichage illisible pour l'utilisateur ; validation du test `test_latei_gui_preflight.py` ligne 100 qui vérifie la chaîne corrompue (`"Titres courants abrÃ©gÃ©s : 3"`), ce qui masque le bug au lieu de le détecter.  
**Correction recommandée :** Remplacer `"Titres courants abrÃ©gÃ©s"` par `"Titres courants abrégés"` dans `gui.py` et mettre à jour l'assertion du test.  
**Passe proposée :** Passe A (immédiat)

---

### Impureté I2 — `site_builder.py` importe `PdfBuilder` et `LatexRenderOptions`

**Gravité :** moyenne  
**Modules :** `purh_site/site_builder.py` lignes 14–16  
**Symptôme :** `site_builder.py` importe de l'ancienne chaîne PDF stable pour le mode `pdf_export_mode`. Ces imports empêchent d'isoler la chaîne stable sans casser le build HTML.  
**Risque :** Couplage invisible entre la chaîne HTML et la chaîne PDF stable. Si `PdfBuilder` est déplacé, le build HTML se casse.  
**Correction recommandée :** Attendre que la chaîne LaTEI soit validée comme alternative de production, puis remplacer `PdfBuilder` par un appel à `run_reversible_export_for_file` dans `site_builder.py`, ou extraire le mode PDF dans un module dédié.  
**Passe proposée :** Passe E (après validation LaTEI directe complète)

---

### Impureté I3 — `latex_renderer.py` ré-exporte des symboles LaTEI depuis `latei_typography.py`

**Gravité :** moyenne  
**Modules :** `purh_site/latex_renderer.py` ligne 67  
**Symptôme :** `latex_renderer.py` importe et ré-exporte `RUNNING_TITLE_STOPWORDS` et `_short_running_title` depuis `latei_typography.py` pour maintenir la compatibilité des tests legacy (`test_pdf_latex.py:5`). Ce ré-export crée une dépendance circulaire apparente et obscurcit la frontière entre les deux chaînes.  
**Risque :** Si un test futur importe ces symboles depuis `latex_renderer` en croyant qu'ils appartiennent à la chaîne stable, la migration vers `legacy/` sera compliquée.  
**Correction recommandée :** Mettre à jour `test_pdf_latex.py` pour importer depuis `latei_typography` directement, puis supprimer le ré-export de `latex_renderer.py`. Vérifier que `test_latei_direct_running_titles.py` et `test_latei_running_titles_minimal.py` importent déjà depuis `latei_typography` (à vérifier explicitement).  
**Passe proposée :** Passe B

---

### Impureté I4 — Absence de bouton GUI `restore_xml_from_latei_monofile`

**Gravité :** moyenne  
**Modules :** `purh_site/gui.py`, `purh_site/reversible_integration.py`  
**Symptôme :** La fonction `restore_xml_from_latei_monofile` existe (ligne 365) et est testée (`test_latei_monofile_restore.py`, `test_latei_monofile_editorial_workflow.py`), mais il n'y a pas d'action GUI pour la déclencher directement depuis un `*.latei.tex`. L'action GUI existante (ligne 159) cible uniquement `*.latei_body.tex` (format legacy).  
**Risque :** L'éditrice qui reçoit un `*.latei.tex` ne peut pas le restaurer en XML directement depuis le GUI — elle doit passer par la CLI ou utiliser l'action legacy sur `*.latei_body.tex`.  
**Correction recommandée :** Ajouter dans le menu Outils une action « Restaurer un XML Métopes depuis un monofichier LaTEI… » qui ouvre un sélecteur filtré sur `*.latei.tex` et appelle `restore_xml_from_latei_monofile`.  
**Passe proposée :** Passe C

---

### Impureté I5 — `test_latei_direct_running_titles.py` et `test_latei_running_titles_minimal.py` importent encore depuis `latex_renderer`

**Gravité :** faible  
**Modules :** `tests/test_latei_direct_running_titles.py`, `tests/test_latei_running_titles_minimal.py`  
**Symptôme :** D'après `AUDIT_LEGACY_PDF_IMPORTS.md` (lignes 130–131), ces deux fichiers importent `RUNNING_TITLE_STOPWORDS` et `_short_running_title` depuis `latex_renderer`. Or ces symboles ont été migrés vers `latei_typography.py`. Le ré-export de `latex_renderer.py` masque ce problème.  
**Risque :** Si le ré-export est supprimé sans mettre à jour ces tests, ils cassent.  
**Correction recommandée :** Mettre à jour les imports de ces tests pour pointer vers `purh_site.latei_typography`.  
**Passe proposée :** Passe B

---

### Impureté I6 — `latei_convergence_audit.py` dépend de `PdfBuilder` sans être marqué clairement debug/legacy

**Gravité :** faible  
**Modules :** `purh_site/latei_convergence_audit.py` lignes 11–13  
**Symptôme :** Ce module importe `PdfBuilder` et `LatexRenderOptions` pour l'audit de convergence. Il est non production mais aucun commentaire dans l'en-tête du module ne précise qu'il sera supprimé en Passe I.  
**Risque :** Un développeur futur pourrait penser que ce module est nécessaire à la production.  
**Correction recommandée :** Ajouter une docstring ou un commentaire de tête indiquant le statut debug/transition et la passe de suppression prévue.  
**Passe proposée :** Passe D (annotation) / Passe I (suppression)

---

### Impureté I7 — Artefact `*.reversible.tex` redondant avec `*.latei_body.tex`

**Gravité :** faible  
**Modules :** `purh_site/reversible_integration.py` lignes 231–232 et 407  
**Symptôme :** `run_reversible_export_for_file` écrit deux fois le même contenu (`result.latex`) : une fois dans `latex_path` (`*.reversible.tex`) et une fois dans `latei_body_path` (`*.latei_body.tex`). C'est explicite ligne 232 : `latei_body_path.write_text(result.latex, ...)` après ligne 231 `latex_path.write_text(result.latex, ...)`. Le test `test_reversible_integration.py` ligne 49 vérifie même l'égalité des deux fichiers.  
**Risque :** Confusion sur quel fichier est « le » corps réversible. Gaspillage d'espace disque minimal. Le champ `ReversibleExportResult.latex_path` pointe vers `*.reversible.tex` mais n'est affiché nulle part dans le GUI principal.  
**Correction recommandée :** En Passe F, supprimer l'écriture de `*.reversible.tex` ou le renommer en alias de `*.latei_body.tex`. Mettre à jour les tests qui vérifient `result.latex_path`.  
**Passe proposée :** Passe F

---

## Modules candidats debug/legacy

| Module | Classification | Justification |
|--------|---------------|---------------|
| `purh_site/semantic_model.py` | ACTIF_PRODUIT | Requis par `tei_to_model`, `latex_renderer`, `pdf_builder` — tous actifs |
| `purh_site/tei_to_model.py` | ACTIF_PRODUIT | Requis par `pdf_builder.py` — appelé par `site_builder.py` et `latei_stable_pdf.py` |
| `purh_site/latex_renderer.py` | ACTIF_PRODUIT + ACTIF_LATEI | Appelé par `site_builder.py` via `PdfBuilder` ; ré-exporte des symboles LaTEI |
| `purh_site/pdf_builder.py` | ACTIF_PRODUIT | Appelé par `site_builder.py` (mode `latex`/`latex_pdf`) et `latei_stable_pdf.py` |
| `purh_site/latei_stable_pdf.py` | DEBUG / TRANSITION | Pont explicite LaTEI → stable PDF, non intégré workflow éditorial, non appelé par GUI principal |
| `purh_site/latei_convergence_audit.py` | DEBUG | Outil de comparaison uniquement, non production |
| `purh_site/latei_preamble.py` | ACTIF_LATEI | Appelé par `latei_driver.py` et `latex_renderer._render_purh_preamble` |
| `purh_site/latei_driver.py` | ACTIF_LATEI | Production LaTEI : construit le monofichier et le driver fragmenté |
| `purh_site/latei_assets.py` | ACTIF_LATEI | Packaging images LaTEI |
| `purh_site/latei_running_titles.py` | ACTIF_LATEI | Mapping titres courants LaTEI |
| `purh_site/latei_typography.py` | ACTIF_LATEI | Utilitaire indépendant partagé (importé par `latex_renderer` et `latei_running_titles`) |
| `purh_site/reversible_integration.py` | ACTIF_LATEI | Adaptateur application-level, expose GUI/CLI |
| `purh_site/reversible/` | ACTIF_LATEI | Core réversible (lecteur/écrivain/roundtrip) |
| `purh_site/site_builder.py` | ACTIF_PRODUIT + ACTIF_HTML | Orchestre le build HTML multi-pages |
| `purh_site/config.py` | ACTIF_PRODUIT | Configuration du build HTML |
| `purh_site/gui.py` | ACTIF_PRODUIT | Interface graphique |

---

## Architecture cible recommandée

Aucun déplacement n'est effectué ici. L'architecture cible souhaitable est :

```
purh_site/
├── [chaîne HTML — statu quo]
│   site_builder.py, config.py, normalizer.py, tei_loader.py,
│   site_structure.py, resources/tei_to_html.xsl, ...
│
├── [chaîne LaTEI — active]
│   reversible_integration.py
│   reversible/ (core)
│   latei_driver.py, latei_preamble.py, latei_assets.py,
│   latei_running_titles.py, latei_typography.py, latei_metadata.py
│
├── [chaîne PDF stable — active dans site_builder + oracle tests]
│   semantic_model.py, tei_to_model.py, latex_renderer.py, pdf_builder.py
│
├── debug/  [futur — pas encore créé]
│   latei_stable_pdf.py    [condition : validation complète LaTEI direct]
│   latei_convergence_audit.py  [condition : idem]
│
└── legacy/  [futur — pas encore créé]
    [tests/legacy/]
        test_pdf_latex.py
        test_pdf_structure.py
        test_pdf_latex_compile.py
    [semantic_model.py, tei_to_model.py, latex_renderer.py, pdf_builder.py]
    [condition : site_builder.py migré vers LaTEI direct pour le PDF]
```

### Déplacements souhaitables (non effectués)

| Déplacement | Condition préalable | Risque | Tests à lancer | Priorité |
|------------|---------------------|--------|----------------|---------|
| `test_pdf_latex.py` → `tests/legacy/` | Ré-exports `latex_renderer` nettoyés (I3+I5) | Faible | Suite complète | Passe G |
| `test_pdf_structure.py` → `tests/legacy/` | Idem | Faible | Suite complète | Passe G |
| `latei_stable_pdf.py` → `purh_site/debug/` | LaTEI direct validé sur fixture réelle | Moyen | `test_latei_to_stable_pdf.py` | Passe I |
| `latei_convergence_audit.py` → `purh_site/debug/` | Idem | Faible | `test_latei_{pdf,tex}_convergence_audit.py` | Passe I |
| `semantic_model.py`, `tei_to_model.py`, `latex_renderer.py`, `pdf_builder.py` → `purh_site/legacy/` | `site_builder.py` migré vers LaTEI pour PDF | Fort | Suite entière | Passe E+H |

---

## Plan de passes suivant

### Passe A — Corrections d'encodage et documentation

**Objectif :** Corriger la corruption UTF-8 dans `format_latei_export_summary` et améliorer la docstring de `latei_convergence_audit.py`.  
**Fichiers :** `purh_site/gui.py` (ligne 688), `tests/test_latei_gui_preflight.py` (ligne 100), `purh_site/latei_convergence_audit.py` (en-tête)  
**Tests :** `test_latei_gui_preflight.py`  
**Critère de succès :** Le résumé affiche « Titres courants abrégés » correctement ; le test valide la nouvelle chaîne  
**Risque :** Nul

---

### Passe B — Nettoyage imports `latex_renderer` dans les tests de running titles

**Objectif :** Mettre à jour `test_latei_direct_running_titles.py` et `test_latei_running_titles_minimal.py` pour importer depuis `purh_site.latei_typography` directement. Supprimer ou isoler le ré-export de `latex_renderer.py` ligne 67.  
**Fichiers :** `tests/test_latei_direct_running_titles.py`, `tests/test_latei_running_titles_minimal.py`, `purh_site/latex_renderer.py`  
**Tests :** `test_latei_direct_running_titles.py`, `test_latei_running_titles_minimal.py`, `test_pdf_latex.py` (vérifier que le ré-export ne casse rien)  
**Critère de succès :** Aucun import LaTEI depuis `latex_renderer` dans les tests LaTEI ; `latex_renderer.py` n'importe plus depuis `latei_typography` sauf pour son usage interne  
**Risque :** Faible — vérifier que `test_pdf_latex.py` (qui importe `_short_running_title` depuis `latex_renderer`) ne casse pas

---

### Passe C — Bouton GUI `restore_xml_from_latei_monofile`

**Objectif :** Ajouter dans le menu Outils une action « Restaurer un XML Métopes depuis un monofichier LaTEI… » qui cible `*.latei.tex` et appelle `restore_xml_from_latei_monofile`.  
**Fichiers :** `purh_site/gui.py`  
**Tests :** `test_latei_gui_preflight.py` (ajouter assertion sur le label du nouveau menu)  
**Critère de succès :** Le menu Outils contient les deux actions de restauration ; la restauration depuis monofichier fonctionne en GUI  
**Risque :** Faible — ajout pur, pas de modification de code existant

---

### Passe D — Annotation des modules debug/transition

**Objectif :** Ajouter en en-tête de `latei_stable_pdf.py` et `latei_convergence_audit.py` un bloc docstring indiquant clairement leur statut (DEBUG/TRANSITION) et la passe de suppression prévue.  
**Fichiers :** `purh_site/latei_stable_pdf.py`, `purh_site/latei_convergence_audit.py`  
**Tests :** Aucun requis  
**Critère de succès :** Les deux modules ont une mention explicite de leur statut  
**Risque :** Nul

---

### Passe E — Migration `site_builder.py` vers LaTEI pour la génération PDF

**Objectif :** Remplacer l'appel à `PdfBuilder` dans `site_builder._build_pdf_site_artifacts` par un appel à `run_reversible_export_for_file`, ou extraire le mode PDF dans un module optionnel.  
**Fichiers :** `purh_site/site_builder.py`, `purh_site/config.py`  
**Tests :** `test_smoke.py`, `test_site_quality_report.py`, tests d'intégration HTML  
**Critère de succès :** `site_builder.py` n'importe plus `PdfBuilder` ni `LatexRenderOptions` ; le mode `latex_pdf` produit un PDF via la chaîne LaTEI  
**Risque :** Fort — blocant sur validation complète de la chaîne LaTEI en production

---

### Passe F — Suppression de l'artefact redondant `*.reversible.tex`

**Objectif :** Supprimer l'écriture de `latex_path` (`*.reversible.tex`) dans `run_reversible_export_for_file`, ou faire de `latex_path` un alias vers `latei_body_path`.  
**Fichiers :** `purh_site/reversible_integration.py`, `tests/test_reversible_integration.py`  
**Tests :** `test_reversible_integration.py` (mettre à jour les assertions sur `result.latex_path`)  
**Critère de succès :** Un seul fichier corps réversible produit ; le champ `latex_path` reste valide  
**Risque :** Faible — mais impact sur tous les tests qui vérifient `result.latex_path.exists()`

---

### Passe G — Déplacement des tests pure stable vers `tests/legacy/`

**Objectif :** Déplacer `test_pdf_latex.py`, `test_pdf_structure.py`, `test_pdf_latex_compile.py` vers `tests/legacy/`. Conserver `test_stable_purh_decisions_contract.py` comme oracle à long terme.  
**Fichiers :** 3 fichiers de tests + `pyproject.toml` / `pytest.ini` pour exclure ou inclure `tests/legacy/`  
**Tests :** Suite complète pour vérifier que les tests déplacés passent toujours  
**Critère de succès :** Suite principale plus rapide ; oracle conservé  
**Risque :** Faible si la configuration pytest est mise à jour correctement

---

### Passe H/I — Mise en legacy des modules PDF stable et des modules debug

**Objectif :** Déplacer `latei_stable_pdf.py`, `latei_convergence_audit.py` en `purh_site/debug/`, puis `semantic_model.py`, `tei_to_model.py`, `latex_renderer.py`, `pdf_builder.py` en `purh_site/legacy/`.  
**Condition préalable :** Passe E terminée et validée ; suite principale sans import de ces modules depuis le code de production  
**Tests :** Suite complète ; les tests legacy doivent pointer vers les nouveaux chemins  
**Critère de succès :** Aucun import depuis le code de production vers `purh_site/legacy/`  
**Risque :** Fort — à ne faire qu'après Passe E

---

## Verdict final

### L'architecture actuelle est-elle saine ?

**Oui, globalement.** Les deux chaînes sont opérationnelles et bien séparées. Le code est lisible, les modules ont des responsabilités claires, et les tests couvrent les comportements critiques. Les impuretés identifiées sont connues, documentées (notamment dans `AUDIT_LEGACY_PDF_IMPORTS.md`) et ne bloquent pas le workflow éditorial.

### Le monofichier LaTEI est-il suffisamment installé comme artefact principal ?

**Oui.** Le monofichier `*.latei.tex` est déclaré artefact principal dans :
- `ReversibleExportResult.primary_latei_path` (ligne 56–58 de `reversible_integration.py`)
- Le manifeste JSON (clé `"primary"`)
- `LATEI_USAGE_HELP` (gui.py ligne 28)
- `format_latei_export_summary` (affichage en tête)
- La CLI `main()` (lignes 519–524)
- Les tests `test_latei_monofile.py`, `test_latei_output_manifest.py`, `test_reversible_export_summary.py`, `test_latei_gui_preflight.py`

### Qu'est-ce qui empêche encore de considérer les fragments comme purement debug ?

1. **`restore_xml_from_latei_body`** reste l'unique action GUI de restauration XML. Tant que le GUI ne propose pas `restore_xml_from_latei_monofile`, l'éditrice doit encore accéder à `*.latei_body.tex` pour la restauration via l'interface graphique (Impureté I4).
2. **`*.latei_body.tex` est nécessaire à `latei_stable_pdf.py`** : ce module de validation restaure depuis le corps fragmenté, pas depuis le monofichier. Tant que ce pont de validation est actif, le corps fragmenté reste un artefact fonctionnel.
3. **Les tests de convergence (`latei_convergence_audit.py`, `test_latei_to_stable_pdf.py`)** comparent les deux chaînes en utilisant le corps fragmenté. Tant que la convergence n'est pas déclarée close, ces tests justifient la production du corps.

### Qu'est-ce qui empêche encore de mettre l'ancienne chaîne PDF stable en legacy ?

1. **`site_builder.py` appelle `PdfBuilder`** pour le mode `pdf_export_mode="latex_pdf"`. Tant que ce mode est disponible dans le GUI et que la chaîne LaTEI directe n'est pas proposée comme alternative dans `site_builder`, les quatre modules stables (`semantic_model`, `tei_to_model`, `latex_renderer`, `pdf_builder`) restent nécessaires en production.
2. **`test_stable_purh_decisions_contract.py`** sert d'oracle typographique. Il doit rester actif (même en `tests/legacy/`) pour valider que la chaîne stable ne régresse pas et pour servir de référence lors de la convergence LaTEI.
3. **Les symboles partagés** (`_short_running_title`, `RUNNING_TITLE_STOPWORDS`) sont encore ré-exportés depuis `latex_renderer.py`, ce qui crée une dépendance formelle de la chaîne LaTEI vers la chaîne stable. La Passe B lève ce blocage.

### Quelle est la prochaine passe la plus sûre ?

**Passe A** (correction UTF-8 ligne 688 de `gui.py`) est la plus immédiate et sans risque. Elle améliore l'expérience utilisateur sans toucher à aucune logique.

**Passe B** (nettoyage des ré-exports `latex_renderer`) est la passe structurelle la plus sûre : elle ne déplace aucun fichier, ne supprime aucune fonctionnalité, et permet de clarifier la frontière entre les deux chaînes. C'est le prérequis de toutes les passes de migration ultérieures.

**Passe C** (bouton GUI `restore_xml_from_latei_monofile`) complète le workflow éditorial en rendant le monofichier autonome pour la restauration XML, ce qui rend les fragments encore davantage optionnels du point de vue de l'éditrice.

---

## Passe A réalisée

Date : 2026-06-23

- Correction de l'encodage `Titres courants abrégés` dans `format_latei_export_summary` (`purh_site/gui.py` ligne 687).
- Mise à jour de l'assertion correspondante dans `tests/test_latei_gui_preflight.py` ligne 100.
- Annotation de `purh_site/latei_convergence_audit.py` comme outil debug / transition (remplacement de la docstring d'en-tête).
- Tests lancés : `test_latei_gui_preflight.py` (2 passed), `test_reversible_export_summary.py` (6 passed).
- Vérification : aucune occurrence résiduelle de `abrÃ©gÃ©s` hors du présent rapport.

---

## Passe B réalisée

Date : 2026-06-23

**État initial constaté par `rg` (différent de l'audit) :**

- `tests/test_latei_direct_running_titles.py` et `tests/test_latei_running_titles_minimal.py` importaient **déjà** depuis `purh_site.latei_typography` — aucune modification nécessaire sur ces fichiers.
- `tests/test_pdf_latex.py` l.5 importait `_short_running_title` depuis `purh_site.latex_renderer` — seul fichier à corriger.
- `purh_site/latex_renderer.py` l.67 importait `RUNNING_TITLE_STOPWORDS` et `_short_running_title` depuis `latei_typography` comme re-exports ; `_short_running_title` était utilisé en interne l.399 ; `RUNNING_TITLE_STOPWORDS` n'était utilisé qu'en re-export.

**Modifications effectuées :**

- `purh_site/latex_renderer.py` l.67 : suppression du re-export `RUNNING_TITLE_STOPWORDS, _short_running_title` ; remplacement par `from .latei_typography import _short_running_title as _compute_short_running_title`.
- `purh_site/latex_renderer.py` l.399 : appel interne mis à jour vers `_compute_short_running_title(title)`.
- `tests/test_pdf_latex.py` l.5 : import scindé — `LatexRenderer, LatexRenderOptions` restent depuis `latex_renderer` ; `_short_running_title` migré vers `purh_site.latei_typography`.

**Tests lancés :**

- `test_latei_direct_running_titles.py`, `test_latei_running_titles_minimal.py` : 3 passed
- `test_pdf_latex.py`, `test_pdf_structure.py` : 57 passed
- `test_latei_preamble_independent.py` : 9 passed

**Vérification de pureté :** aucune occurrence de `_short_running_title` ou `RUNNING_TITLE_STOPWORDS` importée depuis `latex_renderer` dans le code source (hors documents d'audit).

---

## Passe C réalisée

Date : 2026-06-23

**Modifications effectuées dans `purh_site/gui.py` :**

- Import ajouté : `restore_xml_from_latei_monofile` depuis `reversible_integration`.
- `LATEI_USAGE_HELP` mis à jour : la restauration depuis monofichier est documentée comme chemin normal ; l'ancienne restauration depuis le corps fragmenté est signalée comme « Ancien format fragmenté (debug/legacy) ».
- Menu `Outils` : entrée `"Restaurer un XML Métopes depuis un monofichier LaTEI…"` ajoutée avant l'entrée corps LaTEI existante.
- Méthode `_restore_xml_from_latei_monofile` ajoutée (filtre `*.latei.tex`, chemin de sortie `*.restored.xml`, message de succès clair, gestion d'erreur).
- Fonction `latei_monofile_restored_stem` ajoutée à côté de `latei_body_restored_stem`.

**L'ancienne restauration depuis `*.latei_body.tex` reste disponible** — visible dans le menu, inchangée, comme mode legacy/debug.

**Le workflow éditrice est désormais aligné sur l'artefact principal :** `*.latei.tex` est à la fois le fichier à corriger, à compiler et à restaurer en XML via l'interface graphique.

**Tests ajoutés dans `tests/test_latei_gui_preflight.py` :**

- `test_gui_exposes_monofile_restore_action` : vérifie que le label, la fonction et le filtre `*.latei.tex` sont présents, et que l'action monofichier précède l'action corps dans le source.
- `test_latei_usage_help_documents_monofile_restore` : vérifie que l'aide documente la restauration monofichier comme chemin normal et la fragmentation comme legacy.
- `test_latei_monofile_restored_stem_strips_latei_suffix` : vérifie le calcul du nom de sortie par défaut.

**Tests lancés :**

- `test_latei_gui_preflight.py` : 5 passed (2 anciens + 3 nouveaux)
- `test_latei_monofile_restore.py`, `test_latei_monofile_editorial_workflow.py` : 17 passed

---

## Passe D réalisée

Date : 2026-06-23

**Nouveau module créé : `purh_site/stable_pdf_export.py`**

Adaptateur transitoire qui encapsule l'appel à `PdfBuilder` et `LatexRenderOptions`.
Exporte `build_stable_pdf_artifacts(xml_input_path, output_dir, *, compile_pdf, latex_engine)` et re-exporte `PdfBuildResult` pour que `site_builder.py` n'ait plus à importer directement les modules stable/legacy.

**Modifications dans `purh_site/site_builder.py` :**

- Suppression des imports `from .latex_renderer import LatexRenderOptions` et `from .pdf_builder import PdfBuildResult, PdfBuilder`.
- Ajout de `from .stable_pdf_export import PdfBuildResult, build_stable_pdf_artifacts`.
- `_build_pdf_site_artifacts` délègue maintenant à `build_stable_pdf_artifacts(...)` au lieu d'instancier `PdfBuilder` directement.

**Ce qui n'a pas changé :**

- Le comportement des modes `"none"`, `"latex"`, `"latex_pdf"` est strictement identique.
- Ce n'est pas encore une migration vers LaTEI — l'ancienne chaîne PDF stable reste active.
- `PdfBuilder`, `LatexRenderOptions`, `semantic_model`, `tei_to_model` restent en place.

**Nouveau test : `tests/test_stable_pdf_export_adapter.py`** (4 tests rapides)

- Vérifie par inspection de source que `site_builder.py` n'importe plus directement `PdfBuilder` ni `LatexRenderOptions`.
- Vérifie que `stable_pdf_export.py` est le seul point d'entrée vers `PdfBuilder` pour le site.
- Vérifie l'importabilité et la cohérence des exports.

**Tests lancés :**

- `test_stable_pdf_export_adapter.py` : 4 passed
- `test_smoke.py`, `test_site_quality_report.py` : 29 passed
- `test_pdf_latex.py`, `test_pdf_structure.py` : 57 passed
