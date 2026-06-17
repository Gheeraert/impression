from __future__ import annotations

import os
from pathlib import Path
import shutil
import uuid

import pytest

from purh_site.latex_renderer import LatexRenderOptions
from purh_site.pdf_builder import PdfBuilder


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


def test_purh_style_minimal_document_compiles_with_lualatex() -> None:
    runtime_dir = Path.cwd() / ".latex-integration-runtime" / uuid.uuid4().hex
    runtime_dir.mkdir(parents=True, exist_ok=False)
    xml_path = write_compile_tei(runtime_dir)

    result = PdfBuilder(
        latex_options=LatexRenderOptions(style="purh"),
        compile_pdf=True,
        latex_engine="lualatex",
    ).build_from_normalized_tei(xml_path, runtime_dir / "pdf")

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
