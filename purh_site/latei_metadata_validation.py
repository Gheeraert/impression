from __future__ import annotations

"""Validation générique des métadonnées LaTEI : balisage littéral échappé et
contributeurs dupliqués (référentiel PURH v0.6 §8.3, P0 — "valider les
métadonnées").

Détecte, ne corrige jamais silencieusement. Les deux défauts visés ici sont
des défauts de source (une balise `<em>` échappée dans un champ, un même
nom saisi deux fois), pas des défauts de rendu — le writer LaTeX n'a aucun
moyen fiable de deviner la bonne correction (quel est le "vrai" nom en
double, laquelle des deux entrées identiques est la faute de frappe), donc
il ne doit pas essayer : voir référentiel §8.3, "défauts mixtes : source,
validation des métadonnées et rendu", et le principe "aucune correction de
contenu silencieuse fondée sur le nom précis de [tel] livre".
"""

import re

from .latei_metadata import LateiMetadata
from .reversible import Diagnostic

# Une balise ouvrante ou fermante plausible : <em>, </em>, <hi rend="...">...
# N'essaie pas d'être un parseur XML/HTML — un simple signal d'alerte pour
# repérer des chevrons échappés retrouvés tels quels dans un champ texte.
_LITERAL_MARKUP_PATTERN = re.compile(r"<\s*/?\s*[a-zA-Z][\w:-]*(?:\s[^<>]*)?>")


def _check_literal_markup(field_name: str, value: str, diagnostics: list[Diagnostic]) -> None:
    if not value:
        return
    match = _LITERAL_MARKUP_PATTERN.search(value)
    if match:
        diagnostics.append(
            Diagnostic(
                code="LITERAL_MARKUP_IN_METADATA",
                message=(
                    f"La métadonnée {field_name!r} contient du balisage littéral "
                    f"({match.group(0)!r}) — probablement des chevrons échappés "
                    "dans la source XML, à corriger en amont plutôt que masqués."
                ),
                path=f"metadata/{field_name}",
            )
        )


def _check_duplicate_contributors(role_name: str, names: list[str], diagnostics: list[Diagnostic]) -> None:
    seen: dict[str, int] = {}
    for name in names:
        key = " ".join(name.split()).casefold()
        if key:
            seen[key] = seen.get(key, 0) + 1
    for key, count in seen.items():
        if count > 1:
            diagnostics.append(
                Diagnostic(
                    code="DUPLICATE_CONTRIBUTOR",
                    message=(
                        f"{key!r} apparaît {count} fois parmi les {role_name}s — "
                        "probablement un doublon dans la source XML, à corriger "
                        "en amont plutôt que dédupliqué silencieusement."
                    ),
                    path=f"metadata/{role_name}",
                )
            )


def validate_latei_metadata(metadata: LateiMetadata) -> list[Diagnostic]:
    """Diagnostics non bloquants sur les métadonnées extraites d'un livre.

    Générique : ne connaît rien du titre ou des contributeurs d'un livre en
    particulier, ne fait que repérer des motifs suspects communs à toute
    source Commons-Publishing mal échappée ou mal saisie.
    """
    diagnostics: list[Diagnostic] = []
    _check_literal_markup("title", metadata.title, diagnostics)
    _check_literal_markup("subtitle", metadata.subtitle, diagnostics)
    _check_literal_markup("publisher", metadata.publisher, diagnostics)
    for name in metadata.authors:
        _check_literal_markup("authors", name, diagnostics)
    for name in metadata.editors:
        _check_literal_markup("editors", name, diagnostics)
    for name in metadata.directors:
        _check_literal_markup("directors", name, diagnostics)
    _check_duplicate_contributors("author", metadata.authors, diagnostics)
    _check_duplicate_contributors("editor", metadata.editors, diagnostics)
    _check_duplicate_contributors("director", metadata.directors, diagnostics)
    return diagnostics
