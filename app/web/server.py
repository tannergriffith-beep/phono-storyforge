# app/web/server.py
#
# =============================================================================
# FLAGSHIP STAGE C: the thin FastAPI shell that drives the real loop.
#
# This is I/O only. It owns NO tutoring logic — it calls TutorSession.prepare /
# record_read unchanged and ships the viz payloads (app/web/viz.py) over one
# WebSocket. The brain (planner, alignment, BKT, store) is reused as-is.
#
# WebSocket protocol (one channel, voice-ready):
#   client -> server (JSON text):
#     {"action": "prepare", "learner_id", "name", "age", "interest"}
#     {"action": "submit",  "transcript": "..."}        # Stage-C step 1 (typed)
#     # step 2 (additive): {"action":"read_start"} -> binary PCM frames ->
#     #                     {"action":"read_end"}        -> app/voice Transcriber
#   server -> client (JSON text):
#     {"type": "prepared", ...prepared_payload}
#     {"type": "outcome",  ...outcome_payload}
#     {"type": "error", "message": "..."}
#
# Per-connection state is just the current PreparedSession (between prepare and
# submit); persistence lives in the shared store, so reconnecting resumes the
# same learner. FastAPI is imported only here — never by the offline suite.
# =============================================================================

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.store.learner_store import JSONLearnerStore
from app.store.session_log import JSONLSessionLogStore
from app.tutor.session import TutorSession
from app.web.viz import journey_payload, outcome_payload, prepared_payload

_STATIC = Path(__file__).parent / "static"
_DEFAULT_DATA_DIR = Path("artifacts") / "tutor_data"


def create_app(
    *,
    data_dir: str | Path = _DEFAULT_DATA_DIR,
    book_provider=None,
    illustrated_book_generator=None,
) -> FastAPI:
    """Builds the FastAPI app wired to a persistent TutorSession.

    `book_provider` defaults to TutorSession's deterministic builder (offline,
    filmable, no key). Pass `make_llm_book_provider()` to use the verifier-gated
    Gemini generator without touching anything else.

    `illustrated_book_generator` is the strictly-opt-in, creds-gated hook for the
    slow illustrated take-home book. When None (the default), the feature is
    disabled: the client is told so and the button stays hidden, so the offline
    demo is unchanged. When provided it must be an async callable
    `(objective, profile, *, progress_cb) -> IllustratedBookResult` — normally
    `app.tutor.illustrated_book.generate_illustrated_book`.
    """
    illustrated_enabled = illustrated_book_generator is not None
    app = FastAPI(title="Phono StoryForge — live tutor")
    store = JSONLearnerStore(Path(data_dir) / "profiles")
    log_store = JSONLSessionLogStore(Path(data_dir) / "sessions")
    tutor_kwargs = {"log_store": log_store}
    if book_provider is not None:
        tutor_kwargs["book_provider"] = book_provider
    tutor = TutorSession(store, **tutor_kwargs)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(_STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=_STATIC), name="static")

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        # Tell the client which optional features are wired so it can show/hide
        # the illustrated-book button. Default (no creds) => disabled.
        await websocket.send_json(
            {"type": "capabilities", "illustrated_enabled": illustrated_enabled}
        )
        prepared = None
        # Step-2 voice: raw 16-bit/16 kHz PCM frames from the browser mic are
        # buffered here only while a read is in progress, then handed to the
        # app/voice Transcriber and discarded. The audio never touches disk and
        # never leaves this layer — only the derived transcript + duration do.
        audio_chunks: list[bytes] = []
        capturing = False
        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    break

                # Binary frame: a chunk of mic PCM (only kept mid-read).
                if message.get("bytes") is not None:
                    if capturing:
                        audio_chunks.append(message["bytes"])
                    continue

                text = message.get("text")
                if text is None:
                    continue
                msg = json.loads(text)
                action = msg.get("action")

                if action == "prepare":
                    prepared = tutor.prepare(
                        msg["learner_id"],
                        name=msg.get("name", ""),
                        age=int(msg.get("age", 6)),
                        interest=msg.get("interest", ""),
                    )
                    await websocket.send_json(prepared_payload(prepared))

                elif action == "journey":
                    # Read-only longitudinal view over persisted SessionLogs
                    # (DESIGN §17). Independent of the current prepared session.
                    learner_id = msg.get("learner_id") or (
                        prepared.profile.learner_id if prepared else ""
                    )
                    if not learner_id:
                        await websocket.send_json(
                            {"type": "error", "message": "no learner to show a journey for"}
                        )
                        continue
                    profile = store.get(learner_id)
                    logs = log_store.list(learner_id)
                    await websocket.send_json(
                        journey_payload(
                            learner_id, profile.name if profile else "", logs
                        )
                    )

                elif action == "submit":
                    if prepared is None:
                        await websocket.send_json(
                            {"type": "error", "message": "prepare a session first"}
                        )
                        continue
                    outcome = tutor.record_read(prepared, msg.get("transcript", ""))
                    await websocket.send_json(outcome_payload(outcome))
                    # Force a fresh prepare for the next session so the advanced
                    # target + new book are rebuilt from persisted mastery.
                    prepared = None

                elif action == "read_start":
                    if prepared is None:
                        await websocket.send_json(
                            {"type": "error", "message": "prepare a session first"}
                        )
                        continue
                    audio_chunks = []
                    capturing = True

                elif action == "read_end":
                    capturing = False
                    if prepared is None:
                        audio_chunks = []
                        continue
                    await websocket.send_json(
                        {"type": "voice_status", "message": "transcribing…"}
                    )
                    try:
                        # Voice is ADDITIVE and never load-bearing: if Live/creds
                        # fail, the typed `submit` path is unaffected. The buffered
                        # frames are replayed as the Transcriber's injectable
                        # audio_source; transcribe() runs in a worker thread so its
                        # internal asyncio.run doesn't clash with this event loop.
                        tokens, duration = await _transcribe(audio_chunks, prepared)
                        outcome = tutor.record_read(
                            prepared, tokens, duration_seconds=duration
                        )
                        payload = outcome_payload(outcome)
                        payload["heard"] = tokens
                        await websocket.send_json(payload)
                        prepared = None
                    except Exception as exc:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "message": (
                                    f"voice transcription failed ({exc}). "
                                    "You can type the read instead."
                                ),
                            }
                        )
                    finally:
                        audio_chunks = []

                elif action == "generate_book":
                    # Explicit, async, end-of-session action: run the illustrated
                    # e-book pipeline for the current objective. NEVER inline in
                    # the read loop. Creds-gated; failures are reported, not fatal.
                    if not illustrated_enabled:
                        await websocket.send_json(
                            {"type": "error", "message": "illustrated book generation is not enabled"}
                        )
                        continue
                    if prepared is None:
                        await websocket.send_json(
                            {"type": "error", "message": "prepare a session first"}
                        )
                        continue

                    async def _progress(text: str) -> None:
                        await websocket.send_json(
                            {"type": "book_progress", "message": text}
                        )

                    try:
                        result = await illustrated_book_generator(
                            prepared.objective, prepared.profile, progress_cb=_progress
                        )
                        await websocket.send_json(
                            {
                                "type": "book_ready",
                                "shareable_url": result.shareable_url,
                                "doc_id": result.doc_id,
                                "title": result.title,
                                "decodable": result.decodable,
                                "source": result.source,
                                "pages": result.pages,
                            }
                        )
                    except Exception as exc:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "message": (
                                    f"illustrated book generation failed ({exc}). "
                                    "The reading loop is unaffected — try again."
                                ),
                            }
                        )

                else:
                    await websocket.send_json(
                        {"type": "error", "message": f"unknown action: {action!r}"}
                    )
        except WebSocketDisconnect:
            return

    return app


