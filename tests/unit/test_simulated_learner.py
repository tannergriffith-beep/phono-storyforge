# tests/unit/test_simulated_learner.py
#
# Unit tests for the simulated learner (Phase 3, Day 6): reproducibility, that
# miscues track latent mastery, and that practice raises true mastery.
#
# Stage D (de-circularization) added tests pinning the two deliberate mismatches
# with BKT/the planner: a logistic/IRT emission keyed on per-grapheme difficulty
# (not the linear slip/guess BKT inverts) and learning with NO prerequisite/ZPD
# gate plus forgetting of unpracticed skills.

import math

from app.phonics_db import GRAPHEME_INVENTORY, LEVEL_SEQUENCE
from eval.book_builder import UNTEACHABLE_GRAPHEMES
from eval.simulated_learner import GRAPHEME_DIFFICULTY, SimulatedLearner


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


# -- de-circularization: emission is logistic/IRT, not BKT's linear slip/guess --


def test_emission_matches_logistic_not_linear() -> None:
    """P(correct) follows the 4PL logistic on per-grapheme difficulty, and is
    measurably different from the linear m*(1-slip)+(1-m)*guess BKT inverts."""
    learner = SimulatedLearner.new("kid", seed=1)
    g = "sh"
    learner.true_mastery[g] = 0.5
    b = GRAPHEME_DIFFICULTY[g]
    expected = learner.guess + (1.0 - learner.slip - learner.guess) * (
        1.0 / (1.0 + math.exp(-learner.discrimination * (0.5 - b)))
    )
    assert learner._p_correct(g) == expected
    linear = 0.5 * (1.0 - learner.slip) + 0.5 * learner.guess
    assert abs(learner._p_correct(g) - linear) > 1e-3  # genuinely not the BKT model


def test_harder_grapheme_is_read_worse_at_equal_mastery() -> None:
    """At identical mastery, a higher-difficulty grapheme has lower P(correct) —
    item difficulty BKT's level-uniform params cannot represent."""
    easy = min(GRAPHEME_DIFFICULTY, key=GRAPHEME_DIFFICULTY.get)
    hard = max(GRAPHEME_DIFFICULTY, key=GRAPHEME_DIFFICULTY.get)
    learner = SimulatedLearner.new("kid", seed=1)
    learner.true_mastery[easy] = 0.6
    learner.true_mastery[hard] = 0.6
    assert learner._p_correct(easy) > learner._p_correct(hard)


# -- de-circularization: no ZPD gate, plus forgetting of unpracticed skills -----


def test_learning_has_no_prerequisite_gate() -> None:
    """A late-level grapheme learns from practice even with ZERO prerequisite
    mastery. The old learner gated this behind prereqs (the planner's thesis);
    the de-circularized learner does not."""
    learner = SimulatedLearner.new("kid", seed=5)
    learner.true_mastery = {g: 0.0 for g, _ in GRAPHEME_INVENTORY}
    late_level = LEVEL_SEQUENCE[-1]
    target = next(g for g, lvl in GRAPHEME_INVENTORY if lvl == late_level)
    learner._practice(
        [type("H", (), {"grapheme": target, "level": late_level})()],
        [True],
    )
    assert learner.true_mastery[target] > 0.0


def test_unpracticed_graphemes_forget() -> None:
    """A skill the child does not rehearse in a session decays."""
    learner = SimulatedLearner.new("kid", seed=5)
    learner.true_mastery["oa"] = 0.8
    for _ in range(5):
        learner.read(["ship"])  # exercises sh/i/p, never 'oa'
    assert learner.true_mastery["oa"] < 0.8


def test_probe_read_neither_learns_nor_forgets() -> None:
    """With learn=False the read is a pure assessment: no practice gain and no
    forgetting, so probing never perturbs the teaching trajectory."""
    learner = SimulatedLearner.new("kid", seed=5)
    before = dict(learner.true_mastery)
    learner.read(["ship", "boat", "cake"], learn=False)
    assert learner.true_mastery == before
