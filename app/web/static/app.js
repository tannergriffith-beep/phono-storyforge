// app/web/static/app.js
//
// FLAGSHIP STAGE C: the vanilla-JS WebSocket client.
//
// Drives the real closed loop over one socket: prepare -> render book + bars,
// submit transcript -> animate the miscue heatmap, mastery bars, and the
// (possibly advanced) next target. No framework, no charting lib — the
// animations are CSS transitions triggered by setting widths/classes here.
// Browser-mic voice (step 2) is additive on this same socket; the typed path
// below stands on its own.

"use strict";

const $ = (id) => document.getElementById(id);

const state = {
  ws: null,
  words: [],            // expected token stream (positions index into this)
  targetPositions: [],  // positions of words exercising the target grapheme
  bars: {},             // grapheme -> {row, fill, p}
};

// ---- WebSocket wiring -------------------------------------------------------

function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  state.ws = ws;

  ws.onopen = () => setStatus("connected", "ok");
  ws.onclose = () => setStatus("disconnected — refresh to reconnect", "err");
  ws.onerror = () => setStatus("connection error", "err");
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === "prepared") renderPrepared(msg);
    else if (msg.type === "outcome") renderOutcome(msg);
    else if (msg.type === "error") setStatus(msg.message, "err");
  };
}

function send(obj) {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) state.ws.send(JSON.stringify(obj));
}

function setStatus(text, cls) {
  const el = $("conn-status");
  el.textContent = text;
  el.className = "status" + (cls ? " " + cls : "");
}

// ---- Actions ----------------------------------------------------------------

function startSession() {
  send({
    action: "prepare",
    learner_id: $("learner-id").value.trim() || "ada",
    name: $("learner-name").value.trim(),
    age: parseInt($("learner-age").value, 10) || 6,
    interest: $("learner-interest").value.trim(),
  });
}

function scoreRead() {
  const transcript = $("transcript").value.trim();
  send({ action: "submit", transcript });
}

// Preset transcripts are built client-side from the known book words so filming
// is smooth; the server still scores them honestly. "One miscue" / "Struggling"
// drop words that actually bear the target grapheme, so the target visibly moves.
function applyPreset(kind) {
  const words = state.words;
  const targets = state.targetPositions;
  let drop = new Set();
  if (kind === "one") {
    drop.add(targets.length ? targets[0] : Math.min(1, words.length - 1));
  } else if (kind === "struggle") {
    if (targets.length) targets.forEach((p) => drop.add(p));
    else for (let i = 1; i < words.length; i += 2) drop.add(i);
  }
  const kept = words.filter((_, i) => !drop.has(i));
  $("transcript").value = kept.join(" ");
}

// ---- Render: prepared -------------------------------------------------------

function renderPrepared(msg) {
  $("setup").hidden = false;
  $("session").hidden = false;
  $("results").hidden = true;
  $("transcript").value = "";

  $("session-pill").textContent = `session #${msg.session_index}`;
  $("target-grapheme").textContent = `/${msg.objective.target_grapheme}/`;
  $("target-level").textContent = msg.objective.target_level;
  $("rationale").textContent = msg.objective.rationale;

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

  renderBars(msg.mastery_bars);
  setMean(msg.mean_mastery);
}

function renderBars(bars) {
  const container = $("bars");
  container.innerHTML = "";
  state.bars = {};
  bars.forEach((b) => {
    const row = document.createElement("div");
    row.className = "bar-row" + (b.is_target ? " target" : "") + (b.is_review ? " review" : "");
    row.innerHTML =
      `<div class="bar-head"><span class="bar-g"></span><span class="bar-p"></span></div>` +
      `<div class="bar-track"><div class="bar-fill"></div></div>`;
    row.querySelector(".bar-g").textContent = b.grapheme;
    const fill = row.querySelector(".bar-fill");
    const pEl = row.querySelector(".bar-p");
    pEl.textContent = pct(b.p_mastery);
    // Defer width so the transition runs from 0 -> value on first paint.
    requestAnimationFrame(() => { fill.style.width = pct(b.p_mastery); });
    if (b.p_mastery >= 0.85) fill.classList.add("mastered");
    container.appendChild(row);
    state.bars[b.grapheme] = { row, fill, pEl };
  });
}

// ---- Render: outcome --------------------------------------------------------

function renderOutcome(msg) {
  // Miscue heatmap: color each expected word by its running-record kind.
  const spans = $("book-text").querySelectorAll(".w");
  msg.heatmap.forEach((cell) => {
    const span = spans[cell.position];
    if (!span) return;
    span.classList.add(cell.kind);
    if (cell.spoken) span.title = `heard: ${cell.spoken}`;
  });

  // Mastery bars: animate every grapheme this read moved to its new P(L).
  msg.mastery_updates.forEach((u) => {
    const bar = state.bars[u.grapheme];
    if (!bar) return;
    bar.fill.style.width = pct(u.p_after);
    bar.pEl.textContent = pct(u.p_after);
    bar.fill.classList.toggle("mastered", u.newly_mastered || u.p_after >= 0.85);
    if (u.newly_mastered) {
      bar.row.classList.add("just-mastered");
    }
  });
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

// ---- Helpers ----------------------------------------------------------------

const pct = (x) => (Math.max(0, Math.min(1, x)) * 100).toFixed(1) + "%";
const stat = (v, k) => `<div class="stat"><div class="v">${v}</div><div class="k">${k}</div></div>`;

function setMean(x) {
  $("mean-fill").style.width = pct(x);
  $("mean-value").textContent = (x * 100).toFixed(0) + "%";
}

// ---- Boot -------------------------------------------------------------------

$("start-btn").addEventListener("click", startSession);
$("score-btn").addEventListener("click", scoreRead);
$("next-btn").addEventListener("click", startSession);
document.querySelectorAll(".presets [data-preset]").forEach((btn) =>
  btn.addEventListener("click", () => applyPreset(btn.dataset.preset))
);
connect();
