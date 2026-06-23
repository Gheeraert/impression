# Audit cible LaTEI monofichier

> Audit réalisé le 2026-06-22. Passe M1 réalisée le 2026-06-22.

---

## Résumé exécutif

L'architecture actuelle produit **cinq fichiers distincts** pour représenter un seul livre : un body réversible, un driver de compilation, une copie des macros, un mappage graphique et un mappage de titres courants. Ces fichiers sont correctement séparés par responsabilité, mais ils rendent impossible la remise d'un seul fichier éditorial à une éditrice.

La migration vers un **LaTEI monofichier** (`book.latei.tex`) est architecturalement faisable sans casser le noyau réversible. Elle requiert :

1. un **balisage de zone** — `\begin{lateiDocument}…\end{lateiDocument}` — pour que le parser puisse ignorer le préambule ;
2. une **fusion des fragments techniques** dans les sections non réversibles du fichier unique ;
3. une **adaptation légère du parser** pour extraire et lire uniquement la zone réversible.

Le noyau Python (`nodes.py`, `latex_reader.py`, `latex_writer.py`, `tei_reader.py`, `tei_writer.py`, `roundtrip.py`) n'a pas besoin d'être modifié. Seul le point d'entrée d'extraction dans le parser doit être étendu.

---

## Artefacts actuels

### `*.latei_body.tex`

Produit par `latex_writer.py` via `run_tei_latex_tei_roundtrip` dans `reversible_integration.py` (ligne 157–161).

| Critère | État |
|---|---|
| Réversible ? | **Oui** — c'est la source de vérité réversible complète |
| Éditorial ? | **Partiel** — lisible par un œil expert, mais sans préambule, il ne compile pas seul |
| Seulement technique ? | Non |
| Nécessaire à la compilation ? | Oui, via `\input` dans le main |
| Nécessaire au retour XML ? | **Oui — seul ce fichier est lu par `restore_xml_from_latei_body`** |
| Peut être intégré dans un fichier unique ? | **Oui — c'est lui qui devient la zone réversible** |

**Contenu actuel** : le corps encodé en LaTEI contrôlé inclut `\begin{teiElement}[name={teiHeader}]`, `\begin{teiElement}[name={front}]`, `\begin{teiElement}[name={body}]`, `\begin{teiElement}[name={back}]`. Le TEI complet est déjà présent dans ce fichier, teiHeader inclus. Il n'y a pas de `\documentclass`.

---

### `*.latei_main.tex`

Produit par `build_latei_driver` dans `latei_driver.py`.

| Critère | État |
|---|---|
| Réversible ? | **Non** — le module le dit explicitement (commentaire ligne 7–9) |
| Éditorial ? | Non — c'est un wrapper de compilation |
| Seulement technique ? | **Oui** |
| Nécessaire à la compilation ? | **Oui** — c'est le fichier passé à LuaLaTeX |
| Nécessaire au retour XML ? | **Non** |
| Peut être intégré dans un fichier unique ? | **Oui — le monofichier lui succède** |

**Structure** : préambule PURH → `\input{macros}` → `\input{graphics_map}` → `\input{running_titles_map}` → `\begin{document}` → page de titre → `\input{body}` → `\tableofcontents` → `\end{document}`.

---

### `*.latei_macros.tex`

Copie de `purh_site/resources/latei_macros.tex` faite par `build_latei_driver` (ligne 47).

| Critère | État |
|---|---|
| Réversible ? | **Non** |
| Éditorial ? | Non — pure couche typographique |
| Seulement technique ? | **Oui** |
| Nécessaire à la compilation ? | **Oui** |
| Nécessaire au retour XML ? | **Non** |
| Peut être intégré dans un fichier unique ? | **Oui — directement inline dans le préambule** |

---

### `*.latei_graphics_map.tex`

Produit par `package_latei_graphics` dans `latei_assets.py`.

| Critère | État |
|---|---|
| Réversible ? | **Non** |
| Éditorial ? | Non |
| Seulement technique ? | **Oui** — mappe des chemins documentaires TEI vers des chemins locaux copiés |
| Nécessaire à la compilation ? | Conditionnellement oui (si des images existent) |
| Nécessaire au retour XML ? | **Non** — les attributs originaux `url`/`target` sont dans le body |
| Peut être intégré dans un fichier unique ? | **Oui — dans une section technique non réversible** |

---

### `*.latei_running_titles_map.tex`

Produit par `package_latei_running_titles` dans `latei_running_titles.py`.

