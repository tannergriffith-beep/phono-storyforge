# app/skills/alignment.py
#
# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop tutor — miscue analysis (Phase 3, Day 5).
#
# This is the "measure" half of the loop's evidence step. Given what a book
# EXPECTED the child to read and what the child actually SPOKE (a transcript),
# it deterministically:
#   1. align()             -> aligns the two word streams (difflib) and
#      classifies every position as a running-record miscue type:
#      correct / substitution / omission / insertion / self_correction /
#      hesitation.
#   2. attribute_evidence() -> diffs the grapheme DECOMPOSITIONS of expected vs
#      spoken words to blame specific graphemes, emitting the exact contract the
#      BKT mastery model consumes: grapheme_evidence: dict[str, list[bool]]
#      (True = read correctly), keyed by GRAPHEME_INVENTORY keys including the
#      structural sentinels (_blend_, -s/-es/-ed/-ing).
#   3. assess()            -> bundles miscues + fluency (accuracy/WCPM) +
#      grapheme_evidence into an AssessmentResult.
#
# Pure Python, no LLM. It builds entirely on decompose() — the same word->
# grapheme map used for decodability and targeting — so attribution and mastery
# share one source of truth.
# =============================================================================

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.skills.decodability import (
    GraphemeHit,
    clean_word,
    decompose,
    inflectional_suffix,
)
from app.skills import fluency
from app.schemas import AssessmentResult, Miscue

# A self-correction is recognized when the child's discarded first attempt is
# this surface-similar to the word they then read correctly (difflib ratio).
_SELF_CORRECTION_SIMILARITY = 0.6

# Miscue kinds. "correct" is not a miscue but is emitted so the op stream is a
# complete account of the read; the rest mirror running-record terminology.
CORRECT = "correct"
SUBSTITUTION = "substitution"
OMISSION = "omission"
INSERTION = "insertion"
SELF_CORRECTION = "self_correction"
HESITATION = "hesitation"

# Kinds that do NOT count against accuracy/WCPM: the word was ultimately read.
_NON_ERROR_KINDS = frozenset({CORRECT, SELF_CORRECTION, HESITATION})


@dataclass
class AlignOp:
    """One aligned position between the expected and spoken word streams."""

    kind: str            # one of the CORRECT/SUBSTITUTION/... constants
    expected: str | None  # expected (cleaned) word, or None for an insertion
    spoken: str | None    # spoken (cleaned) word, or None for an omission
    position: int         # index into the expected word stream
    error_word: str | None = None  # discarded first attempt (self_correction)

    @property
    def is_error(self) -> bool:
        return self.kind not in _NON_ERROR_KINDS


def tokenize(text: str | list[str]) -> list[str]:
    """Splits text into cleaned, lowercased word tokens (drops punctuation/empties)."""
    raw = text if isinstance(text, (list, tuple)) else str(text).split()
    return [c for t in raw if (c := clean_word(t))]


def _similar(a: str, b: str) -> bool:
    """True if two words look like attempts at the same word (surface similarity)."""
    return SequenceMatcher(None, a, b).ratio() >= _SELF_CORRECTION_SIMILARITY


