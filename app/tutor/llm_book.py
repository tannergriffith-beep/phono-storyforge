# app/tutor/llm_book.py
#
# =============================================================================
# FLAGSHIP STAGE B (Part 1): the verifier-gated LLM book generator.
#
# This is the production content engine that replaces the deterministic Stage-A
# book builder behind the SAME BookProvider seam. It reuses the proven pattern
# from app/agent.py's Writer<->QA LoopAgent, but as a tight, synchronous,
# unit-testable Python loop:
#
#   propose (LLM)  ->  prove (check_decodability + target-exercise)  ->  feed
#   the violations back into the prompt  ->  repeat.
#
# Two hard rules:
#   1. NEVER return a book with a decodability violation. If the LLM cannot
#      reach a fully decodable draft within `max_attempts`, this RAISES
#      (BookGenerationError). The provider layer decides whether to surface that
#      or fall back to the guaranteed-decodable deterministic builder.
#   2. The book must exercise the objective's target grapheme. Decodability is
#      the absolute gate; on-target is best-effort — a decodable-but-off-target
#      draft is returned tagged "llm_offtarget" rather than discarded.
#
# The LLM itself is reached through an injectable `StoryProposer` (mirroring how
# app/illustrator.py injects an ImageGenerator), so the whole loop runs offline
# in tests with a fake proposer and zero network. Only app/skills/decodability
# is imported here — no eval/ dependency.
# =============================================================================

from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from typing import Callable

from app.schemas import Objective, StoryDraft
from app.skills.decodability import decompose, inflectional_suffix, check_decodability

# Text model for the writer. Matches the project convention in app/agent.py; the
# decodability budget is enforced deterministically afterward, so a small/fast
# model is fine and any residual violations are caught and fed back.
MODEL_NAME = "gemini-flash-lite-latest"

# Human-readable description of what each phonics level licenses, so the writer
# knows the patterns it may use. Mirrors the writer_instruction in app/agent.py.
_LEVEL_HINTS: dict[str, str] = {
    "short_vowels": "short-vowel CVC/VC words only (cat, red, pin, dog, run, on, at)",
    "digraphs": "consonant digraphs sh, ch, th, wh, ck, ng, ph, qu (ship, chip, this)",
    "blends": "consonant blends (flat, stop, hand, went, drum)",
    "silent_e": "silent-e long vowels (make, like, home, cube)",
    "r_controlled": "r-controlled vowels ar, er, ir, or, ur (car, her, bird, fork)",
    "vowel_teams": "vowel teams (rain, see, boat, night, moon)",
    "glued_sounds": "welded rimes all, ang, ing, ong, ung, ank, ink, onk, unk (ball, sing, bank)",
    "y_vowel": "'y' as a vowel (my, happy)",
    "suffixes": "inflectional endings -s, -es, -ed, -ing on a decodable base (dogs, jumped)",
}


class BookGenerationError(RuntimeError):
    """Raised when the LLM cannot produce a fully decodable book in time."""


# A StoryProposer turns a writer prompt into a draft. The default implementation
# calls Gemini; tests inject a deterministic fake. Returning a StoryDraft lets us
# reuse the existing structured-output schema end to end.
StoryProposer = Callable[[str], StoryDraft]


@dataclass
class GeneratedBook:
    """An LLM-authored decodable practice book. Satisfies the BookLike protocol."""

    title: str
    pages: list[str]
    target_grapheme: str
    objective: Objective
    sight_words: set[str] = field(default_factory=set)
    # Flywheel signal consumed by SessionLog: "llm" (decodable + on-target) or
    # "llm_offtarget" (decodable but the target grapheme never appeared).
    generation_source: str = "llm"

    @property
    def text(self) -> str:
        return " ".join(self.pages)

    @property
    def words(self) -> list[str]:
        """Flat whitespace token list across all pages (what the tutor counts)."""
        return [w for page in self.pages for w in page.split()]


# ---------------------------------------------------------------------------
# Verifiers (deterministic, shared with the rest of the loop)
# ---------------------------------------------------------------------------


def _grapheme_keys(word: str) -> set[str]:
    """All inventory keys a word exercises, including the structural sentinels.

    Reuses decompose() (segmentation is independent of mastery) plus the same
    _blend_/-suffix sentinel rules the miscue attribution and planner use, so the
    target-exercise check agrees with the rest of the system. Local copy of the
    eval helper to keep this module free of any eval/ import.
    """
    d = decompose(word)
    keys = {g.grapheme for g in d.graphemes}
    gs = d.graphemes
    if any(gs[i].kind == "C" and gs[i + 1].kind == "C" for i in range(len(gs) - 1)):
        keys.add("_blend_")
    suffix = inflectional_suffix(d.word)
    if suffix:
        keys.add(f"-{suffix}")
    return keys


def _phonics_profile(objective: Objective, sight_words: set[str]) -> dict:
    """The phonics_profile dict check_decodability expects for this objective."""
    return {
        "mastered_levels": list(objective.mastered_levels),
        "target_level": objective.target_level,
        "sight_words": list(sight_words),
    }