| Critère | État |
|---|---|
| Réversible ? | **Non** |
| Éditorial ? | Non |
| Seulement technique ? | **Oui** — mappe titres complets → titres courants courts |
| Nécessaire à la compilation ? | Conditionnellement oui |
| Nécessaire au retour XML ? | **Non** |
| Peut être intégré dans un fichier unique ? | **Oui — dans une section technique non réversible** |

---

### `latei_assets/` (dossier images)

| Critère | État |
|---|---|
| Réversible ? | Non |
| Éditorial ? | **Oui, partiellement** — les images font partie du livrable éditorial |
| Seulement technique ? | Non |
| Nécessaire à la compilation ? | Oui |
| Nécessaire au retour XML ? | Non |
| Peut être intégré dans un fichier unique ? | **Non — les images restent dans `latei_assets/`** |

---

### `*.roundtrip.xml`

Produit par `run_reversible_export_for_file` (lignes 185–190).

| Critère | État |
|---|---|
| Réversible ? | C'est lui le produit de la réversibilité |
| Éditorial ? | Non — artefact de validation |
| Seulement technique ? | **Oui** |
| Nécessaire à la compilation ? | Non |
| Nécessaire au retour XML ? | Non — c'est le résultat, pas une entrée |

---

### `*.latei.pdf`

| Critère | État |
|---|---|
| Réversible ? | **Non** |
| Éditorial ? | **Oui** — c'est le livrable final |

---

## Fichier LaTEI cible

### Structure proposée

```latex
% !TeX program = lualatex
% Fichier LaTEI généré depuis XML-TEI Métopes / Commons-Publishing.
% Zone éditoriale réversible : entre \begin{lateiDocument} et \end{lateiDocument}.
% Zone technique non réversible : tout le reste (préambule, macros, mappings).
% Les corrections éditoriales doivent être faites uniquement dans la zone réversible.
% Le préambule et les macros sont régénérables depuis les métadonnées XML.

% ============================================================
% ZONE TECHNIQUE — NE PAS MODIFIER
% Générée automatiquement. Régénérable depuis le XML source.
% ============================================================

\documentclass[12pt,twoside,openany]{book}

% -- Préambule PURH généré --
\usepackage[paperwidth=155mm,...]{geometry}
...
\newcommand{\PURHBookTitle}{Titre du livre}
\newcommand{\PURHBookAuthor}{Auteur A ; Auteur B}
...

% -- Macros LaTEI (inline, régénérables) --
\usepackage{xparse}
...
\NewDocumentCommand{\teiP}{O{} +m}{...}
...

% -- Mappings graphiques (régénérables) --
\lateiDeclareGraphic{media/fig1.png}{latei_assets/images/abc123-fig1.png}
...

% -- Mappings titres courants (régénérables) --
\lateiDeclareRunningTitle{Titre très long...}{Titre court}
...

% ============================================================
% ZONE ÉDITORIALE RÉVERSIBLE
% Corrections autorisées dans cette zone uniquement.
% ============================================================

\begin{document}

\begin{titlepage}
...
\end{titlepage}

\begin{lateiDocument}
\begin{teiElement}[name={teiHeader}]
...
\end{teiElement}
\begin{teiElement}[name={text}]
\begin{teiElement}[name={front}]
...
\end{teiElement}
\begin{teiElement}[name={body}]
...
\end{teiElement}
\begin{teiElement}[name={back}]
...
\end{teiElement}
\end{teiElement}
\end{lateiDocument}

\cleardoublepage
\tableofcontents

\end{document}
```

---

### Réponses aux questions de structure

**Où placer les métadonnées ?**
Les métadonnées sont à double représentation :
- Dans le préambule (zone technique) : `\PURHBookTitle`, `\PURHBookAuthor`, etc. — pour la compilation.
- Dans la zone réversible (teiHeader LaTEI) : `\begin{teiElement}[name={teiHeader}]...` — pour le retour XML.

Les deux sont générées depuis les mêmes métadonnées XML ; elles ne sont jamais dupliquées à la main.

**Faut-il encoder le `teiHeader` en LaTEI ?**
Oui. Le body actuel le fait déjà (`\begin{teiElement}[name={teiHeader}]` est présent dans le body — vérifié dans `test_latei_direct_book_skeleton.py` ligne 29). Il faut conserver ce comportement dans la zone réversible du monofichier.

**Faut-il que la zone réversible contienne tout `<TEI>` ou seulement `<text>` ?**
Tout `<TEI>` (teiHeader + text). C'est ce que fait déjà le body actuel. Cela garantit que le retour XML est strictement autonome — il ne dépend d'aucun fichier externe.

**Comment préserver les attributs TEI ?**
Via les options LaTeX : `[type={chapter},xmlid={div01}]`. Le writer et le reader actuels font cela correctement pour tous les attributs TEI. Aucun changement requis.

