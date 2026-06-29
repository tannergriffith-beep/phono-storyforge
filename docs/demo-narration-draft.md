# Demo narration — ROUGH FIRST DRAFT (edit Jul 4–5)

> **Intentionally ugly.** Spoken beats only, timed to ≈5:00. Words to *say*, matched to the
> VERIFIED runbook click-path (`docs/demo-runbook.md`), not the stale Shot-1 choreography in
> `video-skeleton.md`. Placeholders `[SCREENSHOT:…]` / `[CITE:…]` / `TODO:` are deliberate.
> Tone target: the "knowledgeable neighbor" — warm, plain, honest, never salesy (`voice-lexicon.md`).
> Shot order + timing follow `video-skeleton.md`; UI choreography follows the runbook.
> NUMBERS LOCKED: **267 tests**; adapt chain **wh→ck→qu** via **"One miscue"**; evidence **+0.06 acc / +0.04 mean mastery / +4.9 WCPM**.
> DO NOT say the never-punish confidence repair "fires live" — it's a no-op on the Gemini Live path.

---

## Shot 0 — Cold open / problem (0:00–0:30, ~30s)
**On screen:** title card "Phono StoryForge" → one problem line. [SCREENSHOT: title card] (optional scarce-decodable-book stock image)

**Say (rough):**
- "If your child is dyslexic or just struggling to read, you get one piece of advice: read decodable books at their level."
- "Two problems. One — those books are scarce and generic; the right mix of phonics level, age, and interests for *your* kid basically doesn't exist on a shelf."
- "Two — nothing is watching *what* they misread to decide what to practice next. There's no loop."
- "Phono StoryForge closes that loop." [CITE: README "The Problem" README.md:7–9]
- TODO: pick ONE crisp closing clause — "...generates the book, listens to the read, and moves the target itself."

---

## Shot 1 — LIVE web demo: the loop adapting (0:30–2:15, ~1:45) ★ centerpiece
**On screen:** browser at `http://127.0.0.1:8000/?loop`, seeded **`ada`** returning-reader profile.
Reading face → score "One miscue" → "For grown-ups" → Insight face → second read.
**(post-rebrand UI: mastery is a node PATH, heatmap lives in the Insight face, loop rail visible because of `?loop`)**

**Say (rough) — as you land + start the read:**
- "This is the actual product, running live — not a mockup. Same code the experiment later runs."
- "Here's Ada, a returning reader. Tonight's story is built from the sounds she's ready for — the target sounds are softly underlined." [SCREENSHOT: Reading face, gold-underlined graphemes]
- "She reads the page aloud." (Click: expand "⌨ Type or use a preset" → **"One miscue"** → "How did it go? ▸")
- TODO: keep it honest that we're scoring via a typed preset for reproducibility — "I'm scoring a typical read here so it's repeatable on camera."

**Say (rough) — after scoring, before toggling:**
- "First she gets the kid view — a clean win, no scores, no red ink." (Session Arc: Read together → How it went)

**Say (rough) — tap "For grown-ups" (key `i`), Insight face appears:**
- "Now the grown-up view — this is where the loop shows its work."
- "**Why card:** it didn't pick this story at random — here's the reason it chose this sound and this book." [SCREENSHOT: Why card] [CITE: planner rationale, README.md:15–24]
- "**Running record:** every miscue is attributed down to the exact sound she missed — that one red cell is the grapheme she stumbled on, not just 'one word wrong.'" [SCREENSHOT: heatmap, 1 red cell]
- "**Mastery path:** watch the path — the sound she just nailed pops, and the glow travels to the next target. On screen: she's ready for a new sound."
- ⚠ TIMING: the pop/glow fires on the `outcome` event — toggle AFTER it, not before, or you miss it. (runbook ⚠)
- "So in one read: we attributed the miscue, updated what she knows, and moved tomorrow's target — **wh → ck**."

**Say (rough) — second read, to prove it's a loop not a one-shot:**
- "Do it once more on the new book." (Back to Reading `r` → "One miscue" again → back to Insight)
- "Target moves again — **ck → qu**. The loop adapted twice, live. That's the whole thesis in fifteen seconds."
- "And the rail along the [edge TODO: confirm position] — Plan, Generate, Verify, Read, Assess, Adapt — that's the ADK loop you just watched fire." (visible because we opened with `?loop`)

**RUNBOOK NOTE:** if the adapt animation doesn't visibly move → cut to 🏷 Shelf/Journey timeline (sound-by-sound shift across sessions) as the alternate adapt proof.

