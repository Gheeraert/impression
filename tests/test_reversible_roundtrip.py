from __future__ import annotations

from lxml import etree

from purh_site.reversible import (
    Diagnostic,
    RoundTripResult,
    compare_tei_elements,
    run_tei_latex_tei_roundtrip,
    tei_latex_tei_roundtrip,
)
from purh_site.utils import TEI_NS, XML_NS


def parse_tei(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


def diagnostic_codes(diagnostics: list[Diagnostic]) -> list[str]:
    return [diagnostic.code for diagnostic in diagnostics]


def assert_clean_roundtrip(xml: str) -> RoundTripResult:
    result = run_tei_latex_tei_roundtrip(parse_tei(xml))
    assert result.diagnostics == []
    assert isinstance(result.latex, str)
    assert result.first_tree.local_name == result.second_tree.local_name
    return result


def test_roundtrip_function_returns_emitted_tei_element() -> None:
    emitted = tei_latex_tei_roundtrip(
        parse_tei('<p xmlns="http://www.tei-c.org/ns/1.0">Texte</p>')
    )

    assert emitted.tag == f"{{{TEI_NS}}}p"
    assert emitted.text == "Texte"


def test_roundtrip_result_exposes_intermediate_steps() -> None:
    result = assert_clean_roundtrip(
        '<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_001">Texte</p>'
    )

    assert result.source.get(f"{{{XML_NS}}}id") == "p_001"
    assert result.first_tree.xml_id == "p_001"
    assert "xmlid={p\\_001}" in result.latex
    assert result.second_tree.xml_id == "p_001"
    assert result.emitted.get(f"{{{XML_NS}}}id") == "p_001"


def test_roundtrip_p_with_hi_ref_and_note_has_no_diagnostics() -> None:
    assert_clean_roundtrip(
        '<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_001" xml:lang="fr">'
        'Un <hi rend="italic">mot</hi>, une <ref target="#x">reference</ref>'
        ' et une note<note place="foot" xml:id="n_001">Texte de note</note>.'
        "</p>"
    )


def test_roundtrip_div_with_head_paragraph_and_list_has_no_diagnostics() -> None:
    assert_clean_roundtrip(
        '<div xmlns="http://www.tei-c.org/ns/1.0" type="chapter" xml:id="ch_001">'
        "<head>Introduction</head>"
        '<p xml:id="p_001">Texte avec <hi rend="italic">italique</hi>.</p>'
        '<list type="ordered">'
        '<item n="1">Premier item</item>'
        '<item n="2">Second item avec <hi rend="small-caps">petites capitales</hi>.</item>'
        "</list>"
        "</div>"
    )


def test_roundtrip_figure_with_head_and_graphic_has_no_diagnostics() -> None:
    assert_clean_roundtrip(
        '<figure xmlns="http://www.tei-c.org/ns/1.0" xml:id="fig_001">'
        "<head>Figure 1</head>"
        '<graphic target="images/fig1.png"/>'
        "</figure>"
    )


def test_roundtrip_unknown_nested_elements_have_no_diagnostics() -> None:
    assert_clean_roundtrip(
        '<seg xmlns="http://www.tei-c.org/ns/1.0" type="lemma">A <unknown role="x">B</unknown> C</seg>'
    )


def test_roundtrip_preserves_common_attributes() -> None:
    result = assert_clean_roundtrip(
        '<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_001" xml:lang="fr" type="lead">'
        '<hi rend="italic">Texte</hi> '
        '<ref target="#x" n="1">reference</ref>'
        "</p>"
    )

    assert result.emitted.get(f"{{{XML_NS}}}id") == "p_001"
    assert result.emitted.get(f"{{{XML_NS}}}lang") == "fr"
    assert result.emitted.get("type") == "lead"
    assert result.emitted.xpath("boolean(./tei:hi[@rend='italic'])", namespaces={"tei": TEI_NS})
    assert result.emitted.xpath("boolean(./tei:ref[@target='#x' and @n='1'])", namespaces={"tei": TEI_NS})


def test_compare_reports_text_mismatch() -> None:
    diagnostics = compare_tei_elements(
        parse_tei('<p xmlns="http://www.tei-c.org/ns/1.0">A</p>'),
        parse_tei('<p xmlns="http://www.tei-c.org/ns/1.0">B</p>'),
    )

    assert diagnostic_codes(diagnostics) == ["TEXT_MISMATCH"]
    assert diagnostics[0].path == "/p"


def test_compare_reports_missing_attribute() -> None:
    diagnostics = compare_tei_elements(
        parse_tei('<p xmlns="http://www.tei-c.org/ns/1.0" type="lead">A</p>'),
        parse_tei('<p xmlns="http://www.tei-c.org/ns/1.0">A</p>'),
    )

    assert diagnostic_codes(diagnostics) == ["ATTR_MISMATCH"]
    assert diagnostics[0].path == "/p"


def test_compare_reports_missing_child() -> None:
    diagnostics = compare_tei_elements(
        parse_tei('<p xmlns="http://www.tei-c.org/ns/1.0">A <hi>B</hi></p>'),
        parse_tei('<p xmlns="http://www.tei-c.org/ns/1.0">A </p>'),
    )

    assert "CHILD_COUNT_MISMATCH" in diagnostic_codes(diagnostics)
    assert diagnostics[0].path == "/p"


def test_compare_reports_tag_namespace_tail_and_child_order_mismatches() -> None:
    diagnostics = compare_tei_elements(
        parse_tei('<p xmlns="http://www.tei-c.org/ns/1.0"><hi>A</hi><ref>B</ref></p>'),
        parse_tei('<p xmlns="http://example.test/ns"><ref>A</ref><hi>B</hi></p>'),
    )

    codes = diagnostic_codes(diagnostics)
    assert "NAMESPACE_MISMATCH" in codes
    assert "TAG_MISMATCH" in codes
    assert any(diagnostic.path == "/p/hi[1]" for diagnostic in diagnostics)
