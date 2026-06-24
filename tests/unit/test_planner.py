# tests/unit/test_planner.py
#
# =============================================================================
# Unit tests for the adaptive curriculum planner (Phase 2, Day 4).
# Verifies: ZPD target = lowest unmastered grapheme; mastered_levels budget;
# spaced-review picks are due-ordered; all-mastered fallback.
# =============================================================================

from app.phonics_db import GRAPHEME_INVENTORY, MASTERY_THRESHOLD
from app.schemas import LearnerProfile
from app.skills.planner import select_objective


def _master(profile: LearnerProfile, graphemes, *, last_seen=None) -> None:
    """Forces the given graphemes to mastered for test setup."""
    for g in graphemes:
        m = profile.masteries[g]
        m.p_mastery = 0.99
        m.last_seen_session = last_seen


def test_picks_lowest_unmastered_grapheme_fresh_profile() -> None:
    """A fresh learner targets the very first grapheme in the inventory."""
    profile = LearnerProfile.new("kid-1")
    first_grapheme, first_level = GRAPHEME_INVENTORY[0]
    obj = select_objective(profile)
    assert obj.target_grapheme == first_grapheme
    assert obj.target_level == first_level
    assert obj.mastered_levels == []


def test_target_advances_past_mastered_level() -> None:
    """Once short_vowels is fully mastered, the target moves to the next level."""
    profile = LearnerProfile.new("kid-1")
    sv = [g for g, lvl in GRAPHEME_INVENTORY if lvl == "short_vowels"]
    _master(profile, sv, last_seen=0)

    obj = select_objective(profile)
    assert "short_vowels" in obj.mastered_levels
    assert obj.target_level == "digraphs"
    # First digraph in inventory order is the frontier.
    first_digraph = next(g for g, lvl in GRAPHEME_INVENTORY if lvl == "digraphs")
    assert obj.target_grapheme == first_digraph


def test_target_is_weakest_within_partially_learned_level() -> None:
    """The frontier is the first below-threshold grapheme in curriculum order."""
    profile = LearnerProfile.new("kid-1")
    sv = [g for g, lvl in GRAPHEME_INVENTORY if lvl == "short_vowels"]
    # Master all short vowels except the 3rd one; it should be the target.
    _master(profile, sv[:2] + sv[3:], last_seen=0)
    obj = select_objective(profile)
    assert obj.target_grapheme == sv[2]
    assert obj.target_level == "short_vowels"


def test_spaced_review_prefers_least_recently_seen() -> None:
    """Review picks the most-due (oldest last_seen) mastered graphemes."""
    profile = LearnerProfile.new("kid-1")
    sv = [g for g, lvl in GRAPHEME_INVENTORY if lvl == "short_vowels"]
    # Master several with different recency; lower last_seen == more due.
    profile.masteries[sv[0]].p_mastery = 0.99
    profile.masteries[sv[0]].last_seen_session = 5
    profile.masteries[sv[1]].p_mastery = 0.99
    profile.masteries[sv[1]].last_seen_session = 1  # oldest -> most due
    profile.masteries[sv[2]].p_mastery = 0.99
    profile.masteries[sv[2]].last_seen_session = 3

    obj = select_objective(profile, num_review=2)
    # sv[1] (oldest) then sv[2], excluding whatever the target is.
    assert obj.review_graphemes[0] == sv[1]
    assert len(obj.review_graphemes) == 2
    assert obj.target_grapheme not in obj.review_graphemes


def test_no_review_when_nothing_mastered() -> None:
    profile = LearnerProfile.new("kid-1")
    obj = select_objective(profile)
    assert obj.review_graphemes == []


def test_all_mastered_falls_back_to_weakest() -> None:
    """When every grapheme is mastered, target the weakest for reinforcement."""
    profile = LearnerProfile.new("kid-1")
    for m in profile.masteries.values():
        m.p_mastery = 0.99
        m.last_seen_session = 0
    # Make one grapheme the clear weakest (still above threshold).
    weak_g = GRAPHEME_INVENTORY[10][0]
    profile.masteries[weak_g].p_mastery = MASTERY_THRESHOLD + 0.001

    obj = select_objective(profile)
    assert obj.target_grapheme == weak_g
    assert len(obj.mastered_levels) == len({lvl for _g, lvl in GRAPHEME_INVENTORY})