**Comment distinguer la zone éditoriale des zones techniques ?**
Par le balisage `\begin{lateiDocument}...\end{lateiDocument}`. Ce qui est avant est technique et ignoré par le parser lors du retour XML. Ce qui est à l'intérieur est réversible.

**Que doit ignorer le parser LaTEI lors du retour XML ?**
Tout ce qui précède `\begin{lateiDocument}` et tout ce qui suit `\end{lateiDocument}`. Cela inclut : `\documentclass`, `\usepackage`, `\newcommand`, `\begin{document}`, `\begin{titlepage}`, `\cleardoublepage`, `\tableofcontents`, `\end{document}`.

**Que doit-il absolument lire ?**
Le contenu entre `\begin{lateiDocument}` et `\end{lateiDocument}`, tel qu'il est aujourd'hui lu depuis le body.

---

## Zone éditoriale réversible

La zone réversible correspond exactement au body actuel (`*.latei_body.tex`), encadrée dans l'environnement `lateiDocument`.

### Règle de réversibilité

| Ce qui est réversible | Ce qui est régénérable |
|---|---|
| Contenu entre `\begin{lateiDocument}` et `\end{lateiDocument}` | Préambule PURH (depuis métadonnées XML) |
| teiHeader encodé en LaTEI | Macros `latei_macros.tex` (copie de la ressource statique) |
| front, body, back | Mappings graphiques (scan des `<graphic>` dans le XML) |
| Tous les attributs TEI | Mappings titres courants (scan des `<head>` dans le XML) |

### Règle de correction éditoriale

Une correction éditoriale (texte, italique, note, référence, etc.) doit :
1. Se faire **uniquement dans la zone réversible** du fichier monofichier.
2. Utiliser uniquement les macros contrôlées (`\teiHi`, `\teiNote`, `\teiRef`, etc.).
3. Ne pas introduire de macros LaTeX non contrôlées.

### Que se passe-t-il si l'éditrice modifie le préambule ?

Si l'éditrice modifie le préambule (zone technique), la modification :
- n'affecte pas le retour XML (le parser l'ignore) ;
- peut casser la compilation si elle introduit des erreurs LaTeX ;
- est perdue lors de la prochaine régénération du monofichier depuis le XML.

Il faut marquer clairement la zone technique avec un commentaire « NE PAS MODIFIER / régénérable automatiquement ».

### Faut-il un contrôle des modifications hors zone ?

Recommandé à terme (passe M8) : un outil de validation qui compare le hash SHA de la zone technique entre la version générée et la version soumise, et signale toute modification hors zone. Non bloquant pour les passes M1–M4.

---

## Compilation

### Ce qui peut être internalisé dans le fichier unique

| Fragment actuel | Internalisable ? | Méthode |
|---|---|---|
| Préambule PURH | **Oui** | Contenu inline (déjà généré par `render_purh_latex_preamble`) |
| `latei_macros.tex` | **Oui** | Contenu inline (lire `LATEI_MACROS_PATH` et inclure en dur) |
| `*.latei_graphics_map.tex` | **Oui** | Lignes `\lateiDeclareGraphic` inline dans la zone technique |
| `*.latei_running_titles_map.tex` | **Oui** | Lignes `\lateiDeclareRunningTitle` inline dans la zone technique |

### Ce qui doit rester dans un dossier d'assets

| Artefact | Reste externe ? | Raison |
|---|---|---|
| Images (`latei_assets/images/`) | **Oui** | Les images ne peuvent pas être encodées en texte LaTeX |
| Fichier log de compilation | Oui | Artefact technique de build |
| PDF produit | Oui | Livrable final binaire |

**Chemin `graphicspath`** : la valeur `{{latei_assets/images/}}` est déjà dans le préambule (`latei_preamble.py` ligne 222). Elle reste valide pour le monofichier si le dossier `latei_assets/` est un sous-dossier du répertoire du monofichier.

---

## Retour XML

### Pipeline retour XML depuis le monofichier

```python
# Étape 1 — Extraire la zone réversible
zone = extract_latei_zone(monofile_text)
# zone = texte entre \begin{lateiDocument} et \end{lateiDocument}

# Étape 2 — Parser la zone (identique à l'actuel)
node = read_latex_document(zone)

# Étape 3 — Reconstruire le TEI
element = write_tei_element(node)
```

L'étape 1 est la seule nouveauté. Les étapes 2 et 3 sont les appels existants dans `restore_xml_from_latei_body`.

### Implémentation de `extract_latei_zone`

