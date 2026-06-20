from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from purh_site.gui import latei_body_restored_stem
from purh_site.reversible import compare_tei_elements, read_tei_element, write_latex
from purh_site.reversible.latex_reader import LatexParseError
from purh_site.reversible_integration import restore_xml_from_latei_body


TEI_NS = "http://www.tei-c.org/ns/1.0"


def parse_xml(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


def test_restore_xml_from_latei_body_round_trips_fragment(tmp_path: Path) -> None:
    source = parse_xml(
        f"""<p xmlns="{TEI_NS}" xml:id="p_001" xml:lang="fr">
        Un <hi rend="italic">mot</hi> avec une <ref target="#x">référence</ref>.
        </p>"""
    )
    latei_body = write_latex(read_tei_element(source))
    body_path = tmp_path / "fragment.latei_body.tex"
    output_path = tmp_path / "fragment.restored.xml"
    body_path.write_text(latei_body, encoding="utf-8")

    restored_path = restore_xml_from_latei_body(body_path, output_path)
    restored = etree.parse(str(restored_path)).getroot()

    assert restored_path == output_path
    assert compare_tei_elements(source, restored) == []


def test_restore_xml_from_latei_body_rejects_invalid_latei(tmp_path: Path) -> None:
    body_path = tmp_path / "bad.latei_body.tex"
    body_path.write_text(r"\teiP{Texte \emph{non contrôlé}.}", encoding="utf-8")

    with pytest.raises(LatexParseError):
        restore_xml_from_latei_body(body_path, tmp_path / "bad.restored.xml")


def test_latei_body_restored_stem_removes_only_body_suffix() -> None:
    assert latei_body_restored_stem(Path("book.latei_body.tex")) == "book"
    assert latei_body_restored_stem(Path("notes.tex")) == "notes"
