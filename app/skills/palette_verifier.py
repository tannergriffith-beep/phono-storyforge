# app/skills/palette_verifier.py
#
# =============================================================================
# The on-brand "verify" half of the project's through-line.
#
# The architectural moat of this capstone is: LLMs PROPOSE, deterministic
# non-LLM skills VERIFY. `decompose()` proves a story is decodable; this module
# proves a generated illustration is on-palette. An image model (Nano Banana)
# proposes cut-paper art; this deterministic Python checks every dominant color
# against the locked Phono palette and rejects/snaps anything that has drifted.
#
# Because the chosen style is soft cut-paper collage (flat, solid color fills),
# an on-brand page is mostly large blocks of brand color — exactly the signal
# this verifier thresholds on. No LLM, no network: same image in, same verdict
# out, so it is fully unit-testable with synthetic solid-color images.
# =============================================================================

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from PIL import Image

from app.brand import BRAND_COLORS, nearest_brand_color

# ---------------------------------------------------------------------------
# Thresholds, calibrated against real Nano Banana cut-paper output.
# ---------------------------------------------------------------------------
# A genuinely on-brand page does NOT land exactly on the brand hexes: torn-paper
# texture + edge anti-aliasing spread each fill out by ~40-60 in RGB distance,
# and ~99.7% of pixels stay within 80 of a brand color. Clearly off-palette hues
# (a bright primary red/green/blue) land far past 80 from every brand color
# because the palette is a tight, warm, muted set. So 80 cleanly separates
# "paper-textured brand color" from "wrong color."
DEFAULT_TOLERANCE: float = 80.0

# How much of the image is allowed to drift past the tolerance before we call the
# whole page off-brand. A small off-brand prop (stray highlight) is tolerable; a
# whole wrong-colored character (tens of percent of pixels) is not.
DEFAULT_MAX_OFF_BRAND_FRACTION: float = 0.10

# Deterministic downsample edge. Sampling a fixed thumbnail keeps the verdict
# fast and identical across runs; NEAREST resampling subsamples REAL pixels
# instead of inventing blended intermediate colors that could false-positive.
DEFAULT_SAMPLE_SIZE: int = 96


@dataclass
class PaletteVerdict:
    """The deterministic on-brand proof for one generated image."""

    on_brand: bool
    off_brand_fraction: float
    max_distance: float
    # brand color name -> fraction of pixels nearest to it (the palette histogram).
    coverage: dict[str, float] = field(default_factory=dict)
    # The worst-offending off-brand pixel colors (rgb, distance), most common first.
    off_brand_colors: list[tuple[tuple[int, int, int], float]] = field(default_factory=list)
    tolerance: float = DEFAULT_TOLERANCE
    max_off_brand_fraction: float = DEFAULT_MAX_OFF_BRAND_FRACTION

    def reason(self) -> str:
        """Human-readable verdict, also reused as corrective generation feedback."""
        if self.on_brand:
            top = sorted(self.coverage.items(), key=lambda kv: kv[1], reverse=True)[:3]
            cover = ", ".join(f"{name} {pct:.0%}" for name, pct in top)
            return f"On-brand: {self.off_brand_fraction:.1%} off-palette. Dominant brand colors: {cover}."
        offenders = ", ".join(
            f"rgb{rgb} (dist {dist:.0f})" for rgb, dist in self.off_brand_colors[:3]
        )
        return (
            f"Off-brand: {self.off_brand_fraction:.1%} of the image is more than "
            f"{self.tolerance:.0f} from any Phono color (budget "
            f"{self.max_off_brand_fraction:.0%}). Worst colors: {offenders or 'n/a'}."
        )


def _to_image(source: Image.Image | bytes | str) -> Image.Image:
    """Accepts a PIL image, raw image bytes, or a file path; returns an RGB image."""
    if isinstance(source, Image.Image):
        return source.convert("RGB")
    if isinstance(source, (bytes, bytearray)):
        import io

        return Image.open(io.BytesIO(source)).convert("RGB")
    return Image.open(source).convert("RGB")


