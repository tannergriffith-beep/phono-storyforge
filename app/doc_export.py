# app/doc_export.py
#
# =============================================================================
# Phase 5 — embed the REAL generated illustrations into a Google Doc.
#
# Inline images in Google Docs must be inserted by URI from a host Google's
# servers can fetch, so the flow is: upload each page PNG to Drive -> make it
# readable by link -> insertInlineImage by that URI. Auth reuses the
# @googleworkspace/cli OAuth already wired into this project (docs + drive
# scopes), the same path app/agent.py's exporter uses.
#
# The fiddly, breakable part is the Docs batchUpdate index math, so it is split
# out into build_doc_requests() — a pure, deterministic function (no network)
# that is fully unit-tested. The CLI calls are a thin wrapper around it.
#
# Two fonts only (per brand): OpenDyslexic for everything the child reads,
# Poppins for the title/labels. Docs may not have OpenDyslexic installed; we
# still request it via weightedFontFamily and Docs falls back gracefully — the
# brand's "embed-or-fallback" requirement.
# =============================================================================

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass

# Child-facing story text font; Docs falls back if OpenDyslexic isn't installed.
BODY_FONT = "OpenDyslexic"
# Title / label font (a standard Google Font, always available in Docs).
LABEL_FONT = "Poppins"
# Default rendered width for a page illustration, in points.
IMAGE_WIDTH_PT = 360.0
# 1:1 cut-paper pages by default (square); callers can override per page.
IMAGE_HEIGHT_PT = 360.0

# The Google Workspace CLI invocation. Prefer the `gws` binary the user
# authenticated via `gws auth login` (on PATH); a pinned npx build is only a
# fallback when none is installed. NOTE: the previously-pinned 0.7.0 cannot
# decrypt credentials written by a newer gws (a 401 "decryption failed"), so
# PATH-first keeps doc export aligned with whatever version actually holds the
# OAuth. Override the binary with PHONO_GWS_BIN.
_GWS_BIN = os.environ.get("PHONO_GWS_BIN") or shutil.which("gws")
_GWS = [_GWS_BIN] if _GWS_BIN else ["npx", "-y", "@googleworkspace/cli@0.7.0"]


def gws_base_command() -> list[str]:
    """The PATH-first `gws` invocation shared by every deterministic CLI call.

    Prefers the authenticated `gws` on PATH (or ``PHONO_GWS_BIN``); only falls
    back to a pinned ``npx @googleworkspace/cli@0.7.0`` build when none is
    installed. See the module header for why PATH-first: 0.7.0 cannot decrypt
    credentials written by a newer gws (a 401 "decryption failed").

    NOTE: the ADK MCP-server path in app/agent.py deliberately does NOT use this
    resolver — it must stay pinned to 0.7.0 because newer gws removed MCP server
    mode. Only the deterministic, one-shot CLI calls (Docs/Drive export here, and
    the Gmail-draft subprocess in agent.py) are PATH-first.
    """
    return list(_GWS)


@dataclass
class DocPage:
    """One page to lay into the Doc: story text + a fetchable image URI."""

    text: str
    image_uri: str
    width_pt: float = IMAGE_WIDTH_PT
    height_pt: float = IMAGE_HEIGHT_PT


