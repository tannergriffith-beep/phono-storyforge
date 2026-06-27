// app/web/static/components/readerSettings.js
//
// Reader Settings — "the decode is sacred" made operable (design-system §2.1/§15.3).
//
// A child must never be stuck with a typeface, size, or spacing that doesn't
// decode for them. This control lets the grown-up choose the reading typeface
// (a storybook serif default, or a research-backed easy-reading sans — Lexend),
// the text size, the letter/word/line spacing, and a "calm" toggle that quiets
// motion. Choices persist per browser in localStorage and apply by setting CSS
// custom properties the .reading-page consumes (see tokens.css + style.css).
//
// No backend, no payload change — purely a presentation-layer accessibility aid.

"use strict";

import { $ } from "../dom.js";

const KEY = "phono.reader";
// Default to the easy-reading sans (Lexend) for the child's passage — the
// decode is sacred. The storybook serif remains a one-tap choice here.
const DEFAULTS = { font: "sans", size: 1, spacing: "normal", calm: false };
const SIZES = [1, 1.15, 1.3, 1.5]; // multipliers on --fs-read

function load() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || "{}") };
  } catch {
    return { ...DEFAULTS };
  }
}

function save(s) {
  try { localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* private mode */ }
}

function apply(s) {
  const root = document.documentElement.style;
  root.setProperty("--reading-font", s.font === "sans" ? "var(--font-read-sans)" : "var(--font-read)");
  root.setProperty("--reading-scale", String(s.size));
  if (s.spacing === "roomy") {
    root.setProperty("--reading-letter-spacing", "0.06em");
    root.setProperty("--reading-word-spacing", "0.18em");
    root.setProperty("--reading-line-height", "2.15");
  } else {
    root.setProperty("--reading-letter-spacing", "0.01em");
    root.setProperty("--reading-word-spacing", "0.06em");
    root.setProperty("--reading-line-height", "1.85");
  }
  document.body.classList.toggle("reader-calm", !!s.calm);
}

let settings = load();

function seg(legend, name, options, current, onPick) {
  const fs = document.createElement("fieldset");
  fs.className = "rs-group";
  const lg = document.createElement("legend");
  lg.textContent = legend;
  fs.appendChild(lg);
  const row = document.createElement("div");
  row.className = "rs-seg";
  options.forEach((opt) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "rs-opt";
    b.textContent = opt.label;
    b.setAttribute("aria-pressed", String(opt.value === current));
    b.addEventListener("click", () => {
      onPick(opt.value);
      row.querySelectorAll(".rs-opt").forEach((x) => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
    });
    row.appendChild(b);
  });
  fs.appendChild(row);
  return fs;
}

function update(patch) {
  settings = { ...settings, ...patch };
  save(settings);
  apply(settings);
}

export const ReaderSettings = {
  mount() {
    apply(settings); // apply persisted prefs on every load, before first render

    const host = $("reader-settings");
    if (!host) return;
    host.innerHTML = "";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "rs-toggle ghost";
    toggle.innerHTML = '<span aria-hidden="true">Aa</span> Reading settings';
    toggle.setAttribute("aria-expanded", "false");

    const panel = document.createElement("div");
    panel.className = "rs-panel";
    panel.setAttribute("role", "group");
    panel.setAttribute("aria-label", "Reading settings");
    panel.hidden = true;

    panel.appendChild(
      seg("Typeface", "font",
        [{ label: "Storybook", value: "serif" }, { label: "Easy-reading", value: "sans" }],
        settings.font, (v) => update({ font: v }))
    );

    // Text size as A− / A+ around a live sample.
    const sizeFs = document.createElement("fieldset");
    sizeFs.className = "rs-group";
    const sizeLg = document.createElement("legend");
    sizeLg.textContent = "Text size";
    sizeFs.appendChild(sizeLg);
    const sizeRow = document.createElement("div");
    sizeRow.className = "rs-seg";
    const minus = document.createElement("button");
    minus.type = "button"; minus.className = "rs-opt"; minus.textContent = "A−";
    minus.setAttribute("aria-label", "Smaller text");
    const sample = document.createElement("span");
    sample.className = "rs-size-label"; sample.setAttribute("aria-live", "polite");
    const plus = document.createElement("button");
    plus.type = "button"; plus.className = "rs-opt"; plus.textContent = "A+";
    plus.setAttribute("aria-label", "Bigger text");
    const showSize = () => {
      const idx = SIZES.indexOf(settings.size);
      sample.textContent = `${Math.round(settings.size * 100)}%`;
      minus.disabled = idx <= 0;
      plus.disabled = idx >= SIZES.length - 1;
    };
    minus.addEventListener("click", () => {
      const idx = Math.max(0, SIZES.indexOf(settings.size) - 1);
      update({ size: SIZES[idx] }); showSize();
    });
    plus.addEventListener("click", () => {
      const idx = Math.min(SIZES.length - 1, SIZES.indexOf(settings.size) + 1);
      update({ size: SIZES[idx] }); showSize();
    });
    sizeRow.append(minus, sample, plus);
    sizeFs.appendChild(sizeRow);
    panel.appendChild(sizeFs);
    showSize();

    panel.appendChild(
      seg("Spacing", "spacing",
        [{ label: "Normal", value: "normal" }, { label: "Roomy", value: "roomy" }],
        settings.spacing, (v) => update({ spacing: v }))
    );

    const calmLabel = document.createElement("label");
    calmLabel.className = "rs-calm";
    const calm = document.createElement("input");
    calm.type = "checkbox"; calm.checked = !!settings.calm;
    calm.addEventListener("change", () => update({ calm: calm.checked }));
    calmLabel.append(calm, document.createTextNode(" Calm mode (less movement)"));
    panel.appendChild(calmLabel);

    toggle.addEventListener("click", () => {
      const open = panel.hidden;
      panel.hidden = !open;
      toggle.setAttribute("aria-expanded", String(open));
    });
    // Close on outside click / Escape.
    document.addEventListener("click", (e) => {
      if (!host.contains(e.target) && !panel.hidden) {
        panel.hidden = true; toggle.setAttribute("aria-expanded", "false");
      }
    });
    // Escape closes from anywhere while open — the toggle keeps focus after it
    // opens the panel, so a panel-scoped listener would never fire (mirrors the
    // document-level outside-click handler above).
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !panel.hidden) {
        panel.hidden = true; toggle.setAttribute("aria-expanded", "false"); toggle.focus();
      }
    });

    host.append(toggle, panel);
  },
};
