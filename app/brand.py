# app/brand.py
#
# =============================================================================
# Phono brand — single source of truth for the storybook illustrations.
#
# The brand lives in a separate Obsidian vault; this module distills the locked
# decisions that the illustrator agent (Phase 5) must honor so every generated
# image is unmistakably Phono. It holds:
#   - BRAND_COLORS:                the locked 8-color palette (name -> hex/role).
#   - ILLUSTRATION_STYLE_PREAMBLE: the cut-paper-collage style block prepended to
#                                  every image-generation prompt.
#   - AGE_BAND_MODIFIERS:          per-age tone tweaks.
#   - CharacterBible rendering:    a stable text block injected into every page
#                                  prompt so a character looks the same across
#                                  pages (the "character-bible state key").
#   - build_page_prompt():         deterministically composes a full page prompt.
#   - nearest_brand_color():       palette helper for the deterministic post-gen
#                                  palette verifier (LLM proposes art, this side
#                                  verifies it stays on-palette).
#
# Style DECIDED with the user: soft cut-paper collage (Eric Carle-style). Because
# collage is built from solid color shapes, the palette verifier can snap/check
# against the brand hexes cleanly.
# =============================================================================

from __future__ import annotations

from app.schemas import CharacterBible

# ---------------------------------------------------------------------------
# Palette (locked). Roles per toolkit-builder/DESIGN-SYSTEM.md v4.
# ---------------------------------------------------------------------------
# Reading Room palette (Phase 7 — the rebrand's illustration guardrail). The dict
# KEYS are semantic brand-color names (referenced by the palette verifier, the
# illustrator's character cycle, and their tests); VALUES are the brand hexes.
BRAND_COLORS: dict[str, dict[str, str]] = {
    "Ink":    {"hex": "#23262C", "role": "text, line accents, darkest shapes (printer's ink)"},
    "Claret": {"hex": "#5C2A33", "role": "primary signature accent (bookcloth claret)"},
    "Gold":   {"hex": "#B0863F", "role": "highlights, warmth, celebration (gold leaf)"},
    "Sage":   {"hex": "#7C9486", "role": "secondary accent (calm sage green)"},
    "Tide":   {"hex": "#2C5E7A", "role": "decorative accent — use sparingly (deep tide blue)"},
    "Paper":  {"hex": "#F8F4EA", "role": "base background surface (warm paper)"},
    "Cream":  {"hex": "#F4EDDE", "role": "warmer background surface (page cream)"},
    "Shadow": {"hex": "#3A3D42", "role": "soft shadows, secondary darks"},
}

# Plain-language palette line for prompts (image models read color words better
# than hexes, but we name both so the intent is unambiguous and the verifier has
# the truth).
_PALETTE_PHRASE = (
    "deep ink navy (#23262C), bookcloth claret (#5C2A33), warm gold (#B0863F), "
    "calm sage green (#7C9486), deep tide blue (#2C5E7A, used sparingly), and warm "
    "paper / cream backgrounds (#F8F4EA / #F4EDDE)"
)

# ---------------------------------------------------------------------------
# The locked style preamble (cut-paper collage). No curly braces — this string
# is concatenated into the ADK agent instruction, which uses {state} injection.
# ---------------------------------------------------------------------------
ILLUSTRATION_STYLE_PREAMBLE = (
    "Soft cut-paper collage children's-book illustration in the style of layered "
    "torn and cut construction paper. Visible paper texture and slightly rough, "
    "hand-torn edges; shapes layered with gentle drop shadows between layers for "
    "depth. Flat, solid color fills only — absolutely no gradients, no glossy "
    "shading, no photorealism, no 3D render. Warm, handmade, tactile feel. "
    "Characters and faces are built from paper shapes but show real, warm "
    "expressions — never generic smiley faces. Warm, everyday home settings "
    "(kitchen table, living room, backyard, bedroom) — never a classroom. A soft "
    "paper-grain background. Use ONLY these colors: " + _PALETTE_PHRASE + ". "
    "Single cohesive full-bleed illustration with no border or frame. "
    "IMPORTANT: do NOT render any text, letters, numbers, words, or signage in "
    "the image — illustration only."
)

