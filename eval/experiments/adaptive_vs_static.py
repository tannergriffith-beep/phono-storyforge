# eval/experiments/adaptive_vs_static.py
#
# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop tutor — THE EVIDENCE EXPERIMENT (Phase 3, GATE)
#
# The whole thesis in one run: does choosing what to teach from the child's own
# miscue evidence beat a fixed scope-and-sequence that ignores it?
#
# Two arms over the SAME simulated learners (paired by seed, identical latent
# start):
#   - ADAPTIVE: each session select_objective(profile) targets the lowest
#     unmastered grapheme from the tutor's BKT estimate of THIS child.
#   - STATIC:   a fixed curriculum march, identical for every child, that never
#     looks at the evidence.
#
# Both close the same loop (deterministic book -> simulated read -> miscue
# analysis -> BKT update). We track each child's TRUE latent mastery and their
# reading of a FIXED benchmark probe (the same passage for both arms, so the
# fluency comparison is fair). Output: a CSV of the per-session numbers (the
# fallback deliverable that stands on its own) and a matplotlib chart.
#
# Fully deterministic and LLM-free, so the result reproduces exactly.
# =============================================================================

from __future__ import annotations

import argparse
import csv
import random
import statistics
from dataclasses import dataclass
from pathlib import Path

from app.phonics_db import GRAPHEME_LEVEL, LEVEL_SEQUENCE, MASTERY_THRESHOLD
from app.schemas import Objective
from app.skills.alignment import assess
from app.skills.planner import select_objective
from eval.loop import (
    CURRICULUM_GRAPHEMES,
    estimate_duration,
    new_tutor_profile,
    run_session,
)
from eval.simulated_learner import SimulatedLearner

# A fixed benchmark passage spanning the scope-and-sequence. Both arms' children
# read this SAME probe each session (without learning from it), so differences
# in probe accuracy/WCPM reflect real skill, not how hard each arm's books were.
PROBE_WORDS: list[str] = (
    "cat dog sun bed pig top mud "
    "ship chop fish that whip duck rock "
    "stop clap fast jump hand milk "
    "cake bike home rope cute "
    "car corn bird fur "
    "rain feet boat high moon cow boy "
    "all king honk my happy cats jumping"
).split()

_OUTPUT_DIR = Path(__file__).resolve().parent / "results"


