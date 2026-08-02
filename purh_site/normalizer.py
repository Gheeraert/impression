from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from lxml import etree

from .utils import NSMAP, set_xml_id, slugify, xml_id

# Attributs TEI dont les valeurs sont des pointeurs (éventuellement multivalués,
# séparés par des espaces). Seuls les tokens de forme "#identifiant" sont des
# références locales ; les URL externes avec fragment ne sont pas concernées.
LOCAL_POINTER_ATTRIBUTES = frozenset({
    "ana",
    "change",
    "copyOf",
    "corresp",
    "exclude",
    "facs",
    "filter",
    "from",
    "hand",
    "new",
    "next",
    "origin",
    "prev",
    "ref",
    "rendition",
    "resp",
    "sameAs",
    "scribe",
    "source",
    "spanTo",
    "synch",
    "target",
    "to",
    "who",
    "wit",
})

# Un xml:id doit être un NCName : pas de début en chiffre ni en tiret.
_NCNAME_START_RE = re.compile(r"^[A-Za-z_]")

# Forme d'un fragment de pointeur local plausible ("#fragment") : un NCName.
# "[^\W\d]" = lettre (Unicode) ou underscore ; exclut chiffres, "#", ":", etc.
# Un token comme "##" ou "#" isolé n'est pas un pointeur : c'est typiquement
# une valeur de gabarit Métopes restée non remplie.
_NCNAME_RE = re.compile(r"[^\W\d][\w.\-]*\Z")


def _readable_path(element: etree._Element) -> str:
    """XPath lisible fondé sur les noms locaux, pour les messages d'erreur."""
    steps: list[str] = []
    current: etree._Element | None = element
    while current is not None:
        local = etree.QName(current).localname
        parent = current.getparent()
        if parent is None:
            steps.append(f"/{local}")
        else:
            same_name = [
                sibling
                for sibling in parent
                if isinstance(sibling.tag, str) and etree.QName(sibling).localname == local
            ]
            if len(same_name) > 1:
                steps.append(f"/{local}[{same_name.index(current) + 1}]")
            else:
                steps.append(f"/{local}")
        current = parent
    return "".join(reversed(steps))


class DuplicateXmlIdError(ValueError):
    """Le XML source contient des xml:id dupliqués : erreur d'intégrité bloquante."""


@dataclass(slots=True)
class NormalizeReport:
    """Journal de normalisation du TEI avant transformation XSLT."""

    assigned_ids: int = 0
    renamed_duplicate_ids: int = 0
    figure_media_resolved: int = 0
    adjacent_hi_merged: int = 0
    unresolved_references: int = 0
    invalid_pointers: int = 0
    warnings: list[str] = field(default_factory=list)

    def as_lines(self) -> list[str]:
        return [
            f"Identifiants attribués (éléments sans xml:id source) : {self.assigned_ids}",
            f"xml:id dupliqués (non référencés) renommés : {self.renamed_duplicate_ids}",
            f"Figures/médias explicitement résolus : {self.figure_media_resolved}",
            f"Segments typographiques fusionnés : {self.adjacent_hi_merged}",
            f"Références locales non résolues : {self.unresolved_references}",
            f"Pointeurs invalides (valeurs de gabarit ?) : {self.invalid_pointers}",
            *[f"Avertissement : {warning}" for warning in self.warnings],
        ]


