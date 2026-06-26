// app/web/static/components/journey.js
//
// THE JOURNEY (docs/DESIGN.md §17) — the screen that proves "loop, not
// generator." A horizontal strip where the TARGET row shifts (adaptation) while
// the MEAN row rises (learning) — the whole thesis at a glance. It's a pure read
// over persisted SessionLogs (the `journey` action), so it's the one view that
// shows the loop closing over time.
//
// Empty state (session #1): never show an empty chart frame — show one coral dot
// and an invitation, and let the line grow as the loop runs.

"use strict";

import { $, esc } from "../dom.js";
import * as ws from "../ws.js";
import { state } from "../state.js";

function open() {
  if (!state.learnerId) return;
  $("journey-view").hidden = false;
  $("journey-body").innerHTML = `<p class="muted">Loading ${esc(state.learnerName || "the")} journey…</p>`;
  ws.send({ action: "journey", learner_id: state.learnerId });
}

function close() {
  $("journey-view").hidden = true;
}

// A simple SVG area+line sparkline for the mean trend (gold endpoint dot).
function sparkline(means) {
  if (means.length < 2) return "";
  const W = 100, H = 30;
  const x = (i) => (i / (means.length - 1)) * W;
  const y = (m) => H - Math.max(0, Math.min(1, m)) * H;
  const line = means.map((m, i) => `${x(i).toFixed(1)},${y(m).toFixed(1)}`).join(" ");
  const area = `0,${H} ${line} ${W},${H}`;
  const ex = x(means.length - 1).toFixed(1), ey = y(means[means.length - 1]).toFixed(1);
  return (
    `<svg class="journey-spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">` +
    `<polygon points="${area}" class="spark-area"/>` +
    `<polyline points="${line}" class="spark-line"/>` +
    `<circle cx="${ex}" cy="${ey}" r="2.2" class="spark-end"/>` +
    `</svg>`
  );
}

const meanPct = (m) => (m == null ? "—" : Math.round(m * 100) + "%");

function render(msg) {
  const name = msg.learner_name || "This reader";
  $("journey-title").textContent = `${name}'s journey`;
  const body = $("journey-body");
  const sessions = msg.sessions || [];
  const s = msg.summary || {};

  // Empty / first-session state — the line grows; never an empty frame.
  if (sessions.length <= 1) {
    $("journey-summary").textContent = sessions.length
      ? "1 session · the line is just beginning"
      : "";
    body.innerHTML =
      `<div class="journey-empty">` +
      `<span class="journey-dot today"></span>` +
      `<p>${esc(name)}'s journey begins — read your first story to start the line.</p>` +
      `</div>`;
    return;
  }

  $("journey-summary").textContent =
    `${s.count} sessions · mastery ${meanPct(s.first_mean)} → ${meanPct(s.last_mean)}`;

  const means = sessions.map((x) => x.mean_mastery).filter((m) => m != null);

  // Row-based layout so columns align across the four rows (flex:1 per cell).
  const cell = (inner, cls, title) =>
    `<span class="jcell${cls ? " " + cls : ""}"${title ? ` title="${title}"` : ""}>${inner}</span>`;

  const targetRow = sessions
    .map((x) => cell(esc(x.target_grapheme), "journey-target" + (x.target_changed ? " changed" : "")))
    .join("");
  const dotRow = sessions
    .map((x, i) => {
      const today = i === sessions.length - 1;
      const t = `session ${x.session_index}: ${esc(x.book_title || "")} · acc ${Math.round(
        x.accuracy * 100
      )}% · ${Math.round(x.wcpm)} WCPM`;
      return cell(`<span class="journey-dot${today ? " today" : ""}"></span>`, "", t);
    })
    .join("");
  const masteredRow = sessions
    .map((x) =>
      cell((x.newly_mastered || []).map((g) => `✓${esc(g)}`).join(" "), "journey-mastered")
    )
    .join("");
  const meanRow = sessions.map((x) => cell(meanPct(x.mean_mastery), "journey-mean")).join("");

  const row = (label, cells) =>
    `<div class="jrow"><span class="jlabel">${label}</span><div class="jcells">${cells}</div></div>`;

  body.innerHTML =
    `<div class="jtl">` +
    row("target", targetRow) +
    row("session", dotRow) +
    row("mastered", masteredRow) +
    row("mean", meanRow) +
    `</div>` +
    `<div class="jspark-wrap"><span class="jlabel">trend</span>${sparkline(means)}</div>`;
}

export const Journey = {
  mount() {
    const btn = $("journey-btn");
    if (btn) btn.addEventListener("click", open);
    const closeBtn = $("journey-close");
    if (closeBtn) closeBtn.addEventListener("click", close);
    // Reveal the Journey entry point once a learner exists.
    ws.on("prepared", () => { if (btn) btn.hidden = false; });
    ws.on("journey", render);
  },
};