---

## Shot 2 — (OPTIONAL) browser-mic voice (~20s, folded into Shot 1)
**On screen:** click "🎤 Read aloud", speak the page, transcript drives the same loop.

**Say (rough):**
- "She doesn't have to type — she can just *read aloud*. Browser mic streams to Gemini Live, the transcript feeds the exact same loop." [CITE: build-plan Stage C, README.md:42]
- ⚠ DECISION BEFORE RECORDING: test Gemini Live creds on the demo machine. Flaky → CUT, stay on presets, narrate "typed here for reproducibility." Don't discover mid-take.
- DO NOT say the never-punish confidence repair fires live — it's a no-op on the Live path (no per-word confidence). [CITE: README.md:109]

---

## Shot 3 — Offline evidence chart: rigor (2:15–3:45, ~1:30)
**On screen:** full-screen `eval/experiments/results/adaptive_vs_static.png`. (optional: regen command in terminal)

**Say (rough) — the result:**
- "Does adapting actually help, or does it just look clever? We tested it."
- "Same paired, seeded simulated learners. Same fixed benchmark probe every session. Adaptive — picks each session's target from the child's estimate — versus a fixed scope-and-sequence that ignores the evidence."
- "n=30, 40 sessions: **probe accuracy +0.06, true mean mastery +0.04, +4.9 words-correct-per-minute.**" [SCREENSHOT: chart headline]

**Say (rough) — the rigor sub-beat (DON'T skip):**
- "And we didn't let it grade its own homework. The simulated learner was built deliberately *unlike* what the tutor assumes — a logistic/IRT reader with per-sound difficulty, no prerequisite gate, and it *forgets*."
- "De-circularizing roughly halved the gaps — but they stayed positive across all 12 cells of a forgetting-by-difficulty sweep." [CITE: stage-d-independent-learner.md:29–55]

**Say (rough) — honesty beat (KEEP — reads as credible):**
- "One place it's a wash: the count of sounds pushed past a hard 0.95 bar. We log that in the CSV. We don't hide it." [CITE: README.md:79]

**RUNBOOK ⚠:** confirm the committed PNG is the de-circularized re-run before recording.

---

## Shot 4 — Illustrated book: polish (3:45–4:35, ~50s)
**On screen:** `results/sample_book/page_01.png … page_06.png` ("Sam the Fox", 6 pages). Prefer committed PNGs or a pre-captured Doc screen-recording over live `gws`. [SCREENSHOT: book pages]

**Say (rough):**
- "Every page is guaranteed made-from-sounds-they-know. An LLM proposes the words; deterministic Python verifies."
- "Three times, same discipline: a decodability check that won't let an undecodable word ship, a palette verifier that proves every illustration stays on-brand, and a Doc assembled deterministically." [CITE: README content engine README.md:46–71]
- "LLM proposes, code verifies — three guardrails that halt instead of quietly shipping something wrong."
- "And as of last week, this is folded into the live loop — not a separate path." [CITE: commit e7d815b]

**RUNBOOK ⚠:** if a live Doc stalls → fall back to committed page PNGs / pre-captured recording.

---

## Shot 5 — Close (4:35–5:00, ~25s)
**On screen:** architecture loop diagram / recap card; "**267 tests green**" line. [SCREENSHOT: loop diagram] [CITE: README.md:15–24]

**Say (rough):**
- "One deterministic loop — plan, generate, listen, attribute, update — wired into a real product."
- "Proven by a de-circularized study, and now generating illustrated books inside that same loop."
- "**267 offline unit tests green.** Built on ADK, for Agents for Good."
- TODO: pick the single closing line that lands — lead candidate: "A five-minute win beats a fifteen-minute fight — at scale."

---

## Timing check
| Shot | Beat | Dur | Running |
|---|---|---|---|
| 0 | Problem | 0:30 | 0:30 |
| 1 | Live demo (centerpiece) | 1:45 | 2:15 |
| 2 | (opt) voice — within 1 | ~0:20 | (in 1) |
| 3 | Evidence + rigor | 1:30 | 3:45 |
| 4 | Illustrated book | 0:50 | 4:35 |
| 5 | Close | 0:25 | 5:00 |

≈ **5:00** with voice cut. If Shot 2 included, trim ~20s from Shot 1 second-read or Shot 4.
TODO: read aloud with a timer Jul 4 — Shot 1 narration above is dense, likely needs trimming to fit 1:45 around the clicks.
