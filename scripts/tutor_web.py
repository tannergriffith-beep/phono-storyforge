# scripts/tutor_web.py
#
# =============================================================================
# FLAGSHIP STAGE C: launcher for the web read-along + live mastery viz.
#
# Serves the FastAPI app (app/web/server.py) that drives the real closed loop
# in a browser: the planner picks a target, a decodable book is shown, you submit
# what the child read (typed in step 1, browser-mic voice in step 2), and the UI
# animates the miscue heatmap + mastery bars + the shifting next target — all from
# the real SessionOutcome.
#
# Usage:
#   uv run python -m scripts.tutor_web                 # http://127.0.0.1:8000
#   uv run python -m scripts.tutor_web --llm-book      # verifier-gated Gemini books
#   uv run python -m scripts.tutor_web --port 8080 --data-dir artifacts/demo
# =============================================================================

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

# Load app/.env so GOOGLE_API_KEY (and any Vertex settings) reach the Gemini Live
# voice path. The web launcher otherwise inherits only the shell environment, so a
# key sitting in app/.env would never reach the LiveTranscriber and voice would
# silently fall back to typed input.
load_dotenv(Path(__file__).resolve().parent.parent / "app" / ".env")

_DEFAULT_DATA_DIR = Path("artifacts") / "tutor_data"


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Phono StoryForge live web tutor.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    parser.add_argument("--port", type=int, default=8000, help="Bind port.")
    parser.add_argument("--data-dir", type=Path, default=_DEFAULT_DATA_DIR, help="Where profiles + logs live.")
    parser.add_argument("--llm-book", action="store_true", help="Use the verifier-gated LLM book generator.")
    args = parser.parse_args()

    import uvicorn

    from app.web.server import create_app

    book_provider = None
    if args.llm_book:
        from app.tutor.book_source import make_llm_book_provider

        book_provider = make_llm_book_provider()

    app = create_app(data_dir=args.data_dir, book_provider=book_provider)
    print(f"Phono StoryForge live tutor → http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
