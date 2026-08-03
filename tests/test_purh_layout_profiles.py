from __future__ import annotations

"""Verify the versioned PURH layout profiles against the référentiel v0.5 numbers."""

import dataclasses

import pytest

from purh_site.purh_layout_profiles import (
    DEFAULT_LAYOUT_PROFILE_NAME,
    PURH_155X230_CURRENT_2026,
    PURH_155X230_PRODUCTION_2025,
    get_layout_profile,
)


def test_profiles_share_the_same_body_and_note_grid() -> None:
    # Référentiel §2.4/§2.6 (2026) and §5.4 (2025 production) measure the
    # same body/note sizes for both profiles — only the margins diverge.
    for profile in (PURH_155X230_CURRENT_2026, PURH_155X230_PRODUCTION_2025):
        assert profile.body_font_size_pt == 11
        assert profile.body_leading_pt == 13.5
        assert profile.note_font_size_pt == 8.5
        assert profile.note_leading_pt == 10.2


def test_current_2026_margins_match_referentiel_2_1() -> None:
    p = PURH_155X230_CURRENT_2026
    assert (p.margin_top_mm, p.margin_bottom_mm, p.margin_inner_mm, p.margin_outer_mm) == (30, 19, 25, 23)


def test_production_2025_margins_match_referentiel_5_4() -> None:
    p = PURH_155X230_PRODUCTION_2025
    assert (p.margin_top_mm, p.margin_bottom_mm, p.margin_inner_mm, p.margin_outer_mm) == (30, 19, 20, 30)


def test_profiles_stay_distinct_no_averaging() -> None:
    # The référentiel explicitly forbids collapsing the two profiles into a
    # mean compromise (§5.1, §5.4) — they must remain independently
    # addressable and, on margins, genuinely different.
    assert PURH_155X230_CURRENT_2026.name != PURH_155X230_PRODUCTION_2025.name
    assert PURH_155X230_CURRENT_2026.margin_inner_mm != PURH_155X230_PRODUCTION_2025.margin_inner_mm
    assert PURH_155X230_CURRENT_2026.margin_outer_mm != PURH_155X230_PRODUCTION_2025.margin_outer_mm


def test_block_width_matches_referentiel_observed_range() -> None:
    # Block width = paper width - inner - outer margin; référentiel gives
    # ~107mm for 2026 (§2.1) and ~105-106mm for production 2025 (§5.4).
    p2026 = PURH_155X230_CURRENT_2026
    assert p2026.paper_width_mm - p2026.margin_inner_mm - p2026.margin_outer_mm == 107

    p2025 = PURH_155X230_PRODUCTION_2025
    assert p2025.paper_width_mm - p2025.margin_inner_mm - p2025.margin_outer_mm == 105


def test_get_layout_profile_returns_registered_profiles() -> None:
    assert get_layout_profile("purh_155x230_current_2026") is PURH_155X230_CURRENT_2026
    assert get_layout_profile("purh_155x230_production_2025") is PURH_155X230_PRODUCTION_2025


def test_get_layout_profile_unknown_name_raises_with_known_names_listed() -> None:
    with pytest.raises(KeyError) as excinfo:
        get_layout_profile("purh_155x230_typo")
    message = str(excinfo.value)
    assert "purh_155x230_current_2026" in message
    assert "purh_155x230_production_2025" in message


def test_default_layout_profile_targets_production_2025() -> None:
    # This production pass targets the observed printer profile, not the
    # nominal 2026 master (référentiel §5.4, task instructions).
    assert DEFAULT_LAYOUT_PROFILE_NAME == PURH_155X230_PRODUCTION_2025.name


def test_layout_profile_is_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        PURH_155X230_PRODUCTION_2025.margin_inner_mm = 0  # type: ignore[misc]
