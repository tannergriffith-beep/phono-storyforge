# tests/unit/test_brand.py
#
# Unit tests for the Phono brand templates (Phase 5 prep): the locked style
# preamble, the character-bible prompt composer, and the palette verifier helper.

from app.brand import (
    BRAND_COLORS,
    ILLUSTRATION_STYLE_PREAMBLE,
    age_band_modifier,
    build_page_prompt,
    character_bible_block,
    hex_to_rgb,
    nearest_brand_color,
)
from app.schemas import Character, CharacterBible


def _bible() -> CharacterBible:
    return CharacterBible(
        story_title="Sam and the Ship",
        characters=[
            Character(
                name="Sam",
                role="protagonist",
                species="a young child",
                appearance="round torn-paper head, short navy paper hair",
                clothing="a warm coral shirt",
                palette_colors=["Claret", "Ink"],
                defining_features="warm coral shirt and a gold paper star badge",
            )
        ],
        recurring_setting="a cozy kitchen at home",
    )


def test_preamble_locks_collage_palette_and_no_text() -> None:
    p = ILLUSTRATION_STYLE_PREAMBLE.lower()
    assert "cut-paper collage" in p
    assert "no gradients" in p
    assert "any text, letters" in p  # text must never be baked into the image
    assert "never a classroom" in p


def test_preamble_has_no_format_placeholders() -> None:
    """It's concatenated into an ADK instruction; stray braces would break state injection."""
    assert "{" not in ILLUSTRATION_STYLE_PREAMBLE and "}" not in ILLUSTRATION_STYLE_PREAMBLE


def test_age_bands() -> None:
    assert age_band_modifier(6) == age_band_modifier(5)
    assert age_band_modifier(9) != age_band_modifier(6)
    assert age_band_modifier(20) == age_band_modifier(12)  # clamps to oldest band


def test_character_bible_block_is_stable_and_complete() -> None:
    block = character_bible_block(_bible())
    assert "Sam" in block
    assert "cozy kitchen" in block
    assert "Claret" in block
    # Deterministic.
    assert character_bible_block(_bible()) == block


def test_build_page_prompt_composes_all_layers() -> None:
    prompt = build_page_prompt(_bible(), "Sam waves a flag on the ship.", age=6)
    assert prompt.startswith(ILLUSTRATION_STYLE_PREAMBLE)
    assert age_band_modifier(6) in prompt
    assert "Sam" in prompt
    assert "Scene: Sam waves a flag on the ship." in prompt
    assert build_page_prompt(_bible(), "Sam waves a flag on the ship.", age=6) == prompt


def test_palette_helpers() -> None:
    assert hex_to_rgb("#23262C") == (35, 38, 44)
    # An almost-ink color snaps to the darkest brand color with a small distance.
    name, hex_value, dist = nearest_brand_color((35, 40, 46))
    assert name == "Ink" and hex_value == "#23262C"
    assert dist < 8
    # Every palette color snaps to itself at distance 0.
    for spec in BRAND_COLORS.values():
        n, h, d = nearest_brand_color(hex_to_rgb(spec["hex"]))
        assert d == 0.0


def test_palette_is_reading_room() -> None:
    # Locks the Phase-7 rebrand: the illustration palette IS the Reading Room set.
    assert BRAND_COLORS["Claret"]["hex"] == "#5C2A33"  # bookcloth claret signature
    assert BRAND_COLORS["Cream"]["hex"] == "#F4EDDE"   # page cream
    assert BRAND_COLORS["Ink"]["hex"] == "#23262C"     # printer's ink
