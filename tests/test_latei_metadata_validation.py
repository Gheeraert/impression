from __future__ import annotations

"""Validation des métadonnées (référentiel PURH v0.6 §8.3, P0 item 1-2) :
balisage littéral échappé et contributeurs dupliqués, détectés — jamais
corrigés silencieusement, ce sont des défauts de source. Confirmé sur le
vrai livre *Dissimuler pour mieux régner* : le sous-titre contient
littéralement "<em>...</em>" (chevrons échappés dans la source XML) et
"Anaïs Lebreton" apparaît deux fois comme directrice scientifique."""

from pathlib import Path

from lxml import etree

from purh_site.latei_metadata import LateiMetadata, extract_latei_metadata
from purh_site.latei_metadata_validation import validate_latei_metadata
from purh_site.reversible_integration import run_reversible_export_for_file

_DISSIMULER_LIVRE_XML = Path("tests/fixtures/commons-publishing/dissimuler/xml/Dissimuler_LIVRE.xml")


def test_literal_markup_detected_in_subtitle() -> None:
    metadata = LateiMetadata(title="Titre", subtitle="<em>Sous-titre</em> avec balise litterale")
    diagnostics = validate_latei_metadata(metadata)

    codes = [d.code for d in diagnostics]
    assert "LITERAL_MARKUP_IN_METADATA" in codes
    diag = next(d for d in diagnostics if d.code == "LITERAL_MARKUP_IN_METADATA")
    assert diag.path == "metadata/subtitle"
    assert "<em>" in diag.message


def test_clean_subtitle_raises_no_literal_markup_diagnostic() -> None:
    metadata = LateiMetadata(title="Titre", subtitle="Un sous-titre tout a fait normal")
    diagnostics = validate_latei_metadata(metadata)

    assert not any(d.code == "LITERAL_MARKUP_IN_METADATA" for d in diagnostics)


def test_duplicate_director_detected() -> None:
    metadata = LateiMetadata(title="Titre", directors=["Anais Lebreton", "Anais Lebreton"])
    diagnostics = validate_latei_metadata(metadata)

    codes = [d.code for d in diagnostics]
    assert "DUPLICATE_CONTRIBUTOR" in codes
    diag = next(d for d in diagnostics if d.code == "DUPLICATE_CONTRIBUTOR")
    assert diag.path == "metadata/director"
    assert "2 fois" in diag.message


def test_duplicate_detection_is_whitespace_and_case_insensitive() -> None:
    metadata = LateiMetadata(title="Titre", authors=["Jean   Dupont", "jean dupont"])
    diagnostics = validate_latei_metadata(metadata)

    assert any(d.code == "DUPLICATE_CONTRIBUTOR" and d.path == "metadata/author" for d in diagnostics)


def test_distinct_contributors_raise_no_duplicate_diagnostic() -> None:
    metadata = LateiMetadata(title="Titre", authors=["Jean Dupont", "Marie Martin"])
    diagnostics = validate_latei_metadata(metadata)

    assert not any(d.code == "DUPLICATE_CONTRIBUTOR" for d in diagnostics)


def test_validation_does_not_silently_alter_metadata() -> None:
    """The validator only reports — it must never mutate the metadata it
    receives (no silent dedup, no stripped tags): the source stays the
    single source of truth, to be corrected upstream by an editor."""
    metadata = LateiMetadata(
        title="Titre",
        subtitle="<em>x</em>",
        directors=["Anais Lebreton", "Anais Lebreton"],
    )
    validate_latei_metadata(metadata)

    assert metadata.subtitle == "<em>x</em>"
    assert metadata.directors == ["Anais Lebreton", "Anais Lebreton"]


def test_real_dissimuler_book_triggers_both_known_defects() -> None:
    root = etree.parse(str(_DISSIMULER_LIVRE_XML)).getroot()
    metadata = extract_latei_metadata(root)
    diagnostics = validate_latei_metadata(metadata)

    codes = {d.code for d in diagnostics}
    assert "LITERAL_MARKUP_IN_METADATA" in codes
    assert "DUPLICATE_CONTRIBUTOR" in codes


def test_export_writes_metadata_diagnostics_without_failing_the_build(tmp_path: Path) -> None:
    xml_path = tmp_path / "book.xml"
    xml_path.write_text(
        """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type="main">Livre</title>
        <title type="sub">&lt;em&gt;Sous-titre&lt;/em&gt; echappe</title>
        <author role="pbd"><persName><forename>Jean</forename><surname>Dupont</surname></persName></author>
        <author role="pbd"><persName><forename>Jean</forename><surname>Dupont</surname></persName></author>
      </titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p/></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text><body><div><p>Texte.</p></div></body></text>
</TEI>""",
        encoding="utf-8",
    )
    result = run_reversible_export_for_file(xml_path, tmp_path / "out", compile_pdf=False)

    assert result.metadata_diagnostics_count == 2
    assert result.metadata_diagnostics_path.exists()
    content = result.metadata_diagnostics_path.read_text(encoding="utf-8")
    assert "LITERAL_MARKUP_IN_METADATA" in content
    assert "DUPLICATE_CONTRIBUTOR" in content
    # Metadata diagnostics are a separate, non-blocking channel: the
    # round-trip export itself is unaffected by messy source metadata.
    assert result.success is True
    assert result.diagnostics_count == 0