```python
BEGIN_MARKER = r"\begin{lateiDocument}"
END_MARKER = r"\end{lateiDocument}"

def extract_latei_zone(monofile_text: str) -> str:
    start = monofile_text.find(BEGIN_MARKER)
    if start == -1:
        raise LatexParseError("Missing \\begin{lateiDocument}.")
    content_start = start + len(BEGIN_MARKER)
    if monofile_text[content_start:content_start+1] == "\n":
        content_start += 1
    end = monofile_text.find(END_MARKER, content_start)
    if end == -1:
        raise LatexParseError("Missing \\end{lateiDocument}.")
    return monofile_text[content_start:end]
```

Cette fonction est intentionnellement triviale : elle ne parse pas le LaTeX, elle cherche seulement deux marqueurs de texte.

### Le retour XML dépend-il du préambule typographique ?

**Non.** Le préambule ne contient aucune information documentaire que le parser ne trouverait pas déjà dans la zone réversible. Les métadonnées (`\PURHBookTitle`, `\PURHBookAuthor`, etc.) sont des macros de compilation ; elles ne sont pas lues par le parser LaTEI. Les métadonnées réelles pour le retour XML proviennent du teiHeader encodé en LaTEI dans la zone réversible.

---

## Métadonnées et teiHeader

### Recommandation nette : Option B enrichie

L'**Option B** est recommandée avec le complément suivant : le LaTEI monofichier encode le teiHeader **complet en LaTEI** dans la zone réversible — exactement comme le fait déjà le body actuel.

Cela donne le meilleur des deux options :

- Le retour XML est **strictement autonome** (Option A) car le teiHeader est présent dans la zone réversible.
- Le préambule typographique reste **simple et régénérable** (Option B) car les métadonnées de compilation (`\PURHBookTitle`, etc.) sont extraites du XML et jamais éditées manuellement dans le préambule.
- L'éditrice ne voit qu'une seule zone éditoriale avec un code lisible.

**Justification** : le body actuel encode déjà le teiHeader en LaTEI (confirmé par le test `test_latei_direct_book_skeleton_keeps_body_reversible`, ligne 29). Ce comportement est acquis. Il ne faut pas le rétrograder.

**Ce que le teiHeader LaTEI doit contenir** : uniquement ce que le tei_reader capture actuellement (tous les éléments fils récursivement). Le writer (`write_latex` dans `latex_writer.py`) le fait sans filtre — il encode tout.

---

## Assets et images

Le dossier `latei_assets/` reste un dossier séparé, mais il fait **partie du livrable éditorial** remis à l'éditrice. Le fichier monofichier et le dossier `latei_assets/` forment ensemble le «paquet éditorial» :

```
livre_titre/
├── livre_titre.latei.tex        ← fichier éditorial unique
└── latei_assets/
    └── images/
        ├── abc123-fig1.png
        └── ...
```

L'éditrice ouvre `livre_titre.latei.tex`, corrige le texte, et compile en tapant `lualatex livre_titre.latei.tex`. Les images sont accessibles via `graphicspath` déjà configuré dans le préambule.

---

## Plan de migration en passes

### Passe M1 — Produire un LaTEI monofichier minimal
**Objectif** : générer un `stem.latei.tex` unique compilable, en assemblant préambule + macros inline + mappings inline + zone réversible encadrée par `\begin{lateiDocument}...\end{lateiDocument}`.

**Fichiers** :
- `purh_site/reversible_integration.py` : ajouter une fonction `build_latei_monofile(source_path, output_dir)` qui produit `stem.latei.tex` en plus des fragments existants.
- `purh_site/latei_driver.py` : ajouter `build_latei_monofile_content(...)` qui inline les macros et les mappings au lieu de les séparer.

**Tests** :
- `test_monofile_has_preamble` : `\documentclass` dans le fichier.
- `test_monofile_has_latei_document_zone` : `\begin{lateiDocument}` et `\end{lateiDocument}` présents.
- `test_monofile_body_is_inside_zone` : le contenu réversible est bien entre les marqueurs.

**Critère de succès** : le monofichier contient exactement le même corps réversible que le body actuel, encadré par les marqueurs.

---

### Passe M2 — Lire la zone réversible d'un LaTEI complet
**Objectif** : adapter `restore_xml_from_latei_body` (ou créer `restore_xml_from_latei_monofile`) pour extraire et parser uniquement la zone `lateiDocument`.

**Fichiers** :
- `purh_site/reversible_integration.py` : ajouter `restore_xml_from_latei_monofile(monofile_path, output_xml_path)`.
- `purh_site/reversible/latex_reader.py` : ajouter `extract_latei_zone(text: str) -> str` (fonction triviale de recherche de marqueurs).

