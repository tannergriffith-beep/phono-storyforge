# tests/unit/test_store.py
#
# =============================================================================
# Unit tests for the JSON LearnerStore (Phase 2, Day 4).
# Verifies a LearnerProfile round-trips through the store with full fidelity.
# =============================================================================

import pytest

from app.schemas import LearnerProfile
from app.skills.mastery import update_from_evidence
from app.store import JSONLearnerStore


def test_profile_round_trips_through_store(tmp_path) -> None:
    """A profile saved then loaded is identical, including mastery state."""
    store = JSONLearnerStore(tmp_path)
    profile = LearnerProfile.new("kid-1", name="Sam", age=7, interest="trains")
    update_from_evidence(profile, {"sh": [True, True, False], "a": [True]}, session_index=3)

    store.save(profile)
    loaded = store.get("kid-1")

    assert loaded is not None
    assert loaded == profile
    assert loaded.masteries["sh"].opportunities == 3
    assert loaded.masteries["sh"].last_seen_session == 3
    assert loaded.interest == "trains"


def test_get_missing_returns_none(tmp_path) -> None:
    store = JSONLearnerStore(tmp_path)
    assert store.get("nobody") is None


def test_save_overwrites_and_lists_ids(tmp_path) -> None:
    store = JSONLearnerStore(tmp_path)
    store.save(LearnerProfile.new("a-kid"))
    store.save(LearnerProfile.new("b-kid"))

    # Overwrite a-kid with new state.
    p = store.get("a-kid")
    p.sessions_completed = 5
    store.save(p)

    assert store.list_ids() == ["a-kid", "b-kid"]
    assert store.get("a-kid").sessions_completed == 5


def test_get_or_create(tmp_path) -> None:
    store = JSONLearnerStore(tmp_path)
    created = store.get_or_create("kid-1", interest="space")
    assert created.interest == "space"
    # Second call returns the persisted one; seed kwargs are ignored.
    again = store.get_or_create("kid-1", interest="dogs")
    assert again.interest == "space"
    assert store.list_ids() == ["kid-1"]


def test_delete(tmp_path) -> None:
    store = JSONLearnerStore(tmp_path)
    store.save(LearnerProfile.new("kid-1"))
    assert store.delete("kid-1") is True
    assert store.get("kid-1") is None
    assert store.delete("kid-1") is False


def test_traversal_id_is_contained(tmp_path) -> None:
    """Path separators are sanitized so a profile can't escape the store dir."""
    store = JSONLearnerStore(tmp_path)
    path = store._path("../../etc/passwd")
    assert path.parent == tmp_path
    assert "/" not in path.stem


def test_empty_id_rejected(tmp_path) -> None:
    store = JSONLearnerStore(tmp_path)
    with pytest.raises(ValueError):
        store.get("..")
    with pytest.raises(ValueError):
        store.get("   ")
