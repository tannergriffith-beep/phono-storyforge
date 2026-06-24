# tests/unit/test_mastery.py
#
# =============================================================================
# Unit tests for the BKT mastery model (Phase 2, Day 3).
# Verifies: mastery rises on correct evidence, falls on errors, the profile
# factory seeds the full grapheme inventory, and level/threshold bookkeeping.
# =============================================================================

from app.phonics_db import (
    GRAPHEME_INVENTORY,
    GRAPHEME_LEVEL,
    MASTERY_THRESHOLD,
    bkt_params_for_level,
)
from app.schemas import LearnerProfile
from app.skills.mastery import update_from_evidence, _bkt_step


def test_new_profile_seeds_full_inventory() -> None:
    """A fresh profile tracks every inventory grapheme at its BKT prior."""
    profile = LearnerProfile.new("kid-1", interest="dogs")
    assert len(profile.masteries) == len(GRAPHEME_INVENTORY)
    sh = profile.masteries["sh"]
    assert sh.level == "digraphs"
    assert sh.p_mastery == bkt_params_for_level("digraphs")["p_init"]
    # Nothing is mastered at the prior.
    assert profile.mastered_levels() == []


def test_mastery_rises_on_correct_evidence() -> None:
    """Correct observations strictly increase a grapheme's P(L)."""
    profile = LearnerProfile.new("kid-1")
    before = profile.masteries["sh"].p_mastery

    delta = update_from_evidence(profile, {"sh": [True, True, True]}, session_index=0)

    after = profile.masteries["sh"].p_mastery
    assert after > before
    assert profile.masteries["sh"].opportunities == 3
    assert profile.masteries["sh"].correct == 3
    assert profile.masteries["sh"].last_seen_session == 0
    change = next(c for c in delta.changes if c.grapheme == "sh")
    assert change.delta > 0
    assert change.n_correct == 3 and change.n_incorrect == 0


def test_mastery_falls_on_errors() -> None:
    """Incorrect observations decrease a grapheme's P(L) below where it started."""
    profile = LearnerProfile.new("kid-1")
    # Lift 'sh' up first so there is room to fall.
    update_from_evidence(profile, {"sh": [True, True, True, True]})
    raised = profile.masteries["sh"].p_mastery

    delta = update_from_evidence(profile, {"sh": [False, False, False]})
    fell = profile.masteries["sh"].p_mastery

    assert fell < raised
    change = next(c for c in delta.changes if c.grapheme == "sh")
    assert change.delta < 0
    assert change.n_incorrect == 3 and change.n_correct == 0


def test_single_step_directionality() -> None:
    """A correct step raises P(L); an incorrect step lowers it (vs. itself)."""
    params = bkt_params_for_level("digraphs")
    p = 0.5
    assert _bkt_step(p, True, params) > p
    assert _bkt_step(p, False, params) < p


def test_repeated_correct_reaches_mastery_and_reports_it() -> None:
    """Enough correct evidence crosses the threshold and is reported once."""
    profile = LearnerProfile.new("kid-1")
    delta = update_from_evidence(profile, {"sh": [True] * 40}, session_index=2)

    assert profile.masteries["sh"].p_mastery >= MASTERY_THRESHOLD
    assert "sh" in delta.newly_mastered

    # A subsequent correct batch does not re-report an already-mastered grapheme.
    delta2 = update_from_evidence(profile, {"sh": [True, True]})
    assert "sh" not in delta2.newly_mastered


def test_level_becomes_mastered_when_all_graphemes_cross() -> None:
    """A level is reported newly-mastered only once all its graphemes cross."""
    profile = LearnerProfile.new("kid-1")
    # y_vowel has a single grapheme ('y'), so mastering it masters the level.
    assert GRAPHEME_LEVEL["y"] == "y_vowel"
    assert not profile.is_level_mastered("y_vowel")

    delta = update_from_evidence(profile, {"y": [True] * 60})

    assert profile.is_level_mastered("y_vowel")
    assert "y_vowel" in delta.newly_mastered_levels
    assert "y_vowel" in profile.mastered_levels()


def test_empty_and_missing_evidence_are_no_ops() -> None:
    """Empty observation lists produce no changes and no timestamp bump."""
    profile = LearnerProfile.new("kid-1")
    before = profile.updated_at
    delta = update_from_evidence(profile, {"sh": []})
    assert delta.changes == []
    assert profile.updated_at == before


def test_unknown_grapheme_is_created_on_demand() -> None:
    """Evidence for a grapheme not yet in the profile creates it from inventory."""
    profile = LearnerProfile(learner_id="kid-2")  # no seeded masteries
    assert "sh" not in profile.masteries
    update_from_evidence(profile, {"sh": [True]})
    assert "sh" in profile.masteries
    assert profile.masteries["sh"].level == "digraphs"
