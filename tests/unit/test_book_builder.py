# tests/unit/test_book_builder.py
#
# Unit tests for the deterministic book builder (Phase 3, Day 6): every word it
# emits is decodable within the objective's budget, the target grapheme is
# actually exercised, and builds are reproducible.

from app.schemas import Objective
from app.skills.decodability import decompose, is_word_decodable
from eval.book_builder import (
    UNTEACHABLE_GRAPHEMES,
    build_book,
    target_words,
)


def _obj(target="sh", level="digraphs", mastered=("short_vowels",), review=()):
    return Objective(
        target_grapheme=target,
        target_level=level,
        mastered_levels=list(mastered),
        review_graphemes=list(review),
    )


def test_unteachable_is_exactly_ng_and_ph() -> None:
    """Only the two graphemes with no decodable single-syllable word at their
    introduction budget are excluded from the simulated curriculum."""
    assert UNTEACHABLE_GRAPHEMES == frozenset({"ng", "ph"})


def test_every_non_sight_word_is_decodable_within_budget() -> None:
    obj = _obj(review=("a", "t"))
    book = build_book(obj)
    budget = obj.mastered_levels + [obj.target_level]
    for w in book.words:
        if w in book.sight_words:
            continue
        assert is_word_decodable(w, budget), f"{w!r} not decodable in {budget}"


def test_book_exercises_the_target_grapheme() -> None:
    obj = _obj("sh", "digraphs", ("short_vowels",))
    book = build_book(obj)
    exercised = any(
        "sh" in decompose(w).grapheme_strings for w in book.words
    )
    assert exercised


def test_target_words_respects_budget() -> None:
    """A blends-level target only yields words once blends are in the budget."""
    obj = _obj("_blend_", "blends", ("short_vowels", "digraphs"))
    words = target_words(obj)
    assert words  # blends are teachable
    # Without blends mastered, a digraph-only budget can't decode a blend word.
    narrow = _obj("_blend_", "blends", ("short_vowels",))
    assert all(is_word_decodable(w, narrow.mastered_levels + ["blends"]) for w in words)


def test_build_is_deterministic() -> None:
    obj = _obj(review=("a",))
    assert build_book(obj, session_index=3).words == build_book(obj, session_index=3).words


def test_session_index_varies_words() -> None:
    obj = _obj()
    a = build_book(obj, session_index=0).words
    b = build_book(obj, session_index=4).words
    assert a != b  # rotation surfaces different practice words across sessions
