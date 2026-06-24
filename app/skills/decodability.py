# app/skills/decodability.py
#
# =============================================================================
# CAPSTONE CONCEPT 3: Agent Skills — the decodability engine.
#
# This is the keystone deterministic skill of the closed-loop tutor. It does
# two jobs:
#   1. decompose(word, ...)  -> the ordered graphemes a word exercises, each
#      tagged with the phonics level that introduces it. This word->grapheme
#      map is what powers (a) decodability verification, (b) targeting ("does
#      this book actually exercise the target grapheme?"), and (c) miscue
#      attribution in the assessment flow ("the child failed on 'ship' at the
#      'sh' grapheme").
#   2. is_word_decodable / check_decodability -> the QA gate used by the
#      Writer<->QA loop, now derived from the same decomposition.
#
# Phase 1 note: logic moved here from app/tools.py (kept as a re-export shim).
# Day 1 preserves existing behavior exactly; the sound-level corrections
# (-all/-ll, schwa, y-as-vowel, suffixes) land in Day 2.
# =============================================================================

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.phonics_db import DEFAULT_SIGHT_WORDS

# ---------------------------------------------------------------------------
# Grapheme inventory. Each multi-character grapheme is tagged with the phonics
# level that introduces it. Single letters belong to the short_vowels base.
# ---------------------------------------------------------------------------
VOWELS = set("aeiou")
# NOTE: 'y' is treated as a consonant here to preserve Day-1 behavior; Day 2
# adds 'y'-as-vowel handling.
CONSONANTS = set("bcdfghjklmnpqrstvwxyz")

DIGRAPHS = {"sh", "ch", "th", "wh", "ck", "ng", "ph", "qu"}
R_CONTROLLED = {"ar", "er", "ir", "or", "ur"}
VOWEL_TEAMS = {
    "igh",  # 3-char
    "ai", "ay", "ee", "ea", "oa", "oe", "ie",
    "oo", "ou", "ow", "oi", "oy", "au", "aw",
}

# Silent-e middle consonant excludes 'r' (V-r-e reads as r-controlled, e.g.
# 'more', 'here', not as a silent-e split vowel).
_SILENT_E_RE = re.compile(r"[aeiou][bcdfghjklmnpqstvwxyz]e$")


@dataclass
class GraphemeHit:
    """A single grapheme found in a word, tagged with its phonics level."""

    grapheme: str          # e.g. "sh", "a", "ar", "a_e"
    level: str             # phonics level that introduces it
    span: tuple[int, int]  # [start, end) char offsets in the cleaned word
    kind: str              # "C" (consonant unit) or "V" (vowel unit)


@dataclass
class WordDecomposition:
    """The graphemes a word exercises, plus its decodability verdict."""

    word: str
    graphemes: list[GraphemeHit]
    is_decodable: bool
    is_sight_word: bool
    violations: list[str] = field(default_factory=list)

    @property
    def grapheme_strings(self) -> list[str]:
        return [g.grapheme for g in self.graphemes]


def clean_word(word: str) -> str:
    """Strips punctuation, normalizes apostrophes, and lowercases a word."""
    word = word.replace("’", "'").strip().lower()
    word = re.sub(r"[^\w\s']", "", word)
    word = word.strip("'")
    return word


def _segment(word: str) -> list[GraphemeHit] | None:
    """Segments a cleaned word into ordered graphemes left-to-right.

    Returns None if the word contains a character that cannot be mapped to a
    known grapheme (which makes the word non-decodable by definition).
    """
    n = len(word)
    if n == 0:
        return []

    # Detect a trailing silent-e ("magic e"): the final 'e' is silent and binds
    # to the preceding vowel to form a split-vowel grapheme (a_e, i_e, ...).
    se = _SILENT_E_RE.search(word)
    silent_vowel_idx = se.start() if se else None
    final_e_idx = n - 1 if se else None

    hits: list[GraphemeHit] = []
    i = 0
    while i < n:
        # Silent final 'e' — already folded into the split-vowel grapheme.
        if final_e_idx is not None and i == final_e_idx:
            i += 1
            continue

        # Split-vowel (silent-e) grapheme at the bound vowel position.
        if silent_vowel_idx is not None and i == silent_vowel_idx:
            hits.append(
                GraphemeHit(word[i] + "_e", "silent_e", (i, final_e_idx + 1), "V")
            )
            i += 1
            continue

        ch = word[i]

        # Doubled consonant (floss rule: ff, ll, ss, zz, and any geminate) maps
        # to a single consonant grapheme spanning both letters.
        if ch in CONSONANTS and i + 1 < n and word[i + 1] == ch:
            hits.append(GraphemeHit(ch, "short_vowels", (i, i + 2), "C"))
            i += 2
            continue

        # Multi-character graphemes, longest first, never crossing the silent e.
        matched = False
        for length in (3, 2):
            if i + length > n:
                continue
            if final_e_idx is not None and i < final_e_idx < i + length:
                continue
            seg = word[i : i + length]
            if seg in VOWEL_TEAMS:
                hits.append(GraphemeHit(seg, "vowel_teams", (i, i + length), "V"))
            elif seg in R_CONTROLLED:
                hits.append(GraphemeHit(seg, "r_controlled", (i, i + length), "V"))
            elif seg in DIGRAPHS:
                hits.append(GraphemeHit(seg, "digraphs", (i, i + length), "C"))
            else:
                continue
            i += length
            matched = True
            break
        if matched:
            continue

        # Single-character grapheme.
        if ch in VOWELS:
            hits.append(GraphemeHit(ch, "short_vowels", (i, i + 1), "V"))
        elif ch in CONSONANTS:
            hits.append(GraphemeHit(ch, "short_vowels", (i, i + 1), "C"))
        else:
            return None  # unmappable character (e.g. a digit) -> not decodable
        i += 1

    return hits


