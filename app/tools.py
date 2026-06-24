# app/tools.py
#
# =============================================================================
# CAPSTONE CONCEPT 3: Agent Skills
# This file implements the decodability-checker as a discrete Python tool/skill.
# It uses deterministic rule-based pattern matching (no ML) to check if words in
# a text are decodable based on a child's PhonicsProfile.
# =============================================================================

from __future__ import annotations
import re
from typing import Any
from app.phonics_db import PHONICS_LEVELS, DEFAULT_SIGHT_WORDS


def clean_word(word: str) -> str:
    """Strips punctuation, handles standard contractions, and lowercases a word.

    Args:
        word: The raw word string.

    Returns:
        The cleaned, lowercase word.
    """
    # Replace curly apostrophes with straight ones, then strip non-alphanumeric except apostrophes
    word = word.replace("’", "'").strip().lower()
    word = re.sub(r"[^\w\s']", "", word)
    # Strip leading/trailing apostrophes
    word = word.strip("'")
    return word


def is_word_decodable(word: str, mastered_levels: list[str]) -> bool:
    """Checks if a single cleaned word is decodable under the given mastered phonics levels.

    Args:
        word: The cleaned lowercase word.
        mastered_levels: List of phonics levels the child has mastered.

    Returns:
        True if the word is decodable, False otherwise.
    """
    if not word:
        return True

    # 'short_vowels' (CVC) is the absolute base level. If not mastered, no phonics-based decoding is possible.
    if "short_vowels" not in mastered_levels:
        return False

    # Define standard grapheme sets for each level
    digraphs = ["sh", "ch", "th", "wh", "ck", "ng", "ph", "qu"]
    vowel_teams = ["ai", "ay", "ee", "ea", "oa", "oe", "ie", "igh", "oo", "ou", "ow", "oi", "oy", "au", "aw"]
    r_controlled = ["ar", "er", "ir", "or", "ur"]

    # 1. Reject unmastered digraphs, vowel teams, and r-controlled vowels immediately
    if "digraphs" not in mastered_levels:
        for dg in digraphs:
            if dg in word:
                return False

    if "vowel_teams" not in mastered_levels:
        for vt in vowel_teams:
            if vt in word:
                return False

    if "r_controlled" not in mastered_levels:
        for rc in r_controlled:
            if rc in word:
                return False

    # If silent_e is not mastered, reject the silent 'e' pattern at the end of the word.
    # Pattern: [vowel][consonant]e at the end of a word (e.g. make, like, cute, home).
    if "silent_e" not in mastered_levels:
        if re.search(r"[aeiou][bcdfghjklmnpqrstvwxyz]e$", word):
            return False

    # 2. Perform step-by-step reductions to map the word to C and V placeholders.
    temp = word

    # Clean double consonants (floss words: ff, ll, ss, zz) by replacing them with single ones.
    temp = re.sub(r"([bcdfghjklmnpqrstvwxyz])\1", r"\1", temp)

    # Replace vowel teams with 'V' placeholder
    if "vowel_teams" in mastered_levels:
        for vt in sorted(vowel_teams, key=len, reverse=True):
            temp = temp.replace(vt, "V")

    # Replace r-controlled vowels with 'V' placeholder
    if "r_controlled" in mastered_levels:
        for rc in sorted(r_controlled, key=len, reverse=True):
            temp = temp.replace(rc, "V")

    # Replace consonant digraphs with 'C' placeholder
    if "digraphs" in mastered_levels:
        for dg in sorted(digraphs, key=len, reverse=True):
            temp = temp.replace(dg, "C")

    # Handle silent 'e' replacement if mastered
    if "silent_e" in mastered_levels:
        # Pattern: [aeiouV][bcdfghjklmnpqrstvwxyzC]e at the end of the word -> V + C
        pattern = r"([aeiouV])([bcdfghjklmnpqrstvwxyzC])e$"
        if re.search(pattern, temp):
            temp = re.sub(pattern, r"V\2", temp)

    # 3. Reduce any remaining single consonants and vowels to C and V
    temp = re.sub(r"[bcdfghjklmnpqrstvwxyz]", "C", temp)
    temp = re.sub(r"[aeiou]", "V", temp)

    # Any remaining character that is not 'C' or 'V' indicates unmastered spelling rules (e.g. 'y' as vowel)
    if any(char not in ("C", "V") for char in temp):
        return False

    # 4. Check for consonant blends. If 'blends' is not mastered, adjacent consonants ('CC') are not allowed.
    if "blends" not in mastered_levels:
        if "CC" in temp:
            return False

    # Adjacent vowels ('VV') are never allowed (they must have been replaced by a mastered vowel team/r-controlled)
    if "VV" in temp:
        return False

    return True


def check_decodability(story_text: str, phonics_profile: dict[str, Any]) -> dict[str, Any]:
    """Analyzes a story text and returns decodability metrics.

    Args:
        story_text: The full draft text of the story.
        phonics_profile: Dict representation of PhonicsProfile.

    Returns:
        Dict with is_decodable (bool), violations (list[str]), and feedback (str).
    """
    mastered_levels = list(phonics_profile.get("mastered_levels", []))
    target_level = phonics_profile.get("target_level")
    if target_level and target_level not in mastered_levels:
        mastered_levels.append(target_level)
        
    sight_words = [clean_word(w) for w in phonics_profile.get("sight_words", [])]

    # Combine child's sight words with default sight words
    all_sight_words = set(sight_words + [clean_word(w) for w in DEFAULT_SIGHT_WORDS])

    words = story_text.split()
    violations = []

    for raw_word in words:
        cleaned = clean_word(raw_word)
        if not cleaned:
            continue

        if cleaned in all_sight_words:
            continue

        if not is_word_decodable(cleaned, mastered_levels):
            violations.append(raw_word)

    # Deduplicate violations while preserving order of appearance
    seen = set()
    unique_violations = []
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
            f"Story contains phonics violations. The following words are not decodable for this level: "
            f"{', '.join(unique_violations)}. Please rewrite the story to replace or remove these words."
        )

    return {
        "is_decodable": is_decodable,
        "violations": unique_violations,
        "feedback": feedback,
    }
