from __future__ import annotations

from lxml import etree

from purh_site.reversible import read_tei_element, write_latex, write_latex_document


def latex_from_tei(xml: str) -> str:
    element = etree.fromstring(xml.encode("utf-8"))
    return write_latex(read_tei_element(element))


def test_simple_paragraph_uses_semantic_macro() -> None:
    latex = latex_from_tei('<p xmlns="http://www.tei-c.org/ns/1.0">Un paragraphe.</p>')

    assert latex == r"\teiP{Un paragraphe.}"


def test_paragraph_with_inline_hi_preserves_mixed_content() -> None:
    latex = latex_from_tei(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Un <hi rend="italic">mot</hi> ici.</p>'
    )

    assert latex == r"\teiP{Un \teiHi[rend={italic}]{mot} ici.}"


def test_paragraph_with_ref_target_preserves_target_option() -> None:
    latex = latex_from_tei(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Voir <ref target="#x">référence</ref>.</p>'
    )

    assert latex == r"\teiP{Voir \teiRef[target={\#x}]{référence}.}"


def test_paragraph_with_inline_note_preserves_place_and_xml_id() -> None:
    latex = latex_from_tei(
        '<p xmlns="http://www.tei-c.org/ns/1.0">Une note<note place="foot" xml:id="n_001">Texte</note>.</p>'
    )

    assert latex == r"\teiP{Une note\teiNote[place={foot},xmlid={n\_001}]{Texte}.}"


def test_div_with_head_and_paragraph_uses_semantic_environment() -> None:
    latex = latex_from_tei(
        '<div xmlns="http://www.tei-c.org/ns/1.0" type="chapter" xml:id="ch_001">'
        "<head>Introduction</head><p>Texte.</p></div>"
    )

    assert latex == (
        "\\begin{teiDiv}[type={chapter},xmlid={ch\\_001}]\n"
        "\\teiHead{Introduction}\\teiP{Texte.}\n"
        "\\end{teiDiv}"
    )


def test_unknown_element_is_kept_as_generic_semantic_environment() -> None:
    latex = latex_from_tei(
        '<seg xmlns="http://www.tei-c.org/ns/1.0" type="lemma">A <unknown role="x">B</unknown> C</seg>'
    )

    assert latex == (
        "\\begin{teiElement}[name={seg},type={lemma}]\n"
        "A \\begin{teiElement}[name={unknown},role={x}]\n"
        "B\n"
        "\\end{teiElement} C\n"
        "\\end{teiElement}"
    )


def test_latex_special_characters_are_escaped_in_text_only() -> None:
    latex = latex_from_tei(
        r'<p xmlns="http://www.tei-c.org/ns/1.0">A \ { } % $ &amp; _ # ^ ~</p>'
    )

    assert latex == (
        r"\teiP{A \textbackslash{} \{ \} \% \$ \& \_ \# \textasciicircum{} \textasciitilde{}}"
    )


def test_xml_id_and_xml_lang_are_converted_to_stable_options() -> None:
    latex = latex_from_tei(
        '<p xmlns="http://www.tei-c.org/ns/1.0" xml:id="p_001" xml:lang="fr">Texte</p>'
    )

    assert latex == r"\teiP[xmlid={p\_001},xmllang={fr}]{Texte}"


def test_list_item_figure_graphic_and_quote_have_controlled_macros() -> None:
    latex = latex_from_tei(
        '<div xmlns="http://www.tei-c.org/ns/1.0"><quote>Q</quote>'
        '<list type="ordered"><item n="1">Item</item></list>'
        '<figure xml:id="fig_1"><graphic target="img_1.png"/></figure></div>'
    )

    assert "\\begin{teiQuote}\nQ\n\\end{teiQuote}" in latex
    assert "\\begin{teiList}[type={ordered}]\n\\teiItem[n={1}]{Item}\n\\end{teiList}" in latex
    assert "\\begin{teiFigure}[xmlid={fig\\_1}]\n\\teiGraphic[target={img\\_1.png}]\n\\end{teiFigure}" in latex


def test_write_latex_document_delegates_to_main_writer() -> None:
    element = etree.fromstring('<p xmlns="http://www.tei-c.org/ns/1.0">Texte</p>'.encode("utf-8"))
    node = read_tei_element(element)

    assert write_latex_document(node) == r"\teiP{Texte}"
