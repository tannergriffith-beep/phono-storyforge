// app/web/static/components/whyCard.js
//
// "Why this book?" (docs/DESIGN.md §5) — the Spotify "Because you listened to…"
// reasoned moment. It makes the Plan node legible: the planner didn't pick a
// worksheet, it chose this child's lowest unmastered sound from their own
// mastery evidence.
//
// Built entirely from the existing `prepared` payload — no backend change:
//   - objective.rationale         -> the judge-facing "receipt" (raw planner output)
//   - objective.target_grapheme   -> the warm headline + focus chip
//   - objective.review_graphemes  -> spaced-review chips
//   - mastery_bars[].p_mastery    -> the P(L) shown on each chip
//
// (The DESIGN mock also shows prior miscue word-pairs like "had → head"; those
// aren't in this payload, so we surface mastery-evidence chips instead. Adding
// miscue pairs is a small viz.py change to pair with the Journey work.)

"use strict";

import { $, esc } from "../dom.js";
import { on } from "../ws.js";

const pctInt = (p) => Math.round((p || 0) * 100) + "%";

function render(msg) {
  const el = $("why-card");
  if (!el) return;

  const obj = msg.objective;
  const g = obj.target_grapheme;
  const review = obj.review_graphemes || [];
  const name = msg.learner_name || "this reader";

  const byG = {};
  (msg.mastery_bars || []).forEach((b) => { byG[b.grapheme] = b; });
  const tgtP = byG[g] ? byG[g].p_mastery : 0;

  // Warm, parent-facing sentence. Grapheme is server-controlled; name is escaped.
  const sentence = review.length
    ? `Today we practice <b>/${g}/</b> — the next unmastered sound on ${esc(name)}'s path. ` +
      `We'll also revisit ${review.map((r) => `/${esc(r)}/`).join(" and ")} to keep ` +
      `${review.length > 1 ? "them" : "it"} sharp.`
    : `Today we practice <b>/${g}/</b> — the next unmastered sound on ${esc(name)}'s path, ` +
      `chosen by the planner from mastery evidence, not a fixed worksheet.`;

  const chips = [`<span class="evidence-chip is-target">/${g}/ · ${pctInt(tgtP)} · focus</span>`];
  review.forEach((r) =>
    chips.push(`<span class="evidence-chip">/${esc(r)}/ ${pctInt(byG[r] ? byG[r].p_mastery : 0)} ✓</span>`)
  );

  el.innerHTML =
    `<div class="why-card">` +
    `<h4>Why this book?</h4>` +
    `<p class="why-text">${sentence}</p>` +
    `<div class="evidence-chips">${chips.join("")}</div>` +
    `<p class="why-receipt" title="the planner's raw rationale">${esc(obj.rationale)}</p>` +
    `</div>`;
}

export const WhyCard = {
  mount() { on("prepared", render); },
};
