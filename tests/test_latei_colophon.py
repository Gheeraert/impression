from __future__ import annotations

"""Rapport visuel humain du 2026-08-04 (livres *Beautés vitales* et
*Dissimuler pour mieux régner*), trois corrections :

1. Titre courant : gris jugé encore trop clair après la passe précédente
   (§6.1/§6.2) — remplacé par le même système noir X % (CMJN) que le fond
   d'entête de tableau et le texte courant, à 50 % noir (valeur donnée
   explicitement par l'utilisateur, pas une estimation à recalibrer).
2. Faux-titre : remonté sur la page, passé en Josefin Sans Bold capitales,
   même corps que les titres de section (référentiel §8.1).
3. Colophon (page de crédits) : contenu dicté explicitement par
   l'utilisateur — couverture/mise en pages et suivi éditorial (sans
   équivalent XML, fournis par la boîte de dialogue optionnelle du GUI,
   référentiel §8.1), puis copyright/année, adresse et URL institutionnelles
   PURH fixes, puis ISBN. Remplace l'ancien contenu improvisé (direction,
   collection) qui n'avait jamais été demandé."""

import shutil
from pathlib import Path

import pytest
from lxml import etree

from purh_site.latei_metadata import LateiMetadata
from purh_site.reversible_integration import run_reversible_export_for_file

_XML = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title type="main">Beautes vitales</title></titleStmt>
      <publicationStmt>
        <publisher>PURH</publisher>
        <date type="publishing" when="2026">2026</date>
        <ab type="book"><idno type="ISBN-13">979-10-240-1234-5</idno></ab>
      </publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="introduction" data-page-title="Introduction" xml:id="intro">
        <front><div type="titlePage"><p rend="title-main">Introduction</p></div></front>
        <body><div><p>Corps.</p></div></body>
      </group>
    </group>
  </text>
