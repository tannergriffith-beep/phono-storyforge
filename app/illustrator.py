# app/illustrator.py
#
# =============================================================================
# Phase 5 — the illustrator (PRODUCTION / DEMO path).
#
# This is the "LLM proposes" half of the illustration through-line: it calls
# Nano Banana (Gemini image model) to turn a decodable page into soft cut-paper
# collage art, then hands every result to the deterministic palette verifier
# (app/skills/palette_verifier.py) — the "Python proves it" half — and
# regenerates (or snaps) anything that drifts off the locked Phono palette.
#
# Three pieces live here:
#   1. build_character_bible() + state wiring — one CharacterBible per book,
#      stored as a session-state key and injected into EVERY page prompt (via
#      app.brand.build_page_prompt) so characters stay identical across pages.
#   2. make_image_generator() — the real Nano Banana call, isolated behind a
#      simple (prompt, reference_images) -> png_bytes callable so the orchestration
#      can be unit-tested with a fake generator (no network, no determinism rules).
#   3. illustrate_page() / illustrate_book() — the verify-and-regenerate loop.
#
# Image generation is NOT the reproducible experiment loop (that is eval/), so a
# model call here is fine. Image generation needs billing-enabled credentials:
# the free-tier API key returns quota limit:0 for image models, but Vertex AI
# (billed to GOOGLE_CLOUD_PROJECT) works — so the client factory prefers Vertex.
# =============================================================================

from __future__ import annotations

import os
from dataclasses import dataclass

from app.brand import BRAND_COLORS, build_page_prompt
from app.schemas import Character, CharacterBible
from app.skills.palette_verifier import (
    PaletteVerdict,
    snap_to_palette,
    verify_palette,
)

# Nano Banana = Gemini 2.5 Flash Image (verified available 2026-06: model id
# "gemini-2.5-flash-image"). The Pro variant is for hero pages where quality
# matters more than speed/cost. Verified present on this project's Vertex access.
IMAGE_MODEL = "gemini-2.5-flash-image"
HERO_IMAGE_MODEL = "gemini-3-pro-image"

# The per-book consistency contract lives in session state under this key.
CHARACTER_BIBLE_STATE_KEY = "character_bible"

# Warm accent colors cycled across characters so each gets a distinct, on-brand
# identity. Deep Navy is reserved for line/hair, Strikemaster ("the character
# color") used sparingly, backgrounds stay oatmeal/parchment.
CHARACTER_PALETTE_CYCLE: list[str] = ["Japonica", "Warm Gold", "Sage", "Strikemaster"]


# ---------------------------------------------------------------------------
# Piece 1: character bible (deterministic composer + session-state wiring).
# ---------------------------------------------------------------------------
@dataclass
class CharacterSpec:
    """Minimal per-character input for the deterministic bible builder.

    Only `name` is required; everything else has an on-brand default so a bible
    can be built straight from a StoryOutline's bare character names.
    """

    name: str
    role: str = "character"
    species: str = "a young child"
    # A short recognizability hook; the builder weaves it + palette into the
    # cut-paper appearance/defining-features text.
    trait: str = ""


def build_character_bible(
    story_title: str,
    characters: list[CharacterSpec | str],
    *,
    recurring_setting: str,
    palette_note: str = "",
) -> CharacterBible:
    """Deterministically composes a brand-compliant CharacterBible.

    Each character is described AS layered cut-paper shapes and assigned brand
    palette color NAMES (cycled so characters stay visually distinct). The result
    is guaranteed on-palette and home-set by construction — the deterministic
    contract that app.brand.build_page_prompt injects into every page prompt.
    """
    built: list[Character] = []
    for i, spec in enumerate(characters):
        if isinstance(spec, str):
            spec = CharacterSpec(name=spec)
        accent = CHARACTER_PALETTE_CYCLE[i % len(CHARACTER_PALETTE_CYCLE)]
        palette_colors = [accent, "Deep Navy"]
        trait = spec.trait.strip() or f"a {accent.lower()} paper outfit"
        appearance = (
            f"built from layered torn-paper shapes — a rounded {accent.lower()} "
            f"paper body with deep-navy paper details and hand-torn edges"
        )
        clothing = f"a {accent.lower()} cut-paper outfit"
        defining_features = (
            f"{trait}; always the same {accent.lower()} paper shapes and deep-navy outlines"
        )
        built.append(
            Character(
                name=spec.name,
                role=spec.role,
                species=spec.species,
                appearance=appearance,
                clothing=clothing,
                palette_colors=palette_colors,
                defining_features=defining_features,
            )
        )

    return CharacterBible(
        story_title=story_title,
        characters=built,
        recurring_setting=recurring_setting,
        palette_note=palette_note
        or (
            "Use only the Phono palette as flat cut-paper fills; keep each "
            "character's paper colors identical on every page."
        ),
    )


def put_character_bible(state: dict, bible: CharacterBible) -> None:
    """Stores the bible in session state (serialized) — the 'state key' step."""
    state[CHARACTER_BIBLE_STATE_KEY] = bible.model_dump()


