# app/voice/scaffold.py
#
# =============================================================================
# FLAGSHIP STAGE B (Part 2): grapheme-targeted scaffolding + echo/karaoke mode.
#
# When the read-aloud reveals a miss, generic "try again" feedback wastes the
# moment. The closed-loop tutor already knows the EXACT grapheme a word
# exercises (decompose()), so it can localize the failure to the precise sound
# the child stumbled on — "let's sound out the /sh/ in 'ship'" — instead of
# re-reading the whole word blindly.
#
#   - scaffold_for_miscue(miscue): uses decompose() to pinpoint the first
#     grapheme that broke down and returns a child-facing cue for it.
#   - echo_sequence(words): an echo / "karaoke" script (model reads, child
#     repeats) for pre-fluent readers who can't yet decode cold.
#
# Pure Python + decompose(); no LLM and no audio here. The voice CLI decides how
# to deliver the cue (TTS, on-screen, model speech). Tests assert the grapheme
# localization is correct and deterministic.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from app.schemas import Miscue
from app.skills.decodability import decompose


@dataclass
class ScaffoldCue:
    """A targeted prompt for the single grapheme a child stumbled on."""

    word: str          # the expected word that broke down
    grapheme: str      # the localized failed grapheme (e.g. "sh", "a_e")
    level: str         # the phonics level that introduces it
    prompt: str        # child-facing instruction to deliver

    @property
    def is_actionable(self) -> bool:
        return bool(self.grapheme)


@dataclass
class EchoStep:
    """One step of echo/karaoke mode: the model reads, then the child repeats."""

    word: str
    model_says: str    # what the model reads aloud
    child_prompt: str  # cue for the child to repeat


def _localize_failed_grapheme(expected_word: str, spoken_word: str | None):
    """Returns the (grapheme, level) of the first sound that broke down.

    Mirrors the grapheme-diff in miscue attribution: an omission (no spoken
    word) fails on the word's first grapheme; otherwise the expected and spoken
    grapheme sequences are aligned and the first expected grapheme that is not
    preserved in an 'equal' block is the one that broke. Falls back to the first
    grapheme if everything technically aligned (e.g. a pure timing slip).
    """
    decomp = decompose(expected_word)
    graphemes = decomp.graphemes
    if not graphemes:
        return None, ""

    if not spoken_word:
        g = graphemes[0]
        return g.grapheme, g.level

    exp_keys = [g.grapheme for g in graphemes]
    spk_keys = [g.grapheme for g in decompose(spoken_word).graphemes]
    sm = SequenceMatcher(a=exp_keys, b=spk_keys, autojunk=False)
    correct = [False] * len(exp_keys)
    for tag, i1, i2, _j1, _j2 in sm.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                correct[i] = True
    for i, ok in enumerate(correct):
        if not ok:
            return graphemes[i].grapheme, graphemes[i].level
    g = graphemes[0]
    return g.grapheme, g.level


def scaffold_for_miscue(miscue: Miscue) -> ScaffoldCue | None:
    """Builds a grapheme-targeted scaffolding cue for a single miscue.

    Returns None for non-actionable miscues (insertions, self-corrections, and
    hesitations — the word was ultimately read, so there is nothing to reteach).
    """
    if miscue.kind not in ("substitution", "omission") or not miscue.expected:
        return None

    grapheme, level = _localize_failed_grapheme(miscue.expected, miscue.spoken)
    if not grapheme:
        return None

    prompt = (
        f"Let's sound out the /{grapheme}/ in '{miscue.expected}'. "
        f"Say it slowly with me, then read the word again."
    )
    return ScaffoldCue(
        word=miscue.expected, grapheme=grapheme, level=level, prompt=prompt
    )


def echo_sequence(words: list[str]) -> list[EchoStep]:
    """Builds an echo/karaoke script for pre-fluent readers.

    The model reads each word aloud and the child repeats it, then reads the
    whole line. Cleaned, empty tokens are skipped.
    """
    steps: list[EchoStep] = []
    cleaned = [decompose(w).word for w in words]
    cleaned = [w for w in cleaned if w]
    for w in cleaned:
        steps.append(
            EchoStep(
                word=w,
                model_says=w,
                child_prompt=f"Now you say '{w}'.",
            )
        )
    if cleaned:
        line = " ".join(cleaned)
        steps.append(
            EchoStep(
                word=line,
                model_says=line,
                child_prompt="Great! Now read the whole line with me.",
            )
        )
    return steps