def _verdict(
    hits: list[GraphemeHit] | None, mastered_levels: list[str]
) -> tuple[bool, list[str]]:
    """Computes decodability + the list of offending grapheme/structure tokens."""
    if hits is None:
        return False, ["<unsegmentable>"]
    if not hits:
        return True, []
    # short_vowels is the absolute base; without it no phonics decoding applies.
    if "short_vowels" not in mastered_levels:
        return False, [h.grapheme for h in hits]

    violations = [h.grapheme for h in hits if h.level not in mastered_levels]

    # Structural rules over adjacent graphemes:
    #  - two adjacent consonant units => a blend (needs 'blends' mastered)
    #  - two adjacent vowel units => an unrecognized vowel team (never allowed)
    for a, b in zip(hits, hits[1:]):
        if a.kind == "C" and b.kind == "C" and "blends" not in mastered_levels:
            violations.append(f"{a.grapheme}{b.grapheme}")
        elif a.kind == "V" and b.kind == "V":
            violations.append(f"{a.grapheme}{b.grapheme}")

    return (len(violations) == 0), violations


def decompose(
    raw_word: str,
    mastered_levels: list[str] | None = None,
    sight_words: set[str] | None = None,
) -> WordDecomposition:
    """Decomposes a word into graphemes and judges its decodability.

    Args:
        raw_word: The raw (possibly punctuated) word.
        mastered_levels: Levels the child has mastered. If None, decodability is
            reported as False but the grapheme breakdown is still returned.
        sight_words: Cleaned sight words to treat as always-allowed.

    Returns:
        A WordDecomposition with the grapheme breakdown and verdict.
    """
    cleaned = clean_word(raw_word)
    sight = sight_words or set()
    is_sight = bool(cleaned) and cleaned in sight

    hits = _segment(cleaned)
    graphemes = hits or []

    if is_sight or not cleaned:
        return WordDecomposition(cleaned, graphemes, True, is_sight, [])

    decodable, violations = _verdict(hits, mastered_levels or [])
    return WordDecomposition(cleaned, graphemes, decodable, False, violations)


def is_word_decodable(word: str, mastered_levels: list[str]) -> bool:
    """Returns True if a single (already-clean) word is decodable.

    Kept as the public predicate the QA loop and tests rely on; now derived
    from the shared grapheme decomposition.
    """
    hits = _segment(word.lower())
    decodable, _ = _verdict(hits, mastered_levels)
    return decodable


def check_decodability(
    story_text: str, phonics_profile: dict[str, Any]
) -> dict[str, Any]:
    """Analyzes a story and returns decodability metrics for the QA gate."""
    mastered_levels = list(phonics_profile.get("mastered_levels", []))
    target_level = phonics_profile.get("target_level")
    if target_level and target_level not in mastered_levels:
        mastered_levels.append(target_level)

    sight_words = {clean_word(w) for w in phonics_profile.get("sight_words", [])}
    all_sight_words = sight_words | {clean_word(w) for w in DEFAULT_SIGHT_WORDS}

    violations: list[str] = []
    for raw_word in story_text.split():
        cleaned = clean_word(raw_word)
        if not cleaned or cleaned in all_sight_words:
            continue
        if not is_word_decodable(cleaned, mastered_levels):
            violations.append(raw_word)

    # Deduplicate while preserving order of first appearance.
    seen: set[str] = set()
    unique_violations: list[str] = []
    for v in violations:
        c = clean_word(v)
        if c not in seen:
            seen.add(c)
            unique_violations.append(v)

    is_decodable = len(unique_violations) == 0
    if is_decodable:
        feedback = "Story is 100% decodable based on the phonics profile."
    else:
        feedback = (
            "Story contains phonics violations. The following words are not "
            f"decodable for this level: {', '.join(unique_violations)}. "
            "Please rewrite the story to replace or remove these words."
        )

    return {
        "is_decodable": is_decodable,
        "violations": unique_violations,
        "feedback": feedback,
    }
