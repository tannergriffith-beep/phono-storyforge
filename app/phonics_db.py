# app/phonics_db.py
#
# =============================================================================
# CAPSTONE CONCEPT 3: Agent Skills / Phonics Reference
# This database represents the starter phonics scope-and-sequence curriculum
# that is used by the decodability-checker tool (an agent skill) and RAG grounding.
#
# CAPSTONE CONCEPT 4: Security Features
# The security loop agent relies on this database to verify 100% compliance
# with the child's mastered reading patterns before finalizing output.
# =============================================================================

from typing import Any

PHONICS_LEVELS: dict[str, dict[str, Any]] = {
    "short_vowels": {
        "description": "Short vowel sounds in single-syllable words (VC, CVC).",
        "consonants": ["b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w", "x", "y", "z"],
        "vowels": ["a", "e", "i", "o", "u"],
    },
    "digraphs": {
        "description": "Consonant digraphs where two letters make one sound (sh, ch, th, wh, ck, ng, ph, qu).",
        "digraphs": ["sh", "ch", "th", "wh", "ck", "ng", "ph", "qu"],
    },
    "blends": {
        "description": "Consonant blends/clusters (bl, cl, fl, st, sp, nd, nt, mp, ft, etc.) allowing adjacent consonants.",
        "blends_allowed": True,
    },
    "silent_e": {
        "description": "Silent 'e' vowel spelling patterns (a_e, e_e, i_e, o_e, u_e).",
        "patterns": ["a_e", "e_e", "i_e", "o_e", "u_e"],
    },
    "r_controlled": {
        "description": "R-controlled vowel spelling patterns (ar, er, ir, or, ur).",
        "r_controlled": ["ar", "er", "ir", "or", "ur"],
    },
    "vowel_teams": {
        "description": "Vowel teams and diphthongs (ai, ay, ee, ea, oa, oe, ie, igh, oo, ou, ow, oi, oy, au, aw).",
        "vowel_teams": ["ai", "ay", "ee", "ea", "oa", "oe", "ie", "igh", "oo", "ou", "ow", "oi", "oy", "au", "aw"],
    },
    # Cross-cutting skills (not part of the linear cumulative sequence above).
    "glued_sounds": {
        "description": "Welded/glued sounds where a vowel fuses with a nasal or 'l' (all, ang, ing, ong, ung, ank, ink, onk, unk). Not sounded out letter-by-letter.",
        "glued": ["all", "ang", "ing", "ong", "ung", "ank", "ink", "onk", "unk"],
    },
    "y_vowel": {
        "description": "The letter 'y' acting as a vowel (long-i in 'my', /ee/ in 'happy').",
    },
    "suffixes": {
        "description": "Common inflectional endings (-s, -es, -ed, -ing) added to an otherwise-decodable base word.",
        "suffixes": ["s", "es", "ed", "ing"],
    },
}

# High-frequency sight words (irregular words that cannot be decoded easily at early levels but are essential)
DEFAULT_SIGHT_WORDS: list[str] = [
    "the", "was", "said", "of", "to", "do", "into", "are", "have", "you",
    "your", "they", "their", "there", "were", "where", "what", "who", "two",
    "my", "by", "she", "he", "we", "me", "be", "so", "go", "no", "is", "his",
    "has", "as", "some", "come", "here", "there", "give", "live", "one", "once",
    "a", "i", "and", "in", "it", "on", "at", "up", "us", "am", "for"
]


# =============================================================================
# CAPSTONE CONCEPT 5: Closed-loop mastery model (Phase 2)
#
# The grapheme inventory + Bayesian Knowledge Tracing (BKT) parameters below
# are the curriculum substrate for the per-learner mastery model
# (app/skills/mastery.py) and the adaptive planner (app/skills/planner.py).
#
# The *unit of mastery is the grapheme* emitted by decompose() in
# app/skills/decodability.py, tagged with the phonics level that introduces it.
# This module is the lower layer (decodability imports from it), so the
# inventory is derived from PHONICS_LEVELS here rather than importing the
# decoder — that keeps the dependency one-directional and the curriculum in a
# single source of truth.
# =============================================================================

# The order in which phonics levels are introduced. Drives the planner's
# "lowest unmastered level/grapheme" ZPD target selection. The linear core
# (short_vowels..vowel_teams) is followed by the cross-cutting skills.
LEVEL_SEQUENCE: list[str] = [
    "short_vowels",
    "digraphs",
    "blends",
    "silent_e",
    "r_controlled",
    "vowel_teams",
    "glued_sounds",
    "y_vowel",
    "suffixes",
]

