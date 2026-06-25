# app/voice/transcriber.py
#
# =============================================================================
# FLAGSHIP STAGE B (Part 2): the Transcriber seam.
#
# A Transcriber turns one page's read-aloud into exactly what record_read wants:
#
#     transcribe(expected_words) -> (spoken_tokens, duration_seconds)
#
# That is the whole contract. TutorSession is untouched; the voice CLI just does
# `tokens, dur = transcriber.transcribe(page_words)` then
# `record_read(prepared, tokens, duration_seconds=dur)`.
#
# Two implementations:
#   - FakeTranscriber: returns scripted tokens/duration; used by the unit tests
#     and any offline demo, so nothing here needs a mic or the network.
#   - LiveTranscriber: streams mic audio to Gemini Live with input transcription
#     enabled, biases recognition toward the page's expected words, and applies
#     the low-confidence repair so the recognizer never punishes the child.
#
# The genai Live client, asyncio, and the microphone library are all imported
# lazily inside LiveTranscriber so importing this module stays free of audio/
# network deps and the offline suite is unaffected.
# =============================================================================

from __future__ import annotations

from typing import Protocol

from app.voice.confidence import DEFAULT_CONFIDENCE_THRESHOLD, repair_low_confidence

# Live model ids are pinned here so model churn is a one-line change. The right
# id depends on the backend, because the two surfaces expose different models:
#
#   * Developer API (GOOGLE_GENAI_USE_VERTEXAI=0, API key): the lighter half-cascade
#     `gemini-live-2.5-flash` does streaming input transcription with TEXT output —
#     exactly what STT wants (no spoken response), lower latency and cost.
#   * Vertex AI (GOOGLE_GENAI_USE_VERTEXAI=1, ADC): only the native-audio Live model
#     is GA, and it REJECTS TEXT output — it must run with AUDIO output. We still
#     read only the input transcription (what the child said), so the spoken audio
#     it generates is simply ignored. This is the path that works without an API
#     key (the new AQ. auth keys currently 401 on the Developer API).
#
# Do NOT pin the dated preview id (`...-preview-native-audio-09-2025`); it is being
# removed 2026-03-19.
LIVE_MODEL = "gemini-live-2.5-flash"                       # Developer API (TEXT out)
VERTEX_LIVE_MODEL = "gemini-live-2.5-flash-native-audio"   # Vertex AI (AUDIO out)

# Live expects 16-bit PCM mono; 16 kHz is the standard input rate.
INPUT_SAMPLE_RATE = 16000


class Transcriber(Protocol):
    """Produces (spoken_tokens, duration_seconds) for one page read-aloud."""

    def transcribe(self, expected_words: list[str]) -> tuple[list[str], float]: ...


