// app/web/static/components/onboarding.js
//
// The warm on-ramp (design-system §14; ui-audit C2). The app must not open on a
// database form. A frightened parent first meets reassurance ("you found the
// right place"), then a few gentle questions, then one story tonight.
//
// It writes its answers into the existing hidden setup inputs and then calls the
// provided onStart() — so the prepare action and backend contract are unchanged.
// Returning readers skip to a one-tap "read with <name> again?".

"use strict";

import { $ } from "../dom.js";

const KEY = "phono.learner";
const AGE_BANDS = [
  { label: "K–2", sub: "ages 5–7", age: 6 },
  { label: "Grades 3–5", sub: "ages 8–10", age: 9 },
  { label: "Grades 6–8", sub: "ages 11–13", age: 12 },
];
const INTERESTS = ["dinosaurs", "space", "animals", "the sea", "trucks", "fairy tales", "sports", "dragons"];

function loadSaved() {
  try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch { return null; }
}
function persist(data) {
  try { localStorage.setItem(KEY, JSON.stringify(data)); } catch { /* private mode */ }
}
function slug(name) {
  return (name || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "reader";
}

export const Onboarding = {
  mount({ onStart }) {
    const host = $("onboarding");
    if (!host) return;

    // The four legacy inputs still carry the values prepare() reads; onboarding
    // fills them. We just keep them out of the parent's face.
    const fields = document.querySelector(".setup-fields");
    if (fields) fields.hidden = true;
    const startBtn = $("start-btn");
    if (startBtn) startBtn.hidden = true;

    const draft = { name: "", age: 6, interest: "" };

    const begin = () => {
      const id = slug(draft.name);
      $("learner-id").value = id;
      $("learner-name").value = draft.name.trim();
      $("learner-age").value = String(draft.age);
      $("learner-interest").value = draft.interest.trim();
      persist({ id, name: draft.name.trim(), age: draft.age, interest: draft.interest.trim(), onboarded: true });
      onStart();
    };

    const saved = loadSaved();
    let step = saved && saved.onboarded ? "return" : "welcome";

    function render() {
      host.innerHTML = "";
      const card = document.createElement("div");
      card.className = "ob-step";

      if (step === "return") {
        card.appendChild(h("p", "ob-eyebrow", "Welcome back"));
        card.appendChild(h("h2", "ob-title", `Ready to read with ${saved.name}?`));
        card.appendChild(h("p", "ob-lede", "Pick up right where you left off — one short story tonight."));
        const row = document.createElement("div"); row.className = "ob-actions";
        const go = btn("primary", `Read with ${saved.name} →`, () => {
          draft.name = saved.name; draft.age = saved.age; draft.interest = saved.interest; begin();
        });
        const fresh = btn("ghost", "Set up a different reader", () => { step = "welcome"; render(); });
        row.append(go, fresh); card.appendChild(row);
      }

      else if (step === "welcome") {
        card.appendChild(h("p", "ob-eyebrow", "You found the right place"));
        card.appendChild(h("h2", "ob-title", "Let's help your reader — starting tonight."));
        card.appendChild(h("p", "ob-lede",
          "This is built on the same approach reading specialists use, in short, calm sessions you can run without any training. We'll start with one story tonight."));
        const row = document.createElement("div"); row.className = "ob-actions";
        row.appendChild(btn("primary", "Let's begin →", () => { step = "who"; render(); }));
        card.appendChild(row);
      }

      else if (step === "who") {
        card.appendChild(h("p", "ob-eyebrow", "Step 1 of 2"));
        card.appendChild(h("h2", "ob-title", "Who are we reading with?"));
        const nameWrap = document.createElement("label"); nameWrap.className = "ob-field";
        nameWrap.appendChild(h("span", "ob-label", "Their first name"));
        const name = document.createElement("input");
        name.type = "text"; name.value = draft.name; name.placeholder = "e.g. Sam";
        name.autocomplete = "off";
        name.addEventListener("input", () => { draft.name = name.value; });
        nameWrap.appendChild(name); card.appendChild(nameWrap);

        card.appendChild(h("span", "ob-label", "About what grade?"));
        const bands = document.createElement("div"); bands.className = "ob-bands";
        AGE_BANDS.forEach((b) => {
          const el = document.createElement("button");
          el.type = "button"; el.className = "ob-band";
          el.setAttribute("aria-pressed", String(draft.age === b.age));
          el.innerHTML = `<b>${b.label}</b><span>${b.sub}</span>`;
          el.addEventListener("click", () => {
            draft.age = b.age;
            bands.querySelectorAll(".ob-band").forEach((x) => x.setAttribute("aria-pressed", "false"));
            el.setAttribute("aria-pressed", "true");
          });
          bands.appendChild(el);
        });
        card.appendChild(bands);

        const row = document.createElement("div"); row.className = "ob-actions";
        const next = btn("primary", "Next →", () => {
          if (!draft.name.trim()) { name.focus(); name.classList.add("ob-need"); return; }
          step = "interest"; render();
        });
        row.appendChild(next); card.appendChild(row);
        setTimeout(() => name.focus(), 0);
      }

      else if (step === "interest") {
        card.appendChild(h("p", "ob-eyebrow", "Step 2 of 2"));
        card.appendChild(h("h2", "ob-title", `What does ${draft.name.trim() || "your reader"} love?`));
        card.appendChild(h("p", "ob-lede", "We'll weave it into their stories. Pick one, or type your own."));
        const chips = document.createElement("div"); chips.className = "ob-chips";
        INTERESTS.forEach((it) => {
          const c = document.createElement("button");
          c.type = "button"; c.className = "ob-chip"; c.textContent = it;
          c.setAttribute("aria-pressed", String(draft.interest === it));
          c.addEventListener("click", () => {
            draft.interest = it; custom.value = "";
            chips.querySelectorAll(".ob-chip").forEach((x) => x.setAttribute("aria-pressed", "false"));
            c.setAttribute("aria-pressed", "true");
          });
          chips.appendChild(c);
        });
        card.appendChild(chips);
        const custom = document.createElement("input");
        custom.type = "text"; custom.className = "ob-custom"; custom.placeholder = "or something else…";
        custom.addEventListener("input", () => {
          draft.interest = custom.value;
          chips.querySelectorAll(".ob-chip").forEach((x) => x.setAttribute("aria-pressed", "false"));
        });
        card.appendChild(custom);

        card.appendChild(h("p", "ob-note",
          "Sessions are about 15 minutes, a few nights a week. Progress is about showing up — not scores. When you're ready for more, a specialist is the best next step, and we'll help you find one."));
        const row = document.createElement("div"); row.className = "ob-actions";
        row.appendChild(btn("ghost", "← Back", () => { step = "who"; render(); }));
        row.appendChild(btn("primary", "Start tonight's story →", () => {
          if (!draft.interest.trim()) draft.interest = "stories";
          begin();
        }));
        card.appendChild(row);
      }

      host.appendChild(card);
    }

    render();
  },
};

function h(tag, cls, text) {
  const el = document.createElement(tag);
  el.className = cls; el.textContent = text; return el;
}
function btn(variant, label, onClick) {
  const b = document.createElement("button");
  b.type = "button"; b.className = variant; b.textContent = label;
  b.addEventListener("click", onClick); return b;
}
