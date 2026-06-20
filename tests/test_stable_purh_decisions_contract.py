from __future__ import annotations

from pathlib import Path

from purh_site.latex_renderer import LatexRenderOptions
from purh_site.pdf_builder import PdfBuilder
from purh_site.tei_to_model import parse_normalized_tei


FIXTURE_PATH = Path("tests/fixtures/metopes/heraldique_ii.book.normalized.xml")


def build_stable_latex(tmp_path: Path) -> str:
    result = PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=False,
    ).build_from_normalized_tei(FIXTURE_PATH, tmp_path)

    assert result.success is True
    assert result.tex_path.exists()
    assert result.log_path.exists()
    assert result.report_path.exists()
    return result.tex_path.read_text(encoding="utf-8")


def test_stable_purh_book_matter_title_page_and_toc_contract(tmp_path: Path) -> None:
    latex = build_stable_latex(tmp_path)

    assert r"\documentclass[12pt,twoside,openany]{book}" in latex
    assert r"\begin{titlepage}" in latex
    assert r"\thispagestyle{empty}" in latex
    assert "Héraldique et papauté. Moyen Âge-Temps modernes. II" in latex
    assert r"\PurhTitleExtra{PURH}" in latex
    assert r"\frontmatter" in latex
    assert r"\mainmatter" in latex
    assert r"\tableofcontents" in latex


def test_stable_purh_divisions_sections_and_running_heads_contract(tmp_path: Path) -> None:
    latex = build_stable_latex(tmp_path)

    assert r"\chapter*{Remerciements}" in latex
    assert r"\chapter*{Table des abréviations}" in latex
    assert r"\chapter*{Introduction}" in latex
    assert r"\addcontentsline{toc}{chapter}{Introduction}" in latex
    assert r"\part*{Première partie : Papes}" in latex
    assert r"\chapter{Aspects ludiques dans l’appareil héraldique des manuscrits de Léon X (1513-1521)}" in latex
    assert r"\section{Le pontifical de 1520}" in latex
    assert r"\subsection{" in latex
    assert r"\markboth{" in latex
    assert r"\fancyhead[RE]{\PURHHeaderFont\nouppercase{\PURHBookTitle}}" in latex
    assert r"\fancyhead[LO]{\PURHHeaderFont\nouppercase{\leftmark}}" in latex


def test_stable_purh_notes_inline_figures_and_bibliography_contract(tmp_path: Path) -> None:
    latex = build_stable_latex(tmp_path)

    assert r"\footnote{" in latex
    assert r"\textit{" in latex
    assert r"\textsc{" in latex
    assert r"\textsuperscript{" in latex
    assert r"\href{" in latex
    assert r"\fbox{\parbox{0.8\linewidth}{\centering\footnotesize Image absente ou non fournie}}" in latex
    assert r"\begin{PurhBibliography}" in latex
    assert r"\noindent\hangindent=1.5em\hangafter=1" in latex


def test_stable_purh_output_is_not_latei(tmp_path: Path) -> None:
    latex = build_stable_latex(tmp_path)

    assert r"\teiP" not in latex
    assert r"\teiDiv" not in latex
    assert r"\begin{teiElement}" not in latex
    assert "latei_macros" not in latex


def test_stable_model_observes_real_fixture_decisions() -> None:
    book = parse_normalized_tei(FIXTURE_PATH)

    assert book.metadata.title == "Héraldique et papauté. Moyen Âge-Temps modernes. II"
    assert book.metadata.publication.publisher == "PURH"
    assert book.metadata.publication.isbn_print == "979-10-240-1855-3"
    assert [division.title for division in book.body_divisions][:3] == [
        "Remerciements",
        "Table des abréviations",
        "Introduction",
    ]
    assert book.body_divisions[3].title == "Première partie : Papes"
    assert book.body_divisions[3].div_type.value == "part"
    assert book.body_divisions[4].div_type.value == "chapter"
    assert any(division.notes for division in book.body_divisions)
    assert sum(len(division.sections) for division in book.body_divisions) > 0