# ---------------------------------------------------------------------------
# Age-band tone modifiers. Keyed by label and resolvable from an age.
# ---------------------------------------------------------------------------
AGE_BAND_MODIFIERS: dict[str, str] = {
    "5-7": (
        "Rounder paper shapes, simpler compositions, larger character "
        "proportions, gentle and playful energy."
    ),
    "8-10": (
        "Fuller scenes with more cut-paper detail, age-proportionate characters "
        "(not toddler-round), light adventure/narrative energy."
    ),
    "11-13": (
        "More sophisticated collage compositions and realistic proportions, "
        "dynamic layouts; deliberately avoid a babyish early-reader picture-book "
        "look while keeping the cut-paper craft."
    ),
}


def age_band_modifier(age: int) -> str:
    """Returns the tone modifier for a child's age (clamped to the bands)."""
    if age <= 7:
        return AGE_BAND_MODIFIERS["5-7"]
    if age <= 10:
        return AGE_BAND_MODIFIERS["8-10"]
    return AGE_BAND_MODIFIERS["11-13"]


# ---------------------------------------------------------------------------
# Character bible -> stable prompt block (the consistency mechanism).
# ---------------------------------------------------------------------------
def character_bible_block(bible: CharacterBible) -> str:
    """Renders a CharacterBible into a stable text block for page prompts.

    The SAME block is appended to every page's prompt so each character keeps the
    same paper colors, clothing, and defining features across the whole book.
    """
    lines = [f"Recurring setting: {bible.recurring_setting}.", "Characters (keep identical on every page):"]
    for c in bible.characters:
        colors = ", ".join(c.palette_colors) if c.palette_colors else "brand palette"
        lines.append(
            f"- {c.name} ({c.role}): {c.species}. {c.appearance} "
            f"Wearing {c.clothing}. Paper colors: {colors}. "
            f"Always recognizable by: {c.defining_features}."
        )
    if bible.palette_note:
        lines.append(bible.palette_note)
    return "\n".join(lines)


def build_page_prompt(
    bible: CharacterBible, scene_description: str, *, age: int
) -> str:
    """Deterministically composes a full image-generation prompt for one page.

    Target model: Nano Banana (Gemini image model) — chosen for cross-page
    character consistency. Verify the current model id before wiring.

    Order: locked style preamble -> age-band modifier -> character bible block ->
    the page's scene -> a closing consistency + no-text reminder. Pure string
    composition (no LLM), so the same inputs always produce the same prompt.
    """
    return (
        ILLUSTRATION_STYLE_PREAMBLE
        + "\n\n"
        + age_band_modifier(age)
        + "\n\n"
        + character_bible_block(bible)
        + "\n\nScene: "
        + scene_description.strip()
        + "\n\nKeep every character, outfit, and color exactly consistent with "
        "the character descriptions above. Cut-paper collage only. No text in "
        "the image."
    )


# ---------------------------------------------------------------------------
# Palette helpers for the deterministic post-generation verifier.
# ---------------------------------------------------------------------------
def hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


# name -> rgb, precomputed for the verifier.
PALETTE_RGB: dict[str, tuple[int, int, int]] = {
    name: hex_to_rgb(spec["hex"]) for name, spec in BRAND_COLORS.items()
}


def nearest_brand_color(rgb: tuple[int, int, int]) -> tuple[str, str, float]:
    """Snaps an arbitrary RGB color to the closest brand color.

    Returns (name, hex, distance) using Euclidean RGB distance. Distance is the
    knob a palette verifier thresholds on to decide whether a generated image has
    drifted off-palette (a perceptual ΔE could replace the metric later).
    """
    best_name = ""
    best_dist = float("inf")
    for name, prgb in PALETTE_RGB.items():
        dist = sum((a - b) ** 2 for a, b in zip(rgb, prgb)) ** 0.5
        if dist < best_dist:
            best_name, best_dist = name, dist
    return best_name, BRAND_COLORS[best_name]["hex"], best_dist
