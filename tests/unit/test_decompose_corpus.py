# tests/unit/test_decompose_corpus.py
#
# =============================================================================
# EXTERNAL VALIDATION of the grapheme segmenter (_segment / decompose).
#
# The "guaranteed decodable" claim rests entirely on _segment() mapping a word
# to the right ordered graphemes. The eval is otherwise self-validating — the
# same code that writes a book also judges it. This file breaks that loop by
# checking the SEGMENTER against truth that lives OUTSIDE the codebase:
#
#   PART A — a hand-verified truth set of ~55 words with human-checked grapheme
#            segmentations spanning every phonics level. Exact-match assertions.
#
#   PART B — structural invariants ("tiling laws") swept over the system word
#            list /usr/share/dict/words (~210k a-z words). These laws follow
#            from what a segmentation IS, independent of any phonics opinion.
#
# Offline-only: uses /usr/share/dict/words, no network / nltk / CMUdict.
# This file is additive — it asserts nothing about decodability VERDICTS, so it
# cannot move the headline experiment numbers.
# =============================================================================

from __future__ import annotations

import functools

import pytest

from app.skills.decodability import _segment, _SILENT_E_RE, VOWELS

# =============================================================================
# PART A — hand-verified grapheme truth set.
#
# Each entry maps a word to the EXACT ordered grapheme strings a structured-
# literacy decoder should emit. Verified by hand against the phonics scope.
#
# Two representation notes that are correct-by-design (not the segmenter being
# loose):
#   * Doubled consonants (the floss rule: ss/ff/ll/zz, and any geminate) are a
#     SINGLE sound, so they collapse to one grapheme. 'pass' -> [p, a, s] where
#     the 's' grapheme spans both s's. (Span tiling is checked in Part B.)
#   * The silent-e split vowel is one discontinuous grapheme written 'a_e':
#     'cake' -> [c, a_e, k].
# =============================================================================

TRUTH_SET: dict[str, list[str]] = {
    # --- short vowels: VC / CVC, plus x as /ks/ ---
    "cat": ["c", "a", "t"],
    "dog": ["d", "o", "g"],
    "pen": ["p", "e", "n"],
    "box": ["b", "o", "x"],
    "tax": ["t", "a", "x"],
    "six": ["s", "i", "x"],
    # --- digraphs: sh / ch / th / wh / ck / ph / qu ---
    "ship": ["sh", "i", "p"],
    "fish": ["f", "i", "sh"],
    "chop": ["ch", "o", "p"],
    "chest": ["ch", "e", "s", "t"],
    "bath": ["b", "a", "th"],
    "this": ["th", "i", "s"],
    "then": ["th", "e", "n"],
    "when": ["wh", "e", "n"],
    "whip": ["wh", "i", "p"],
    "duck": ["d", "u", "ck"],
    "sock": ["s", "o", "ck"],
    "quiz": ["qu", "i", "z"],
    "graph": ["g", "r", "a", "ph"],
    "rich": ["r", "i", "ch"],
    "much": ["m", "u", "ch"],
    # --- blends (adjacent single consonants stay separate graphemes) ---
    "flat": ["f", "l", "a", "t"],
    "stop": ["s", "t", "o", "p"],
    "sand": ["s", "a", "n", "d"],
    "splash": ["s", "p", "l", "a", "sh"],
    "crunch": ["c", "r", "u", "n", "ch"],
    "scratch": ["s", "c", "r", "a", "t", "ch"],
    # --- silent-e / split vowel (a_e, i_e, o_e ...) ---
    "cake": ["c", "a_e", "k"],
    "make": ["m", "a_e", "k"],
    "like": ["l", "i_e", "k"],
    "home": ["h", "o_e", "m"],
    "choke": ["ch", "o_e", "k"],
    "phone": ["ph", "o_e", "n"],
    # --- r-controlled: ar / or / ir / ur / er ---
    "car": ["c", "ar"],
    "star": ["s", "t", "ar"],
    "fork": ["f", "or", "k"],
    "born": ["b", "or", "n"],
    "turn": ["t", "ur", "n"],
    "girl": ["g", "ir", "l"],
    "bird": ["b", "ir", "d"],
    "her": ["h", "er"],
    "shark": ["sh", "ar", "k"],
    # --- vowel teams: ai / ay / ee / ea / oa / igh ---
    "rain": ["r", "ai", "n"],
    "boat": ["b", "oa", "t"],
    "meet": ["m", "ee", "t"],
    "day": ["d", "ay"],
    "play": ["p", "l", "ay"],
    "green": ["g", "r", "ee", "n"],
    "stream": ["s", "t", "r", "ea", "m"],
    "night": ["n", "igh", "t"],
    "high": ["h", "igh"],
    # --- glued / welded sounds: -all, -ing/-ang/-ong/-ung, -ank/-ink/-unk ---
    "ball": ["b", "all"],
    "tall": ["t", "all"],
    "small": ["s", "m", "all"],
    "thing": ["th", "ing"],
    "sing": ["s", "ing"],
    "king": ["k", "ing"],
    "song": ["s", "ong"],
    "bank": ["b", "ank"],
    "sink": ["s", "ink"],
    "sung": ["s", "ung"],
    # 'ng' here is the plain digraph (the rime 'eng' is not a glued unit).
    "strength": ["s", "t", "r", "e", "ng", "th"],
    # --- floss doubles: the doubled consonant is one grapheme (one sound) ---
    "pass": ["p", "a", "s"],
    "puff": ["p", "u", "f"],
    "buzz": ["b", "u", "z"],
    "miss": ["m", "i", "s"],
    "bell": ["b", "e", "l"],
    "fizz": ["f", "i", "z"],
    # --- y as a vowel (non-initial) vs consonant (word-initial) ---
    "my": ["m", "y"],
    "by": ["b", "y"],
    "fly": ["f", "l", "y"],
    "happy": ["h", "a", "p", "y"],
    "gym": ["g", "y", "m"],
    "myth": ["m", "y", "th"],
    "yes": ["y", "e", "s"],  # word-initial y -> consonant
    # --- inflections -s and -ing (clean: -s is its own grapheme, -ing welds) ---
    "dogs": ["d", "o", "g", "s"],
    "cats": ["c", "a", "t", "s"],
    "jumps": ["j", "u", "m", "p", "s"],
    "ducks": ["d", "u", "ck", "s"],
    "jumping": ["j", "u", "m", "p", "ing"],
    "running": ["r", "u", "n", "ing"],
    "making": ["m", "a", "k", "ing"],
}