**Tests** :
- `test_parser_ignores_preamble` : un fichier avec préambule complet et zone réversible est parsé sans erreur.
- `test_parser_raises_on_missing_zone` : un fichier sans marqueurs lève `LatexParseError`.
- `test_restore_xml_from_monofile_round_trips` : round-trip XML → monofichier → XML produit un TEI identique.

**Critère de succès** : `compare_tei_elements(source, restored) == []` sur le fixture Métopes.

---

### Passe M3 — Round-trip complet `XML → monofichier → XML`
**Objectif** : brancher la passe M1 et la passe M2 pour un round-trip XML → `stem.latei.tex` → XML sans passer par les fragments.

**Fichiers** :
- `purh_site/reversible_integration.py` : `run_reversible_export_for_file` produit le monofichier en plus (ou à la place) des fragments.

**Tests** :
- `test_monofile_roundtrip_metopes_fixture` : round-trip sur le fixture réel Métopes.
- `test_monofile_roundtrip_preserves_tei_header` : le teiHeader est présent et identique dans le XML restauré.
- `test_monofile_roundtrip_preserves_notes` : les notes (`\teiNote`) sont correctement round-tripées.

**Critère de succès** : zéro diagnostic sur le fixture Métopes.

---

### Passe M4 — Compilation `monofichier → PDF`
**Objectif** : compiler `stem.latei.tex` directement avec LuaLaTeX sans fichier auxiliaire.

**Fichiers** :
- `purh_site/latei_driver.py` : `compile_latei_pdf` prend le monofichier directement.

**Tests** :
- `test_monofile_compiles_with_lualatex` : le PDF est produit et non vide.
- `test_monofile_pdf_page_count` : au moins 10 pages sur le fixture Métopes.

**Critère de succès** : `lualatex stem.latei.tex` sans erreur, PDF ≥ 10 pages.

---

### Passe M5 — Intégration des mappings graphiques dans le monofichier
**Objectif** : s'assurer que les `\lateiDeclareGraphic` sont inline dans le monofichier et que les images de `latei_assets/` sont trouvées.

**Fichiers** :
- `purh_site/latei_assets.py` : produire les lignes inline en plus ou au lieu du fichier séparé.
- `purh_site/latei_driver.py` : inclure ces lignes dans le monofichier zone technique.

**Tests** :
- `test_monofile_graphic_map_inline` : `\lateiDeclareGraphic` présent dans le monofichier.
- `test_monofile_images_compiled` : le PDF contient une page avec une image (si image disponible).

**Critère de succès** : aucune image manquante signalée au log de compilation.

---

### Passe M6 — Intégration des titres courants dans le monofichier
**Objectif** : s'assurer que les `\lateiDeclareRunningTitle` sont inline dans le monofichier.

**Fichiers** :
- `purh_site/latei_running_titles.py` : produire les lignes inline en plus du fichier séparé.

**Tests** :
- `test_monofile_running_titles_inline` : `\lateiDeclareRunningTitle` présent dans le monofichier.

**Critère de succès** : les titres courants courts apparaissent correctement dans le PDF compilé.

---

### Passe M7 — GUI : bouton « Exporter LaTEI éditable »
**Objectif** : remplacer (ou compléter) le bouton d'export fragmentaire par un bouton produisant `stem.latei.tex` + `latei_assets/`.

**Fichiers** :
- `purh_site/gui.py` (ou équivalent GUI) : nouvelle action « Exporter LaTEI éditable ».
- `purh_site/reversible_integration.py` : `ReversibleExportResult` expose `latei_monofile_path`.

**Tests** :
- `test_gui_exports_monofile` : l'action produit un fichier `*.latei.tex` avec la zone réversible.

**Critère de succès** : l'éditrice reçoit un seul fichier `.tex` + un dossier `latei_assets/`.

---

### Passe M8 — Contrôle des modifications hors zone (optionnel)
**Objectif** : détecter si l'éditrice a modifié la zone technique d'un monofichier reçu en retour.

**Fichiers** :
- `purh_site/latei_monofile_validator.py` (nouveau) : compare la zone technique générée avec la zone technique du fichier soumis.

**Tests** :
- `test_validator_flags_preamble_change` : un fichier avec préambule modifié déclenche un avertissement.
- `test_validator_accepts_editorial_change` : un fichier avec correction dans `lateiDocument` est accepté.

**Critère de succès** : aucun faux positif sur des corrections légitimes.

---

### Passe M9 — Mode legacy/debug pour les fragments actuels
**Objectif** : conserver les fragments actuels (`*.latei_body.tex`, `*.latei_main.tex`, etc.) en mode debug ou option `--legacy`.