def align(expected: str | list[str], spoken: str | list[str]) -> list[AlignOp]:
    """Aligns expected vs spoken word streams and classifies each position.

    Uses difflib's SequenceMatcher over token lists, then post-processes the
    opcodes to recover two running-record patterns difflib can't label on its
    own:
      - hesitation/repetition: an extra copy of a word adjacent to its correct
        reading (e.g. expected "cat", spoken "cat cat").
      - self_correction: a wrong attempt immediately followed by the correct
        word, where the attempt is surface-similar to it (expected "cat",
        spoken "cot cat").
    Both are treated as the word eventually being read correctly; only true
    substitutions/omissions/insertions are errors.
    """
    exp = tokenize(expected)
    spk = tokenize(spoken)
    sm = SequenceMatcher(a=exp, b=spk, autojunk=False)
    opcodes = sm.get_opcodes()

    ops: list[AlignOp] = []
    idx = 0
    n = len(opcodes)
    while idx < n:
        tag, i1, i2, j1, j2 = opcodes[idx]

        if tag == "equal":
            for k in range(i2 - i1):
                ops.append(AlignOp(CORRECT, exp[i1 + k], spk[j1 + k], i1 + k))
            idx += 1
            continue

        if tag == "delete":
            for k in range(i2 - i1):
                ops.append(AlignOp(OMISSION, exp[i1 + k], None, i1 + k))
            idx += 1
            continue

        if tag == "insert":
            # A lone inserted token next to an equal block may be a repetition
            # (hesitation) or a discarded self-correction attempt rather than a
            # genuine extra word.
            if (j2 - j1) == 1:
                w = spk[j1]
                prev = opcodes[idx - 1] if idx > 0 else None
                nxt = opcodes[idx + 1] if idx + 1 < n else None
                prev_word = exp[prev[2] - 1] if prev and prev[0] == "equal" else None
                next_word = exp[nxt[1]] if nxt and nxt[0] == "equal" else None

                if w == prev_word or w == next_word:
                    # Repetition: the correct read is recorded by the equal block.
                    pos = nxt[1] if next_word == w else prev[2] - 1
                    ops.append(AlignOp(HESITATION, w, w, pos))
                    idx += 1
                    continue
                if next_word is not None and _similar(w, next_word):
                    # The following equal block records the correct read.
                    ops.append(
                        AlignOp(SELF_CORRECTION, next_word, next_word, nxt[1], error_word=w)
                    )
                    idx += 1
                    continue
            # Genuine extra word(s).
            for k in range(j2 - j1):
                ops.append(AlignOp(INSERTION, None, spk[j1 + k], i1))
            idx += 1
            continue

        # replace: pair expected/spoken positionally; leftovers are omissions or
        # insertions.
        exp_block = exp[i1:i2]
        spk_block = spk[j1:j2]
        for k in range(max(len(exp_block), len(spk_block))):
            e = exp_block[k] if k < len(exp_block) else None
            s = spk_block[k] if k < len(spk_block) else None
            if e is not None and s is not None:
                ops.append(AlignOp(SUBSTITUTION, e, s, i1 + k))
            elif e is not None:
                ops.append(AlignOp(OMISSION, e, None, i1 + k))
            else:
                ops.append(AlignOp(INSERTION, None, s, i2 - 1))
        idx += 1

    return ops


# ---------------------------------------------------------------------------
# Grapheme attribution
# ---------------------------------------------------------------------------


def _adjacent_blend_pairs(graphemes: list[GraphemeHit]) -> list[tuple[int, int]]:
    """Indices of adjacent consonant-grapheme pairs (the structural blend rule)."""
    return [
        (i, i + 1)
        for i in range(len(graphemes) - 1)
        if graphemes[i].kind == "C" and graphemes[i + 1].kind == "C"
    ]


def _grapheme_correct_flags(
    exp_graphemes: list[GraphemeHit], spoken_word: str | None, sight: set[str]
) -> list[bool]:
    """Per-expected-grapheme correctness for one word.

    None spoken word => omission (all wrong). An identical spoken word => all
    correct. Otherwise the two grapheme sequences are aligned and graphemes that
    survive in an 'equal' block are correct; replaced/deleted ones are wrong.
    """
    if spoken_word is None:
        return [False] * len(exp_graphemes)

    exp_keys = [g.grapheme for g in exp_graphemes]
    spk_keys = [g.grapheme for g in decompose(spoken_word, sight_words=sight).graphemes]
    if exp_keys == spk_keys:
        return [True] * len(exp_graphemes)

    flags = [False] * len(exp_graphemes)
    sm = SequenceMatcher(a=exp_keys, b=spk_keys, autojunk=False)
    for tag, i1, i2, _j1, _j2 in sm.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                flags[i] = True
    return flags


