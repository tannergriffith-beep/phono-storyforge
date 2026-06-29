# Demo runbook — live recording script (current UI, post-Reading-Room rebrand)

> **Status: rough working doc for rehearsal.** Supersedes the on-screen choreography in
> `video-skeleton.md` Shot 1 (written before the Jun 27 rebrand, commit `d1ab921`).
> The skeleton's shot ORDER, narration beats, and timing budget still hold — use it for *what to say*.
> Use THIS doc for *what to click*, because the UI moved underneath the skeleton.
> **Do not record cold.** Rehearse the marked ⚠ moments until smooth.

---

## What changed under the skeleton (why this doc exists)

The "Reading Room" rebrand (Jun 27) changed exactly the things Shot 1 depends on:

| Skeleton said | Current reality | Demo consequence |
|---|---|---|
| "mastery **bars** animate" | Mastery **Path**: graphemes are *nodes* on a sequence; newly-mastered node "pops", coral glow travels to next target | Narration "bars fill" is wrong — say "the path lights up / the target moves" |
| heatmap lights per word, on screen | Heatmap lives in the **Insight face only**; child sees a clean celebration | Must tap **"For grown-ups"** to reveal the heatmap on camera |
| presets visible | Presets collapsed inside `<details>` "⌨ Type or use a preset" | Must **expand it once** before scoring (or pre-expand off-camera) |
| loop rail (Plan→…→Adapt) visible | Hidden unless `?loop` URL flag or `localStorage.phono.devLoop=1` | For the ADK-loop visual, **open with `?loop`** |
| mic "🎤" | Button reads "🎤 Read aloud" | cosmetic only |
| — | New: **Session Arc** (Tonight's story → Read together → How it went → What's next), **Why card**, **Shelf/Journey** timeline | new assets you can show; not breaking |

---

## Pre-flight (do once, off camera, before every take)

```bash
cd /Users/tannergriffith/Projects/agy/agy-capstoneproject
# Use the pre-seeded demo profile so the shelf/history isn't empty and the adapt is legible.
# NOTE: confirm which data-dir the seeded "ada" lives in (.phono-demo-data) and point at it:
uv run python -m scripts.tutor_web --data-dir .phono-demo-data --port 8000
```

- Open **http://127.0.0.1:8000/?loop**  ← the `?loop` flag shows the ADK loop rail for the architecture beat.
- Browser zoom so reading words + mastery path are both legible at recording resolution.
- **Pre-expand** the operator controls `<details>` if you're scoring via preset, so there's no fumble on camera. (Decide: preset path vs. live mic — see Shot 2 decision.)
- Confirm the seeded **`ada`** profile loads (returning-reader path) OR plan to onboard fresh (cold-start path) — pick ONE and rehearse it. Returning-reader = faster, shelf already populated; fresh onboard = shows the warm onboarding flow but empty shelf.
- Window-manage: hide bookmarks bar, notifications off, mic permission pre-granted.

✅ **VERIFIED Jun 28 (headless WS replay against a copy of `.phono-demo-data`):** the seeded `ada` advances on every strong read. Known-good target chain: **wh → ck → qu** (each read masters the current digraph and advances). The seeded profile was NOT mutated by this check.

---

## Shot-by-shot click choreography

### Shot 0 — Cold open / problem (~0:30)
Static title card / narration only. No UI. (Unchanged from skeleton.)

---

### Shot 1 — LIVE web demo: the loop adapting (~1:45) ★ centerpiece

**Click path (returning-reader `ada`):**
1. Land on **http://127.0.0.1:8000/?loop**. If returning-reader prompt shows → **"Read with Ada →"**.
   - (Fresh path instead: type name → tap age band → tap an interest chip → **"Start tonight's story →"**.)
2. **Reading face** appears: story words, target graphemes softly gold-underlined. Narrate the problem→loop framing here.
3. Score the read:
   - **Preset path (safe, recommended): use "One miscue".** Expand **"⌨ Type or use a preset"** → click **"One miscue"** → footer **"How did it go? ▸"**.
   - **Why "One miscue" is the right pick (VERIFIED Jun 28):** it's the only single read that fires ALL the visual proof at once —
     - **Perfect read:** acc 1.00, advances wh→ck, but **0 heatmap miscues** (nothing to narrate in the running record).
     - **One miscue:** acc 0.95, **1 red heatmap cell + 1 scaffold cue**, AND advances wh→ck. ← shows attribution + adapt together.
     - **Struggling:** acc 0.68, 6 red cells, but the target **holds** (wh→wh, "keep practicing") — use only if you want to demo the non-advance branch.
