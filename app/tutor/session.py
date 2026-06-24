# app/tutor/session.py
#
# =============================================================================
# FLAGSHIP STAGE A: the real, stateful closed loop.
#
# This is the production analog of eval/loop.run_session. One real session:
#
#   load LearnerProfile (persistent memory)
#     -> select_objective(profile)        # adaptive planner: WHAT to teach next
#     -> build a decodable book           # Stage-A: deterministic; Stage-B: LLM
#     -> child reads it aloud             # Stage-A: typed transcript; Stage-B: voice
#     -> assess(): align + attribute      # deterministic miscue analysis
#     -> update_from_evidence(): BKT      # how mastery moved
#     -> persist profile + append SessionLog
#     -> select_objective() again         # the next target has shifted -> ADAPTATION
#
# Unlike the one-shot ADK pipeline, this remembers the learner across sessions:
# the planner targets THIS child's actual gaps, and tomorrow's book changes
# because of how today's read went. The planner, alignment, mastery model, and
# store are reused unchanged from the existing codebase.
# =============================================================================

from __future__ import annotations

import random
from dataclasses import dataclass

from app.phonics_db import GRAPHEME_INVENTORY, MASTERY_THRESHOLD
from app.schemas import (
    AssessmentResult,
    LearnerProfile,
    MasteryDelta,
    Objective,
    SessionLog,
)
from app.skills.alignment import assess
from app.skills.mastery import update_from_evidence
from app.skills.planner import select_objective
from app.store.learner_store import LearnerStore
from app.store.session_log import SessionLogStore
from app.tutor.book_source import (
    BookLike,
    BookProvider,
    deterministic_book_provider,
    new_learner_profile,
)

# Read-aloud timing model used only when a transcript arrives without a measured
# duration (typed-transcript path): seconds per word plus a per-error penalty, so
# WCPM still moves in the right direction. Voice input (Stage B) supplies a real
# duration and bypasses this. Mirrors eval/loop.py so simulation and product agree.
_SEC_PER_WORD = 0.5
_SEC_PER_ERROR = 0.7


def estimate_duration(num_words: int, errors: int) -> float:
    """Estimates read-aloud seconds from word count and error count."""
    return num_words * _SEC_PER_WORD + errors * _SEC_PER_ERROR


def _mean_mastery(profile: LearnerProfile) -> float:
    """Mean BKT P(L) across the full grapheme inventory (the growth-curve metric)."""
    masteries = [
        profile.masteries[g].p_mastery
        for g, _ in GRAPHEME_INVENTORY
        if g in profile.masteries
    ]
    return sum(masteries) / len(masteries) if masteries else 0.0


@dataclass
class PreparedSession:
    """A session that has been planned and has a book ready, awaiting the read.

    Carries everything `record_read` needs so the two-step (show book -> child
    reads -> submit transcript) flow never has to recompute or re-seed the book.
    """

    profile: LearnerProfile
    objective: Objective
    book: BookLike
    session_index: int


@dataclass
class SessionOutcome:
    """The full result of one recorded read-aloud session."""

    session_index: int
    objective: Objective
    book: BookLike
    assessment: AssessmentResult
    delta: MasteryDelta
    log: SessionLog
    mean_mastery: float          # mean P(L) across the inventory after this session
    next_objective: Objective    # what the planner would target next -> visible adaptation


class TutorSession:
    """Stateful orchestrator for the real closed-loop reading tutor.

    Owns the persistence and skill wiring; exposes a two-step API:
      prepare(learner_id)            -> PreparedSession (objective + book to read)
      record_read(prepared, spoken)  -> SessionOutcome  (assess + update + persist)
    """

    def __init__(
        self,
        store: LearnerStore,
        *,
        log_store: SessionLogStore | None = None,
        book_provider: BookProvider = deterministic_book_provider,
        num_target: int = 6,
        book_length: int = 16,
        threshold: float = MASTERY_THRESHOLD,
    ) -> None:
        self.store = store
        self.log_store = log_store
        self.book_provider = book_provider
        self.num_target = num_target
        self.book_length = book_length
        self.threshold = threshold

    def prepare(
        self,
        learner_id: str,
        *,
        rng: random.Random | None = None,
        **profile_kwargs,
    ) -> PreparedSession:
        """Loads (or creates) the learner, picks the next objective, builds a book.

        Extra keyword args (name, age, interest, sight_words) seed a brand-new
        profile and are ignored for an existing learner.
        """
        profile = self.store.get(learner_id)
        if profile is None:
            profile = new_learner_profile(learner_id, **profile_kwargs)
            self.store.save(profile)

        session_index = profile.sessions_completed
        objective = select_objective(
            profile, session_index=session_index, threshold=self.threshold
        )
        book = self.book_provider(
            objective,
            session_index=session_index,
            sight_words=set(profile.sight_words),
            num_target=self.num_target,
            length=self.book_length,
            interest=profile.interest,
            age=profile.age,
            rng=rng,
        )
        return PreparedSession(
            profile=profile,
            objective=objective,
            book=book,
            session_index=session_index,
        )

    def record_read(
        self,
        prepared: PreparedSession,
        spoken: str | list[str],
        *,
        duration_seconds: float | None = None,
    ) -> SessionOutcome:
        """Scores a read-aloud, updates mastery, and persists profile + log.

        `spoken` is the child's transcript (a string or token list). If no
        duration is supplied, one is estimated from the read so WCPM is sane.
        """
        profile = prepared.profile
        book = prepared.book

        if duration_seconds is None:
            # First pass only to count errors, then a realistic duration.
            provisional = assess(
                book.text, spoken, duration_seconds=1.0, sight_words=book.sight_words
            )
            duration_seconds = estimate_duration(len(book.words), provisional.errors)

        assessment = assess(
            book.text,
            spoken,
            duration_seconds=duration_seconds,
            sight_words=book.sight_words,
        )

        delta = update_from_evidence(
            profile,
            assessment.grapheme_evidence,
            session_index=prepared.session_index,
            threshold=self.threshold,
        )
        profile.sessions_completed += 1
        self.store.save(profile)

        log = SessionLog.build(
            learner_id=profile.learner_id,
            session_index=prepared.session_index,
            objective=prepared.objective,
            book_title=getattr(book, "title", ""),
            assessment=assessment,
            delta=delta,
            generation_source=getattr(book, "generation_source", "deterministic"),
        )
        if self.log_store is not None:
            self.log_store.append(log)

        next_objective = select_objective(
            profile, session_index=profile.sessions_completed, threshold=self.threshold
        )

        return SessionOutcome(
            session_index=prepared.session_index,
            objective=prepared.objective,
            book=book,
            assessment=assessment,
            delta=delta,
            log=log,
            mean_mastery=_mean_mastery(profile),
            next_objective=next_objective,
        )
