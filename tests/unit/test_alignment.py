# tests/unit/test_alignment.py
#
# =============================================================================
# Unit tests for miscue analysis (Phase 3, Day 5): alignment + classification +
# grapheme attribution. Verifies the op stream labels each running-record miscue
# type, and that attribution emits the exact grapheme_evidence contract the BKT
# mastery model consumes (keyed by inventory keys incl. _blend_ / -ed sentinels).
# =============================================================================

from app.skills.alignment import (
    align,
    assess,
    attribute_evidence,
    tokenize,
)
from app.schemas import AssessmentResult
from app.skills.mastery import update_from_evidence
from app.schemas import LearnerProfile


def _kinds(ops):
    return [op.kind for op in ops]


# ---------------------------------------------------------------------------
# Alignment + classification
# ---------------------------------------------------------------------------


def test_perfect_read_is_all_correct() -> None:
    ops = align("the cat ran", "the cat ran")
    assert _kinds(ops) == ["correct", "correct", "correct"]
    assert all(not op.is_error for op in ops)


def test_substitution_is_flagged() -> None:
    ops = align("the ship can sail", "the sip can sail")
    sub = next(op for op in ops if op.kind == "substitution")
    assert sub.expected == "ship" and sub.spoken == "sip"
    assert sub.is_error


def test_omission_and_insertion() -> None:
    assert "omission" in _kinds(align("the big dog", "the dog"))
    assert "insertion" in _kinds(align("the dog", "the big dog"))


def test_self_correction_detected_and_not_an_error() -> None:
    """A wrong-then-right attempt is a self-correction (the word is read)."""
    ops = align("the cat ran", "the cot cat ran")
    sc = next(op for op in ops if op.kind == "self_correction")
    assert sc.expected == "cat"
    assert sc.error_word == "cot"
    assert not sc.is_error
    # The corrected word is still recorded once as a correct read.
    assert sum(1 for op in ops if op.kind == "correct" and op.expected == "cat") == 1


def test_hesitation_repetition_detected() -> None:
    ops = align("the cat ran", "the cat cat ran")
    assert "hesitation" in _kinds(ops)
    assert not any(op.kind == "insertion" for op in ops)


def test_dissimilar_extra_word_is_insertion_not_self_correction() -> None:
    """An unrelated extra word before a correct read is a true insertion."""
    ops = align("the cat ran", "the big cat ran")
    assert "insertion" in _kinds(ops)
    assert "self_correction" not in _kinds(ops)


def test_tokenize_strips_punctuation_and_case() -> None:
    assert tokenize("The cat, ran!") == ["the", "cat", "ran"]


# ---------------------------------------------------------------------------
# Grapheme attribution -> evidence contract
# ---------------------------------------------------------------------------


def test_substitution_blames_only_the_failed_grapheme() -> None:
    """Dropping the 'sh' digraph blames 'sh' and credits the rest of the word."""
    ev = attribute_evidence(align("ship", "sip"))
    assert ev["sh"] == [False]
    assert ev["i"] == [True]
    assert ev["p"] == [True]


def test_correct_read_is_all_positive_evidence() -> None:
    ev = attribute_evidence(align("ship", "ship"))
    assert ev["sh"] == [True] and ev["i"] == [True] and ev["p"] == [True]


def test_blend_sentinel_emitted() -> None:
    """A botched consonant cluster blames the _blend_ sentinel; a clean one credits it."""
    assert attribute_evidence(align("stop", "top"))["_blend_"] == [False]
    assert attribute_evidence(align("stop", "stop"))["_blend_"] == [True]


def test_suffix_sentinel_emitted() -> None:
    """Inflectional endings map to their -ed / -ing mastery sentinels."""
    assert attribute_evidence(align("jumped", "jump"))["-ed"] == [False]
    assert attribute_evidence(align("jumping", "jumping"))["-ing"] == [True]


def test_omission_is_negative_evidence() -> None:
    """A skipped word yields negative evidence on its graphemes."""
    ev = attribute_evidence(align("the big dog", "the dog"))
    assert ev["b"] == [False] and ev["i"] == [False]


def test_sight_words_contribute_no_grapheme_evidence() -> None:
    ev = attribute_evidence(align("the cat", "the cat"), sight_words={"the"})
    assert "th" not in ev  # 'the' is memorized, not decoded
    assert ev["c"] == [True]


def test_evidence_feeds_mastery_model() -> None:
    """The emitted contract drives update_from_evidence without massaging."""
    profile = LearnerProfile.new("kid-align")
    before = profile.masteries["sh"].p_mastery
    ev = attribute_evidence(align("ship ship ship", "ship ship ship"))
    update_from_evidence(profile, ev, session_index=0)
    assert profile.masteries["sh"].p_mastery > before


# ---------------------------------------------------------------------------
# Assessment bundle (fluency)
# ---------------------------------------------------------------------------


def test_assess_bundles_fluency_and_evidence() -> None:
    r = assess(
        "the ship can sail",
        "the sip can sail",
        duration_seconds=6.0,
        sight_words={"the", "can"},
    )
    assert isinstance(r, AssessmentResult)
    assert r.total_words == 4
    assert r.words_correct == 3
    assert r.errors == 1 and r.substitutions == 1
    assert r.accuracy == 0.75
    assert r.wcpm == 30.0  # 3 correct words / 6s * 60
    assert r.grapheme_evidence["sh"] == [False]


def test_self_correction_does_not_lower_accuracy() -> None:
    clean = assess("the cat ran", "the cat ran", duration_seconds=3.0)
    fixed = assess("the cat ran", "the cot cat ran", duration_seconds=3.0)
    assert fixed.accuracy == clean.accuracy == 1.0
    assert fixed.self_corrections == 1
