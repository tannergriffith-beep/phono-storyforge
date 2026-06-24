# app/voice/
#
# =============================================================================
# FLAGSHIP STAGE B (Part 2): Gemini Live voice read-aloud.
#
# This package turns a child reading aloud into exactly what the existing
# TutorSession.record_read(prepared, spoken, duration_seconds=...) already
# consumes — a spoken token list plus a real measured duration — WITHOUT
# changing the alignment/assessment logic in app/skills/alignment.py.
#
#   mic audio --> Transcriber (Gemini Live) --> (tokens, duration_seconds)
#                                                      |
#                          record_read(prepared, tokens, duration_seconds=...)
#
# Three pieces, each independently unit-testable offline:
#   - transcriber.py : the Transcriber seam (Live-backed + a fake for tests).
#   - confidence.py  : map low-confidence ASR to the expected word so the
#                      recognizer never PUNISHES the child for its own
#                      uncertainty (treated as a non-error, like a hesitation).
#   - scaffold.py    : decompose()-localized grapheme cues + echo/karaoke mode.
#
# Privacy: raw child audio is streamed and discarded; only the derived
# transcript (tokens) + duration leave this layer and get persisted via the
# normal mastery/log path. No audio is written to disk.
#
# Everything that needs the network, a microphone, or the google-genai Live
# client is lazy-imported so importing this package stays cheap and the offline
# unit suite never touches audio/Live.
# =============================================================================
