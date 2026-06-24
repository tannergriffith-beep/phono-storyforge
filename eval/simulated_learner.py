# eval/simulated_learner.py
#
# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop tutor — the simulated learner (Phase 3, Day 6).
#
# This is the ground-truth "child" that lets us close and measure the loop
# WITHOUT real audio. It is pure Python (NOT an LLM): an LLM child would be slow,
# non-deterministic, and unable to expose its own latent knowledge for scoring.
#
# The learner holds TRUE per-grapheme mastery, kept entirely separate from the
# tutor's BKT *estimate*. Given a book it produces a read-aloud transcript whose
# miscues are driven by that latent mastery (errors are more likely on
# unmastered graphemes), and practice nudges the true mastery up as a side
# effect — so the child genuinely learns over sessions. A seeded RNG makes every
# read reproducible, which is what makes the N-session experiment a stable chart.
# =============================================================================

from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.phonics_db import GRAPHEME_INVENTORY, LEVEL_SEQUENCE
from app.skills.decodability import GraphemeHit, decompose

_VOWELS = "aeiou"
_CONSONANTS = "bcdfghjklmnpqrstvwxyz"

# Graphemes the deterministic corpus cannot teach (ng, ph): they are assumed
# already known so they never gate progress. Imported lazily to avoid a circular
# import (book_builder imports nothing from here).
from eval.book_builder import UNTEACHABLE_GRAPHEMES


@dataclass
class SimulatedLearner:
    """A latent-mastery child that reads books aloud and learns from practice."""

    learner_id: str
    rng: random.Random
    true_mastery: dict[str, float]
    # Emission model: P(read grapheme correctly) = m*(1-slip) + (1-m)*guess.
    slip: float = 0.04
    guess: float = 0.10
    # Learning: true mastery moves toward 1.0 by this fraction of the gap per
    # practice (a correct read consolidates more than a failed attempt).
    learn_rate: float = 0.12
    fail_learn_factor: float = 0.35
    # Realism: rates for non-error reading behaviours.
    hesitation_rate: float = 0.05
    self_correct_floor_mastery: float = 0.45
    sight_words: set[str] = field(default_factory=set)

    @classmethod
    def new(
        cls,
        learner_id: str,
        *,
        seed: int,
        sight_words: set[str] | None = None,
    ) -> "SimulatedLearner":
        """Creates a heterogeneous learner with a randomized latent profile.

        Each child gets a per-learner aptitude plus per-grapheme noise, and
        earlier-introduced graphemes start a little stronger — so the population
        has genuinely different gaps for the planner to adapt to. Unteachable
        graphemes start fully mastered so they never block progress.
        """
        rng = random.Random(seed)
        aptitude = rng.uniform(0.0, 0.30)
        true_mastery: dict[str, float] = {}
        for grapheme, level in GRAPHEME_INVENTORY:
            if grapheme in UNTEACHABLE_GRAPHEMES:
                true_mastery[grapheme] = 1.0
                continue
            level_idx = LEVEL_SEQUENCE.index(level)
            start = aptitude + rng.uniform(-0.10, 0.20) - 0.015 * level_idx
            true_mastery[grapheme] = min(0.6, max(0.0, start))
        return cls(
            learner_id=learner_id,
            rng=rng,
            true_mastery=true_mastery,
            sight_words=set(sight_words or set()),
        )

    # -- reading -----------------------------------------------------------

    def _p_correct(self, grapheme: str) -> float:
        m = self.true_mastery.get(grapheme, 0.0)
        return m * (1.0 - self.slip) + (1.0 - m) * self.guess

    def _swap_letter(self, ch: str) -> str:
        pool = _VOWELS if ch in _VOWELS else _CONSONANTS
        choices = [c for c in pool if c != ch] or list(pool)
        return self.rng.choice(choices)

    def _corrupt(self, word: str, hit: GraphemeHit) -> str:
        """Returns a misread of `word` that differs at one failed grapheme."""
        i = min(hit.span[0], len(word) - 1)
        wrong = word[:i] + self._swap_letter(word[i]) + word[i + 1 :]
        return wrong if wrong != word else word + self.rng.choice(_VOWELS)

    def _practice(self, hits: list[GraphemeHit], correct_flags: list[bool]) -> None:
        for hit, ok in zip(hits, correct_flags):
            g = hit.grapheme
            m = self.true_mastery.get(g, 0.0)
            rate = self.learn_rate if ok else self.learn_rate * self.fail_learn_factor
            self.true_mastery[g] = min(1.0, m + rate * (1.0 - m))

    def _read_word(self, word: str) -> list[str]:
        """Reads one expected word, returning the spoken token(s) for it."""
        decomp = decompose(word, mastered_levels=LEVEL_SEQUENCE, sight_words=self.sight_words)

        # Memorized sight words (and trivial tokens) are recalled, not decoded.
        if decomp.is_sight_word or not decomp.graphemes:
            return [word] if self.rng.random() < 0.97 else []

        hits = decomp.graphemes
        flags = [self.rng.random() < self._p_correct(h.grapheme) for h in hits]
        self._practice(hits, flags)

        if all(flags):
            if self.rng.random() < self.hesitation_rate:
                return [word, word]  # repetition (hesitation) — still correct
            return [word]

        failed = [h for h, ok in zip(hits, flags) if not ok]
        wrong = self._corrupt(word, failed[0])
        avg_failed_mastery = sum(self.true_mastery.get(h.grapheme, 0.0) for h in failed) / len(failed)
        frac_failed = len(failed) / len(hits)

        # A near-known word that slipped tends to be self-corrected.
        if avg_failed_mastery >= self.self_correct_floor_mastery and self.rng.random() < 0.6:
            return [wrong, word]  # self-correction
        # A word that mostly fell apart is sometimes skipped.
        if frac_failed >= 0.6 and self.rng.random() < 0.4:
            return []  # omission
        return [wrong]  # substitution

    def read(self, words: list[str], *, sight_words: set[str] | None = None) -> list[str]:
        """Reads a book's word sequence aloud, returning the spoken transcript.

        `sight_words` (the book's connectors plus the learner's own) are treated
        as memorized for this read; they do not exercise decoding.
        """
        prior = self.sight_words
        if sight_words is not None:
            self.sight_words = prior | sight_words
        try:
            spoken: list[str] = []
            for w in words:
                spoken.extend(self._read_word(w))
            return spoken
        finally:
            self.sight_words = prior

    # -- ground-truth metrics (for the experiment) -------------------------

    def true_mean_mastery(self, graphemes: list[str]) -> float:
        if not graphemes:
            return 0.0
        return sum(self.true_mastery.get(g, 0.0) for g in graphemes) / len(graphemes)

    def true_num_mastered(self, graphemes: list[str], threshold: float) -> int:
        return sum(1 for g in graphemes if self.true_mastery.get(g, 0.0) >= threshold)
