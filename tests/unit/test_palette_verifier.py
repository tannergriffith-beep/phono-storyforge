# tests/unit/test_palette_verifier.py
#
# Unit tests for the deterministic palette verifier — the on-brand "verify" half
# of the LLM-proposes / Python-verifies through-line. Synthetic solid-color
# images (no network, no image model) give exact, reproducible fractions.

from PIL import Image

from app.brand import BRAND_COLORS, hex_to_rgb
from app.skills.palette_verifier import (
    DEFAULT_TOLERANCE,
    PaletteVerdict,
    snap_to_palette,
    verify_palette,
)


def _solid(rgb: tuple[int, int, int], size: int = 64) -> Image.Image:
    return Image.new("RGB", (size, size), rgb)


def _half_and_half(
    left: tuple[int, int, int], right: tuple[int, int, int], size: int = 64
) -> Image.Image:
    img = Image.new("RGB", (size, size), left)
    for x in range(size // 2, size):
        for y in range(size):
            img.putpixel((x, y), right)
    return img


NAVY = hex_to_rgb(BRAND_COLORS["Deep Navy"]["hex"])
CORAL = hex_to_rgb(BRAND_COLORS["Japonica"]["hex"])
OATMEAL = hex_to_rgb(BRAND_COLORS["Pearl Bush"]["hex"])
PURE_RED = (255, 0, 0)
PURE_GREEN = (0, 255, 0)


def test_exact_brand_color_is_on_brand_at_zero_distance() -> None:
    verdict = verify_palette(_solid(NAVY))
    assert verdict.on_brand
    assert verdict.off_brand_fraction == 0.0
    assert verdict.max_distance == 0.0
    # The palette histogram attributes 100% to the one brand color present.
    assert verdict.coverage.get("Deep Navy") == 1.0


def test_every_brand_color_passes_itself() -> None:
    for name, spec in BRAND_COLORS.items():
        verdict = verify_palette(_solid(hex_to_rgb(spec["hex"])))
        assert verdict.on_brand, f"{name} should verify as on-brand"
        assert verdict.max_distance == 0.0


def test_pure_offbrand_color_is_rejected() -> None:
    verdict = verify_palette(_solid(PURE_RED))
    assert not verdict.on_brand
    assert verdict.off_brand_fraction == 1.0
    assert verdict.max_distance > DEFAULT_TOLERANCE
    # The offender is surfaced for corrective regeneration.
    assert verdict.off_brand_colors
    assert verdict.off_brand_colors[0][0] == PURE_RED


def test_paper_textured_brand_color_within_tolerance_passes() -> None:
    # Simulate torn-paper / anti-alias drift: nudge coral by ~30 per channel.
    nudged = tuple(min(255, c + 30) for c in CORAL)
    verdict = verify_palette(_solid(nudged))  # type: ignore[arg-type]
    assert verdict.max_distance < DEFAULT_TOLERANCE
    assert verdict.on_brand


def test_small_offbrand_region_within_budget_passes() -> None:
    # ~5% pure-red speckle on an oatmeal page stays within the 10% budget.
    img = _solid(OATMEAL, size=100)
    for x in range(5):  # 5 of 100 columns -> 5% of pixels
        for y in range(100):
            img.putpixel((x, y), PURE_RED)
    verdict = verify_palette(img)
    assert 0.0 < verdict.off_brand_fraction <= 0.10
    assert verdict.on_brand


def test_wrong_colored_half_exceeds_budget_and_fails() -> None:
    verdict = verify_palette(_half_and_half(OATMEAL, PURE_GREEN))
    assert verdict.off_brand_fraction > 0.10
    assert not verdict.on_brand
    assert "Off-brand" in verdict.reason()


def test_verdict_is_deterministic() -> None:
    img = _half_and_half(OATMEAL, PURE_RED)
    a = verify_palette(img)
    b = verify_palette(img)
    assert (a.on_brand, a.off_brand_fraction, a.max_distance) == (
        b.on_brand,
        b.off_brand_fraction,
        b.max_distance,
    )


def test_accepts_png_bytes() -> None:
    import io

    buf = io.BytesIO()
    _solid(NAVY).save(buf, format="PNG")
    verdict = verify_palette(buf.getvalue())
    assert isinstance(verdict, PaletteVerdict)
    assert verdict.on_brand


def test_snap_to_palette_forces_full_compliance() -> None:
    # A half-off-brand image, once snapped, must verify fully on-brand.
    img = _half_and_half(NAVY, PURE_RED)
    assert not verify_palette(img).on_brand
    snapped = snap_to_palette(img)
    snapped_verdict = verify_palette(snapped)
    assert snapped_verdict.on_brand
    assert snapped_verdict.off_brand_fraction == 0.0


def test_snap_preserves_in_tolerance_pixels() -> None:
    # A pixel within tolerance is left exactly as-is (texture preserved).
    nudged = tuple(min(255, c + 20) for c in NAVY)
    snapped = snap_to_palette(_solid(nudged))  # type: ignore[arg-type]
    assert snapped.getpixel((0, 0)) == nudged


def test_on_brand_reason_lists_dominant_colors() -> None:
    verdict = verify_palette(_solid(NAVY))
    assert "On-brand" in verdict.reason()
    assert "Deep Navy" in verdict.reason()