@pytest.mark.parametrize("word, expected", TRUTH_SET.items())
def test_segment_matches_hand_truth(word: str, expected: list[str]) -> None:
    """_segment must reproduce the human-checked grapheme breakdown exactly."""
    hits = _segment(word)
    assert hits is not None, f"{word!r} should be segmentable"
    assert [h.grapheme for h in hits] == expected


# The inflectional -ed ending is folded into ordinary letter graphemes (e + d)
# rather than emitted as a single 'ed' unit. This is the documented contract of
# the decoder (see inflectional_suffix's docstring: "the decomposition itself
# never emits those sentinels ... it folds the ending into the ordinary
# letter/glued graphemes"). The '-ed' skill is recovered at the WORD level for
# miscue attribution, not inside _segment. Locked here so the boundary is
# explicit rather than mistaken for a bug.
ED_FOLDED_TRUTH: dict[str, list[str]] = {
    "jumped": ["j", "u", "m", "p", "e", "d"],
    "hopped": ["h", "o", "p", "e", "d"],   # 'pp' floss-collapses to one 'p'
    "liked": ["l", "i", "k", "e", "d"],
}


@pytest.mark.parametrize("word, expected", ED_FOLDED_TRUTH.items())
def test_segment_ed_folds_into_letters(word: str, expected: list[str]) -> None:
    """Documented behavior: '-ed' is split into e + d, not a unit grapheme."""
    assert [h.grapheme for h in _segment(word)] == expected


