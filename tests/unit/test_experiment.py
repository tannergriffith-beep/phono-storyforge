# tests/unit/test_experiment.py
#
# Unit tests for the GATE experiment (Phase 3, Day 7). These lock in the thesis:
# over the same simulated learners, evidence-adaptive targeting beats a fixed
# scope-and-sequence on the fair metrics (benchmark reading accuracy and true
# latent mastery), and the experiment is reproducible.

from eval.experiments.adaptive_vs_static import (
    run_experiment,
    static_objective,
)


def test_adaptive_beats_static_on_reading_accuracy() -> None:
    result = run_experiment(num_learners=12, num_sessions=25)
    last = result.num_sessions - 1
    assert result.adaptive["probe_accuracy"][last] > result.static["probe_accuracy"][last]


def test_adaptive_beats_static_on_true_mastery() -> None:
    result = run_experiment(num_learners=12, num_sessions=25)
    last = result.num_sessions - 1
    assert result.adaptive["true_mean_mastery"][last] > result.static["true_mean_mastery"][last]


def test_advantage_emerges_from_a_tied_start() -> None:
    """The arms start identical (paired by seed) and adaptive earns a sustained
    accuracy lead by the end.

    NOTE: against the de-circularized learner (logistic emission, no ZPD gate,
    forgetting) the gap does NOT widen monotonically — early on every grapheme is
    hard for both arms, so they track together, then adaptive pulls ahead and
    holds. We assert the honest property (absent at the tied start, clearly
    present at the end), not the old "gap always widens" narrative that the
    self-consistent learner produced.
    """
    result = run_experiment(num_learners=20, num_sessions=35)
    start_gap = (
        result.adaptive["probe_accuracy"][0] - result.static["probe_accuracy"][0]
    )
    final_gap = (
        result.adaptive["probe_accuracy"][-1] - result.static["probe_accuracy"][-1]
    )
    assert abs(start_gap) < 1e-9          # identical paired start, no advantage yet
    assert final_gap > 0.02               # a clear, sustained lead by the end


def test_experiment_is_reproducible() -> None:
    a = run_experiment(num_learners=8, num_sessions=15)
    b = run_experiment(num_learners=8, num_sessions=15)
    assert a.adaptive == b.adaptive
    assert a.static == b.static


def test_static_control_never_targets_unteachable() -> None:
    targets = {static_objective(i).target_grapheme for i in range(200)}
    assert "ng" not in targets and "ph" not in targets
