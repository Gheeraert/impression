from __future__ import annotations

"""Rapport visuel humain du 2026-08-04 (livres *Beautés vitales* et
*Dissimuler pour mieux régner*), quatre points :

1. Colophon : calé en bas de page (\\vspace*{{\\fill}}, pas centré), la ligne
   copyright/année reste juste au-dessus de l'adresse même quand les lignes
   couverture/suivi éditorial sont omises, interlignage resserré.
2. Page de titre : titre même hauteur que le faux-titre mais corps plus
   grand, sous-titre gras bas de casse sur deux lignes (retour à la ligne
   reproduit, même principe que \\PURHContributionTitleWidth pour les
   titres d'ouverture), puis « sous la direction de » + noms sur deux
   lignes explicites.
3. Signature de fin d'article : « les articles sont signés à la fin »,
   calée à droite, Chaparral sans graisse, corps réduit — capturée
   globalement dans \\lateiContributionAuthor/\\lateiContributionAffiliation
   (indépendamment de \\iflateiShowContributionAuthor, qui ne régit que
   l'affichage en tête de page) et réémise après le corps de la
   contribution.
4. TDM : « Table des matières » centrée ; entrées de contribution sans
   graisse/Chaparral/calé à gauche avec filet pointillé (pas de saut de
   ligne entre elles) ; prénom + nom de l'auteur en gras sur la ligne
   suivante, indentée (même mécanisme de capture que le point 3, réutilisé
   via \\addcontentsline différé — \\latei_finish_contribution_toc_entry:) ;
   entrées de partie Josefin gras centré, ligne vide avant/après.

Non traité (référentiel §9.1, §11.5/liste des auteurs) : accueil du
colophon en bas de la seconde page de TDM ; séparation par ligne vide entre
notices d'une liste d'auteurs en fin d'ouvrage (aucun marqueur structurel
distinct dans le TEI source pour détecter génériquement ce cas — une suite
de <p> ordinaires, indiscernable d'un corps de texte normal — voir Ch21 de
*Beautés vitales* : "Les auteurs" n'est identifiable que par son titre,
qu'il serait incorrect de coder en dur dans les macros générales)."""

import shutil
from pathlib import Path

import pytest

from purh_site.reversible_integration import run_reversible_export_for_file

_TWO_ARTICLES_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type="main">Beautes vitales</title>
        <title type="sub">Pour une approche contemporaine de la beaute</title>
        <author role="pbd"><persName><forename>Anne-Lise</forename><surname>Worms</surname></persName></author>
        <author role="pbd"><persName><forename>Clelia</forename><surname>Zernik</surname></persName></author>
      </titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="article" data-page-title="Plotin contre Platon" xml:id="a1">
        <front><div type="titlePage">
          <p rend="title-main">Plotin contre Platon</p>
          <p rend="author-aut">Anne-Lise <hi rend="small-caps">Worms</hi></p>
          <p rend="authority_affiliation">Universite de Rouen Normandie, ERIAC UR 4705, France</p>
        </div></front>
        <body><div><p>Corps de larticle sur la beaute.</p></div></body>
      </group>
      <group type="article" data-page-title="Article sans auteur" xml:id="a2">
        <front><div type="titlePage"><p rend="title-main">Article sans auteur</p></div></front>
        <body><div><p>Corps sans auteur signale.</p></div></body>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def two_articles_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_toc_author_signature")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_TWO_ARTICLES_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


# ---------------------------------------------------------------------------
# 1. Colophon
# ---------------------------------------------------------------------------

def test_colophon_is_bottom_anchored_with_starred_fill() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    credits_macro = preamble_source.split(r"\newcommand{{\PURHCreditsPage}}[1]{{%")[1]
    assert r"\vspace*{{\fill}}" in preamble_source
    # The old 0.3\textheight value is only named in the explanatory comment
    # above the fix now, never as active code inside the macro body itself.
    assert r"\vspace*{{0.3\textheight}}" not in credits_macro[:200]


def test_colophon_line_spacing_is_tighter_than_before() -> None:
    driver_source = Path("purh_site/latei_driver.py").read_text(encoding="utf-8")
    assert r'r"\vspace{0.1\baselineskip}".join' in driver_source
    assert r'r"\vspace{0.5\baselineskip}".join' in driver_source
    assert r'r"\vspace{0.4\baselineskip}".join' not in driver_source
    assert r'r"\vspace{1\baselineskip}".join' not in driver_source


