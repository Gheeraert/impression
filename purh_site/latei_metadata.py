from __future__ import annotations

"""Metopes/Commons-Publishing metadata extraction for the LaTEI PURH driver.

This module reads metadata for the experimental LaTEI driver only. It does not
rebuild, normalize, or remove the TEI header; the reversible body keeps the
original documentary structure.
"""

import re
from dataclasses import dataclass, field

from lxml import etree

from .utils import TEI_NS

NS = {"tei": TEI_NS}
EMPTY_MARKERS = {"", "#", "-", "##"}


def parse_directors_override(value: str) -> list[str]:
    """Split a " et "/","/";"-separated string of director names.

    Shared by the LaTEI PDF pipeline (reversible_integration.py) and the
    HTML site pipeline (site_builder.py) — both read a TEI <author
    role="pbd"> to identify "sous la direction de" names, and both need the
    same manual-correction escape hatch when that role is misattributed in
    the TEI/Métopes source (constaté sur *Dissimuler pour mieux régner* :
    le seul role="pbd" du livre y désigne la compositrice, pas les
    éditrices scientifiques — un défaut du balisage source, jamais deviné
    depuis le contenu, corrigé par saisie explicite uniquement).
    """
    return [name.strip() for name in re.split(r"\s+et\s+|[,;]", value) if name.strip()]


@dataclass(slots=True)
class LateiMetadata:
    title: str = ""
    subtitle: str = ""
    authors: list[str] = field(default_factory=list)
    editors: list[str] = field(default_factory=list)
    directors: list[str] = field(default_factory=list)
    publisher: str = ""
    publication_year: str = ""
    publication_place: str = ""
    isbn_print: str = ""
    isbn_pdf: str = ""
    isbn_epub: str = ""
    doi: str = ""
    issn: str = ""
    collection_title: str = ""
    collection_number: str = ""
    collection_issn: str = ""
    language: str = ""
    abstract: str = ""
    keywords: list[str] = field(default_factory=list)
    rights: str = ""
    # cover_designer : sans équivalent dans la source TEI/Métopes, renseigné
    # par l'éditrice via la boîte de dialogue optionnelle du GUI
    # (référentiel PURH v0.6 §8.1, colophon, 2026-08-04), jamais extrait du
    # XML. editorial_contact : a un équivalent TEI depuis le 2026-08-06
    # (<editionStmt>/<respStmt>/<name>, voir extract_latei_metadata) — la
    # valeur GUI, quand fournie, reste prioritaire (voir
    # reversible_integration.run_reversible_export_for_file).
    cover_designer: str = ""
    editorial_contact: str = ""

    @property
    def contributors(self) -> list[str]:
        return [*self.authors, *self.editors, *self.directors]

    @property
    def contributor_line(self) -> str:
        return " ; ".join(self.contributors)

    @property
    def preferred_isbn(self) -> str:
        return self.isbn_pdf or self.isbn_print or self.isbn_epub


