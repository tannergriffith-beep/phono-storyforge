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

import json
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.store.learner_store import JSONLearnerStore
from app.store.session_log import JSONLSessionLogStore
from app.tutor.session import TutorSession
from app.web.viz import outcome_payload, prepared_payload

_STATIC = Path(__file__).parent / "static"
_DEFAULT_DATA_DIR = Path("artifacts") / "tutor_data"


def create_app(
    *,
    data_dir: str | Path = _DEFAULT_DATA_DIR,
    book_provider=None,
) -> FastAPI:
    """Builds the FastAPI app wired to a persistent TutorSession.

    `book_provider` defaults to TutorSession's deterministic builder (offline,
    filmable, no key). Pass `make_llm_book_provider()` to use the verifier-gated
    Gemini generator without touching anything else.
    """
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
        prepared = None
        try:
            while True:
                msg = json.loads(await websocket.receive_text())
                action = msg.get("action")

                if action == "prepare":
                    prepared = tutor.prepare(
                        msg["learner_id"],
                        name=msg.get("name", ""),
                        age=int(msg.get("age", 6)),
                        interest=msg.get("interest", ""),
                    )
                    await websocket.send_json(prepared_payload(prepared))

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

                else:
                    await websocket.send_json(
                        {"type": "error", "message": f"unknown action: {action!r}"}
                    )
        except WebSocketDisconnect:
            return

    return app


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
    return create_app(data_dir=data_dir, book_provider=book_provider)


app = _build_default_app()
