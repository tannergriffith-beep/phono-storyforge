# Phono / StoryForge — Implementation Plan (Phase 6)

*Phase 6 of the rebrand. An incremental, safe PR roadmap that migrates the live app ([app/web/](app/web/)) to the Phase-4 [design-system.md](design-system.md), resolving the Phase-5 [ui-audit.md](ui-audit.md) findings. Each PR is small, independently shippable, independently reversible, and changes **one system at a time.***

---

## Migration principles (apply to every PR)

1. **Additive first, subtractive last.** Introduce new tokens/components alongside the old, migrate one component family, then delete the old styles in the *same* PR once that family is green. Never leave two systems fighting across PRs.
2. **The deterministic brain is off-limits.** [app/skills/](app/skills/), [app/tutor/session.py](app/tutor/session.py), [app/store/](app/store/), and [schemas.py](app/schemas.py) are the product's tested core. PRs touch **presentation** ([app/web/static/](app/web/static/)) and, narrowly, **payload copy** ([app/web/viz.py](app/web/viz.py), [app/web/server.py](app/web/server.py)) — never the loop logic, never payload *shape* that tests assert.
3. **Green at every step.** `uv run pytest tests/unit` (the full offline suite) must pass on every PR. Backend-touching PRs add their own guard tests (see "New invariant tests" below).
4. **Feature-flag the risky/structural changes** (session-arc nav, illustration) so rollback is a flag flip, not a revert.
5. **Manual verification** each PR via `uv run python scripts/tutor_web.py` + the `/verify` skill, against a per-PR QA checklist. (No automated visual-regression harness exists; this is the substitute.)
6. **Branching:** one branch per PR off `main` (`redesign/NN-slug`); small, reviewable diffs; commit footer `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`. Do not stack unrelated changes.
7. **Two product-wide invariants are now tested, not trusted** (design-system §19): (a) no accuracy/percentage/score string ever reaches a child-facing payload field; (b) child-facing copy contains none of the forbidden lexicon. These get assertion tests in PR 3 and are guarded thereafter.

### Sequence & dependency graph
```
PR1 tokens+type  ──┬─► PR2 effort-chrome (C1)
   (enabler)       ├─► PR3 lexicon + guards (C3)
                   ├─► PR4 reading face + Reader Settings (C4)   ◄─ needs fonts from PR1
                   └─► PR5 onboarding (C2)        ◄─ needs PR3 lexicon
PR6 toggle+CTA  ◄─ PR3
PR7 insight honesty ◄─ PR1,PR3
PR8 session-arc nav (flagged) ◄─ PR1,PR3
PR9 journey + earned shelf ◄─ PR1,PR3
PR10 calm states + keepsake ◄─ PR1,PR3
PR11 icon system ◄─ PR1
PR12 illustration guardrails (flagged, backend) ◄─ PR1
```
Ship in number order; PR6–PR12 can be parallelized by a second contributor after PR1/PR3 land, since each owns a disjoint component family.

---

## PR 1 — Token & type foundation *(enabler; must land first)*

**Objective.** Introduce the design-system tokens and the three (+1) typefaces as a foundation that later PRs consume. Visually near-neutral on its own.

**Affected files.** New `app/web/static/tokens.css`; new `app/web/static/fonts/` (self-hosted woff2); [index.html](app/web/static/index.html) (`<link>` tokens.css before style.css; `@font-face` via tokens.css); minor [style.css](app/web/static/style.css) (set base `font-family`, page background to `--paper`).

**Implementation steps.**
1. Create `tokens.css` with every token from design-system §1–§5, §15.2 as `:root` custom properties (`--ink`, `--claret`, `--gold`/`--gold-deep`, `--sage`/`--sage-deep`, `--cream`, spacing, radius, elevation, motion).
2. Self-host **Literata**, **Source Sans 3**, **Source Code Pro**, and **Lexend** (woff2, subset to Latin) under `fonts/`; declare `@font-face` with `font-display: swap`. (Self-hosted, not CDN — offline-friendly and no third-party dependency.)
3. Set global base: body → `--paper`, `--text-primary`, Source Sans 3; reading containers will opt into Literata in PR4.
4. Map a small compatibility shim: alias the legacy vars still in use (`--navy`, `--coral`, `--gold`, `--tundora`, `--white`) to the nearest new token **only** where removing them now would break unmigrated components — documented as temporary, removed as each family migrates.