**Fichiers** :
- `purh_site/reversible_integration.py` : paramètre `legacy_fragments: bool = False`.
- `purh_site/latei_driver.py` : `build_latei_driver` devient optionnel.

**Tests** : les tests existants continuent de passer avec `legacy_fragments=True`.

**Critère de succès** : aucun test existant cassé.

---

## Tests à prévoir

| Test | Description | Passe |
|---|---|---|
| `test_monofile_compiles` | Le monofichier compile avec LuaLaTeX | M4 |
| `test_monofile_has_latei_document_zone` | Le monofichier contient `\begin{lateiDocument}` et `\end{lateiDocument}` | M1 |
| `test_parser_ignores_preamble` | Le parser ne lève pas d'erreur sur un fichier complet | M2 |
| `test_parser_raises_on_missing_zone` | Absence de marqueurs → `LatexParseError` | M2 |
| `test_restore_xml_from_monofile` | Round-trip XML → monofichier → XML sans diagnostic | M3 |
| `test_monofile_tei_header_preserved` | Le teiHeader est complet dans le XML restauré | M3 |
| `test_monofile_images_resolved` | Images trouvées dans `latei_assets/` lors de la compilation | M5 |
| `test_monofile_running_titles_inline` | `\lateiDeclareRunningTitle` présent dans le monofichier | M6 |
| `test_monofile_notes_roundtrip` | Les `\teiNote` survivent au round-trip | M3 |
| `test_monofile_bibliography_roundtrip` | Les `\begin{teiBibl}` survivent au round-trip | M3 |
| `test_monofile_editorial_correction_roundtrip` | Corriger un `\teiP` dans la zone → XML restauré reflète la correction | M3 |
| `test_monofile_pdf_page_count` | PDF ≥ 10 pages sur le fixture Métopes | M4 |
| `test_monofile_macros_inline` | Les macros LaTEI sont présentes inline dans le monofichier | M1 |
| `test_monofile_no_external_input` | Le monofichier ne contient pas de `\input{}` | M4 |

---

## Recommandation finale

### Faut-il viser un vrai LaTEI monofichier ?

**Oui, sans ambiguïté.** L'architecture actuelle est correcte pour l'expérimentation, mais elle ne peut pas servir de livrable éditorial. Un seul fichier `book.latei.tex` est la cible produit.

### Quelle partie doit rester réversible ?

La **zone `lateiDocument`** uniquement. Le préambule, les macros et les mappings sont techniques et régénérables. Le critère est simple : si on peut reconstruire l'information depuis le XML source par un calcul déterministe, elle n'a pas besoin d'être dans la zone réversible.

### Que faire des fragments actuels ?

Les conserver en mode **legacy/debug** (passe M9) jusqu'à ce que toutes les passes M1–M7 soient validées par les tests. Ne rien supprimer avant que le monofichier soit prouvé compilable et réversible sur les fixtures réels.

### Quelle est la première passe sûre ?

**Passe M1**, immédiatement, sans risque. Elle produit un fichier supplémentaire (`stem.latei.tex`) sans toucher aux fragments existants ni au noyau réversible. Les tests existants ne sont pas affectés. Le seul nouveau code est dans `reversible_integration.py` et `latei_driver.py`.

**La passe M2 suit immédiatement** : `extract_latei_zone` est une fonction triviale de 10 lignes. La greffer sur `read_latex_document` existant ne touche pas au parser. Une fois M1 et M2 validées par les tests, le round-trip complet (M3) est une composition directe des deux.

---

## Passe M1 réalisée

**Date** : 2026-06-22

### Fichier monofichier produit

`stem.latei.tex` (ex. : `heraldique_ii.book.normalized.latei.tex`) dans le même dossier de sortie que les fragments existants.

### Ce qui est internalisé dans le monofichier

| Contenu | Source | Méthode |
|---|---|---|
| Préambule PURH | `latei_preamble.render_purh_latex_preamble` | Rendu inline |
| Macros LaTEI | `purh_site/resources/latei_macros.tex` | Lu et inclus inline |
| Mappings graphiques | `*.latei_graphics_map.tex` (généré) | Lu après écriture, inclus inline |
| Mappings titres courants | `*.latei_running_titles_map.tex` (généré) | Lu après écriture, inclus inline |
| Corps réversible | `result.latex` du round-trip | Encadré par `\begin{lateiDocument}...\end{lateiDocument}` |

### Ce qui reste externe

| Artefact | Raison |
|---|---|
| `latei_assets/images/` | Les images binaires ne peuvent pas être encodées inline |
| `*.latei_mono.pdf` | PDF produit par la compilation du monofichier |
| `*.latei_mono_build.log` | Log de compilation |