def extract_latei_metadata(root: etree._Element) -> LateiMetadata:
    """Extract conservative PURH/Metopes metadata from the TEI header."""
    header = _find_header(root)
    if header is None:
        return LateiMetadata(title=_fallback_title(root))

    title_stmt = header.find("./tei:fileDesc/tei:titleStmt", namespaces=NS)
    publication_stmt = header.find("./tei:fileDesc/tei:publicationStmt", namespaces=NS)
    series_stmt = header.find("./tei:fileDesc/tei:seriesStmt", namespaces=NS)
    edition_stmt = header.find("./tei:fileDesc/tei:editionStmt", namespaces=NS)
    profile_desc = header.find("./tei:profileDesc", namespaces=NS)

    return LateiMetadata(
        title=_first_text(
            title_stmt,
            [
                "./tei:title[@type='main']",
                "./tei:title[1]",
            ],
        ),
        subtitle=_first_text(title_stmt, ["./tei:title[@type='sub']"]),
        authors=_people(title_stmt, "./tei:author[not(translate(normalize-space(@role), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='pbd')]"),
        editors=_people(title_stmt, "./tei:editor"),
        directors=_people(title_stmt, "./tei:author[translate(normalize-space(@role), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='pbd']"),
        publisher=_first_text(publication_stmt, [".//tei:publisher"]),
        publication_year=_publication_year(publication_stmt),
        publication_place=_first_text(publication_stmt, [".//tei:pubPlace"]),
        isbn_print=_identifier_in_ab(
            publication_stmt,
            ab_type="book",
            idno_types=("ISBN-13", "ISBN"),
        ),
        isbn_pdf=_identifier_in_ab(
            publication_stmt,
            ab_type="digital_download",
            subtype="PDF",
            idno_types=("ISBN", "ISBN-13"),
        ),
        isbn_epub=_identifier_in_ab(
            publication_stmt,
            ab_type="digital_download",
            subtype="EPUB",
            idno_types=("ISBN", "ISBN-13"),
        ),
        doi=_publication_doi(publication_stmt),
        issn=_identifier_in_ab(
            publication_stmt,
            ab_type="book",
            idno_types=("ISSN",),
        ),
        collection_title=_first_text(
            series_stmt,
            [
                "./tei:title[@level='s']",
                "./tei:title[1]",
            ],
        ),
        collection_number=_collection_number(series_stmt),
        collection_issn=_first_identifier(series_stmt, ("ISSN",)),
        language=_first_attr(profile_desc, "./tei:langUsage/tei:language", "ident"),
        abstract=_first_text(
            profile_desc,
            [
                "./tei:abstract[@rend='resume']/tei:p",
                "./tei:abstract[@rend='abstract']/tei:p",
            ],
        ),
        # <editionStmt>/<respStmt>/<name> : constaté sur *Dissimuler pour
        # mieux régner* et *Beautés vitales*, c'est le seul emplacement TEI
        # qui désigne fiablement la personne chargée de la mise en forme/
        # mise en pages (jamais un rôle scientifique — <author role="pbd">
        # reste le seul emplacement pour les éditeurs scientifiques, voir
        # `directors`/`parse_directors_override` ci-dessous). Utilisé par
        # défaut pour "Suivi éditorial :" au colophon (référentiel PURH
        # v0.7 §7.4, 2026-08-06) ; le champ editorial_contact du GUI reste
        # disponible pour le corriger explicitement si besoin — voir
        # reversible_integration.run_reversible_export_for_file, qui
        # n'écrase cette valeur que si le GUI en fournit une autre.
        editorial_contact=_first_text(edition_stmt, ["./tei:respStmt/tei:name"]),
    )


def _find_header(root: etree._Element) -> etree._Element | None:
    if etree.QName(root).localname == "TEI":
        return root.find("./tei:teiHeader", namespaces=NS)
    return root.find(".//tei:teiHeader", namespaces=NS)


def _first_text(context: etree._Element | None, paths: list[str]) -> str:
    if context is None:
        return ""
    for path in paths:
        for node in context.xpath(path, namespaces=NS):
            value = _node_text(node)
            if value:
                return value
    return ""


def _first_attr(context: etree._Element | None, path: str, attr: str) -> str:
    if context is None:
        return ""
    for node in context.xpath(path, namespaces=NS):
        if isinstance(node, etree._Element):
            value = _clean(node.get(attr) or "")
            if value:
                return value
    return ""


def _people(context: etree._Element | None, path: str) -> list[str]:
    if context is None:
        return []
    values: list[str] = []
    for node in context.xpath(path, namespaces=NS):
        if not isinstance(node, etree._Element):
            continue
        value = _person_text(node)
        if value:
            values.append(value)
    return values


def _person_text(node: etree._Element) -> str:
    pers_name = node.find(".//tei:persName", namespaces=NS)
    if pers_name is not None:
        parts: list[str] = []
        for child in pers_name.iter():
            if not isinstance(child.tag, str):
                continue
            if etree.QName(child).localname in {"forename", "surname", "name"}:
                value = _node_text(child)
                if value:
                    parts.append(value)
        if parts:
            return _clean(" ".join(parts))
        value = _node_text(pers_name)
        if value:
            return value

    name = node.find(".//tei:name", namespaces=NS)
    if name is not None:
        value = _node_text(name)
        if value:
            return value
    return _node_text(node)