class FakeTranscriber:
    """Deterministic Transcriber for tests/offline demos — no audio, no network.

    Returns the configured tokens and duration. If `confidences` is supplied it
    runs the same low-confidence repair the Live path uses, so tests can prove
    the never-punish behavior end to end against the expected words.
    """

    def __init__(
        self,
        tokens: list[str],
        duration_seconds: float,
        *,
        confidences: list[float] | None = None,
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> None:
        self._tokens = list(tokens)
        self._duration = float(duration_seconds)
        self._confidences = confidences
        self._threshold = threshold

    def transcribe(self, expected_words: list[str]) -> tuple[list[str], float]:
        if self._confidences is not None:
            tokens = repair_low_confidence(
                expected_words,
                self._tokens,
                self._confidences,
                threshold=self._threshold,
            )
        else:
            tokens = list(self._tokens)
        return tokens, self._duration


def _bias_instruction(expected_words: list[str]) -> str:
    """System instruction that biases Live recognition toward the page text."""
    expected = " ".join(expected_words)
    return (
        "A young child is reading the following text aloud, word by word:\n"
        f'"{expected}"\n'
        "Transcribe exactly what the child says, in order. Expect the words "
        "above; prefer them when the audio is ambiguous. Do not correct, "
        "complete, or add words the child did not say."
    )


class LiveTranscriber:
    """Gemini Live transcriber: streams mic audio -> word-level transcript.

    Args:
        client: a google-genai client (built lazily if None).
        model: the Live model id (defaults to the pinned LIVE_MODEL).
        audio_source: an iterable/async-iterable of raw 16-bit PCM mono chunks
            for one read (built from the microphone if None).
        language_code: ASR language hint passed to input transcription.
        confidence_threshold: forwarded to the low-confidence repair.

    transcribe() opens a session, enables input transcription, streams the audio
    while collecting the transcript, then discards the audio and returns the
    repaired tokens plus the duration measured from the audio length.

    NOTE: this path requires a microphone, network, and Live quota, so it is kept
    out of the default test suite (the free tier 429s). It is exercised manually
    via scripts/tutor_voice_cli.py.
    """

    def __init__(
        self,
        *,
        client=None,
        model: str | None = None,
        audio_source=None,
        language_code: str = "en-US",
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        sample_rate: int = INPUT_SAMPLE_RATE,
    ) -> None:
        self._client = client
        # None => auto-select the model for the active backend at connect time
        # (Vertex needs the native-audio id; the Developer API uses the half-cascade).
        self._model = model
        self._audio_source = audio_source
        self._language_code = language_code
        self._threshold = confidence_threshold
        self._sample_rate = sample_rate

    @staticmethod
    def _vertex_enabled() -> bool:
        """True when the env selects the Vertex backend (flag set + project present).

        Vertex authenticates with ADC (gcloud) instead of an API key, which is the
        working path while the Developer API's new AQ. auth keys 401.
        """
        import os

        return (
            os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "0") == "1"
            and bool(os.environ.get("GOOGLE_CLOUD_PROJECT"))
        )

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        import os

        from google import genai
        from google.genai import types

        if self._vertex_enabled():
            # Vertex Live speaks v1beta1; the Developer API path uses v1beta.
            project = os.environ.get("GOOGLE_CLOUD_PROJECT")
            location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
            self._client = genai.Client(
                vertexai=True,
                project=project,
                location=location,
                http_options=types.HttpOptions(api_version="v1beta1"),
            )
        else:
            self._client = genai.Client(http_options=types.HttpOptions(api_version="v1beta"))
        return self._client

    def transcribe(self, expected_words: list[str]) -> tuple[list[str], float]:
        import asyncio

        return asyncio.run(self._transcribe_async(expected_words))

    async def _transcribe_async(
        self, expected_words: list[str]
    ) -> tuple[list[str], float]:
        from google.genai import types

        client = self._ensure_client()
        is_vertex = self._vertex_enabled()
        # Vertex's only GA Live model is native-audio, which requires AUDIO output;
        # the Developer API's half-cascade model gives TEXT. Either way we read only
        # the input transcription, so any spoken audio the native model emits is
        # ignored. Model id is auto-selected per backend unless one was injected.
        model = self._model or (VERTEX_LIVE_MODEL if is_vertex else LIVE_MODEL)
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"] if is_vertex else ["TEXT"],
            input_audio_transcription=types.AudioTranscriptionConfig(),
            system_instruction=_bias_instruction(expected_words),
        )

        source = self._audio_source
        if source is None:
            source = microphone_chunks(sample_rate=self._sample_rate)

        transcript_parts: list[str] = []
        total_bytes = 0
        async with client.aio.live.connect(model=model, config=config) as session:
            # Stream audio; the SDK accepts a sync or async iterable of chunks.
            if hasattr(source, "__aiter__"):
                async for chunk in source:
                    total_bytes += len(chunk)
                    await session.send_realtime_input(
                        audio=types.Blob(
                            data=chunk, mime_type=f"audio/pcm;rate={self._sample_rate}"
                        )
                    )
            else:
                for chunk in source:
                    total_bytes += len(chunk)
                    await session.send_realtime_input(
                        audio=types.Blob(
                            data=chunk, mime_type=f"audio/pcm;rate={self._sample_rate}"
                        )
                    )
            await session.send_realtime_input(audio_stream_end=True)

            async for message in session.receive():
                sc = getattr(message, "server_content", None)
                if sc is not None:
                    it = getattr(sc, "input_transcription", None)
                    if it is not None and getattr(it, "text", None):
                        transcript_parts.append(it.text)
                    if getattr(sc, "turn_complete", False):
                        break

        # Raw audio is never retained — only the derived transcript + duration.
        text = "".join(transcript_parts)
        tokens = text.split()
        # No per-word confidence from Live transcription today: trust the
        # transcript (repair becomes a safe no-op). The hook stays here so a
        # future confidence signal flips on the never-punish behavior for free.
        tokens = repair_low_confidence(
            expected_words, tokens, confidences=None, threshold=self._threshold
        )
        duration = total_bytes / (self._sample_rate * 2) if total_bytes else 0.0
        return tokens, duration


def microphone_chunks(
    *, sample_rate: int = INPUT_SAMPLE_RATE, block_ms: int = 100, silence_stop_s: float = 2.5
):
    """Yields raw 16-bit PCM mono chunks from the default microphone until a
    short trailing silence ends the utterance.

    Lazy-imports `sounddevice`/`numpy` so the dependency is only required when
    voice capture actually runs (the offline suite never reaches here).
    """
    import numpy as np  # type: ignore
    import sounddevice as sd  # type: ignore

    block = int(sample_rate * block_ms / 1000)
    silence_blocks = int(silence_stop_s * 1000 / block_ms)
    quiet = 0
    started = False
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
        while True:
            data, _ = stream.read(block)
            pcm = data[:, 0]
            yield pcm.tobytes()
            loud = bool(np.abs(pcm).mean() > 200)
            started = started or loud
            quiet = 0 if loud else quiet + 1
            if started and quiet >= silence_blocks:
                break
