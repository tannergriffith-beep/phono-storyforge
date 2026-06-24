# app/skills/mastery.py
#
# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop mastery model — Bayesian Knowledge Tracing.
#
# This is the deterministic, non-LLM skill that turns per-grapheme evidence
# (from miscue attribution in Phase 3) into an updated knowledge state. It is
# the "verify/measure" half of the through-line: the LLM proposes a book, the
# child reads it, deterministic alignment attributes errors to graphemes, and
# THIS module quantifies what the child now knows.
#
# BKT models each grapheme as a latent binary "known/not-known" state with a
# 4-parameter model (p_init, p_transit, p_slip, p_guess). Each observed
# opportunity updates the posterior P(L) via Bayes, then a learning transition
# accounts for the chance the practice itself taught the skill.
# =============================================================================

from __future__ import annotations

from app.phonics_db import (
    GRAPHEME_LEVEL,
    MASTERY_THRESHOLD,
    bkt_params_for_level,
)
from app.schemas import (
    GraphemeDelta,
    GraphemeMastery,
    LearnerProfile,
    MasteryDelta,
)

# Evidence is a mapping of grapheme -> list of per-opportunity outcomes, where
# True == the learner read the grapheme correctly and False == a miscue.
GraphemeEvidence = dict[str, list[bool]]


def _bkt_step(p_known: float, correct: bool, params: dict[str, float]) -> float:
    """Applies one BKT observation: Bayesian posterior + learning transition.

    Args:
        p_known: P(L) — current probability the grapheme is known.
        correct: whether this single opportunity was answered correctly.
        params: {p_transit, p_slip, p_guess} for the grapheme's level.

    Returns:
        The updated P(L) after conditioning on the observation and applying the
        learning transition.
    """
    slip = params["p_slip"]
    guess = params["p_guess"]
    transit = params["p_transit"]

    if correct:
        # P(L | correct) = P(L)(1-slip) / [P(L)(1-slip) + (1-P(L))guess]
        numerator = p_known * (1.0 - slip)
        denominator = numerator + (1.0 - p_known) * guess
    else:
        # P(L | incorrect) = P(L)slip / [P(L)slip + (1-P(L))(1-guess)]
        numerator = p_known * slip
        denominator = numerator + (1.0 - p_known) * (1.0 - guess)

    posterior = numerator / denominator if denominator > 0 else p_known

    # Learning transition: even unknown skills may be acquired through practice.
    return posterior + (1.0 - posterior) * transit


def update_from_evidence(
    profile: LearnerProfile,
    grapheme_evidence: GraphemeEvidence,
    *,
    session_index: int | None = None,
    threshold: float = MASTERY_THRESHOLD,
) -> MasteryDelta:
    """Updates a learner's mastery in place from a batch of grapheme evidence.

    For each grapheme with observations, applies a BKT step per opportunity (in
    order), records correct/opportunity counts, and stamps the session index for
    spaced review. Returns a MasteryDelta describing every change plus anything
    that newly crossed the mastery threshold.

    Graphemes absent from the profile are created on demand from the inventory
    (falling back to default params for any unknown grapheme key).
    """
    levels_mastered_before = set(profile.mastered_levels(threshold))

    changes: list[GraphemeDelta] = []
    newly_mastered: list[str] = []

    for grapheme, observations in grapheme_evidence.items():
        if not observations:
            continue

        level = GRAPHEME_LEVEL.get(grapheme, "")
        params = bkt_params_for_level(level)

        mastery = profile.masteries.get(grapheme)
        if mastery is None:
            mastery = GraphemeMastery(
                grapheme=grapheme,
                level=level,
                p_mastery=params["p_init"],
            )
            profile.masteries[grapheme] = mastery

        p_before = mastery.p_mastery
        was_mastered = p_before >= threshold

        p = p_before
        n_correct = 0
        for correct in observations:
            p = _bkt_step(p, correct, params)
            if correct:
                n_correct += 1

        mastery.p_mastery = p
        mastery.opportunities += len(observations)
        mastery.correct += n_correct
        if session_index is not None:
            mastery.last_seen_session = session_index

        changes.append(
            GraphemeDelta(
                grapheme=grapheme,
                level=level,
                p_before=p_before,
                p_after=p,
                n_correct=n_correct,
                n_incorrect=len(observations) - n_correct,
            )
        )
        if not was_mastered and p >= threshold:
            newly_mastered.append(grapheme)

    if changes:
        profile.touch()

    levels_mastered_after = set(profile.mastered_levels(threshold))
    newly_mastered_levels = [
        lvl
        for lvl in profile.mastered_levels(threshold)
        if lvl in (levels_mastered_after - levels_mastered_before)
    ]

    return MasteryDelta(
        changes=changes,
        newly_mastered=newly_mastered,
        newly_mastered_levels=newly_mastered_levels,
    )