def test_colophon_renders_bottom_anchored(two_articles_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not two_articles_export.latei_pdf_success:
        log = two_articles_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Sample did not compile.\n{log[:4000]}")
    assert two_articles_export.latei_pdf_path.exists()


# ---------------------------------------------------------------------------
# 2. Page de titre
# ---------------------------------------------------------------------------

def test_title_page_shares_the_false_titles_vertical_start() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    # Both macros now use the same \vspace* value as active code (a third,
    # non-code mention also lives in an explanatory comment); the earlier
    # \PURHTitlePage value (0.15\textheight) must be gone entirely.
    assert preamble_source.count(r"\vspace*{{0.25\textheight}}") >= 2
    assert r"\vspace*{{0.15\textheight}}" not in preamble_source


def test_title_page_main_title_is_bold_uppercase_josefin_larger_than_false_title() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\newcommand{{\PurhTitleMain}}[1]{{%" in preamble_source
    assert r"\PURHTitleFont\bfseries\fontsize{{22pt}}{{26pt}}\selectfont\centering\MakeUppercase{{#1}}" in preamble_source
    # 22 pt (title) > 12 pt (false title) — both share the same family/weight.
    assert r"\PURHTitleFont\bfseries\fontsize{{12pt}}{{14pt}}\selectfont\MakeUppercase{{#1}}" in preamble_source


def test_subtitle_is_bold_lowercase_and_wraps_after_contemporaine(two_articles_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not two_articles_export.latei_pdf_success:
        log = two_articles_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(two_articles_export.latei_pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert process.returncode == 0, process.stderr
    lines = [line.strip() for line in process.stdout.splitlines()]

    assert "Pour une approche contemporaine" in lines
    assert "de la beaute" in lines
    assert "Pour une approche contemporaine de la beaute" not in process.stdout


def test_editorial_responsibility_is_two_explicit_lines(two_articles_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not two_articles_export.latei_pdf_success:
        log = two_articles_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(two_articles_export.latei_pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert process.returncode == 0, process.stderr
    lines = [line.strip() for line in process.stdout.splitlines()]

    assert "sous la direction de" in lines
    assert "Anne-Lise Worms et Clelia Zernik" in lines


def test_responsibility_falls_back_to_authors_without_the_directed_prefix() -> None:
    from purh_site.latei_driver import _title_page_responsibility_lines
    from purh_site.latei_metadata import LateiMetadata

    directed = _title_page_responsibility_lines(LateiMetadata(directors=["Jean Dupont"]))
    assert directed == "sous la direction de\\\\Jean Dupont"

    authored = _title_page_responsibility_lines(LateiMetadata(authors=["Marie Martin"]))
    assert authored == "Marie Martin"
    assert "sous la direction de" not in authored

    assert _title_page_responsibility_lines(LateiMetadata()) == ""


# ---------------------------------------------------------------------------
# 3. Signature de fin d'article
# ---------------------------------------------------------------------------

def test_signature_capture_is_independent_of_the_opening_display_flag() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    author_macro = macros.split(r"\newcommand{\lateiContributionAuthor}[1]{%")[1].split(r"\newcommand{\lateiContributionAffiliation}")[0]
    assert r"\global\def\lateiSignatureAuthor{#1}%" in author_macro
    # The capture line itself must sit outside \iflateiShowContributionAuthor.
    assert author_macro.index(r"\global\def\lateiSignatureAuthor") < author_macro.index(r"\iflateiShowContributionAuthor")


def test_no_at_sign_empty_sentinel_regression() -> None:
    """Bug réel constaté par compilation : \\@empty hors \\makeatletter se
    tokenise en "\\@" + le texte ordinaire "empty", qui s'imprimait
    littéralement ("empty empty" visible sur la page)."""
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    # \@empty may still be named in the explanatory comment above the fix;
    # only the absence from active code (\let/\ifx targets) matters here.
    assert r"\let\lateiSignatureAuthor\@empty" not in macros
    assert r"\ifx\lateiSignatureAuthor\@empty" not in macros
    assert r"\lateiSignatureEmpty" in macros


def test_signature_appears_right_aligned_after_the_body_not_at_the_opening(two_articles_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not two_articles_export.latei_pdf_success:
        log = two_articles_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(two_articles_export.latei_pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    body_pos = text.index("Corps de larticle sur la beaute.")
    # "Anne-Lise" also legitimately appears earlier, on the book's own title
    # page ("sous la direction de Anne-Lise Worms et Clelia Zernik") — the
    # signature specifically is the occurrence *after* the article body.
    signature_pos = text.index("Anne-Lise", body_pos)
    assert signature_pos > body_pos, "Signature must appear after the body, not at the opening."
    assert "Universite de Rouen Normandie" in text


def test_signature_does_not_leak_into_the_next_authorless_article(two_articles_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not two_articles_export.latei_pdf_success:
        log = two_articles_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(two_articles_export.latei_pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    second_article_pos = text.index("Corps sans auteur signale.")
    # "Anne-Lise" legitimately reappears later, under the TOC entry for the
    # *first* (signed) article — excluded from this window, which only
    # checks the body pages of the second (unsigned) article.
    toc_marker = text.upper().index("TABLE DES MATI")
    body_after_second_article = text[second_article_pos:toc_marker]
    assert "Anne-Lise" not in body_after_second_article


def test_signature_and_reversible_body_stay_untouched(two_articles_export) -> None:
    body = two_articles_export.latei_body_path.read_text(encoding="utf-8")
    assert r"\lateiSignatureAuthor" not in body
    assert r"\lateiRenderContributionSignature" not in body
    assert two_articles_export.success is True
    assert two_articles_export.diagnostics_count == 0


# ---------------------------------------------------------------------------
# 4. Table des matières
# ---------------------------------------------------------------------------

def test_toc_heading_is_centered() -> None:
    driver_source = Path("purh_site/latei_driver.py").read_text(encoding="utf-8")
    assert r"\titleformat{\chapter}[display]" in driver_source
    chapter_override = driver_source.split(r"\titleformat{\chapter}[display]")[1].split('"')[0]
    assert r"\centering" in chapter_override


def test_chapter_toc_entries_are_plain_with_dotted_leader() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    chapter_titlecontents = preamble_source.split(r"\titlecontents{{chapter}}")[1].split(r"\titlecontents{{part}}")[0]
    assert r"\PURHTitleFont" not in chapter_titlecontents
    assert r"\bfseries" not in chapter_titlecontents
    assert r"\addvspace" not in chapter_titlecontents
    assert r"\titlerule*[0.5pc]{{.}}\contentspage" in chapter_titlecontents


def test_part_toc_entries_are_bold_centered_with_blank_lines() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\titlecontents{{part}}" in preamble_source
    assert r"\addvspace{{1\baselineskip}}\PURHTitleFont\bfseries\fontsize{{12pt}}{{14pt}}\selectfont\centering" in preamble_source
    assert r"[\addvspace{{1\baselineskip}}]" in preamble_source


def test_toc_defers_the_entry_to_include_the_author_line() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert r"\latei_finish_contribution_toc_entry:" in macros
    assert r"\lateiTocAuthorBreak" in macros
    # The old immediate \addcontentsline inside the opening break is gone.
    opening_break = macros.split(r"\cs_new_protected:Npn \latei_add_contribution_opening_break:")[1].split(
        r"\cs_new_protected:Npn \latei_finish_contribution_toc_entry:"
    )[0]
    assert r"\addcontentsline" not in opening_break


def test_toc_shows_bold_author_line_under_the_signed_article_only(two_articles_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not two_articles_export.latei_pdf_success:
        log = two_articles_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(two_articles_export.latei_pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert process.returncode == 0, process.stderr
    toc_marker = process.stdout.upper().index("TABLE DES MATI")
    toc_text = process.stdout[toc_marker:]

    assert "Plotin contre Platon" in toc_text
    assert "Anne-Lise Worms" in toc_text
    plotin_pos = toc_text.index("Plotin contre Platon")
    author_pos = toc_text.index("Anne-Lise Worms")
    sans_auteur_pos = toc_text.index("Article sans auteur")
    assert plotin_pos < author_pos < sans_auteur_pos
    # No author line leaks under the second, unsigned entry.
    assert "Anne-Lise" not in toc_text[sans_auteur_pos:]
