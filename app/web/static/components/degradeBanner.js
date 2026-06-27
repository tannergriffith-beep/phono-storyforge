// app/web/static/components/degradeBanner.js
//
// DEGRADE BANNER (archive/legacy-design/DESIGN.md (legacy, archived) §9) — the one graceful-degradation surface.
// Voice/Live-quota loss, illustration-pipeline failures, and connection drops
// used to surface only as plain status text inside the Setup card (#conn-status)
// — which disappears once a session starts. This promotes them to a dismissible
// banner that stays visible across the whole session.
//
// It owns no state beyond visibility; it's a pure sink for two signals:
//   - `error` WS messages (server-side soft failures), and
//   - `phono:connection` CustomEvents dispatched by ws.js on open/close/error.
// A fresh `prepared` payload means the loop is healthy again, so we clear.

"use strict";

import { $ } from "../dom.js";
import { on } from "../ws.js";

let bannerEl, msgEl, iconEl, dismissBtn;

// Calm marks, never an alarm triangle (design-system §13).
const ICON = { warn: "ⓘ", err: "ⓘ", ok: "✓" };

function show(message, severity = "warn") {
  if (!bannerEl || !message) return;
  msgEl.textContent = message;
  iconEl.textContent = ICON[severity] || ICON.warn;
  bannerEl.dataset.severity = severity;
  bannerEl.hidden = false;
}

function clear() {
  if (!bannerEl) return;
  bannerEl.hidden = true;
  msgEl.textContent = "";
}

export const DegradeBanner = {
  mount() {
    bannerEl = $("degrade-banner");
    if (!bannerEl) return;
    msgEl = bannerEl.querySelector(".degrade-msg");
    iconEl = bannerEl.querySelector(".degrade-icon");
    dismissBtn = bannerEl.querySelector(".degrade-dismiss");
    dismissBtn.addEventListener("click", clear);

    // Server-side soft failures (voice/Live quota, illustration pipeline).
    on("error", (m) => show(m.message, "err"));

    // Connection loss must stay visible after the Setup card is hidden.
    document.addEventListener("phono:connection", (e) => {
      const d = e.detail || {};
      if (d.ok) clear();
      else show(d.text || "We lost the connection for a moment — refresh if it doesn't come back.", "err");
    });

    // The loop is running again — drop any stale notice.
    on("prepared", clear);
  },
  show,
  clear,
};
