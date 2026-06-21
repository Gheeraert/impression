# Audit PDF Stable Vs LaTEI Direct

## Source

- Fixture: `tests\fixtures\metopes\heraldique_ii.book.normalized.xml`
- Stable TeX: `C:\impression2\_latei_pdf_audit_runtime\stable_pdf\book.tex`
- Stable PDF: `C:\impression2\_latei_pdf_audit_runtime\stable_pdf\book.pdf`
- LaTEI body: `_latei_pdf_audit_runtime\latei_pdf\heraldique_ii.book.normalized.latei_body.tex`
- LaTEI main: `_latei_pdf_audit_runtime\latei_pdf\heraldique_ii.book.normalized.latei_main.tex`
- LaTEI macros: `_latei_pdf_audit_runtime\latei_pdf\heraldique_ii.book.normalized.latei_macros.tex`
- LaTEI PDF: `_latei_pdf_audit_runtime\latei_pdf\heraldique_ii.book.normalized.latei.pdf`

## Essential Metadata

- Title: `Héraldique et papauté. Moyen Âge-Temps modernes. II`
- Publisher: `PURH`
- Publication year: `2025`
- Print ISBN: `979-10-240-1855-3`

## Compilation Result

- Stable success: `True`
- LaTEI success: `True`
- Stable pages: `351`
- LaTEI pages: `357`
- Stable page size: `439.37 x 651.968 pts`
- LaTEI page size: `439.37 x 651.968 pts`
- Stable PDF size: `1345582` bytes
- LaTEI PDF size: `1219867` bytes

## LaTeX Comparison

### Preamble

- documentclass book twoside openany: stable `yes` / LaTEI `yes`
- geometry: stable `yes` / LaTEI `yes`
- fontspec: stable `yes` / LaTEI `yes`
- microtype: stable `yes` / LaTEI `yes`
- babel: stable `yes` / LaTEI `yes`
- csquotes: stable `yes` / LaTEI `yes`
- hyperref: stable `no` / LaTEI `no`
- fancyhdr: stable `yes` / LaTEI `yes`
- titlesec: stable `no` / LaTEI `no`
- PurhBibliography: stable `yes` / LaTEI `yes`

### Title Page

- titlepage: stable `yes` / LaTEI `yes`
- title: stable `yes` / LaTEI `yes`
- publisher: stable `yes` / LaTEI `yes`
- no visible year line: stable `yes` / LaTEI `yes`
- no visible print ISBN line: stable `yes` / LaTEI `yes`
- no visible PDF ISBN line: stable `yes` / LaTEI `yes`
- no visible ePub ISBN line: stable `yes` / LaTEI `yes`
- no visible DOI line: stable `yes` / LaTEI `yes`
- no visible experimental mention: stable `yes` / LaTEI `yes`

### Book Structure

- frontmatter: stable `yes` / LaTEI `yes`
- mainmatter: stable `yes` / LaTEI `yes`
- backmatter: stable `no` / LaTEI `yes`
- table of contents: stable `yes` / LaTEI `yes`
- part: stable `yes` / LaTEI `yes`
- chapter: stable `yes` / LaTEI `yes`
- section: stable `yes` / LaTEI `yes`
- running heads: stable `yes` / LaTEI `yes`

### Blocks

- paragraphs: stable `yes` / LaTEI `yes`
- inline quotation: stable `no` / LaTEI `yes`
- notes: stable `yes` / LaTEI `yes`
- figures: stable `no` / LaTEI `yes`
- missing image fallback: stable `yes` / LaTEI `yes`
- bibliography block: stable `yes` / LaTEI `yes`
- hanging bibliography entry: stable `yes` / LaTEI `yes`
- tables: stable `no` / LaTEI `no`
- lists: stable `yes` / LaTEI `yes`

## PDF Text Comparison

- Stable text starts with: `Héraldique et papauté. Moyen Âge-Temps modernes. II PURH Remerciements Toute notre gratitude va aux institutions qui ont permis la publication de ce recueil : le Centre Saint-Louis à Rome et son directeur François-Xavier Adam, hôtes du deux`
- LaTEI text starts with: `Héraldique et papauté. Moyen Âge-Temps modernes. II PURH Remerciements Toute notre gratitude va aux institutions qui ont permis la publication de ce recueil : le Centre Saint-Louis à Rome et son directeur François-Xavier Adam, hôtes du deux`
- First significant text gap: same prefix, different extracted length: stable 113919 words, LaTEI 113379 words

## Elements Not Yet Migrated Or Still Divergent

- Table/list policies are not yet audited to visual parity.
- Bibliographic punctuation is readable but not yet equivalent to the stable Python model.
- Figure captions and credits remain conservative and need visual comparison against the stable renderer.
- Page count is allowed to differ while the remaining block policies are still migrating.
- Direct LaTEI must keep converging toward the stable PDF; the stable PDF remains the reference until this audit is closed.
