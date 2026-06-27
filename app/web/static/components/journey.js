// app/web/static/components/journey.js
//
// THE JOURNEY (redesign PR9) — promoted from a hidden modal to a first-class,
// effort-framed space. The emotional centerpiece is THE SHELF: every story the
// child has finished, as a little bound book they earned. Below it, the quiet
// proof the loop adapts (the sound practiced shifts, the growth line rises).
//
// Framed by EFFORT, never accuracy (design-system §12): no percentages, no
// accuracy headline. Pure read over persisted SessionLogs (the `journey` action).

"use strict";

import { $, esc } from "../dom.js";
import * as ws from "../ws.js";
import { state } from "../state.js";

// Deterministic spine color from a title, so a child's shelf is stable across
// loads without any backend/schema change. Palette = brand cloth colors.
const SPINES = ["#5C2A33", "#3E5247", "#2C5E7A", "#6E5320", "#6E4A55", "#4A222A"];
function spineColor(title) {
  let h = 0;
  for (let i = 0; i < title.length; i++) h = (h * 31 + title.charCodeAt(i)) >>> 0;
  return SPINES[h % SPINES.length];
}

function open() {
  $("journey-view").hidden = false;
  if (!state.learnerId) {
    $("journey-title").textContent = "Your shelf";
    $("journey-summary").textContent = "";
    $("journey-body").innerHTML =
      `<div class="journey-empty"><span class="journey-dot today"></span>` +
      `<p>Read your first story tonight — this is where the books you finish will live.</p></div>`;
    return;
  }
  $("journey-title").textContent = `${esc(state.learnerName || "Your")}${state.learnerName ? "'s" : ""} shelf`;
  $("journey-body").innerHTML = `<p class="muted">Gathering your books…</p>`;
  ws.send({ action: "journey", learner_id: state.learnerId });
}

function close() {
  $("journey-view").hidden = true;
}

// A calm growth line — the rise IS the proof; no axis, no numbers (gold endpoint).
function sparkline(means) {
  if (means.length < 2) return "";
  const W = 100, H = 30;
  const x = (i) => (i / (means.length - 1)) * W;
  const y = (m) => H - Math.max(0, Math.min(1, m)) * H;
  const line = means.map((m, i) => `${x(i).toFixed(1)},${y(m).toFixed(1)}`).join(" ");
  const area = `0,${H} ${line} ${W},${H}`;
  const ex = x(means.length - 1).toFixed(1), ey = y(means[means.length - 1]).toFixed(1);
  return (
    `<svg class="journey-spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" ` +
    `role="img" aria-label="Reading is growing over time">` +
    `<polygon points="${area}" class="spark-area"/>` +
    `<polyline points="${line}" class="spark-line"/>` +
    `<circle cx="${ex}" cy="${ey}" r="2.2" class="spark-end"/>` +
    `</svg>`
  );
}

function shelf(sessions) {
  // One spine per finished story; de-dupe repeated titles so the shelf reads as
  // a collection, not a log.
  const seen = new Set();
  const books = [];
  sessions.forEach((s) => {
    const title = (s.book_title || "").trim();
    if (!title || seen.has(title)) return;
    seen.add(title);
    books.push(title);
  });
  const spines = books
    .map(
      (t) =>
        `<span class="shelf-spine" style="background:${spineColor(t)}" title="${esc(t)}">` +
        `<span class="shelf-title">${esc(t)}</span></span>`
    )
    .join("");
  return `<div class="shelf" role="list" aria-label="Books finished">${spines}</div>`;
}

function render(msg) {
  const name = msg.learner_name || "This reader";
  $("journey-title").textContent = `${esc(name)}'s shelf`;
  const body = $("journey-body");
  const sessions = msg.sessions || [];

  if (sessions.length === 0) {
    $("journey-summary").textContent = "";
    body.innerHTML =
      `<div class="journey-empty"><span class="journey-dot today"></span>` +
      `<p>${esc(name)}'s shelf is waiting — read your first story to add a book.</p></div>`;
    return;
  }

  const soundsLearned = sessions.reduce((n, s) => n + (s.newly_mastered || []).length, 0);
  const storyWord = sessions.length === 1 ? "story" : "stories";
  $("journey-summary").textContent =
    `${sessions.length} ${storyWord} together` +
    (soundsLearned ? ` · ${soundsLearned} new sound${soundsLearned === 1 ? "" : "s"} learned` : "");

  const means = sessions.map((x) => x.mean_mastery).filter((m) => m != null);

  // The quiet adaptation proof: the sound practiced shifts; sounds get learned.
  const cell = (inner, cls, title) =>
    `<span class="jcell${cls ? " " + cls : ""}"${title ? ` title="${esc(title)}"` : ""}>${inner}</span>`;
  const soundRow = sessions
    .map((x) => cell(`/${esc(x.target_grapheme)}/`, "journey-target" + (x.target_changed ? " changed" : "")))
    .join("");
  const storyRow = sessions
    .map((x, i) => {
      const today = i === sessions.length - 1;
      return cell(`<span class="journey-dot${today ? " today" : ""}"></span>`, "", x.book_title || `story ${i + 1}`);
    })
    .join("");
  const learnedRow = sessions
    .map((x) => cell((x.newly_mastered || []).map((g) => `✓${esc(g)}`).join(" "), "journey-mastered"))
    .join("");

  const row = (label, cells) =>
    `<div class="jrow"><span class="jlabel">${label}</span><div class="jcells">${cells}</div></div>`;

  body.innerHTML =
    shelf(sessions) +
    (means.length >= 2
      ? `<div class="jspark-wrap"><span class="jlabel">growing</span>${sparkline(means)}</div>`
      : "") +
    `<details class="journey-detail"><summary>Story by story</summary><div class="jtl">` +
    row("sound", soundRow) +
    row("story", storyRow) +
    row("learned", learnedRow) +
    `</div></details>`;
}

export const Journey = {
  mount() {
    const btn = $("journey-btn");
    if (btn) {
      btn.hidden = false; // first-class: always reachable
      btn.addEventListener("click", open);
    }
    const closeBtn = $("journey-close");
    if (closeBtn) closeBtn.addEventListener("click", close);
    ws.on("journey", render);
  },
};
