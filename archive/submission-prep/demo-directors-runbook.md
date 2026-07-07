# Director's Runbook — operations only, zero narration

> Sits beside the computer while recording. Everything mechanical lives HERE and only here:
> commands, clicks, keys, files, failure modes, recovery. What to *say* lives in
> `demo-cheat-sheet.md` (on the desk) and `demo-speaker-notes.md` (practice only).
>
> Sources of truth: `demo-runbook.md` (verified click paths + Jul 5 verification log),
> `demo-narration-draft.md` (locked facts), `video-skeleton.md` (shot order/timing).

## Screen ↔ shot map

The presenter docs use 7 screens; older docs use shot numbers. Mapping:

| Screen | Old shot | On screen | Budget |
|---|---|---|---|
| 1 | Shot 0 | Title card (static) | 0:30 |
| 2 | Shot 1a | Reading face + score | ~0:25 |
| 3 | Shot 1b | Kid celebration → Insight face | ~0:45 |
| 4 | Shot 1c | Second read + loop rail | ~0:35 |
| 5 | Shot 3 | Evidence chart PNG | 1:30 |
| 6 | Shot 4 | Book page PNGs | 0:50 |
| 7 | Shot 5 | Architecture / recap card | 0:25 |

Shot 2 (browser-mic voice) is **CUT** (decided Jul 5). Total ≈ 5:00.

---

## One-time setup (per browser profile)

The returning-reader "Read with Ada →" card is gated on `localStorage["phono.learner"]`,
which the on-disk seed never writes. On a fresh profile/incognito you'd get the cold-start
card. Fix once, either way:

