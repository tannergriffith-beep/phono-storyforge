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
  mic: { ctx: null, stream: null, node: null, recording: false },
  illustratedEnabled: false,  // creds-gated take-home book feature
  learnerName: "",            // for the "Generate <name>'s book" label
};

const OUT_RATE = 16000;  // app/voice expects 16-bit/16 kHz mono PCM

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
    if (msg.type === "capabilities") { state.illustratedEnabled = !!msg.illustrated_enabled; }
    else if (msg.type === "prepared") renderPrepared(msg);
    else if (msg.type === "outcome") renderOutcome(msg);
    else if (msg.type === "voice_status") voiceStatus(msg.message);
    else if (msg.type === "book_progress") bookProgress(msg.message);
    else if (msg.type === "book_ready") renderBookReady(msg);
    else if (msg.type === "error") { setStatus(msg.message, "err"); voiceStatus(msg.message); bookProgress(msg.message); endBookGen(); }
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

// ---- Illustrated take-home book (opt-in, creds-gated) -----------------------

function generateBook() {
  const btn = $("gen-book-btn");
  btn.disabled = true;
  $("book-result").hidden = true;
  bookProgress("Starting…");
  send({ action: "generate_book" });
}

function bookProgress(text) { $("book-progress").textContent = text || ""; }

function endBookGen() {
  const btn = $("gen-book-btn");
  if (btn) btn.disabled = false;
}

function renderBookReady(msg) {
  endBookGen();
  bookProgress("Done — the illustrated book is ready.");

  // Doc link — present unless the export degraded to pages-only.
  const link = $("book-link");
  if (msg.shareable_url) {
    link.href = msg.shareable_url;
    link.textContent = (msg.title ? `Open “${msg.title}” ↗` : "Open the Google Doc ↗");
    link.hidden = false;
  } else {
    link.hidden = true;
  }

  $("book-decodable").textContent = msg.decodable ? "decodable ✓" : "decodability unverified";

  // A short note when something degraded, so the result is never misleading.
  const notes = {
    illustrated_pages_only: "Pages illustrated, but the Google Docs export was unavailable — showing the pages here.",
    text_only: "Illustrations were unavailable, so this is a text-only book.",
    text_only_pages_only: "Illustrations and the Docs export were unavailable — showing the page text only.",
  };
  $("book-note").textContent = notes[msg.source] || "";

  // Pages with inline thumbnails when illustrated.
  const pagesEl = $("book-pages");
  pagesEl.innerHTML = "";
  (msg.pages || []).forEach((p, i) => {
    const div = document.createElement("div");
    div.className = "book-page";
    if (p.image_ref) {
      const img = document.createElement("img");
      img.className = "book-thumb";
      img.src = p.image_ref;
      img.alt = `page ${i + 1} illustration`;
      div.appendChild(img);
    }
    const num = document.createElement("span");
    num.className = "book-page-n";
    num.textContent = i + 1;
    const txt = document.createElement("span");
    txt.className = "book-page-t";
    txt.textContent = p.text;
    div.appendChild(num);
    div.appendChild(txt);
    pagesEl.appendChild(div);
  });
  $("book-result").hidden = false;
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

// ---- Step 2: browser mic -> WebSocket -> app/voice Transcriber --------------
//
// Additive enhancement: stream 16 kHz/16-bit PCM frames over the same socket
// between read_start/read_end. The server feeds them to the injectable
// LiveTranscriber audio_source. If anything fails (no mic, no Live quota), the
// typed presets above still work — voice is never load-bearing.

async function toggleMic() {
  if (state.mic.recording) { stopMic(); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    await ctx.audioWorklet.addModule("/static/pcm-worklet.js");
    const src = ctx.createMediaStreamSource(stream);
    const node = new AudioWorkletNode(ctx, "pcm-capture");
    const inRate = ctx.sampleRate;
    node.port.onmessage = (e) => {
      const pcm16 = downsampleTo16k(e.data, inRate);
      if (pcm16.length && state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(pcm16.buffer);
      }
    };
    src.connect(node);
    node.connect(ctx.destination); // pulls the graph; worklet output is silent (no echo)
    state.mic = { ctx, stream, node, recording: true };
    send({ action: "read_start" });
    setMicUI(true);
    voiceStatus("🎤 listening… click Stop when the child finishes the page");
  } catch (err) {
    voiceStatus("mic unavailable: " + err.message + " — use the typed presets instead");
  }
}

function stopMic() {
  send({ action: "read_end" });
  const m = state.mic;
  if (m.node) m.node.disconnect();
  if (m.stream) m.stream.getTracks().forEach((t) => t.stop());
  if (m.ctx) m.ctx.close();
  state.mic = { ctx: null, stream: null, node: null, recording: false };
  setMicUI(false);
  voiceStatus("transcribing…");
}

// Nearest-sample downsample from the mic's native rate to 16 kHz, then to Int16.
function downsampleTo16k(f32, inRate) {
  const ratio = inRate / OUT_RATE;
  const outLen = Math.floor(f32.length / ratio);
  const out = new Int16Array(outLen);
  for (let i = 0; i < outLen; i++) {
    const s = Math.max(-1, Math.min(1, f32[Math.floor(i * ratio)]));
    out[i] = s * 0x7fff;
  }
  return out;
}

function setMicUI(recording) {
  const btn = $("mic-btn");
  btn.textContent = recording ? "⏹ Stop" : "🎤 Read aloud";
  btn.classList.toggle("recording", recording);
}

function voiceStatus(text) { $("voice-status").textContent = text || ""; }

// ---- Render: prepared -------------------------------------------------------

function renderPrepared(msg) {
  $("setup").hidden = false;
  $("session").hidden = false;
  $("results").hidden = true;
  $("transcript").value = "";
  voiceStatus("");

  $("session-pill").textContent = `session #${msg.session_index}`;
  $("target-grapheme").textContent = `/${msg.objective.target_grapheme}/`;
  $("target-level").textContent = msg.objective.target_level;
  $("rationale").textContent = msg.objective.rationale;

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
$("mic-btn").addEventListener("click", toggleMic);
$("gen-book-btn").addEventListener("click", generateBook);
document.querySelectorAll(".presets [data-preset]").forEach((btn) =>
  btn.addEventListener("click", () => applyPreset(btn.dataset.preset))
);
connect();
