# tests/unit/test_llm_book.py
#
# =============================================================================
# FLAGSHIP STAGE B (Part 1): unit tests for the verifier-gated LLM book source.
#
# These prove the production content engine behaves WITHOUT touching the network:
# the LLM is mocked via an injected StoryProposer. We assert the loop's hard
# guarantees — it never returns a book with a decodability violation, it feeds
# violations back and retries, it exercises the target grapheme, and it tags the
# generation source so the Stage-D flywheel can measure quality. The provider is
# shown to be a drop-in for the deterministic one through TutorSession unchanged.
# =============================================================================

from __future__ import annotations

import pytest

from app.schemas import Objective, StoryDraft
from app.store.learner_store import JSONLearnerStore
from app.store.session_log import JSONLSessionLogStore
from app.tutor.book_source import make_llm_book_provider
from app.tutor.llm_book import (
    BookGenerationError,
    GeneratedBook,
    generate_decodable_book,
)
from app.tutor.session import TutorSession


# A short-vowel objective targeting 'a'; budget is short_vowels only.
OBJECTIVE = Objective(
    target_grapheme="a",
    target_level="short_vowels",
    mastered_levels=[],
    review_graphemes=[],
    rationale="test",
)

# Decodable at short_vowels AND exercises 'a' (cat/sat/fat).
CLEAN = StoryDraft(title="The Cat", pages=["A cat sat.", "The cat is fat."])
# Decodable except 'ship' (needs the 'sh' digraph) -> one violation to feed back.
VIOLATION = StoryDraft(title="The Ship", pages=["A cat sat.", "The ship is big."])
# Decodable at short_vowels but contains no 'a' word -> off target.
OFFTARGET = StoryDraft(title="The Pig", pages=["The pig is big."])


class ScriptedProposer:
    """A fake StoryProposer that returns scripted drafts and records prompts.

    Returns each draft in turn; once exhausted it repeats the final draft, so a
    single 'always returns X' script just passes one draft.
    """

    def __init__(self, *drafts: StoryDraft) -> None:
        self.drafts = list(drafts)
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> StoryDraft:
        self.prompts.append(prompt)
        idx = min(len(self.prompts) - 1, len(self.drafts) - 1)
        return self.drafts[idx]


# ---------------------------------------------------------------------------
# generate_decodable_book — the verifier-gated loop
# ---------------------------------------------------------------------------


def test_clean_on_target_draft_passes_first_try() -> None:
    proposer = ScriptedProposer(CLEAN)
    book = generate_decodable_book(OBJECTIVE, proposer=proposer, length=12)

    assert isinstance(book, GeneratedBook)
    assert book.generation_source == "llm"
    assert book.target_grapheme == "a"
    assert "cat" in book.text and "sat" in book.text
    assert len(proposer.prompts) == 1


def test_violation_is_fed_back_and_retried() -> None:
    proposer = ScriptedProposer(VIOLATION, CLEAN)
    book = generate_decodable_book(OBJECTIVE, proposer=proposer, length=12)

    assert book.generation_source == "llm"
    # Two attempts: the first violated, the second was clean.
    assert len(proposer.prompts) == 2
    # The offending word was surfaced to the writer on the retry.
    assert "ship" in proposer.prompts[1]


def test_never_returns_a_book_with_a_violation() -> None:
    proposer = ScriptedProposer(VIOLATION)  # always violates
    with pytest.raises(BookGenerationError):
        generate_decodable_book(OBJECTIVE, proposer=proposer, length=12, max_attempts=3)
    assert len(proposer.prompts) == 3  # tried up to the cap


def test_decodable_but_off_target_is_tagged_not_discarded() -> None:
    proposer = ScriptedProposer(OFFTARGET)  # decodable, never hits 'a'
    book = generate_decodable_book(OBJECTIVE, proposer=proposer, length=12, max_attempts=3)

    assert book.generation_source == "llm_offtarget"
    # Decodable content is still safe to read.
    assert book.words
    assert len(proposer.prompts) == 3


def test_on_target_draft_is_preferred_over_earlier_off_target() -> None:
    proposer = ScriptedProposer(OFFTARGET, CLEAN)
    book = generate_decodable_book(OBJECTIVE, proposer=proposer, length=12)

    assert book.generation_source == "llm"
    assert "cat" in book.text
    assert len(proposer.prompts) == 2


def test_generated_book_satisfies_booklike() -> None:
    book = generate_decodable_book(OBJECTIVE, proposer=ScriptedProposer(CLEAN))
    assert book.text == "A cat sat. The cat is fat."
    assert book.words == ["A", "cat", "sat.", "The", "cat", "is", "fat."]
    assert isinstance(book.sight_words, set)


# ---------------------------------------------------------------------------
# make_llm_book_provider — protocol + fallback policy
# ---------------------------------------------------------------------------


def test_provider_returns_llm_book_on_success() -> None:
    provider = make_llm_book_provider(ScriptedProposer(CLEAN))
    book = provider(
        OBJECTIVE,
        session_index=0,
        sight_words=set(),
        num_target=6,
        length=12,
        interest="cats",
        age=6,
    )
    assert book.generation_source == "llm"


def test_provider_falls_back_to_deterministic_with_warning() -> None:
    provider = make_llm_book_provider(ScriptedProposer(VIOLATION), max_attempts=2)
    with pytest.warns(RuntimeWarning):
        book = provider(
            OBJECTIVE,
            session_index=0,
            sight_words=set(),
            num_target=6,
            length=12,
        )
    # The fallback book is guaranteed decodable and tagged for the flywheel.
    assert book.generation_source == "deterministic_fallback"
    assert book.words


# ---------------------------------------------------------------------------
# Drop-in through TutorSession (session.py orchestration unchanged)
# ---------------------------------------------------------------------------


@pytest.fixture
def stores(tmp_path):
    return (
        JSONLearnerStore(tmp_path / "profiles"),
        JSONLSessionLogStore(tmp_path / "sessions"),
    )


def test_tutor_session_uses_llm_provider_and_logs_source(stores) -> None:
    store, log_store = stores
    tutor = TutorSession(
        store,
        log_store=log_store,
        book_provider=make_llm_book_provider(ScriptedProposer(CLEAN)),
    )
    prepared = tutor.prepare("kid", interest="cats", age=6)
    assert prepared.objective.target_grapheme == "a"  # fresh learner frontier

    outcome = tutor.record_read(prepared, prepared.book.text)  # perfect read
    assert outcome.assessment.accuracy == pytest.approx(1.0)
    assert outcome.log.generation_source == "llm"

    # Persisted to the session log with the source intact.
    logs = log_store.list("kid")
    assert logs[0].generation_source == "llm"


def test_tutor_session_logs_fallback_source(stores) -> None:
    store, log_store = stores
    tutor = TutorSession(
        store,
        log_store=log_store,
        book_provider=make_llm_book_provider(ScriptedProposer(VIOLATION), max_attempts=2),
    )
    with pytest.warns(RuntimeWarning):
        prepared = tutor.prepare("kid")
    outcome = tutor.record_read(prepared, prepared.book.text)
    assert outcome.log.generation_source == "deterministic_fallback"
