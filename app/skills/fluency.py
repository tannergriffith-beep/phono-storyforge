# app/skills/fluency.py
#
# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop tutor — fluency metrics (Phase 3, Day 5).
#
# The two standard running-record fluency numbers, kept as tiny pure functions
# so both the assessment pipeline (app/skills/alignment.py) and the experiment
# can compute them the same way:
#   - accuracy: fraction of expected words read correctly.
#   - WCPM: words correct per minute (the canonical oral-reading-fluency rate).
# Self-corrections and hesitations are not errors — the caller passes the count
# of words ultimately read correctly, so those are already folded in.
# =============================================================================

from __future__ import annotations


def accuracy(words_correct: int, total_words: int) -> float:
    """Fraction of expected words read correctly (1.0 for an empty passage)."""
    if total_words <= 0:
        return 1.0
    return words_correct / total_words


def wcpm(words_correct: int, duration_seconds: float) -> float:
    """Words Correct Per Minute. 0.0 when no time elapsed."""
    if duration_seconds <= 0:
        return 0.0
    return words_correct * 60.0 / duration_seconds