class TeiNormalizer:
    """Normalisation légère et pragmatique d'un TEI Métopes pour le rendu web.

    Politique d'intégrité :
    - un xml:id source unique est conservé strictement à l'identique ;
    - des xml:id dupliqués dans la source déclenchent une DuplicateXmlIdError ;
    - les identifiants générés ne concernent que les éléments sans xml:id,
      sont déterministes et ne peuvent pas entrer en collision avec la source ;
    - note/@n n'est jamais écrit ni modifié : c'est une donnée éditoriale
      source (la numérotation d'affichage est calculée dans la couche de rendu) ;
    - les pointeurs locaux "#id" sont contrôlés après attribution des
      identifiants ; les cibles introuvables sont signalées dans le rapport.
    """

    def normalize(self, tree: etree._ElementTree) -> NormalizeReport:
        report = NormalizeReport()
        self._reject_duplicate_ids(tree, report)
        self._ensure_ids(tree, report)
        self._merge_adjacent_hi(tree, report)
        self._check_local_references(tree, report)
        self._resolve_figure_media(tree, report)
        self._check_metadata_integrity(tree, report)
        return report

    _LITERAL_MARKUP_RE = re.compile(r"</?(em|i|b|strong|sup|sub|span|br)\b[^>]*>", re.IGNORECASE)

    def _check_metadata_integrity(self, tree: etree._ElementTree, report: NormalizeReport) -> None:
        """Signale des défauts déjà présents dans la source XML, en amont de
        ce pipeline (ex. un export d'un outil d'édition tiers) : du balisage
        HTML resté littéral dans du texte au lieu d'être interprété (souvent
        `<em>...</em>` dans un sous-titre), ou un·e même auteur·rice listé·e
        plusieurs fois dans les métadonnées. Ni l'un ni l'autre ne doit être
        corrigé ou masqué silencieusement par une rustine de rendu : ces
        défauts sont dans la donnée elle-même et doivent remonter jusqu'à
        l'éditrice pour correction à la source.
        """
        for title in tree.xpath("//tei:title | //tei:head", namespaces=NSMAP):
            text = "".join(title.itertext())
            if self._LITERAL_MARKUP_RE.search(text):
                report.warnings.append(
                    f"Balisage HTML littéral dans le texte de <{etree.QName(title).localname}> "
                    f"à {_readable_path(title)} : {text[:100]!r}"
                )

        seen_authors: dict[str, list[etree._Element]] = defaultdict(list)
        for author in tree.xpath("//tei:titleStmt/tei:author", namespaces=NSMAP):
            name = re.sub(r"\s+", " ", " ".join(author.itertext())).strip()
            if name:
                seen_authors[name].append(author)
        for name, elements in seen_authors.items():
            if len(elements) > 1:
                positions = ", ".join(_readable_path(el) for el in elements)
                report.warnings.append(
                    f"Auteur·rice dupliqué·e dans les métadonnées : {name!r} "
                    f"apparaît {len(elements)} fois ({positions})."
                )

    def _merge_adjacent_hi(self, tree: etree._ElementTree, report: NormalizeReport) -> None:
        """
        Fusionne les balises <hi> consécutives ayant le même @rend.

        Certains XML Métopes peuvent produire des fragments comme :
            <hi rend="italic">imit</hi><hi rend="italic">erò</hi>

        ou :
            <hi rend="italic">dedicata</hi> <hi rend="italic">l’Opera</hi>

        On fusionne ces segments avant le passage XSLT, en conservant
        l'éventuel texte intercalaire présent dans first.tail.
        """

        changed = True
        while changed:
            changed = False

            for first in list(tree.xpath("//tei:hi[@rend]", namespaces=NSMAP)):
                parent = first.getparent()
                if parent is None:
                    continue

                second = first.getnext()
                if second is None:
                    continue

                second_qname = etree.QName(second)
                if second_qname.namespace != NSMAP["tei"] or second_qname.localname != "hi":
                    continue

                first_rend = (first.get("rend") or "").strip()
                second_rend = (second.get("rend") or "").strip()
                if first_rend != second_rend:
                    continue

                # On ne fusionne que si le texte entre les deux balises est vide
                # ou constitué d'espaces. S'il y a du vrai texte, on ne touche pas.
                if first.tail and first.tail.strip():
                    continue

                self._append_text_to_element(first, first.tail or "")
                self._append_text_to_element(first, second.text or "")

                for child in list(second):
                    second.remove(child)
                    first.append(child)

                first.tail = second.tail
                parent.remove(second)

                report.adjacent_hi_merged += 1
                changed = True
                break

    @staticmethod
    def _append_text_to_element(element: etree._Element, text: str) -> None:
        """Ajoute du texte à la fin du contenu d'un élément XML."""
        if not text:
            return

        if len(element):
            last_child = element[-1]
            last_child.tail = (last_child.tail or "") + text
        else:
            element.text = (element.text or "") + text

    # Un livre composé de nombreux chapitres indépendants (assemblés par le
    # fichier maître via XInclude/group) peut aisément réutiliser les mêmes
    # xml:id génériques ("p1", "p2"...) dans chaque chapitre : une fois
    # assemblés, cela peut produire des centaines de doublons, chacun listant
    # toutes ses occurrences — le message explose sinon à des dizaines de
    # milliers de caractères, illisible et peu maniable dans une boîte de
    # dialogue. Bornage : les totaux réels restent toujours indiqués, rien
    # n'est perdu silencieusement, seul le détail affiché est plafonné.
    _MAX_DUPLICATE_VALUES_SHOWN = 20
    _MAX_POSITIONS_SHOWN = 5

    def _reject_duplicate_ids(self, tree: etree._ElementTree, report: NormalizeReport) -> None:
        """Résout les xml:id dupliqués qui ne sont jamais la cible d'une
        référence locale — le cas courant d'un livre Métopes assemblé par
        XInclude à partir de chapitres écrits indépendamment, chacun
        numérotant ses propres paragraphes ("p1", "p2"...) sans que rien,
        une fois le livre assemblé, ne pointe explicitement vers ces
        identifiants génériques. La première occurrence garde son
        identifiant source ; les suivantes sont renommées de façon
        déterministe, sans collision, et le renommage est journalisé.

        Un xml:id dupliqué qui EST la cible d'un pointeur local reste en
        revanche bloquant : le renommer silencieusement rendrait cette
        référence ambiguë (vers lequel des porteurs ?), et seul un
        correctif à la source peut lever cette ambiguïté.
        """
        carriers: dict[str, list[etree._Element]] = defaultdict(list)
        for element in tree.xpath("//*[@xml:id]", namespaces=NSMAP):
            current_id = xml_id(element)
            if current_id:
                carriers[current_id].append(element)

        duplicates = {value: elements for value, elements in carriers.items() if len(elements) > 1}
        if not duplicates:
            return

        referenced_ids = self._collect_local_pointer_targets(tree)
        ambiguous = {value: elements for value, elements in duplicates.items() if value in referenced_ids}
        if ambiguous:
            self._raise_duplicate_ids_error(tree, ambiguous)

        seen_ids: set[str] = set(carriers.keys())
        for value, elements in duplicates.items():
            for element in elements[1:]:
                new_id = self._make_unique_duplicate_id(value, seen_ids)
                set_xml_id(element, new_id)
                seen_ids.add(new_id)
                report.renamed_duplicate_ids += 1
                report.warnings.append(
                    f"xml:id \"{value}\" dupliqué (non référencé) sur <{etree.QName(element).localname}> "
                    f"à {_readable_path(element)} — renommé en \"{new_id}\"."
                )

    def _collect_local_pointer_targets(self, tree: etree._ElementTree) -> set[str]:
        targets: set[str] = set()
        for element in tree.iter(etree.Element):
            for attribute, raw_value in element.attrib.items():
                if etree.QName(attribute).localname not in LOCAL_POINTER_ATTRIBUTES:
                    continue
                for token in raw_value.split():
                    if token.startswith("#") and len(token) > 1:
                        targets.add(token[1:])
        return targets

    @staticmethod
    def _make_unique_duplicate_id(base: str, seen_ids: set[str]) -> str:
        suffix = 2
        while f"{base}-{suffix}" in seen_ids:
            suffix += 1
        return f"{base}-{suffix}"

    def _raise_duplicate_ids_error(
        self, tree: etree._ElementTree, duplicates: dict[str, list[etree._Element]]
    ) -> None:
        source = tree.docinfo.URL or "document en mémoire"
        shown_values = list(duplicates.items())[: self._MAX_DUPLICATE_VALUES_SHOWN]
        details: list[str] = []
        for value, elements in shown_values:
            shown_positions = elements[: self._MAX_POSITIONS_SHOWN]
            positions = "; ".join(
                f"<{etree.QName(el).localname}> à {_readable_path(el)}" for el in shown_positions
            )
            omitted_positions = len(elements) - len(shown_positions)
            if omitted_positions > 0:
                positions += f"; … et {omitted_positions} autre(s) occurrence(s)"
            details.append(f"xml:id \"{value}\" ({len(elements)} occurrences) porté par : {positions}")

        omitted_values = len(duplicates) - len(shown_values)
        summary = (
            f"{len(duplicates)} xml:id dupliqué(s) et référencé(s) (ambigu) dans " + source + " — "
            + " | ".join(details)
        )
        if omitted_values > 0:
            summary += f" | … et {omitted_values} autre(s) identifiant(s) dupliqué(s) et référencé(s)"
        raise DuplicateXmlIdError(summary)

    def _ensure_ids(self, tree: etree._ElementTree, report: NormalizeReport) -> None:
        """Attribue un identifiant aux seuls éléments qui n'en ont pas.

        Les xml:id source sont conservés strictement. Les identifiants générés
        sont déterministes (mêmes entrées → mêmes sorties) et ne peuvent pas
        entrer en collision avec un identifiant source grâce au jeu `seen_ids`
        pré-rempli avec tous les identifiants du document.
        """
        counters: defaultdict[str, int] = defaultdict(int)
        seen_ids: set[str] = {
            value
            for value in (
                xml_id(element) for element in tree.xpath("//*[@xml:id]", namespaces=NSMAP)
            )
            if value
        }
        candidates = tree.xpath(
            "//tei:group | //tei:div | //tei:head | //tei:p | //tei:figure | //tei:note"
            " | //tei:listBibl | //tei:bibl | //tei:body | //tei:text",
            namespaces=NSMAP,
        )
        for element in candidates:
            if xml_id(element):
                continue

            local = etree.QName(element).localname
            if local == "head":
                base = slugify(" ".join(element.itertext()), fallback="head")
            elif local == "group":
                base = slugify(element.get("type", "group"), fallback="group")
            elif local == "div":
                base = slugify(element.get("type", "div"), fallback="div")
            else:
                base = local
            if not _NCNAME_START_RE.match(base):
                base = f"id-{base}"

            while True:
                counters[base] += 1
                candidate_id = f"{base}-{counters[base]:03d}"
                if candidate_id not in seen_ids:
                    break

            set_xml_id(element, candidate_id)
            seen_ids.add(candidate_id)
            report.assigned_ids += 1

    def _check_local_references(self, tree: etree._ElementTree, report: NormalizeReport) -> None:
        """Contrôle l'intégrité des pointeurs locaux "#identifiant".

        Ne concerne que les attributs pointeurs TEI connus ; les tokens qui ne
        commencent pas par "#" (URL externes, y compris avec fragment) sont
        ignorés. Politique du projet : signalement non bloquant dans le rapport.
        """
        known_ids: set[str] = {
            value
            for value in (
                xml_id(element) for element in tree.xpath("//*[@xml:id]", namespaces=NSMAP)
            )
            if value
        }
        for element in tree.iter(etree.Element):
            for attribute, raw_value in element.attrib.items():
                local_name = etree.QName(attribute).localname
                if local_name not in LOCAL_POINTER_ATTRIBUTES:
                    continue
                for token in raw_value.split():
                    if not token.startswith("#"):
                        continue
                    fragment = token[1:]
                    if fragment and fragment in known_ids:
                        continue
                    if not _NCNAME_RE.match(fragment):
                        # "#", "##"… : pas un pointeur local de forme "#identifiant",
                        # mais une valeur de gabarit incomplète ou invalide. Signalée
                        # à part, sans être comptée comme référence orpheline.
                        report.invalid_pointers += 1
                        report.warnings.append(
                            "Pointeur local invalide (valeur de gabarit non remplie ?) : "
                            f"{local_name}=\"{token}\" sur <{etree.QName(element).localname}> "
                            f"({_readable_path(element)})"
                        )
                        continue
                    report.unresolved_references += 1
                    report.warnings.append(
                        "Référence locale introuvable : "
                        f"{local_name}=\"{token}\" sur <{etree.QName(element).localname}> "
                        f"({_readable_path(element)})"
                    )

    def _resolve_figure_media(self, tree: etree._ElementTree, report: NormalizeReport) -> None:
        figures = tree.xpath("//tei:figure", namespaces=NSMAP)
        for figure in figures:
            if figure.xpath("./tei:graphic[@url] | ./tei:media[@url]", namespaces=NSMAP):
                report.figure_media_resolved += 1
                continue
            head_text = " ".join(figure.xpath("./tei:head//text()", namespaces=NSMAP)).strip()
            if head_text and not figure.xpath("./tei:graphic | ./tei:media", namespaces=NSMAP):
                report.warnings.append(f"Figure sans ressource explicite : {head_text[:100]}")
