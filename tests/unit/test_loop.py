# tests/unit/test_loop.py
#
# Unit tests for the closed loop (Phase 3, Day 6): one session updates the tutor
# profile from real miscue evidence, the profile evolves across sessions, and
# the run is reproducible.

from app.skills.planner import select_objective
from eval.loop import (
    CURRICULUM_GRAPHEMES,
    new_tutor_profile,
    run_adaptive_loop,
    run_session,
)
from eval.simulated_learner import SimulatedLearner


def test_single_session_updates_profile() -> None:
    learner = SimulatedLearner.new("kid", seed=11)
    profile = new_tutor_profile("kid")
    objective = select_objective(profile, session_index=0)

    result = run_session(profile, learner, objective, session_index=0)

    assert profile.sessions_completed == 1
    assert result.assessment.total_words > 0
    assert result.delta.changes  # evidence moved at least one grapheme


def test_true_mastery_rises_over_sessions() -> None:
    learner = SimulatedLearner.new("kid", seed=11)
    profile = new_tutor_profile("kid")
    start = learner.true_mean_mastery(CURRICULUM_GRAPHEMES)

    results = run_adaptive_loop(profile, learner, num_sessions=25)

    assert results[-1].true_mean_mastery > start
    # The tutor's BKT estimate also climbs as evidence accrues.
    assert results[-1].est_mean_mastery > results[0].est_mean_mastery


def test_loop_is_reproducible() -> None:
    def run():
        learner = SimulatedLearner.new("kid", seed=99)
        profile = new_tutor_profile("kid")
        res = run_adaptive_loop(profile, learner, num_sessions=15)
        return [(r.objective.target_grapheme, round(r.true_mean_mastery, 6)) for r in res]

    assert run() == run()


def test_unteachable_never_targeted() -> None:
    """The planner must never stall on a grapheme the corpus can't teach."""
    learner = SimulatedLearner.new("kid", seed=11)
    profile = new_tutor_profile("kid")
    results = run_adaptive_loop(profile, learner, num_sessions=40)
    targets = {r.objective.target_grapheme for r in results}
    assert "ng" not in targets and "ph" not in targets
