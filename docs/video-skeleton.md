# Video skeleton — ~5 min capstone demo

> **Skeleton only.** Shot list + rough spoken beats + durations. Final narration is written/recorded in
> the Jul 4–5 window. Order follows build-plan.md "Jul 4–5" (build-plan.md:242–244):
> **live web demo first → offline evidence chart for rigor → illustrated book for polish.**
> Browser-mic voice is the *optional* live beat (needs Gemini Live creds); typed presets are the safe fallback.
> Target total ≈ 5:00.
>
> **Authoritative narration:** [`demo-narration-draft.md`](demo-narration-draft.md) is the source of truth for
> spoken lines and the locked choreography (Reading Room redesign: LoopRail, MasteryPath, Read/Insight faces,
> the **wh→ck→qu** adapt chain on the seeded `ada`). This skeleton is the shot/timing scaffold; where the two
> differ, the narration draft wins.

---

## Shot 0 — Cold open / problem (0:00–0:30, ~30s)

- **On screen:** title card (Phono StoryForge) → one line of the problem; optionally a generic/scarce decodable-book stock image.
- **Says (rough):** "Struggling and dyslexic readers are told to read decodable books at their level — but those books are scarce and generic, and nothing watches what the child *misreads* to pick what to practice next. Phono StoryForge closes that loop."
- **Source for claim:** README "The Problem" (README.md:7–9).
- **Risk:** none (static).

---

## Shot 1 — LIVE web demo: the loop adapting (0:30–2:15, ~1:45) ★ the centerpiece