def _publication_year(publication_stmt: etree._Element | None) -> str:
    if publication_stmt is None:
        return ""
    paths = [
        ".//tei:date[@type='publishing']",
        ".//tei:date",
    ]
    for path in paths:
        for date in publication_stmt.xpath(path, namespaces=NS):
            if not isinstance(date, etree._Element):
                continue
            value = _clean(date.get("when") or date.get("notBefore") or date.get("from") or "")
            if not value:
                value = _node_text(date)
            if value:
                return _extract_year(value)
    return ""


def _identifier_in_ab(
    publication_stmt: etree._Element | None,
    *,
    ab_type: str,
    idno_types: tuple[str, ...],
    subtype: str | None = None,
) -> str:
    if publication_stmt is None:
        return ""
    expected_type = ab_type.lower()
    expected_subtype = subtype.lower() if subtype else None
    for ab in publication_stmt.findall("./tei:ab", namespaces=NS):
        if (ab.get("type") or "").strip().lower() != expected_type:
            continue
        if expected_subtype and (ab.get("subtype") or "").strip().lower() != expected_subtype:
            continue
        value = _first_identifier(ab, idno_types)
        if value:
            return value
    return ""


def _publication_doi(publication_stmt: etree._Element | None) -> str:
    if publication_stmt is None:
        return ""
    pdf_ab = _publication_ab(publication_stmt, "digital_download", subtype="PDF")
    return (
        _first_identifier(pdf_ab, ("DOI",))
        or _first_ref_target_or_text(pdf_ab, "DOI")
        or _first_identifier(publication_stmt, ("DOI",))
        or _first_ref_target_or_text(publication_stmt, "DOI")
    )


def _publication_ab(
    publication_stmt: etree._Element,
    ab_type: str,
    *,
    subtype: str | None = None,
) -> etree._Element | None:
    expected_type = ab_type.lower()
    expected_subtype = subtype.lower() if subtype else None
    for ab in publication_stmt.findall("./tei:ab", namespaces=NS):
        if (ab.get("type") or "").strip().lower() != expected_type:
            continue
        if expected_subtype and (ab.get("subtype") or "").strip().lower() != expected_subtype:
            continue
        return ab
    return None


def _first_identifier(context: etree._Element | None, idno_types: tuple[str, ...]) -> str:
    if context is None:
        return ""
    expected = {value.upper() for value in idno_types}
    for idno in context.findall(".//tei:idno", namespaces=NS):
        kind = (idno.get("type") or "").strip().upper()
        if kind in expected:
            value = _node_text(idno)
            if value not in EMPTY_MARKERS:
                return value
    return ""


def _first_ref_target_or_text(context: etree._Element | None, ref_type: str) -> str:
    if context is None:
        return ""
    expected = ref_type.upper()
    for ref in context.findall(".//tei:ref", namespaces=NS):
        kind = (ref.get("type") or "").strip().upper()
        if kind != expected:
            continue
        value = _clean(ref.get("target") or "") or _node_text(ref)
        if value not in EMPTY_MARKERS:
            return value
    return ""


def _collection_number(series_stmt: etree._Element | None) -> str:
    value = _first_text(
        series_stmt,
        [
            "./tei:biblScope[@unit='volume']",
            "./tei:biblScope[@unit='number']",
            "./tei:biblScope[@unit='issue']",
        ],
    )
    if not value:
        return ""
    digits = "".join(char for char in value if char.isdigit())
    return digits or value


def _node_text(node: object) -> str:
    if isinstance(node, etree._Element):
        return _clean(" ".join(node.itertext()))
    return _clean(str(node))


def _clean(value: str) -> str:
    return " ".join(value.split())


def _extract_year(value: str) -> str:
    for token in value.replace("/", "-").split("-"):
        if len(token) >= 4 and token[:4].isdigit():
            return token[:4]
    return value[:4] if len(value) >= 4 and value[:4].isdigit() else value


def _fallback_title(root: etree._Element) -> str:
    value = _first_text(root, [".//tei:head[1]"])
    if value:
        return value
    return etree.QName(root).localname
