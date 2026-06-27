// app/web/static/components/whyCard.js
//
// "Why this book?" (archive/legacy-design/DESIGN.md (legacy, archived) §5) — the Spotify "Because you listened to…"
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

  // Warm, parent-facing sentence — composed from structured fields, NOT echoed
  // from the planner's raw (technical) rationale. Grapheme is server-controlled;
  // name is escaped. No percentages, no "mastery"/"unmastered" (voice-lexicon).
  const sentence = review.length
    ? `Tonight we practice the <b>/${g}/</b> sound — the next one ${esc(name)} is ready for. ` +
      `We'll also revisit ${review.map((r) => `/${esc(r)}/`).join(" and ")} to keep ` +
      `${review.length > 1 ? "them" : "it"} familiar.`
    : `Tonight we practice the <b>/${g}/</b> sound — the next one ${esc(name)} is ready for, ` +
      `chosen from how they read last time, not a fixed worksheet.`;

  const chips = [`<span class="evidence-chip is-target">/${g}/ · tonight's sound</span>`];
  review.forEach((r) =>
    chips.push(`<span class="evidence-chip">/${esc(r)}/ · keeping it familiar</span>`)
  );

  el.innerHTML =
    `<div class="why-card">` +
    `<h4>Why this story?</h4>` +
    `<p class="why-text">${sentence}</p>` +
    `<div class="evidence-chips">${chips.join("")}</div>` +
    `</div>`;
}

export const WhyCard = {
  mount() { on("prepared", render); },
};
