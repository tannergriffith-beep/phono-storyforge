// app/web/static/components/sessionArc.js
//
// The human session arc (design-system §10; ui-audit #2) — replaces the engineer
// "loop rail" as the parent-facing navigation. A parent's mental model isn't
// Plan/Generate/Verify/Assess/Adapt; it's a night with their child:
//
//     Tonight's story  →  Read together  →  How it went  →  What's next
//
// It advances on the SAME ws events the loop rail used (prepared / voice_status /
// outcome), so no backend change. The technical six-node loop still exists behind
// a flag (loopRail.js) for educators/demos — see app.js.

"use strict";

import { on } from "../ws.js";

const STEPS = ["Tonight's story", "Read together", "How it went", "What's next"];
let host = null;
let cells = [];

function paint(activeIdx) {
  cells.forEach((el, i) => {
    el.classList.toggle("done", i < activeIdx);
    el.classList.toggle("active", i === activeIdx);
    if (i === activeIdx) el.setAttribute("aria-current", "step");
    else el.removeAttribute("aria-current");
  });
}

function setActive(idx) {
  if (!host) return;
  paint(idx);
}

export const SessionArc = {
  mount(el) {
    host = el;
    if (!host) return;
    host.innerHTML = "";
    cells = STEPS.map((label, i) => {
      const step = document.createElement("span");
      step.className = "arc-step";
      step.innerHTML = `<span class="arc-dot" aria-hidden="true"></span><span class="arc-label">${label}</span>`;
      host.appendChild(step);
      if (i < STEPS.length - 1) {
        const sep = document.createElement("span");
        sep.className = "arc-sep";
        sep.setAttribute("aria-hidden", "true");
        host.appendChild(sep);
      }
      return step;
    });

    // Story is ready → now read together.
    on("prepared", () => setActive(1));
    // The child finished reading (voice transcribing) → how it went.
    on("voice_status", (m) => { if (m && m.message) setActive(2); });
    // Scored → what's next.
    on("outcome", () => setActive(3));

    setActive(0);
  },
  // Called from app.js when the adult taps "How did it go?" on the typed path
  // (no inbound event precedes the outcome there).
  beginScore() { setActive(2); },
};
