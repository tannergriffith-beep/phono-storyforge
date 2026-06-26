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
  // Advance the rail to Assess immediately (the typed path has no inbound echo
  // before the outcome arrives); the outcome handler then closes it on Adapt.
  LoopRail.beginAssess();
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

// LoopRail registers its own ws subscriptions (prepared/voice_status/outcome/error).
LoopRail.mount($("loop-rail"));
// WhyCard renders the planner rationale + evidence chips on each `prepared`.
WhyCard.mount();
// MasteryPath renders the phonics path on `prepared` and animates it on `outcome`.
MasteryPath.mount();

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