# Sentinel grapheme keys for levels that decompose() enforces as *structural*
# rules rather than emitting as a GraphemeHit. They still need a trackable
# mastery unit so every phonics level is represented in the inventory:
#   - blends:   adjacent consonants (no single grapheme) -> one sentinel unit
#   - suffixes: inflectional endings handled at word level -> namespaced units
#     keyed with a leading hyphen so "-s" never collides with the consonant "s".
BLEND_GRAPHEME = "_blend_"


def _build_grapheme_inventory() -> list[tuple[str, str]]:
    """Builds the ordered (grapheme, level) inventory from PHONICS_LEVELS.

    Ordering follows LEVEL_SEQUENCE, then the natural order within each level,
    so the planner can scan for the lowest unmastered grapheme deterministically.
    """
    inv: list[tuple[str, str]] = []

    sv = PHONICS_LEVELS["short_vowels"]
    for vowel in sv["vowels"]:
        inv.append((vowel, "short_vowels"))
    for cons in sv["consonants"]:
        # 'y' is tracked as a single unit under y_vowel (its vowel use); its
        # word-initial consonant use reuses the same key.
        if cons == "y":
            continue
        inv.append((cons, "short_vowels"))

    for g in PHONICS_LEVELS["digraphs"]["digraphs"]:
        inv.append((g, "digraphs"))

    inv.append((BLEND_GRAPHEME, "blends"))

    for p in PHONICS_LEVELS["silent_e"]["patterns"]:
        inv.append((p, "silent_e"))

    for g in PHONICS_LEVELS["r_controlled"]["r_controlled"]:
        inv.append((g, "r_controlled"))

    for g in PHONICS_LEVELS["vowel_teams"]["vowel_teams"]:
        inv.append((g, "vowel_teams"))

    for g in PHONICS_LEVELS["glued_sounds"]["glued"]:
        inv.append((g, "glued_sounds"))

    inv.append(("y", "y_vowel"))

    for s in PHONICS_LEVELS["suffixes"]["suffixes"]:
        inv.append((f"-{s}", "suffixes"))

    return inv


# Ordered list of (grapheme, level) and a grapheme -> level lookup. These are
# the canonical set of mastery units tracked per learner.
GRAPHEME_INVENTORY: list[tuple[str, str]] = _build_grapheme_inventory()
GRAPHEME_LEVEL: dict[str, str] = {g: lvl for g, lvl in GRAPHEME_INVENTORY}
GRAPHEMES_BY_LEVEL: dict[str, list[str]] = {
    level: [g for g, lvl in GRAPHEME_INVENTORY if lvl == level]
    for level in LEVEL_SEQUENCE
}

# BKT parameters. Standard 4-parameter Bayesian Knowledge Tracing:
#   p_init    P(L_0)            prior probability the skill is already known
#   p_transit P(T)             probability of learning per practice opportunity
#   p_slip    P(slip|known)    probability of an error despite knowing it
#   p_guess   P(guess|unknown) probability of a correct response by chance
DEFAULT_BKT_PARAMS: dict[str, float] = {
    "p_init": 0.25,
    "p_transit": 0.15,
    "p_slip": 0.10,
    "p_guess": 0.20,
}

# Optional per-level overrides. Later/harder levels start from a lower prior and
# are harder to guess; the linear progression makes early skills stickier.
BKT_PARAMS_BY_LEVEL: dict[str, dict[str, float]] = {
    "short_vowels": {"p_init": 0.35, "p_transit": 0.20},
    "vowel_teams": {"p_init": 0.15, "p_guess": 0.15},
    "y_vowel": {"p_init": 0.15, "p_guess": 0.15},
    "suffixes": {"p_init": 0.20, "p_guess": 0.15},
}

# A grapheme is considered mastered once its BKT P(L) reaches this probability.
MASTERY_THRESHOLD: float = 0.95


def bkt_params_for_level(level: str) -> dict[str, float]:
    """Returns the BKT parameter set for a phonics level (defaults + overrides)."""
    return {**DEFAULT_BKT_PARAMS, **BKT_PARAMS_BY_LEVEL.get(level, {})}


def bkt_params_for_grapheme(grapheme: str) -> dict[str, float]:
    """Returns the BKT parameter set for a grapheme via its phonics level."""
    return bkt_params_for_level(GRAPHEME_LEVEL.get(grapheme, ""))
