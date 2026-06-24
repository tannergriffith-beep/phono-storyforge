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


def test_gap_widens_over_time() -> None:
    """The advantage should grow, not just exist at a single point."""
    result = run_experiment(num_learners=12, num_sessions=25)
    early_gap = (
        result.adaptive["probe_accuracy"][5] - result.static["probe_accuracy"][5]
    )
    late_gap = (
        result.adaptive["probe_accuracy"][-1] - result.static["probe_accuracy"][-1]
    )
    assert late_gap > early_gap


def test_experiment_is_reproducible() -> None:
    a = run_experiment(num_learners=8, num_sessions=15)
    b = run_experiment(num_learners=8, num_sessions=15)
    assert a.adaptive == b.adaptive
    assert a.static == b.static


def test_static_control_never_targets_unteachable() -> None:
    targets = {static_objective(i).target_grapheme for i in range(200)}
    assert "ng" not in targets and "ph" not in targets
