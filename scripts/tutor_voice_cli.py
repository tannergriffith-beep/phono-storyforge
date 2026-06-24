# scripts/tutor_voice_cli.py
#
# =============================================================================
# FLAGSHIP STAGE B (Part 2): voice read-aloud entry path for the closed loop.
#
# The voice sibling of scripts/tutor_cli.py. Same one real adaptive session, but
# the child READS ALOUD instead of someone typing the transcript:
#   1. the planner picks the next target grapheme for THIS child,
#   2. a decodable book is shown (deterministic by default, or the verifier-
#      gated LLM generator with --llm-book),
#   3. Gemini Live transcribes the read-aloud -> (tokens, duration),
#   4. the SAME record_read() runs miscue analysis + BKT update + persistence,
#   5. it prints how mastery moved, scaffolds any miss to the exact grapheme,
#      and shows what the planner will target NEXT.
#
# This file is deliberately SEPARATE from tutor_cli.py so the offline, no-key,
# always-works typed path stays clean: all audio/Live/genai imports here are
# lazy (only the chosen Transcriber pulls them in), and the offline unit suite
# never imports this module.
#
# Usage:
#   uv run python -m scripts.tutor_voice_cli --learner ada --interest dinosaurs --age 6
#   # speak the page aloud when prompted; stops on a short silence.
#   uv run python -m scripts.tutor_voice_cli --learner ada --echo   # karaoke mode
# =============================================================================

from __future__ import annotations

import argparse
from pathlib import Path

from app.store.learner_store import JSONLearnerStore
from app.store.session_log import JSONLSessionLogStore
from app.tutor.session import TutorSession

_DEFAULT_DATA_DIR = Path("artifacts") / "tutor_data"


def _build_book_provider(use_llm: bool):
    """Lazily builds the chosen BookProvider (LLM generator or deterministic)."""
    if not use_llm:
        from app.tutor.book_source import deterministic_book_provider

        return deterministic_book_provider
    from app.tutor.book_source import make_llm_book_provider

    return make_llm_book_provider()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one real adaptive tutor session with Gemini Live voice."
    )
    parser.add_argument("--learner", required=True, help="Stable learner id (also the profile filename).")
    parser.add_argument("--name", default="", help="Display name for a new learner.")
    parser.add_argument("--age", type=int, default=6, help="Age for a new learner.")
    parser.add_argument("--interest", default="", help="Interest topic for a new learner.")
    parser.add_argument("--data-dir", type=Path, default=_DEFAULT_DATA_DIR, help="Where profiles + logs live.")
    parser.add_argument("--llm-book", action="store_true", help="Use the verifier-gated LLM book generator.")
    parser.add_argument("--echo", action="store_true", help="Echo/karaoke mode: model reads, child repeats (pre-fluent readers).")
    args = parser.parse_args()

    store = JSONLearnerStore(args.data_dir / "profiles")
    log_store = JSONLSessionLogStore(args.data_dir / "sessions")
    tutor = TutorSession(
        store, log_store=log_store, book_provider=_build_book_provider(args.llm_book)
    )

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

    # Echo/karaoke pre-read for pre-fluent readers (model reads, child repeats).
    if args.echo:
        from app.voice.scaffold import echo_sequence

        print("-" * 70)
        print("Echo mode — repeat each word after me:")
        for step in echo_sequence(prepared.book.words):
            print(f"  🔊 {step.model_says}   ({step.child_prompt})")

    # Lazy: only now do we touch the Live client / microphone.
    from app.voice.transcriber import LiveTranscriber

    transcriber = LiveTranscriber()
    print("-" * 70)
    print("🎤 Read the page aloud now... (recording stops on a short silence)")
    tokens, duration = transcriber.transcribe(prepared.book.words)
    print(f"Heard: {' '.join(tokens)}   ({duration:.1f}s)")

    outcome = tutor.record_read(prepared, tokens, duration_seconds=duration)

    a = outcome.assessment
    print("-" * 70)
    print(f"Read: {a.words_correct}/{a.total_words} correct  "
          f"| accuracy {a.accuracy:.0%}  | {a.wcpm:.0f} WCPM  | {a.errors} errors")
    if a.miscues:
        misses = ", ".join(
            f"{m.expected or '∅'}→{m.spoken or '∅'} ({m.kind})" for m in a.miscues
        )
        print(f"Miscues: {misses}")

        # Grapheme-targeted scaffolding for each real miss.
        from app.voice.scaffold import scaffold_for_miscue

        for m in a.miscues:
            cue = scaffold_for_miscue(m)
            if cue is not None:
                print(f"  ↳ scaffold: {cue.prompt}")

    tgt = outcome.objective.target_grapheme
    change = next((c for c in outcome.delta.changes if c.grapheme == tgt), None)
    if change is not None:
        print(f"Target '{tgt}' mastery: {change.p_before:.2f} -> {change.p_after:.2f}  "
              f"({change.delta:+.2f})")
    if outcome.delta.newly_mastered:
        print(f"Newly mastered: {', '.join(outcome.delta.newly_mastered)}")

    print(f"Mean mastery across inventory: {outcome.mean_mastery:.3f}")
    print(f"Book source: {outcome.log.generation_source}")
    print("=" * 70)
    print(f"Next session will target: '{outcome.next_objective.target_grapheme}' "
          f"(level: {outcome.next_objective.target_level})")
    if outcome.next_objective.target_grapheme != tgt:
        print("  ↳ the target ADVANCED because of this read. The loop adapted.")
    print(f"\nProfile + session log saved under {args.data_dir}/")


if __name__ == "__main__":
    main()
