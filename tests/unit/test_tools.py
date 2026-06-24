# tests/unit/test_tools.py
#
# =============================================================================
# Phonics tools unit tests verifying the rule-based decodability engine.
# =============================================================================

import pytest
from app.tools import is_word_decodable, check_decodability


def test_base_level_not_mastered() -> None:
    """Verifies that if short_vowels is not mastered, no word is decodable."""
    assert not is_word_decodable("cat", [])
    assert not is_word_decodable("dog", ["digraphs"])


def test_level_short_vowels() -> None:
    """Tests short_vowels level individually (VC, CVC)."""
    mastered = ["short_vowels"]
    
    # 3 Known-good words
    assert is_word_decodable("cat", mastered)
    assert is_word_decodable("dog", mastered)
    assert is_word_decodable("pen", mastered)
    
    # 3 Known-violation words
    assert not is_word_decodable("fish", mastered)  # Digraph 'sh'
    assert not is_word_decodable("flat", mastered)  # Consonant blend 'fl'
    assert not is_word_decodable("make", mastered)  # Silent 'e'
    assert not is_word_decodable("car", mastered)   # R-controlled 'ar'
    assert not is_word_decodable("boat", mastered)  # Vowel team 'oa'


def test_level_digraphs() -> None:
    """Tests digraphs level (adds sh, ch, th, wh, ck, ng, ph, qu)."""
    mastered = ["short_vowels", "digraphs"]
    
    # 3 Known-good words
    assert is_word_decodable("fish", mastered)
    assert is_word_decodable("chop", mastered)
    assert is_word_decodable("bath", mastered)
    
    # 3 Known-violation words
    assert not is_word_decodable("flat", mastered)  # Consonant blend 'fl'
    assert not is_word_decodable("make", mastered)  # Silent 'e'
    assert not is_word_decodable("car", mastered)   # R-controlled 'ar'
    assert not is_word_decodable("boat", mastered)  # Vowel team 'oa'


def test_level_blends() -> None:
    """Tests blends level (allows adjacent consonants)."""
    mastered = ["short_vowels", "blends"]
    
    # 3 Known-good words
    assert is_word_decodable("flat", mastered)
    assert is_word_decodable("stop", mastered)
    assert is_word_decodable("sand", mastered)
    
    # 3 Known-violation words
    assert not is_word_decodable("fish", mastered)  # Digraph 'sh'
    assert not is_word_decodable("make", mastered)  # Silent 'e'
    assert not is_word_decodable("boat", mastered)  # Vowel team 'oa'


def test_level_silent_e() -> None:
    """Tests silent_e level (allows final v_c_e patterns)."""
    mastered = ["short_vowels", "silent_e"]
    
    # 3 Known-good words
    assert is_word_decodable("make", mastered)
    assert is_word_decodable("like", mastered)
    assert is_word_decodable("home", mastered)
    
    # 3 Known-violation words
    assert not is_word_decodable("fish", mastered)  # Digraph 'sh'
    assert not is_word_decodable("flat", mastered)  # Consonant blend 'fl'
    assert not is_word_decodable("car", mastered)   # R-controlled 'ar'


def test_level_r_controlled() -> None:
    """Tests r_controlled level (allows ar, er, ir, or, ur)."""
    mastered = ["short_vowels", "r_controlled"]
    
    # 3 Known-good words
    assert is_word_decodable("car", mastered)
    assert is_word_decodable("fork", mastered)
    assert is_word_decodable("turn", mastered)
    
    # 3 Known-violation words
    assert not is_word_decodable("fish", mastered)  # Digraph 'sh'
    assert not is_word_decodable("flat", mastered)  # Consonant blend 'fl'
    assert not is_word_decodable("boat", mastered)  # Vowel team 'oa'


def test_level_vowel_teams() -> None:
    """Tests vowel_teams level (allows ai, ay, ee, ea, oa, etc.)."""
    mastered = ["short_vowels", "vowel_teams"]
    
    # 3 Known-good words
    assert is_word_decodable("rain", mastered)
    assert is_word_decodable("boat", mastered)
    assert is_word_decodable("meet", mastered)
    
    # 3 Known-violation words
    assert not is_word_decodable("fish", mastered)  # Digraph 'sh'
    assert not is_word_decodable("flat", mastered)  # Consonant blend 'fl'
    assert not is_word_decodable("make", mastered)  # Silent 'e'


def test_stacked_levels() -> None:
    """Tests cumulative combinations of phonics levels."""
    # Stacking digraphs + blends
    stacked_db = ["short_vowels", "digraphs", "blends"]
    assert is_word_decodable("brush", stacked_db)  # blend 'br' + digraph 'sh'
    assert is_word_decodable("champ", stacked_db)  # digraph 'ch' + blend 'mp'
    assert is_word_decodable("shack", stacked_db)  # digraph 'sh' + digraph 'ck'
    assert not is_word_decodable("make", stacked_db)  # Silent 'e'

    # Stacking all levels
    all_mastered = ["short_vowels", "digraphs", "blends", "silent_e", "r_controlled", "vowel_teams"]
    assert is_word_decodable("shark", all_mastered)   # sh + ar + rk (blend)
    assert is_word_decodable("stream", all_mastered)  # str + ea
    assert is_word_decodable("choke", all_mastered)   # ch + o_e
    
    # Known-violations even with all levels mastered (non-standard adjacent vowels or spelling)
    assert not is_word_decodable("chaos", all_mastered)  # 'ao' is not a valid vowel team (causes VV)
    assert not is_word_decodable("trial", all_mastered)  # 'ia' is not a valid vowel team (causes VV)
    assert not is_word_decodable("cruel", all_mastered)  # 'ue' is not a valid vowel team (causes VV)
    assert not is_word_decodable("video", all_mastered)  # 'eo' is not a valid vowel team (causes VV)
    assert not is_word_decodable("neon", all_mastered)   # 'eo' is not a valid vowel team (causes VV)


def test_check_decodability_sight_words() -> None:
    """Tests check_decodability with both default and custom sight words."""
    profile = {
        "mastered_levels": ["short_vowels"],
        "target_level": "short_vowels",
        "sight_words": ["dinosaur", "galaxy"]
    }
    
    # Story text containing default sight words ('the', 'was', 'said'),
    # custom sight words ('dinosaur', 'galaxy'), and decodable words ('cat', 'run').
    story_text = "the cat was fast said the dinosaur in the galaxy"
    # Wait, 'fast' contains blend 'st'. With only short_vowels mastered, 'fast' is a violation.
    # Let's replace 'fast' with 'big' to make the decodable parts actually decodable.
    story_text = "the cat was big said the dinosaur in the galaxy"
    
    result = check_decodability(story_text, profile)
    
    assert result["is_decodable"] is True
    assert len(result["violations"]) == 0
    assert "100% decodable" in result["feedback"]


def test_check_decodability_violations() -> None:
    """Tests check_decodability when violations are present."""
    profile = {
        "mastered_levels": ["short_vowels"],
        "target_level": "short_vowels",
        "sight_words": []
    }
    
    # 'fish' (digraph), 'make' (silent e), and 'jump' (blend) are violations
    story_text = "the cat had a fish and did jump to make a home"
    
    result = check_decodability(story_text, profile)
    
    assert result["is_decodable"] is False
    # Check that the violating words are recorded (deduplicated)
    # Note: 'home' is also a violation (silent e)
    expected_violations = {"fish", "jump", "make", "home"}
    assert set(result["violations"]) == expected_violations
    assert "Story contains phonics violations" in result["feedback"]