def _exercises_target(pages: list[str], target_grapheme: str) -> bool:
    """True if any word across the pages exercises the target grapheme."""
    return any(
        target_grapheme in _grapheme_keys(w)
        for page in pages
        for w in page.split()
    )


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def _build_prompt(
    objective: Objective,
    *,
    sight_words: set[str],
    length: int,
    interest: str,
    age: int,
    feedback: str,
) -> str:
    """Builds the writer prompt for one attempt, folding in any prior feedback."""
    budget = list(objective.mastered_levels)
    if objective.target_level not in budget:
        budget.append(objective.target_level)
    allowed = "\n".join(
        f"  - {lvl}: {_LEVEL_HINTS.get(lvl, lvl)}" for lvl in budget
    )
    theme = interest.strip() or "a friendly everyday adventure"
    review = ", ".join(objective.review_graphemes) or "none"
    sight = ", ".join(sorted(sight_words)) or "none"

    parts = [
        "You are the Phono StoryForge Decodable Writer.",
        f"Write a short decodable practice story of about {length} words across "
        "3-5 short pages (1-2 simple sentences each) for a child who is "
        f"{age} years old and loves {theme}.",
        "",
        f"FOCUS SOUND (must appear): the '{objective.target_grapheme}' grapheme "
        f"(phonics level '{objective.target_level}'). Use several words that "
        "clearly contain this sound.",
        f"Also gently revisit these review sounds if natural: {review}.",
        "",
        "DECODABILITY BUDGET — every word must be decodable using ONLY these "
        "phonics levels:",
        allowed,
        f"Sight words the child also knows (always allowed): {sight}.",
        "Common little connector words (the, a, and, is, on, in, it) are fine.",
        "Do NOT use any word that needs a phonics pattern outside the budget "
        "above unless it is one of the allowed sight words.",
        "",
        "Keep the tone warm and age-appropriate. Return the story as pages.",
    ]
    if feedback:
        parts += [
            "",
            "REVISION REQUIRED — your previous draft failed the decodability "
            "check. Fix it by replacing or removing these words:",
            feedback,
        ]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# The verifier-gated generation loop
# ---------------------------------------------------------------------------


def generate_decodable_book(
    objective: Objective,
    *,
    proposer: StoryProposer,
    session_index: int = 0,
    sight_words: set[str] | None = None,
    num_target: int = 6,
    length: int = 16,
    interest: str = "",
    age: int = 6,
    rng: random.Random | None = None,
    max_attempts: int = 4,
) -> GeneratedBook:
    """Generates a fully decodable book for an objective, verifier-gated.

    Loops propose -> prove -> feed-back until the draft is 100% decodable, then
    returns it. Tags the result "llm" if it also exercises the target grapheme,
    or "llm_offtarget" otherwise (decodable is the hard gate; on-target is
    best-effort). Raises BookGenerationError if no decodable draft is produced
    within `max_attempts`.

    `num_target`/`rng`/`session_index` are accepted to match the deterministic
    builder's signature; the LLM uses `length`, `interest`, and `age` for shape
    and theme while the verifiers enforce the hard constraints.
    """
    sight = set(sight_words or set())
    profile = _phonics_profile(objective, sight)

    feedback = ""
    best_decodable: StoryDraft | None = None
    for _attempt in range(max_attempts):
        prompt = _build_prompt(
            objective,
            sight_words=sight,
            length=length,
            interest=interest,
            age=age,
            feedback=feedback,
        )
        draft = proposer(prompt)
        pages = [p for p in (draft.pages or []) if p and p.strip()]

        check = check_decodability("\n".join(pages), profile)
        if not check["is_decodable"]:
            # Feed the exact offending words back into the next attempt.
            feedback = ", ".join(check["violations"])
            continue

        # Decodable. Prefer one that also exercises the target grapheme; keep the
        # first decodable draft as a fallback in case none ever hits the target.
        on_target = _exercises_target(pages, objective.target_grapheme)
        if on_target:
            return GeneratedBook(
                title=draft.title or f"The {objective.target_grapheme} Story",
                pages=pages,
                target_grapheme=objective.target_grapheme,
                objective=objective,
                sight_words=sight,
                generation_source="llm",
            )
        if best_decodable is None:
            best_decodable = draft
        feedback = (
            f"the story is decodable but uses no word with the focus sound "
            f"'{objective.target_grapheme}' — add some"
        )

    if best_decodable is not None:
        # Decodable but never on-target: safe to read, logged as off-target so
        # the flywheel can see the generator missed the pedagogical goal.
        pages = [p for p in best_decodable.pages if p and p.strip()]
        return GeneratedBook(
            title=best_decodable.title or f"The {objective.target_grapheme} Story",
            pages=pages,
            target_grapheme=objective.target_grapheme,
            objective=objective,
            sight_words=sight,
            generation_source="llm_offtarget",
        )

    raise BookGenerationError(
        f"LLM did not produce a fully decodable book for target "
        f"'{objective.target_grapheme}' within {max_attempts} attempts; "
        f"last violations: {feedback}"
    )


# ---------------------------------------------------------------------------
# The Gemini-backed proposer (production default)
# ---------------------------------------------------------------------------


def make_gemini_proposer(client=None, *, model: str = MODEL_NAME) -> StoryProposer:
    """Returns a StoryProposer backed by Gemini structured output.

    The client is built lazily (Vertex-preferred, mirroring app/illustrator.py)
    so importing this module never requires credentials; only calling the
    returned proposer touches the network.
    """
    from google import genai
    from google.genai import types

    def _client():
        if client is not None:
            return client
        http_options = types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=4,
                http_status_codes=[408, 429, 500, 502, 503, 504],
            )
        )
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "0") == "1"
        if use_vertex and project:
            return genai.Client(
                vertexai=True, project=project, location=location, http_options=http_options
            )
        return genai.Client(http_options=http_options)

    active = _client()

    def _propose(prompt: str) -> StoryDraft:
        response = active.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StoryDraft,
            ),
        )
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, StoryDraft):
            return parsed
        return StoryDraft.model_validate_json(response.text)

    return _propose
