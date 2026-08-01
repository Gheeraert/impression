from __future__ import annotations

"""Utilities for LaTEI running titles and typographic shortening.

This module is deliberately independent of ``LatexRenderer`` and
``semantic_model`` so that the LaTEI production chain can import it
without pulling in the legacy stable-PDF chain.
"""

import re

RUNNING_TITLE_STOPWORDS = {
    "de",
    "d'",
    "d’",
    "du",
    "des",
    "le",
    "la",
    "les",
    "l'",
    "l’",
    "un",
    "une",
    "à",
    "au",
    "aux",
    "en",
    "dans",
    "sur",
    "sous",
    "par",
    "pour",
    "avec",
    "sans",
    "chez",
    "et",
    "ou",
    "mais",
    "donc",
    "or",
    "ni",
    "car",
}


def _short_running_title(title: str, max_chars: int = 58) -> str:
    """Return a readable shortened title for running headers."""

    normalized = re.sub(r"\s+", " ", (title or "").strip())
    if len(normalized) <= max_chars:
        return normalized

    words = normalized.split()
    kept: list[str] = []
    for word in words:
        candidate = " ".join([*kept, word])
        if len(candidate) + 1 > max_chars:
            break
        kept.append(word)

    if not kept:
        return normalized[: max(1, max_chars - 1)].rstrip() + "…"

    while len(kept) > 1:
        last = kept[-1].strip(" ,;:.!?()[]{}").lower()
        if last not in RUNNING_TITLE_STOPWORDS:
            break
        kept.pop()

    return " ".join(kept).rstrip(" ,;:") + "…"
