# eval/loop.py
#
# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop tutor — the loop (Phase 3, Day 6).
#
# Wires the whole evidenced loop for one session, arm-agnostic:
#
#   Objective -> deterministic book -> simulated read-aloud -> miscue analysis
#   + grapheme attribution -> BKT mastery update -> (persist) -> next Objective
#
# The Objective is passed in, so the same loop drives both experiment arms: the
# ADAPTIVE arm feeds select_objective(profile); the STATIC control feeds a fixed
# scope-and-sequence. Everything here is deterministic and LLM-free.
# =============================================================================

from __future__ import annotations

import random
from dataclasses import dataclass

from app.phonics_db import GRAPHEME_INVENTORY, MASTERY_THRESHOLD
from app.schemas import AssessmentResult, LearnerProfile, MasteryDelta, Objective
from app.skills.alignment import assess
from app.skills.mastery import update_from_evidence
from app.skills.planner import select_objective
from app.store.learner_store import LearnerStore
from eval.book_builder import UNTEACHABLE_GRAPHEMES, Book, build_book
from eval.simulated_learner import SimulatedLearner

# The graphemes the deterministic curriculum can actually teach — the set the
# experiment measures progress over.
CURRICULUM_GRAPHEMES: list[str] = [
    g for g, _ in GRAPHEME_INVENTORY if g not in UNTEACHABLE_GRAPHEMES
]

# Read-aloud timing model: seconds per word, plus a penalty per error, so WCPM
# improves as the child makes fewer mistakes.
_SEC_PER_WORD = 0.5
_SEC_PER_ERROR = 0.7


def new_tutor_profile(learner_id: str, **kwargs) -> LearnerProfile:
    """A fresh tutor-side profile with the unteachable graphemes pre-mastered.

    The tutor's BKT estimate starts at the priors for everything teachable; the
    out-of-curriculum graphemes (ng, ph) are seeded as mastered so the planner
    never targets a grapheme the book builder can't exercise.
    """
    profile = LearnerProfile.new(learner_id, **kwargs)
    for g in UNTEACHABLE_GRAPHEMES:
        if g in profile.masteries:
            profile.masteries[g].p_mastery = 1.0
    return profile


def estimate_duration(result_words: int, errors: int) -> float:
    return result_words * _SEC_PER_WORD + errors * _SEC_PER_ERROR


@dataclass
class SessionResult:
    """Everything one closed-loop session produced (for logging/experiments)."""

    session_index: int
    objective: Objective
    book: Book
    assessment: AssessmentResult
    delta: MasteryDelta
    true_mean_mastery: float       # ground-truth, over CURRICULUM_GRAPHEMES
    true_num_mastered: int         # ground-truth count over CURRICULUM_GRAPHEMES
    est_mean_mastery: float        # tutor BKT estimate, over CURRICULUM_GRAPHEMES


def run_session(
    profile: LearnerProfile,
    learner: SimulatedLearner,
    objective: Objective,
    *,
    session_index: int,
    store: LearnerStore | None = None,
    book_rng: random.Random | None = None,
    threshold: float = MASTERY_THRESHOLD,
) -> SessionResult:
    """Runs one full closed-loop session and returns the result.

    Builds a decodable book for `objective`, has the simulated learner read it,
    runs miscue analysis, updates the tutor's BKT estimate from the resulting
    grapheme_evidence, advances the session counter, and (optionally) persists.
    """
    book = build_book(
        objective,
        session_index=session_index,
        sight_words=set(profile.sight_words),
        rng=book_rng,
    )

    spoken = learner.read(book.words, sight_words=book.sight_words)
    duration = estimate_duration(len(book.words), errors=0)
    # First pass to count errors for a realistic duration, then re-assess.
    provisional = assess(book.text, spoken, duration_seconds=1.0, sight_words=book.sight_words)
    duration = estimate_duration(len(book.words), errors=provisional.errors)
    assessment = assess(
        book.text, spoken, duration_seconds=duration, sight_words=book.sight_words
    )

    delta = update_from_evidence(
        profile, assessment.grapheme_evidence, session_index=session_index, threshold=threshold
    )
    profile.sessions_completed += 1
    if store is not None:
        store.save(profile)

    est_mean = (
        sum(profile.masteries[g].p_mastery for g in CURRICULUM_GRAPHEMES if g in profile.masteries)
        / len(CURRICULUM_GRAPHEMES)
        if CURRICULUM_GRAPHEMES
        else 0.0
    )

    return SessionResult(
        session_index=session_index,
        objective=objective,
        book=book,
        assessment=assessment,
        delta=delta,
        true_mean_mastery=learner.true_mean_mastery(CURRICULUM_GRAPHEMES),
        true_num_mastered=learner.true_num_mastered(CURRICULUM_GRAPHEMES, threshold),
        est_mean_mastery=est_mean,
    )


def run_adaptive_loop(
    profile: LearnerProfile,
    learner: SimulatedLearner,
    *,
    num_sessions: int,
    store: LearnerStore | None = None,
    book_rng: random.Random | None = None,
) -> list[SessionResult]:
    """Runs the adaptive arm: each session the planner picks the next Objective."""
    results: list[SessionResult] = []
    for i in range(num_sessions):
        objective = select_objective(profile, session_index=i)
        results.append(
            run_session(
                profile, learner, objective, session_index=i, store=store, book_rng=book_rng
            )
        )
    return results
