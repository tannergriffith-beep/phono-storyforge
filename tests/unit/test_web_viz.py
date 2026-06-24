# tests/unit/test_web_viz.py
#
# =============================================================================
# FLAGSHIP STAGE C: unit tests for the viz-state mapping (app/web/viz.py).
#
# These exercise the PURE serialization layer against a REAL TutorSession run
# (deterministic book provider, tmp_path store) — no FastAPI, no socket, no
# browser, no mic. They prove the payloads the browser animates from are faithful
# to the SessionOutcome the closed loop produced:
#   - the heatmap has one cell per expected word, colored by miscue kind;
#   - every mastery bar that animates on outcome was already on screen at
#     prepare() (the bar-set invariant);
#   - the next-target panel's `advanced` flag tracks real planner movement;
#   - both payloads are JSON-serializable.
# =============================================================================

from __future__ import annotations

import json

import pytest

from app.store.learner_store import JSONLearnerStore
from app.store.session_log import JSONLSessionLogStore
from app.tutor.session import TutorSession
from app.web.viz import outcome_payload, prepared_payload


@pytest.fixture
def tutor(tmp_path):
    store = JSONLearnerStore(tmp_path / "profiles")
    log_store = JSONLSessionLogStore(tmp_path / "sessions")
    return TutorSession(store, log_store=log_store)


def _is_json_serializable(obj) -> bool:
    json.dumps(obj)
    return True


# ---- prepared_payload -------------------------------------------------------


def test_prepared_payload_shape_and_serializable(tutor):
    prepared = tutor.prepare("ada", name="Ada", age=6, interest="dinosaurs")
    payload = prepared_payload(prepared)

    assert payload["type"] == "prepared"
    assert payload["learner_id"] == "ada"
    assert payload["session_index"] == 0
    assert payload["book"]["words"], "the book should have words to read"
    assert payload["objective"]["target_grapheme"]
    assert 0.0 <= payload["mean_mastery"] <= 1.0
    assert _is_json_serializable(payload)


def test_target_word_positions_point_at_target_bearing_words(tutor):
    prepared = tutor.prepare("ada")
    payload = prepared_payload(prepared)
    words = payload["book"]["words"]
    positions = payload["book"]["target_word_positions"]

    from app.skills.decodability import decompose

    target = payload["book"]["target_grapheme"]
    for pos in positions:
        assert 0 <= pos < len(words)
        graphemes = decompose(words[pos], sight_words=set(prepared.book.sight_words)).grapheme_strings
        assert target in graphemes


def test_prepared_bars_include_target_and_book_graphemes(tutor):
    prepared = tutor.prepare("ada")
    payload = prepared_payload(prepared)
    bar_graphemes = {b["grapheme"] for b in payload["mastery_bars"]}

    assert payload["objective"]["target_grapheme"] in bar_graphemes
    assert any(b["is_target"] for b in payload["mastery_bars"])
    for bar in payload["mastery_bars"]:
        assert 0.0 <= bar["p_mastery"] <= 1.0


# ---- outcome_payload --------------------------------------------------------


def test_heatmap_has_one_cell_per_expected_word(tutor):
    prepared = tutor.prepare("ada")
    n_words = len(prepared.book.words)
    outcome = tutor.record_read(prepared, " ".join(prepared.book.words))  # perfect read
    payload = outcome_payload(outcome)

    assert len(payload["heatmap"]) == n_words
    assert all(cell["kind"] == "correct" for cell in payload["heatmap"])
    assert [c["position"] for c in payload["heatmap"]] == list(range(n_words))


def test_heatmap_colors_a_dropped_word_as_a_miscue(tutor):
    prepared = tutor.prepare("ada")
    words = prepared.book.words
    # Omit the second word -> exactly that expected position should not be correct.
    spoken = " ".join(words[:1] + words[2:])
    outcome = tutor.record_read(prepared, spoken)
    payload = outcome_payload(outcome)

    non_correct = [c for c in payload["heatmap"] if c["kind"] != "correct"]
    assert non_correct, "dropping a word should surface at least one miscue cell"
    assert all(c["kind"] in {"omission", "substitution"} for c in non_correct)


def test_bar_set_invariant_every_update_was_present_at_prepare(tutor):
    prepared = tutor.prepare("ada")
    prepared_bars = {b["grapheme"] for b in prepared_payload(prepared)["mastery_bars"]}
    # A messy read so several graphemes get evidence.
    outcome = tutor.record_read(prepared, prepared.book.words[0])
    payload = outcome_payload(outcome)

    moved = {u["grapheme"] for u in payload["mastery_updates"]}
    assert moved, "a read should move at least one grapheme"
    assert moved <= prepared_bars, (
        "every animated bar must have existed at prepare(): "
        f"{moved - prepared_bars} were missing"
    )


def test_outcome_payload_fluency_and_next_target(tutor):
    prepared = tutor.prepare("ada")
    target_before = prepared.objective.target_grapheme
    outcome = tutor.record_read(prepared, " ".join(prepared.book.words))
    payload = outcome_payload(outcome)

    f = payload["fluency"]
    assert f["accuracy"] == 1.0
    assert f["total_words"] == len(prepared.book.words)
    assert f["words_correct"] == f["total_words"]

    nt = payload["next_target"]
    assert nt["previous_grapheme"] == target_before
    assert nt["advanced"] == (nt["target_grapheme"] != target_before)
    assert _is_json_serializable(payload)


def test_repeated_strong_reads_eventually_advance_the_target(tutor):
    # The loop must visibly adapt: enough perfect reads move the planner's target.
    advanced = False
    first_target = None
    for _ in range(12):
        prepared = tutor.prepare("ace", name="Ace")
        if first_target is None:
            first_target = prepared.objective.target_grapheme
        payload = outcome_payload(tutor.record_read(prepared, " ".join(prepared.book.words)))
        if payload["next_target"]["advanced"]:
            advanced = True
            break
    assert advanced, "repeated perfect reads should eventually advance the target"
