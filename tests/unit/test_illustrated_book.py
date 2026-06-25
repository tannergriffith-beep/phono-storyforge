# tests/unit/test_illustrated_book.py
#
# =============================================================================
# INTEGRATION: unit tests for the Objective + LearnerProfile -> PhonicsProfile
# adapter (app/tutor/illustrated_book.objective_to_phonics_profile).
#
# These are PURE and offline — no ADK, no LLM, no creds. They prove the adapter
# that feeds the illustrated-book pipeline maps the live loop's state cleanly:
#   - the mapped levels are valid PhonicsProfile levels (the section-3 risk);
#   - the decodable budget (mastered_levels) is carried through, in order;
#   - personalization (interest/age/sight_words) round-trips, with a fallback;
#   - the profile validates (Pydantic) and round-trips through model_dump.
# The full generation path is creds/LLM-gated and exercised manually.
# =============================================================================

from __future__ import annotations

import pytest

from app.phonics_db import LEVEL_SEQUENCE
from app.schemas import LearnerProfile, Objective, PhonicsProfile
from app.tutor.illustrated_book import (
    _DEFAULT_INTEREST,
    _character_bible_from_outline,
    _text_doc_requests,
    _thumbnail_data_uri,
    objective_to_phonics_profile,
)

# The set of valid PhonicsProfile levels, read off the schema's Literal so this
# test fails if the schema and the planner curriculum ever diverge.
_PROFILE_LEVELS = set(
    PhonicsProfile.model_fields["target_level"].annotation.__args__
)


def test_level_names_match_schema():
    """Section-3 open question: phonics_db levels == PhonicsProfile Literal set."""
    assert set(LEVEL_SEQUENCE) == _PROFILE_LEVELS


def test_adapter_maps_core_fields():
    objective = Objective(
        target_grapheme="sh",
        target_level="digraphs",
        mastered_levels=["short_vowels"],
        review_graphemes=["a"],
        rationale="frontier",
    )
    profile = LearnerProfile.new(
        "ada", name="Ada", age=7, interest="dinosaurs", sight_words=["the", "was"]
    )

    pp = objective_to_phonics_profile(objective, profile)

    assert isinstance(pp, PhonicsProfile)
    assert pp.target_level == "digraphs"
    assert pp.mastered_levels == ["short_vowels"]
    assert pp.interest == "dinosaurs"
    assert pp.age == 7
    assert pp.sight_words == ["the", "was"]
    assert pp.reading_level  # required field, non-empty


def test_mastered_levels_kept_in_curriculum_order_and_deduped():
    objective = Objective(
        target_grapheme="a_e",
        target_level="silent_e",
        # Deliberately out of order + duplicated.
        mastered_levels=["blends", "short_vowels", "digraphs", "short_vowels"],
    )
    profile = LearnerProfile.new("leo", age=6, interest="trucks")

    pp = objective_to_phonics_profile(objective, profile)

    assert pp.mastered_levels == ["short_vowels", "digraphs", "blends"]


def test_blank_interest_falls_back_to_default():
    objective = Objective(
        target_grapheme="a",
        target_level="short_vowels",
        mastered_levels=[],
    )
    profile = LearnerProfile.new("kim", age=5, interest="   ")  # whitespace only

    pp = objective_to_phonics_profile(objective, profile)

    assert pp.interest == _DEFAULT_INTEREST


def test_profile_validates_and_round_trips():
    objective = Objective(
        target_grapheme="ar",
        target_level="r_controlled",
        mastered_levels=["short_vowels", "digraphs", "blends", "silent_e"],
    )
    profile = LearnerProfile.new("sam", age=8, interest="space")

    pp = objective_to_phonics_profile(objective, profile)

    # model_dump -> re-validate is a faithful round trip.
    restored = PhonicsProfile.model_validate(pp.model_dump())
    assert restored == pp
    # reading_level scales with progress: 4 mastered levels -> developing reader.
    assert restored.reading_level == "developing reader"


def test_empty_mastered_levels_is_early_reader():
    objective = Objective(
        target_grapheme="a", target_level="short_vowels", mastered_levels=[]
    )
    profile = LearnerProfile.new("ed", age=5)
    pp = objective_to_phonics_profile(objective, profile)
    assert pp.reading_level == "early reader"
    assert pp.mastered_levels == []


# ---- deterministic Doc request builder (pure, offline) ----------------------


def test_text_doc_requests_indices_are_monotonic_and_cover_text():
    """The batchUpdate index math must stay consistent across inserts/styles."""
    title = "Kate the Cute Cat"
    pages = ["Kate is a cat.", "Kate can ride the bike.", ""]  # blank page skipped
    reqs = _text_doc_requests(title, pages)

    # Title + 2 non-empty pages => 3 insertText, each with a paragraph + text style.
    inserts = [r for r in reqs if "insertText" in r]
    assert len(inserts) == 3
    assert inserts[0]["insertText"]["text"] == title + "\n"
    assert inserts[1]["insertText"]["text"] == "Kate is a cat.\n"

    # Every insert location is strictly increasing and accounts for prior text.
    locs = [r["insertText"]["location"]["index"] for r in inserts]
    assert locs == sorted(locs) and len(set(locs)) == len(locs)
    assert locs[0] == 1  # first insertable index in a fresh doc
    assert locs[1] == 1 + len(title + "\n")

    # Title paragraph is a heading; styling ranges never go backwards.
    para_styles = [r["updateParagraphStyle"] for r in reqs if "updateParagraphStyle" in r]
    assert para_styles[0]["paragraphStyle"]["namedStyleType"] == "HEADING_1"
    for r in reqs:
        for key in ("updateParagraphStyle", "updateTextStyle"):
            if key in r:
                rng = r[key]["range"]
                assert rng["startIndex"] < rng["endIndex"]


# ---- illustration helpers (pure, offline) -----------------------------------


def test_character_bible_from_outline_uses_outline_cast_and_setting():
    outline = {"title": "Kate the Cat", "characters": ["Kate", "Sam"], "setting": "a sunny park"}
    bible = _character_bible_from_outline(outline, "Kate the Cat")
    names = [c.name for c in bible.characters]
    assert names == ["Kate", "Sam"]
    assert bible.recurring_setting == "a sunny park"


def test_character_bible_from_outline_defaults_when_empty():
    bible = _character_bible_from_outline({}, "Untitled")
    assert bible.characters  # a default cast is always present
    assert bible.recurring_setting  # never blank


def test_thumbnail_data_uri_is_small_jpeg():
    import base64
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (1024, 1024), (219, 126, 101)).save(buf, format="PNG")
    uri = _thumbnail_data_uri(buf.getvalue(), max_px=320)

    assert uri.startswith("data:image/jpeg;base64,")
    raw = base64.b64decode(uri.split(",", 1)[1])
    thumb = Image.open(io.BytesIO(raw))
    assert max(thumb.size) <= 320  # downscaled
    assert len(raw) < len(buf.getvalue())  # smaller than the source PNG


def test_invalid_level_name_raises():
    objective = Objective(
        target_grapheme="zz",
        target_level="not_a_real_level",
        mastered_levels=["short_vowels"],
    )
    profile = LearnerProfile.new("zoe", age=6)
    with pytest.raises(ValueError, match="not valid PhonicsProfile levels"):
        objective_to_phonics_profile(objective, profile)
