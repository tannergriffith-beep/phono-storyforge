// app/web/static/dom.js
//
// Tiny DOM helpers shared across the vanilla-JS modules. No framework — these
// are the only abstractions over the document the rest of the app needs.

"use strict";

/** getElementById shorthand. */
export const $ = (id) => document.getElementById(id);

/** Clamp 0..1 and format as a width/percent string ("42.0%"). */
export const pct = (x) => (Math.max(0, Math.min(1, x)) * 100).toFixed(1) + "%";

/** A fluency stat tile (value over uppercase key). */
export const stat = (v, k) =>
  `<div class="stat"><div class="v">${v}</div><div class="k">${k}</div></div>`;

/** True when the user has asked the OS to reduce motion (DESIGN §10.4/§11). */
export const prefersReducedMotion = () =>
  !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
