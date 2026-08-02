from __future__ import annotations

from lxml import etree

from purh_site.reversible import run_tei_latex_tei_roundtrip
from purh_site.utils import TEI_NS, XML_NS

NS = {"tei": TEI_NS, "xml": XML_NS}


def run(xml: str):
    return run_tei_latex_tei_roundtrip(etree.fromstring(xml.encode("utf-8")))


def test_q_simple_in_paragraph_round_trips_with_dedicated_macro() -> None:
    result = run(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Un <q type="spoken">mot cite</q>.</p>'
    )
    q = result.emitted.xpath("./tei:q", namespaces=NS)[0]

    assert result.diagnostics == []
    assert "\\teiQ[type={spoken}]{mot cite}" in result.latex
    assert "name={q}" not in result.latex
    assert q.get("type") == "spoken"
    assert q.text == "mot cite"
    assert q.tail == "."


def test_said_preserves_who_and_uses_dedicated_macro() -> None:
    result = run(
        '<p xmlns="http://www.tei-c.org/ns/1.0">'
        '<said who="#speaker" source="#src1">Paroles</said>'
        "</p>"
    )
    said = result.emitted.xpath("./tei:said", namespaces=NS)[0]

    assert result.diagnostics == []
    assert "\\teiSaid[who={\\#speaker},source={\\#src1}]{Paroles}" in result.latex
    assert "name={said}" not in result.latex
    assert said.get("who") == "#speaker"
    assert said.get("source") == "#src1"


def test_cit_with_quote_and_bibl_preserves_child_order() -> None:
    result = run(
        '<cit xmlns="http://www.tei-c.org/ns/1.0" type="example" xml:id="cit_001">'
        "<quote>Une citation</quote>"
        '<bibl source="#src1">Source courte</bibl>'
        "</cit>"
    )

    assert result.diagnostics == []
    assert "\\begin{teiCit}[type={example},xmlid={cit_001}]" in result.latex
    assert "\\begin{teiBibl}[source={\\#src1}]" in result.latex
    assert "name={cit}" not in result.latex
    assert "name={bibl}" not in result.latex
    assert [etree.QName(child).localname for child in result.emitted] == ["quote", "bibl"]
    assert result.emitted.get(f"{{{XML_NS}}}id") == "cit_001"
    assert result.emitted.xpath("boolean(./tei:bibl[@source='#src1'])", namespaces=NS)


def test_bibl_with_structured_children_keeps_children_and_specialized_bibl_macros() -> None:
    result = run(
        '<bibl xmlns="http://www.tei-c.org/ns/1.0" xml:lang="fr" type="book">'
        '<title level="m">Titre</title>, '
        "<author>Autrice</author>, "
        '<date when="2020">2020</date>, '
        '<idno type="isbn">123</idno>'
        "</bibl>"
    )

    assert result.diagnostics == []
    assert "\\begin{teiBibl}[xmllang={fr},type={book}]" in result.latex
    assert "\\teiTitle[level={m}]{Titre}" in result.latex
    assert "\\teiDate[when={2020}]{2020}" in result.latex
    assert "\\teiAuthor{Autrice}" in result.latex
    assert "\\teiIdno[type={isbn}]{123}" in result.latex
    assert result.emitted.get(f"{{{XML_NS}}}lang") == "fr"
    assert result.emitted.get("type") == "book"
    assert result.emitted.xpath("boolean(./tei:author)", namespaces=NS)
    assert result.emitted.xpath("boolean(./tei:idno[@type='isbn'])", namespaces=NS)


def test_citation_bibliography_attributes_survive() -> None:
    result = run(
        '<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_001" xml:lang="fr">'
        '<q xml:id="q_001" source="#src" corresp="#c" resp="#ed" cert="high">Texte</q>'
        '<said who="#speaker" rend="italic">Dit</said>'
        "</p>"
    )
    q = result.emitted.xpath("./tei:q", namespaces=NS)[0]
    said = result.emitted.xpath("./tei:said", namespaces=NS)[0]

    assert result.diagnostics == []
    assert result.emitted.get(f"{{{XML_NS}}}id") == "p_001"
    assert result.emitted.get(f"{{{XML_NS}}}lang") == "fr"
    assert q.get(f"{{{XML_NS}}}id") == "q_001"
    assert q.get("source") == "#src"
    assert q.get("corresp") == "#c"
    assert q.get("resp") == "#ed"
    assert q.get("cert") == "high"
    assert said.get("who") == "#speaker"
    assert said.get("rend") == "italic"