- **On screen:** `scripts/tutor_web.py` in the browser (`uv run python -m scripts.tutor_web --data-dir .phono-demo-data` → http://127.0.0.1:8000), Reading Room redesign. Open the seeded `ada` session. The **LoopRail** narrates the six steps (Plan → Generate → Verify → Read → Assess → Adapt), lighting up as each runs. Read a page (typed/preset input), then on the **Insight face**:
  - miscue **heatmap** lights per word as the read is scored,
  - the **"Why this book?"** card shows the planner's rationale (judge-facing receipt),
  - the **MasteryPath** updates — graphemes as nodes (mastered / current target / in-progress / locked), not animating bars,
  - the **next-target advances** along the seeded chain: **wh → ck → qu** (each strong read masters the current digraph and advances).
  - Do a second read to show the target visibly moving along the chain + persistence across the session.
- **Says (rough):** narrate the loop live — "child reads → every miscue is attributed down to the exact grapheme → mastery updates → the next target just shifted on screen. This is the real production loop, not a mockup — same `prepare`/`record_read` code the experiment exercises." (Final lines: see `demo-narration-draft.md`.)
- **Sources:** README Stage C (README.md:42), build-plan Stage C (build-plan.md:173–192), `demo-narration-draft.md` (locked choreography), demo-runbook.md (verified wh→ck→qu chain).
- **⚠ Risk / pre-Jul-4 rehearsal REQUIRED:** must rehearse `scripts/tutor_web.py` end-to-end on the demo machine — confirm LoopRail + heatmap + MasteryPath + target-advance all fire on the seeded `ada` input sequence, and **copy/restore `.phono-demo-data` before each take** so the wh→ck→qu chain doesn't self-mutate. This is the load-bearing shot; do not record cold.

---

## Shot 2 — (OPTIONAL) browser-mic voice beat (insert within Shot 1, ~20–25s)

- **On screen:** click the 🎤 in the web UI, speak a page aloud, transcript drives the same loop.
- **Says (rough):** "And the child can just *read aloud* — browser mic streams to Gemini Live, the transcript feeds the exact same loop."
- **Source:** build-plan Stage C step 2 (build-plan.md:185–189), README.md:42.
- **⚠ Risk / conditional:** depends on **Gemini Live creds working on the demo machine** at record time. If creds/Live are flaky, CUT this shot and stay on typed presets (the fallback is explicitly fine — README.md:42, build-plan.md:244). Decision must be made *before* recording, not mid-take. Also note: "never-punish" confidence repair is a no-op on the live path today (Live returns no per-word confidence) — don't claim it fires live. (README.md:109)

---

## Shot 3 — Offline evidence chart: rigor (2:15–3:45, ~1:30)

- **On screen:** `eval/experiments/results/adaptive_vs_static.png` (full-screen). Optionally show the one-line regen command in a terminal: `uv run python -m eval.experiments.adaptive_vs_static`.
- **Says (rough):** "Does the adaptation actually help? Same paired, seeded simulated learners, same fixed benchmark probe each session — adaptive vs a fixed scope-and-sequence. n=30, 40 sessions: **probe accuracy +0.06, true mean mastery +0.04, +4.9 WCPM.**"
- **The rigor sub-beat (don't skip):** "And this isn't self-validating — the simulated learner was deliberately built *unlike* what the tutor assumes: logistic/IRT emission with per-grapheme difficulty, no ZPD gate, and it *forgets*. De-circularizing roughly halved the gaps but they stayed positive across all 12 cells of a forgetting × discrimination sweep."
- **Honesty beat (keep it — it reads as credible):** "One place it's a wash: count of skills past a hard 0.95 bar. We log that, we don't hide it."
- **Sources:** README Evidence (README.md:73–79), stage-d doc headline table (stage-d-independent-learner.md:29–55).
- **Risk:** low — chart is committed. ⚠ but confirm the committed PNG reflects the de-circularized re-run before recording (see writeup-skeleton TODO 3e).

---

## Shot 4 — Illustrated book: polish (3:45–4:35, ~50s)

- **On screen:** the sample illustrated book — `results/sample_book/page_01.png … page_06.png` ("Sam the Fox", 6 decodable pages, current illustration style — legacy look), ideally scrolling in the actual Google Doc. Optionally the propose/verify diagram (README.md:50–64).
- **Says (rough):** "Every page is guaranteed decodable — an LLM proposes, deterministic Python verifies: the decodability QA loop won't let an undecodable word ship, a palette verifier proves every illustration stays on-brand, and the Doc is assembled deterministically. The same proposes/verifies discipline, three times. And as of last week it's folded into the live loop, not a separate path."
- **Sources:** README content engine (README.md:46–71), commit e7d815b, build-plan Phase 5 (build-plan.md:99–111).
- **Risk:** low if using committed page PNGs. ⚠ if showing a *live* Google Doc, that needs `gws` creds + render rehearsal — prefer the committed PNGs / a pre-captured Doc screen-recording to de-risk.

---

## Shot 5 — Close (4:35–5:00, ~25s)

- **On screen:** architecture loop diagram (README.md:15–24) or recap card; full offline suite green line.
- **Says (rough):** "One deterministic loop — plan, generate, listen, attribute, update — wired into a real product, proven by a de-circularized study, and now generating illustrated books in the loop. Built on ADK for Agents for Good."
- **Source:** README.md:36, 44, 93–102.
- **Risk:** none.

---

## Timing summary

| Shot | Beat | Dur | Running |
|---|---|---|---|
| 0 | Problem cold open | 0:30 | 0:30 |
| 1 | Live web demo (centerpiece) | 1:45 | 2:15 |
| 2 | (optional) voice — folded into 1 | ~0:20 | (within 1) |
| 3 | Evidence chart + rigor | 1:30 | 3:45 |
| 4 | Illustrated book | 0:50 | 4:35 |
| 5 | Close | 0:25 | 5:00 |

≈ **5:00** with voice cut; if voice beat (Shot 2) is included, trim ~20s from Shot 1's second-read or Shot 4.

---

## Pre-record checklist (do before Jul 4)

- ⚠ **Rehearse `scripts/tutor_web.py` end-to-end** — scripted input sequence that produces a clean visible target advance + bar animation (Shot 1 is load-bearing).
- ⚠ **Decide voice in/out** — test Gemini Live creds on the demo machine; if flaky, commit to typed presets and cut Shot 2 before recording (build-plan.md:244).
- ⚠ **Confirm chart PNG is the de-circularized re-run** (re-run the regen command, eyeball headline numbers).
- TODO: capture a fallback **screen-recording of the Google Doc** (Shot 4) so the demo doesn't depend on live `gws` at record time.
- TODO: pick the demo learner/interest/age + preset reads in advance so the on-screen story is decodable and the adapt is legible.
