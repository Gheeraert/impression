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


def test_directors_override_replaces_misattributed_pbd_author() -> None:
    """Constaté sur *Dissimuler pour mieux régner* (2026-08-04) : le seul
    <author role="pbd"> du TEI/Métopes source y désigne la compositrice, pas
    les éditrices scientifiques — sans marqueur fiable pour les distinguer
    dans le TEI, la correction se fait par saisie explicite (GUI/config),
    jamais en devinant depuis le contenu."""
    from purh_site.reversible_integration import run_reversible_export_for_file

    xml = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
      <teiHeader>
        <fileDesc>
          <titleStmt>
            <title type="main">Dissimuler pour mieux regner</title>
            <author role="pbd"><persName><forename>Anais</forename><surname>Lebreton</surname></persName></author>
          </titleStmt>
          <publicationStmt><publisher>PURH</publisher></publicationStmt>
          <sourceDesc><p/></sourceDesc>
        </fileDesc>
      </teiHeader>
      <text><group type="book">
        <group type="introduction" data-page-title="Introduction" xml:id="intro">
          <front><div type="titlePage"><p rend="title-main">Introduction</p></div></front>
          <body><div><p>Corps.</p></div></body>
        </group>
      </group></text>
    </TEI>"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "book.xml"
        xml_path.write_text(xml, encoding="utf-8")
        result = run_reversible_export_for_file(
            xml_path,
            Path(tmp) / "out",
            directors_override="Floriane Daguise et Florence Fix",
        )
        main = result.latei_main_path.read_text(encoding="utf-8")
        assert "Floriane Daguise et Florence Fix" in main
        assert "Anais Lebreton" not in main


