from __future__ import annotations

import pytest
from lxml import etree

from purh_site.reversible import (
    ElementNode,
    LatexParseError,
    TextNode,
    read_latex,
    read_latex_document,
    read_tei_element,
    write_latex,
    write_tei_element,
)
from purh_site.utils import TEI_NS, XML_NS

NS = {"tei": TEI_NS, "xml": XML_NS}


def text_content(node: ElementNode) -> str:
    return "".join(node.iter_text())


def structural_signature(element: etree._Element) -> tuple:
    return (
        element.tag,
        tuple(sorted(element.attrib.items())),
        element.text,
        element.tail,
        tuple(structural_signature(child) for child in element),
    )


def full_round_trip(xml: str) -> tuple[etree._Element, etree._Element]:
    source = etree.fromstring(xml.encode("utf-8"))
    first_tree = read_tei_element(source)
    latex = write_latex(first_tree)
    second_tree = read_latex_document(latex)
    emitted = write_tei_element(second_tree)
    return source, emitted


def test_reads_simple_paragraph() -> None:
    node = read_latex_document(r"\teiP{Un paragraphe.}")

    assert node.local_name == "p"
    assert text_content(node) == "Un paragraphe."


def test_reads_paragraph_with_inline_hi() -> None:
    node = read_latex_document(r"\teiP{Un \teiHi[rend={italic}]{mot} ici.}")

    assert node.local_name == "p"
    assert [child.local_name for child in node.children if isinstance(child, ElementNode)] == ["hi"]
    hi = node.children[1]
    assert isinstance(hi, ElementNode)
    assert hi.local_name == "hi"
    assert hi.get_attr("rend") == "italic"
    assert [child.text for child in node.children if isinstance(child, TextNode)] == ["Un ", " ici."]


def test_reads_ref_target_and_unescapes_option_value() -> None:
    node = read_latex_document(r"\teiP{Voir \teiRef[target={\#x}]{reference}.}")
    ref = node.children[1]

    assert isinstance(ref, ElementNode)
    assert ref.local_name == "ref"
    assert ref.get_attr("target") == "#x"
    assert text_content(ref) == "reference"


def test_reads_inline_note_with_place_and_xml_id() -> None:
    node = read_latex_document(r"\teiP{Une note\teiNote[place={foot},xmlid={n\_001}]{Texte}.}")
    note = node.children[1]

    assert isinstance(note, ElementNode)
    assert note.local_name == "note"
    assert note.get_attr("place") == "foot"
    assert note.xml_id == "n_001"
    assert f"{{{XML_NS}}}id" in note.attrs


def test_reads_div_with_head_and_paragraph() -> None:
    node = read_latex_document(
        "\\begin{teiDiv}[type={chapter},xmlid={ch\\_001}]\n"
        "\\teiHead{Introduction}\\teiP{Texte.}\n"
        "\\end{teiDiv}"
    )

    elements = [child for child in node.children if isinstance(child, ElementNode)]
    assert node.local_name == "div"
    assert node.get_attr("type") == "chapter"
    assert node.xml_id == "ch_001"
    assert [element.local_name for element in elements] == ["head", "p"]
    assert [child for child in node.children if isinstance(child, TextNode)] == []


def test_reads_generic_tei_element() -> None:
    node = read_latex_document(
        "\\begin{teiElement}[name={seg},type={lemma}]\n"
        "A \\begin{teiElement}[name={unknown},role={x}]\n"
        "B\n"
        "\\end{teiElement} C\n"
        "\\end{teiElement}"
    )

    assert type(node) is ElementNode
    assert node.local_name == "seg"
    assert node.get_attr("type") == "lemma"
    unknown = node.children[1]
    assert isinstance(unknown, ElementNode)
    assert type(unknown) is ElementNode
    assert unknown.local_name == "unknown"
    assert unknown.get_attr("role") == "x"
    assert text_content(node) == "A B C"


def test_reads_graphic_without_content() -> None:
    node = read_latex_document(r"\teiGraphic[target={img\_1.png}]")

    assert node.local_name == "graphic"
    assert node.get_attr("target") == "img_1.png"
    assert node.children == []


def test_reads_xmlid_and_xmllang_as_xml_namespace_attributes() -> None:
    node = read_latex_document(r"\teiP[xmlid={p\_001},xmllang={fr}]{Texte}")

    assert node.xml_id == "p_001"
    assert node.get_attr("xml:lang") == "fr"
    assert f"{{{XML_NS}}}id" in node.attrs
    assert f"{{{XML_NS}}}lang" in node.attrs


