# app/tutor/illustrated_book.py
#
# =============================================================================
# INTEGRATION: fold the illustrated e-book pipeline into the live closed loop.
#
# The web tutor (app/web) runs the per-page read loop and tracks per-grapheme
# mastery. This module is the bridge that lets that loop produce the SLOW,
# illustrated take-home deliverable: it maps the live loop's Objective +
# LearnerProfile into the ADK pipeline's PhonicsProfile, then runs the existing
# `root_agent` story pipeline (app/agent.py) seeded with that profile.
#
# Two pieces:
#   1. objective_to_phonics_profile(...)  — the pure, offline, unit-tested adapter.
#   2. generate_illustrated_book(...)     — the async, creds-gated generation fn
#      that drives the ADK Runner, illustrates each page, and exports a Doc,
#      returning the link plus inline base64 page thumbnails.
#
# Design choices (see docs/integration-illustrated-book-loop.md):
#   - The book is decodable for EXACTLY the levels this child has mastered
#     (objective.mastered_levels), so the deliverable matches what the loop
#     scored against. The pipeline's QA LoopAgent enforces this; we re-assert it.
#   - Pages are illustrated with Nano Banana + the deterministic palette verifier
#     (app/illustrator.py — the build_sample_book path), keyed off a CharacterBible
#     built from the planner's outline for cross-page character consistency.
#   - Two independent degrade axes keep a partial result useful and the read loop
#     safe: if illustration is unavailable (image quota/creds) the book falls back
#     to text-only; if the Docs export is unavailable it falls back to pages-only
#     (thumbnails returned, no link). `IllustratedBookResult.source` records which.
#   - We seed `phonics_profile` directly into ADK session state and run a pipeline
#     that SKIPS the intake agent (no extra LLM hop, no chance of intake
#     re-deriving a different mastery budget), the LLM-driven export agent, and
#     the Gmail parent-report agent. The skip is done by cloning the existing
#     sub-agents into a fresh SequentialAgent — clone() resets the parent link,
#     so app/agent.py is left untouched.
#   - The Google Doc is exported DETERMINISTICALLY via app/doc_export.py (the
#     same path scripts/build_sample_book.py uses), NOT via app/agent.py's
#     LLM-driven formatter_export_agent. That agent asks an LLM to orchestrate
#     the Docs/Drive MCP calls and hand-format a JSON result, which is flaky
#     (it routinely returns doc_id="unknown"). The deterministic Docs batchUpdate
#     path produces a real link every time, so the link is the reliable part of
#     the deliverable — only the (already QA-gated) story text comes from the LLM.
#   - app/agent.py is imported LAZILY (inside generate_illustrated_book) so the
#     offline default web demo never pulls in the ADK/MCP stack or its creds.
# =============================================================================

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Optional

from app.phonics_db import LEVEL_SEQUENCE
from app.schemas import LearnerProfile, Objective, PhonicsProfile

# The planner / phonics_db curriculum level names. These are identical to the
# PhonicsProfile `Literal` set (verified), so the adapter needs no remapping —
# but we validate against this set so a future divergence fails loudly in the
# adapter rather than as an opaque Pydantic error deep in the ADK pipeline.
_VALID_LEVELS: frozenset[str] = frozenset(LEVEL_SEQUENCE)

# A child whose `interest` is blank still gets a personalized story; "animals"
# is a safe, universally-decodable-friendly default theme.
_DEFAULT_INTEREST = "animals"

# Async or sync progress sink: receives coarse stage strings ("Planning…", …).
ProgressCb = Optional[Callable[[str], Awaitable[None] | None]]


# ---------------------------------------------------------------------------
# Step 1: the adapter (pure, offline, deterministic, unit-tested)
# ---------------------------------------------------------------------------
def _reading_level_for(objective: Objective) -> str:
    """A coarse reading-level label derived from how far the child has progressed.

    PhonicsProfile requires `reading_level` (a free-text category used only to
    nudge story tone). We derive it deterministically from the number of mastered
    levels so the adapter stays a pure function of its inputs.
    """
    n = len(objective.mastered_levels)
    if n <= 1:
        return "early reader"
    if n <= 4:
        return "developing reader"
    return "fluent reader"


