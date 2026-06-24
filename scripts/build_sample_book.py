#!/usr/bin/env python
# scripts/build_sample_book.py
#
# =============================================================================
# Phase 5 demo: produce ONE real, illustrated, decodable book end-to-end and
# open it in Google Docs. This is the production/demo path (real Nano Banana
# calls), NOT the reproducible experiment loop in eval/.
#
# It exercises the whole illustration through-line:
#   1. A hand-authored decodable book, each page VERIFIED decodable by the same
#      check_decodability() that guards the writer loop.
#   2. One CharacterBible, stored in session state and injected into every page
#      prompt (app.brand.build_page_prompt) for cross-page character consistency.
#   3. Nano Banana generates soft cut-paper collage pages; the deterministic
#      palette verifier proves each one is on the Phono palette (regenerate/snap
#      on drift).
#   4. The real images are embedded into a Google Doc (Drive upload + Docs
#      inline image), OpenDyslexic body / Poppins title.
#
# Usage:
#   python -m scripts.build_sample_book                # generate + export to Docs
#   python -m scripts.build_sample_book --no-export    # images only (skip Docs)
#   python -m scripts.build_sample_book --model gemini-3-pro-image   # hero quality
# =============================================================================

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load credentials the same way the test suite does.
load_dotenv(Path(__file__).resolve().parent.parent / "app" / ".env")

from app.doc_export import (  # noqa: E402
    DocPage,
    apply_doc_requests,
    build_doc_requests,
    create_doc,
    doc_url,
    drive_image_uri,
    make_drive_file_public,
    upload_image_to_drive,
)
from app.illustrator import (  # noqa: E402
    IMAGE_MODEL,
    CharacterSpec,
    build_character_bible,
    get_character_bible,
    illustrate_book,
    make_image_client,
    make_image_generator,
    put_character_bible,
)
from app.skills.decodability import check_decodability  # noqa: E402

# --- The decodable sample book (digraphs level): "Sam the Fox" -------------
TITLE = "Sam the Fox"
PROFILE = {"target_level": "digraphs", "mastered_levels": ["short_vowels", "digraphs"]}
AGE = 6

PAGES = [
    {
        "text": "Sam is a fox.",
        "description": "Sam the small fox stands in a warm, cozy living room, paws "
        "up, looking friendly and happy at the reader.",
    },
    {
        "text": "Sam has a red cup.",
        "description": "Sam the fox sits at the kitchen table holding a red paper "
        "cup, warm morning light.",
    },
    {
        "text": "Sam sat in the sun.",
        "description": "Sam the fox sits by a big sunny window at home, warm gold "
        "light pouring in.",
    },
    {
        "text": "Sam ran to the shed.",
        "description": "Sam the fox runs across a cozy backyard toward a small "
        "wooden garden shed.",
    },
    {
        "text": "Sam met a big cat.",
        "description": "Sam the fox meets a big friendly cat in the backyard; the "
        "two greet each other warmly.",
    },
    {
        "text": "Sam and the cat nap.",
        "description": "Sam the fox and the big cat curl up together, napping on a "
        "soft rug in a cozy living room.",
    },
]


def verify_decodable() -> None:
    """Abort unless every page is decodable for the profile (project through-line)."""
    bad = []
    for p in PAGES:
        result = check_decodability(p["text"], PROFILE)
        if not result["is_decodable"]:
            bad.append((p["text"], result["violations"]))
    if bad:
        raise SystemExit(f"Sample book is NOT fully decodable: {bad}")
    print(f"[decodability] all {len(PAGES)} pages verified decodable for {PROFILE['target_level']}.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=IMAGE_MODEL, help="image model id")
    ap.add_argument("--no-export", action="store_true", help="skip the Google Doc export")
    ap.add_argument("--out", default="results/sample_book", help="output dir for PNGs")
    ap.add_argument("--max-attempts", type=int, default=2)
    ap.add_argument("--skip-generate", action="store_true",
                    help="reuse PNGs already in --out (export only, no image calls)")
    args = ap.parse_args()

    verify_decodable()
    out_dir = Path(args.out)

    if args.skip_generate:
        pages = _load_cached_pages(out_dir)
        print(f"[generate] skipped — reusing {len(pages)} cached pages from {out_dir}/")
        _export(pages, out_dir, no_export=args.no_export)
        return

    # --- One CharacterBible, stored in state, injected into every page ---
    bible = build_character_bible(
        TITLE,
        [
            CharacterSpec("Sam", role="protagonist", species="a small fox",
                          trait="warm coral paper fur and a deep navy paper vest"),
            CharacterSpec("the cat", role="friend", species="a big friendly cat",
                          trait="sage-green paper fur and warm gold paper eyes"),
        ],
        recurring_setting="a warm, cozy home (kitchen, living room, sunny window, backyard)",
    )
    state: dict = {}
    put_character_bible(state, bible)  # the session-state key
    bible = get_character_bible(state)  # read back for prompt injection
    print(f"[bible] {len(bible.characters)} characters; setting = {bible.recurring_setting}")

    # --- Real Nano Banana generator + verify/snap loop ---
    client = make_image_client()
    generate_fn = make_image_generator(client, model=args.model)

    def timed_generate(prompt: str, refs):
        out = generate_fn(prompt, refs)
        time.sleep(2)  # gentle pacing for image-model quotas
        return out

    print(f"[generate] illustrating {len(PAGES)} pages with {args.model} ...")
    pages = illustrate_book(
        bible, PAGES, age=AGE, generate_fn=timed_generate,
        max_attempts=args.max_attempts, enforce="snap",
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    for page in pages:
        png_path = out_dir / f"page_{page.page_number:02d}.png"
        png_path.write_bytes(page.image_bytes)
        flag = " [SNAPPED]" if page.snapped else ""
        print(
            f"  page {page.page_number}: {page.verdict.off_brand_fraction:.1%} off-palette, "
            f"{page.attempts} attempt(s){flag} -> {png_path}"
        )
    print(f"[generate] saved {len(pages)} pages to {out_dir}/")

    _export(pages, out_dir, no_export=args.no_export)


@dataclass
class _CachedPage:
    page_number: int
    text: str


def _load_cached_pages(out_dir: Path) -> list[_CachedPage]:
    """Rebuilds page metadata for export from PNGs already on disk."""
    pages = []
    for i, p in enumerate(PAGES, start=1):
        if not (out_dir / f"page_{i:02d}.png").exists():
            raise SystemExit(f"--skip-generate: missing {out_dir}/page_{i:02d}.png")
        pages.append(_CachedPage(page_number=i, text=p["text"]))
    return pages


def _export(pages, out_dir: Path, *, no_export: bool) -> None:
    """Uploads each page image to Drive and embeds it in a new Google Doc."""
    if no_export:
        print("[export] skipped (--no-export).")
        return
    print("[export] uploading images to Drive + building the Doc ...")
    doc_pages: list[DocPage] = []
    for page in pages:
        png_path = out_dir / f"page_{page.page_number:02d}.png"
        file_id = upload_image_to_drive(str(png_path), f"{TITLE} - p{page.page_number}.png")
        make_drive_file_public(file_id)
        doc_pages.append(DocPage(text=page.text, image_uri=drive_image_uri(file_id)))

    doc_id = create_doc(TITLE)
    apply_doc_requests(doc_id, build_doc_requests(TITLE, doc_pages))
    url = doc_url(doc_id)
    print(f"\n[export] DONE — illustrated decodable book is in Google Docs:\n  {url}")


if __name__ == "__main__":
    main()