def test_unescapes_special_characters_in_text() -> None:
    node = read_latex_document(
        r"\teiP{A \textbackslash{} \{ \} \% \$ \& \_ \# \textasciicircum{} \textasciitilde{}}"
    )

    assert text_content(node) == r"A \ { } % $ & _ # ^ ~"


def test_preserves_multiple_successive_inline_macros() -> None:
    node = read_latex_document(r"\teiP{A \teiHi{B}C \teiRef[target={\#d}]{D}E}")

    assert [child.local_name for child in node.children if isinstance(child, ElementNode)] == ["hi", "ref"]
    assert [child.text for child in node.children if isinstance(child, TextNode)] == ["A ", "C ", "E"]


def test_reads_namespace_option_for_generic_element() -> None:
    node = read_latex_document(
        "\\begin{teiElement}[name={external},namespace={http://example.test/ns}]\n"
        "Text\n"
        "\\end{teiElement}"
    )

    assert node.local_name == "external"
    assert node.namespace == "http://example.test/ns"


def test_unknown_macro_raises_explicit_error() -> None:
    with pytest.raises(LatexParseError):
        read_latex(r"\emph{not controlled}")


def test_partial_round_trip_tei_tree_latex_tree_tei() -> None:
    source = etree.fromstring(
        b'<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_001">'
        b'Un <hi rend="italic">mot</hi> avec une <ref target="#x">reference</ref>.'
        b"</p>"
    )

    first_tree = read_tei_element(source)
    latex = write_latex(first_tree)
    second_tree = read_latex_document(latex)
    emitted = write_tei_element(second_tree)

    assert structural_signature(emitted) == structural_signature(source)


def test_full_round_trip_preserves_div_environment_structure() -> None:
    source, emitted = full_round_trip(
        '<div xmlns="http://www.tei-c.org/ns/1.0" type="chapter" xml:id="ch_001">\n'
        "  <head>Introduction</head>\n"
        '  <p xml:id="p_001">Texte avec <hi rend="italic">italique</hi>.</p>\n'
        "</div>"
    )

    assert structural_signature(emitted) == structural_signature(source)


def test_full_round_trip_preserves_list_environment_structure() -> None:
    source, emitted = full_round_trip(
        '<list xmlns="http://www.tei-c.org/ns/1.0" type="ordered">\n'
        '  <item n="1">Premier item</item>\n'
        '  <item n="2">Second item avec <hi rend="small-caps">petites capitales</hi>.</item>\n'
        "</list>"
    )

    assert structural_signature(emitted) == structural_signature(source)


def test_full_round_trip_preserves_figure_environment_structure() -> None:
    source, emitted = full_round_trip(
        '<figure xmlns="http://www.tei-c.org/ns/1.0" xml:id="fig_001">\n'
        "  <head>Figure 1</head>\n"
        '  <graphic target="images/fig1.png"/>\n'
        "</figure>"
    )

    assert structural_signature(emitted) == structural_signature(source)


def test_full_round_trip_preserves_generic_element_environment_structure() -> None:
    source, emitted = full_round_trip(
        '<seg xmlns="http://www.tei-c.org/ns/1.0" type="lemma">A <unknown role="x">B</unknown> C</seg>'
    )

    assert structural_signature(emitted) == structural_signature(source)


def test_cosmetic_newline_after_begin_does_not_create_document_text() -> None:
    node = read_latex_document(
        "\\begin{teiDiv}\n"
        "\\teiHead{Introduction}\\teiP{Texte.}\n"
        "\\end{teiDiv}"
    )

    assert [child.local_name for child in node.children if isinstance(child, ElementNode)] == ["head", "p"]
    assert [child for child in node.children if isinstance(child, TextNode)] == []


def test_inline_spaces_inside_paragraph_are_preserved() -> None:
    node = read_latex_document(r"\teiP{Un \teiHi{mot} ici}")

    assert [child.text for child in node.children if isinstance(child, TextNode)] == ["Un ", " ici"]
    assert text_content(node) == "Un mot ici"


def test_significant_text_inside_generic_environment_is_preserved() -> None:
    node = read_latex_document(
        "\\begin{teiElement}[name={seg}]\n"
        "Texte significatif\n"
        "\\end{teiElement}"
    )

    assert text_content(node) == "Texte significatif"


def test_read_latex_can_return_text_node_for_plain_text() -> None:
    node = read_latex(r"Texte \_ seul")

    assert isinstance(node, TextNode)
    assert node.text == "Texte _ seul"
