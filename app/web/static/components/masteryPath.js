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

function update(msg) {
  (msg.mastery_updates || []).forEach((u) => {
    const node = nodes[u.grapheme];
    if (!node) return;
    node.p = u.p_after;
    const cls = classOf(u.p_after, node.isTarget);
    node.el.className = "grapheme-node " + cls;
    node.el.setAttribute("aria-label", labelFor(u.grapheme, u.p_after, cls));
    if (u.newly_mastered) {
      // Re-trigger the pop animation reliably.
      node.el.classList.remove("just-mastered");
      void node.el.offsetWidth; // reflow
      node.el.classList.add("just-mastered");
    }
  });
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
  mount() {
    on("prepared", render);
    on("outcome", update);
  },
};
