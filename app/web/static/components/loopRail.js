// app/web/static/components/loopRail.js
//
// THE HERO OBJECT (docs/DESIGN.md §4). A persistent rail of the six loop steps
// that lights as each runs and turns green ✓ when its guardrail passes. It both
// narrates the ADK architecture to a judge and is the app's IA spine.
//
// It re-stages events the loop already emits (no new backend):
//   prepared  -> Plan/Generate/Verify ran and passed before the book was sent,
//                so they stagger to ✓; Read begins (lit + pulse, waiting).
//   beginAssess (typed submit) / voice_status (transcribing) -> Read ✓, Assess lit.
//   outcome   -> Assess ✓, Adapt lights then ✓ (the loop closed this session).
//   error mid-read -> revert to "waiting to read" so the rail never lies.
//
// The Verify node is the differentiator (deterministic check_decodability) — it
// gets a subtle ring on pass (see .loop-node[data-node="verify"].done in CSS).

"use strict";

import { on } from "../ws.js";
import { prefersReducedMotion } from "../dom.js";

const NODES = [
  { id: "plan", n: 1, name: "Plan", sub: "select_objective" },
  { id: "generate", n: 2, name: "Generate", sub: "decodable book" },
  { id: "verify", n: 3, name: "Verify", sub: "check_decodability" },
  { id: "read", n: 4, name: "Read", sub: "child reads aloud" },
  { id: "assess", n: 5, name: "Assess", sub: "assess + attribute" },
  { id: "adapt", n: 6, name: "Adapt", sub: "update_from_evidence" },
];

let els = {};        // id -> node element
let reduce = false;
const timers = [];   // pending stagger timeouts (cleared on reset)

function build(container) {
  container.innerHTML = "";
  els = {};
  NODES.forEach((node) => {
    const div = document.createElement("div");
    div.className = "loop-node";
    div.dataset.node = node.id;
    div.innerHTML =
      `<span class="ln-index" aria-hidden="true">${node.n}</span>` +
      `<span class="ln-name">${node.name}</span>` +
      `<span class="ln-sub">${node.sub}</span>`;
    container.appendChild(div);
    els[node.id] = div;
  });
}

function clearTimers() {
  while (timers.length) clearTimeout(timers.pop());
}
function after(ms, fn) {
  timers.push(setTimeout(fn, reduce ? 0 : ms));
}

function setNode(id, cls) {
  const el = els[id];
  if (el) el.className = "loop-node" + (cls ? " " + cls : "");
}

function reset() {
  clearTimers();
  NODES.forEach((node) => setNode(node.id, ""));
}

// prepared: the planner chose, the generator wrote, the verifier passed — all
// before this payload arrived. Stagger them to ✓, then hand off to Read.
function onPrepared() {
  reset();
  const seq = ["plan", "generate", "verify"];
  const step = reduce ? 0 : 150; // DESIGN §10.4 stagger
  seq.forEach((id, i) => {
    after(i * step, () => setNode(id, "lit"));
    after(i * step + 160, () => setNode(id, "done"));
  });
  after(seq.length * step, () => setNode("read", "lit pulse"));
}

// The child's read is complete; attribution + BKT are about to run.
function beginAssess() {
  if (!els.assess) return;
  setNode("read", "done");
  setNode("assess", "lit pulse");
}

// outcome: assessment + mastery update landed. Close the loop on the Adapt node.
function onOutcome() {
  setNode("assess", "done");
  setNode("adapt", "lit pulse");
  after(500, () => setNode("adapt", "done"));
}

// A read/transcription failed — return to "waiting to read" so the rail is honest.
function onError() {
  if (els.assess && els.assess.classList.contains("lit")) {
    setNode("assess", "");
    setNode("read", "lit pulse");
  }
}

export const LoopRail = {
  mount(container) {
    if (!container) return;
    reduce = prefersReducedMotion();
    build(container);
    on("prepared", onPrepared);
    on("voice_status", beginAssess); // server's "transcribing…" marks read done
    on("outcome", onOutcome);
    on("error", onError);
  },
  // Exposed for the typed-submit path (no inbound echo before the outcome).
  beginAssess,
  reset,
};