def objective_to_phonics_profile(
    objective: Objective, profile: LearnerProfile
) -> PhonicsProfile:
    """Maps the live loop's Objective + LearnerProfile into an ADK PhonicsProfile.

    The resulting profile carries the child's mastered levels as the decodable
    budget, so the story the ADK pipeline writes is decodable for exactly this
    child. Raises ValueError if a level name is not a valid PhonicsProfile level
    (i.e. the curriculum and the schema have diverged).
    """
    candidate_levels = [objective.target_level, *objective.mastered_levels]
    unknown = sorted({lvl for lvl in candidate_levels if lvl not in _VALID_LEVELS})
    if unknown:
        raise ValueError(
            f"Objective level name(s) {unknown} are not valid PhonicsProfile "
            f"levels {sorted(_VALID_LEVELS)}. The planner/phonics_db curriculum "
            "and the PhonicsProfile schema have diverged; add normalization here."
        )

    # Keep mastered levels in curriculum order and de-duplicated.
    mastered_set = set(objective.mastered_levels)
    mastered = [lvl for lvl in LEVEL_SEQUENCE if lvl in mastered_set]

    interest = (profile.interest or "").strip() or _DEFAULT_INTEREST

    return PhonicsProfile(
        target_level=objective.target_level,
        mastered_levels=mastered,
        sight_words=list(profile.sight_words),
        interest=interest,
        age=profile.age,
        reading_level=_reading_level_for(objective),
    )


# ---------------------------------------------------------------------------
# Step 2: the async generation function (creds/LLM-gated, exercised manually)
# ---------------------------------------------------------------------------
@dataclass
class IllustratedBookResult:
    """The small payload the web layer needs to surface the deliverable."""

    shareable_url: str
    doc_id: str
    title: str
    pages: list[dict] = field(default_factory=list)  # [{"text", "image_ref"}]
    decodable: bool = False
    source: str = "adk_pipeline"


# ADK sub-agent name -> coarse stage message shown in the browser as the run
# progresses. Keyed on event.author so we emit one line per stage transition.
# (Illustration + export are driven deterministically below, not by an agent, so
# their progress is emitted separately.)
_STAGE_MESSAGES = {
    "story_planner": "Planning the story…",
    "writer_agent": "Writing decodable pages…",
    "qa_agent": "Checking every word is decodable…",
}


def _build_seeded_story_pipeline():
    """A fresh SequentialAgent: story planner -> writer/QA loop.

    Built from clones of the existing app/agent.py sub-agents (clone() detaches
    them from `root_agent`), with intake, the illustration-prompt agent, the LLM
    export agent, and the Gmail parent-report agent omitted. The decodability QA
    LoopAgent stays in the path, so the guarantee is preserved. Illustration is
    done directly via app/illustrator.py (Nano Banana + the palette verifier, the
    same path scripts/build_sample_book.py uses) so we get real raster pages with
    cross-page character consistency — the prompt-only agent cannot. Imported
    lazily so the offline default never loads the ADK/MCP stack.
    """
    from google.adk.agents import SequentialAgent

    from app.agent import story_planner, writer_qa_loop

    return SequentialAgent(
        name="story_forge_seeded",
        sub_agents=[story_planner.clone(), writer_qa_loop.clone()],
    )


def _text_doc_requests(title: str, page_texts: list[str]) -> list[dict]:
    """A text-only Google Docs batchUpdate request list (title + one para/page).

    Mirrors the text styling of app.doc_export.build_doc_requests but omits the
    inline page images (raster thumbnails are Phase 2). Pure and deterministic.
    """
    from app.doc_export import BODY_FONT, LABEL_FONT

    requests: list[dict] = []
    index = 1  # first insertable index in a freshly created doc

    def insert(text: str, *, named_style: str, font: str, bold: bool = False) -> None:
        nonlocal index
        start = index
        requests.append({"insertText": {"location": {"index": start}, "text": text}})
        index += len(text)
        requests.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": index},
                    "paragraphStyle": {"namedStyleType": named_style},
                    "fields": "namedStyleType",
                }
            }
        )
        text_style: dict = {"weightedFontFamily": {"fontFamily": font}}
        fields = "weightedFontFamily"
        if bold:
            text_style["bold"] = True
            fields += ",bold"
        requests.append(
            {
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": index - 1},
                    "textStyle": text_style,
                    "fields": fields,
                }
            }
        )

    insert(title + "\n", named_style="HEADING_1", font=LABEL_FONT, bold=True)
    for text in page_texts:
        text = text.strip()
        if text:
            insert(text + "\n", named_style="NORMAL_TEXT", font=BODY_FONT)
    return requests