def _attribute_word(
    expected_word: str,
    spoken_word: str | None,
    evidence: dict[str, list[bool]],
    sight: set[str],
) -> None:
    """Appends per-grapheme True/False evidence for one expected word.

    Emits evidence for every grapheme decompose() produces, plus the structural
    sentinels (_blend_ for adjacent consonant clusters, -s/-es/-ed/-ing for
    inflectional endings) so every phonics level is trackable. Sight words are
    memorized, not decoded, so they contribute no grapheme evidence.
    """
    decomp = decompose(expected_word, sight_words=sight)
    if decomp.is_sight_word or not decomp.graphemes:
        return

    graphemes = decomp.graphemes
    flags = _grapheme_correct_flags(graphemes, spoken_word, sight)

    for g, ok in zip(graphemes, flags):
        evidence[g.grapheme].append(ok)

    # Blend sentinel: one observation per adjacent consonant pair.
    for i, j in _adjacent_blend_pairs(graphemes):
        evidence["_blend_"].append(flags[i] and flags[j])

    # Suffix sentinel: was the inflectional ending read correctly as a whole?
    suffix = inflectional_suffix(decomp.word)
    if suffix:
        start = len(decomp.word) - len(suffix)
        suffix_flags = [
            ok for g, ok in zip(graphemes, flags) if g.span[0] >= start
        ]
        if suffix_flags:
            evidence[f"-{suffix}"].append(all(suffix_flags))


def attribute_evidence(
    ops: list[AlignOp], *, sight_words: set[str] | None = None
) -> dict[str, list[bool]]:
    """Turns a classified op stream into grapheme_evidence for the mastery model.

    Correct reads (and self-corrections/hesitations, whose correct read is
    recorded by the adjacent equal op) yield positive evidence; substitutions
    are diffed grapheme-by-grapheme; omissions yield negative evidence. Pure
    insertions have no expected word and contribute nothing.
    """
    sight = {clean_word(w) for w in (sight_words or set())}
    evidence: dict[str, list[bool]] = defaultdict(list)
    for op in ops:
        if op.kind == CORRECT:
            _attribute_word(op.expected, op.expected, evidence, sight)
        elif op.kind == SUBSTITUTION:
            _attribute_word(op.expected, op.spoken, evidence, sight)
        elif op.kind == OMISSION:
            _attribute_word(op.expected, None, evidence, sight)
        # self_correction / hesitation: covered by the adjacent CORRECT op.
        # insertion: no expected grapheme to attribute.
    return dict(evidence)


# ---------------------------------------------------------------------------
# Assessment (miscues + fluency + evidence)
# ---------------------------------------------------------------------------


def assess(
    expected: str | list[str],
    spoken: str | list[str],
    *,
    duration_seconds: float,
    sight_words: set[str] | None = None,
) -> AssessmentResult:
    """Runs the full miscue analysis for one read-aloud and returns the result."""
    ops = align(expected, spoken)
    total_words = len(tokenize(expected))

    words_correct = sum(1 for op in ops if op.kind == CORRECT)
    substitutions = sum(1 for op in ops if op.kind == SUBSTITUTION)
    omissions = sum(1 for op in ops if op.kind == OMISSION)
    insertions = sum(1 for op in ops if op.kind == INSERTION)
    self_corrections = sum(1 for op in ops if op.kind == SELF_CORRECTION)

    evidence = attribute_evidence(ops, sight_words=sight_words)
    miscues = [
        Miscue(
            kind=op.kind,
            expected=op.expected,
            spoken=op.spoken,
            position=op.position,
            error_word=op.error_word,
        )
        for op in ops
        if op.kind != CORRECT
    ]

    return AssessmentResult(
        expected_text=expected if isinstance(expected, str) else " ".join(expected),
        spoken_text=spoken if isinstance(spoken, str) else " ".join(spoken),
        total_words=total_words,
        words_correct=words_correct,
        errors=substitutions + omissions + insertions,
        substitutions=substitutions,
        omissions=omissions,
        insertions=insertions,
        self_corrections=self_corrections,
        accuracy=fluency.accuracy(words_correct, total_words),
        wcpm=fluency.wcpm(words_correct, duration_seconds),
        duration_seconds=duration_seconds,
        miscues=miscues,
        grapheme_evidence=evidence,
    )