</TEI>"""


@pytest.fixture(scope="module")
def colophon_export(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_colophon")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_XML, encoding="utf-8")
    return run_reversible_export_for_file(
        xml_path,
        tmp_path / "out",
        cover_designer="Jeanne Martin",
        editorial_contact="Paul Durand",
    )


@pytest.fixture(scope="module")
def colophon_export_without_names(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("latei_colophon_no_names")
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(_XML, encoding="utf-8")
    return run_reversible_export_for_file(xml_path, tmp_path / "out")


# ---------------------------------------------------------------------------
# 1. Titre courant
# ---------------------------------------------------------------------------

def test_running_title_uses_regular_weight_at_75_percent_not_gray_rgb() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\newcommand{{\PURHHeaderFont}}{{\PURHTitleFont\small\color[cmyk]{{0,0,0,0.75}}}}" in preamble_source


# ---------------------------------------------------------------------------
# 2. Faux-titre
# ---------------------------------------------------------------------------

def test_false_title_is_bold_uppercase_same_size_as_section_titles() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    false_title_block = preamble_source.split(r"\newcommand{{\PURHFalseTitle}}[1]{{%")[1].split(
        r"\newcommand{{\PURHCreditsPage}}"
    )[0]
    assert r"\PURHTitleFont\bfseries\fontsize{{12pt}}{{14pt}}\selectfont\MakeUppercase{{#1}}" in false_title_block
    assert r"\vspace*{{0.25\textheight}}" in false_title_block


def test_false_title_moved_higher_than_the_previous_0_35_textheight() -> None:
    preamble_source = Path("purh_site/latei_preamble.py").read_text(encoding="utf-8")
    assert r"\vspace*{{0.35\textheight}}" not in preamble_source


def test_false_title_renders_bold_uppercase(colophon_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not colophon_export.latei_pdf_success:
        log = colophon_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Colophon sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(colophon_export.latei_pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert process.returncode == 0, process.stderr
    assert "BEAUTES VITALES" in process.stdout


# ---------------------------------------------------------------------------
# 3. Colophon
# ---------------------------------------------------------------------------

def test_latei_metadata_cover_designer_has_no_xml_source() -> None:
    """cover_designer n'a aucun équivalent dans le XML (contrairement à
    editorial_contact depuis le 2026-08-06, voir le test dédié ci-dessous,
    ou à publication_year/isbn_print) — vérifie juste qu'il existe comme
    champ simple, jamais peuplé par extract_latei_metadata."""
    metadata = LateiMetadata()
    assert metadata.cover_designer == ""


def test_editorial_contact_defaults_from_edition_stmt_resp_stmt_name() -> None:
    """Vérification humaine directe, 2026-08-06 : <editionStmt>/<respStmt>/
    <name> désigne fiablement la personne chargée de la mise en forme/mise
    en pages (jamais un rôle scientifique, contrairement à <author
    role="pbd"> — voir directors/parse_directors_override) — utilisé par
    défaut pour "Suivi éditorial :", sans saisie manuelle nécessaire."""
    from purh_site.latei_metadata import extract_latei_metadata

    root = etree.fromstring(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0">
          <teiHeader><fileDesc>
            <titleStmt><title type="main">Livre</title></titleStmt>
            <editionStmt>
              <edition><date/></edition>
              <respStmt><resp/><name>Anais Lebreton</name></respStmt>
              <sponsor/>
            </editionStmt>
            <publicationStmt><publisher>PURH</publisher></publicationStmt>
            <sourceDesc><p/></sourceDesc>
          </fileDesc></teiHeader>
          <text><body><p>Texte.</p></body></text>
        </TEI>""".encode("utf-8")
    )
    metadata = extract_latei_metadata(root)
    assert metadata.editorial_contact == "Anais Lebreton"

    # An empty <name/> (real case: Beautés vitales) stays empty, never a
    # fabricated placeholder.
    root_empty = etree.fromstring(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0">
          <teiHeader><fileDesc>
            <titleStmt><title type="main">Livre</title></titleStmt>
            <editionStmt>
              <edition><date/></edition>
              <respStmt><resp/><name/></respStmt>
              <sponsor/>
            </editionStmt>
            <publicationStmt><publisher>PURH</publisher></publicationStmt>
            <sourceDesc><p/></sourceDesc>
          </fileDesc></teiHeader>
          <text><body><p>Texte.</p></body></text>
        </TEI>""".encode("utf-8")
    )
    assert extract_latei_metadata(root_empty).editorial_contact == ""


def test_editorial_contact_gui_override_still_takes_precedence_over_xml() -> None:
    """La saisie manuelle (GUI, dialogue colophon) reste prioritaire quand
    elle est fournie — le défaut XML ne s'applique que si le champ GUI est
    laissé vide (voir reversible_integration.run_reversible_export_for_file)."""
    import tempfile
    from pathlib import Path as _Path

    from purh_site.reversible_integration import run_reversible_export_for_file

    xml = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
      <teiHeader><fileDesc>
        <titleStmt><title type="main">Livre</title></titleStmt>
        <editionStmt>
          <edition><date/></edition>
          <respStmt><resp/><name>Anais Lebreton</name></respStmt>
          <sponsor/>
        </editionStmt>
        <publicationStmt><publisher>PURH</publisher></publicationStmt>
        <sourceDesc><p/></sourceDesc>
      </fileDesc></teiHeader>
      <text><group type="book">
        <group type="introduction" data-page-title="Introduction" xml:id="intro">
          <front><div type="titlePage"><p rend="title-main">Introduction</p></div></front>
          <body><div><p>Corps.</p></div></body>
        </group>
      </group></text>
    </TEI>"""
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = _Path(tmp) / "book.xml"
        xml_path.write_text(xml, encoding="utf-8")

        default_result = run_reversible_export_for_file(xml_path, _Path(tmp) / "out_default")
        default_main = default_result.latei_main_path.read_text(encoding="utf-8")
        assert "Suivi éditorial : Anais Lebreton" in default_main

        override_result = run_reversible_export_for_file(
            xml_path, _Path(tmp) / "out_override", editorial_contact="Paul Durand"
        )
        override_main = override_result.latei_main_path.read_text(encoding="utf-8")
        assert "Suivi éditorial : Paul Durand" in override_main
        assert "Anais Lebreton" not in override_main


def test_export_accepts_cover_designer_and_editorial_contact_overrides(colophon_export) -> None:
    body = colophon_export.latei_body_path.read_text(encoding="utf-8")
    # These two values have no TEI representation: they must not leak into
    # the reversible body, only into the generated front matter.
    assert "Jeanne Martin" not in body
    assert "Paul Durand" not in body

    main = colophon_export.latei_main_path.read_text(encoding="utf-8")
    assert "Couverture et mise en pages : Jeanne Martin" in main
    assert "Suivi éditorial : Paul Durand" in main


def test_colophon_omits_production_lines_when_not_provided(colophon_export_without_names) -> None:
    main = colophon_export_without_names.latei_main_path.read_text(encoding="utf-8")
    assert "Couverture et mise en pages" not in main
    assert "Suivi éditorial" not in main


def test_colophon_always_shows_fixed_purh_address_and_url() -> None:
    driver_source = Path("purh_site/latei_driver.py").read_text(encoding="utf-8")
    assert "2 place Émile Blondel" in driver_source
    assert "http://purh.univ-rouen.fr" in driver_source


def test_colophon_copyright_line_always_shown_even_without_publication_year() -> None:
    """Vérification humaine directe du 2026-08-04 : "(c) Presses
    universitaires de Rouen et du Havre" doit TOUJOURS figurer, juste
    au-dessus de l'adresse — pas seulement quand l'année de publication est
    connue (contrairement au comportement précédent)."""
    from purh_site.latei_driver import _colophon_institutional_lines
    from purh_site.latei_metadata import LateiMetadata

    lines_without_year = _colophon_institutional_lines(LateiMetadata())
    assert lines_without_year[0] == "© Presses universitaires de Rouen et du Havre."
    assert "2 place Émile Blondel" in lines_without_year[1]


def test_colophon_isbn_line_has_a_label_prefix() -> None:
    """Vérification humaine directe du 2026-08-05 : "ISBN :" doit précéder
    le numéro lui-même dans le colophon."""
    from purh_site.latei_driver import _colophon_institutional_lines
    from purh_site.latei_metadata import LateiMetadata

    lines = _colophon_institutional_lines(LateiMetadata(isbn_pdf="979-10-240-1234-5"))
    assert "ISBN : 979-10-240-1234-5" in lines
    assert "979-10-240-1234-5" not in lines[:-1]  # not present anywhere without the prefix

    lines_with_year = _colophon_institutional_lines(LateiMetadata(publication_year="2026"))
    assert lines_with_year[0] == "© Presses universitaires de Rouen et du Havre, 2026."
    assert "2 place Émile Blondel" in lines_with_year[1]


def test_colophon_renders_full_structure_in_the_generated_pdf(colophon_export) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("LuaLaTeX is unavailable.")
    if not colophon_export.latei_pdf_success:
        log = colophon_export.latei_log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(f"Colophon sample did not compile.\n{log[:4000]}")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is unavailable.")

    import subprocess

    process = subprocess.run(
        [shutil.which("pdftotext"), "-enc", "UTF-8", "-layout", str(colophon_export.latei_pdf_path), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert process.returncode == 0, process.stderr
    text = process.stdout

    assert "Couverture et mise en pages : Jeanne Martin" in text
    assert "Suivi éditorial : Paul Durand" in text
    assert "Presses universitaires de Rouen et du Havre, 2026." in text
    assert "2 place Émile Blondel" in text
    assert "Mont-Saint-Aignan Cedex" in text
    assert "purh.univ-rouen.fr" in text
    # "ISBN : " devant le numéro (vérification humaine directe, 2026-08-05).
    assert "ISBN : 979-10-240-1234-5" in text


# ---------------------------------------------------------------------------
# 4. Plomberie GUI (BuildConfig, site_latei_pdf_export, gui.py)
# ---------------------------------------------------------------------------

def test_build_config_has_colophon_fields() -> None:
    from purh_site.config import BuildConfig

    config = BuildConfig(output_dir=Path("."), cover_designer="A", editorial_contact="B")
    assert config.cover_designer == "A"
    assert config.editorial_contact == "B"
    assert BuildConfig(output_dir=Path(".")).cover_designer == ""


def test_site_latei_pdf_export_forwards_colophon_kwargs() -> None:
    import inspect

    from purh_site.site_latei_pdf_export import build_site_latei_pdf_artifacts

    params = inspect.signature(build_site_latei_pdf_artifacts).parameters
    assert "cover_designer" in params
    assert "editorial_contact" in params


def test_gui_exposes_format_dropdown_and_colophon_dialog() -> None:
    source = Path("purh_site/gui.py").read_text(encoding="utf-8")
    assert "_LAYOUT_FORMAT_OPTIONS" in source
    assert "155 × 230 mm" in source


def test_build_config_has_directors_override_field() -> None:
    from purh_site.config import BuildConfig

    config = BuildConfig(output_dir=Path("."), directors_override="Jean Dupont et Marie Martin")
    assert config.directors_override == "Jean Dupont et Marie Martin"
    assert BuildConfig(output_dir=Path(".")).directors_override == ""


def test_site_latei_pdf_export_forwards_directors_override_kwarg() -> None:
    import inspect

    from purh_site.site_latei_pdf_export import build_site_latei_pdf_artifacts

    params = inspect.signature(build_site_latei_pdf_artifacts).parameters
    assert "directors_override" in params


def test_gui_exposes_directors_override_field() -> None:
    source = Path("purh_site/gui.py").read_text(encoding="utf-8")
    assert "directors_override_var" in source
    assert "Sous la direction de (correction)" in source
    assert "_open_colophon_dialog" in source
    assert "cover_designer_var" in source
    assert "editorial_contact_var" in source


def test_gui_window_is_taller_than_the_previous_780():
    source = Path("purh_site/gui.py").read_text(encoding="utf-8")
    assert 'geometry("1080x780")' not in source
    assert 'geometry("1080x900")' in source