def build_doc_requests(
    title: str,
    pages: list[DocPage],
    *,
    body_font: str = BODY_FONT,
    label_font: str = LABEL_FONT,
) -> list[dict]:
    """Builds an ordered Google Docs batchUpdate request list (pure, deterministic).

    Requests are emitted in application order with a running insertion index, so
    each insert's absolute index already accounts for every earlier insert. Text
    indices are UTF-16 code units; the decodable story text is plain ASCII-range
    English, so len() matches. An inline image occupies exactly one index unit.

    Layout: a HEADING_1 title (Poppins) cover page, then EACH story page on its
    own physical page — its text (OpenDyslexic) followed by its illustration. The
    per-page page break is load-bearing: the illustrations are ~360pt (half a
    page) tall, so without a hard break the paginated/printed Doc pushes each
    image onto the *next* page's text, making every picture show the wrong (prior)
    scene. The break pins the rendered pairing to text[i] <-> image[i].
    """
    requests: list[dict] = []
    index = 1  # first insertable index in a freshly created doc

    def insert_text(text: str) -> tuple[int, int]:
        nonlocal index
        start = index
        requests.append(
            {"insertText": {"location": {"index": start}, "text": text}}
        )
        index += len(text)
        return start, index  # [start, end)

    def insert_page_break() -> None:
        nonlocal index
        requests.append({"insertPageBreak": {"location": {"index": index}}})
        index += 1  # a page break occupies exactly one index unit

    def style_text(start: int, end: int, font: str, *, bold: bool = False) -> None:
        fields = "weightedFontFamily"
        text_style: dict = {"weightedFontFamily": {"fontFamily": font}}
        if bold:
            text_style["bold"] = True
            fields += ",bold"
        requests.append(
            {
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "textStyle": text_style,
                    "fields": fields,
                }
            }
        )

    def style_paragraph(start: int, end: int, named_style: str) -> None:
        requests.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": {"namedStyleType": named_style},
                    "fields": "namedStyleType",
                }
            }
        )

    # --- Title ---
    t_start, t_end = insert_text(title + "\n")
    style_paragraph(t_start, t_end, "HEADING_1")
    style_text(t_start, t_end - 1, label_font, bold=True)

    # --- Pages ---
    for page in pages:
        # Start every story page on its own physical page so its text and its
        # illustration stay together (see docstring — prevents the off-by-one
        # where an image drifts onto the following page's text).
        insert_page_break()
        text = page.text.strip()
        if text:
            p_start, p_end = insert_text(text + "\n")
            style_paragraph(p_start, p_end, "NORMAL_TEXT")
            style_text(p_start, p_end - 1, body_font)
        # Inline image on its own line (occupies one index unit).
        requests.append(
            {
                "insertInlineImage": {
                    "location": {"index": index},
                    "uri": page.image_uri,
                    "objectSize": {
                        "width": {"magnitude": page.width_pt, "unit": "PT"},
                        "height": {"magnitude": page.height_pt, "unit": "PT"},
                    },
                }
            }
        )
        index += 1
        insert_text("\n")

    return requests


# ---------------------------------------------------------------------------
# Thin Workspace-CLI wrappers (integration path; auth = @googleworkspace/cli).
# ---------------------------------------------------------------------------
def _run_gws(args: list[str], *, upload: str | None = None) -> dict:
    """Runs a Workspace CLI command and returns parsed JSON (raises on failure)."""
    cmd = gws_base_command() + args
    # @googleworkspace/cli >=0.7.0 sandboxes --upload to paths inside the current
    # working directory and rejects anything outside it (the page PNGs live in a
    # tempfile.TemporaryDirectory). Run the upload from the file's own directory
    # and pass just the basename so the sandbox check passes.
    cwd = None
    if upload:
        upload_abs = os.path.abspath(upload)
        cwd = os.path.dirname(upload_abs)
        cmd += ["--upload", os.path.basename(upload_abs)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Workspace CLI failed: {' '.join(args)}\n{result.stderr}")
    out = result.stdout.strip()
    return json.loads(out) if out else {}


def upload_image_to_drive(path: str, name: str, *, folder_id: str | None = None) -> str:
    """Uploads a local PNG to Drive and returns its file id."""
    body: dict = {"name": name, "mimeType": "image/png"}
    if folder_id:
        body["parents"] = [folder_id]
    data = _run_gws(
        ["drive", "files", "create", "--json", json.dumps(body)], upload=path
    )
    return data["id"]


def make_drive_file_public(file_id: str) -> None:
    """Grants anyone-with-link read access so Docs servers can fetch the image."""
    _run_gws(
        [
            "drive",
            "permissions",
            "create",
            "--params",
            json.dumps({"fileId": file_id}),
            "--json",
            json.dumps({"type": "anyone", "role": "reader"}),
        ]
    )


def drive_image_uri(file_id: str) -> str:
    """A direct-content URI for a public Drive image that Docs can fetch."""
    return f"https://lh3.googleusercontent.com/d/{file_id}"


def create_doc(title: str) -> str:
    """Creates an empty Google Doc and returns its document id."""
    data = _run_gws(["docs", "documents", "create", "--json", json.dumps({"title": title})])
    return data["documentId"]


def apply_doc_requests(doc_id: str, requests: list[dict]) -> None:
    """Applies a batchUpdate request list to a document."""
    _run_gws(
        [
            "docs",
            "documents",
            "batchUpdate",
            "--params",
            json.dumps({"documentId": doc_id}),
            "--json",
            json.dumps({"requests": requests}),
        ]
    )


def doc_url(doc_id: str) -> str:
    return f"https://docs.google.com/document/d/{doc_id}/edit"