def _sample_pixels(image: Image.Image, sample_size: int) -> list[tuple[int, int, int]]:
    """Subsamples the image to a fixed thumbnail of real pixels (deterministic)."""
    small = image.convert("RGB").resize(
        (sample_size, sample_size), resample=Image.Resampling.NEAREST
    )
    raw = small.tobytes()  # tightly packed RGB, 3 bytes/pixel (no getdata deprecation)
    return [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]


def verify_palette(
    source: Image.Image | bytes | str,
    *,
    tolerance: float = DEFAULT_TOLERANCE,
    max_off_brand_fraction: float = DEFAULT_MAX_OFF_BRAND_FRACTION,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
) -> PaletteVerdict:
    """Proves whether a generated illustration stays on the locked Phono palette.

    Every sampled pixel is snapped to its nearest brand color; a pixel beyond
    `tolerance` has drifted off-palette. The page is on-brand only if the
    off-brand fraction stays within `max_off_brand_fraction`. Pure, deterministic.
    """
    pixels = _sample_pixels(_to_image(source), sample_size)
    total = len(pixels)
    if total == 0:
        return PaletteVerdict(
            on_brand=False,
            off_brand_fraction=1.0,
            max_distance=float("inf"),
            tolerance=tolerance,
            max_off_brand_fraction=max_off_brand_fraction,
        )

    coverage_counts: Counter[str] = Counter()
    off_brand_counts: Counter[tuple[int, int, int]] = Counter()
    off_brand_dist: dict[tuple[int, int, int], float] = {}
    off_brand = 0
    max_distance = 0.0

    for rgb in pixels:
        name, _hex, dist = nearest_brand_color(rgb)
        coverage_counts[name] += 1
        if dist > max_distance:
            max_distance = dist
        if dist > tolerance:
            off_brand += 1
            off_brand_counts[rgb] += 1
            off_brand_dist[rgb] = dist

    off_brand_fraction = off_brand / total
    coverage = {name: count / total for name, count in coverage_counts.items()}
    off_brand_colors = [
        (rgb, off_brand_dist[rgb]) for rgb, _ in off_brand_counts.most_common(5)
    ]

    return PaletteVerdict(
        on_brand=off_brand_fraction <= max_off_brand_fraction,
        off_brand_fraction=off_brand_fraction,
        max_distance=max_distance,
        coverage=coverage,
        off_brand_colors=off_brand_colors,
        tolerance=tolerance,
        max_off_brand_fraction=max_off_brand_fraction,
    )


def snap_to_palette(
    source: Image.Image | bytes | str,
    *,
    tolerance: float = DEFAULT_TOLERANCE,
) -> Image.Image:
    """Deterministic enforcement: rewrite every off-tolerance pixel to its nearest
    brand color, leaving on-brand pixels untouched.

    This is the "or snap" enforcement option alongside reject-and-regenerate: it
    guarantees a 100%-on-palette image without another model call. Only pixels
    that have actually drifted are moved, so paper texture within tolerance is
    preserved.
    """
    image = _to_image(source)
    raw = image.tobytes()  # packed RGB (avoids deprecated getdata)
    pixels = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]
    snapped: list[tuple[int, int, int]] = []
    # Cache snapped results per unique color — collage images have few colors.
    cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    from app.brand import hex_to_rgb

    for rgb in pixels:
        out = cache.get(rgb)
        if out is None:
            _name, hex_value, dist = nearest_brand_color(rgb)
            out = hex_to_rgb(hex_value) if dist > tolerance else rgb
            cache[rgb] = out
        snapped.append(out)

    result = Image.new("RGB", image.size)
    result.putdata(snapped)
    return result


# Brand color names exposed for callers building corrective prompts.
BRAND_COLOR_NAMES: list[str] = list(BRAND_COLORS.keys())