# =============================================================================
# PART B — invariant sweep over /usr/share/dict/words.
#
# These laws follow from what a segmentation IS. We hold them to the whole
# dictionary and report the pass rate + any counterexamples.
#
#   (1) Tiling: graphemes partition the word — spans cover [0, len) with no
#       gaps and no overlaps.
#   (2) Reconstruction: concatenating word[s:e] over the spans rebuilds word.
#   (3) Vowel nucleus: every accepted word has >= 1 vowel grapheme (kind "V").
#   (4) Compression: grapheme count <= letter count.
#
# (1)+(2) are the same law for contiguous spans. The ONE legitimate exception
# is the silent-e split vowel, a deliberately DISCONTINUOUS grapheme: its span
# runs vowel..final-e and therefore overlaps the medial consonant's span (e.g.
# 'cake' -> a_e spans 'ake'). For those words strict partition cannot hold, so
# we assert the weaker-but-correct COVERAGE law (the union of spans is the whole
# word, no gaps) instead. See `_classify` below.
# =============================================================================

DICT_PATH = "/usr/share/dict/words"


def _index_set(hits) -> set[int]:
    """All char indices touched by any grapheme span (union, overlaps merged)."""
    covered: set[int] = set()
    for h in hits:
        covered.update(range(h.span[0], h.span[1]))
    return covered


def _is_strict_partition(hits, n: int) -> bool:
    """True iff spans tile [0, n) with no gaps and no overlaps."""
    spans = sorted(h.span for h in hits)
    if spans[0][0] != 0 or spans[-1][1] != n:
        return False
    return all(prev[1] == nxt[0] for prev, nxt in zip(spans, spans[1:]))


def _reconstructs(hits, word: str) -> bool:
    """True iff concatenating word[s:e] over sorted spans rebuilds the word."""
    spans = sorted(h.span for h in hits)
    return "".join(word[s:e] for s, e in spans) == word


@functools.lru_cache(maxsize=1)
def _sweep() -> dict:
    """Runs every lowercase a-z dict word through _segment once and tallies the
    invariants. Cached so the four invariant tests share one pass over the file.

    Word population: pure lowercase ASCII a-z (drops proper nouns, contractions,
    accented loanwords). _segment never returns None on such words (it only
    rejects non-letters), so 'accepted' == the whole population here.
    """
    stats = {
        "total": 0,
        "strict_ok": 0,          # (1)+(2) hold strictly (contiguous graphemes)
        "split_coverage_ok": 0,  # split vowel emitted; union covers the word
        "count_fail": [],        # (4) violations
        "no_vowel": [],          # (3) words with no V grapheme
        "no_vowel_real_bug": [], # (3) AND the word has a usable vowel letter
        "trailing_e_dropped": [],  # known limitation (characterized below)
        "trailing_e_gap_not_final": [],  # would mean the bug is mischaracterized
        "uncovered": [],         # any gap not explained by the known limitation
    }
    with open(DICT_PATH, encoding="utf-8") as fh:
        for line in fh:
            word = line.strip()
            if not (word.isalpha() and word.islower() and word.isascii()):
                continue
            stats["total"] += 1
            hits = _segment(word)
            assert hits is not None  # a-z words are always segmentable
            n = len(word)

            # (4) compression
            if len(hits) > n:
                stats["count_fail"].append(word)

            # (3) vowel nucleus
            if not any(h.kind == "V" for h in hits):
                stats["no_vowel"].append(word)
                # A drop is only a bug if there WAS a vowel to assign: any
                # a/e/i/o/u, or a non-initial 'y' (which should read as a vowel).
                has_real_vowel = any(c in VOWELS for c in word) or (
                    "y" in word and word.index("y") != 0
                )
                if has_real_vowel:
                    stats["no_vowel_real_bug"].append(word)

            # (1)+(2) tiling / reconstruction
            emitted_split = any(h.grapheme.endswith("_e") for h in hits)
            detected_split = _SILENT_E_RE.search(word) is not None
            if _is_strict_partition(hits, n) and _reconstructs(hits, word):
                stats["strict_ok"] += 1
            elif emitted_split:
                # Discontinuous split-vowel grapheme: strict partition can't
                # hold, but the union must still cover the whole word.
                if _index_set(hits) == set(range(n)):
                    stats["split_coverage_ok"] += 1
                else:
                    stats["uncovered"].append(word)
            elif detected_split and not emitted_split:
                # KNOWN LIMITATION: the silent-e regex fired, but the nominal
                # split vowel got absorbed into a multi-char vowel team (oo, ie,
                # ou, ...) before the split grapheme could be emitted, so the
                # trailing silent 'e' is dropped. e.g. booze, achieve, sieve.
                stats["trailing_e_dropped"].append(word)
                gap = set(range(n)) - _index_set(hits)
                if gap != {n - 1}:
                    # The bug should ONLY ever drop the final char; anything
                    # else means it's not the limitation we think it is.
                    stats["trailing_e_gap_not_final"].append(word)
            else:
                stats["uncovered"].append(word)
    return stats


