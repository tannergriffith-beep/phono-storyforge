# Phono / StoryForge — UX Audit (Phase 5)

*Phase 5 of the rebrand. A screen-by-screen audit of the **current** app ([app/web/static/index.html](app/web/static/index.html), [render.js](app/web/static/render.js), and the seven components in [app/web/static/components/](app/web/static/components/)) measured against the approved direction and the Phase-4 [design-system.md](design-system.md). For every screen: **what works · what's confusing · what should change · why · expected user impact.** This audit is grounded in the actual markup and copy strings as they exist today.*

**Reminder of the standard we're auditing against:** the decode is sacred; effort never accuracy, celebration never score; two audiences (calm child / opt-in adult) on one surface; a human session arc, not engineer narration; plain language, never jargon; a warm on-ramp before any data.

## Severity legend
- 🔴 **Critical** — violates a load-bearing principle (shame/accuracy exposure, decode/accessibility, the scared-parent on-ramp). Fix early.
- 🟠 **Major** — undermines trust, clarity, or the emotional journey.
- 🟡 **Minor / polish** — real but lower-stakes; batch later.
- ✅ **Keep** — works; preserve through the redesign.

---

## Cross-cutting findings (the systemic issues, surfaced first)

These recur across screens and are the spine of the Phase-6 plan.

