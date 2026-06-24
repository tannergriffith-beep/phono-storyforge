# app/voice/confidence.py
#
# =============================================================================
# FLAGSHIP STAGE B (Part 2): never punish the child for the recognizer's doubt.
#
# Voice ASR is imperfect: it sometimes hears a different word than the child
# actually read. If we fed that raw guess into assess(), a recognizer error
# would be scored as a reading miscue — punishing the child for the machine's
# mistake and corrupting the BKT mastery signal.
#
# The rule: when the ASR is UNSURE about a word it substituted (confidence below
# a threshold), give the child the benefit of the doubt — snap that token back
# to the word the page expected there. assess()'s alignment then scores it as a
# correct read, i.e. effectively a non-punitive hesitation, NOT a miscue.
#
# Crucially we only do this for LOW-confidence substitutions. A confident
# substitution that is surface-similar to the target (e.g. "sip" for "ship") is
# a REAL phonics miscue we must keep — that is exactly the signal the tutor
# exists to catch. So similarity is never used as the trigger; only the ASR's
# own confidence is. When no confidence signal is available, nothing is snapped
# (the transcript is trusted as-is) — a safe, honest default.
#
# This is pure Python and reuses the same SequenceMatcher primitive as
# app/skills/alignment.align(); it does not modify alignment or assess().
# =============================================================================

from __future__ import annotations

from difflib import SequenceMatcher

from app.skills.alignment import tokenize
from app.skills.decodability import clean_word

# Below this ASR confidence, a substituted word is treated as recognizer doubt
# (snapped to the expected word) rather than a child miscue.
DEFAULT_CONFIDENCE_THRESHOLD = 0.5


def repair_low_confidence(
    expected: str | list[str],
    spoken_tokens: list[str],
    confidences: list[float] | None = None,
    *,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> list[str]:
    """Returns a spoken token list with low-confidence substitutions repaired.

    Aligns the expected and spoken word streams; for any position where the ASR
    substituted a word it was UNSURE of (confidence < threshold), replaces the
    spoken token with the expected word. Correct reads, confident substitutions
    (real miscues), insertions, and omissions are left exactly as spoken.

    Args:
        expected: the page's expected text (string or token list).
        spoken_tokens: the ASR's word tokens.
        confidences: per-token ASR confidence in [0, 1], parallel to
            `spoken_tokens`. If None or mismatched in length, every token is
            treated as fully confident and nothing is snapped.
        threshold: confidence below which a substitution is treated as doubt.

    Returns:
        A repaired list of (cleaned) spoken word tokens ready for record_read.
    """
    exp = tokenize(expected)

    # Clean spoken tokens while keeping confidences aligned position-for-position.
    if confidences is None or len(confidences) != len(spoken_tokens):
        confidences = [1.0] * len(spoken_tokens)
    pairs = [
        (cleaned, conf)
        for w, conf in zip(spoken_tokens, confidences)
        if (cleaned := clean_word(w))
    ]
    spk = [p[0] for p in pairs]
    conf = [p[1] for p in pairs]

    sm = SequenceMatcher(a=exp, b=spk, autojunk=False)
    out: list[str] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.extend(spk[j1:j2])
        elif tag == "insert":
            out.extend(spk[j1:j2])  # genuine extra word(s)
        elif tag == "delete":
            pass  # omission — the child skipped it; nothing spoken to keep
        else:  # replace: pair expected/spoken positionally
            for k in range(max(i2 - i1, j2 - j1)):
                si, ei = j1 + k, i1 + k
                if si < j2 and ei < i2:
                    if conf[si] < threshold:
                        out.append(exp[ei])  # recognizer doubt -> trust the page
                    else:
                        out.append(spk[si])  # confident: a real miscue, keep it
                elif si < j2:
                    out.append(spk[si])  # extra spoken token (insertion-like)
                # ei < i2 only -> omission, nothing to append
    return out
