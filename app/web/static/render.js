// app/web/static/render.js
//
// Shared renderers for the two faces of the Session screen. renderPrepared
// populates both the Reading face (child-safe words) and the Insight face
// (running-record host) from one payload; renderOutcome paints the post-hoc
// heatmap into Insight only and flips Reading to the child-safe celebration.
// Dedicated components own the rest: WhyCard, MasteryPath, LoopRail, ModeToggle.

"use strict";

import { $, pct, stat } from "./dom.js";
import { state } from "./state.js";
import { voiceStatus } from "./voice.js";
import { endBookGen, bookProgress } from "./book.js";

// ---- Render: prepared -------------------------------------------------------

export function renderPrepared(msg) {
  // Setup is the empty state of the Session screen (DESIGN §8) — collapse it
  // once a session is live so it stops lingering above #session. Connection
  // health now lives in the DegradeBanner, which survives this being hidden.
  $("setup").hidden = true;
  $("session").hidden = false;
  $("journey-view").hidden = true;
  $("transcript").value = "";
  voiceStatus("");

  $("session-pill").textContent = `session #${msg.session_index}`;
  $("target-grapheme").textContent = `/${msg.objective.target_grapheme}/`;
  $("target-level").textContent = msg.objective.target_level;
  // Planner rationale -> WhyCard (#why-card); mastery -> MasteryPath; both
  // subscribe to `prepared` directly.

  // Reset + reveal the take-home book panel (only when the feature is enabled).
  state.learnerId = msg.learner_id || "";
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
  const tgtPos = new Set(state.targetPositions);

  const title = msg.book.title || "Practice page";
  $("reading-title").textContent = title;
  $("book-title").textContent = title;
  $("book-source").textContent = msg.book.generation_source;

  // Render the words into BOTH faces from the same payload (DESIGN §18: the two
  // faces are pure views of one payload). Reading = child-safe (target words
  // softly underlined, never colored); Insight = running-record host for the
  // post-hoc heatmap.
  const rp = $("reading-page");
  const text = $("book-text");
  rp.innerHTML = "";
  text.innerHTML = "";
  msg.book.words.forEach((w, i) => {
    const rw = document.createElement("span");
    rw.className = "rw" + (tgtPos.has(i) ? " tgt-word" : "");
    rw.textContent = w;
    rp.appendChild(rw);
    rp.appendChild(document.createTextNode(" "));

    const span = document.createElement("span");
    span.className = "w";
    span.dataset.position = i;
    span.textContent = w;
    text.appendChild(span);
    text.appendChild(document.createTextNode(" "));
  });

  // Reset the read flow: child-safe Reading state, scoring is the primary CTA,
  // and the Insight result regions are cleared for the new session.
  $("read-celebrate").hidden = true;
  $("score-btn").hidden = false;
  $("next-btn").hidden = true;
  $("fluency").innerHTML = "";
  $("scaffolds").innerHTML = "";
  $("next-target").innerHTML = "";

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

  // Privacy boundary (DESIGN §18): stay child-safe in Reading; the running
  // record + analysis live in Insight, reachable only by an adult tap (the
  // ModeToggle sets a pip on `outcome`). Never auto-flip red into the child's view.
  $("read-celebrate").hidden = false;
  $("score-btn").hidden = true;
  $("next-btn").hidden = false;
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
