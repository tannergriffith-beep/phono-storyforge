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
    }
}

# High-frequency sight words (irregular words that cannot be decoded easily at early levels but are essential)
DEFAULT_SIGHT_WORDS: list[str] = [
    "the", "was", "said", "of", "to", "do", "into", "are", "have", "you",
    "your", "they", "their", "there", "were", "where", "what", "who", "two",
    "my", "by", "she", "he", "we", "me", "be", "so", "go", "no", "is", "his",
    "has", "as", "some", "come", "here", "there", "give", "live", "one", "once",
    "a", "i", "and", "in", "it", "on", "at", "up", "us", "am", "for"
]
