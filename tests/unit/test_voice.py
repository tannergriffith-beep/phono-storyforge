# tests/unit/test_voice.py
#
# =============================================================================
# FLAGSHIP STAGE B (Part 2): unit tests for the voice read-aloud layer.
#
# All offline, no mic, no network: the Live client is never touched. We prove
#   - low-confidence ASR is repaired to the expected word (never punish), while
#     a CONFIDENT wrong word survives as a real miscue,
#   - scaffolding localizes the exact failed grapheme via decompose(),
#   - echo/karaoke produces a sane repeat-after-me script,
#   - a FakeTranscriber drops straight into the unchanged record_read(), and
#   - importing app.voice does NOT drag in google-genai / audio deps.
# =============================================================================

from __future__ import annotations

import sys

import pytest

from app.schemas import Miscue
from app.store.learner_store import JSONLearnerStore
from app.store.session_log import JSONLSessionLogStore
from app.tutor.session import TutorSession
from app.voice.confidence import repair_low_confidence
from app.voice.scaffold import echo_sequence, scaffold_for_miscue
from app.voice.transcriber import FakeTranscriber


# ---------------------------------------------------------------------------
# Low-confidence repair (never punish the child for the recognizer's doubt)
# ---------------------------------------------------------------------------


def test_perfect_read_is_unchanged() -> None:
    expected = ["the", "big", "cat"]
    out = repair_low_confidence(expected, ["the", "big", "cat"], [0.9, 0.9, 0.9])
    assert out == ["the", "big", "cat"]


def test_low_confidence_substitution_snaps_to_expected() -> None:
    # The ASR was unsure (0.2) about the last word -> give the child the benefit
    # of the doubt and trust the page.
    out = repair_low_confidence(
        "the big cat", ["the", "big", "kat"], [0.9, 0.9, 0.2]
    )
    assert out == ["the", "big", "cat"]


def test_confident_substitution_is_kept_as_a_real_miscue() -> None:
    # A CONFIDENT mishearing-shaped token is a genuine reading miscue; keep it so
    # the tutor can catch and reteach it.
    out = repair_low_confidence(
        "the big cat", ["the", "big", "kat"], [0.9, 0.9, 0.95]
    )
    assert out == ["the", "big", "kat"]


def test_no_confidence_signal_trusts_the_transcript() -> None:
    out = repair_low_confidence("the big cat", ["the", "big", "kat"], None)
    assert out == ["the", "big", "kat"]


def test_insertions_and_omissions_survive_repair() -> None:
    # Child added "um" and dropped "cat"; low-conf only on the insertion.
    out = repair_low_confidence(
        "the big cat", ["the", "um", "big"], [0.9, 0.2, 0.9]
    )
    assert out == ["the", "um", "big"]


# ---------------------------------------------------------------------------
# Grapheme-targeted scaffolding
# ---------------------------------------------------------------------------


def test_scaffold_localizes_the_failed_digraph() -> None:
    cue = scaffold_for_miscue(
        Miscue(kind="substitution", expected="ship", spoken="sip", position=0)
    )
    assert cue is not None
    assert cue.grapheme == "sh"
    assert cue.level == "digraphs"
    assert "ship" in cue.prompt and "sh" in cue.prompt


def test_scaffold_handles_omission_on_first_grapheme() -> None:
    cue = scaffold_for_miscue(
        Miscue(kind="omission", expected="ship", spoken=None, position=0)
    )
    assert cue is not None
    assert cue.grapheme == "sh"


def test_scaffold_ignores_non_actionable_miscues() -> None:
    assert scaffold_for_miscue(
        Miscue(kind="insertion", expected=None, spoken="extra", position=0)
    ) is None
    assert scaffold_for_miscue(
        Miscue(kind="self_correction", expected="cat", spoken="cat", position=0)
    ) is None


def test_echo_sequence_builds_repeat_then_whole_line() -> None:
    steps = echo_sequence(["A", "cat", "sat."])
    assert [s.word for s in steps[:3]] == ["a", "cat", "sat"]
    # Final step reads the whole line back.
    assert steps[-1].model_says == "a cat sat"
    assert len(steps) == 4


# ---------------------------------------------------------------------------
# FakeTranscriber drops straight into record_read (TutorSession unchanged)
# ---------------------------------------------------------------------------


@pytest.fixture
def tutor(tmp_path):
    store = JSONLearnerStore(tmp_path / "profiles")
    log_store = JSONLSessionLogStore(tmp_path / "sessions")
    return TutorSession(store, log_store=log_store)


def test_voice_transcript_feeds_record_read_with_real_duration(tutor) -> None:
    prepared = tutor.prepare("kid")
    transcriber = FakeTranscriber(prepared.book.words, duration_seconds=20.0)

    tokens, duration = transcriber.transcribe(prepared.book.words)
    outcome = tutor.record_read(prepared, tokens, duration_seconds=duration)

    assert outcome.assessment.accuracy == pytest.approx(1.0)
    # The measured voice duration is used directly (not the typed estimate).
    assert outcome.assessment.duration_seconds == pytest.approx(20.0)


def test_low_confidence_token_does_not_punish_through_the_session(tutor) -> None:
    prepared = tutor.prepare("kid")
    words = prepared.book.words

    # Mangle the first content word but mark it low-confidence -> should be
    # repaired to a perfect read rather than scored as a miscue.
    spoken = ["xqz"] + words[1:]
    confidences = [0.1] + [0.95] * (len(words) - 1)
    transcriber = FakeTranscriber(spoken, duration_seconds=18.0, confidences=confidences)

    tokens, duration = transcriber.transcribe(words)
    outcome = tutor.record_read(prepared, tokens, duration_seconds=duration)

    assert outcome.assessment.accuracy == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Laziness: importing the voice layer must not pull in audio/Live deps
# ---------------------------------------------------------------------------


def test_importing_voice_does_not_import_live_or_audio_stack() -> None:
    # google.genai/numpy may already be imported elsewhere in the suite, so we
    # assert the microphone library stays out until voice capture actually runs.
    import app.voice.transcriber  # noqa: F401

    assert "sounddevice" not in sys.modules
