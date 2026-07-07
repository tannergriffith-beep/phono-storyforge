# Full Recording Script — say + do, per screen

> Merges `demo-speaker-notes.md` (narration) + `demo-directors-runbook.md` (clicks/keys) into one
> document. Everything you need for a take is on this page — you shouldn't need to flip between
> docs while rolling. Total runtime ≈ 5:00.
>
> **Voice:** the knowledgeable neighbor. Warm, plain, honest.
>
> **Never say:** a specific test count · "the mastery bars fill" (say "the path lights up" /
> "the target moves") · that confidence repair "fires live" · the word "story" for the in-app
> reading (that's always a **book**; "story" is reserved for Screen 6's illustrated export).
>
> **Rule that beats all others:** silence is a feature. When the adapt animation plays, say
> nothing for ~2 seconds. Then speak.

---

## Pre-flight (before EVERY take)

```bash
cd /Users/tannergriffith/Projects/agy/agy-capstoneproject
git restore .phono-demo-data
uv run python -m scripts.tutor_web --data-dir .phono-demo-data --port 8000
```

- Open **`http://127.0.0.1:8000/?loop&demo`**
- Reduce Motion: OFF (macOS) · in-app Calm mode: OFF
- Browser zoom 110–125%
- Pre-expand "⌨ Type or use a preset"
- Confirm "Read with Ada →" shows (returning-reader). If cold-start card shows instead, run
  the one-time `localStorage` seed (see `demo-directors-runbook.md`) and reload.
- Bookmarks bar hidden, notifications off. No mic needed — never click "🎤 Read aloud."

---

## Screen 1 — Title card
**Budget: 0:30 | Running: 0:30**

**On screen:** `artifacts/media/title-card.png`, full-screen (or `F11` the `.html` source).

**Do:** Nothing else — static card for the whole 30s, then cut to the browser.

**Say:**
> "If your child struggles to read, you get one piece of advice: decodable books, at their level."

*(pause)*

> "Two problems. The right book — your kid's phonics level, age, and interests — basically doesn't exist on a shelf. And nothing is watching *what* they misread to decide what to practice next. There's no loop."

*(small pause — this is the thesis of the whole video)*

> "Phono StoryForge closes that loop. It generates the book, listens to the read, and moves the target itself."

**Transition line:** "Let me show you — running live." *(cut to browser)*

---

## Screen 2 — Reading face + score
**Budget: ~0:25 | Running: 0:55**

**On screen:** `http://127.0.0.1:8000/?loop&demo`, Reading face, story words with gold-underlined targets.

**Do:**
1. Land on the URL → click **"Read with Ada →"**.
2. Expand "⌨ Type or use a preset" (should already be pre-expanded).
3. Click **"One miscue"** → footer **"How did it go? ▸"**.

**Say (talk while/after clicking):**
> "This is the actual product running live — the same code the experiment runs."

> "Ada's book tonight is built from the sounds she's ready for. See the soft underlines? Those are her targets."

> "She reads the page — I'll score a typical read from the keyboard, so it's repeatable on camera."

**Transition line:** "First — what the kid sees."

⚠ Score from the Reading face, never from Insight (see Screen 3 mechanics).

---

## Screen 3 — Kid view → Insight face ★ most-practiced moment
**Budget: ~0:45 | Running: 1:40**

**On screen:** Session Arc celebration (kid view) → tap **"For grown-ups"** (key `i`) → Insight face: Why card, running-record heatmap, Mastery Path.

**Do:**
1. After scoring, Session Arc advances; celebration shows. Narrate the kid view here.
2. Tap **"For grown-ups"** / press `i`.
3. The adapt beat is deferred and fires the instant you enter Insight — you can't miss it by
   toggling late. Toggle when ready, then **hold silence ~2s** while pop → glow → caption land.

**Say:**
> "First, the kid view — a clean win. No scores, no red ink."

*(a second to let it read as genuinely gentle)*

> "Now the grown-up view."

*(switch — then SAY NOTHING for ~2 seconds while the pop/glow/caption land)*

> "It didn't pick this book at random — here's why it chose this sound and this book."

> "And the running record: that red cell is the exact sound she stumbled on. Not 'she got 95%' — *this grapheme*."

> "And the path — the sound she just nailed lit up, and the target moved. wh to ck."

*(don't read the on-screen caption aloud — point, don't narrate every pixel)*

> "One read: miscue attributed, mastery updated, tomorrow's target moved."

**Transition line:** "One read. Is this a loop, or a party trick? Let's read again."

---

## Screen 4 — Second read + loop rail
**Budget: ~0:35 | Running: 2:15**

**On screen:** Back to Reading (new "ck" book) → score again → Insight → target advances again → loop rail lit (Plan → Generate → Verify ✓ → Read → Assess → Adapt).

**Do:**
1. Press `r` (Insight → Reading).
2. Click **"One miscue"** again on the new book → score.
3. Press `i` back to Insight. Target advances **ck → qu**.
4. Point at the loop rail under the top bar (visible because of `?loop`).

**Say:**
> "Once more, on the new book."

*(a little quiet here is fine — the audience knows the rhythm now)*

