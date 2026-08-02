from __future__ import annotations

from lxml import etree

from purh_site.reversible import compare_tei_elements, run_tei_latex_tei_roundtrip
from purh_site.utils import TEI_NS, XML_NS

NS = {"tei": TEI_NS, "xml": XML_NS}


BIBL_METADATA_FRAGMENT = (
    '<bibl xmlns="http://www.tei-c.org/ns/1.0" xml:id="bibl-real-001" type="book">'
    '<author><persName><forename>Blaise</forename><surname>Pascal</surname></persName></author>'
    '<title level="m">Les Provinciales</title>'
    '<pubPlace>Paris</pubPlace>'
    '<publisher>Guillaume Desprez</publisher>'
    '<date when="1657">1657</date>'
    '<idno type="ISBN">979-10-240-0000-0</idno>'
    '<address><addrLine>Rue Saint-Jacques</addrLine></address>'
    '<availability status="free"><licence target="https://creativecommons.org/licenses/by/4.0/">CC BY</licence></availability>'
    "</bibl>"
)


BODY_FRAGMENT = (
    '<div xmlns="http://www.tei-c.org/ns/1.0" type="section1" xml:id="sec-real-001">'
    "<head>Port-Royal et la lecture</head>"
    '<p xml:id="p-real-001">En <date when="1670">1670</date>, '
    '<persName ref="#pascal">Pascal</persName> est lu avec '
    '<title level="m">Les Provinciales</title><note place="foot" xml:id="n-real-001">'
    'Voir <bibl>Pascal, <title>Les Provinciales</title>, 1657.</bibl></note>.</p>'
    '<p>Une formule <hi rend="italic">in medias res</hi> renvoie au '
    '<ref target="#chapitre-2">chapitre II</ref><pb n="12"/>suite<lb n="4"/>ligne.</p>'
    '<quote xml:id="q-real-001"><p>Une citation courte.</p></quote>'
    "</div>"
)


COMPLEX_FRAGMENT = (
    '<div xmlns="http://www.tei-c.org/ns/1.0" type="section2" xml:id="complex-real-001">'
    '<list type="unordered"><item n="1">Premier element avec <cit><quote>citation breve</quote>'
    '<bibl>Source breve</bibl></cit>.</item><item n="2">Second element.</item></list>'
    '<figure xml:id="fig-real-001"><head>Figure 1. Port-Royal</head>'
    '<graphic url="port-royal.jpg" width="600" height="400"/></figure>'
    '<table xml:id="tab-real-001" rows="1" cols="2"><row role="label">'
    "<cell>Nom</cell><cell>Valeur avec <hi rend=\"italic\">italique</hi></cell>"
    "</row></table>"
    "</div>"
)