### C1. 🔴 Accuracy and "mastery %" are exposed where they must never be
The top bar renders a **persistent "Mastery" meter with a live percentage** ([index.html:21–25](app/web/static/index.html#L21-L25), `setMean()` writes `(x*100).toFixed(0) + "%"` in [render.js:165-168](app/web/static/render.js#L165-L168)). It is visible **on the child's Reading face**, the whole time. The Insight fluency readout leads with **`accuracy %` and an `errors` count** ([render.js:109-115](app/web/static/render.js#L109-L115)).
- **Why it's wrong:** the brief and design system forbid accuracy/score framing in child-facing surfaces, and forbid comparison/percentage as the progress model. A struggling reader (or a parent in front of them) seeing "Mastery 42%" is exactly the shame mechanic the product exists to remove.
- **Change:** remove the percentage from the persistent chrome; reframe to "Sounds we've practiced" with the **sage growth** treatment (no number) per design-system §10/§12. Keep accuracy/WCPM **only** inside the opt-in adult view, demoted below the effort framing.
- **Impact:** removes the single biggest shame-leak; makes the privacy boundary real instead of partial.

### C2. 🔴 No on-ramp — the app opens on a data form
First contact is `#setup` titled **"Start a session"** with fields **"Learner id / Name / Age / Interest"** ([index.html:46-56](app/web/static/index.html#L46-L56)). There is no reassurance, no "you found the right place," no explanation.
- **Why:** a frightened parent meets a database form and jargon before any human warmth (design-system §14; Phase 1 §15.3).
- **Change:** add the warm onboarding flow (reassure → who are we reading with → how it works → first story).
- **Impact:** converts anxiety into safety in the first 15 seconds; raises the odds she starts at all.

### C3. 🔴 Pervasive engineer/clinical vocabulary
User-facing strings include **"Learner id," "target /grapheme/," "Mastery," "wcpm," "errors," "session #0," "the phonics path," "the loop adapted," "decodable," "today's target," "Runs the full story pipeline."** These are the forbidden-words list (design-system §18) in the live UI.
- **Why:** intimidates the non-expert parent and re-frames a child's reading as a clinical readout.
- **Change:** translate everything to the plain, warm lexicon ("the next sound your reader is ready for," "sounds," "stories on the shelf," "sessions together"). Keep technical terms only in an optional "behind the scenes" adult view / internal tooling.
- **Impact:** the product stops sounding like its own architecture diagram and starts sounding like a knowledgeable neighbor.

### C4. 🔴 Reader Settings are absent (decode-sacred gap)
There is no control for reading typeface, text size, or letter/word/line spacing. The child is stuck with whatever the default renders.
- **Why:** the design system makes reading-text adjustability a first-class accessibility requirement (§2.1, §15.3) — the core promise that the decode is sacred.
- **Change:** add Reader Settings, surfaced in onboarding and reachable from the Reading face.
- **Impact:** guarantees no child is locked out by a face/size/spacing that doesn't decode for them.

### C5. 🟠 Emoji stand in for an icon system
`📖 📊 📈 🎤 📚 ⚠️ 🌟` are used as functional icons across the chrome.
- **Why:** inconsistent rendering across platforms, no stroke/weight discipline, reads as informal/unfinished — counter to the editorial icon system (design-system §6).
- **Change:** replace with the line-icon set; reserve a single emoji-free brand mark (the fox/beacon).
- **Impact:** lifts perceived craft and trustworthiness; consistent at all sizes.

### C6. ✅ What the current build gets genuinely right — preserve it
- **The privacy boundary is correctly implemented:** on `outcome`, the view stays on Reading, the celebration shows, and the running record stays in Insight behind an adult tap with a pip ([render.js:140-146](app/web/static/render.js#L140-L146)). *This is the product's best idea — keep the behavior, restyle the surface.*
- **The two-faced architecture** (one payload, two views) is clean ([render.js:63-76](app/web/static/render.js#L63-L76)).
- **Graceful degradation on independent axes** (voice/illustration/connection) and **aria-live regions** on status/degrade/caption are real accessibility groundwork.
- **"Great reading! 🌟"** is the right instinct (effort celebration) — keep the sentiment, restyle and extend it into the earned shelf.
- **The "Why this book?" and "next target" concepts** are trust gold — they just need plain-language reframing, not removal.

---

## Screen-by-screen audit

### 1. Top bar / persistent chrome — 🔴
[index.html:11-27](app/web/static/index.html#L11-L27)

- **Works:** persistent brand presence; Journey entry exists; meter gives an at-a-glance signal. The `title` tooltip is a (small) accessibility nicety.
- **Confusing / wrong:** brand reads **"Phono StoryForge"** with tagline **"a closed-loop adaptive reading tutor"** — describes the *architecture*, not the *promise*; the **"Mastery" percentage** is the C1 violation, live during child reading; "📈 Journey" is hidden until first prepare (`hidden` attr) so the longitudinal proof is invisible to a first-time user.
- **Should change:** wordmark → the Phono-endorses-StoryForge lockup (design-system §10); tagline → a human promise or nothing; meter → "Sounds we've practiced," sage, **no %**; promote Shelf + Journey to first-class, always-visible (even empty, per §13).
- **Why:** the chrome currently advertises the engine and leaks a score; it should advertise trust and growth.
- **Impact:** the always-on surface stops shaming and starts reassuring; the growth story becomes discoverable.

### 2. The "Loop rail" — 🟠
[index.html:29-32](app/web/static/index.html#L29-L32) · `aria-label="The adaptive loop — each step lights as it runs"`

- **Works:** as a *stakeholder demo* device it narrates the architecture beautifully; the staggered lighting is genuinely impressive to a technical audience.
- **Confusing:** for a parent it narrates *the system's* six steps (Plan/Generate/Verify/Read/Assess/Adapt) — a mental model she doesn't have and doesn't need.
- **Should change:** replace with the **human session arc** — *Tonight's story → Read together → How it went → What's next* (design-system §10). Relocate the technical loop to an optional "behind the scenes" view for educators/demos.
- **Why:** navigation should map to the parent's journey, not the engineering pipeline (Phase 1 §15.2).
- **Impact:** the parent always knows where she is in *her* night, not in the algorithm.

### 3. Degrade banner — 🟡
[index.html:39-43](app/web/static/index.html#L39-L43)

- **Works:** correct pattern (polite live region, dismissible, survives setup hiding); degradation is partial not fatal — excellent.
- **Confusing:** the **⚠️ warning icon** and "degrade" framing read as *alarm*; an anxious parent reads "something is broken."
- **Should change:** restyle as the calm `--info` **Sign card** with reassuring copy ("Tonight we'll read with typing instead of the microphone — everything else works") per design-system §13.
- **Why:** degraded states are designed places in the journey, not errors.
- **Impact:** a flaky mic becomes a shrug, not a scare.

### 4. Setup / empty state — 🔴
[index.html:46-56](app/web/static/index.html#L46-L56)

- **Works:** mercifully short; sensible fields; single clear CTA ("Begin →").
- **Confusing / wrong:** **"Start a session"** + **"Learner id"** is clinical-database language; the field is prefilled with dev fixtures **"ada / Ada / 6 / dinosaurs"** (ships looking like test data); **"connecting…"** exposes socket state to the user; no reassurance (C2); "Age" is a bare number stepper (design system calls for a friendly band picker).
- **Should change:** fold into the onboarding flow (§14): warm intro first; "Who are we reading with?" instead of "Learner id"; age as a band picker; interest as example chips; remove fixtures; move connection state into the calm degrade/Sign system.
- **Why:** this is the scared parent's first screen and currently it's the least warm one.
- **Impact:** dramatically better first impression and start-rate.

### 5. Session — Reading face (the child) — 🟠
[index.html:73-97](app/web/static/index.html#L73-L97)

- **Works:** **genuinely good** — words only, no stats, no red; target words *softly underlined, never colored* ([render.js:63-68](app/web/static/render.js#L63-L68)); the typed/preset path is correctly demoted into a `<details>` so the **mic is primary**; `tabindex="-1"` supports focus management; "Great reading! 🌟" is warm.
- **Confusing / wrong:** the **mic button is styled `ghost`** ([index.html:82](app/web/static/index.html#L82)) while **"Score read ▸" is `primary`** — the *child's* hero action looks secondary and an adult-framed "Score" looks primary, on the child's page. The persistent top-bar % (C1) hovers above this calm space. No Reader Settings (C4). Reading text isn't yet on the cream/serif/measure spec.
- **Should change:** make **Read aloud the primary claret pill** (design-system §7.1); move/rename "Score read" out of the child's visual field (it's an adult action — fold into "How it went"); apply the reading-face type, cream ground, 50–55ch measure, and Reader Settings.
- **Why:** the decode is sacred and the child's action must be the obvious one; nothing scoring-flavored belongs in their eyeline.
- **Impact:** the child sees a calm, beautiful page and one inviting thing to do.

### 6. Mode toggle — 🟠
[index.html:66-71](app/web/static/index.html#L66-L71) · `modeToggle.js`

- **Works:** the *mechanism* is excellent — pure view switch, keyboard shortcuts, the pip-not-auto-flip privacy default, custom-event coordination. Preserve all of it.
- **Confusing:** labels **"📖 Reading / 📊 Insight"** — "Insight" is product jargon; the chart emoji frames the adult view as analytics-first.
- **Should change:** relabel **"Reading" / "For grown-ups"** (design-system §10); replace emoji with line icons; keep every behavior.
- **Why:** the words should tell a parent what the second view is *for*, not name an internal concept.
- **Impact:** parents actually understand and use the second view — and trust that the first is safe for the child.

### 7. Session — Insight face (the adult) — 🟠
[index.html:99-133](app/web/static/index.html#L99-L133) · `whyCard.js`, `masteryPath.js`, `adaptBeat.js`

Sub-elements:
- **"Why this book?" (`#why-card`)** — ✅ concept is trust gold; ensure plain-language copy ("the next sound your reader is ready for") and the gold-rule Why card styling (design-system §8).
- **Running record + legend** — 🟠 ✅ *credit first:* the heatmap already encodes each miscue with a **shape, not just hue** ([style.css:544-550](app/web/static/style.css#L544-L550)) — solid underline / strike-through / dashed — deliberate color-blind support to preserve. *But:* substitution is `var(--coral)` with white text ([style.css:547](app/web/static/style.css#L547)) — the alarm treatment we forbid; self-correction (the *win* of a running record) is rendered the same neutral amber as everything else, not celebrated; and the legend exposes **"substitution / omission"** jargon. **Change** to the de-alarmed palette (design-system §1.5): keep the shape-encoding, but recolor — self-corrections *celebrated* in sage, substitution a neutral `--caution` dotted line (never coral/white), plain-language key ("swapped a sound," "skipped," "fixed it themselves"). **Why:** even the adult analysis must read as understanding, not red-pen judgement. **Impact:** a parent reads the record as insight — and sees her child's self-corrections as wins, not failures.
- **Fluency readout** — 🟠 leads with **accuracy %, wcpm, correct, errors** ([render.js:109-115](app/web/static/render.js#L109-L115)). **Change:** lead with effort/growth (sessions, sounds, time); keep accuracy/WCPM present but **secondary and clearly labelled as a teacher's metric**, never the headline. **Why/Impact:** keeps the rigor available without making accuracy the story.
- **Scaffolds** — 🟡 useful ("/sh/ in 'ship' — …"); keep, ensure the `/grapheme/` notation is softened to "the /sh/ sound."
- **Mastery path** — 🟠 titled **"Mastery — the phonics path"**; component behavior (states, tap-for-detail, the adapt animation) is strong — keep it. **Change** the title and the tap-detail copy to plain language; map node colors to learned=sage / today=claret / coming-up=cloth-grey-dashed (design-system §12). Raw P(L) % only in the deep "behind the scenes" view.
- **Adapt caption + "Tomorrow's target"** — 🟠 copy reads **"the target ADVANCED from /x/ — the loop adapted"** ([render.js:135-137](app/web/static/render.js#L135-L137)) — engineer triumph, not parent meaning. **Change:** "Sam learned /sh/. Next we'll practice /ch/." Keep the *advancement signal* (it's the proof of adaptation), lose the loop language.
- **Overall impact:** the adult view becomes a warm, honest "how it went," not a clinical dashboard — while keeping every bit of the real rigor one tap deeper.

### 8. Footer CTAs — 🟡
[index.html:136-140](app/web/static/index.html#L136-L140)

- **Works:** single primary action at a time (Score → Next); clean state flip.
- **Confusing:** **"Score read ▸"** is adult/clinical language living under the child's Reading face; **"Next session →"** is fine but could be warmer.
- **Should change:** "Score read" → an adult-framed "How did it go?" that belongs to the grown-up step, not the child's page; "Next session" → "Read another tonight" / "What's next."
- **Impact:** the primary action stops sounding like grading.

### 9. Take-home illustrated book — 🟡
[index.html:143-157](app/web/static/index.html#L143-L157)

- **Works:** genuinely magical feature; correctly opt-in, creds-gated, hidden when unavailable; progress + result + decodable badge + page thumbnails is a complete little flow.
- **Confusing:** copy is technical — **"illustrated, decodable book for today's target," "Runs the full story pipeline — takes a few minutes," "Open the Google Doc ↗," source/decodable "badges."**
- **Should change:** reframe as a keepsake ("Make tonight's story into a little book Sam can keep"); calm count-up loading per §13 ("Making Sam's book…"); the illustration must follow design-system §17 (palette-verifier + CharacterBible, never under reading text); badge → quiet reassurance, not a `source-badge`.
- **Impact:** the feature reads as a gift, not a build job — and becomes a powerful shareable/retention moment.

### 10. Journey view — 🟠
[index.html:160-169](app/web/static/index.html#L160-L169) · `journey.js`

- **Works:** the longitudinal growth proof exists; the component handles empty states and a trend sparkline thoughtfully.
- **Confusing:** it's a **hidden modal** reachable only via a top-bar button that's itself hidden until first prepare — so the most motivating artifact (the rising line) is buried; the table currently centers session/target/mean data in fairly technical framing.
- **Should change:** promote Journey to a **first-class, always-reachable space** framed around effort, sessions, sounds learned, and **the earned Shelf**; the sparkline becomes the sage/gold growth chart (§12); add the Shelf of finished books as the emotional centerpiece (§8).
- **Why:** "it's working" is the parent's deepest motivation; it shouldn't hide behind two layers (Phase 1 §15.4).
- **Impact:** turns a hidden stats modal into the reason a parent comes back.

---

## Accessibility audit (against WCAG 2.1 AA / AAA-reading)

| Area | Status | Action |
|---|---|---|
| Reading-text contrast | unknown (palette being replaced) | Adopt verified tokens — ink/cream 13:1 (AAA) |
| Reading typeface/size/spacing control | 🔴 absent | Add Reader Settings (C4) |
| Color as sole indicator | ✅ heatmap already shape-encodes ([style.css:544-550](app/web/static/style.css#L544-L550)) | Preserve shapes; recolor + add plain labels (§1.5) |
| Focus management | ✅ partial (`tabindex=-1`, live regions) | Keep; add always-visible focus rings (§7.2) |
| `prefers-reduced-motion` | components claim support | Verify across loop/adapt/page-turn (§15.3) |
| Emoji as meaningful icons | 🟠 | Replace with labelled line icons + `aria-hidden` on decorative (C5, §6) |
| Shame-free states | 🔴 % exposure (C1), red miscues | Remove %; de-alarm heatmap |
| Keyboard / SR labels | ✅ groundwork present | Preserve; relabel jargon `aria-label`s |
| Touch targets (future app) | mic/score OK; presets small | Enforce 44px min (§7.2) |

---

## Priority matrix → seeds Phase 6

| # | Finding | Severity | Rough effort | Suggested PR grouping |
|---|---|---|---|---|
| C1 | Remove accuracy/% exposure; reframe meter | 🔴 | S–M | PR: "Effort-not-accuracy chrome" |
| C3 | De-jargon all user-facing copy | 🔴 | M | PR: "Plain-language copy pass" |
| C2 | Warm onboarding on-ramp | 🔴 | M | PR: "Onboarding & setup" |
| C4 | Reader Settings (type/size/spacing) | 🔴 | M | PR: "Reader Settings / decode-sacred" |
| — | Token foundation (`tokens.css`) | 🔴 (enabler) | M | PR 1: "Design tokens" (must land first) |
| 7 | De-alarm running record + fluency reframe | 🟠 | M | PR: "Insight face: honest, not clinical" |
| 2 | Loop rail → human session arc | 🟠 | M | PR: "Session arc nav" |
| 10 | Journey + Shelf first-class | 🟠 | M–L | PR: "Journey & the earned shelf" |
| 5/6/8 | Reading-face polish, toggle relabel, CTA reframe | 🟠 | S–M | PR: "Reading face & mode" |
| 3/9 | Calm degrade Sign; take-home reframe | 🟡 | S | PR: "Calm states & keepsake" |
| C5 | Icon system replaces emoji | 🟡 | M | PR: "Icon system" |
| 17 | Illustration guardrails wired to brand | 🟡 | M | PR: "Illustration system" |

---

## Self-critique (per process)

- *"You're auditing a hackathon demo as if it were a shipped consumer product."* True, and stated: much of what reads as "wrong" (loop rail, mastery %, jargon) is *correct for its original judging context*. The audit's job is to re-aim it at the scared parent — and to **credit what's genuinely excellent** (the privacy boundary, the two-face architecture, graceful degradation) rather than throw it out.
- *"Some 'critical' items are really copy changes."* Fair — but copy *is* the shame-leak here (C1/C3), so I've kept their severity high while noting low-to-medium effort. The token PR is the true prerequisite and is flagged as the enabler.
- *"Are you sure the heatmap uses red?"* I inferred it from the `correct/substitution/omission/fixed` classes and standard running-record convention; Phase 6 must confirm the actual CSS before changing it — flagged, not assumed.
- *Residual risk:* I have not yet read every line of each component's render path (e.g., exact `masteryPath` color values). Phase 6 PRs will each begin by reading the specific files they touch.

---

## Gate

Phase 5 is complete: every screen audited against the design system, with severities, rationale, expected impact, an accessibility pass, and a priority matrix that pre-stages the Phase-6 PRs.

**Awaiting approval to proceed to Phase 6 — the Implementation Plan (`implementation-plan.md`)**, an incremental, safe PR roadmap (objective · affected files · steps · testing · accessibility checklist · rollback) built directly from this priority matrix, starting with the token foundation.
