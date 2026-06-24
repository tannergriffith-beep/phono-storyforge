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
    # How the book was produced; consumed by SessionLog for the content flywheel.
    # Optional: providers that don't set it are read defensively as "deterministic".
    generation_source: str

    @property
    def text(self) -> str: ...


class BookProvider(Protocol):
    """Produces a decodable practice book for a learning objective.

    `interest`/`age` are optional personalization inputs: the LLM provider uses
    them for theme and tone, while the deterministic builder ignores them. They
    default so the protocol stays satisfiable by either provider.
    """

    def __call__(
        self,
        objective: Objective,
        *,
        session_index: int,
        sight_words: set[str],
        num_target: int,
        length: int,
        interest: str = "",
        age: int = 6,
        rng: random.Random | None = None,
    ) -> BookLike: ...


def deterministic_book_provider(
    objective: Objective,
    *,
    session_index: int,
    sight_words: set[str],
    num_target: int,
    length: int,
    interest: str = "",
    age: int = 6,
    rng: random.Random | None = None,
) -> BookLike:
    """Stage-A default: the offline decodable builder from the experiment.

    `interest`/`age` are accepted for protocol compatibility but unused — the
    deterministic builder is word-list based and does not personalize.
    """
    from eval.book_builder import build_book

    return build_book(
        objective,
        session_index=session_index,
        num_target=num_target,
        length=length,
        sight_words=sight_words,
        rng=rng,
    )


def make_llm_book_provider(
    proposer=None,
    *,
    max_attempts: int = 4,
    fallback: BookProvider = deterministic_book_provider,
) -> BookProvider:
    """Builds the Stage-B verifier-gated LLM BookProvider.

    Returns a provider matching the BookProvider protocol exactly, so it drops
    into TutorSession in place of `deterministic_book_provider`. Policy:
      - decodable + on-target  -> the LLM book (generation_source="llm")
      - decodable, off-target  -> the LLM book (generation_source="llm_offtarget")
      - never reaches decodable -> a loud warning + the guaranteed-decodable
        `fallback` book, re-tagged generation_source="deterministic_fallback"
        so degradation is logged, never silent.

    `proposer` is the injectable LLM seam (a `StoryProposer`); when omitted it is
    built lazily from a Gemini client on first use, so importing this module and
    constructing the provider never require credentials.
    """
    import warnings

    from app.tutor.llm_book import (
        BookGenerationError,
        generate_decodable_book,
        make_gemini_proposer,
    )

    def _provider(
        objective: Objective,
        *,
        session_index: int,
        sight_words: set[str],
        num_target: int,
        length: int,
        interest: str = "",
        age: int = 6,
        rng: random.Random | None = None,
    ) -> BookLike:
        active = proposer if proposer is not None else make_gemini_proposer()
        try:
            return generate_decodable_book(
                objective,
                proposer=active,
                session_index=session_index,
                sight_words=sight_words,
                num_target=num_target,
                length=length,
                interest=interest,
                age=age,
                rng=rng,
                max_attempts=max_attempts,
            )
        except BookGenerationError as exc:
            warnings.warn(
                f"LLM book generation failed for target "
                f"'{objective.target_grapheme}'; falling back to the "
                f"deterministic builder. Cause: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            book = fallback(
                objective,
                session_index=session_index,
                sight_words=sight_words,
                num_target=num_target,
                length=length,
                interest=interest,
                age=age,
                rng=rng,
            )
            # Tag the fallback so the flywheel can measure the LLM's failure rate.
            try:
                book.generation_source = "deterministic_fallback"
            except (AttributeError, ValueError):
                pass
            return book

    return _provider


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
