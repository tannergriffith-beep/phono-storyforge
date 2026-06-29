# app/store/session_log.py
#
# =============================================================================
# FLAGSHIP STAGE A: append-only persistence for read-aloud sessions.
#
# LearnerProfile (learner_store.py) is the *current* mastery state — overwritten
# every session. SessionLog is the *history*: one immutable row per completed
# read, kept so we can draw the longitudinal growth curve, feed the content
# flywheel, and prove the loop adapts over time. JSON-lines (one log per line)
# is append-friendly and dependency-free, mirroring JSONLearnerStore's scope.
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas import SessionLog

# Reuse the same id-sanitization the profile store uses, so a learner's profile
# and its session log live under matching, escape-proof filenames.
from app.store.learner_store import _safe_id


class SessionLogStore(ABC):
    """Abstract append-only store for per-learner SessionLogs."""

    @abstractmethod
    def append(self, log: SessionLog) -> None:
        """Records one completed session."""

    @abstractmethod
    def list(self, learner_id: str) -> list[SessionLog]:
        """Returns a learner's sessions in the order they were recorded."""


class JSONLSessionLogStore(SessionLogStore):
    """Stores each learner's sessions as JSON-lines in `<root>/<id>.sessions.jsonl`."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, learner_id: str) -> Path:
        return self.root / f"{_safe_id(learner_id)}.sessions.jsonl"

    def append(self, log: SessionLog) -> None:
        path = self._path(log.learner_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(log.model_dump_json() + "\n")

    def list(self, learner_id: str) -> list[SessionLog]:
        path = self._path(learner_id)
        if not path.exists():
            return []
        return [
            SessionLog.model_validate_json(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
