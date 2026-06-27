// app/web/static/components/modeToggle.js
//
// READ ⇄ INSIGHT (archive/legacy-design/DESIGN.md (legacy, archived) §5/§18) — the two faces of one screen, the
// single highest-value move in the redesign. It dissolves two UX risks at once:
// the child never sees their misses in red (Reading is child-safe), and the one
// surface stops overwhelming all three viewers.
//
// The safe model (DESIGN §18):
//   - PURE view-switch over the already-received payload — never re-fetch, never
//     re-score. Both faces persist in the DOM; we only toggle visibility, so the
//     reading position and the insight content are preserved on return.
//   - The transition is the PRIVACY BOUNDARY: after a Score we NEVER auto-flip
//     red miscues into the child's face. We show "Great reading!" in Reading and
//     drop a notification pip on the Insight tab; an adult must tap to cross over.
//   - 200ms cross-fade; a keyboard shortcut (r / i) for the filmed run.

"use strict";

import { $, prefersReducedMotion } from "../dom.js";
import { on } from "../ws.js";

let mode = "reading";
let reduce = false;
let readingBtn, insightBtn, readingFace, insightFace;
let fadeTimer = null;

// opts.focus moves keyboard/SR focus to the incoming face after the swap — set
// for user-initiated switches (click/keypress), not the programmatic reset on a
// new `prepared` (which would yank focus mid-render).
function setMode(next, opts = {}) {
  if (next === mode) { if (next === "insight") clearPip(); return; }
  const outFace = mode === "reading" ? readingFace : insightFace;
  const inFace = next === "reading" ? readingFace : insightFace;
  mode = next;

  readingBtn.setAttribute("aria-pressed", String(next === "reading"));
  insightBtn.setAttribute("aria-pressed", String(next === "insight"));

  // Announce the view change so the AdaptBeat can play a deferred climax when
  // an adult crosses into Insight (DESIGN §18).
  document.dispatchEvent(new CustomEvent("phono:mode", { detail: { mode: next } }));

  const swap = () => {
    outFace.hidden = true;
    outFace.classList.remove("is-active");
    inFace.hidden = false;
    // next frame so the opacity transition runs from 0 -> 1
    requestAnimationFrame(() => {
      inFace.classList.add("is-active");
      if (opts.focus) inFace.focus();
    });
  };

  clearTimeout(fadeTimer);
  if (reduce) {
    swap();
  } else {
    outFace.classList.remove("is-active"); // fade the current face out first
    fadeTimer = setTimeout(swap, 180);
  }

  if (next === "insight") clearPip();
}

function clearPip() { insightBtn.classList.remove("has-pip"); }
function setPip() { if (mode !== "insight") insightBtn.classList.add("has-pip"); }

function onKey(e) {
  const tag = (e.target && e.target.tagName ? e.target.tagName : "").toLowerCase();
  if (tag === "input" || tag === "textarea" || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === "r" || e.key === "R") setMode("reading", { focus: true });
  else if (e.key === "i" || e.key === "I") setMode("insight", { focus: true });
}

export const ModeToggle = {
  mount() {
    readingBtn = $("mode-reading");
    insightBtn = $("mode-insight");
    readingFace = $("reading-face");
    insightFace = $("insight-face");
    if (!readingBtn || !insightBtn) return;
    reduce = prefersReducedMotion();

    readingBtn.addEventListener("click", () => setMode("reading", { focus: true }));
    insightBtn.addEventListener("click", () => setMode("insight", { focus: true }));
    document.addEventListener("keydown", onKey);

    // A new session starts child-facing with no pip (privacy default).
    on("prepared", () => { setMode("reading"); clearPip(); });
    // New analysis to see, but never auto-flip — the pip invites the adult tap.
    on("outcome", setPip);
  },
};
