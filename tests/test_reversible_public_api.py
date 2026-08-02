from __future__ import annotations

from lxml import etree

from purh_site.reversible import (
    compare_tei_elements,
    read_latex_document,
    read_tei_element,
    run_tei_latex_tei_roundtrip,
    write_latex,
    write_tei_element,
)


def test_experimental_public_api_imports_and_round_trips_minimal_paragraph():
    source = etree.fromstring(
        b'<p xmlns="http://www.tei-c.org/ns/1.0">Texte</p>'
    )

    first_tree = read_tei_element(source)
    latex = write_latex(first_tree)
    second_tree = read_latex_document(latex)
    emitted = write_tei_element(second_tree)

    assert latex == r"\teiP{Texte}"
    assert compare_tei_elements(source, emitted) == []

    result = run_tei_latex_tei_roundtrip(source)

    assert result.diagnostics == []
