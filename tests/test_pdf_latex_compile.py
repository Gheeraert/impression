from __future__ import annotations

import os
from pathlib import Path
import shutil
import struct
import time
import uuid
import zlib

import pytest

from purh_site.config import BuildConfig
from purh_site.latex_renderer import LatexRenderOptions
from purh_site.pdf_builder import PdfBuilder
from purh_site.site_builder import SiteBuilder


RUN_LATEX = os.environ.get("IMPRESSIONS_RUN_LATEX_INTEGRATION") == "1"
HAS_LUALATEX = shutil.which("lualatex") is not None

pytestmark = pytest.mark.skipif(
    not RUN_LATEX or not HAS_LUALATEX,
    reason="Compilation LuaLaTeX optionnelle désactivée ou lualatex indisponible.",
)


def write_compile_tei(runtime_dir: Path) -> Path:
    xml_path = runtime_dir / "book.normalized.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type="main">Livre PURH compilable</title>
        <title type="sub">Sous-titre compilable</title>
        <author>
          <persName>
            <forename>Alice</forename>
            <surname>Auteur</surname>
          </persName>
        </author>
        <editor>
          <persName>
            <forename>Élodie</forename>
            <surname>Éditrice</surname>
          </persName>
        </editor>
      </titleStmt>
      <publicationStmt>
        <publisher>Presses universitaires de Rouen et du Havre</publisher>
        <pubPlace>Rouen</pubPlace>
        <date type="publishing" when="2026">2026</date>
        <ab type="book">
          <idno type="ISBN-13">978-2-0000-0000-0</idno>
        </ab>
        <ab type="digital_download" subtype="PDF">
          <idno type="DOI">10.0000/purh.test</idno>
        </ab>
      </publicationStmt>
      <sourceDesc><p>Source de test.</p></sourceDesc>
    </fileDesc>
    <profileDesc>
      <langUsage><language ident="fr">français</language></langUsage>
    </profileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group xml:id="chapitre-1" type="chapter" data-page-title="Chapitre compilable">
        <body>
          <head>Chapitre compilable</head>
          <p>Texte avec caractères à échapper : Racine &amp; Port-Royal, 50%, mot_cle, #1.</p>
          <p>Phrase avec une note<note place="foot">Note simple de bas de page.</note>.</p>
          <div type="blockquote">
            <p>Citation bloc.</p>
            <p>Suite de citation.</p>
          </div>
          <list>
            <item><p>Premier élément.</p></item>
            <item><p>Second élément.</p></item>
          </list>
          <figure>
            <graphic url="image-absente.png"/>
            <head>Figure absente</head>
            <p rend="caption">Légende de figure absente.</p>
          </figure>
          <listBibl>
            <head>Bibliographie</head>
            <bibl>Alice Auteur, <title>Ouvrage de test</title>, Rouen, PURH, 2026.</bibl>
          </listBibl>
        </body>
      </group>
    </group>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    return xml_path


def make_runtime_dir() -> Path:
    runtime_dir = Path.cwd() / ".latex-integration-runtime" / uuid.uuid4().hex
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def cleanup_runtime_dir(runtime_dir: Path) -> None:
    def remove_readonly(function, path, exc_info) -> None:
        os.chmod(path, 0o700)
        function(path)

    for _ in range(3):
        try:
            shutil.rmtree(runtime_dir, onexc=remove_readonly)
            return
        except OSError:
            time.sleep(0.2)
    shutil.rmtree(runtime_dir, ignore_errors=True)


def run_purh_compile(xml_path: Path, runtime_dir: Path):
    return PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=True,
        latex_engine="lualatex",
    ).build_from_normalized_tei(xml_path, runtime_dir / "pdf")


def write_one_pixel_png(path: Path) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        checksum = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw_scanline = b"\x00\xff\xff\xff"
    path.write_bytes(
        signature
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw_scanline))
        + chunk(b"IEND", b"")
    )