4. Session Arc advances (Read together → How it went). Child-safe celebration shows first.
5. ⚠ **Tap "For grown-ups"** (mode toggle; keyboard `i`) to reveal the **Insight face**:
   - **Why card** = planner rationale + review chips (narrate "it chose this book *because*…").
   - **Running-record heatmap** = miscues color-coded (only visible here).
   - **Mastery Path** = newly-mastered node pops → coral glow travels to next target → **adapt caption** resolves ("ready for a new sound — next we'll practice /x/").
6. **Second read** to show the target *move again*: back to Reading (`r`), click **"One miscue"** again on the new ck book, return to Insight → target advances **ck → qu**. This is the "loop adapted, not a mockup" proof. (First read advances wh→ck; second ck→qu — verified chain.)
7. If showing the ADK loop: the **loop rail** (Plan→Generate→Verify✓→Read→Assess→Adapt) is lit because you opened with `?loop`.

**Narration:** use skeleton Shot 1 beats BUT replace "mastery bars animate" → "the mastery path lights up and the target moves to the next sound."

⚠ **Most-practiced moment:** the Reading→Insight toggle + landing on the adapt animation at the right time. The animation fires on the `outcome` event; if you toggle too early you'll miss the pop/glow. Rehearse the timing.

---

### Shot 2 — (OPTIONAL) browser-mic voice (~20s, folded into Shot 1)

- Click **"🎤 Read aloud"**, speak the page, transcript drives the same loop.
- ⚠ **Decision before recording:** test Gemini Live creds on the demo machine. If flaky → CUT, stay on presets (explicitly fine). Don't discover this mid-take.
- Don't claim never-punish confidence repair "fires live" — it's a no-op on the Live path (no per-word confidence).

---

### Shot 3 — Offline evidence chart (~1:30)
Full-screen `eval/experiments/results/adaptive_vs_static.png`. Narration unchanged (skeleton Shot 3). ⚠ confirm the PNG is the de-circularized re-run before recording.

---

### Shot 4 — Illustrated book (~0:50)
Show `results/sample_book/page_01.png … page_06.png`. Prefer committed PNGs or a **pre-captured Google Doc screen-recording** over live `gws` at record time. Narration unchanged (skeleton Shot 4).

---

### Shot 5 — Close (~0:25)
Architecture loop + "full offline suite green" (count-free — don't show a specific number; older skeletons say 260/267, both now superseded). Narration unchanged.

---

## Recovery plans (likely failures → what to do on camera)

| If this fails | Recover by |
|---|---|
| Voice/Gemini Live dead | Stay on typed presets — it's the documented fallback; don't apologize, just narrate "typed here for reproducibility" |
| Adapt animation doesn't visibly move the target | Cut to the **Shelf/Journey** timeline (🏷 Shelf) — sound-by-sound shift + growth line is an alternate adaptation proof across sessions |
| `?loop` rail clutters / distracts | Reload without `?loop`; the human Session Arc carries the narrative |
| DegradeBanner appears (quota/connection) | If filming graceful-degradation is intentional, narrate it; otherwise reload and re-take |
| Server hiccup mid-take | App reboots in ~3s; keep `--data-dir .phono-demo-data` so state persists |
| Illustrated book live Doc stalls | Fall back to committed page PNGs / pre-captured Doc recording |

---

## Rehearsal checklist (gate before any recording)

- [ ] App boots against `.phono-demo-data` and `ada` loads (returning path) — **confirmed bootable Jun 28**.
- [ ] Decided: returning-`ada` vs fresh-onboard. Rehearsed the chosen one ≥3×.
- [ ] Decided: voice in/out. If in, Gemini Live verified on demo machine.
- [x] **Adapt mechanic verified headless (Jun 28):** wh→ck→qu on strong reads; "One miscue" advances + lights heatmap. Still confirm it's *visually* legible on screen during a live dry run.
- [ ] Toggle timing (Reading→Insight) lands on the adapt animation, not before it.
- [ ] Operator `<details>` pre-expanded or expanding it is part of the rehearsed motion.
- [ ] `adaptive_vs_static.png` confirmed = de-circularized run.
- [ ] Fallback Google Doc screen-recording captured.
- [ ] Full dry run completed end-to-end with NO hesitation before any real take.

---

## Verification log
- **Jun 28 — headless WS replay (done).** Replayed prepare→read against a copy of `.phono-demo-data`. Perfect & One-miscue reads advance wh→ck→qu; Struggling holds (wh→wh). One-miscue is the recommended demo read (heatmap + scaffold + advance in one). Seeded profile untouched. Verified via a one-off ad-hoc WS-replay script (not committed — scratch only); to re-verify, replay the preset reads through `scripts/tutor_web` against a *copy* of `.phono-demo-data`.
- **Remaining (needs a human + a screen):** a full live dry run on the demo machine to confirm the node-pop / glow-travel animation and the Reading→Insight toggle timing are *visually* clean — the headless check proves the data, not the pixels.