def get_character_bible(state: dict) -> CharacterBible:
    """Reads the per-book bible back out of session state for prompt injection."""
    raw = state[CHARACTER_BIBLE_STATE_KEY]
    return raw if isinstance(raw, CharacterBible) else CharacterBible.model_validate(raw)


# ---------------------------------------------------------------------------
# Piece 2: the real Nano Banana image call, isolated behind a callable.
# ---------------------------------------------------------------------------
# A generator takes (prompt, reference_images) and returns PNG bytes. The
# orchestration only depends on this signature, so tests inject a fake.
ImageGenerator = "Callable[[str, list[bytes] | None], bytes]"


def make_image_client(*, prefer_vertex: bool = True):
    """Builds a google-genai client able to reach the image models.

    Prefers Vertex AI (billed to GOOGLE_CLOUD_PROJECT) because the free-tier
    Gemini API key returns quota limit:0 for image generation. Falls back to the
    API-key client only if no project is configured.
    """
    from google import genai
    from google.genai import types

    # Image models have a low per-minute quota; back off and retry on 429/5xx so
    # a full book's worth of calls succeeds without manual babysitting.
    http_options = types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=6,
            initial_delay=15.0,
            max_delay=90.0,
            exp_base=1.7,
            http_status_codes=[408, 429, 500, 502, 503, 504],
        )
    )
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    if prefer_vertex and project:
        return genai.Client(
            vertexai=True, project=project, location=location, http_options=http_options
        )
    return genai.Client(http_options=http_options)


def make_image_generator(client=None, *, model: str = IMAGE_MODEL):
    """Returns a (prompt, reference_images) -> png_bytes generator backed by Nano Banana.

    `reference_images` (prior page PNGs / a character sheet) are passed alongside
    the prompt to exploit the model's multi-image character consistency.
    """
    import time

    from google.genai import types

    if client is None:
        client = make_image_client()

    def _extract_image(response) -> bytes | None:
        candidate = (response.candidates or [None])[0]
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                return inline.data
        return None

    def _generate(prompt: str, reference_images: list[bytes] | None = None) -> bytes:
        parts: list = [prompt]
        for ref in reference_images or []:
            parts.append(types.Part.from_bytes(data=ref, mime_type="image/png"))
        # Image models occasionally return an empty (text-only) candidate; that
        # is transient, so retry a few times before giving up on the page.
        last_finish = None
        for _attempt in range(3):
            response = client.models.generate_content(model=model, contents=parts)
            image = _extract_image(response)
            if image is not None:
                return image
            cand = (response.candidates or [None])[0]
            last_finish = getattr(cand, "finish_reason", None)
            time.sleep(5)
        raise RuntimeError(
            f"Image model returned no image data after 3 tries "
            f"(last finish_reason={last_finish})."
        )

    return _generate


# ---------------------------------------------------------------------------
# Piece 2b: the OFFLINE stub generator — zero quota, instant, no network.
# ---------------------------------------------------------------------------
# Routine UI/flow testing must never touch the image model (its Vertex quota is
# only ~2 requests/min, so a real book takes minutes and rate-limits hard). This
# drop-in generator has the SAME (prompt, reference_images) -> png_bytes contract
# as make_image_generator, but composes a deterministic, on-palette cut-paper
# placeholder with PIL — so the whole pipeline (verifier, thumbnails, Docs export)
# runs unchanged and for free. Selected via PHONO_STUB_IMAGES (see
# app/tutor/illustrated_book.py) / the tutor_web --stub-images flag.
def make_stub_image_generator(*, size: int = 768):
    """Returns a (prompt, reference_images) -> png_bytes generator with NO network.

    Each page is filled with brand hexes (parchment ground + a cycled accent
    'cut-paper' block + a deep-navy caption), so it is on-palette by construction
    and the real palette verifier passes it without a snap. The accent is derived
    deterministically from the prompt, so pages look distinct but a given page is
    stable across runs. Used for quota-free UI/flow testing.
    """
    import io

    from PIL import Image, ImageDraw

    from app.brand import hex_to_rgb

    ground = hex_to_rgb(BRAND_COLORS["Parchment"]["hex"])
    navy = hex_to_rgb(BRAND_COLORS["Deep Navy"]["hex"])
    accents = [hex_to_rgb(BRAND_COLORS[name]["hex"]) for name in CHARACTER_PALETTE_CYCLE]

    def _generate(prompt: str, reference_images: list[bytes] | None = None) -> bytes:
        # Deterministic accent pick: stable per-prompt, distinct across pages.
        accent = accents[sum(prompt.encode("utf-8")) % len(accents)]
        secondary = accents[(sum(prompt.encode("utf-8")) + 1) % len(accents)]

        img = Image.new("RGB", (size, size), ground)
        draw = ImageDraw.Draw(img)
        # A couple of large flat "cut-paper" blocks — the on-brand collage signal.
        draw.rounded_rectangle(
            [size * 0.10, size * 0.16, size * 0.90, size * 0.70], radius=40, fill=accent
        )
        draw.ellipse(
            [size * 0.55, size * 0.48, size * 0.88, size * 0.82], fill=secondary
        )
        draw.rectangle([0, size * 0.86, size, size], fill=navy)
        draw.text((size * 0.06, size * 0.88), "PLACEHOLDER — stub illustrator", fill=ground)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    return _generate


