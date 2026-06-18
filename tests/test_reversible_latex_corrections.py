from __future__ import annotations

import pytest
from lxml import etree

from purh_site.reversible import (
    LatexParseError,
    read_latex_document,
    read_tei_element,
    write_latex,
    write_tei_element,
)
from purh_site.utils import TEI_NS, XML_NS


NS = {"tei": TEI_NS, "xml": XML_NS}


def corrected_tei(source_xml: str, expected_latex: str, corrected_latex: str) -> etree._Element:
    source = etree.fromstring(source_xml.encode("utf-8"))
    latex = write_latex(read_tei_element(source))
    assert latex == expected_latex
    return write_tei_element(read_latex_document(corrected_latex))


def test_simple_text_correction_returns_to_tei() -> None:
    emitted = corrected_tei(
        '<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_001">Ancien texte.</p>',
        r"\teiP[xmlid={p\_001}]{Ancien texte.}",
        r"\teiP[xmlid={p\_001}]{Nouveau texte.}",
    )

    assert emitted.tag == f"{{{TEI_NS}}}p"
    assert emitted.get(f"{{{XML_NS}}}id") == "p_001"
    assert emitted.text == "Nouveau texte."
    assert len(emitted) == 0


def test_inline_hi_text_correction_preserves_rend() -> None:
    emitted = corrected_tei(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Un <hi rend="italic">ancien</hi> mot.</p>',
        r"\teiP{Un \teiHi[rend={italic}]{ancien} mot.}",
        r"\teiP{Un \teiHi[rend={italic}]{nouveau} mot.}",
    )
    hi = emitted.xpath("./tei:hi", namespaces=NS)[0]

    assert emitted.text == "Un "
    assert hi.get("rend") == "italic"
    assert hi.text == "nouveau"
    assert hi.tail == " mot."


def test_note_correction_preserves_place_and_xml_id() -> None:
    emitted = corrected_tei(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Texte<note place="foot" xml:id="n_001">Ancienne note.</note>.</p>',
        r"\teiP{Texte\teiNote[place={foot},xmlid={n\_001}]{Ancienne note.}.}",
        r"\teiP{Texte\teiNote[place={foot},xmlid={n\_001}]{Nouvelle note.}.}",
    )
    note = emitted.xpath("./tei:note", namespaces=NS)[0]

    assert emitted.text == "Texte"
    assert note.get("place") == "foot"
    assert note.get(f"{{{XML_NS}}}id") == "n_001"
    assert note.text == "Nouvelle note."
    assert note.tail == "."


def test_head_correction_preserves_div_attributes_and_structure() -> None:
    emitted = corrected_tei(
        '<div xmlns="http://www.tei-c.org/ns/1.0" type="chapter" xml:id="ch_001">'
        "<head>Ancien titre</head>"
        "<p>Texte.</p>"
        "</div>",
        "\\begin{teiDiv}[type={chapter},xmlid={ch\\_001}]\n"
        "\\teiHead{Ancien titre}\\teiP{Texte.}\n"
        "\\end{teiDiv}",
        "\\begin{teiDiv}[type={chapter},xmlid={ch\\_001}]\n"
        "\\teiHead{Nouveau titre}\\teiP{Texte.}\n"
        "\\end{teiDiv}",
    )

    assert emitted.get("type") == "chapter"
    assert emitted.get(f"{{{XML_NS}}}id") == "ch_001"
    assert [etree.QName(child).localname for child in emitted] == ["head", "p"]
    assert emitted.xpath("string(./tei:head)", namespaces=NS) == "Nouveau titre"
    assert emitted.xpath("string(./tei:p)", namespaces=NS) == "Texte."


def test_controlled_attribute_correction_updates_ref_target() -> None:
    emitted = corrected_tei(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Voir <ref target="#ancien">reference</ref>.</p>',
        r"\teiP{Voir \teiRef[target={\#ancien}]{reference}.}",
        r"\teiP{Voir \teiRef[target={\#nouveau}]{reference}.}",
    )
    ref = emitted.xpath("./tei:ref", namespaces=NS)[0]

    assert ref.get("target") == "#nouveau"
    assert ref.text == "reference"
    assert ref.tail == "."


def test_controlled_attribute_correction_updates_hi_rend() -> None:
    emitted = corrected_tei(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Un <hi rend="italic">mot</hi>.</p>',
        r"\teiP{Un \teiHi[rend={italic}]{mot}.}",
        r"\teiP{Un \teiHi[rend={small-caps}]{mot}.}",
    )
    hi = emitted.xpath("./tei:hi", namespaces=NS)[0]

    assert hi.get("rend") == "small-caps"
    assert hi.text == "mot"


def test_free_latex_macro_introduced_by_editor_is_rejected() -> None:
    with pytest.raises(LatexParseError):
        read_latex_document(r"\teiP{Texte \emph{non contrôlé}.}")
