# tests/unit/test_illustrator.py
#
# Unit tests for the deterministic illustrator pieces: the character-bible
# composer + session-state wiring, and the verify-and-regenerate orchestration
# (exercised with a fake image generator — no network, no image model).

import io

from PIL import Image

from app.brand import BRAND_COLORS, build_page_prompt, hex_to_rgb
from app.illustrator import (
    CHARACTER_BIBLE_STATE_KEY,
    CharacterSpec,
    build_character_bible,
    get_character_bible,
    illustrate_book,
    illustrate_page,
    put_character_bible,
)
from app.schemas import CharacterBible

NAVY = hex_to_rgb(BRAND_COLORS["Ink"]["hex"])
OATMEAL = hex_to_rgb(BRAND_COLORS["Paper"]["hex"])
PURE_RED = (255, 0, 0)
BRAND_NAMES = set(BRAND_COLORS.keys())


def _png(rgb: tuple[int, int, int], size: int = 32) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (size, size), rgb).save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Character bible (piece 1)
# ---------------------------------------------------------------------------
def test_bible_builder_from_bare_names_is_brand_compliant() -> None:
    bible = build_character_bible(
        "Sam and Tom",
        ["Sam", "Tom"],
        recurring_setting="a cozy kitchen at home",
    )
    assert isinstance(bible, CharacterBible)
    assert [c.name for c in bible.characters] == ["Sam", "Tom"]
    # Every assigned palette color must be a real brand color name.
    for c in bible.characters:
        assert c.palette_colors
        assert set(c.palette_colors) <= BRAND_NAMES
    # Distinct accents are cycled so the two characters look different.
    assert bible.characters[0].palette_colors[0] != bible.characters[1].palette_colors[0]


def test_bible_builder_is_deterministic() -> None:
    a = build_character_bible("B", [CharacterSpec("Pip", trait="a gold star badge")],
                              recurring_setting="a living room")
    b = build_character_bible("B", [CharacterSpec("Pip", trait="a gold star badge")],
                              recurring_setting="a living room")
    assert a.model_dump() == b.model_dump()


def test_bible_round_trips_through_session_state() -> None:
    bible = build_character_bible("Story", ["Sam"], recurring_setting="a backyard")
    state: dict = {}
    put_character_bible(state, bible)
    assert CHARACTER_BIBLE_STATE_KEY in state
    # Stored serialized (state must be JSON-friendly for ADK).
    assert isinstance(state[CHARACTER_BIBLE_STATE_KEY], dict)
    restored = get_character_bible(state)
    assert restored.model_dump() == bible.model_dump()


def test_state_bible_injects_into_every_page_prompt() -> None:
    bible = build_character_bible("Story", ["Sam"], recurring_setting="a backyard")
    state: dict = {}
    put_character_bible(state, bible)
    p1 = build_page_prompt(get_character_bible(state), "Sam digs.", age=6)
    p2 = build_page_prompt(get_character_bible(state), "Sam naps.", age=6)
    # Same character block appears verbatim on different pages (cross-page consistency).
    assert "Sam" in p1 and "Sam" in p2
    assert "a backyard" in p1 and "a backyard" in p2


# ---------------------------------------------------------------------------
# Verify-and-regenerate loop (piece 3)
# ---------------------------------------------------------------------------
def _bible() -> CharacterBible:
    return build_character_bible("Sam", ["Sam"], recurring_setting="a cozy kitchen")


def test_on_brand_first_try_does_not_retry() -> None:
    calls = []

    def gen(prompt, refs):
        calls.append(prompt)
        return _png(OATMEAL)

    page = illustrate_page(_bible(), "Sam waves.", age=6, page_number=1, generate_fn=gen)
    assert page.verdict.on_brand
    assert page.attempts == 1
    assert len(calls) == 1
    assert not page.snapped


def test_regenerates_until_on_brand() -> None:
    # First attempt off-brand (pure red), second on-brand (oatmeal).
    seq = [_png(PURE_RED), _png(OATMEAL)]

    def gen(prompt, refs):
        return seq.pop(0)

    page = illustrate_page(_bible(), "Sam waves.", age=6, page_number=1,
                           generate_fn=gen, max_attempts=3)
    assert page.verdict.on_brand
    assert page.attempts == 2


def test_second_prompt_carries_corrective_feedback() -> None:
    prompts = []
    seq = [_png(PURE_RED), _png(OATMEAL)]

    def gen(prompt, refs):
        prompts.append(prompt)
        return seq.pop(0)

    illustrate_page(_bible(), "Sam waves.", age=6, page_number=1, generate_fn=gen)
    assert len(prompts) == 2
    assert "CORRECTION" in prompts[1]
    assert "CORRECTION" not in prompts[0]


def test_persistent_drift_is_snapped_to_palette() -> None:
    # Every attempt drifts; with enforce="snap" the result must end on-brand.
    def gen(prompt, refs):
        return _png(PURE_RED)

    page = illustrate_page(_bible(), "Sam waves.", age=6, page_number=1,
                           generate_fn=gen, max_attempts=2, enforce="snap")
    assert page.snapped
    assert page.verdict.on_brand  # snapped image now verifies on-brand
    assert page.attempts == 2


def test_persistent_drift_without_enforcement_returns_best_offbrand() -> None:
    def gen(prompt, refs):
        return _png(PURE_RED)

    page = illustrate_page(_bible(), "Sam waves.", age=6, page_number=1,
                           generate_fn=gen, max_attempts=2, enforce="none")
    assert not page.snapped
    assert not page.verdict.on_brand


def test_illustrate_book_threads_first_page_as_reference() -> None:
    seen_refs = []

    def gen(prompt, refs):
        seen_refs.append(refs)
        return _png(OATMEAL)

    scenes = [
        {"description": "Sam wakes up.", "text": "Sam is up."},
        {"description": "Sam eats.", "text": "Sam has jam."},
        {"description": "Sam naps.", "text": "Sam naps."},
    ]
    pages = illustrate_book(_bible(), scenes, age=6, generate_fn=gen)
    assert len(pages) == 3
    assert [p.page_number for p in pages] == [1, 2, 3]
    # Page 1 has no reference; later pages receive exactly the page-1 image.
    assert seen_refs[0] is None
    assert seen_refs[1] == [pages[0].image_bytes]
    assert seen_refs[2] == [pages[0].image_bytes]