### Environnement LaTeX transparent

Ajouté à la fin de `purh_site/resources/latei_macros.tex` :

```latex
\newenvironment{lateiDocument}{}{}
```

Cet environnement est complètement transparent à la compilation — il ne change pas le rendu. Il sert uniquement de délimiteur de zone réversible pour le futur parser (passe M2).

### Fragments debug conservés

Les fragments existants sont **tous produits sans changement** :
- `*.latei_body.tex` — body réversible inchangé
- `*.latei_main.tex` — driver fragmenté inchangé
- `*.latei_macros.tex` — copie locale des macros inchangée
- `*.latei_graphics_map.tex` — mapping graphique inchangé
- `*.latei_running_titles_map.tex` — mapping titres courants inchangé

### Fichiers modifiés

| Fichier | Nature de la modification |
|---|---|
| `purh_site/resources/latei_macros.tex` | Ajout `\newenvironment{lateiDocument}{}{}` |
| `purh_site/latei_driver.py` | Ajout `build_latei_monofile`, `_monofile_content`, `_monofile_section`, `_MONOFILE_FILE_HEADER` |
| `purh_site/reversible_integration.py` | Extension `ReversibleExportResult` (5 champs), `_output_paths` (3 chemins), flow principal, 3 early returns |
| `tests/test_latei_monofile.py` | Nouveau fichier — 16 tests |

### Tests lancés

```
tests/test_latei_monofile.py          → 16 passed
tests/test_latei_direct_title_page.py → 3 passed (legacy non cassé)
tests/test_latei_running_titles_minimal.py → 1 passed (legacy non cassé)
tests/test_latei_direct_book_skeleton.py → 4 passed (legacy non cassé)
tests/test_latei_restore_from_body.py → 3 passed (body réversible inchangé)
tests/test_reversible_roundtrip.py    → 12 passed (noyau réversible inchangé)
```

### Lecture XML depuis monofichier

Explicitement reportée à la **passe M2**. Le parser actuel (`latex_reader.py`) ne lit que des corps réversibles purs. La passe M2 ajoutera `extract_latei_zone(monofile_text)` qui extrait le contenu entre `\begin{lateiDocument}` et `\end{lateiDocument}` avant de le passer au parser existant.

---

## Passe M2 réalisée

**Date** : 2026-06-22

### Fonction d'extraction

`extract_latei_document_zone(monofile_text: str) -> str`  
**Module** : `purh_site/reversible/latex_reader.py`  
**Exportée** via `purh_site/reversible/__init__.py`

La fonction :
- cherche `\begin{lateiDocument}` — lève `LatexParseError` si absent ;
- vérifie qu'il n'en existe pas plusieurs — lève `LatexParseError` si plusieurs ;
- cherche `\end{lateiDocument}` à partir du contenu — lève `LatexParseError` si absent (couvre aussi le cas où `\end` précède `\begin`) ;
- saute le saut de ligne cosmétique immédiatement après `\begin{lateiDocument}` ;
- supprime les sauts de ligne finaux inutiles (`.rstrip("\n")`) avant de retourner le texte ;
- ne parse pas le LaTeX général : c'est une recherche de chaîne plain-text.

### Fonction de restauration XML depuis monofichier

`restore_xml_from_latei_monofile(monofile_path: Path, output_xml_path: Path) -> Path`  
**Module** : `purh_site/reversible_integration.py`

Pipeline :
```
monofile_path → read_text() → extract_latei_document_zone()
→ read_latex_document() → write_tei_element() → XML écrit sur disque
```

### Ce que le parser lit

Uniquement le contenu entre `\begin{lateiDocument}` et `\end{lateiDocument}` — identique au corps `*.latei_body.tex`.

### Ce que le parser ignore

Tout ce qui précède `\begin{lateiDocument}` : `\documentclass`, `\usepackage`, `\newcommand`, préambule PURH, macros inline, mappings graphiques, mappings titres courants, `\begin{document}`, page de titre.

Tout ce qui suit `\end{lateiDocument}` : `\cleardoublepage`, `\tableofcontents`, `\end{document}`.

### Invariants de strictesse

Le parser strict (`read_latex_document`) reste inchangé. Passer le monofichier complet à `read_latex_document` sans extraction lève toujours `LatexParseError` (validé par `test_parser_strict_rejects_full_monofile`).

### Restauration depuis body non cassée

`restore_xml_from_latei_body` est inchangée. Les résultats des deux fonctions sont identiques sur le fixture Métopes (`compare_tei_elements` retourne `[]`).

### Fichiers modifiés

