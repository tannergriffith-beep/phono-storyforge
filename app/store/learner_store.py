# app/store/learner_store.py
#
# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop mastery model — persistence (Phase 2, Day 4).
#
# LearnerProfile is the cross-session memory that makes the tutor adaptive: the
# mastery state has to survive between sessions for the planner to target the
# learner's actual gaps next time. This module defines a small storage interface
# plus a dependency-free JSON implementation (one file per learner). A SQLite
# implementation could be added behind the same interface, but JSON is the
# committed scope; SQLite is optional upside.
# =============================================================================

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas import LearnerProfile

# Learner ids are used as filenames; restrict to a safe charset so a profile
# can never escape the store directory.
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]")


def _safe_id(learner_id: str) -> str:
    cleaned = _SAFE_ID_RE.sub("_", learner_id.strip())
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError(f"Invalid learner_id: {learner_id!r}")
    return cleaned


class LearnerStore(ABC):
    """Abstract persistence interface for cross-session LearnerProfiles."""

    @abstractmethod
    def get(self, learner_id: str) -> LearnerProfile | None:
        """Returns the stored profile, or None if it does not exist."""

    @abstractmethod
    def save(self, profile: LearnerProfile) -> None:
        """Persists a profile (insert or overwrite)."""

    @abstractmethod
    def list_ids(self) -> list[str]:
        """Returns all stored learner ids, sorted."""

    @abstractmethod
    def delete(self, learner_id: str) -> bool:
        """Removes a profile; returns True if one was removed."""

    def get_or_create(self, learner_id: str, **kwargs) -> LearnerProfile:
        """Returns the stored profile or creates, persists, and returns a new one.

        Extra keyword args (name, age, interest, sight_words) seed a new profile
        via LearnerProfile.new; they are ignored when a profile already exists.
        """
        existing = self.get(learner_id)
        if existing is not None:
            return existing
        profile = LearnerProfile.new(learner_id, **kwargs)
        self.save(profile)
        return profile


class JSONLearnerStore(LearnerStore):
    """Stores each LearnerProfile as a pretty-printed JSON file in a directory."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, learner_id: str) -> Path:
        return self.root / f"{_safe_id(learner_id)}.json"

    def get(self, learner_id: str) -> LearnerProfile | None:
        path = self._path(learner_id)
        if not path.exists():
            return None
        return LearnerProfile.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, profile: LearnerProfile) -> None:
        path = self._path(profile.learner_id)
        # Write to a temp sibling then atomically replace, so a crash mid-write
        # can't corrupt an existing profile.
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(path)

    def list_ids(self) -> list[str]:
        return sorted(p.stem for p in self.root.glob("*.json"))

    def delete(self, learner_id: str) -> bool:
        path = self._path(learner_id)
        if path.exists():
            path.unlink()
            return True
        return False