def _export_doc_sync(title: str, page_texts: list[str]) -> tuple[str, str]:
    """Creates a Google Doc with the story text and returns (doc_id, shareable_url).

    Deterministic: drives the @googleworkspace CLI directly (no LLM). Blocking —
    call via asyncio.to_thread. Raises on any CLI/auth failure.
    """
    from app.doc_export import apply_doc_requests, create_doc, doc_url

    doc_id = create_doc(title or "Phono StoryForge book")
    apply_doc_requests(doc_id, _text_doc_requests(title or "Phono StoryForge book", page_texts))
    return doc_id, doc_url(doc_id)


async def _emit(progress_cb: ProgressCb, message: str) -> None:
    """Calls the progress sink, awaiting it if it is a coroutine function."""
    if progress_cb is None:
        return
    result = progress_cb(message)
    if inspect.isawaitable(result):
        await result


def _character_bible_from_outline(outline: dict, title: str):
    """Builds a deterministic CharacterBible from the planner's story outline.

    Reuses app.illustrator.build_character_bible (on-palette cut-paper characters,
    cycled brand colors) so every page keeps the same characters — exactly the
    consistency contract scripts/build_sample_book.py relies on.
    """
    from app.illustrator import build_character_bible

    characters = outline.get("characters") if isinstance(outline, dict) else None
    characters = [c for c in (characters or []) if isinstance(c, str) and c.strip()]
    if not characters:
        characters = ["the friend"]  # a safe, decodable-agnostic default cast
    setting = (outline.get("setting") if isinstance(outline, dict) else "") or ""
    recurring_setting = setting.strip() or "a warm, cozy home"
    return build_character_bible(
        title or "Phono StoryForge book", characters, recurring_setting=recurring_setting
    )


def _illustrate_pages_sync(bible, page_texts: list[str], *, age: int, model: str, progress=None):
    """Illustrates every page with Nano Banana + the palette verifier (blocking).

    Mirrors app.illustrator.illustrate_book but loops here so we can emit per-page
    progress, and threads the first on-brand page as the reference image so later
    pages keep the characters identical. Call via asyncio.to_thread.

    Degradation is PER-PAGE, not all-or-nothing: the image model occasionally
    returns no image for one page (an empty/text-only candidate), and at the image
    model's ~2-req/min quota a long book is exactly when that is most likely. Rather
    than discard every successfully-illustrated page, a failed page falls back to an
    on-palette placeholder so the rest of the book keeps its real art. The book is
    only fully text-only if the image backend is unavailable from the very first page
    (the placeholder generator is offline, so that only happens for a real-model
    page-1 failure when not in stub mode).
    """
    import os
    import time

    from app.illustrator import (
        illustrate_page,
        make_image_client,
        make_image_generator,
        make_stub_image_generator,
    )

    # The offline placeholder generator: instant, on-palette, zero quota. It is the
    # whole image source in stub mode, and the per-page fallback in real mode.
    fallback_generate = make_stub_image_generator()

    # Offline stub mode (PHONO_STUB_IMAGES): swap ONLY the image generator for the
    # placeholder so routine UI/flow testing never touches the ~2-req/min image
    # quota. Everything else (story LLM, decodability, palette verifier, thumbnails,
    # Docs export) runs unchanged. No client, no pacing sleep.
    if os.environ.get("PHONO_STUB_IMAGES") == "1":
        timed_generate = fallback_generate
    else:
        client = make_image_client()
        generate_fn = make_image_generator(client, model=model)

        def timed_generate(prompt, refs):
            out = generate_fn(prompt, refs)
            time.sleep(2)  # gentle pacing for the image model's per-minute quota
            return out

    def _render(text: str, page_number: int, generate_fn):
        return illustrate_page(
            bible,
            text,  # the decodable page text doubles as the scene description
            age=age,
            page_number=page_number,
            generate_fn=generate_fn,
            page_text=text,
            max_attempts=2,
            enforce="snap",
            reference_images=list(reference) or None,
        )

    pages = []
    reference: list[bytes] = []
    total = len(page_texts)
    for i, text in enumerate(page_texts, start=1):
        if progress:
            progress(f"Illustrating page {i} of {total}…")
        try:
            page = _render(text, i, timed_generate)
            real = True
        except Exception as exc:
            if progress:
                progress(f"Page {i} unavailable ({exc}); using a placeholder for this page.")
            page = _render(text, i, fallback_generate)
            real = False
        pages.append(page)
        # Lock the reference to the first REAL page so a placeholder never becomes
        # the character anchor every later page is matched against.
        if real and not reference:
            reference.append(page.image_bytes)
    return pages


