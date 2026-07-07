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
| mic "🎤" | Button reads "🎤 Read aloud" | cosmetic only — voice shot is CUT; never click it on camera |
| — | New: **Session Arc** (Tonight's story → Read together → How it went → What's next), **Why card**, **Shelf/Journey** timeline | new assets you can show; not breaking |

---

## Pre-flight (do once, off camera, before every take)

```bash
cd /path/to/phono-storyforge
# Use the pre-seeded demo profile (confirmed: seeded "ada" lives in .phono-demo-data):
uv run python -m scripts.tutor_web --data-dir .phono-demo-data --port 8000
```

- **RESTORE THE SEED before EVERY take (verified Jul 5: a live take mutates it):** each session
  rewrites `profiles/ada.json` and appends to the session log, so take 2 would open on **ck**, not
  **wh**, desyncing the narration. The seed is git-tracked — between takes run:
  ```bash
  git restore .phono-demo-data
  ```
- **SEED THE BROWSER once per browser profile (verified Jul 5):** the "Read with Ada →"
  returning-reader card is gated on `localStorage["phono.learner"]`, which the on-disk seed never
  writes — on a fresh profile/incognito you get the cold-start card instead. Either do one
  throwaway onboard typing **Ada** / K–2 / dinosaurs (`slug("Ada") = ada`, so it loads the full
  seeded profile *with* populated shelf — the "fresh onboard = empty shelf" caveat does NOT apply
  to the name Ada), or paste in DevTools and reload:
  ```js
  localStorage.setItem('phono.learner', JSON.stringify({id:'ada',name:'Ada',age:6,interest:'dinosaurs',onboarded:true}))
  ```
- Open **http://127.0.0.1:8000/?loop&demo**  ← `loop` shows the ADK loop rail for the architecture beat; `demo` slows the adapt pop/glow ~1.5× so the camera catches each frame (verified Jul 5: `adaptBeat.js:95`). These are the only two URL flags.
- **Motion check (verified Jul 5 — recording trap):** the adapt beat honors OS *Reduce Motion*
  AND the in-app Calm toggle (`motionReduced()` zeroes every delay). Confirm macOS
  System Settings → Accessibility → Display → **Reduce Motion is OFF** and the app's Calm mode
  is OFF, or the pop/glow payoff will not animate on camera.
- Browser zoom **110–125%** (verified via 1920×1080 headless capture Jul 5: at 100% the
  loop-rail sub-labels and topbar growth caption are illegible on video; the six step names are
  fine). Check reading words + mastery path both fit after zooming.
- ⚠ **The mastered-node "pop" is subtle** (scale 1.06 over 0.7s) — `?demo` slows it 1.5× and
  zoom helps, but treat the **glow travel + adapt caption** as the narratable payoff, not the pop.
- **Pre-expand** the operator controls `<details>` — scoring is via preset (voice shot CUT, see Shot 2), so there's no fumble on camera.
- Confirm the seeded **`ada`** profile loads (returning-reader path) OR plan to onboard fresh (cold-start path) — pick ONE and rehearse it.
- Window-manage: hide bookmarks bar, notifications off. (No mic needed — voice shot is CUT.)

✅ **VERIFIED Jun 28 (headless WS replay against a copy of `.phono-demo-data`):** the seeded `ada` advances on every strong read. Known-good target chain: **wh → ck → qu** (each read masters the current digraph and advances). The seeded profile was NOT mutated by this check.

---

## Shot-by-shot click choreography

### Shot 0 — Cold open / problem (~0:30)
Static title card / narration only. No UI.
- **Asset (created Jul 5): `artifacts/media/title-card.png`** (1920×1080, Reading Room brand,
  real Literata 600). Source: `artifacts/media/title-card.html` — open it full-screen in the
  browser (`F11` / ⌃⌘F) if you prefer a live render; PNG and HTML are pixel-identical.
- Display it full-screen for the whole ~30s narration, then cut to the browser for Shot 1.

---

### Shot 1 — LIVE web demo: the loop adapting (~1:45) ★ centerpiece

**Click path (returning-reader `ada`):**
1. Land on **http://127.0.0.1:8000/?loop&demo**. If returning-reader prompt shows → **"Read with Ada →"**.
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

⚠ **Most-practiced moment:** the Reading→Insight toggle. Mechanics verified Jul 5
(`adaptBeat.js`): when you score from the Reading face, the adapt beat is **deferred** and plays
the moment you enter Insight — you cannot miss it by toggling "late," so don't rush. Toggle
when you're ready, then **let the ~2s pop → glow → caption land in silence** before speaking.
(Only failure mode: sitting in Insight *while* scoring — the beat plays immediately and you may
be mid-sentence. Score from the Reading face.)

---

### Shot 2 — CUT (was: browser-mic voice)

**Decision made Jul 5: the voice shot is OUT.** Typed presets are the documented, approved
path — narrate "I'm scoring a typical read from the keyboard so it's repeatable on camera" and
move on. Rationale: Gemini Live is unverified on the demo machine and its failure mode is
unacceptable on camera (verified Jul 5): dead creds do NOT error — the UI hangs on
"transcribing…" indefinitely and **wedges the whole WebSocket**, so even typed presets stop
responding until a page reload.

⚠ **Do not click "🎤 Read aloud" at any point during recording.** The button stays visible on
the Reading face — it's scenery, not part of the demo. Shot numbering below (3–5) is unchanged
to keep cross-references stable.

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
| "🎤 Read aloud" clicked by accident (voice shot is CUT) | **Reload the page** — a mic click with dead creds hangs on "transcribing…" and wedges the WebSocket, so typed presets stop responding; disk state persists, so you resume where you were |
| Adapt animation doesn't visibly move the target | Cut to the **Shelf/Journey** timeline (🏷 Shelf) — sound-by-sound shift + growth line is an alternate adaptation proof across sessions |
| `?loop` rail clutters / distracts | Reload without `?loop`; the human Session Arc carries the narrative |
| DegradeBanner appears (quota/connection) | If filming graceful-degradation is intentional, narrate it; otherwise reload and re-take |
| Server hiccup mid-take | App reboots in ~3s; keep `--data-dir .phono-demo-data` so state persists **mid-take** (but `git restore .phono-demo-data` **between** takes — see pre-flight) |
| Illustrated book live Doc stalls | Fall back to committed page PNGs / pre-captured Doc recording |

---

## Rehearsal checklist (gate before any recording)

- [ ] App boots against `.phono-demo-data` and `ada` loads (returning path) — **confirmed bootable Jun 28**.
- [ ] Decided: returning-`ada` vs fresh-onboard. Rehearsed the chosen one ≥3×.
- [x] Voice shot CUT (decided Jul 5) — typed presets only; never click 🎤 on camera.
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
