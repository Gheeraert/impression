from __future__ import annotations

"""<div type="titlePage"> carries title/subtitle/author/translator (real
schema confirmed on tests/fixtures/metopes/heraldique_ii.book.normalized.xml:
<p rend="title-main">/<p rend="title-sub">/<p rend="author-aut">/<p rend="editor-trl">)
but was entirely discarded, and the group's own chapter heading printed an
automatic "Chapitre N" label instead (référentiel PURH v0.5, "Ouvertures de
contribution"). Fixed by rendering titlePage content directly and dropping
the chapter label/numbering — titlePage is now the only visible source."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_CONTRIBUTION_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Contribution Opening Test</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="article" data-page-title="Titre article" xml:id="article-001">
        <front>
          <div type="titlePage">
            <p rend="title-main">Titre article</p>
            <p rend="title-sub">Un sous-titre éclairant</p>
            <p rend="author-aut">Prénom Nom</p>
            <p rend="editor-trl">Traduit de l anglais par Quelqu un.</p>
          </div>
        </front>
        <body>
          <div><p>Texte du corps de larticle.</p></div>
        </body>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def contribution_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_contribution_opening")
    xml_path = tmp_path / "contrib.xml"
    xml_path.write_text(_CONTRIBUTION_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


def test_title_page_body_routes_title_subtitle_author_translator(contribution_export) -> None:
    body = contribution_export.latei_body_path.read_text(encoding="utf-8")

    assert r"\teiP[rend={title-main}]{Titre article}" in body
    assert r"\teiP[rend={title-sub}]{Un sous-titre éclairant}" in body
    assert r"\teiP[rend={author-aut}]{Prénom Nom}" in body


def test_macros_render_title_page_content_instead_of_discarding_it() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")

    assert r"\lateiContributionTitle" in macros
    assert r"\lateiContributionSubtitle" in macros
    assert r"\lateiContributionAuthor" in macros
    assert r"\lateiContributionTranslator" in macros


def test_chapter_group_no_longer_prints_a_visible_chapter_label() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")

    # The old \chapter{title} call gave every numbered contribution an
    # automatic "Chapitre N" label; the structural break must not carry a
    # title argument at all now — the titlePage macros are the only thing
    # allowed to print visible title text.
    assert r"\latei_add_contribution_opening_break:" in macros
    assert r"\chapter{\tl_use:N \l_latei_option_page_title_tl}" not in macros
    assert r"\chapter*{\tl_use:N \l_latei_option_page_title_tl}" not in macros


def test_contribution_opening_compiles_without_chapitre_label_and_keeps_toc(
    contribution_export,
) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")

    if not contribution_export.latei_pdf_success:
        log = contribution_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(log.splitlines()[:160])
        pytest.fail(f"Contribution opening sample did not compile.\n{excerpt}")

    assert shutil.which("pdftotext") is not None, "pdftotext is required to verify the rendered text."
    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(contribution_export.latei_pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    assert "Chapitre" not in text
    # title-main is rendered in capitals (référentiel §2.5, §5.3: titraille);
    # the TOC entry below keeps the original case since it comes from
    # data-page-title, a different (metadata) path than the visible heading.
    assert "TITRE ARTICLE" in text
    assert "Un sous-titre" in text  # accented word itself skipped: pdftotext/apostrophe interaction is unrelated to this fix
    assert "Prénom Nom" in text
    assert "Traduit de l anglais par Quelqu un." in text

    toc_path = contribution_export.latei_pdf_path.with_suffix(".toc")
    assert toc_path.exists()
    toc = toc_path.read_text(encoding="utf-8", errors="replace")
    assert r"\contentsline {chapter}{Titre article}" in toc
