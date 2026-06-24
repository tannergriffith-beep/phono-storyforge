# eval/experiments/robustness_sweep.py
#
# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop tutor — ROBUSTNESS SWEEP for the headline result.
#
# The de-circularized experiment (adaptive_vs_static.py) reports adaptive beats a
# fixed sequence on benchmark reading accuracy by +0.06 at one operating point
# (decay=0.03, discrimination a=7.0). A single point invites the objection that
# the win is a knife-edge of two hand-set constants. This sweep answers that: it
# re-runs the SAME paired experiment across a grid of the two de-circularizing
# constants and reports the final-session accuracy gap (adaptive - static) for
# every cell.
#
#   * decay         — how fast unpracticed graphemes are forgotten (the learning
#                     dynamic that replaced the ZPD gate). 0.0 turns forgetting
#                     OFF entirely, the hardest case for adaptive.
#   * discrimination (a) — the logistic emission slope; how sharply P(correct)
#                     responds to mastery crossing item difficulty.
#
# It reuses adaptive_vs_static's exact per-run machinery (same probe, same loop,
# same aggregation), only overriding the two swept constants on each learner, so
# the (decay=0.03, a=7.0) cell reproduces the committed headline gap exactly.
#
# Fully deterministic and LLM-free, like the experiment it sweeps.
# =============================================================================

from __future__ import annotations

import argparse
import csv
import statistics
from dataclasses import dataclass
from pathlib import Path

from app.skills.planner import select_objective
from eval.experiments.adaptive_vs_static import (
    SessionRow,
    _probe,
    static_objective,
)
from eval.loop import new_tutor_profile, run_session
from eval.simulated_learner import SimulatedLearner

_OUTPUT_DIR = Path(__file__).resolve().parent / "results"

# The grid swept over the two de-circularizing constants.
DECAYS: tuple[float, ...] = (0.0, 0.02, 0.03, 0.05)
DISCRIMINATIONS: tuple[float, ...] = (5.0, 7.0, 9.0)


def _run_one(
    seed: int,
    num_sessions: int,
    *,
    adaptive: bool,
    decay: float,
    discrimination: float,
) -> list[SessionRow]:
    """Identical to adaptive_vs_static._run_one, but overrides the two swept
    constants on the learner before the loop runs. Kept in lockstep with the
    committed runner so the baseline cell reproduces the headline numbers."""
    learner = SimulatedLearner.new(f"learner-{seed}", seed=seed)
    learner.decay = decay
    learner.discrimination = discrimination
    profile = new_tutor_profile(f"learner-{seed}")
    rows: list[SessionRow] = []
    for i in range(num_sessions):
        objective = (
            select_objective(profile, session_index=i)
            if adaptive
            else static_objective(i)
        )
        result = run_session(
            profile, learner, objective, session_index=i, num_target=6, book_length=10
        )
        acc, wcpm = _probe(learner, i)
        rows.append(
            SessionRow(
                true_mean_mastery=result.true_mean_mastery,
                true_num_mastered=result.true_num_mastered,
                probe_accuracy=acc,
                probe_wcpm=wcpm,
            )
        )
    return rows


def _final_mean(runs: list[list[SessionRow]], attr: str) -> float:
    last = len(runs[0]) - 1
    return statistics.mean(getattr(run[last], attr) for run in runs)


@dataclass
class ConfigGap:
    decay: float
    discrimination: float
    accuracy_gap: float
    mastery_gap: float
    wcpm_gap: float
    num_mastered_gap: float


def sweep(num_learners: int = 30, num_sessions: int = 40) -> list[ConfigGap]:
    """Runs the full decay x discrimination grid and returns the final-session
    gaps (adaptive - static) for each cell."""
    out: list[ConfigGap] = []
    for decay in DECAYS:
        for a in DISCRIMINATIONS:
            adaptive_runs = [
                _run_one(s, num_sessions, adaptive=True, decay=decay, discrimination=a)
                for s in range(num_learners)
            ]
            static_runs = [
                _run_one(s, num_sessions, adaptive=False, decay=decay, discrimination=a)
                for s in range(num_learners)
            ]
            out.append(
                ConfigGap(
                    decay=decay,
                    discrimination=a,
                    accuracy_gap=_final_mean(adaptive_runs, "probe_accuracy")
                    - _final_mean(static_runs, "probe_accuracy"),
                    mastery_gap=_final_mean(adaptive_runs, "true_mean_mastery")
                    - _final_mean(static_runs, "true_mean_mastery"),
                    wcpm_gap=_final_mean(adaptive_runs, "probe_wcpm")
                    - _final_mean(static_runs, "probe_wcpm"),
                    num_mastered_gap=_final_mean(adaptive_runs, "true_num_mastered")
                    - _final_mean(static_runs, "true_num_mastered"),
                )
            )
    return out


def write_csv(gaps: list[ConfigGap], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["decay", "discrimination", "accuracy_gap", "mastery_gap",
             "wcpm_gap", "num_mastered_gap"]
        )
        for g in gaps:
            writer.writerow(
                [g.decay, g.discrimination, round(g.accuracy_gap, 4),
                 round(g.mastery_gap, 4), round(g.wcpm_gap, 4),
                 round(g.num_mastered_gap, 4)]
            )
    return path


def _print_table(gaps: list[ConfigGap], num_learners: int, num_sessions: int) -> None:
    print(
        f"\nRobustness sweep: final-session accuracy gap (adaptive - static), "
        f"n={num_learners}, {num_sessions} sessions"
    )
    print(f"  {len(gaps)} configs ({len(DECAYS)} decays x {len(DISCRIMINATIONS)} discriminations)\n")
    print(f"  {'decay':>6} {'a':>5} {'acc_gap':>9} {'mastery_gap':>12} {'wcpm_gap':>9} {'num_mast_gap':>13}")
    for g in gaps:
        print(
            f"  {g.decay:>6.2f} {g.discrimination:>5.1f} {g.accuracy_gap:>+9.4f} "
            f"{g.mastery_gap:>+12.4f} {g.wcpm_gap:>+9.3f} {g.num_mastered_gap:>+13.3f}"
        )
    pos = sum(1 for g in gaps if g.accuracy_gap > 0)
    worst = min(gaps, key=lambda g: g.accuracy_gap)
    print(
        f"\n  accuracy gap positive in {pos}/{len(gaps)} configs; "
        f"min = {worst.accuracy_gap:+.4f} at decay={worst.decay}, a={worst.discrimination}"
    )
    if pos < len(gaps):
        print("  WARNING: adaptive does NOT win on accuracy in every config (see above).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Robustness sweep for adaptive-vs-static.")
    parser.add_argument("--learners", type=int, default=30)
    parser.add_argument("--sessions", type=int, default=40)
    parser.add_argument("--outdir", type=Path, default=_OUTPUT_DIR)
    args = parser.parse_args()

    gaps = sweep(num_learners=args.learners, num_sessions=args.sessions)
    _print_table(gaps, args.learners, args.sessions)
    csv_path = write_csv(gaps, args.outdir / "robustness_sweep.csv")
    print(f"\nWrote sweep table: {csv_path}")


if __name__ == "__main__":
    main()
