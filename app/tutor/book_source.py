# app/tutor/book_source.py
#
# =============================================================================
# FLAGSHIP STAGE A: the swappable content seam.
#
# The TutorSession orchestrator does not care HOW a decodable practice book is
# produced — only that it gets words to put in front of the child and the sight
# words to exclude from grapheme attribution. That contract is `BookProvider`.
#
# Stage A reuses the deterministic, offline book builder from the experiment
# (eval/book_builder.py) as the default provider, so the real loop runs today
# with zero LLM dependency. Stage B replaces this single function with the
# verifier-gated Gemini generator (LLM proposes -> check_decodability proves)
# without touching session.py.
#
# The eval import is deliberately confined to THIS adapter (and lazily, at call
# time) so the durable orchestrator stays free of any eval/ dependency.
# =============================================================================

from __future__ import annotations

import random
from typing import Protocol

from app.schemas import LearnerProfile, Objective


class BookLike(Protocol):
    """The minimal book shape the tutor loop consumes (eval's Book satisfies it)."""

    title: str
    words: list[str]
    target_grapheme: str
    sight_words: set[str]

    @property
    def text(self) -> str: ...


class BookProvider(Protocol):
    """Produces a decodable practice book for a learning objective."""

    def __call__(
        self,
        objective: Objective,
        *,
        session_index: int,
        sight_words: set[str],
        num_target: int,
        length: int,
        rng: random.Random | None = None,
    ) -> BookLike: ...


def deterministic_book_provider(
    objective: Objective,
    *,
    session_index: int,
    sight_words: set[str],
    num_target: int,
    length: int,
    rng: random.Random | None = None,
) -> BookLike:
    """Stage-A default: the offline decodable builder from the experiment."""
    from eval.book_builder import build_book

    return build_book(
        objective,
        session_index=session_index,
        num_target=num_target,
        length=length,
        sight_words=sight_words,
        rng=rng,
    )


def unteachable_graphemes() -> frozenset[str]:
    """Graphemes the deterministic corpus can never exercise (e.g. 'ng', 'ph').

    With the Stage-A book source these must be pre-mastered, or the planner will
    keep targeting a grapheme it can never get evidence for and the loop stalls.
    Stage B's generator can teach them, at which point this seeding goes away.
    """
    from eval.book_builder import UNTEACHABLE_GRAPHEMES

    return UNTEACHABLE_GRAPHEMES


def new_learner_profile(learner_id: str, **kwargs) -> LearnerProfile:
    """A fresh profile with the Stage-A unteachable graphemes seeded as mastered."""
    profile = LearnerProfile.new(learner_id, **kwargs)
    for grapheme in unteachable_graphemes():
        mastery = profile.masteries.get(grapheme)
        if mastery is not None:
            mastery.p_mastery = 1.0
    return profile