def parse(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


def test_real_metopes_bibliographic_metadata_fragment_round_trips() -> None:
    result = run_tei_latex_tei_roundtrip(parse(BIBL_METADATA_FRAGMENT))
    emitted = result.emitted
    latex = result.latex

    assert result.diagnostics == []
    assert latex
    assert "\\begin{teiBibl}[xmlid={bibl-real-001},type={book}]" in latex
    assert "\\teiAuthor{" in latex
    assert "\\teiPersName{" in latex
    assert "\\teiPublisher{Guillaume Desprez}" in latex
    assert "\\teiIdno[type={ISBN}]{979-10-240-0000-0}" in latex
    assert "\\teiDate[when={1657}]{1657}" in latex
    assert "\\begin{teiElement}[name={forename}]" in latex
    assert "\\begin{teiElement}[name={surname}]" in latex
    assert "\\begin{teiElement}[name={pubPlace}]" in latex
    assert "\\begin{teiElement}[name={availability},status={free}]" in latex
    assert "\\begin{teiElement}[name={licence},target={https://creativecommons.org/licenses/by/4.0/}]" in latex
    assert emitted.get(f"{{{XML_NS}}}id") == "bibl-real-001"
    assert emitted.xpath("boolean(./tei:author/tei:persName/tei:forename)", namespaces=NS)
    assert emitted.xpath("boolean(./tei:author/tei:persName/tei:surname)", namespaces=NS)
    assert emitted.xpath("boolean(./tei:availability[@status='free']/tei:licence)", namespaces=NS)
    assert emitted.xpath("boolean(./tei:address/tei:addrLine)", namespaces=NS)


def test_real_metopes_body_fragment_round_trips() -> None:
    result = run_tei_latex_tei_roundtrip(parse(BODY_FRAGMENT))
    emitted = result.emitted
    latex = result.latex

    assert result.diagnostics == []
    assert latex
    assert "\\begin{teiDiv}[type={section1},xmlid={sec-real-001}]" in latex
    assert "\\teiHead{Port-Royal et la lecture}" in latex
    assert "\\teiP[xmlid={p-real-001}]" in latex
    assert "\\teiDate[when={1670}]{1670}" in latex
    assert "\\teiPersName[ref={\\#pascal}]{Pascal}" in latex
    assert "\\teiTitle[level={m}]{Les Provinciales}" in latex
    assert "\\teiNote[place={foot},xmlid={n-real-001}]" in latex
    assert "\\teiRef[target={\\#chapitre-2}]{chapitre II}" in latex
    assert "\\teiPb[n={12}]" in latex
    assert "\\teiLb[n={4}]" in latex
    assert "\\begin{teiQuote}[xmlid={q-real-001}]" in latex
    assert emitted.xpath("boolean(./tei:p[@xml:id='p-real-001'])", namespaces=NS)
    assert emitted.xpath("boolean(.//tei:note[@place='foot' and @xml:id='n-real-001'])", namespaces=NS)
    assert [etree.QName(child).localname for child in emitted] == ["head", "p", "p", "quote"]


def test_real_metopes_complex_structure_fragment_round_trips() -> None:
    result = run_tei_latex_tei_roundtrip(parse(COMPLEX_FRAGMENT))
    emitted = result.emitted
    latex = result.latex

    assert result.diagnostics == []
    assert latex
    assert "\\begin{teiList}[type={unordered}]" in latex
    assert "\\teiItem[n={1}]" in latex
    assert "\\begin{teiCit}" in latex
    assert "\\begin{teiBibl}" in latex
    assert "\\begin{teiFigure}[xmlid={fig-real-001}]" in latex
    assert "\\teiGraphic[url={port-royal.jpg},width={600},height={400}]" in latex
    assert "\\begin{teiTable}[xmlid={tab-real-001},rows={1},cols={2}]" in latex
    assert "\\begin{teiRow}[role={label}]" in latex
    assert "\\begin{teiCell}" in latex
    assert emitted.xpath("boolean(./tei:list/tei:item[1]/tei:cit/tei:quote)", namespaces=NS)
    assert emitted.xpath("boolean(./tei:figure[@xml:id='fig-real-001']/tei:graphic[@url='port-royal.jpg'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:table[@xml:id='tab-real-001']/tei:row/tei:cell[2]/tei:hi[@rend='italic'])", namespaces=NS)
    assert [etree.QName(child).localname for child in emitted] == ["list", "figure", "table"]


def test_real_metopes_fallback_elements_are_preserved_without_loss() -> None:
    result = run_tei_latex_tei_roundtrip(parse(BIBL_METADATA_FRAGMENT))
    emitted = result.emitted
    latex = result.latex

    assert result.diagnostics == []
    assert "\\begin{teiElement}[name={forename}]" in latex
    assert "\\begin{teiElement}[name={surname}]" in latex
    assert "\\begin{teiElement}[name={address}]" in latex
    assert "\\begin{teiElement}[name={addrLine}]" in latex
    assert "\\begin{teiElement}[name={availability},status={free}]" in latex
    assert "\\begin{teiElement}[name={licence},target={https://creativecommons.org/licenses/by/4.0/}]" in latex
    assert emitted.xpath("string(./tei:author/tei:persName/tei:forename)", namespaces=NS) == "Blaise"
    assert emitted.xpath("string(./tei:author/tei:persName/tei:surname)", namespaces=NS) == "Pascal"
    assert emitted.xpath("string(./tei:address/tei:addrLine)", namespaces=NS) == "Rue Saint-Jacques"
    assert emitted.xpath("string(./tei:availability/tei:licence)", namespaces=NS) == "CC BY"


def test_real_metopes_diagnostics_remain_useful_on_changed_fragment() -> None:
    source = parse(BODY_FRAGMENT)
    result = run_tei_latex_tei_roundtrip(source)
    changed = etree.fromstring(etree.tostring(result.emitted))
    changed.xpath("./tei:p[@xml:id='p-real-001']", namespaces=NS)[0].text = "Texte modifie "
    changed.xpath("./tei:p[@xml:id='p-real-001']/tei:date", namespaces=NS)[0].set("when", "1669")

    diagnostics = compare_tei_elements(source, changed)

    assert result.diagnostics == []
    assert {diagnostic.code for diagnostic in diagnostics} >= {"TEXT_MISMATCH", "ATTR_MISMATCH"}
    assert any(diagnostic.path == "/div/p[2]" for diagnostic in diagnostics)
    assert any(diagnostic.path == "/div/p[2]/date[1]" for diagnostic in diagnostics)
