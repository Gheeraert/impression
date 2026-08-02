from __future__ import annotations

import pytest
from lxml import etree

from purh_site.reversible import LatexParseError, read_latex_document, run_tei_latex_tei_roundtrip
from purh_site.utils import TEI_NS, XML_NS

NS = {"tei": TEI_NS, "xml": XML_NS}


def run(xml: str):
    return run_tei_latex_tei_roundtrip(etree.fromstring(xml.encode("utf-8")))


def test_ptr_target_round_trips_with_empty_macro() -> None:
    result = run('<ptr xmlns="http://www.tei-c.org/ns/1.0" target="#x" xml:id="ptr_001"/>')

    assert result.diagnostics == []
    assert result.emitted.tag == f"{{{TEI_NS}}}ptr"
    assert result.emitted.get("target") == "#x"
    assert result.emitted.get(f"{{{XML_NS}}}id") == "ptr_001"
    assert result.emitted.text is None
    assert len(result.emitted) == 0
    assert result.latex == r"\teiPtr[target={\#x},xmlid={ptr_001}]"
    assert "{}" not in result.latex
    assert "teiElement" not in result.latex


def test_lb_n_round_trips_with_empty_macro() -> None:
    result = run('<lb xmlns="http://www.tei-c.org/ns/1.0" n="3" ed="A"/>')

    assert result.diagnostics == []
    assert result.emitted.tag == f"{{{TEI_NS}}}lb"
    assert result.emitted.get("n") == "3"
    assert result.emitted.get("ed") == "A"
    assert result.latex == r"\teiLb[n={3},ed={A}]"
    assert "{}" not in result.latex


def test_lb_followed_by_elision_bracket_round_trips() -> None:
    # Real bug, found on a genuine Metopes book: a scholarly elision bracket
    # ("[…]") directly after <lb/> with no separating space made the reader
    # mistake the escaped bracket for \teiLb's own option list ("Expected
    # '=' after option key"), then — once "[" was escaped as literal "{[}"
    # — for braced content passed to it ("must not have braced content").
    result = run(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Texte<lb/>[…] la suite.</p>'
    )

    assert result.diagnostics == []
    assert result.emitted.xpath("string(.)") == "Texte[…] la suite."


def test_bare_lb_glued_to_following_word_round_trips() -> None:
    # Real bug, found on a genuine Metopes book (poetry, no space before the
    # next line): "\teiLb" is a control WORD — TeX consumes every letter
    # immediately following it into the control sequence's own name, so a
    # bare \teiLb directly before "Parce" becomes the bogus, undefined
    # "\teiLbParce" ("Undefined control sequence") unless something that
    # isn't a letter (here "{}") stands between them.
    result = run(
        '<p xmlns="http://www.tei-c.org/ns/1.0">'
        "Et j’aime l’ortie,<lb/>Parce qu’on les hait ;<lb/>Et que rien ne leur plaît"
        "</p>"
    )

    assert result.diagnostics == []
    assert r"\teiLb{}Parce" in result.latex
    assert "".join(result.emitted.itertext()) == (
        "Et j’aime l’ortie,Parce qu’on les hait ;Et que rien ne leur plaît"
    )


def test_pb_n_round_trips_with_empty_macro() -> None:
    result = run('<pb xmlns="http://www.tei-c.org/ns/1.0" n="12" facs="page12.png"/>')

    assert result.diagnostics == []
    assert result.emitted.tag == f"{{{TEI_NS}}}pb"
    assert result.emitted.get("n") == "12"
    assert result.emitted.get("facs") == "page12.png"
    assert result.latex == r"\teiPb[n={12},facs={page12.png}]"
    assert "{}" not in result.latex


def test_milestones_keep_exact_position_in_mixed_content() -> None:
    result = run(
        '<p xmlns="http://www.tei-c.org/ns/1.0">'
        'Avant<pb n="12"/>apres <lb n="3"/>ligne <ptr target="#x"/>.'
        "</p>"
    )
    emitted = result.emitted

    assert result.diagnostics == []
    assert [etree.QName(child).localname for child in emitted] == ["pb", "lb", "ptr"]
    assert emitted.text == "Avant"
    assert emitted[0].get("n") == "12"
    assert emitted[0].tail == "apres "
    assert emitted[1].get("n") == "3"
    assert emitted[1].tail == "ligne "
    assert emitted[2].get("target") == "#x"
    assert emitted[2].tail == "."
    assert "".join(emitted.itertext()) == "Avantapres ligne ."
    assert r"\teiPb[n={12}]" in result.latex
    assert r"\teiLb[n={3}]" in result.latex
    assert r"\teiPtr[target={\#x}]" in result.latex
    assert "name={pb}" not in result.latex
    assert "name={lb}" not in result.latex
    assert "name={ptr}" not in result.latex


def test_milestone_attributes_survive() -> None:
    result = run(
        '<p xmlns="http://www.tei-c.org/ns/1.0">'
        '<pb xml:id="pb_001" xml:lang="fr" n="12" ed="A" facs="page12.png" rend="recto" rendition="#r1"/>'
        "</p>"
    )
    pb = result.emitted.xpath("./tei:pb", namespaces=NS)[0]

    assert result.diagnostics == []
    assert pb.get(f"{{{XML_NS}}}id") == "pb_001"
    assert pb.get(f"{{{XML_NS}}}lang") == "fr"
    assert pb.get("n") == "12"
    assert pb.get("ed") == "A"
    assert pb.get("facs") == "page12.png"
    assert pb.get("rend") == "recto"
    assert pb.get("rendition") == "#r1"
    assert "xmlid={pb_001}" in result.latex
    assert "xmllang={fr}" in result.latex
    assert "rendition={\\#r1}" in result.latex


def test_empty_macro_with_braced_content_is_rejected_for_pb() -> None:
    with pytest.raises(LatexParseError, match=r"\\teiPb.*must not have braced content"):
        read_latex_document(r"\teiPb[n={12}]{contenu interdit}")


def test_empty_macro_with_braced_content_is_rejected_for_ptr() -> None:
    with pytest.raises(LatexParseError, match=r"\\teiPtr.*must not have braced content"):
        read_latex_document(r"\teiPtr[target={\#x}]{texte}")


def test_braced_empty_paragraph_round_trips_without_diagnostics() -> None:
    result = run('<p xmlns="http://www.tei-c.org/ns/1.0"/>')

    assert result.diagnostics == []
    assert result.latex == r"\teiP{}"
    assert result.emitted.tag == f"{{{TEI_NS}}}p"
    assert result.emitted.text is None
    assert len(result.emitted) == 0


def test_braced_empty_head_round_trips_without_error() -> None:
    result = run('<head xmlns="http://www.tei-c.org/ns/1.0"/>')

    assert result.diagnostics == []
    assert result.latex == r"\teiHead{}"
    assert result.emitted.tag == f"{{{TEI_NS}}}head"
    assert result.emitted.text is None


def test_braced_empty_hi_preserves_attribute() -> None:
    result = run('<hi xmlns="http://www.tei-c.org/ns/1.0" rend="italic"/>')

    assert result.diagnostics == []
    assert result.latex == r"\teiHi[rend={italic}]{}"
    assert result.emitted.tag == f"{{{TEI_NS}}}hi"
    assert result.emitted.get("rend") == "italic"
    assert result.emitted.text is None
