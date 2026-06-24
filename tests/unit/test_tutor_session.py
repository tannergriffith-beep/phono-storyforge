# tests/unit/test_tutor_session.py
#
# =============================================================================
# FLAGSHIP STAGE A: unit tests for the real, stateful closed-loop tutor.
#
# These prove the product-side loop (app/tutor) behaves: it plans from the
# learner's own mastery, scores a typed read-aloud, moves mastery in the right
# direction, persists profile + session log, and ADAPTS its target across
# sessions — the behavior the eval simulation modeled, now exercised on the
# production path.
# =============================================================================

from __future__ import annotations

import pytest

from app.store.learner_store import JSONLearnerStore
from app.store.session_log import JSONLSessionLogStore
from app.tutor.session import TutorSession


@pytest.fixture
def tutor(tmp_path):
    store = JSONLearnerStore(tmp_path / "profiles")
    log_store = JSONLSessionLogStore(tmp_path / "sessions")
    return TutorSession(store, log_store=log_store), store, log_store


def test_prepare_creates_and_persists_a_new_learner(tutor) -> None:
    t, store, _ = tutor
    prepared = t.prepare("ada", name="Ada", age=6, interest="dinosaurs")

    assert prepared.profile.learner_id == "ada"
    assert prepared.session_index == 0
    assert prepared.book.words, "a non-empty practice book should be built"
    # The new learner was persisted so the next prepare() loads, not recreates.
    assert store.get("ada") is not None


def test_first_objective_targets_the_lowest_unmastered_grapheme(tutor) -> None:
    t, _, _ = tutor
    prepared = t.prepare("kid")
    # A fresh learner is below threshold everywhere, so the frontier is the very
    # first teachable grapheme in curriculum order (a short vowel).
    assert prepared.objective.target_level == "short_vowels"


def test_perfect_read_raises_target_mastery_and_logs(tutor) -> None:
    t, store, log_store = tutor
    prepared = t.prepare("kid")
    target = prepared.objective.target_grapheme

    # A perfect read = the child said exactly the book text.
    outcome = t.record_read(prepared, prepared.book.text)

    change = next(c for c in outcome.delta.changes if c.grapheme == target)
    assert change.p_after > change.p_before
    assert outcome.assessment.accuracy == pytest.approx(1.0)

    # Profile advanced and persisted; session logged.
    assert store.get("kid").sessions_completed == 1
    logs = log_store.list("kid")
    assert len(logs) == 1
    assert logs[0].target_grapheme == target
    assert logs[0].session_index == 0


def test_omitting_target_words_yields_negative_evidence(tutor) -> None:
    t, _, _ = tutor
    prepared = t.prepare("kid")
    target = prepared.objective.target_grapheme

    # The child read nothing (every word omitted) -> negative evidence.
    outcome = t.record_read(prepared, "")

    change = next(c for c in outcome.delta.changes if c.grapheme == target)
    assert change.p_after < change.p_before
    assert outcome.assessment.accuracy == pytest.approx(0.0)


def test_target_advances_across_sessions_with_strong_reads(tutor) -> None:
    """Repeated perfect reads should eventually move the planner off a target.

    This is the adaptation guarantee: the tutor does not keep teaching what the
    child has demonstrably learned.
    """
    t, store, log_store = tutor
    seen_targets = []
    for _ in range(12):
        prepared = t.prepare("kid")
        seen_targets.append(prepared.objective.target_grapheme)
        t.record_read(prepared, prepared.book.text)

    # The planner targeted more than one distinct grapheme over the run.
    assert len(set(seen_targets)) > 1
    # Session indices are contiguous and persisted.
    logs = log_store.list("kid")
    assert [log.session_index for log in logs] == list(range(12))
    assert store.get("kid").sessions_completed == 12


def test_next_objective_reflects_post_session_state(tutor) -> None:
    t, _, _ = tutor
    prepared = t.prepare("kid")
    outcome = t.record_read(prepared, prepared.book.text)
    # next_objective is computed from the updated profile (session_index advanced).
    assert outcome.next_objective is not None
    assert outcome.session_index == 0