def static_objective(session_index: int, *, sessions_per_target: int = 3) -> Objective:
    """The control policy: march through the teachable curriculum on a fixed
    cadence, identical for every learner, ignoring all evidence.

    Each target declares the levels strictly before it as 'mastered' (assumed by
    the schedule), so a child who is actually behind is pushed content above
    their reach — exactly the failure mode adaptive targeting avoids.
    """
    idx = (session_index // sessions_per_target) % len(CURRICULUM_GRAPHEMES)
    grapheme = CURRICULUM_GRAPHEMES[idx]
    level = GRAPHEME_LEVEL[grapheme]
    mastered = LEVEL_SEQUENCE[: LEVEL_SEQUENCE.index(level)]
    return Objective(
        target_grapheme=grapheme,
        target_level=level,
        mastered_levels=mastered,
        review_graphemes=[],
    )


def _probe(learner: SimulatedLearner, session_index: int) -> tuple[float, float]:
    """Administers the fixed benchmark probe without changing latent mastery.

    Uses an isolated RNG so probing never perturbs the teaching trajectory.
    """
    saved_rng = learner.rng
    learner.rng = random.Random(learner.seed * 100_003 + 7919 + session_index)
    try:
        spoken = learner.read(PROBE_WORDS, learn=False)
    finally:
        learner.rng = saved_rng
    text = " ".join(PROBE_WORDS)
    provisional = assess(text, spoken, duration_seconds=1.0)
    duration = estimate_duration(len(PROBE_WORDS), provisional.errors)
    result = assess(text, spoken, duration_seconds=duration)
    return result.accuracy, result.wcpm


@dataclass
class SessionRow:
    true_mean_mastery: float
    true_num_mastered: int
    probe_accuracy: float
    probe_wcpm: float


def _run_one(seed: int, num_sessions: int, *, adaptive: bool) -> list[SessionRow]:
    learner = SimulatedLearner.new(f"learner-{seed}", seed=seed)
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


@dataclass
class ExperimentResult:
    num_learners: int
    num_sessions: int
    # Per-session means across learners, one list per metric per arm.
    adaptive: dict[str, list[float]]
    static: dict[str, list[float]]


_METRICS = ("true_mean_mastery", "true_num_mastered", "probe_accuracy", "probe_wcpm")


def run_experiment(num_learners: int = 30, num_sessions: int = 40) -> ExperimentResult:
    """Runs both arms over `num_learners` paired learners and aggregates per session."""
    adaptive_runs = [_run_one(s, num_sessions, adaptive=True) for s in range(num_learners)]
    static_runs = [_run_one(s, num_sessions, adaptive=False) for s in range(num_learners)]

    def aggregate(runs: list[list[SessionRow]]) -> dict[str, list[float]]:
        agg: dict[str, list[float]] = {m: [] for m in _METRICS}
        for i in range(num_sessions):
            for m in _METRICS:
                agg[m].append(statistics.mean(getattr(run[i], m) for run in runs))
        return agg

    return ExperimentResult(
        num_learners=num_learners,
        num_sessions=num_sessions,
        adaptive=aggregate(adaptive_runs),
        static=aggregate(static_runs),
    )


def write_csv(result: ExperimentResult, path: Path) -> Path:
    """Writes the per-session aggregate table. This IS the fallback deliverable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["session"] + [
        f"{arm}_{m}" for m in _METRICS for arm in ("adaptive", "static")
    ]
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for i in range(result.num_sessions):
            row = [i]
            for m in _METRICS:
                row.append(round(result.adaptive[m][i], 4))
                row.append(round(result.static[m][i], 4))
            writer.writerow(row)
    return path


def plot(result: ExperimentResult, path: Path) -> Path | None:
    """Renders the evidence chart. Returns None (and warns) if matplotlib is
    unavailable — the CSV remains the deliverable in that case."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping chart. The CSV table is the deliverable.")
        return None

    sessions = list(range(result.num_sessions))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    panels = [
        ("probe_accuracy", "Benchmark reading accuracy", "accuracy (same probe)"),
        ("true_mean_mastery", "True latent mastery", "mean P(known) across graphemes"),
    ]
    for ax, (metric, title, ylabel) in zip(axes, panels):
        ax.plot(sessions, result.adaptive[metric], label="adaptive", color="#1b7837", linewidth=2)
        ax.plot(sessions, result.static[metric], label="static control", color="#b2182b",
                linewidth=2, linestyle="--")
        ax.set_title(title)
        ax.set_xlabel("session")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        ax.legend()

    fig.suptitle(
        f"Evidence-adaptive tutoring vs. a fixed sequence "
        f"(n={result.num_learners} simulated learners)",
        fontsize=13,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _print_summary(result: ExperimentResult) -> None:
    last = result.num_sessions - 1
    print(f"\nFinal session ({last}) means over {result.num_learners} learners:")
    print(f"  {'metric':<22} {'adaptive':>10} {'static':>10} {'gap':>10}")
    for m in _METRICS:
        a, s = result.adaptive[m][last], result.static[m][last]
        print(f"  {m:<22} {a:>10.3f} {s:>10.3f} {a - s:>+10.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Adaptive-vs-static tutor experiment.")
    parser.add_argument("--learners", type=int, default=30)
    parser.add_argument("--sessions", type=int, default=40)
    parser.add_argument("--outdir", type=Path, default=_OUTPUT_DIR)
    args = parser.parse_args()

    result = run_experiment(num_learners=args.learners, num_sessions=args.sessions)
    _print_summary(result)
    csv_path = write_csv(result, args.outdir / "adaptive_vs_static.csv")
    print(f"\nWrote table: {csv_path}")
    chart_path = plot(result, args.outdir / "adaptive_vs_static.png")
    if chart_path:
        print(f"Wrote chart: {chart_path}")


if __name__ == "__main__":
    main()