def _thumbnail_data_uri(png_bytes: bytes, *, max_px: int = 320) -> str:
    """Downscales a page PNG to a small JPEG data URI for inline browser preview."""
    import base64
    import io

    from PIL import Image

    img = Image.open(io.BytesIO(png_bytes))
    img.thumbnail((max_px, max_px))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _export_illustrated_doc_sync(title: str, illustrated_pages) -> tuple[str, str]:
    """Exports an ILLUSTRATED Google Doc: each page's image uploaded + embedded.

    Uploads every page PNG to Drive (public-by-link so Docs can fetch it), then
    builds the doc with app.doc_export.build_doc_requests — the proven Phase-5
    export path. Blocking; call via asyncio.to_thread. Raises on any CLI failure.
    """
    import os
    import tempfile

    from app.doc_export import (
        DocPage,
        apply_doc_requests,
        build_doc_requests,
        create_doc,
        doc_url,
        drive_image_uri,
        make_drive_file_public,
        upload_image_to_drive,
    )

    safe_title = title or "Phono StoryForge book"
    doc_pages: list[DocPage] = []
    with tempfile.TemporaryDirectory() as tmp:
        for page in illustrated_pages:
            png_path = os.path.join(tmp, f"page_{page.page_number:02d}.png")
            with open(png_path, "wb") as fh:
                fh.write(page.image_bytes)
            file_id = upload_image_to_drive(png_path, f"{safe_title} - p{page.page_number}.png")
            make_drive_file_public(file_id)
            doc_pages.append(DocPage(text=page.text, image_uri=drive_image_uri(file_id)))

        doc_id = create_doc(safe_title)
        # batchUpdate fetches the (public Drive) image URIs now, before tmp cleanup.
        apply_doc_requests(doc_id, build_doc_requests(safe_title, doc_pages))
    return doc_id, doc_url(doc_id)


def _verify_decodable(state: dict, phonics_profile: PhonicsProfile) -> bool:
    """Re-asserts decodability of the final draft against the child's profile.

    The QA LoopAgent already guarantees this (the pipeline raises otherwise), but
    we check the shipped result defensively with the same shared keystone the
    live loop scores against, so the guarantee is independently verified here.
    """
    from app.skills.decodability import check_decodability

    draft = state.get("story_draft") or {}
    title = draft.get("title", "") if isinstance(draft, dict) else ""
    pages = draft.get("pages", []) if isinstance(draft, dict) else []
    full_text = f"{title}\n" + "\n".join(pages)
    try:
        return bool(check_decodability(full_text, phonics_profile.model_dump())["is_decodable"])
    except Exception:
        return False


