// app/web/static/render.js
//
// Legacy single-screen renderers (the current Stage C surface). Behavior is
// preserved verbatim from the original app.js; only the wiring moved to modules.
// Phase 2's later screens (MasteryPath, Read⇄Insight split, Adapt beat) will
// replace pieces of renderOutcome/renderBars — for now they keep the working
// demo intact while the LoopRail lands on top.

"use strict";

import { $, pct, stat } from "./dom.js";
import { state } from "./state.js";
import { voiceStatus } from "./voice.js";
import { endBookGen, bookProgress } from "./book.js";

// ---- Render: prepared -------------------------------------------------------

export function renderPrepared(msg) {
  $("setup").hidden = false;
  $("session").hidden = false;
  $("results").hidden = true;
  $("transcript").value = "";
  voiceStatus("");

  $("session-pill").textContent = `session #${msg.session_index}`;
  $("target-grapheme").textContent = `/${msg.objective.target_grapheme}/`;
  $("target-level").textContent = msg.objective.target_level;
  // The planner rationale is now rendered by the WhyCard component (#why-card).

  // Reset + reveal the take-home book panel (only when the feature is enabled).
  state.learnerName = msg.learner_name || "";
  const bookGen = $("book-gen");
  bookGen.hidden = !state.illustratedEnabled;
  if (state.illustratedEnabled) {
    $("book-gen-name").textContent = state.learnerName || "this learner";
    $("book-result").hidden = true;
    bookProgress("");
    endBookGen();
  }

  state.words = msg.book.words;
  state.targetPositions = msg.book.target_word_positions || [];

  $("book-title").textContent = msg.book.title || "Practice page";
  $("book-source").textContent = msg.book.generation_source;
  const text = $("book-text");
  text.innerHTML = "";
  msg.book.words.forEach((w, i) => {
    const span = document.createElement("span");
    span.className = "w";
    span.dataset.position = i;
    span.textContent = w;
    text.appendChild(span);
    text.appendChild(document.createTextNode(" "));
  });

  // The mastery sidebar is now the MasteryPath component (masteryPath.js),
  // which subscribes to `prepared`/`outcome` directly.
  setMean(msg.mean_mastery);
}

// ---- Render: outcome --------------------------------------------------------

export function renderOutcome(msg) {
  // If this read came from voice, show what was heard; otherwise clear status.
  voiceStatus(msg.heard ? "heard: " + msg.heard.join(" ") : "");

  // Miscue heatmap: color each expected word by its running-record kind.
  const spans = $("book-text").querySelectorAll(".w");
  msg.heatmap.forEach((cell) => {
    const span = spans[cell.position];
    if (!span) return;
    span.classList.add(cell.kind);
    if (cell.spoken) span.title = `heard: ${cell.spoken}`;
  });

  // Mastery updates are animated by the MasteryPath component (masteryPath.js).
  setMean(msg.mean_mastery);

  // Fluency readout.
  const f = msg.fluency;
  $("fluency").innerHTML = [
    stat(Math.round(f.accuracy * 100) + "%", "accuracy"),
    stat(Math.round(f.wcpm), "wcpm"),
    stat(`${f.words_correct}/${f.total_words}`, "correct"),
    stat(f.errors, "errors"),
  ].join("");

  // Grapheme-targeted scaffolds for each miss.
  const sc = $("scaffolds");
  sc.innerHTML = "";
  msg.scaffolds.forEach((s) => {
    const div = document.createElement("div");
    div.className = "scaffold";
    div.innerHTML = `<b>/${s.grapheme}/</b> in “${s.word}” — ${s.prompt}`;
    sc.appendChild(div);
  });

  // Next target — highlight when the loop advanced.
  const nt = msg.next_target;
  const box = $("next-target");
  box.className = "next-target" + (nt.advanced ? " advanced" : "");
  box.innerHTML =
    `<h4>Tomorrow's target</h4>` +
    `<div>Next session will target <span class="next-g">/${nt.target_grapheme}/</span> ` +
    `<span class="muted">(${nt.target_level})</span></div>` +
    (nt.advanced
      ? `<div class="adv-badge">↳ the target ADVANCED from /${nt.previous_grapheme}/ — the loop adapted.</div>`
      : `<div class="muted">still consolidating /${nt.previous_grapheme}/.</div>`) +
    `<p class="rationale">${nt.rationale}</p>`;

  $("results").hidden = false;
}

// Preset transcripts are built client-side from the known book words so filming
// is smooth; the server still scores them honestly. "One miscue" / "Struggling"
// drop words that actually bear the target grapheme, so the target visibly moves.
export function applyPreset(kind) {
  const words = state.words;
  const targets = state.targetPositions;
  const drop = new Set();
  if (kind === "one") {
    drop.add(targets.length ? targets[0] : Math.min(1, words.length - 1));
  } else if (kind === "struggle") {
    if (targets.length) targets.forEach((p) => drop.add(p));
    else for (let i = 1; i < words.length; i += 2) drop.add(i);
  }
  const kept = words.filter((_, i) => !drop.has(i));
  $("transcript").value = kept.join(" ");
}

function setMean(x) {
  $("mean-fill").style.width = pct(x);
  $("mean-value").textContent = (x * 100).toFixed(0) + "%";
}