**Testing strategy.** `pytest tests/unit` (unaffected — no Python change). Manual: app loads, fonts resolve (network tab shows woff2, no FOUT crash), no layout breakage. Lighthouse/devtools check fonts load < 100KB each.

**Accessibility checklist.** ☐ Fonts include the glyphs needed for child text. ☐ `font-display: swap` (no invisible text). ☐ Base contrast ink/paper ≥ AA. ☐ No reliance on the new tokens yet for meaning.

**Rollback.** Remove the two `<link>`/`@font-face` references; delete `tokens.css`. Zero behavioral impact (no component depends on it yet).

---

## PR 2 — Effort-not-accuracy chrome *(resolves C1 — the shame leak)*

**Objective.** Remove the persistent "Mastery %" from the top bar (visible during child reading) and reframe it as non-numeric growth.

**Affected files.** [index.html](app/web/static/index.html#L21-L25) (the `.mean-meter` block); [render.js](app/web/static/render.js#L165-L168) (`setMean`); [style.css](app/web/static/style.css) (`.mean-*`); possibly [viz.py](app/web/viz.py) only if a "sounds practiced" count is cleaner server-side (prefer deriving client-side from existing `mastery_bars`).

**Implementation steps.**
1. Replace the numeric `#mean-value` with a label **"Sounds we've practiced"** + a sage progress treatment with **no percentage** and no comparison.
2. `setMean()` stops writing `(x*100)…%`; instead drives the sage growth width and an aria-label like "growing — X sounds practiced together" (count derived from `mastery_bars` already in the payload).
3. Migrate the top-bar styles to tokens (claret/sage/cream).

**Testing strategy.** `pytest tests/unit`. Add a frontend assertion in QA: no `%` character renders in the top bar in any state. Manual: prepare → read → outcome, confirm no number/score appears in persistent chrome.

**Accessibility checklist.** ☐ No accuracy/score exposed in child-visible chrome. ☐ Growth conveyed by label + shape, not color alone. ☐ aria-label is effort-framed, never "X% mastered."

**Rollback.** Revert the file diff; the meter returns. Isolated to chrome.

---

## PR 3 — Plain-language lexicon + invariant guards *(resolves C3)*

**Objective.** Translate centralized/shared and backend-sourced user-facing strings to the warm lexicon, document the glossary, and add the two product-wide guard tests.

**Affected files.** [render.js](app/web/static/render.js) (shared strings); [viz.py](app/web/viz.py) (rationale, scaffold prompts, next-target copy, `generation_source` display labels); [server.py](app/web/server.py) (any user-facing message strings); new `tests/unit/test_copy_invariants.py`; new `docs/voice-lexicon.md` (the glossary from design-system §18). *Per-screen inline labels are handled in their own PRs — this PR owns the shared + backend strings and the reference glossary.*

**Implementation steps.**
1. Author `docs/voice-lexicon.md`: forbidden words → preferred phrasings (mastery→"sounds learned", grapheme→"sound", target→"the next sound your reader is ready for", wcpm/accuracy→adult-only, "the loop adapted"→"what's next", session #N→"your Nth story together", decodable→"made from sounds they know").
2. Rewrite the backend-sourced strings in `viz.py`/`server.py` to the lexicon **without changing payload field names or shapes** (only the string *values*).
3. Add `test_copy_invariants.py`: (a) assert no child-facing payload field (book title/text/celebration) contains any forbidden token; (b) assert the rationale/next-target strings avoid "loop/grapheme/mastery"; (c) a maintained forbidden-word list.

**Testing strategy.** `pytest tests/unit` incl. the new file. Tests must assert on *values*, tolerant of wording (regex on banned tokens), so future copy tweaks don't break them spuriously.

**Accessibility checklist.** ☐ Plain language (lowers cognitive load for stressed adults). ☐ No clinical terms in child surfaces. ☐ Reading level of adult copy ~grade 7–8.

**Rollback.** Revert string diffs; keep the harmless glossary + tests (tests would simply pass on old strings only if old strings comply — if not, keep tests and fix forward rather than rolling back the safety net).

---

## PR 4 — Reading face + Reader Settings *(resolves C4; decode-sacred)*

**Objective.** Make the child's reading surface match the spec (cream ground, Literata, generous measure/leading) and add user-controlled type/size/spacing.

**Affected files.** [index.html](app/web/static/index.html#L73-L97) (reading-face + a Reader Settings control); [style.css](app/web/static/style.css) (`.reading-page`, `.reading-title`, `.mic`); [render.js](app/web/static/render.js) (mic as primary); new `app/web/static/components/readerSettings.js`; [state.js](app/web/static/state.js) (persist settings).

**Implementation steps.**
1. Apply reading-face tokens: `--cream` ground, Literata, `--fs-reading` (25px min, 1.85 lh), measure capped 50–55ch, left-aligned ragged-right; target words softly underlined (keep existing non-colored treatment).
2. Promote **Read aloud** to the primary claret pill (≥52px); demote/relabel the scoring action (handled fully in PR6).
3. Build `readerSettings.js`: typeface (Literata serif default / **Lexend** sans option), size (1×–1.6×), letter/word/line spacing, "calm" motion toggle; persist to `localStorage` keyed by learner; apply via CSS custom props on the reading container.
4. Surface a quiet "Aa" Reader Settings entry on the Reading face (and again in onboarding, PR5).

**Testing strategy.** `pytest tests/unit` (no backend change). Manual: toggle each setting, confirm it re-renders the passage and persists across reload; verify Lexend renders b/d/p/q distinctly; measure ≤55ch at all widths.

**Accessibility checklist.** ☐ Reading text contrast ink/cream = 13:1 (AAA). ☐ Min 25px, scalable to 40px. ☐ Sans option (Lexend) available. ☐ Settings reachable by keyboard, labelled. ☐ Respects `prefers-reduced-motion` + the calm toggle. ☐ Touch target ≥44px.

**Rollback.** Feature-flag `READER_SETTINGS` (default on); flip off to hide the control and fall back to default Literata. Reading-face style diff is isolated.

---

## PR 5 — Onboarding & setup *(resolves C2)*

**Objective.** Add the warm on-ramp before any data and reframe the setup form.

**Affected files.** New `app/web/static/components/onboarding.js`; [index.html](app/web/static/index.html#L46-L56) (`#setup` becomes step in flow); [style.css](app/web/static/style.css); [app.js](app/web/static/app.js) (boot into onboarding for new users); [state.js](app/web/static/state.js) (returning-user skip).

**Implementation steps.**
1. Build the 4-step flow (design-system §14): reassure → "Who are we reading with?" → "how this works (90s)" → first story. One question per step.
2. Replace "Learner id" UX with a friendly "child's first name" (keep a stable id under the hood, derived/hidden); age as a band picker; interest as example chips; remove the `ada/Ada/6/dinosaurs` fixtures.
3. Move "connecting…" out of the user's face into the calm degrade/Sign system (coordinate with PR10).
4. Skip onboarding for returning learners (localStorage flag).

**Testing strategy.** `pytest tests/unit`. Manual: first-run shows reassurance first; returning user lands straight in; the hidden learner-id still maps to the same persisted profile (verify `prepare` resolves the same `LearnerStore` record).

**Accessibility checklist.** ☐ One focal action per step. ☐ Inputs labelled, errors are guidance not blame (§9). ☐ Keyboard/SR flow through steps. ☐ No child-facing validation styling. ☐ Skippable.

**Rollback.** Flag `ONBOARDING` (default on); off → boot directly to the (reframed) setup card. Pure frontend.

---

## PR 6 — Mode toggle relabel + footer CTA reframe

**Objective.** Replace jargon labels and the scoring-flavored CTA on the child's page.

**Affected files.** [index.html](app/web/static/index.html#L66-L71) (toggle), [#L136-L140](app/web/static/index.html#L136-L140) (footer); [components/modeToggle.js](app/web/static/components/modeToggle.js) (labels/aria only — keep all behavior); [style.css](app/web/static/style.css).

**Implementation steps.**
1. Relabel toggle **"Reading" / "For grown-ups"**; replace emoji with PR11 icons (or text until then); keep the pip-not-auto-flip privacy logic untouched.
2. Reframe "Score read ▸" → an adult-framed "How did it go?" associated with the grown-up step (not the child's eyeline); "Next session →" → "Read another" / "What's next".
3. Migrate toggle/footer styles to tokens.

**Testing strategy.** `pytest tests/unit`. Manual: confirm privacy default preserved (stays on Reading after scoring, pip appears, no auto-flip); keyboard shortcuts still work.

**Accessibility checklist.** ☐ `aria-pressed`/labels updated to plain language. ☐ Focus rings visible. ☐ Pip has text alternative. ☐ No behavior regression.

**Rollback.** Revert labels/CTA strings; isolated.

---

## PR 7 — Insight face: honest, not clinical

**Objective.** De-alarm the running record, reframe fluency around effort, and plain-language the why-card/mastery-path/next-target — keeping all the rigor one tap deeper.

**Affected files.** [style.css](app/web/static/style.css#L541-L557) (miscue colors/legend); [render.js](app/web/static/render.js#L96-L138) (fluency order, next-target copy); [components/whyCard.js](app/web/static/components/whyCard.js), [components/masteryPath.js](app/web/static/components/masteryPath.js), [components/adaptBeat.js](app/web/static/components/adaptBeat.js) (copy/colors only); [viz.py](app/web/viz.py) (heatmap `kind` labels if surfaced).

**Implementation steps.**
1. Recolor the running record to the de-alarmed palette (design-system §1.5): **keep the existing shape-encoding** (underline/strike/dashed — already color-blind-safe per [style.css:544-550](app/web/static/style.css#L544-L550)); substitution → `--caution` dotted (never coral/white); self-correction → **celebrated in sage**; plain-language legend ("fixed it themselves / swapped a sound / skipped").
2. Reframe the fluency readout: lead with effort (sessions together, sounds, minutes); demote accuracy/WCPM to a clearly-labelled "teacher's numbers" sub-row, never the headline.
3. Mastery path: retitle from "Mastery — the phonics path", recolor nodes (learned=sage / today=claret / coming-up=cloth-grey-dashed), plain-language tap detail; raw P(L) % only behind the optional deep view.
4. Next-target/adapt caption: "Sam learned /sh/. Next we'll practice /ch/." — keep the advancement signal, drop "the loop adapted".

**Testing strategy.** `pytest tests/unit`. Manual across perfect/one-miscue/struggling presets: confirm no coral, self-corrections read as wins, accuracy is not the headline, adapt caption is plain.

**Accessibility checklist.** ☐ Miscue meaning carried by shape + label, not color (preserved). ☐ All Insight text ≥ AA. ☐ Live-region captions intact. ☐ No red anywhere.

**Rollback.** Revert; this PR is presentation-only (no payload-shape change).

---

## PR 8 — Session-arc navigation *(flagged)*

**Objective.** Replace the engineer "loop rail" with the human session arc; relocate the technical loop to an optional view.

**Affected files.** [index.html](app/web/static/index.html#L29-L32) (`#loop-rail`); [components/loopRail.js](app/web/static/components/loopRail.js) (refactor → `sessionArc.js` consuming the same `prepared`/`outcome`/`voice_status` events); [style.css](app/web/static/style.css); new flag in [state.js](app/web/static/state.js).

**Implementation steps.**
1. Build `sessionArc.js`: four human steps (Tonight's story → Read together → How it went → What's next), driven by the *same* events the loop rail already subscribes to (no backend change).
2. Behind a `SHOW_LOOP_INTERNALS` flag (default off; on for educator/demo), keep the six-node technical loop available in a "behind the scenes" panel.
3. Preserve the existing reduced-motion handling and event coordination.

**Testing strategy.** `pytest tests/unit`. Manual: arc advances correctly through prepare→read→score→next; voice_status still advances "Read"; error reverts gracefully; flag on restores the technical loop.

**Accessibility checklist.** ☐ Arc has `aria-label` in plain language. ☐ Current step announced (aria-current). ☐ Reduced-motion collapses timings. ☐ Keyboard reachable.

**Rollback.** Flip `SHOW_LOOP_INTERNALS` on / revert the component swap. The structural risk is contained by the flag.

---

## PR 9 — Journey + the earned shelf

**Objective.** Promote Journey from a hidden modal to a first-class, effort-framed space, with the Shelf of finished books as the emotional centerpiece.

**Affected files.** [index.html](app/web/static/index.html#L160-L169) (`#journey-view`); [components/journey.js](app/web/static/components/journey.js); new `app/web/static/components/shelf.js`; [style.css](app/web/static/style.css); [viz.py](app/web/viz.py) (journey payload may add a stable per-book cover color/spine — derived deterministically from title, no schema change); reads existing `SessionLog`s via the current `journey` ws action.

**Implementation steps.**
1. Make Journey always reachable (not hidden until first prepare); top-bar Shelf entry promoted.
2. Reframe the table around effort (sessions, sounds learned, the sage/gold growth chart from §12) — no accuracy column as headline; highlight target changes (claret) and newly-learned sounds (sage).
3. Build `shelf.js`: each finished story (from `SessionLog.book_title`) becomes a spine/cover; deterministic cover color from a title hash (so no persistence change); empty state = "the line is just beginning" (§13).

**Testing strategy.** `pytest tests/unit`. Manual: run several sessions, confirm shelf grows, growth line rises, empty states render, journey reachable from cold load.

**Accessibility checklist.** ☐ Chart has plain-language caption + non-color encoding. ☐ Table is a real `<table>` with headers (Tufte-clean per §11). ☐ Shelf items have text labels (titles), keyboard focusable. ☐ No accuracy headline.

**Rollback.** Revert; reading/scoring loop unaffected (Journey is read-only over logs).

---

## PR 10 — Calm states + take-home keepsake reframe

**Objective.** Make degraded/empty/loading states calm and intentional; reframe the take-home book as a gift.

**Affected files.** [index.html](app/web/static/index.html#L39-L43) (degrade banner), [#L143-L157](app/web/static/index.html#L143-L157) (book-gen); [components/degradeBanner.js](app/web/static/components/degradeBanner.js); [book.js](app/web/static/book.js); [style.css](app/web/static/style.css).

**Implementation steps.**
1. Restyle the degrade banner as the calm `--info` Sign card; replace ⚠️/"degrade" with reassuring copy ("Tonight we'll read with typing — everything else works"). Move "connecting…" here.
2. Reframe take-home copy as a keepsake ("Make tonight's story into a little book Sam can keep"); calm count-up loading ("Making Sam's book…") + paper skeleton, not an anxious spinner; quiet reassurance instead of `source-badge`/"decodable" jargon.

**Testing strategy.** `pytest tests/unit`. Manual: force voice/illustration failure paths, confirm calm partial degrade and no alarm; generate a book, confirm calm progress + result.

**Accessibility checklist.** ☐ Banner remains polite live region, dismissible. ☐ Loading announced calmly (aria-live). ☐ No alarm iconography. ☐ Link has descriptive text.

**Rollback.** Revert; degrade/keepsake are non-load-bearing.

---

## PR 11 — Icon system

**Objective.** Replace functional emoji with the editorial line-icon set.

**Affected files.** New `app/web/static/icons.svg` (sprite) + `components/icon.js` helper; [index.html](app/web/static/index.html) and components that currently use `📖📊📈🎤📚⚠️🌟`; [style.css](app/web/static/style.css).

**Implementation steps.**
1. Author the core set (design-system §6: book, shelf, bookmark, listen, mic, fox, beacon, route, calendar, win, settings, help) as a 24px, 1.5px-stroke SVG sprite.
2. Add `icon.js` for accessible inline use (`aria-hidden` when decorative, labelled when meaningful).
3. Swap emoji → icons across chrome, toggle, CTAs, banner.

**Testing strategy.** `pytest tests/unit`. Manual: icons render at 16/24px crisply, consistent stroke, correct labels/aria.

**Accessibility checklist.** ☐ Decorative icons `aria-hidden`. ☐ Meaningful icons have text/label. ☐ Never icon-only navigation. ☐ Contrast ≥ AA (ink/claret on cream).

**Rollback.** Revert swaps; emoji return. Purely cosmetic.

---

## PR 12 — Illustration system guardrails *(flagged; backend-touching)*

**Objective.** Ensure AI-generated art is on-brand, consistent, never under reading text, and always degrades calmly — wiring the brand into the *existing* generation pipeline.

**Affected files.** [app/illustrator.py](app/illustrator.py), [app/skills/palette_verifier.py](app/skills/palette_verifier.py), [app/tutor/illustrated_book.py](app/tutor/illustrated_book.py) (CharacterBible + palette lock to the new brand palette); [book.js](app/web/static/book.js) + [style.css](app/web/static/style.css) (display rules); new tests in `tests/unit`.

**Implementation steps.**
1. Update the palette-verifier's target palette to the brand tokens (claret/gold/sage/cream/ink + bounded per-book extension); reject/regenerate off-palette art (the existing deterministic gate, re-pointed).
2. Confirm CharacterBible enforces the recurring cast (fox mascot) cross-page.
3. Enforce display rule: illustration frames/opens/rewards but **never sits beneath reading text** (CSS + render logic); every image has alt text; decorative art `aria-hidden`; text-only decodable fallback always available (already exists — verify it stays the graceful path).
4. Keep generation explicit/opt-in and cached per learner (cost discipline, §17).

**Testing strategy.** `pytest tests/unit` incl. a new palette-verifier test against the brand palette and a test asserting the text-only fallback path. Manual (creds-gated): generate a book, confirm on-palette art, consistent character, calm degrade when image gen fails. Respect the 2 req/min image quota (use `PHONO_STUB_IMAGES` for offline testing).

**Accessibility checklist.** ☐ Alt text on every meaningful image. ☐ Decorative art hidden from SR. ☐ Illustration never overlaps/underlays reading text. ☐ Fallback (text-only decodable book) verified.

**Rollback.** Flag `ILLUSTRATION_BRAND_PALETTE`; revert palette target to prior. The read loop never depends on illustration, so worst case degrades to text-only — no user-facing breakage.

---

## New invariant tests introduced (summary)
- `test_copy_invariants.py` (PR3): no forbidden lexicon / no score string in child-facing payload.
- Reader-settings persistence smoke (PR4, manual + optional JS test).
- Palette-verifier brand-palette test + text-only fallback test (PR12).
- These encode the design system's non-negotiables (§19) so a future change can't silently re-introduce shame mechanics.

## What this plan deliberately does NOT do
- Touch the deterministic loop, BKT model, planner, or schemas.
- Change payload *shapes* the `tests/unit` suite asserts (only string values + additive fields).
- Ship dark mode (deferred, design-system §1.7).
- Build the marketing site or print toolkits (system is *built to extend* there; out of this app-first engagement's scope).

---

## Self-critique (per process)
- *"Twelve PRs is a lot for a solo founder."* True — so they're ordered by value-per-risk: PR1–PR5 alone (tokens, kill the shame leak, plain language, the sacred reading face, the on-ramp) deliver most of the emotional turnaround; PR6–PR12 are polish/structure that can wait or be parallelized. The plan is a menu with a spine, not an all-or-nothing.
- *"Copy is split between PR3 and the screen PRs — risk of collision."* Flagged explicitly: PR3 owns shared + backend strings + the glossary; screen PRs own their inline labels and reference the glossary. Sequence PR3 before the screen PRs to avoid churn.
- *"Are the flags real rollback, or theater?"* For PR8/PR12 the flag genuinely restores prior behavior because the backend/event contracts are unchanged — verified by keeping the same event subscriptions and payload shapes. For pure-CSS PRs, `git revert` is the honest rollback.
- *Residual risk:* exact legacy-variable usage in `style.css` isn't fully mapped here; PR1 must begin by grepping `var(--coral|--navy|--tundora)` to size the compatibility shim before writing it.

## Gate
Phase 6 is complete: a sequenced, safe, reversible PR roadmap with objectives, affected files, steps, testing, accessibility checklists, and rollback for each.

**Awaiting approval to proceed to Phase 7 — Implementation**, starting with **PR 1 (Token & type foundation)**. Per the process, I'll implement one PR at a time and, after each, explain the changes, tradeoffs, and risks, and request review before continuing.