def write_realistic_metopes_tei(runtime_dir: Path) -> Path:
    images_dir = runtime_dir / "images"
    images_dir.mkdir()
    write_one_pixel_png(images_dir / "figure-reelle.png")
    xml_path = runtime_dir / "metopes.normalized.xml"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="tei-realiste">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type="main">Livre Métopes réaliste</title>
        <title type="sub">Essai de structure PURH</title>
        <editor>
          <persName>
            <forename>Claire</forename>
            <surname>Directrice</surname>
          </persName>
        </editor>
      </titleStmt>
      <publicationStmt>
        <publisher>Presses universitaires de Rouen et du Havre</publisher>
        <pubPlace>Rouen</pubPlace>
        <date type="publishing" when="2026">2026</date>
        <ab type="book">
          <idno type="ISBN-13">978-2-87775-000-0</idno>
        </ab>
        <ab type="digital_download" subtype="PDF">
          <idno type="ISBN">978-2-87775-001-7</idno>
          <idno type="DOI">10.4000/purh.test-realiste</idno>
        </ab>
      </publicationStmt>
      <sourceDesc><p>TEI normalisée de test.</p></sourceDesc>
    </fileDesc>
    <profileDesc>
      <langUsage><language ident="fr">français</language></langUsage>
      <abstract rend="resume"><p>Résumé d'un volume de test pour la chaîne PDF PURH.</p></abstract>
      <abstract rend="4e-couv"><p>Texte de quatrième de couverture pour le test.</p></abstract>
    </profileDesc>
  </teiHeader>
  <text type="book" xml:id="book">
    <front>
      <div type="acknowledgments">
        <head>Remerciements</head>
        <p>Nous remercions les équipes éditoriales.</p>
      </div>
    </front>
    <group type="book">
      <group xml:id="dedicace" type="dedication" data-page-title="Dédicace">
        <body>
          <div type="section1"><head>Dédicace</head><p>À celles et ceux qui lisent.</p></div>
        </body>
      </group>
      <group xml:id="introduction" type="introduction" data-page-title="Introduction générale">
        <body>
          <div type="section1">
            <head>Entrer dans le volume</head>
            <p>Un paragraphe avec <hi rend="italic">italique</hi>, <hi rend="small-caps">PURH</hi> et XVII<hi rend="sup">e</hi> siècle.</p>
            <p>Une note liminaire<note place="foot">Note de l'introduction.</note> accompagne le propos.</p>
          </div>
        </body>
      </group>
      <group xml:id="partie-1" type="part" data-page-title="Première partie">
        <group xml:id="chapitre-1" type="chapter" data-page-title="Premier chapitre">
          <body>
            <div type="section1">
              <head>Section du premier chapitre</head>
              <p>Premier chapitre avec une liste.</p>
              <list>
                <item><p>Premier point.</p></item>
                <item><p>Second point.</p></item>
              </list>
              <div type="section2">
                <head>Sous-section du premier chapitre</head>
                <p>Texte de sous-section.</p>
              </div>
            </div>
          </body>
        </group>
        <group xml:id="chapitre-2" type="chapter" data-page-title="Contribution locale" data-page-subtitle="Sous-titre local" data-page-authors="Alice Locale@@Université de Rouen||Bob Local">
          <body>
            <div type="section1">
              <head>Section de contribution</head>
              <p>Contribution avec caractères spéciaux : Rouen &amp; Le Havre, 30%, mot_cle, #2.</p>
              <div type="blockquote">
                <p>Une citation bloc représentative.</p>
                <p>Sa suite immédiate.</p>
              </div>
              <figure>
                <graphic url="illustration-absente.png"/>
                <head>Illustration absente</head>
                <p rend="caption">Légende éditoriale.</p>
              </figure>
              <figure>
                <graphic url="images/figure-reelle.png"/>
                <head>Figure réelle</head>
                <p rend="caption">Une image minimale réellement compilée.</p>
                <p rend="credits">Image de test.</p>
              </figure>
              <listBibl>
                <head>Bibliographie du chapitre</head>
                <bibl>Alice Locale, <title>Article de test</title>, Rouen, PURH, 2026.</bibl>
              </listBibl>
              <table>
                <head>Tableau de synthèse</head>
                <row>
                  <cell role="label">Notion</cell>
                  <cell role="label">Valeur</cell>
                </row>
                <row>
                  <cell>Volume</cell>
                  <cell>Collectif</cell>
                </row>
                <row>
                  <cell>Éditeur</cell>
                  <cell>PURH</cell>
                </row>
              </table>
            </div>
          </body>
        </group>
      </group>
      <group xml:id="conclusion" type="conclusion" data-page-title="Conclusion">
        <body>
          <div type="section1"><head>Conclusion</head><p>Clôture du volume.</p></div>
        </body>
      </group>
      <group xml:id="bibliographie-generale" type="bibliography" data-page-title="Bibliographie générale">
        <body>
          <listBibl>
            <head>Bibliographie générale</head>
            <bibl>Claire Directrice, <title>Volume collectif</title>, PURH, 2026.</bibl>
            <biblStruct>
              <monogr>
                <author><persName><forename>Blaise</forename><surname>Pascal</surname></persName></author>
                <title level="m">Pensées</title>
                <imprint>
                  <pubPlace>Paris</pubPlace>
                  <publisher>Gallimard</publisher>
                  <date>1976</date>
                </imprint>
                <idno type="ISBN">9782070100010</idno>
              </monogr>
            </biblStruct>
            <biblStruct>
              <analytic>
                <author><persName><forename>Jean</forename><surname>Dupont</surname></persName></author>
                <title level="a">Contribution structurée</title>
              </analytic>
              <monogr>
                <editor><persName><forename>Claire</forename><surname>Directrice</surname></persName></editor>
                <title level="m">Volume collectif</title>
                <imprint>
                  <pubPlace>Rouen</pubPlace>
                  <publisher>PURH</publisher>
                  <date>2026</date>
                  <biblScope unit="page">p. 15-32</biblScope>
                </imprint>
                <idno type="DOI">10.4000/impressions.test</idno>
              </monogr>
            </biblStruct>
            <biblStruct>
              <analytic>
                <author><persName><forename>Marie</forename><surname>Leroy</surname></persName></author>
                <title level="a">Article savant</title>
              </analytic>
              <monogr>
                <title level="j">Revue de test</title>
                <imprint>
                  <biblScope unit="volume">12</biblScope>
                  <biblScope unit="issue">3</biblScope>
                  <date>2025</date>
                  <biblScope unit="page">p. 45-56</biblScope>
                </imprint>
              </monogr>
            </biblStruct>
          </listBibl>
        </body>
      </group>
    </group>
    <back>
      <div type="appendix">
        <head>Annexe documentaire</head>
        <p>Complément documentaire.</p>
      </div>
    </back>
  </text>
