from __future__ import annotations

from lxml import etree

from purh_site.reversible import run_tei_latex_tei_roundtrip
from purh_site.utils import TEI_NS

NS = {"tei": TEI_NS}


INLINE_CASES = [
    ("title", "teiTitle", {"level": "m"}, "Titre"),
    ("foreign", "teiForeign", {"xml:lang": "la"}, "verbum"),
    ("term", "teiTerm", {"type": "concept"}, "notion"),
    ("name", "teiName", {"key": "nom-cle"}, "Nom"),
    ("persName", "teiPersName", {"ref": "#p1"}, "Personne"),
    ("placeName", "teiPlaceName", {"ref": "#lieu1"}, "Lieu"),
    ("orgName", "teiOrgName", {"role": "publisher"}, "Organisation"),
    ("date", "teiDate", {"when": "2026-06-18"}, "18 juin 2026"),
    ("num", "teiNum", {"type": "ordinal"}, "premier"),
    ("label", "teiLabel", {"n": "1"}, "I"),
]


def attrs_to_xml(attrs: dict[str, str]) -> str:
    return "".join(f' {name}="{value}"' for name, value in attrs.items())


def test_each_scholarly_inline_element_round_trips_with_dedicated_macro() -> None:
    for element_name, macro_name, attrs, text in INLINE_CASES:
        xml = (
            f'<p xmlns="http://www.tei-c.org/ns/1.0">'
            f'Avant <{element_name}{attrs_to_xml(attrs)}>{text}</{element_name}> après.'
            f"</p>"
        )

        result = run_tei_latex_tei_roundtrip(etree.fromstring(xml.encode("utf-8")))
        emitted = result.emitted
        inline = emitted.xpath(f"./tei:{element_name}", namespaces=NS)[0]

        assert result.diagnostics == []
        assert f"\\{macro_name}" in result.latex
        assert f"name={{{element_name}}}" not in result.latex
        assert inline.text == text
        for attr_name, attr_value in attrs.items():
            if attr_name == "xml:lang":
                assert inline.get("{http://www.w3.org/XML/1998/namespace}lang") == attr_value
            else:
                assert inline.get(attr_name) == attr_value


def test_successive_scholarly_inline_elements_preserve_order_and_spaces() -> None:
    result = run_tei_latex_tei_roundtrip(
        etree.fromstring(
            b'<p xmlns="http://www.tei-c.org/ns/1.0">'
            b'<title level="m">Livre</title> par '
            b'<persName ref="#p1">Autrice</persName>, '
            b'<date when="2026-06-18">2026</date> : '
            b'<term type="keyword">mot-cle</term>.'
            b"</p>"
        )
    )

    emitted = result.emitted

    assert result.diagnostics == []
    assert [etree.QName(child).localname for child in emitted] == ["title", "persName", "date", "term"]
    assert emitted[0].tail == " par "
    assert emitted[1].tail == ", "
    assert emitted[2].tail == " : "
    assert emitted[3].tail == "."
    assert "".join(emitted.itertext()) == "Livre par Autrice, 2026 : mot-cle."


def test_scholarly_inline_latex_uses_specialized_macros_not_generic_elements() -> None:
    result = run_tei_latex_tei_roundtrip(
        etree.fromstring(
            b'<p xmlns="http://www.tei-c.org/ns/1.0">'
            b'<title level="m">Livre</title>'
            b'<persName ref="#p1">Nom</persName>'
            b'<date when="2026-06-18">Date</date>'
            b'<num type="ordinal">premier</num>'
            b'<label n="1">I</label>'
            b"</p>"
        )
    )

    assert result.diagnostics == []
    assert "\\teiTitle[level={m}]{Livre}" in result.latex
    assert "\\teiPersName[ref={\\#p1}]{Nom}" in result.latex
    assert "\\teiDate[when={2026-06-18}]{Date}" in result.latex
    assert "\\teiNum[type={ordinal}]{premier}" in result.latex
    assert "\\teiLabel[n={1}]{I}" in result.latex
    assert "\\begin{teiElement}[name={title}" not in result.latex
    assert "\\begin{teiElement}[name={persName}" not in result.latex
