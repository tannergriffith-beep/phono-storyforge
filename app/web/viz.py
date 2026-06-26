# app/web/viz.py
#
# =============================================================================
# FLAGSHIP STAGE C: viz-state mapping (PURE, unit-tested).
#
# Turns the real objects the closed loop already produces —
#   - PreparedSession (objective + book, before the read)
#   - SessionOutcome  (assessment + mastery delta + next objective, after it)
# into the flat, JSON-serializable payloads the browser animates from. Nothing
# here is invented: every number traces to a field on those dataclasses.
#
# This module imports ONLY the brain layer (app.tutor / app.skills / app.voice
# scaffold). It does NOT import FastAPI, so the payload logic is fully testable
# offline without the web stack, and the web deps never leak into app/.
#
# The two payloads and the exact SessionOutcome fields each viz reads:
#   prepared_payload  -> book words, objective, and the INITIAL mastery bars.
#   outcome_payload   -> miscue heatmap, mastery-bar updates, fluency, scaffold
#                        cues, mean mastery, and the (possibly advanced) next
#                        target.
#
# Bar-set invariant: the bars shown at prepare() are exactly the graphemes the
# book can produce evidence for (computed via the real attribution path), unioned
# with the target + review graphemes. So every bar that animates on outcome was
# already on screen — delta.changes is always a subset of the prepared bar set.
# =============================================================================

from __future__ import annotations

from app.phonics_db import LEVEL_SEQUENCE
from app.skills.alignment import align, attribute_evidence, tokenize
from app.tutor.session import PreparedSession, SessionOutcome, _mean_mastery
from app.voice.scaffold import scaffold_for_miscue


def _level_index(level: str) -> int:
    """Curriculum order for a level (unknown/sentinel levels sort last)."""
    try:
        return LEVEL_SEQUENCE.index(level)
    except ValueError:
        return len(LEVEL_SEQUENCE)


def _evidence_graphemes(book) -> list[str]:
    """The grapheme keys this book can produce mastery evidence for.

    Runs the REAL attribution path against a perfect read of the book, so the
    keys are exactly those `record_read` will move (a real read with miscues
    yields evidence for the same expected graphemes, just some marked wrong).
    This guarantees the prepared bar set is a superset of any outcome's
    delta.changes.
    """
    ops = align(book.text, book.text)
    evidence = attribute_evidence(ops, sight_words=book.sight_words)
    return list(evidence.keys())


def _mastery_bars(profile, book, objective) -> list[dict]:
    """Initial mastery bars: book-exercised graphemes + target + review.

    Each bar carries its current BKT P(L) from the learner's profile, plus flags
    so the UI can highlight the session's target and spaced-review graphemes.
    """
    keys = set(_evidence_graphemes(book))
    keys.add(objective.target_grapheme)
    keys.update(objective.review_graphemes)

    bars: list[dict] = []
    for grapheme in keys:
        mastery = profile.masteries.get(grapheme)
        bars.append(
            {
                "grapheme": grapheme,
                "level": mastery.level if mastery else "",
                "p_mastery": round(mastery.p_mastery if mastery else 0.0, 4),
                "is_target": grapheme == objective.target_grapheme,
                "is_review": grapheme in objective.review_graphemes,
            }
        )
    bars.sort(key=lambda b: (_level_index(b["level"]), b["grapheme"]))
    return bars


def _target_word_positions(book) -> list[int]:
    """Positions (in the expected token stream) of words exercising the target.

    Lets the UI's preset transcripts ("one miscue", "struggling") drop a word
    that actually bears the target grapheme, so the target's mastery visibly
    moves — the substitution/omission is real and scored honestly by the server.
    """
    from app.skills.decodability import decompose

    target = book.target_grapheme
    sight = book.sight_words
    positions: list[int] = []
    for i, word in enumerate(tokenize(book.text)):
        decomp = decompose(word, sight_words=sight)
        if target in decomp.grapheme_strings:
            positions.append(i)
    return positions


def prepared_payload(prepared: PreparedSession) -> dict:
    """The 'prepared' message: book to read + objective + initial mastery bars."""
    book = prepared.book
    objective = prepared.objective
    return {
        "type": "prepared",
        "session_index": prepared.session_index,
        "learner_id": prepared.profile.learner_id,
        "learner_name": prepared.profile.name,
        "book": {
            "title": getattr(book, "title", ""),
            "words": tokenize(book.text),
            "sight_words": sorted(book.sight_words),
            "target_grapheme": book.target_grapheme,
            "target_word_positions": _target_word_positions(book),
            "generation_source": getattr(book, "generation_source", "deterministic"),
        },
        "objective": {
            "target_grapheme": objective.target_grapheme,
            "target_level": objective.target_level,
            "rationale": objective.rationale,
            "review_graphemes": list(objective.review_graphemes),
        },
        "mastery_bars": _mastery_bars(prepared.profile, book, objective),
        "mean_mastery": round(_mean_mastery(prepared.profile), 4),
    }


