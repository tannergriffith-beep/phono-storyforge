# app/skills/planner.py
#
# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop mastery model — adaptive planner (Day 4).
#
# Given a learner's mastery state, deterministically choose the next learning
# Objective: a single ZPD ("zone of proximal development") target grapheme plus
# a few spaced-review picks and the set of mastered levels that bound what the
# generated book is allowed to use. This is pure Python (no LLM) — the planner
# decides WHAT to teach; the LLM only decides HOW to dress it up as a story.
#
# Target rule: the lowest unmastered grapheme in curriculum order. Because
# GRAPHEME_INVENTORY is ordered by LEVEL_SEQUENCE then within-level, the first
# grapheme below threshold sits in the learner's lowest not-yet-finished level.
# =============================================================================

from __future__ import annotations

from app.phonics_db import GRAPHEME_INVENTORY, MASTERY_THRESHOLD
from app.schemas import LearnerProfile, Objective

# Inventory index per grapheme, used as a stable deterministic tiebreaker.
_ORDER: dict[str, int] = {g: i for i, (g, _lvl) in enumerate(GRAPHEME_INVENTORY)}


def select_objective(
    profile: LearnerProfile,
    *,
    session_index: int | None = None,
    num_review: int = 2,
    threshold: float = MASTERY_THRESHOLD,
) -> Objective:
    """Selects the next learning Objective for a learner.

    Args:
        profile: the learner's current mastery state.
        session_index: current session number (only used in the rationale).
        num_review: how many mastered graphemes to surface for spaced review.
        threshold: BKT P(L) at which a grapheme counts as mastered.

    Returns:
        An Objective with the ZPD target grapheme/level, the mastered-level
        budget for the book, and spaced-review picks.
    """
    mastered_levels = profile.mastered_levels(threshold)

    # ZPD target = lowest unmastered grapheme in curriculum order.
    target = None
    for grapheme, level in GRAPHEME_INVENTORY:
        mastery = profile.masteries.get(grapheme)
        p = mastery.p_mastery if mastery is not None else 0.0
        if p < threshold:
            target = (grapheme, level, p)
            break

    if target is None:
        # Everything is mastered — keep practicing the weakest grapheme.
        weakest = min(
            profile.masteries.values(),
            key=lambda m: (m.p_mastery, _ORDER.get(m.grapheme, 0)),
        )
        target_grapheme, target_level = weakest.grapheme, weakest.level
        rationale = (
            "All tracked graphemes are mastered; reinforcing the weakest "
            f"('{target_grapheme}', P(L)={weakest.p_mastery:.2f})."
        )
    else:
        target_grapheme, target_level, target_p = target
        rationale = (
            f"Lowest unmastered grapheme '{target_grapheme}' "
            f"(level '{target_level}', P(L)={target_p:.2f})."
        )

    review = _spaced_review_picks(
        profile, exclude=target_grapheme, num_review=num_review, threshold=threshold
    )
    if review:
        rationale += f" Spaced review: {', '.join(review)}."
    if session_index is not None:
        rationale = f"[session {session_index}] " + rationale

    return Objective(
        target_grapheme=target_grapheme,
        target_level=target_level,
        mastered_levels=mastered_levels,
        review_graphemes=review,
        rationale=rationale,
    )


def _spaced_review_picks(
    profile: LearnerProfile,
    *,
    exclude: str,
    num_review: int,
    threshold: float,
) -> list[str]:
    """Picks the most 'due' mastered graphemes for spaced review.

    Most due = least recently seen (never-seen first), then weakest P(L), then
    curriculum order — fully deterministic.
    """
    if num_review <= 0:
        return []
    candidates = [
        m
        for m in profile.masteries.values()
        if m.grapheme != exclude and m.is_mastered(threshold)
    ]
    candidates.sort(
        key=lambda m: (
            m.last_seen_session if m.last_seen_session is not None else -1,
            m.p_mastery,
            _ORDER.get(m.grapheme, 0),
        )
    )
    return [m.grapheme for m in candidates[:num_review]]