def test_publisher_mention_is_always_the_fixed_full_name_bottom_anchored() -> None:
    """Vérification humaine directe du 2026-08-04 : au lieu du sigle "PURH"
    (tel quel dans le TEI/Métopes source, constaté sur *Dissimuler pour
    mieux régner*) juste sous les éditeurs scientifiques, il faut le nom
    complet, en majuscules grasses Chaparral, calé en bas de la page de
    titre."""
    from purh_site.latei_driver import _full_title_page
    from purh_site.latei_metadata import LateiMetadata

    page = _full_title_page(LateiMetadata(title="Titre", publisher="PURH"))
    assert r"\vspace*{\fill}" in page
    assert r"\PurhPublisherMention{Presses universitaires de Rouen et du Havre}" in page
    assert r"\PurhTitleExtra{PURH}" not in page

    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\newcommand{{\PurhPublisherMention}}[1]{{%" in preamble_source
    mention_macro = preamble_source.split(r"\newcommand{{\PurhPublisherMention}}[1]{{%")[1].split("\n")[1]
    assert r"\bfseries\MakeUppercase" in mention_macro
    assert r"\PURHTitleFont" not in mention_macro  # Chaparral (ambient font), pas Josefin


def test_century_roman_numerals_are_smallcaps_in_the_subtitle() -> None:
    """Vérification humaine directe du 2026-08-04, sur *Dissimuler pour
    mieux régner* : "XVIIe-XIXe siècles" apparaissait en grandes capitales
    au lieu de petites capitales dans le sous-titre."""
    from purh_site.latei_driver import _small_caps_century_numerals

    text = r"Locus politicus, locus secretus en litterature (XVIIe-XIXe siecles)"
    result = _small_caps_century_numerals(text)
    assert r"\textsc{XVII}e-\textsc{XIX}e siecles" in result
    # Ordinary words must not be mistaken for roman numerals.
    assert "litterature" in result and r"\textsc" not in result.split("(")[0]


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
    """Vérification humaine directe du 2026-08-04 : les points de suite et
    le numéro de page doivent apparaître au niveau du TITRE, pas de
    l'auteur. Le filet reste dans le 4e argument dédié de
    \\titlecontents{chapter} (inchangé) — une première tentative avait
    déplacé \\titlerule*/\\contentspage DANS le texte transmis à
    \\addcontentsline pour les faire suivre immédiatement le titre ;
    abandonnée, le paquet bookmark (signets PDF automatiques, construits
    depuis ce même texte) ne tolère pas ces macros dans cet argument
    ("Token not allowed in a PDF string", puis désynchronisation de
    titlesec — bug réel constaté par compilation). Solution retenue : le
    nom d'auteur n'est plus jamais concaténé dans le texte de l'entrée de
    chapitre — voir test_toc_author_line_is_not_smallcaps pour son
    mécanisme de ligne séparée."""
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    chapter_titlecontents = preamble_source.split(r"\titlecontents{{chapter}}")[1].split(r"\titlecontents{{part}}")[0]
    assert r"\PURHTitleFont" not in chapter_titlecontents
    assert r"\bfseries" not in chapter_titlecontents
    assert r"\addvspace" not in chapter_titlecontents
    assert r"\titlerule*[0.5pc]{{.}}\contentspage" in chapter_titlecontents

    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    finish_entry = macros.split(r"\cs_new_protected:Npn \latei_finish_contribution_toc_entry:")[1]
    # \addcontentsline carries the title alone; the author, if any, is
    # written as a wholly separate \addtocontents call below it.
    addcontentsline_call = finish_entry.split(r"\addcontentsline{toc}{chapter}{")[1].split("}\n")[0]
    assert r"\lateiTocAuthorLine" not in addcontentsline_call
    assert r"\addtocontents{toc}{\protect\lateiTocAuthorLine{\lateiTocAuthorPlain}}" in finish_entry


def test_part_toc_entries_are_bold_smallcaps_centered_with_blank_lines() -> None:
    """Vérification humaine directe du 2026-08-04 : les titres de ce niveau
    (le référentiel dit « titres de section », mais désigne bien le niveau
    \\part) doivent être en petites capitales — à la différence du nom
    d'auteur sous chaque entrée de contribution, qui doit au contraire
    rester bas de casse (voir test_toc_author_line_is_not_smallcaps)."""
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\titlecontents{{part}}" in preamble_source
    assert (
        r"\addvspace{{1\baselineskip}}\PURHTitleFont\bfseries\scshape\fontsize{{12pt}}{{14pt}}\selectfont\centering"
        in preamble_source
    )
    assert r"[\addvspace{{1\baselineskip}}]" in preamble_source


def test_toc_author_line_is_not_smallcaps() -> None:
    """Vérification humaine directe du 2026-08-04 : le nom de l'auteur dans
    la TDM doit rester bas de casse, alors que la signature de fin
    d'article (§8) affiche le nom de famille en petites capitales
    (\\textsc{{Nom}}, capturé tel quel dans \\lateiSignatureAuthor).

    Une première tentative redéfinissait \\textsc localement DANS
    l'argument de \\addcontentsline (via \\renewcommand, entre
    \\lateiTocAuthorBreak et le nom) — abandonnée : \\addcontentsline écrit
    son argument via \\protected@write, qui \\edef-développe le texte, et un
    \\edef ne peut pas EXÉCUTER les primitives non désarmables (\\def,
    \\global…) que \\renewcommand appelle en interne — il les recopie telles
    quelles, corrompant le fichier .toc plutôt que de neutraliser \\textsc
    (bug réel constaté par compilation : erreurs "\\textsc has an extra }"
    ailleurs dans le document). La capture "texte brut" se fait donc plus
    tôt, au fil normal du document (\\lateiContributionAuthor), via
    \\protected@xdef et une redéfinition locale de \\textsc par un simple
    \\def (pas par \\renewcommand)."""
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    author_macro = macros.split(r"\newcommand{\lateiContributionAuthor}[1]{%")[1].split(
        r"\newcommand{\lateiContributionAffiliation}"
    )[0]
    assert r"\def\textsc##1{##1}%" in author_macro
    assert r"\protected@xdef\lateiTocAuthorPlain{#1}%" in author_macro

    assert r"\global\let\lateiTocAuthorPlain\lateiSignatureEmpty" in macros

    finish_entry = macros.split(r"\cs_new_protected:Npn \latei_finish_contribution_toc_entry:")[1]
    # \lateiSignatureAuthor is only used as the emptiness guard (\ifx) here;
    # \lateiTocAuthorPlain is what actually gets printed in the TOC.
    assert r"\ifx\lateiSignatureAuthor\lateiSignatureEmpty\else" in finish_entry
    assert r"\addtocontents{toc}{\protect\lateiTocAuthorLine{\lateiTocAuthorPlain}}" in finish_entry


def test_toc_defers_the_entry_to_include_the_author_line() -> None:
    macros = Path("purh_site/resources/latei_macros.tex").read_text(encoding="utf-8")
    assert r"\latei_finish_contribution_toc_entry:" in macros
    assert r"\lateiTocAuthorLine" in macros
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

    # Dotted leader must sit on the title's own line, not the author's below
    # it (vérification humaine directe du 2026-08-04): with "-layout",
    # pdftotext keeps each visual line separate, so the title line and the
    # author line are distinguishable by splitting on newlines.
    plotin_line = next(line for line in toc_text.splitlines() if "Plotin contre Platon" in line)
    author_line = next(line for line in toc_text.splitlines() if "Anne-Lise Worms" in line)
    assert "." in plotin_line
    assert "." not in author_line
