# scripts/tutor_cli.py
#
# =============================================================================
# FLAGSHIP STAGE A: typed-transcript entry path for the real closed loop.
#
# A tiny interactive harness that runs ONE real adaptive session against a
# persistent learner profile:
#   1. the planner picks the next target grapheme for THIS child,
#   2. a decodable practice book is shown,
#   3. you type what the child actually read aloud (the Stage-A stand-in for
#      Gemini Live voice input),
#   4. the miscue analysis + BKT mastery update run, and
#   5. it prints how mastery moved and what the planner will target NEXT.
#
# Run it twice for the same learner with strong reads and watch the target
# advance — that is the closed loop the eval simulation only modeled, now real.
#
# Usage:
#   uv run python -m scripts.tutor_cli --learner ada --interest dinosaurs --age 6
#   # then paste/type the child's read-aloud when prompted (Enter on its own
#   # line, or "=" for a perfect read).
# =============================================================================

from __future__ import annotations

import argparse
from pathlib import Path

from app.store.learner_store import JSONLearnerStore
from app.store.session_log import JSONLSessionLogStore
from app.tutor.session import TutorSession

_DEFAULT_DATA_DIR = Path("artifacts") / "tutor_data"


def _read_transcript(expected_words: list[str]) -> str:
    """Reads the child's read-aloud from stdin.

    A lone '=' means a perfect read (echoes the expected text); otherwise type
    the words the child actually said on one line.
    """
    print(
        "\nType what the child read aloud (one line). "
        "Enter '=' for a perfect read:"
    )
    line = input("> ").strip()
    if line == "=" or line == "":
        return " ".join(expected_words)
    return line


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one real adaptive tutor session (typed transcript).")
    parser.add_argument("--learner", required=True, help="Stable learner id (also the profile filename).")
    parser.add_argument("--name", default="", help="Display name for a new learner.")
    parser.add_argument("--age", type=int, default=6, help="Age for a new learner.")
    parser.add_argument("--interest", default="", help="Interest topic for a new learner.")
    parser.add_argument("--data-dir", type=Path, default=_DEFAULT_DATA_DIR, help="Where profiles + logs live.")
    args = parser.parse_args()

    store = JSONLearnerStore(args.data_dir / "profiles")
    log_store = JSONLSessionLogStore(args.data_dir / "sessions")
    tutor = TutorSession(store, log_store=log_store)

    prepared = tutor.prepare(
        args.learner, name=args.name, age=args.age, interest=args.interest
    )
    obj = prepared.objective
    print("=" * 70)
    print(f"Learner: {prepared.profile.learner_id}  |  session #{prepared.session_index}")
    print(f"Planner target: '{obj.target_grapheme}' (level: {obj.target_level})")
    print(f"  why: {obj.rationale}")
    print("-" * 70)
    print(f"Book: {getattr(prepared.book, 'title', '')}")
    print(f"  {prepared.book.text}")

    spoken = _read_transcript(prepared.book.words)
    outcome = tutor.record_read(prepared, spoken)

    a = outcome.assessment
    print("-" * 70)
    print(f"Read: {a.words_correct}/{a.total_words} correct  "
          f"| accuracy {a.accuracy:.0%}  | {a.wcpm:.0f} WCPM  | {a.errors} errors")
    if a.miscues:
        misses = ", ".join(
            f"{m.expected or '∅'}→{m.spoken or '∅'} ({m.kind})"
            for m in a.miscues
        )
        print(f"Miscues: {misses}")

    tgt = outcome.objective.target_grapheme
    change = next((c for c in outcome.delta.changes if c.grapheme == tgt), None)
    if change is not None:
        print(f"Target '{tgt}' mastery: {change.p_before:.2f} -> {change.p_after:.2f}  "
              f"({change.delta:+.2f})")
    if outcome.delta.newly_mastered:
        print(f"Newly mastered: {', '.join(outcome.delta.newly_mastered)}")
    if outcome.delta.newly_mastered_levels:
        print(f"Newly mastered LEVELS: {', '.join(outcome.delta.newly_mastered_levels)}")

    print(f"Mean mastery across inventory: {outcome.mean_mastery:.3f}")
    print("=" * 70)
    print(f"Next session will target: '{outcome.next_objective.target_grapheme}' "
          f"(level: {outcome.next_objective.target_level})")
    if outcome.next_objective.target_grapheme != tgt:
        print("  ↳ the target ADVANCED because of this read. The loop adapted.")
    print(f"\nProfile + session log saved under {args.data_dir}/")


if __name__ == "__main__":
    main()
