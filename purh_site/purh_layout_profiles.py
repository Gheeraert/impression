from __future__ import annotations

"""Versioned PURH page-layout profiles (format, margins, body/note grid).

Source of truth: ``tests/fixtures/commons-publishing/
Referentiel_mise_en_page_PURH_audit_v0.5.docx``, sections 2.1, 2.4, 2.6 and
5.4. Two profiles are attested there and must stay distinct — the
référentiel explicitly forbids averaging them into a single compromise:

* ``purh_155x230_current_2026`` — measured directly from the 2026 InDesign
  master (IDML ``UE_155x230``), status "confirmé/partiel" (§1, §2.1).
* ``purh_155x230_production_2025`` — the profile observed independently in
  two real PURH-printed books (*Beautés vitales*, *Dissimuler pour mieux
  régner*), status "confirmé" by that cross-book agreement (§5.4). This is
  the profile a given production pass targets when it aims to reproduce a
  PURH-printer PDF, per the task that created this module.

Both profiles share the same body/note grid (11/13.5 pt body, 8.5/10.2 pt
notes) but differ on margins — the référentiel treats this as a real,
unresolved divergence pending arbitration by the editors, not a measurement
error, so it is recorded here rather than reconciled.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PurhLayoutProfile:
    """Plain-data page-layout profile: format, margins, body/note grid.

    All dimensions are in millimeters, all type sizes in points. Values are
    the numeric core of the référentiel's prose; see the module docstring
    for the exact source section per profile.
    """

    name: str
    status: str
    paper_width_mm: float
    paper_height_mm: float
    margin_top_mm: float
    margin_bottom_mm: float
    margin_inner_mm: float
    margin_outer_mm: float
    body_font_size_pt: float
    body_leading_pt: float
    note_font_size_pt: float
    note_leading_pt: float


PURH_155X230_CURRENT_2026 = PurhLayoutProfile(
    name="purh_155x230_current_2026",
    status="confirmé/partiel",
    paper_width_mm=155,
    paper_height_mm=230,
    margin_top_mm=30,
    margin_bottom_mm=19,
    margin_inner_mm=25,
    margin_outer_mm=23,
    body_font_size_pt=11,
    body_leading_pt=13.5,
    note_font_size_pt=8.5,
    note_leading_pt=10.2,
)

PURH_155X230_PRODUCTION_2025 = PurhLayoutProfile(
    name="purh_155x230_production_2025",
    status="confirmé",
    paper_width_mm=155,
    paper_height_mm=230,
    margin_top_mm=30,
    margin_bottom_mm=19,
    margin_inner_mm=20,
    margin_outer_mm=30,
    body_font_size_pt=11,
    body_leading_pt=13.5,
    note_font_size_pt=8.5,
    note_leading_pt=10.2,
)

# The profile a fresh production PDF should target unless a caller asks
# otherwise: the observed printer profile, since the current mission is to
# converge the generated PDF toward it (référentiel §5.4).
DEFAULT_LAYOUT_PROFILE_NAME = PURH_155X230_PRODUCTION_2025.name

_LAYOUT_PROFILES: dict[str, PurhLayoutProfile] = {
    PURH_155X230_CURRENT_2026.name: PURH_155X230_CURRENT_2026,
    PURH_155X230_PRODUCTION_2025.name: PURH_155X230_PRODUCTION_2025,
}


def get_layout_profile(name: str) -> PurhLayoutProfile:
    """Look up a registered layout profile by name.

    Raises ``KeyError`` with the list of valid names if ``name`` is unknown,
    rather than silently falling back to a default — an unrecognized
    profile name is almost always a typo the caller needs to see.
    """
    try:
        return _LAYOUT_PROFILES[name]
    except KeyError:
        known = ", ".join(sorted(_LAYOUT_PROFILES))
        raise KeyError(f"Unknown PURH layout profile {name!r}; known profiles: {known}") from None