- **Option A:** one throwaway onboard typing **Ada** / K–2 / dinosaurs. (`slug("Ada") = ada`,
  so it loads the full seeded profile *with* populated shelf — the "fresh onboard = empty
  shelf" caveat does NOT apply to the name Ada.)
- **Option B:** DevTools console, then reload:
  ```js
  localStorage.setItem('phono.learner', JSON.stringify({id:'ada',name:'Ada',age:6,interest:'dinosaurs',onboarded:true}))
  ```

---

## Pre-flight (before EVERY take)

1. **Restore the seed** — a live take mutates it (verified Jul 5: each session rewrites
   `profiles/ada.json` and appends to the session log; take 2 would open on **ck**, not **wh**):
   ```bash
   cd /Users/tannergriffith/Projects/agy/agy-capstoneproject
   git restore .phono-demo-data
   ```
2. **Boot the server:**
   ```bash
   uv run python -m scripts.tutor_web --data-dir .phono-demo-data --port 8000
   ```
3. **Open exactly this URL:** `http://127.0.0.1:8000/?loop&demo`
   - `loop` → shows the ADK loop rail (Screen 4 beat)
   - `demo` → slows the adapt pop/glow ~1.5× so the camera catches it (verified Jul 5, `adaptBeat.js:95`)
   - These are the only two URL flags.
4. **Motion check (recording trap):** the adapt beat honors OS Reduce Motion AND the in-app
   Calm toggle — either one zeroes every delay and kills the payoff animation. Confirm:
   - macOS System Settings → Accessibility → Display → **Reduce Motion: OFF**
   - In-app **Calm mode: OFF**
5. **Browser zoom 110–125%** (verified at 1920×1080: at 100% the loop-rail sub-labels and
   topbar growth caption are illegible on video). After zooming, check the reading words AND
   the mastery path both fit.
6. **Pre-expand** the operator controls `<details>` ("⌨ Type or use a preset") so there's no
   fumble on camera.
7. Confirm the returning-reader card shows ("Read with Ada →"). If not → One-time setup above.
8. Window management: bookmarks bar hidden, notifications off. No mic needed.

---

## Screen-by-screen operations

### Screen 1 — Title card
- Asset: `artifacts/media/title-card.png` (1920×1080, Reading Room brand). Source
  `artifacts/media/title-card.html` — open full-screen (`F11` / ⌃⌘F) if you prefer a live
  render; PNG and HTML are pixel-identical.
- Full-screen for the whole ~30s, then cut to the browser.

### Screen 2 — Reading face + score
1. Land on `http://127.0.0.1:8000/?loop&demo` → click **"Read with Ada →"**.
2. Reading face: story words, targets gold-underlined. Talk here.
3. Score: expand "⌨ Type or use a preset" (should already be pre-expanded) → click
   **"One miscue"** → footer **"How did it go? ▸"**.
   - **Why "One miscue"** (verified Jun 28) — the only single read that fires ALL the proof:
     - Perfect: acc 1.00, advances wh→ck, but 0 heatmap miscues (nothing to narrate).
     - **One miscue: acc 0.95, 1 red heatmap cell + 1 scaffold cue, AND advances wh→ck.** ← use this.
     - Struggling: acc 0.68, 6 red cells, target holds wh→wh (only for the non-advance branch).
4. **Score from the Reading face, never while sitting in Insight** — see Screen 3.

### Screen 3 — Kid view → Insight face  ⚠ most-practiced moment
1. After scoring, the Session Arc advances (Read together → How it went); child-safe
   celebration shows first. Narrate the kid view.
2. Toggle to Insight: tap **"For grown-ups"** or press **`i`**.
3. **Mechanics (verified Jul 5, `adaptBeat.js`):** when you score from the Reading face the
   adapt beat is **deferred** and plays the moment you enter Insight — you cannot miss it by
   toggling "late," so don't rush. Toggle when ready, then let the ~2s pop → glow → caption
   land in silence.
   - Only failure mode: sitting in Insight *while* scoring — the beat plays immediately and
     you may be mid-sentence. That's why you always score from Reading.
4. The mastered-node "pop" is subtle (scale 1.06 over 0.7s). The narratable payoff is the
   **glow travel + adapt caption**, not the pop.
5. Insight face contents: Why card (planner rationale + review chips), running-record heatmap
   (only visible here), Mastery Path (node pops → coral glow travels → caption resolves).
6. First read advances **wh → ck**.

### Screen 4 — Second read + loop rail
1. Back to Reading: press **`r`**.
2. Click **"One miscue"** again on the new ck book → score → return to Insight (**`i`**).
3. Target advances **ck → qu** (verified chain: wh → ck → qu on strong reads).
4. Loop rail (Plan → Generate → Verify ✓ → Read → Assess → Adapt) is lit because the page
   was opened with `?loop` — horizontal rail directly under the top bar.

### Screen 5 — Evidence chart
- Full-screen `eval/experiments/results/adaptive_vs_static.png`.
- ⚠ Before recording, confirm the committed PNG is the **de-circularized re-run**
  (regen if unsure: `uv run python -m eval.experiments.adaptive_vs_static`).
- Optional: show the regen command in a terminal.

### Screen 6 — Book pages
- Show `results/sample_book/page_01.png` … `page_06.png` ("Sam the Fox", 6 pages).
- Prefer committed PNGs or a **pre-captured Google Doc screen recording** over live `gws`
  at record time.

### Screen 7 — Close
- Architecture loop diagram / recap card + "full offline suite green" line.
- **Count-free** on screen: do NOT show a specific test number (260/267 in older docs are
  both superseded).

---

## Things NOT to click / show

- **"🎤 Read aloud" — never, at any point.** The voice shot is CUT (Jul 5). With unverified
  Gemini Live creds it does NOT error — it hangs on "transcribing…" indefinitely and
  **wedges the whole WebSocket**, so even typed presets stop responding until a page reload.
  The button stays visible on the Reading face; it's scenery.
- Any specific test count (say/show "suite green" only).
- The in-app Calm toggle (kills the animation — see pre-flight motion check).

## Keyboard shortcuts

| Key | Action |
|---|---|
| `i` | Reading → Insight ("For grown-ups") |
| `r` | Insight → Reading |
| `F11` / ⌃⌘F | Full-screen the title card |

---

## Failure modes → recovery

| If this happens | Do this |
|---|---|
| 🎤 clicked by accident | **Reload the page.** Disk state persists, so you resume where you were. |
| Adapt animation doesn't visibly move the target | Cut to the **Shelf/Journey** timeline (🏷 Shelf) — sound-by-sound shift + growth line is the alternate adaptation proof across sessions. |
| `?loop` rail clutters/distracts | Reload without `?loop`; the human Session Arc carries the narrative. |
| DegradeBanner appears (quota/connection) | If filming graceful degradation is intentional, narrate it; otherwise reload and re-take. |
| Server hiccup mid-take | App reboots in ~3s; `--data-dir .phono-demo-data` persists state **mid-take**. (Still `git restore .phono-demo-data` **between** takes.) |
| Live Google Doc stalls (Screen 6) | Fall back to committed page PNGs / pre-captured Doc recording. |
| Cold-start card instead of "Read with Ada →" | localStorage seed missing — One-time setup, then reload. |

---

## Gate checklist (no recording until all checked)

- [ ] App boots against `.phono-demo-data`, `ada` loads via returning-reader card (bootable confirmed Jun 28).
- [ ] Decided returning-`ada` vs fresh-onboard; rehearsed the chosen one ≥3×. (Recommended: returning-`ada`.)
- [x] Voice shot CUT (Jul 5) — typed presets only; never click 🎤 on camera.
- [x] Adapt mechanic verified headless (Jun 28): wh→ck→qu on strong reads; "One miscue" advances + lights heatmap.
- [ ] Live dry run confirms the pop/glow is *visually* legible on the demo machine (headless check proved the data, not the pixels).
- [ ] Reading→Insight toggle rehearsed: score from Reading, toggle, 2s silence.
- [ ] Operator `<details>` pre-expanded (or expanding is part of the rehearsed motion).
- [ ] `adaptive_vs_static.png` confirmed = de-circularized run.
- [ ] Fallback Google Doc screen recording captured (or committed PNGs accepted as the plan).
- [ ] Reduce Motion OFF + Calm mode OFF confirmed on the recording machine.
- [ ] Zoom set 110–125%; words + mastery path both fit.
- [ ] One full stopwatched dry run end-to-end with NO hesitation.

---

## Verification log (inherited)

- **Jun 28 — headless WS replay:** perfect & one-miscue reads advance wh→ck→qu; struggling
  holds (wh→wh). Seeded profile untouched by the check. (Ad-hoc script, not committed; to
  re-verify, replay preset reads through `scripts/tutor_web` against a *copy* of `.phono-demo-data`.)
- **Jul 5 —** seed mutation on live takes confirmed (hence `git restore` between takes);
  localStorage gating confirmed; `?demo` slow-down confirmed (`adaptBeat.js:95`); Reduce
  Motion/Calm trap confirmed; 100% zoom illegibility confirmed at 1920×1080; deferred adapt
  beat on Insight entry confirmed; mic-hang WebSocket wedge confirmed.
- **Remaining:** a full live dry run on the demo machine to confirm the animation and toggle
  timing are visually clean.
