from __future__ import annotations

from lxml import etree

from purh_site.reversible import run_tei_latex_tei_roundtrip
from purh_site.utils import TEI_NS, XML_NS

NS = {"tei": TEI_NS, "xml": XML_NS}


REALISTIC_FRAGMENT = (
    '<div xmlns="http://www.tei-c.org/ns/1.0" type="chapter" xml:id="ch_real_001">'
    "<head>Chapitre premier</head>"
    '<p xml:id="p_real_001">En <date when="1857">1857</date>, '
    '<persName ref="#baudelaire">Baudelaire</persName> publie '
    '<title level="m">Les Fleurs du mal</title> à '
    '<placeName ref="#paris">Paris</placeName>'
    '<note place="foot" xml:id="n_real_001">Voir <bibl>Edition originale</bibl>.</note>.'
    "</p>"
    '<p xml:id="p_real_002">Ce passage contient <hi rend="italic">un terme souligne</hi> '
    'et une <ref target="#note_editoriale">reference interne</ref>.</p>'
    '<quote xml:id="q_real_001">'
    '<p>Une citation avec <hi rend="italic">emphase</hi> et '
    '<cit><quote>citation imbriquee</quote><bibl>Source breve</bibl></cit>.</p>'
    "</quote>"
    '<list type="ordered">'
    '<item n="1">Premier item avec <title level="a">titre article</title>.</item>'
    '<item n="2">Second item avec <persName ref="#p1">un nom</persName>.</item>'
    "</list>"
    "</div>"
)


def test_realistic_commons_publishing_fragment_round_trips_without_diagnostics() -> None:
    result = run_tei_latex_tei_roundtrip(etree.fromstring(REALISTIC_FRAGMENT.encode("utf-8")))
    emitted = result.emitted

    assert result.diagnostics == []
    assert emitted.get(f"{{{XML_NS}}}id") == "ch_real_001"
    assert emitted.get("type") == "chapter"
    assert emitted.xpath("boolean(./tei:p[@xml:id='p_real_001'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:p[@xml:id='p_real_002'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:quote[@xml:id='q_real_001'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:hi[@rend='italic'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:ref[@target='#note_editoriale'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:note[@place='foot' and @xml:id='n_real_001'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:list[@type='ordered']/tei:item[@n='1'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:list[@type='ordered']/tei:item[@n='2'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:title[@level='m'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:persName[@ref='#baudelaire'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:placeName[@ref='#paris'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:date[@when='1857'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:bibl)", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:cit)", namespaces=NS)
    assert [etree.QName(child).localname for child in emitted] == ["head", "p", "p", "quote", "list"]
    assert "".join(emitted.xpath("./tei:p[@xml:id='p_real_001']//text()", namespaces=NS)).startswith(
        "En 1857, Baudelaire publie Les Fleurs du mal"
    )


def test_realistic_fragment_latex_uses_specialized_macros_and_generic_fallbacks() -> None:
    result = run_tei_latex_tei_roundtrip(etree.fromstring(REALISTIC_FRAGMENT.encode("utf-8")))
    latex = result.latex

    assert "\\begin{teiDiv}[type={chapter},xmlid={ch_real_001}]" in latex
    assert "\\teiHead{Chapitre premier}" in latex
    assert "\\teiP[xmlid={p_real_001}]" in latex
    assert "\\teiHi[rend={italic}]" in latex
    assert "\\teiNote[place={foot},xmlid={n_real_001}]" in latex
    assert "\\teiRef[internaltarget={note_editoriale}]" in latex
    assert "\\begin{teiQuote}[xmlid={q_real_001}]" in latex
    assert "\\begin{teiList}[type={ordered}]" in latex
    assert "\\teiItem[n={1}]" in latex
    assert "\\teiItem[n={2}]" in latex
    assert "\\teiTitle[level={m}]" in latex
    assert "\\teiTitle[level={a}]" in latex
    assert "\\teiPersName[ref={\\#baudelaire}]" in latex
    assert "\\teiPersName[ref={\\#p1}]" in latex
    assert "\\teiPlaceName[ref={\\#paris}]" in latex
    assert "\\teiDate[when={1857}]" in latex
    assert "\\begin{teiBibl}" in latex
    assert "\\begin{teiCit}" in latex
