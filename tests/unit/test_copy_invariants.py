# tests/unit/test_copy_invariants.py
#
# =============================================================================
# REDESIGN INVARIANTS (Phase 7, PR3) — the non-negotiables of design-system.md
# encoded as tests so a future change can't silently re-introduce shame mechanics
# or clinical jargon into surfaces a child or a frightened parent sees.
#
# Two guards:
#   1. The child-facing payload (book title + words a child reads) and the static
#      Reading-face / top-bar chrome copy contain NONE of the forbidden lexicon.
#   2. The persistent chrome exposes no accuracy/percentage/score (effort, never
#      accuracy — design-system §1/§10).
#
# Scope note: the adult "For grown-ups" view and the planner's internal rationale
# are deliberately EXEMPT (see docs/voice-lexicon.md). These guards protect the
# child surface and the always-visible chrome only.
# =============================================================================

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.store.learner_store import JSONLearnerStore
from app.store.session_log import JSONLSessionLogStore
from app.tutor.session import TutorSession
from app.web.viz import prepared_payload

# Words that must never reach a child or the persistent chrome. Matched as
# whole-words, case-insensitive, so ordinary story text ("a cat") is unaffected.
FORBIDDEN = [
    "mastery", "mastered", "grapheme", "wcpm", "accuracy",
    "bkt", "zpd", "decodab", "objective", "closed-loop", "p(l)",
]

INDEX_HTML = Path("app/web/static/index.html")


def _contains_forbidden(text: str) -> list[str]:
    low = text.lower()
    hits = []
    for term in FORBIDDEN:
        # "decodab" is a stem; the rest match on word-ish boundaries.
        pattern = re.escape(term) if term.endswith(("ab",)) else r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, low):
            hits.append(term)
    return hits


def _strip_comments(html: str) -> str:
    # HTML comments are not user-facing; the engineering notes in them legitimately
    # reference the technical terms these guards forbid in *visible* copy.
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def _slice(html: str, start_marker: str, end_marker: str) -> str:
    i = html.index(start_marker)
    j = html.index(end_marker, i)
    return _strip_comments(html[i:j])


@pytest.fixture
def tutor(tmp_path):
    store = JSONLearnerStore(tmp_path / "profiles")
    log_store = JSONLSessionLogStore(tmp_path / "sessions")
    return TutorSession(store, log_store=log_store)


# ---- Guard 1: child-facing READING CONTENT is jargon-free -------------------

@pytest.mark.parametrize(
    "learner,age,interest",
    [("ada", 6, "dinosaurs"), ("sam", 5, "space"), ("mia", 7, "the sea")],
)
def test_child_facing_book_content_has_no_jargon(tutor, learner, age, interest):
    prepared = tutor.prepare(learner, name=learner.title(), age=age, interest=interest)
    payload = prepared_payload(prepared)
    title = payload["book"]["title"]
    words = " ".join(payload["book"]["words"])
    for field, value in (("title", title), ("words", words)):
        hits = _contains_forbidden(value)
        assert not hits, f"forbidden lexicon {hits} in child-facing book {field}: {value!r}"


# ---- Guard 2: the Reading face (static copy) is jargon-free -----------------

def test_reading_face_copy_has_no_jargon():
    html = INDEX_HTML.read_text(encoding="utf-8")
    # The child's reading region runs from #reading-face up to #insight-face.
    reading = _slice(html, 'id="reading-face"', 'id="insight-face"')
    hits = _contains_forbidden(reading)
    assert not hits, f"forbidden lexicon {hits} in the child's Reading face"


# ---- Guard 3: persistent chrome shows no accuracy/score ---------------------

def test_topbar_chrome_exposes_no_score():
    html = INDEX_HTML.read_text(encoding="utf-8")
    topbar = _slice(html, '<header class="topbar">', "</header>")
    # No accuracy/mastery framing and no numeric percent gauge in the always-on chrome.
    assert "mastery" not in topbar.lower(), "top-bar must not show a 'Mastery' readout"
    assert "%" not in topbar, "top-bar must not expose a percentage/score"
    assert _contains_forbidden(topbar) == [], "top-bar chrome must be jargon-free"