async def generate_illustrated_book(
    objective: Objective,
    profile: LearnerProfile,
    *,
    progress_cb: ProgressCb = None,
    illustrate: bool = True,
) -> IllustratedBookResult:
    """Runs the story pipeline, illustrates the pages, and exports a Google Doc.

    Seeds `phonics_profile` into ADK session state, runs the seeded story pipeline
    via the ADK Runner (natively async — iterated directly so per-stage progress
    can stream), generates a raster illustration per page (Nano Banana + palette
    verifier), then exports an illustrated Google Doc. Returns the Doc link plus
    small base64 page thumbnails for inline browser preview.

    Two independent DEGRADE axes keep a partial result useful and the read loop
    safe (`source` records which path was taken):
      - illustration unavailable (image quota/creds) -> text-only book;
      - Docs export unavailable -> pages-only (thumbnails returned, no link).

    Credentials-gated: requires the Vertex backend (story + images) and the
    @googleworkspace CLI auth (Docs/Drive export).
    """
    import asyncio

    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from app.illustrator import IMAGE_MODEL

    phonics_profile = objective_to_phonics_profile(objective, profile)
    await _emit(progress_cb, "Preparing the illustrated book…")

    session_service = InMemorySessionService()
    user_id = profile.learner_id or "learner"
    session_id = f"book-{user_id}-{objective.target_grapheme}"
    await session_service.create_session(
        app_name="app",
        user_id=user_id,
        session_id=session_id,
        state={"phonics_profile": phonics_profile.model_dump()},
    )

    pipeline = _build_seeded_story_pipeline()
    runner = Runner(agent=pipeline, session_service=session_service, app_name="app")

    # A non-empty user message is required to kick off the run even though the
    # profile is already seeded in state (intake is skipped).
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Generate the illustrated book from the seeded phonics_profile.")],
    )

    seen_authors: set[str] = set()
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=message
    ):
        author = getattr(event, "author", None)
        if author in _STAGE_MESSAGES and author not in seen_authors:
            seen_authors.add(author)
            await _emit(progress_cb, _STAGE_MESSAGES[author])

    session = await session_service.get_session(
        app_name="app", user_id=user_id, session_id=session_id
    )
    state = session.state if session else {}

    draft = state.get("story_draft") or {}
    outline = state.get("story_outline") or {}
    title = (draft.get("title") if isinstance(draft, dict) else "") or (
        outline.get("title") if isinstance(outline, dict) else ""
    ) or ""
    page_texts = draft.get("pages", []) if isinstance(draft, dict) else []
    if not page_texts:
        raise RuntimeError("The story pipeline produced no pages to export.")

    # Re-assert the decodability guarantee on the shipped pages (the QA LoopAgent
    # already enforces it; this is an independent, defensive check).
    decodable = _verify_decodable(state, phonics_profile)

    # --- Degrade axis 1: illustration (Nano Banana). Falls back to text-only. ---
    illustrated_pages: list = []
    if illustrate:
        try:
            bible = _character_bible_from_outline(outline, title)
            loop = asyncio.get_running_loop()
            thread_progress = None
            if progress_cb is not None:
                def thread_progress(msg: str) -> None:
                    # Bridge the worker thread's progress back onto the event loop
                    # (and block until sent so the messages stay ordered).
                    asyncio.run_coroutine_threadsafe(_emit(progress_cb, msg), loop).result()

            await _emit(
                progress_cb,
                f"Illustrating {len(page_texts)} pages (this takes a few minutes)…",
            )
            illustrated_pages = await asyncio.to_thread(
                _illustrate_pages_sync,
                bible,
                page_texts,
                age=phonics_profile.age,
                model=IMAGE_MODEL,
                progress=thread_progress,
            )
        except Exception as exc:
            await _emit(
                progress_cb,
                f"Illustration unavailable ({exc}); continuing with a text-only book.",
            )
            illustrated_pages = []

    # --- Degrade axis 2: Docs export. Falls back to pages-only (no link). ---
    doc_id, shareable_url = "", ""
    try:
        await _emit(progress_cb, "Exporting to Google Docs…")
        if illustrated_pages:
            doc_id, shareable_url = await asyncio.to_thread(
                _export_illustrated_doc_sync, title, illustrated_pages
            )
        else:
            doc_id, shareable_url = await asyncio.to_thread(
                _export_doc_sync, title, page_texts
            )
    except Exception as exc:
        await _emit(
            progress_cb,
            f"Google Docs export unavailable ({exc}); showing the pages only.",
        )
        doc_id, shareable_url = "", ""

    # Assemble pages with inline thumbnails (image_ref None when not illustrated).
    thumbs = {p.page_number: _thumbnail_data_uri(p.image_bytes) for p in illustrated_pages}
    pages = [
        {"text": text, "image_ref": thumbs.get(i)}
        for i, text in enumerate(page_texts, start=1)
    ]

    has_images = bool(illustrated_pages)
    source = ("illustrated" if has_images else "text_only") + (
        "" if shareable_url else "_pages_only"
    )

    await _emit(progress_cb, "Done — the illustrated book is ready.")
    return IllustratedBookResult(
        shareable_url=shareable_url,
        doc_id=doc_id,
        title=title,
        pages=pages,
        decodable=decodable,
        source=source,
    )
