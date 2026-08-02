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


def test_standalone_block_quote_keeps_block_environment_and_straight_quotes() -> None:
    # A <cit>/<quote> standing alone (not inside <p>/<item>/<note>) is a set-off
    # block quotation: no automatic marks, indentation carries the meaning —
    # matching the HTML XSLT's plain tei:cit -> div.cit-block (not span).
    result = run(
        '<div xmlns="http://www.tei-c.org/ns/1.0"><cit><quote>"Une citation."</quote></cit></div>'
    )

    assert result.diagnostics == []
    assert "\\begin{teiQuote}" in result.latex
    assert "teiQuoteInline" not in result.latex
    assert result.emitted.xpath("string(.//tei:quote)", namespaces=NS) == '"Une citation."'


def test_inline_quote_in_paragraph_uses_enquote_and_stays_inline() -> None:
    # <cit>/<quote> used mid-sentence inside <p> must not force LaTeX's
    # block quote environment (it breaks the paragraph even spliced inside
    # a \teiP{...} argument) — matching the HTML XSLT's tei:p/tei:cit ->
    # span.cit-inline (not div.cit-block). A redundant straight quote typed
    # by hand around the whole quoted text is stripped since \enquote
    # already supplies proper guillemets and would otherwise double up.
    result = run(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Comme le disait Jean, '
        '<cit xml:id="cit1"><quote>"le renard... (La Fontaine)"</quote></cit>, blah.</p>'
    )
    quote = result.emitted.xpath(".//tei:quote", namespaces=NS)[0]

    assert "\\teiQuoteInline{le renard... (La Fontaine)}" in result.latex
    assert "\\begin{teiQuote}" not in result.latex
    # Stripping the redundant straight quotes is a deliberate, one-way
    # normalization (matching the tolerated-whitespace diagnostics already
    # used throughout this pipeline) — reported, not silently discarded.
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "TEXT_MISMATCH"
    assert quote.text == "le renard... (La Fontaine)"


def test_inline_quote_in_list_item_stays_inline() -> None:
    result = run(
        '<list xmlns="http://www.tei-c.org/ns/1.0"><item>Comme le disait Jean, '
        '<cit><quote>"le renard..."</quote></cit>, blah.</item></list>'
    )

    assert "\\teiQuoteInline{le renard...}" in result.latex
    assert "\\begin{teiQuote}" not in result.latex


def test_inline_quote_anywhere_inside_note_stays_inline() -> None:
    # note// in the XSLT means any depth, not just a direct child — an extra
    # wrapping element between <note> and <cit> must still count as inline.
    result = run(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Texte'
        '<note><hi rend="italic"><cit><quote>"Citee"</quote></cit></hi></note>.</p>'
    )

    assert "\\teiQuoteInline{Citee}" in result.latex
    assert "\\begin{teiQuote}" not in result.latex


def test_inline_quote_only_strips_matching_straight_quote_pair() -> None:
    # A single stray straight quote on only one side is ambiguous (could be
    # real content, e.g. a quote-within-the-quote) — leave it untouched
    # rather than guess.
    result = run(
        '<p xmlns="http://www.tei-c.org/ns/1.0">'
        '<cit><quote>"Guillemet ouvrant seul</quote></cit>'
        "</p>"
    )
    quote = result.emitted.xpath(".//tei:quote", namespaces=NS)[0]

    assert '\\teiQuoteInline{"Guillemet ouvrant seul}' in result.latex
    assert quote.text == '"Guillemet ouvrant seul'
    assert result.diagnostics == []


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
