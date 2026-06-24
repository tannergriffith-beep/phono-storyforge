# tests/unit/test_simulated_learner.py
#
# Unit tests for the simulated learner (Phase 3, Day 6): reproducibility, that
# miscues track latent mastery, and that practice raises true mastery.

from app.phonics_db import GRAPHEME_INVENTORY
from eval.book_builder import UNTEACHABLE_GRAPHEMES
from eval.simulated_learner import SimulatedLearner


def test_same_seed_reads_identically() -> None:
    words = "ship shop fish dish cash".split()
    a = SimulatedLearner.new("kid", seed=7).read(words)
    b = SimulatedLearner.new("kid", seed=7).read(words)
    assert a == b


def test_different_seeds_differ() -> None:
    words = "ship shop fish dish cash hush rush shut".split()
    a = SimulatedLearner.new("kid", seed=1).read(words)
    b = SimulatedLearner.new("kid", seed=2).read(words)
    assert a != b


def test_strong_learner_reads_accurately() -> None:
    """A child with full latent mastery reads a decodable word list near-perfectly."""
    learner = SimulatedLearner.new("strong", seed=3)
    learner.true_mastery = {g: 1.0 for g, _ in GRAPHEME_INVENTORY}
    words = "ship shop fish dish cash stop clap".split()
    spoken = learner.read(words)
    # Every expected word appears in order (allowing repetitions); no losses.
    assert all(w in spoken for w in words)


def test_weak_learner_makes_errors() -> None:
    """A child with near-zero mastery mangles a hard word list."""
    learner = SimulatedLearner.new("weak", seed=3)
    learner.true_mastery = {g: 0.0 for g, _ in GRAPHEME_INVENTORY}
    words = "ship shop fish dish cash".split()
    spoken = learner.read(words)
    assert spoken != words


def test_practice_raises_true_mastery() -> None:
    learner = SimulatedLearner.new("kid", seed=5)
    learner.true_mastery["sh"] = 0.2
    before = learner.true_mastery["sh"]
    for _ in range(20):
        learner.read(["ship"])
    assert learner.true_mastery["sh"] > before


def test_unteachable_graphemes_start_mastered() -> None:
    learner = SimulatedLearner.new("kid", seed=5)
    for g in UNTEACHABLE_GRAPHEMES:
        assert learner.true_mastery[g] == 1.0