> "And the target moves again — ck to qu. The loop adapted twice, live."

*(pause — this is the moment you earned)*

> "That rail along the top — Plan, Generate, Verify, Read, Assess, Adapt — that's the ADK loop you just watched fire."

**Transition line:** "Does adapting actually help, or does it just look clever? We tested it."

⚠ If the adapt animation doesn't visibly move: cut to the Shelf/Journey timeline (🏷 Shelf) as the alternate adaptation proof.

---

## Screen 5 — Evidence chart
**Budget: ~1:30 (only ~50s talking) | Running: 3:45**

**On screen:** full-screen `eval/experiments/results/adaptive_vs_static.png`.

**Do:** Confirm before recording this is the de-circularized re-run (regen if unsure:
`uv run python -m eval.experiments.adaptive_vs_static`). Let the chart breathe — don't fill the slack.

**Say — the result:**
> "Same paired, seeded simulated learners. Same fixed benchmark probe every session. Adaptive — which picks each session's target from the child's own estimate — versus a fixed scope-and-sequence that ignores the evidence."

> "n of thirty, forty sessions: probe accuracy up point-oh-six. True mean mastery up point-oh-four. Almost five more words correct per minute."

*(let the chart breathe a few seconds)*

**Say — the rigor beat (do not skip):**
> "And we didn't let it grade its own homework. The simulated learner was built deliberately *unlike* what the tutor assumes — a logistic reader with per-sound difficulty, no prerequisite gate, and it *forgets*."

> "De-circularizing roughly halved the gaps. But they stayed positive — across all twelve cells of the sweep."

**Say — the honesty beat (keep it, it reads as credible):**
> "One place it's a wash: the count of sounds pushed past a hard zero-point-nine-five bar. We log that. We don't hide it."

**Transition line:** "So it works. Can it also be something a kid wants to hold?"

---

## Screen 6 — Illustrated book
**Budget: ~0:50 (only ~30s talking) | Running: 4:35**

**On screen:** `results/sample_book/page_01.png … page_06.png` ("Sam the Fox", 6 pages). Prefer
committed PNGs or a pre-captured Google Doc screen recording over live `gws`.

**Do:** Let a page or two turn in silence (~20s of the budget is pages, not speech).

**Say:**
> "And here's the story it forges — fully illustrated. Every page is guaranteed made from sounds they know. An LLM proposes the words; deterministic Python verifies."

*(let pages turn)*

> "Same discipline, three times: a decodability check that won't let an undecodable word ship. A palette verifier that proves every illustration stays on brand. And a Doc assembled deterministically."

> "Three guardrails that halt instead of quietly shipping something wrong."

> "And as of last week, this is folded into the live loop — not a separate path."

**Transition line:** "So — what did you just watch?"

⚠ If the live Doc stalls: fall back to committed page PNGs / pre-captured recording.

---

## Screen 7 — Close
**Budget: ~0:25 | Running: 5:00**

**On screen:** architecture loop diagram / recap card. **Count-free** — no specific test number on screen or in speech.

**Say:**
> "One deterministic loop — plan, generate, listen, attribute, update — wired into a real product."

> "Proven by a de-circularized study. Now forging illustrated stories inside that same loop."

> "The whole offline suite passes green. Built on ADK, for Agents for Good."

*(pause — then the locked line, word for word)*

> "A five-minute win beats a fifteen-minute fight — at scale."

*(hold a beat. Done.)*

---

## Keyboard shortcuts
| Key | Action |
|---|---|
| `i` | Reading → Insight ("For grown-ups") |
| `r` | Insight → Reading |
| `F11` / ⌃⌘F | Full-screen the title card |

## Failure modes → recovery
| If this happens | Do this |
|---|---|
| 🎤 clicked by accident | Reload the page — disk state persists, you resume where you were |
| Adapt animation doesn't visibly move | Cut to Shelf/Journey timeline as alternate adapt proof |
| `?loop` rail clutters/distracts | Reload without `?loop`; Session Arc carries the narrative |
| DegradeBanner appears | Narrate it if intentional, otherwise reload and re-take |
| Server hiccup mid-take | Reboots in ~3s; `--data-dir .phono-demo-data` persists state mid-take |
| Live Google Doc stalls | Fall back to committed page PNGs / pre-captured recording |
| Cold-start card instead of "Read with Ada →" | localStorage seed missing — run one-time setup, reload |

## Gate checklist before any recording
- [ ] App boots against `.phono-demo-data`, `ada` loads via returning-reader card
- [ ] Voice shot CUT — typed presets only, never click 🎤 on camera
- [ ] Reduce Motion OFF + Calm mode OFF confirmed
- [ ] Zoom 110–125%; words + mastery path both fit
- [ ] Operator `<details>` pre-expanded
- [ ] `adaptive_vs_static.png` confirmed = de-circularized run
- [ ] Fallback Google Doc screen recording captured (or committed PNGs accepted)
- [ ] Reading→Insight toggle rehearsed: score from Reading, toggle, 2s silence
- [ ] Full stopwatched dry run end-to-end with NO hesitation
