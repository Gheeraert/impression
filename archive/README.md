# archive/

Documents d'audit et de migration historiques, conservés pour traçabilité
mais **ne décrivant plus l'état actuel du code**. La plupart portent sur
l'ancienne chaîne PDF « stable » (`PdfBuilder`, `latex_renderer.py`,
`semantic_model.py`) ou sur des passes de migration intermédiaires,
supprimées depuis (voir `../ARCHITECTURE_DROP_STABLE_PDF_CHAIN.md`, qui
reste à la racine comme référence de l'état actuel).

Ne pas s'appuyer sur ces fichiers pour comprendre l'architecture présente :
se référer à `../README.md`, `../LATEI_LAYOUT_COMMANDS.md`,
`../METOPES_COMMONS_LATEI_CONTRACT.md` et
`../ARCHITECTURE_DROP_STABLE_PDF_CHAIN.md`.

## Contenu

- `ARCHITECTURE_PURH_STABLE_DECISIONS.md`, `ARCHITECTURE_LATEI_DIRECT_MIGRATION.md`
  — décisions typographiques de l'ancienne chaîne stable et notes de la
  première migration vers LaTEI direct.
- `AUDIT_CODEX.md`, `AUDIT_CLAUDE_COMPLET.md`, `AUDIT_CLAUDE_RELECTURE_CODEX.md`
  — audits généraux datés de juin 2026, antérieurs à la suppression de la
  chaîne stable et à l'ajout des commandes de mise en page LaTEI à 3 couches.
- `AUDIT_PDF_LATEX.md`, `AUDIT_PDF_STABLE_VS_LATEI.md`, `AUDIT_TEX_STABLE_VS_LATEI.md`,
  `AUDIT_F1_PDF_STABLE_VS_LATEI_HERALDIQUE_25P.md`, `AUDIT_F2_INLINE_STYLES_RUNNING_TITLES_LATEI.md`,
  `AUDIT_LATEI_PDF_HERALDIQUE.md`, `AUDIT_LEGACY_PDF_IMPORTS.md`
  — comparaisons entre l'ancienne chaîne stable et LaTEI, et cartographie
  des imports vers les modules aujourd'hui supprimés.
- `AUDIT_LATEI_PURH_CONVERGENCE.md`, `AUDIT_LATEI_MONOFILE_TARGET.md`,
  `AUDIT_PASSE_E_SITE_BUILDER_PDF_LATEI.md`
  — passes de convergence/migration intermédiaires, terminées depuis
  (LaTEI est l'unique chaîne PDF active, cf. commit « Make LaTEI the only
  active PDF export mode »).
- `AUDIT_TEMPLATE_PURH.md`, `AUDIT_TEMPLATES_PURH.md`
  — audits exploratoires de templates LaTeX antérieurs au préambule PURH
  actuel (`purh_site/latei_preamble.py`).
- `AUDIT_CODEX_COMPLET.md`, `AUDIT_CODE_ET_RENDUS.md`, `audit.md`
  — audits généraux datés du 11 et du 12 juillet 2026, antérieurs à la
  refactorisation de `SiteBuilder` (extraction de `site_credits.py`,
  `site_zotero.py`, `site_quality.py`, `citation.py`), au câblage du
  manifeste des ressources (`site_asset_manifest.py`) et à la mise en
  place de la CI/du lint ruff.