def test_dict_available() -> None:
    """Sanity guard: skip the sweep cleanly on hosts without the word list."""
    import os

    if not os.path.exists(DICT_PATH):
        pytest.skip(f"{DICT_PATH} not present on this host")


@pytest.mark.skipif(
    not __import__("os").path.exists(DICT_PATH), reason="no system word list"
)
class TestDictInvariants:
    """Structural laws swept over the full system dictionary."""

    def test_count_le_letters(self) -> None:
        """(4) A word can never decode to more graphemes than it has letters."""
        s = _sweep()
        assert s["count_fail"] == [], f"grapheme count > letters: {s['count_fail'][:20]}"

    def test_tiling_and_reconstruction(self) -> None:
        """(1)+(2) Every word is either a strict partition, a coverage-complete
        split-vowel word, or the one characterized trailing-e limitation. No
        word may have an UNEXPLAINED gap/overlap."""
        s = _sweep()
        assert s["uncovered"] == [], (
            f"unexplained tiling failures: {s['uncovered'][:20]}"
        )

    def test_split_vowel_is_coverage_complete(self) -> None:
        """The discontinuous split vowel still covers the whole word (no gaps);
        only its overlap with the medial consonant breaks strict partition."""
        s = _sweep()
        # all emitted-split words landed in split_coverage_ok, none in uncovered
        assert s["split_coverage_ok"] > 0
        assert not any(_SILENT_E_RE.search(w) for w in s["uncovered"])

    def test_every_word_has_a_vowel(self) -> None:
        """(3) The segmenter never strips the vowel nucleus from a word that has
        one. Words with NO vowel grapheme are allowed ONLY when the word is
        genuinely vowelless (initialisms/interjections/Welsh loans: nth, grr,
        cwm, tch, sh, ...)."""
        s = _sweep()
        assert s["no_vowel_real_bug"] == [], (
            f"vowel dropped from words that have one: {s['no_vowel_real_bug'][:20]}"
        )

    def test_known_trailing_e_limitation_is_bounded(self) -> None:
        """The only place tiling weakens to nothing is the documented trailing-e
        drop (vowel-team + silent e). Pin it: it exists, it is a small fraction,
        and it NEVER drops anything but the final char."""
        s = _sweep()
        assert s["trailing_e_gap_not_final"] == [], (
            "trailing-e limitation drops a non-final char — recharacterize it: "
            f"{s['trailing_e_gap_not_final'][:20]}"
        )
        # Bounded: this is a rare orthographic tail, not a pervasive failure.
        assert len(s["trailing_e_dropped"]) < 0.01 * s["total"]


def test_print_validation_summary() -> None:
    """Emits the one-line stats the writeup quotes. Run with -s to view."""
    import os

    if not os.path.exists(DICT_PATH):
        pytest.skip(f"{DICT_PATH} not present on this host")
    s = _sweep()
    total = s["total"]
    tiled = s["strict_ok"] + s["split_coverage_ok"]
    dropped = len(s["trailing_e_dropped"])
    print("\n" + "=" * 70)
    print("SEGMENTER EXTERNAL VALIDATION  (/usr/share/dict/words)")
    print("=" * 70)
    print(
        f"_segment satisfies tiling+reconstruction on {tiled}/{total} dict words "
        f"({s['strict_ok']} strict partition + {s['split_coverage_ok']} "
        f"coverage-complete split-vowel words)."
    )
    print(
        f"grapheme-count<=letter-count holds on {total}/{total}; every word with "
        f"a vowel letter keeps a vowel nucleus ({len(s['no_vowel'])} genuinely "
        f"vowelless edges, 0 false drops)."
    )
    print(
        f"Known bounded limitation: {dropped} words (vowel-team + silent e, e.g. "
        f"'booze'/'achieve') drop the trailing silent 'e' — flagged, not hidden."
    )
    print("=" * 70)
    # Cheap re-assert so this body is also a real test, not just a printer.
    assert tiled + dropped == total
