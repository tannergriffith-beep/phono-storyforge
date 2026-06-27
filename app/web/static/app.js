// app/web/static/app.js
//
// FLAGSHIP STAGE C: boot module. Wires the vanilla-JS modules together and
// drives the real closed loop over one socket. No framework, no charting lib —
// animations are CSS transitions triggered by the component modules.
//
// Architecture (DESIGN §9, ES modules):
//   dom.js      — DOM + format helpers
//   state.js    — shared per-connection UI state
//   ws.js       — the socket + a type-keyed pub/sub (on/send/sendBinary)
//   voice.js    — browser mic -> PCM frames (Stage B, additive)
//   book.js     — illustrated take-home book (opt-in coda)
//   render.js   — legacy single-screen renderers (kept functional)
//   components/loopRail.js — the persistent Loop rail (DESIGN §4)
//
// This module owns only the message<->handler registrations and the button
// wiring; each concern lives in its own module.

"use strict";

import { $ } from "./dom.js";
import { state } from "./state.js";
import * as ws from "./ws.js";
import * as voice from "./voice.js";
import * as book from "./book.js";
import { renderPrepared, renderOutcome, applyPreset } from "./render.js";
import { LoopRail } from "./components/loopRail.js";
import { WhyCard } from "./components/whyCard.js";
import { MasteryPath } from "./components/masteryPath.js";
import { ModeToggle } from "./components/modeToggle.js";
import { AdaptBeat } from "./components/adaptBeat.js";
import { Journey } from "./components/journey.js";
import { DegradeBanner } from "./components/degradeBanner.js";
import { ReaderSettings } from "./components/readerSettings.js";
import { Onboarding } from "./components/onboarding.js";
import { SessionArc } from "./components/sessionArc.js";

// The technical loop is opt-in (educators/demos); parents see the human arc.
const showLoopInternals = (() => {
  try {
    return localStorage.getItem("phono.devLoop") === "1" || /[?&]loop\b/.test(location.search);
  } catch { return false; }
})();

// ---- Actions ----------------------------------------------------------------

function startSession() {
  ws.send({
    action: "prepare",
    learner_id: $("learner-id").value.trim() || "ada",
    name: $("learner-name").value.trim(),
    age: parseInt($("learner-age").value, 10) || 6,
    interest: $("learner-interest").value.trim(),
  });
}

function scoreRead() {
  // Advance both the human arc and (if shown) the technical rail immediately —
  // the typed path has no inbound echo before the outcome arrives.
  SessionArc.beginScore();
  if (showLoopInternals) LoopRail.beginAssess();
  ws.send({ action: "submit", transcript: $("transcript").value.trim() });
}

// ---- Inbound message routing (ws.on by type) --------------------------------

ws.on("capabilities", (m) => { state.illustratedEnabled = !!m.illustrated_enabled; });
ws.on("prepared", renderPrepared);
ws.on("outcome", renderOutcome);
ws.on("voice_status", (m) => voice.voiceStatus(m.message));
ws.on("book_progress", (m) => book.bookProgress(m.message));
ws.on("book_ready", book.renderBookReady);
ws.on("error", (m) => {
  ws.setStatus(m.message, "err");
  voice.voiceStatus(m.message);
  book.bookProgress(m.message);
  book.endBookGen();
});

// SessionArc: the parent-facing "where we are tonight" (always on).
SessionArc.mount($("session-arc"));
// LoopRail: the technical six-node loop — opt-in only (educators/demos).
if (showLoopInternals) {
  $("loop-rail").hidden = false;
  LoopRail.mount($("loop-rail"));
}
// WhyCard renders the planner rationale + evidence chips on each `prepared`.
WhyCard.mount();
// MasteryPath renders the phonics path on `prepared` and animates it on `outcome`.
MasteryPath.mount();
// ModeToggle owns the Read ⇄ Insight view-switch + the privacy boundary.
ModeToggle.mount();
// AdaptBeat choreographs the climax on `outcome` (deferred until Insight is open).
AdaptBeat.mount();
// Journey: the cross-session "loop, not generator" proof (reads persisted logs).
Journey.mount();
// DegradeBanner: the single graceful-degradation surface (DESIGN §9). Mount
// before connect() so it catches the very first connection signal.
DegradeBanner.mount();
// ReaderSettings: type/size/spacing/calm controls — applies persisted prefs on load.
ReaderSettings.mount();
// Onboarding: the warm on-ramp; fills the hidden setup fields then starts the session.
Onboarding.mount({ onStart: startSession });

// ---- Button wiring ----------------------------------------------------------

$("start-btn").addEventListener("click", startSession);
$("score-btn").addEventListener("click", scoreRead);
$("next-btn").addEventListener("click", startSession);
$("mic-btn").addEventListener("click", voice.toggleMic);
$("gen-book-btn").addEventListener("click", book.generateBook);
document.querySelectorAll(".presets [data-preset]").forEach((btn) =>
  btn.addEventListener("click", () => applyPreset(btn.dataset.preset))
);

ws.connect();