def journey_payload(learner_id: str, learner_name: str, logs) -> dict:
    """The 'journey' message: a longitudinal read over persisted SessionLogs.

    Proves "loop, not generator" (DESIGN §17): the target row shifts (adaptation)
    while the mean row rises (learning). Pure read over history — no new
    instrumentation. `mean_mastery` is optional on older logs (written before it
    was tracked); such cells carry null and the client renders them as gaps.
    """
    sessions: list[dict] = []
    prev_target: str | None = None
    for log in logs:
        sessions.append(
            {
                "session_index": log.session_index,
                "target_grapheme": log.target_grapheme,
                "target_changed": prev_target is not None and log.target_grapheme != prev_target,
                "mean_mastery": round(log.mean_mastery, 4) if log.mean_mastery is not None else None,
                "accuracy": round(log.accuracy, 4),
                "wcpm": round(log.wcpm, 1),
                "newly_mastered": list(log.newly_mastered),
                "book_title": log.book_title,
            }
        )
        prev_target = log.target_grapheme

    means = [s["mean_mastery"] for s in sessions if s["mean_mastery"] is not None]
    return {
        "type": "journey",
        "learner_id": learner_id,
        "learner_name": learner_name,
        "sessions": sessions,
        "summary": {
            "count": len(sessions),
            "first_mean": means[0] if means else None,
            "last_mean": means[-1] if means else None,
        },
    }


def _heatmap(outcome: SessionOutcome) -> tuple[list[dict], list[dict]]:
    """Per-expected-word heatmap cells + a separate list of inserted words.

    Every expected token starts 'correct'; miscues overlay their running-record
    kind at the position they occurred. Insertions have no expected word, so
    they are returned separately rather than coloring a cell.
    """
    words = tokenize(outcome.assessment.expected_text)
    cells = [
        {"position": i, "word": word, "kind": "correct"}
        for i, word in enumerate(words)
    ]
    insertions: list[dict] = []
    for miscue in outcome.assessment.miscues:
        if miscue.kind == "insertion":
            insertions.append({"position": miscue.position, "spoken": miscue.spoken})
            continue
        if 0 <= miscue.position < len(cells):
            cells[miscue.position]["kind"] = miscue.kind
            cells[miscue.position]["spoken"] = miscue.spoken
    return cells, insertions


def _mastery_updates(outcome: SessionOutcome) -> list[dict]:
    """Per-grapheme before/after for every bar this read moved (sorted to match)."""
    newly = set(outcome.delta.newly_mastered)
    updates = [
        {
            "grapheme": change.grapheme,
            "level": change.level,
            "p_before": round(change.p_before, 4),
            "p_after": round(change.p_after, 4),
            "delta": round(change.delta, 4),
            "n_correct": change.n_correct,
            "n_incorrect": change.n_incorrect,
            "newly_mastered": change.grapheme in newly,
        }
        for change in outcome.delta.changes
    ]
    updates.sort(key=lambda u: (_level_index(u["level"]), u["grapheme"]))
    return updates


def _scaffolds(outcome: SessionOutcome) -> list[dict]:
    """Grapheme-targeted cues for each actionable miss (reuses Stage B)."""
    cues = []
    for miscue in outcome.assessment.miscues:
        cue = scaffold_for_miscue(miscue)
        if cue is not None:
            cues.append(
                {
                    "word": cue.word,
                    "grapheme": cue.grapheme,
                    "level": cue.level,
                    "prompt": cue.prompt,
                }
            )
    return cues


def outcome_payload(outcome: SessionOutcome) -> dict:
    """The 'outcome' message: everything the UI animates after a recorded read."""
    cells, insertions = _heatmap(outcome)
    assessment = outcome.assessment
    current = outcome.objective.target_grapheme
    nxt = outcome.next_objective
    return {
        "type": "outcome",
        "session_index": outcome.session_index,
        "heatmap": cells,
        "insertions": insertions,
        "fluency": {
            "accuracy": round(assessment.accuracy, 4),
            "wcpm": round(assessment.wcpm, 1),
            "words_correct": assessment.words_correct,
            "total_words": assessment.total_words,
            "errors": assessment.errors,
            "substitutions": assessment.substitutions,
            "omissions": assessment.omissions,
            "insertions": assessment.insertions,
            "self_corrections": assessment.self_corrections,
            "duration_seconds": round(assessment.duration_seconds, 2),
        },
        "mastery_updates": _mastery_updates(outcome),
        "scaffolds": _scaffolds(outcome),
        "mean_mastery": round(outcome.mean_mastery, 4),
        "newly_mastered": list(outcome.delta.newly_mastered),
        "newly_mastered_levels": list(outcome.delta.newly_mastered_levels),
        "generation_source": getattr(outcome.log, "generation_source", "deterministic"),
        "next_target": {
            "target_grapheme": nxt.target_grapheme,
            "target_level": nxt.target_level,
            "rationale": nxt.rationale,
            "previous_grapheme": current,
            "advanced": nxt.target_grapheme != current,
            # Current P(L) of the next target, so the Adapt-beat "ahead" node and
            # its tap-detail are truthful rather than fabricated (DESIGN §7/§16).
            "p_mastery": round(outcome.next_target_p_mastery, 4),
        },
    }
