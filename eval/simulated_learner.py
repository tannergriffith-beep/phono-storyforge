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
#
# DE-CIRCULARIZATION (Stage D): this learner's generative process is deliberately
# NOT what BKT/the planner assume, so the experiment is not self-validating:
#   * Emission is logistic/IRT with per-grapheme difficulty (see _p_correct),
#     not the linear slip/guess BKT inverts — the tutor faces a model mismatch.
#   * Learning has NO prerequisite/ZPD gate (the planner's own thesis). Practice
#     works directly and unpracticed skills FORGET (_apply_forgetting), so
#     adaptive must earn its edge by revisiting each child's decaying frontier.
# =============================================================================

from __future__ import annotations

import math
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

# -----------------------------------------------------------------------------
# DE-CIRCULARIZATION (Stage D): per-grapheme item difficulty for the logistic
# emission model below. BKT parameterizes slip/guess by LEVEL only
# (bkt_params_for_level), so it is structurally blind to difficulty that varies
# *within* a level. Drawing a stable difficulty per grapheme (same realistic
# "some graphemes are intrinsically harder" structure for the whole population)
# gives the tutor's measurement model something it cannot represent — a genuine
# model mismatch, not the self-consistent slip/guess the old emission shared
# with BKT. Seeded so the table is identical on every run.
_DIFFICULTY_RNG = random.Random(20260624)
GRAPHEME_DIFFICULTY: dict[str, float] = {
    g: round(_DIFFICULTY_RNG.uniform(0.35, 0.75), 3) for g, _ in GRAPHEME_INVENTORY
}


@dataclass
class SimulatedLearner:
    """A latent-mastery child that reads books aloud and learns from practice."""

    learner_id: str
    rng: random.Random
    true_mastery: dict[str, float]
    seed: int = 0
    # Emission model (DE-CIRCULARIZED): a 4PL/IRT-style logistic, NOT the linear
    # slip/guess BKT inverts. P(correct) = guess + (1-slip-guess)*sigmoid(a*(m-b)),
    # where `b` is the grapheme's per-item difficulty (GRAPHEME_DIFFICULTY) and
    # `a` is the discrimination slope. guess/slip remain the floor (0.10) and the
    # ceiling miss (so P maxes at 1-slip=0.96). Because P is non-linear in m and
    # keyed on per-grapheme difficulty that BKT's level-uniform params cannot
    # express, the tutor must now estimate mastery under a model mismatch.
    slip: float = 0.04
    guess: float = 0.10
    discrimination: float = 7.0
    # Learning (DE-CIRCULARIZED): true mastery moves toward 1.0 by this fraction
    # of the gap per practice — with NO prerequisite/ZPD gate. The old learner
    # only consolidated a grapheme once its lower levels were mastered, which is
    # exactly the planner's own "target the lowest unmastered grapheme" thesis;
    # rewarding that made the experiment circular. Here practice works directly,
    # and instead unpracticed graphemes FORGET (decay below). Adaptive can now
    # only win by concentrating practice on each child's decaying frontier, not
    # by satisfying a built-in ZPD reward.
    learn_rate: float = 0.18
    fail_learn_factor: float = 0.15     # a misread grapheme barely sticks
    decay: float = 0.03                 # per-session forgetting of unpracticed graphemes
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
            seed=seed,
            sight_words=set(sight_words or set()),
        )

    # -- reading -----------------------------------------------------------

    def _p_correct(self, grapheme: str) -> float:
        """Logistic (IRT) emission keyed on per-grapheme difficulty.

        Deliberately NOT the linear m*(1-slip)+(1-m)*guess that BKT inverts: the
        sigmoid is non-linear in mastery and the difficulty `b` varies per
        grapheme within a level, which BKT's level-uniform slip/guess cannot
        represent. P ranges from `guess` (m << b) up to `1 - slip` (m >> b).
        """
        m = self.true_mastery.get(grapheme, 0.0)
        b = GRAPHEME_DIFFICULTY.get(grapheme, 0.55)
        sig = 1.0 / (1.0 + math.exp(-self.discrimination * (m - b)))
        return self.guess + (1.0 - self.slip - self.guess) * sig

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
        """Direct practice gain (no ZPD/prerequisite gate): mastery moves toward
        1.0 by `learn_rate` of the remaining gap; a misread grapheme barely
        sticks. The gate that the old learner used is gone on purpose — it was
        the planner's own thesis. The counterweight is forgetting (below)."""
        for hit, ok in zip(hits, correct_flags):
            g = hit.grapheme
            m = self.true_mastery.get(g, 0.0)
            rate = self.learn_rate if ok else self.learn_rate * self.fail_learn_factor
            self.true_mastery[g] = min(1.0, m + rate * (1.0 - m))

    def _apply_forgetting(self, practiced: set[str]) -> None:
        """Decay every teachable grapheme NOT practiced this session.

        This is the independent learning dynamic that replaces the ZPD gate: a
        skill the child did not rehearse this session slips. It rewards revisiting
        the child's actual frontier (what adaptive does) rather than marching a
        fixed schedule that lets off-schedule skills rot — an advantage that does
        NOT presuppose the planner's prerequisite premise."""
        for g, m in self.true_mastery.items():
            if g in practiced or g in UNTEACHABLE_GRAPHEMES:
                continue
            self.true_mastery[g] = m * (1.0 - self.decay)

    def _read_word(
        self, word: str, *, learn: bool = True, practiced: set[str] | None = None
    ) -> list[str]:
        """Reads one expected word, returning the spoken token(s) for it.

        When `learn` is False the read is a pure assessment — latent mastery is
        observed but not updated (used for the fixed benchmark probe). When
        learning, every decoded grapheme is recorded in `practiced` so the
        session-end forgetting pass knows what to spare.
        """
        decomp = decompose(word, mastered_levels=LEVEL_SEQUENCE, sight_words=self.sight_words)

        # Memorized sight words (and trivial tokens) are recalled, not decoded.
        if decomp.is_sight_word or not decomp.graphemes:
            return [word] if self.rng.random() < 0.97 else []

        hits = decomp.graphemes
        flags = [self.rng.random() < self._p_correct(h.grapheme) for h in hits]
        if learn:
            self._practice(hits, flags)
            if practiced is not None:
                practiced.update(h.grapheme for h in hits)

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

    def read(
        self,
        words: list[str],
        *,
        sight_words: set[str] | None = None,
        learn: bool = True,
    ) -> list[str]:
        """Reads a book's word sequence aloud, returning the spoken transcript.

        `sight_words` (the book's connectors plus the learner's own) are treated
        as memorized for this read; they do not exercise decoding. With
        `learn=False` the read does not change latent mastery (benchmark probe) —
        and forgetting is skipped too, so probing never perturbs the trajectory.
        """
        prior = self.sight_words
        if sight_words is not None:
            self.sight_words = prior | sight_words
        try:
            spoken: list[str] = []
            practiced: set[str] = set()
            for w in words:
                spoken.extend(self._read_word(w, learn=learn, practiced=practiced))
            if learn:
                self._apply_forgetting(practiced)
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
