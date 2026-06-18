from __future__ import annotations

from lxml import etree

from purh_site.reversible import run_tei_latex_tei_roundtrip
from purh_site.utils import TEI_NS, XML_NS


NS = {"tei": TEI_NS, "xml": XML_NS}


def run(xml: str):
    return run_tei_latex_tei_roundtrip(etree.fromstring(xml.encode("utf-8")))


def test_simple_table_two_rows_two_cells_round_trips() -> None:
    result = run(
        '<table xmlns="http://www.tei-c.org/ns/1.0" xml:id="tab_001" rows="2" cols="2">'
        '<row role="label">'
        "<cell>Nom</cell>"
        "<cell>Valeur</cell>"
        "</row>"
        "<row>"
        "<cell><p>Premier</p></cell>"
        '<cell>Second avec <hi rend="italic">italique</hi></cell>'
        "</row>"
        "</table>"
    )
    emitted = result.emitted

    assert result.diagnostics == []
    assert emitted.tag == f"{{{TEI_NS}}}table"
    assert emitted.get(f"{{{XML_NS}}}id") == "tab_001"
    assert emitted.get("rows") == "2"
    assert emitted.get("cols") == "2"
    assert [etree.QName(child).localname for child in emitted] == ["row", "row"]
    assert [etree.QName(child).localname for child in emitted[0]] == ["cell", "cell"]
    assert [etree.QName(child).localname for child in emitted[1]] == ["cell", "cell"]
    assert emitted[0].get("role") == "label"
    assert emitted.xpath("string(./tei:row[1]/tei:cell[1])", namespaces=NS) == "Nom"
    assert emitted.xpath("string(./tei:row[1]/tei:cell[2])", namespaces=NS) == "Valeur"
    assert emitted.xpath("boolean(./tei:row[2]/tei:cell[1]/tei:p)", namespaces=NS)
    assert emitted.xpath("boolean(./tei:row[2]/tei:cell[2]/tei:hi[@rend='italic'])", namespaces=NS)


def test_table_latex_uses_semantic_environments_not_generic_fallback() -> None:
    result = run(
        '<table xmlns="http://www.tei-c.org/ns/1.0" rows="1" cols="1">'
        "<row><cell>Valeur</cell></row>"
        "</table>"
    )

    assert result.diagnostics == []
    assert "\\begin{teiTable}[rows={1},cols={1}]" in result.latex
    assert "\\begin{teiRow}" in result.latex
    assert "\\begin{teiCell}" in result.latex
    assert "name={table}" not in result.latex
    assert "name={row}" not in result.latex
    assert "name={cell}" not in result.latex
    assert "tabular" not in result.latex
    assert "longtable" not in result.latex


def test_table_attributes_are_preserved() -> None:
    result = run(
        '<table xmlns="http://www.tei-c.org/ns/1.0" xml:id="tab_002" xml:lang="fr" '
        'rows="3" cols="2" role="data" rend="compact" rendition="#table-rend" n="A">'
        '<row role="label"><cell role="label">Nom</cell><cell role="label">Valeur</cell></row>'
        "</table>"
    )
    emitted = result.emitted
    first_cell = emitted.xpath("./tei:row/tei:cell[1]", namespaces=NS)[0]

    assert result.diagnostics == []
    assert emitted.get(f"{{{XML_NS}}}id") == "tab_002"
    assert emitted.get(f"{{{XML_NS}}}lang") == "fr"
    assert emitted.get("rows") == "3"
    assert emitted.get("cols") == "2"
    assert emitted.get("role") == "data"
    assert emitted.get("rend") == "compact"
    assert emitted.get("rendition") == "#table-rend"
    assert emitted.get("n") == "A"
    assert emitted[0].get("role") == "label"
    assert first_cell.get("role") == "label"


def test_cell_can_contain_paragraph_and_mixed_content() -> None:
    result = run(
        '<table xmlns="http://www.tei-c.org/ns/1.0">'
        "<row>"
        '<cell><p>Texte <ref target="#x">reference</ref>.</p></cell>'
        '<cell>Mixte <hi rend="italic">italique</hi><note place="foot" xml:id="n1">Note</note>.</cell>'
        "</row>"
        "</table>"
    )
    emitted = result.emitted
    second_cell = emitted.xpath("./tei:row/tei:cell[2]", namespaces=NS)[0]
    hi = second_cell.xpath("./tei:hi", namespaces=NS)[0]
    note = second_cell.xpath("./tei:note", namespaces=NS)[0]

    assert result.diagnostics == []
    assert emitted.xpath("boolean(./tei:row/tei:cell[1]/tei:p/tei:ref[@target='#x'])", namespaces=NS)
    assert second_cell.text == "Mixte "
    assert hi.get("rend") == "italic"
    assert hi.text == "italique"
    assert hi.tail is None
    assert note.get("place") == "foot"
    assert note.get(f"{{{XML_NS}}}id") == "n1"
    assert note.text == "Note"
    assert note.tail == "."


def test_table_preserves_row_and_cell_order() -> None:
    result = run(
        '<table xmlns="http://www.tei-c.org/ns/1.0">'
        '<row n="1"><cell n="a">A1</cell><cell n="b">B1</cell></row>'
        '<row n="2"><cell n="a">A2</cell><cell n="b">B2</cell></row>'
        "</table>"
    )
    emitted = result.emitted

    assert result.diagnostics == []
    assert [row.get("n") for row in emitted.xpath("./tei:row", namespaces=NS)] == ["1", "2"]
    assert [cell.text for cell in emitted.xpath("./tei:row[1]/tei:cell", namespaces=NS)] == ["A1", "B1"]
    assert [cell.text for cell in emitted.xpath("./tei:row[2]/tei:cell", namespaces=NS)] == ["A2", "B2"]