# ---------------------------------------------------------------------------
# Piece 3: the verify-and-regenerate orchestration.
# ---------------------------------------------------------------------------
@dataclass
class IllustratedPage:
    """One generated page: the art, plus the deterministic on-brand proof."""

    page_number: int
    text: str
    prompt: str
    image_bytes: bytes
    verdict: PaletteVerdict
    attempts: int
    snapped: bool = False


def _corrective_suffix(verdict: PaletteVerdict) -> str:
    """Turns an off-brand verdict into a corrective instruction for regeneration."""
    palette = ", ".join(f"{name} ({spec['hex']})" for name, spec in BRAND_COLORS.items())
    return (
        "\n\nIMPORTANT CORRECTION: the previous attempt drifted off-palette "
        f"({verdict.reason()}). Use ONLY these flat cut-paper colors and no "
        f"others: {palette}. No gradients, no new colors, no shading."
    )


def illustrate_page(
    bible: CharacterBible,
    scene_description: str,
    *,
    age: int,
    page_number: int,
    generate_fn,
    page_text: str = "",
    max_attempts: int = 3,
    enforce: str = "snap",
    reference_images: list[bytes] | None = None,
    verify_kwargs: dict | None = None,
) -> IllustratedPage:
    """Generates one page, then verifies + regenerates until it is on-brand.

    The verifier rejects off-palette art; we regenerate with a corrective prompt
    up to `max_attempts`. If still off-brand and `enforce="snap"`, the best
    attempt is deterministically snapped onto the palette so the book is never
    off-brand. With `enforce="regenerate"`/`"none"` the best attempt is returned
    as-is. `generate_fn` is injected, so this whole loop is testable offline.
    """
    base_prompt = build_page_prompt(bible, scene_description, age=age)
    best: IllustratedPage | None = None

    for attempt in range(1, max_attempts + 1):
        prompt = base_prompt
        if best is not None:
            prompt = base_prompt + _corrective_suffix(best.verdict)
        image_bytes = generate_fn(prompt, reference_images)
        verdict = verify_palette(image_bytes, **(verify_kwargs or {}))
        candidate = IllustratedPage(
            page_number=page_number,
            text=page_text,
            prompt=prompt,
            image_bytes=image_bytes,
            verdict=verdict,
            attempts=attempt,
        )
        if verdict.on_brand:
            return candidate
        # Keep the least-drifted attempt as the fallback.
        if best is None or verdict.off_brand_fraction < best.verdict.off_brand_fraction:
            best = candidate

    assert best is not None
    # The loop ran to exhaustion: report the total number of generations made.
    best.attempts = max_attempts
    if enforce == "snap":
        tolerance = (verify_kwargs or {}).get("tolerance")
        snap_kwargs = {"tolerance": tolerance} if tolerance is not None else {}
        snapped_img = snap_to_palette(best.image_bytes, **snap_kwargs)
        import io

        buf = io.BytesIO()
        snapped_img.save(buf, format="PNG")
        snapped_bytes = buf.getvalue()
        best = IllustratedPage(
            page_number=best.page_number,
            text=best.text,
            prompt=best.prompt,
            image_bytes=snapped_bytes,
            verdict=verify_palette(snapped_bytes, **(verify_kwargs or {})),
            attempts=best.attempts,
            snapped=True,
        )
    return best


def illustrate_book(
    bible: CharacterBible,
    scenes: list[dict],
    *,
    age: int,
    generate_fn,
    use_reference: bool = True,
    max_attempts: int = 3,
    enforce: str = "snap",
    verify_kwargs: dict | None = None,
) -> list[IllustratedPage]:
    """Illustrates every page, threading the first page as a character reference.

    `scenes` is a list of {"description": ..., "text": ...}. Once the first page
    is on-brand it becomes the reference image fed to every later page so Nano
    Banana keeps the characters identical (multi-image consistency).
    """
    pages: list[IllustratedPage] = []
    reference: list[bytes] = []
    for i, scene in enumerate(scenes, start=1):
        page = illustrate_page(
            bible,
            scene["description"],
            age=age,
            page_number=i,
            generate_fn=generate_fn,
            page_text=scene.get("text", ""),
            max_attempts=max_attempts,
            enforce=enforce,
            reference_images=list(reference) or None,
            verify_kwargs=verify_kwargs,
        )
        pages.append(page)
        if use_reference and not reference:
            # Lock the first page's art as the persistent character reference.
            reference.append(page.image_bytes)
    return pages
