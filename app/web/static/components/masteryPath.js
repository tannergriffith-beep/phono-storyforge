// app/web/static/components/masteryPath.js
//
// THE MASTERY PATH (docs/DESIGN.md §6) — replaces the always-on 340px / 30-bar
// scroll. Graphemes are nodes along the level sequence:
//   mastered  -> sage-filled        (P(L) >= MASTERY_BAR)
//   current   -> coral, glowing, up  (this session's target)
//   progress  -> sage-tinted         (started, not yet mastered, not the target)
//   locked    -> pearl, dashed        (not yet introduced)
// One hero number (mean mastery) stays in the top bar; per-grapheme P(L) appears
// on tap (progressive disclosure — Oura/Whirl pattern).
//
// Data: the existing `prepared.mastery_bars` (already sorted by level) and
// `outcome.mastery_updates`. No backend change. The render/update API is kept
// generic ({grapheme, level, p_mastery, is_target}) so the Adapt beat (§7) can
// later feed it a richer node list including "ahead" graphemes.

"use strict";

import { $, esc } from "../dom.js";
import { on } from "../ws.js";

const MASTERY_BAR = 0.85; // matches the BKT mastery threshold used elsewhere

let nodes = {};   // grapheme -> { el, p, level }
let pathEl = null;
let detailEl = null;

function classOf(p, isTarget) {
  if (isTarget) return "current";
  if (p >= MASTERY_BAR) return "mastered";
  if (p > 0) return "progress";
  return "locked";
}

function labelFor(g, p, cls) {
  const state = { current: "current target", mastered: "mastered", progress: "in progress", locked: "ahead" }[cls];
  return `${g}, ${state}, mastery ${Math.round(p * 100)} percent`;
}

function makeNode(bar) {
  const cls = classOf(bar.p_mastery, bar.is_target);
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "grapheme-node " + cls;
  btn.textContent = bar.grapheme;
  btn.dataset.grapheme = bar.grapheme;
  btn.setAttribute("aria-label", labelFor(bar.grapheme, bar.p_mastery, cls));
  btn.addEventListener("click", () => showDetail(bar.grapheme));
  return btn;
}

function render(msg) {
  pathEl = $("mastery-path");
  detailEl = $("mastery-detail");
  if (!pathEl) return;
  pathEl.innerHTML = "";
  if (detailEl) detailEl.innerHTML = "";
  nodes = {};

  const bars = msg.mastery_bars || [];
  bars.forEach((bar, i) => {
    const el = makeNode(bar);
    nodes[bar.grapheme] = { el, p: bar.p_mastery, level: bar.level, isTarget: !!bar.is_target };
    pathEl.appendChild(el);
    if (i < bars.length - 1) {
      const link = document.createElement("span");
      link.className = "gn-link";
      pathEl.appendChild(link);
    }
  });
}

// ---- Imperative ops (driven by the AdaptBeat on outcome, §7/§16) -----------

/** Sync P(L) + reclassify for each update. `skip` defers one grapheme (the
 *  just-finished target, which the Adapt beat animates itself). No pop here. */
function applyUpdates(updates, opts = {}) {
  (updates || []).forEach((u) => {
    if (opts.skip && u.grapheme === opts.skip) return;
    syncOne(u.grapheme, u.p_after);
  });
}

/** Set one grapheme's final P(L) state without any celebratory animation. */
function syncOne(grapheme, p) {
  const node = nodes[grapheme];
  if (!node) return;
  if (p != null) node.p = p;
  const cls = classOf(node.p, node.isTarget);
  node.el.className = "grapheme-node " + cls;
  node.el.setAttribute("aria-label", labelFor(grapheme, node.p, cls));
}

/** The just-mastered node fills sage and pops (DESIGN §16 F2). */
function popMastered(grapheme) {
  const node = nodes[grapheme];
  if (!node) return;
  node.isTarget = false;
  node.el.className = "grapheme-node mastered";
  node.el.setAttribute("aria-label", labelFor(grapheme, node.p, "mastered"));
  node.el.classList.remove("just-mastered");
  void node.el.offsetWidth; // reflow so the animation re-triggers
  node.el.classList.add("just-mastered");
}

/** The coral glow arrives: this node becomes the current target (DESIGN §16 F3). */
function setCurrent(grapheme) {
  const node = nodes[grapheme];
  if (!node) return;
  node.isTarget = true;
  node.el.className = "grapheme-node current";
  node.el.setAttribute("aria-label", labelFor(grapheme, node.p, "current"));
}

/** No-advance payoff: pulse the still-current target in place (DESIGN §16). */
function pulse(grapheme) {
  const node = nodes[grapheme];
  if (!node) return;
  node.el.classList.remove("pulse");
  void node.el.offsetWidth;
  node.el.classList.add("pulse");
}

/** Ensure a node exists so the glow can travel to the next target. Appended as
 *  whatever its real P(L) classifies to (usually locked/ahead). */
function ensureNode(grapheme, level, p) {
  if (nodes[grapheme]) return;
  if (!pathEl) return;
  const el = makeNode({ grapheme, level: level || "", p_mastery: p || 0, is_target: false });
  const link = document.createElement("span");
  link.className = "gn-link";
  pathEl.appendChild(link);
  pathEl.appendChild(el);
  nodes[grapheme] = { el, p: p || 0, level: level || "", isTarget: false };
}

function showDetail(grapheme) {
  if (!detailEl) return;
  const node = nodes[grapheme];
  if (!node) return;
  const cls = classOf(node.p, node.isTarget);
  const stateLabel = { current: "today's target", mastered: "mastered ✓", progress: "in progress", locked: "ahead" }[cls];
  detailEl.innerHTML =
    `<span class="md-g">/${esc(grapheme)}/</span> ` +
    (node.level ? `<span class="muted">${esc(node.level)}</span> · ` : "") +
    `<span class="md-p">${Math.round(node.p * 100)}%</span> P(L) · ${stateLabel}`;
}

export const MasteryPath = {
  // render() runs on `prepared`; the post-outcome animation is driven by the
  // AdaptBeat via the imperative ops below (so the climax is one choreography).
  mount() { on("prepared", render); },
  applyUpdates,
  syncOne,
  popMastered,
  setCurrent,
  pulse,
  ensureNode,
};
