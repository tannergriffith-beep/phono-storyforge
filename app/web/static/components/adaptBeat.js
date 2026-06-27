// app/web/static/components/adaptBeat.js
//
// THE ADAPT CLIMAX (archive/legacy-design/DESIGN.md (legacy, archived) §7/§16) — the demo's payoff. It turns "a
// number changed" into "the AI just decided." ~1.5s of choreography fired after
// a read is scored and the planner's target advanced.
//
// Where it plays: the climax lives in Insight mode (the mastery path is there)
// and respects the privacy boundary (DESIGN §18) — after a Score the child stays
// in the child-safe Reading celebration, so the beat is DEFERRED until an adult
// taps Insight (or plays immediately if Insight is already open). The Insight tab
// pip (ModeToggle) is the invitation.
//
// It orchestrates the MasteryPath imperatively so the whole climax is one
// sequence: prev target pops to mastered → coral glow travels to the next
// target → caption resolves. The no-advance case never falls flat — it pulses
// the still-current target with its own line (DESIGN §16 camera notes).
//
// `?demo` in the URL slows the beat ~1.5× so the camera catches each frame.

"use strict";

import { $, esc, prefersReducedMotion } from "../dom.js";
import { on } from "../ws.js";
import { MasteryPath } from "./masteryPath.js";

let mode = "reading";
let pending = null; // {adv, prevG, nextG, prevMastered, name}
let reduce = false;
let speed = 1;
let learnerName = "this reader";

const captionEl = () => $("adapt-caption");

function resetCaption() {
  const cap = captionEl();
  if (cap) { cap.classList.remove("show"); cap.textContent = ""; }
}

function play() {
  const b = pending;
  pending = null;
  if (!b) return;
  const cap = captionEl();
  const ms = (x) => (reduce ? 0 : x * speed);

  if (b.adv) {
    // F2: the prev target crossed the bar → fills sage + pop (or just syncs).
    if (b.prevMastered) MasteryPath.popMastered(b.prevG);
    else MasteryPath.syncOne(b.prevG);
    // F3: the coral glow travels to the next target.
    setTimeout(() => MasteryPath.setCurrent(b.nextG), ms(450));
    // F4: the sentence lands — "chosen from her reading, not a worksheet."
    setTimeout(() => {
      if (!cap) return;
      cap.innerHTML =
        `${esc(b.name)} knows the /${esc(b.prevG)}/ sound now. Next we'll practice <b>/${esc(b.nextG)}/</b>.`;
      cap.classList.add("show");
    }, ms(900));
  } else {
    // No-advance variant — always a payoff (DESIGN §16): pulse in place.
    MasteryPath.pulse(b.prevG);
    if (cap) {
      cap.innerHTML = `Still building /${esc(b.prevG)}/ — one more story.`;
      cap.classList.add("show");
    }
  }
}

function onOutcome(msg) {
  const nt = msg.next_target;
  const updates = msg.mastery_updates || [];
  const prevG = nt.previous_grapheme;
  const nextG = nt.target_grapheme;
  const adv = !!nt.advanced;

  // Make sure the next target has a node so the glow has somewhere to travel.
  MasteryPath.ensureNode(nextG, nt.target_level, nt.p_mastery);
  // Sync every moved grapheme now (data must be correct even in Reading view);
  // when advancing, defer the prev target — the beat animates it.
  MasteryPath.applyUpdates(updates, { skip: adv ? prevG : null });

  const prevU = updates.find((u) => u.grapheme === prevG);
  pending = { adv, prevG, nextG, prevMastered: !!(prevU && prevU.newly_mastered), name: learnerName };

  resetCaption();
  if (mode === "insight") play(); // already viewing → play now; else await the tap
}

export const AdaptBeat = {
  mount() {
    reduce = prefersReducedMotion();
    speed = location.search.indexOf("demo") !== -1 ? 1.5 : 1;
    on("prepared", (m) => {
      learnerName = m.learner_name || "this reader";
      pending = null;
      resetCaption();
    });
    on("outcome", onOutcome);
    // ModeToggle announces view changes; play a deferred beat on entering Insight.
    document.addEventListener("phono:mode", (e) => {
      mode = e.detail && e.detail.mode;
      if (mode === "insight" && pending) play();
    });
  },
};
