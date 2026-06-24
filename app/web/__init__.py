# app/web/
#
# =============================================================================
# FLAGSHIP STAGE C: the filmable web read-along + live mastery viz.
#
# A child reads a page in the browser; a miscue heatmap lights up per word,
# mastery bars animate as BKT updates, and tomorrow's target visibly shifts on
# screen. This package DRIVES the real closed loop (app/tutor) over a WebSocket
# — it never fakes the numbers.
#
# Three layers, isolated so the web deps never leak into the offline path:
#   - viz.py    : PURE mapping from PreparedSession / SessionOutcome to the
#                 JSON payloads the UI animates from. No FastAPI, no eval, no
#                 audio. This is the unit-tested surface.
#   - server.py : a thin FastAPI app + one WebSocket endpoint. I/O only: it
#                 calls TutorSession.prepare/record_read unchanged and ships the
#                 viz payloads. The only module that imports FastAPI.
#   - static/   : one HTML page + vanilla JS (CSS-transition animations, no
#                 charting lib, no framework).
#
# The brain layer (planner, alignment, BKT, store) is reused UNCHANGED; the web
# layer adds zero new logic beyond serialization. Browser-mic voice (Stage C
# step 2) plugs into the existing app/voice Transcriber seam additively, so the
# typed path here always works on its own.
# =============================================================================