</TEI>
""",
        encoding="utf-8",
    )
    return xml_path


def test_purh_style_minimal_document_compiles_with_lualatex() -> None:
    runtime_dir = make_runtime_dir()
    xml_path = write_compile_tei(runtime_dir)
    success = False

    try:
        result = run_purh_compile(xml_path, runtime_dir)

        tex = result.tex_path.read_text(encoding="utf-8")
        log = result.log_path.read_text(encoding="utf-8")

        assert result.success is True, log
        assert result.pdf_path.exists()
        assert result.tex_path.exists()
        assert result.log_path.exists()
        assert result.commands
        assert r"\documentclass[12pt,twoside,openany]{book}" in tex
        assert r"\usepackage[french]{babel}" in tex
        assert r"\pagestyle{fancy}" in tex
        success = True
    finally:
        if success:
            cleanup_runtime_dir(runtime_dir)


def test_purh_style_realistic_metopes_sample_compiles_with_lualatex() -> None:
    runtime_dir = make_runtime_dir()
    xml_path = write_realistic_metopes_tei(runtime_dir)
    success = False

    try:
        result = run_purh_compile(xml_path, runtime_dir)

        tex = result.tex_path.read_text(encoding="utf-8")
        log = result.log_path.read_text(encoding="utf-8")

        assert result.success is True, log
        assert result.pdf_path.exists()
        assert result.tex_path.exists()
        assert result.log_path.exists()
        assert result.commands
        assert r"\documentclass[12pt,twoside,openany]{book}" in tex
        assert r"\usepackage[french]{babel}" in tex
        assert r"\pagestyle{fancy}" in tex
        assert r"\part*{Première partie}" in tex
        assert tex.index(r"\chapter*{Remerciements}") < tex.index(r"\mainmatter")
        assert tex.index(r"\mainmatter") < tex.index(r"\part*{Première partie}")
        assert tex.index(r"\chapter{Premier chapitre}") < tex.index(r"\chapter{Contribution locale}")
        assert tex.index(r"\chapter{Contribution locale}") < tex.index(r"\chapter*{Conclusion}")
        assert tex.index(r"\backmatter") < tex.index(r"\chapter{Annexe documentaire}")
        assert r"\PurhContributors{Alice Locale ; Bob Local}" in tex
        assert r"\includegraphics" in tex
        assert "images/figure-reelle.png" in tex
        assert r"\begin{tabularx}{\linewidth}{XX}" in tex
        assert "Tableau de synthèse" in tex
        assert "ISBN 9782070100010" in tex
        assert r"\enquote{Contribution structurée}" in tex
        assert "https://doi.org/10.4000/impressions.test" in tex
        assert "https://doi.org/https://doi.org" not in tex
        assert "None" not in tex
        assert "Sans titre" not in tex
        assert "{memoir}" not in tex
        assert "polyglossia" not in tex
        success = True
    finally:
        if success:
            cleanup_runtime_dir(runtime_dir)


def test_generated_pdf_is_downloaded_when_lualatex_integration_enabled() -> None:
    runtime_dir = make_runtime_dir()
    xml_path = write_compile_tei(runtime_dir)
    success = False

    try:
        result = SiteBuilder().build_from_master(
            xml_path,
            BuildConfig(output_dir=runtime_dir / "site", pdf_export_mode="latex_pdf"),
        )

        index_html = result.html_path.read_text(encoding="utf-8")
        generated_dir = runtime_dir / "site" / "assets" / "generated"

        assert result.html_path.exists()
        assert (generated_dir / "book.tex").exists()
        assert (generated_dir / "book.pdf").exists()
        assert (generated_dir / "latex_build.log").exists()
        assert (generated_dir / "pdf_build_report.txt").exists()
        assert "Télécharger le LaTeX" in index_html
        assert 'href="assets/generated/book.tex"' in index_html
        assert "Télécharger le PDF généré" in index_html
        assert 'href="assets/generated/book.pdf"' in index_html
        assert 'name="citation_pdf_url" content="assets/generated/book.pdf"' in index_html
        assert "Télécharger le PDF éditeur" not in index_html
        success = True
    finally:
        if success:
            cleanup_runtime_dir(runtime_dir)
