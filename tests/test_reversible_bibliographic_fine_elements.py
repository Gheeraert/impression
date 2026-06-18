from __future__ import annotations

from lxml import etree

from purh_site.reversible import run_tei_latex_tei_roundtrip
from purh_site.utils import TEI_NS, XML_NS


NS = {"tei": TEI_NS, "xml": XML_NS}


def run(xml: str):
    return run_tei_latex_tei_roundtrip(etree.fromstring(xml.encode("utf-8")))


def test_bibl_with_fine_bibliographic_elements_round_trips() -> None:
    result = run(
        '<bibl xmlns="http://www.tei-c.org/ns/1.0" type="book">'
        '<author><persName><forename>Claire</forename><surname>Duras</surname></persName></author>'
        '<title level="m">Ourika</title>'
        "<publisher>PURH</publisher>"
        '<date when="2026">2026</date>'
        '<idno type="ISBN">979-10-000-0000-0</idno>'
        '<biblScope unit="page" from="12" to="18">p. 12-18</biblScope>'
        "</bibl>"
    )
    emitted = result.emitted

    assert result.diagnostics == []
    assert emitted.get("type") == "book"
    assert emitted.xpath("boolean(./tei:author/tei:persName/tei:forename)", namespaces=NS)
    assert emitted.xpath("boolean(./tei:author/tei:persName/tei:surname)", namespaces=NS)
    assert emitted.xpath("boolean(./tei:title[@level='m'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:publisher)", namespaces=NS)
    assert emitted.xpath("boolean(./tei:date[@when='2026'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:idno[@type='ISBN'])", namespaces=NS)
    assert emitted.xpath("boolean(./tei:biblScope[@unit='page' and @from='12' and @to='18'])", namespaces=NS)
    assert [etree.QName(child).localname for child in emitted] == [
        "author",
        "title",
        "publisher",
        "date",
        "idno",
        "biblScope",
    ]


def test_bibliographic_latex_uses_dedicated_macros_and_keeps_nested_fallbacks() -> None:
    result = run(
        '<bibl xmlns="http://www.tei-c.org/ns/1.0">'
        '<author><persName><forename>Claire</forename><surname>Duras</surname></persName></author>'
        '<publisher>PURH</publisher>'
        '<idno type="ISBN">979-10-000-0000-0</idno>'
        "</bibl>"
    )
    latex = result.latex

    assert result.diagnostics == []
    assert "\\teiAuthor{" in latex
    assert "\\teiPublisher{PURH}" in latex
    assert "\\teiIdno[type={ISBN}]{979-10-000-0000-0}" in latex
    assert "name={author}" not in latex
    assert "name={publisher}" not in latex
    assert "name={idno}" not in latex
    assert "\\begin{teiElement}[name={forename}]" in latex
    assert "\\begin{teiElement}[name={surname}]" in latex


def test_bibl_scope_preserves_unit_from_to_and_empty_content_group() -> None:
    result = run(
        '<biblScope xmlns="http://www.tei-c.org/ns/1.0" '
        'xml:id="bs_001" unit="page" from="12" to="18"/>'
    )

    assert result.diagnostics == []
    assert result.latex == r"\teiBiblScope[xmlid={bs\_001},unit={page},from={12},to={18}]{}"
    assert result.emitted.get(f"{{{XML_NS}}}id") == "bs_001"
    assert result.emitted.get("unit") == "page"
    assert result.emitted.get("from") == "12"
    assert result.emitted.get("to") == "18"
    assert result.emitted.text is None


def test_editor_with_role_and_nested_pers_name_round_trips() -> None:
    result = run(
        '<editor xmlns="http://www.tei-c.org/ns/1.0" role="dir">'
        'Direction <persName ref="#p1">Nom</persName>'
        "</editor>"
    )
    emitted = result.emitted

    assert result.diagnostics == []
    assert result.latex.startswith(r"\teiEditor[role={dir}]{Direction \teiPersName[ref={\#p1}]{Nom}}")
    assert emitted.get("role") == "dir"
    assert emitted.text == "Direction "
    assert emitted.xpath("boolean(./tei:persName[@ref='#p1'])", namespaces=NS)


def test_fine_bibliographic_attributes_survive() -> None:
    result = run(
        '<author xmlns="http://www.tei-c.org/ns/1.0" xml:id="a_001" xml:lang="fr" '
        'type="person" subtype="primary" role="main" n="1">Autrice</author>'
    )
    emitted = result.emitted

    assert result.diagnostics == []
    assert emitted.get(f"{{{XML_NS}}}id") == "a_001"
    assert emitted.get(f"{{{XML_NS}}}lang") == "fr"
    assert emitted.get("type") == "person"
    assert emitted.get("subtype") == "primary"
    assert emitted.get("role") == "main"
    assert emitted.get("n") == "1"
    assert emitted.text == "Autrice"
    assert "\\teiAuthor[" in result.latex
    assert "name={author}" not in result.latex