async def _transcribe(audio_chunks: list[bytes], prepared) -> tuple[list[str], float]:
    """Transcribes buffered mic PCM via the app/voice LiveTranscriber seam.

    The buffered frames are passed as the Transcriber's injectable `audio_source`
    (so the CLI's server-side sounddevice path is never used), and the blocking
    transcribe() — which wraps Gemini Live in asyncio.run — runs in a worker
    thread to stay clear of the server's running event loop. Returns the spoken
    tokens biased toward the page words plus the duration measured from audio.
    """
    from app.voice.transcriber import LiveTranscriber

    transcriber = LiveTranscriber(audio_source=list(audio_chunks))
    return await asyncio.to_thread(transcriber.transcribe, list(prepared.book.words))


def _build_default_app() -> FastAPI:
    """Module-level app for `uvicorn app.web.server:app`.

    Honors PHONO_DATA_DIR and PHONO_LLM_BOOK=1 (verifier-gated Gemini generator)
    so the same entrypoint serves the offline and LLM-backed demos.
    """
    data_dir = os.environ.get("PHONO_DATA_DIR", str(_DEFAULT_DATA_DIR))
    book_provider = None
    if os.environ.get("PHONO_LLM_BOOK", "0") == "1":
        from app.tutor.book_source import make_llm_book_provider

        book_provider = make_llm_book_provider()
    illustrated_book_generator = None
    if os.environ.get("PHONO_ILLUSTRATED_BOOK", "0") == "1":
        from app.tutor.illustrated_book import generate_illustrated_book

        illustrated_book_generator = generate_illustrated_book
    return create_app(
        data_dir=data_dir,
        book_provider=book_provider,
        illustrated_book_generator=illustrated_book_generator,
    )


app = _build_default_app()