| Fichier | Nature de la modification |
|---|---|
| `purh_site/reversible/latex_reader.py` | Ajout `extract_latei_document_zone`, constantes `_BEGIN_LATEI_DOCUMENT` / `_END_LATEI_DOCUMENT` |
| `purh_site/reversible/__init__.py` | Export de `extract_latei_document_zone` |
| `purh_site/reversible_integration.py` | Import et ajout `restore_xml_from_latei_monofile` |
| `tests/test_latei_monofile_restore.py` | Nouveau fichier — 9 tests |

### Tests lancés

```
tests/test_latei_monofile_restore.py   →  9 passed
tests/test_latei_monofile.py           → 16 passed  (M1 non cassé)
tests/test_latei_restore_from_body.py  →  3 passed  (body non cassé)
tests/test_reversible_roundtrip.py     → 12 passed  (noyau réversible non cassé)
```

---

## Passe M3 réalisée

**Date** : 2026-06-22

### Objectif validé

Le fichier LaTEI monofichier peut désormais servir de fichier éditorial corrigible. Une correction faite dans la zone `lateiDocument` est reflétée dans le XML restauré. Les modifications hors zone sont ignorées par le parser.

### Ce que prouvent les tests

| Test | Résultat prouvé |
|---|---|
| `test_text_correction_in_zone_reflected_in_restored_xml` | Correction de texte brut dans la zone → XML restauré contient la correction |
| `test_uncorrected_monofile_preserves_original_text` | Sans correction, le XML restauré est identique à l'original |
| `test_inline_structural_correction_reflected_in_restored_xml` | Correction inline structurée (`\teiHi[rend={italic}]`) → `<hi rend="italic">` dans le XML |
| `test_inline_note_correction_reflected_in_restored_xml` | Ajout d'une note (`\teiNote{}`) dans la zone → `<note>` dans le XML |
| `test_technical_zone_modification_ignored_by_xml_restore` | Modification du commentaire et de la page de titre (zone technique) → `compare_tei_elements == []` |
| `test_modification_outside_editorial_zone_leaves_xml_unchanged` | Ajout après `\end{lateiDocument}` → `compare_tei_elements == []`, texte technique absent du XML |

### Invariants confirmés

- **Seule la zone `lateiDocument` rétroagit vers le XML.** Les modifications dans le préambule, les macros, la page de titre ou tout contenu après `\end{lateiDocument}` sont invisibles au parser.
- **Le préambule reste régénérable.** Il n'est jamais lu par le parser de retour XML.
- **Le parser strict reste inchangé.** Aucune modification de `read_latex_document`.

### Architecture des tests M3

Les tests M3 travaillent entièrement en mémoire (0.03 s) via :
- `write_latex(read_tei_element(element))` → corps LaTEI brut
- `make_monofile(latex_body)` — helper local qui encadre le corps d'une zone technique fictive
- `replace_inside_latei_document(monofile_text, old, new)` — helper local qui remplace uniquement dans la zone réversible
- `restore_from_monofile_text(monofile_text)` — extrait + parse + écrit en un appel

Aucun appel à `run_reversible_export_for_file` dans M3 (pas de compilation PDF, pas de I/O disque superflu).

### Fichiers modifiés

| Fichier | Nature de la modification |
|---|---|
| `tests/test_latei_monofile_editorial_workflow.py` | Nouveau fichier — 6 tests |
| `AUDIT_LATEI_MONOFILE_TARGET.md` | Section « Passe M3 réalisée » |

### Test d'intégration sur vrai monofichier généré (M3-bis)

`test_editorial_correction_on_real_generated_monofile` valide le flux complet sur un fichier produit par le moteur réel :

1. Mini XML TEI écrit sur disque dans `tmp_path`
2. `run_reversible_export_for_file` → génère `*.latei.tex` réel
3. `replace_inside_latei_document` → corrige uniquement la zone réversible
4. Monofichier corrigé écrit sous `edited.latei.tex`
5. `restore_xml_from_latei_monofile` → XML restauré
6. Assertions sur le texte corrigé présent et l'original absent

Ce test garantit que le pipeline de production (pas seulement les helpers en mémoire) supporte le flux éditorial.

### Tests lancés

```
tests/test_latei_monofile_editorial_workflow.py  →  7 passed (8.45 s, dont 1 test d'intégration réel)
tests/test_latei_monofile.py                     → 16 passed (M1 intact)
tests/test_latei_monofile_restore.py             →  9 passed (M2 intact)
tests/test_reversible_roundtrip.py               → 12 passed (noyau intact)
```

---

*Audit rédigé depuis l'inspection directe du code. Aucun fichier modifié.*
