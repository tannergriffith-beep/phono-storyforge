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
#                                  every Imagen prompt.
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
BRAND_COLORS: dict[str, dict[str, str]] = {
    "Deep Navy":    {"hex": "#192255", "role": "text, line accents, darkest shapes"},
    "Japonica":     {"hex": "#DB7E65", "role": "primary warm accent / energy (coral)"},
    "Warm Gold":    {"hex": "#EBBA7A", "role": "highlights, warmth"},
    "Sage":         {"hex": "#527164", "role": "secondary accent (muted green)"},
    "Strikemaster": {"hex": "#9C6D8B", "role": "character/decorative accent — use sparingly (plum)"},
    "Pearl Bush":   {"hex": "#ECE5DB", "role": "base background surface (oatmeal)"},
    "Parchment":    {"hex": "#F0E9DF", "role": "warmer background surface"},
    "Tundora":      {"hex": "#483E45", "role": "soft shadows, secondary darks"},
}

# Plain-language palette line for prompts (Imagen reads words better than hexes,
# but we name both so the intent is unambiguous and the verifier has the truth).
_PALETTE_PHRASE = (
    "deep navy (#192255), warm coral (#DB7E65), warm gold (#EBBA7A), "
    "muted sage green (#527164), soft plum (#9C6D8B, used sparingly), and warm "
    "oatmeal / parchment backgrounds (#ECE5DB / #F0E9DF)"
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
    """Deterministically composes a full Imagen prompt for one page.

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
