# Phono / StoryForge — Design System (Phase 4)

*The single source of truth for the StoryForge identity. Every screen, component, and future surface derives from this document. Built on the approved Phase-3 direction: **The Reading Room**, governed by **The Clear Path** (the decode is sacred), endorsed by **The Lighthouse** (the Phono parent). It supersedes any prior visual system for new work.*

**Governing one-liner:** *Phono is the trusted institution that points the way; StoryForge is the beautiful, calm, dignified reading room it leads your child into.*

**Three rules that win every tie-break:**
1. **The decode is sacred.** Any beauty decision that taxes a struggling reader loses. Romance lives in the chrome and the celebration — never in the child's reading moment.
2. **Effort, never accuracy; celebration, never score.** No percentages, ranks, streaks-as-pressure, or "wrong/failing" in any child-facing surface.
3. **Two audiences, one surface.** The Reading face (calm, child) and the Insight face (analytical, adult, opt-in) are layered, never merged; the child never auto-sees errors.

**Accessibility target:** **WCAG 2.1 AA minimum**, with **AAA contrast (≥7:1) for all child reading text** (proposed and adopted here, since the brief pinned none). Implementation is token-first: everything below maps to CSS custom properties for the vanilla-JS app in `app/web/static/`.

---

## 1. Color

### 1.1 Philosophy
Bookish, warm, low-arousal. Claret is the **family signature** (the Phono mark, spines, covers). Gold means **earned celebration only** — so it always *means* something. Sage carries **growth/progress and never reads as a score**. The child reads ink-on-cream at maximum contrast; color expression is reserved for chrome. Neutrals are warm (paper/stone), never pure cool grey — calm must never tip clinical.

### 1.2 Base palette (raw tokens)

| Token | Hex | Role |
|---|---|---|
| `--ink` | `#23262C` | Primary text & structure (printer's ink) |
| `--ink-soft` | `#3A3D42` | Secondary text |
| `--claret` | `#5C2A33` | Brand signature; primary actions; spines |
| `--claret-tint` | `#EBDADD` | Claret wash / selected backgrounds |
| `--gold` | `#B0863F` | Celebration **fills/graphics only** (not text) |
| `--gold-deep` | `#6E5320` | Text/icon-safe gold (celebration labels) |
| `--gold-tint` | `#F0E4CC` | Celebration background wash |
| `--sage` | `#7C9486` | Growth **fills/graphics only** (not text) |
| `--sage-deep` | `#3E5247` | Text/icon-safe sage (growth labels) |
| `--sage-tint` | `#DCE5DE` | Growth background wash |
| `--paper` | `#F8F4EA` | App ground |
| `--paper-50` | `#FBF8F0` | Lightest surface |
| `--cream` | `#F4EDDE` | **Reading ground** (the child's page) |
| `--paper-sunken` | `#EFE7D6` | Wells, insets, skeletons |
| `--white` | `#FFFFFF` | Insight cards / data surfaces |
| `--stone-600` | `#6E6A60` | Muted text (AA on cream) |
| `--stone-400` | `#9A958A` | Quiet UI, disabled, cloth grey |
| `--stone-200` | `#CFC9BD` | Subtle dividers on dark |
| `--line` | `#E4DBC8` | Hairlines & borders |

### 1.3 Semantic tokens

| Token | Value | Use |
|---|---|---|
| `--text-primary` | `--ink` | Body & reading text |
| `--text-secondary` | `--ink-soft` | Supporting copy |
| `--text-muted` | `--stone-600` | Captions, meta |
| `--surface-app` | `--paper` | App background |
| `--surface-reading` | `--cream` | Reading face only |
| `--surface-card` | `--white` | Insight/data cards |
| `--border` | `--line` | All hairlines |
| `--accent` | `--claret` | Primary brand action |
| `--celebrate` | `--gold` / `--gold-deep` | Earned moments |
| `--growth` | `--sage` / `--sage-deep` | Progress, mastery |
| `--focus-ring` | `--claret` | Keyboard focus |

### 1.4 State colors (kept separate from the accent; gentle by mandate)
**Never used in child-facing surfaces.** The harsh-red convention is forbidden product-wide — even system errors stay warm.

| Token | Hex | Contrast on cream | Use |
|---|---|---|---|
| `--info` | `#2C5E7A` (deep tide) | 6.0:1 | Parent/system info, the Phono wayfinding accent |
| `--positive` | `--sage-deep` `#3E5247` | 7.2:1 | Confirmations, growth |
| `--caution` | `#7E5523` (text) / `#9A6B2E` (large/UI) | 5.3:1 / 3.99:1 | Gentle "heads-up" (adult only) |
| `--system-error` | `#8C3A2E` (muted brick) | 6.5:1 | Adult/system failures only; calm, with a fix |

### 1.5 Running-record palette (the adult miscue heatmap — deliberately de-alarmed)
The running record is **adult-only** and must read as *analysis*, not *judgement*. No bright red.

| Miscue type | Token | Treatment |
|---|---|---|
| Correct | `--ink` on `--cream` | Plain text, no highlight |
| Self-correction | `--sage` underline | The *win* of the heatmap — gently celebrated |
| Substitution | `--caution` dotted underline | Neutral "swapped a sound" |
| Omission | `--stone-400` strikethrough-light | Quiet "skipped" |
| Insertion | `--info` caret | Quiet "added" |
| Target grapheme | `--claret` underline | Today's focus, tied to brand |

### 1.6 Verified contrast (WCAG 2.1)
ink/cream **13.0:1** · ink-soft/cream 9.4:1 · claret/cream **9.8:1** (white 11.5:1) · sage-deep/cream 7.2:1 · gold-deep/cream 6.2:1 · info/cream 6.0:1 · system-error/cream 6.5:1 · stone-600/cream 4.6:1.
**Rule:** `--gold` (2.85:1) and `--sage` (2.80:1) are **graphics/fills only**, never text or essential icons; their `-deep` variants are the text-safe forms.

### 1.7 Dark mode
Deferred (not in app scope today), but tokens are structured to invert: `--surface-reading` → a warm dark `#2A2622`, `--text-primary` → `#F0E8D8`, claret → a lighter `#C98494` for AA. **Do not** ship dark mode for child reading without re-validating decode contrast.

---

## 2. Typography

### 2.1 Faces & rationale
Three roles. All recommendations are **open-source** (solo-founder sustainable) and screen+print capable.

| Role | Recommended | Rationale | Fallback stack |
|---|---|---|---|
| **Reading / Display serif** (the protagonist) | **Literata** | A reading serif designed for long-form on-screen reading; warm, bookish, fairly disambiguated letterforms; variable; free. | `"Literata","Iowan Old Style",Palatino,Georgia,serif` |
| **UI / Wayfinding sans** | **Source Sans 3** | Warm humanist grotesque that harmonizes with Literata; legible at small sizes; not an over-used "default." | `"Source Sans 3","Source Sans Pro",system-ui,sans-serif` |
| **Data / Numerals** | **Source Code Pro** (tabular) | Aligns digits in the Insight layer; pairs with the family. | `"Source Code Pro",ui-monospace,Menlo,monospace` |

> **The decode is sacred — the reading-text decision is a feature, not a default.** The child's *decodable practice text* defaults to Literata at generous size/spacing, but ships with a **Reader Settings** control (see §15.3) offering: (a) a humanist sans alternative tuned for decoding — recommend **Lexend** (research-backed reading-proficiency face with disambiguated b/d/p/q and single-story *a*); (b) adjustable letter-, word-, and line-spacing; (c) larger sizes. Default chosen with the founder against decoding criteria; the toggle guarantees no child is stuck with a face that doesn't decode for them.

**Forbidden:** decorative/calligraphic display serifs for reading text; condensed faces anywhere near child text; justified text (always left-aligned, ragged right); all-caps for reading content (labels only).

### 2.2 Type scale (1.20 minor-third, base 16px)
Tokens are `--fs-*`. Reading text intentionally **larger** than typical UI.

| Token | px / rem | Line-height | Typical use |
|---|---|---|---|
| `--fs-display` | 44 / 2.75 | 1.05 | Story covers, hero |
| `--fs-h1` | 33 / 2.06 | 1.12 | Screen titles |
| `--fs-h2` | 26 / 1.63 | 1.2 | Section heads |
| `--fs-h3` | 21 / 1.31 | 1.3 | Card titles |
| `--fs-reading` | **25 / 1.56** | **1.85** | **Child decodable text** (min; user-scalable to 32) |
| `--fs-body` | 17 / 1.06 | 1.55 | Adult body copy |
| `--fs-ui` | 15 / 0.94 | 1.45 | Controls, labels |
| `--fs-caption` | 13 / 0.81 | 1.45 | Meta, captions |
| `--fs-micro` | 11 / 0.69 | 1.4 | Eyebrows (uppercase, +.14em tracking) |

**Rules:** body measure **60–66ch**; child reading measure **50–55ch**. Headings `text-wrap:balance`. Numerals in tables/charts `font-variant-numeric:tabular-nums`. Weights: serif 400/500/600; sans 400/600/700. Never fake-bold; never letter-space lowercase reading text.

---

## 3. Spacing

8px-based scale with 4px half-steps. Tokens `--sp-*`. Layout uses **flex/grid `gap`**, never per-element margins that collapse.

| Token | px | Token | px |
|---|---|---|---|
| `--sp-1` | 4 | `--sp-6` | 32 |
| `--sp-2` | 8 | `--sp-7` | 40 |
| `--sp-3` | 12 | `--sp-8` | 48 |
| `--sp-4` | 16 | `--sp-9` | 64 |
| `--sp-5` | 24 | `--sp-10` | 80 |

Component padding baseline: cards `--sp-5`/`--sp-6`; touch controls ≥ `--sp-4` vertical; section rhythm `--sp-8`/`--sp-9`. Reading face uses *more* space than the rest of the app — generosity is the calm.

---

## 4. Grid & layout

- **Breakpoints:** `sm` ≤599 (1-col, mobile-first for the future app) · `md` 600–999 (8-col) · `lg` ≥1000 (12-col).
- **Container max:** 1080px app chrome; **reading column capped at 34rem** regardless of viewport (protects measure).
- **Gutters:** 16px (`sm`) → 24px (`md`) → 32px (`lg`).
- **Layout philosophy:** one focal action per view (Clear Path); the reading panel is always the visual center on the Reading face; Insight adds editorial sidebars around — never on top of — the reading column.

---

## 5. Radius, shadow & elevation

### 5.1 Radius (book-craft, not bubbly — used purposefully, not everywhere)
`--radius-xs` 3px (spines, chips) · `--radius-sm` 6px (buttons, inputs) · `--radius-md` 10px (cards) · `--radius-lg` 14px (surfaces, modals) · `--radius-pill` 999px (the "Read aloud" CTA only). **No blanket `rounded-lg`** — radius signals object type (a spine is sharp; a friendly callout is soft).

### 5.2 Shadow & elevation (warm-tinted; light from above, like a real shelf)
Shadows use `rgba(35,38,44,*)` (ink), never pure black.

| Token | Value | Use |
|---|---|---|
| `--elev-0` | none + `1px --line` | Flat cards, default |
| `--elev-1` | `0 1px 2px rgba(35,38,44,.06)` | Resting cards |
| `--elev-2` | `0 4px 12px -4px rgba(35,38,44,.12)` | Raised / hover |
| `--elev-3` | `0 12px 28px -10px rgba(35,38,44,.18)` | Books, popovers |
| `--elev-4` | `0 24px 48px -24px rgba(35,38,44,.30)` | Modals, the open book |
| `--elev-spine` | `inset -6px 0 12px -8px rgba(35,38,44,.40)` | Book-spine depth |

---

## 6. Iconography

- **Style:** editorial line icons — 1.5px stroke at 24px, round caps/joins, 24px grid with 2px safe area. Warm-geometric (Aicher lineage) but literary in restraint — closer to imprint colophons than app-store glyphs.
- **Color:** `--ink` default; `--claret` for active/brand; `--stone-400` for quiet. Never gold/sage as the sole carrier of meaning (contrast).
- **Core set (start small, grow deliberately):** book/story, shelf, bookmark, sound/listen (a soundwave), microphone, fox (brand mascot mark), beacon (Phono wayfinding), arrow/route, calendar/session, heart-win, settings, help.
- **Rules:** icons accompany text labels in navigation (never icon-only nav); decorative-only icons get `aria-hidden`; pictograms must read at 16px. No filled+outline inconsistency within a set.

---

## 7. Buttons & actions

### 7.1 Hierarchy
| Variant | Look | Use |
|---|---|---|
| **Primary** | `--claret` fill, `--paper-50` text, `--radius-sm` | The one main action per view |
| **Read-aloud (child)** | `--claret` **pill**, mic icon, large (≥52px tall) | The hero child action; unmistakable |
| **Secondary** | `--ink` 1.5px outline, transparent fill | Alternative actions |
| **Tertiary / ghost** | `--claret` text only | Low-emphasis (e.g., "type instead") |
| **Celebration** | not a button — `--gold` is reserved for *earned* states, never to bait a click |

### 7.2 Sizing & states
- Heights: sm 36 / md 44 / lg 52px. **Min touch target 44×44** (`sm` only for dense adult tables).
- States: **hover** = darken 6% + `--elev-2`; **active** = darken 10%, translateY(1px); **focus-visible** = 2px `--focus-ring` ring, 2px offset (always visible, never removed); **disabled** = `--stone-400` text on `--paper-sunken`, no shadow, `cursor:not-allowed`.
- **Labels say what happens** ("Read aloud", "Start tonight's story", "See why this book"), never "Submit"/"OK". Confirmation toasts use past tense ("Saved", "Added to the shelf").

---

## 8. Cards & surfaces

A small, named set — every surface is one of these:

| Card | Anatomy | Radius / Elev | Use |
|---|---|---|---|
| **Book (cover)** | claret/sage cloth field, gold rule, serif title, fox motif | md / elev-3 | A story to read; library items |
| **Spine** | 46×128, vertical serif title, `--elev-spine` | xs | The earned shelf |
| **Sign** (info) | white, `--info` left rule, sans label + serif body | md / elev-1 | Wayfinding, Phono guidance |
| **Insight panel** | white, hairline, editorial sidebar | md / elev-0 | Adult analytics |
| **Note from a friend** | `--gold-tint` bg, soft radius-lg, hand-mark | lg / elev-0 | Warm coaching (Kitchen Table voice) |
| **Why-this-book** | `--gold-deep` left rule on white, serif | md / elev-0 | The reasoned moment, plain-language |

Cards never nest more than one level. Padding `--sp-5`/`--sp-6`. The Reading face uses **no card chrome** around the passage — the page is the surface.

---

## 9. Forms & inputs

- **Layout:** label **above** field (never placeholder-as-label); 1.5px `--line` border; `--radius-sm`; min height 44px; generous `--sp-4` padding; help text below in `--text-muted`.
- **Focus:** border → `--claret`, plus the focus ring. **Filled/active** state clearly distinct from empty.
- **Validation (calm, never shaming):** inline, on blur, with a **fix, not a blame** — "We'll need your child's first name to personalize the stories" (not "Required field"). Color `--caution` text + an icon + text (never color alone). **No validation styling ever appears on child-facing inputs.**
- **Setup form (onboarding):** one question per step where possible (Clear Path); warm microcopy; age as a friendly band picker, not a number stepper; "interest" as selectable chips with examples.

---

## 10. Navigation

**Replace the engineer-facing "loop rail" with a human session arc.** (Phase 1 §15 structural recommendation, now systematized.)

- **Top bar (persistent):** Phono beacon mark + `StoryForge` wordmark (left) · the growth meter reframed as **"Sounds we've practiced"** + a calm sage progress, *no percentage* (right) · the **Shelf** entry (the child's earned books) promoted to first-class.
- **The session arc** (replaces loop-rail): **Tonight's story → Read together → How it went → What's next.** Four human steps; the technical loop (plan/generate/verify/assess/adapt) survives only in an optional adult/educator "behind the scenes" view.
- **Mode control:** reframed from "Reading/Insight" jargon to **"Reading" / "For grown-ups"** with the privacy default preserved (stays on Reading after scoring; the grown-up view gets a quiet pip, never auto-opens).
- **Mobile:** bottom tab bar for the future app (Story · Shelf · Journey · Guide); icon **+ label** always.
- **Wayfinding rule (Lighthouse):** the user always knows where they are and what's next; the path to a specialist (the Phono directory) is always reachable, never buried.

---

## 11. Tables (adult Insight & Journey only)

Tufte-clean: no vertical rules, hairline `--line` row separators only, generous row height (`--sp-4`), `tabular-nums`, left-align text / right-align numbers, sticky header in `--fs-micro` uppercase. Row hover `--paper-50`. The Journey history table highlights **target changes** (claret) and **newly-learned sounds** (sage) — the adaptation proof — and never shows an accuracy column as the primary read.

---

## 12. Charts & data viz

Honest, minimal-ink, framed by **effort and growth, never accuracy/comparison**.

- **Growth line (the Journey hero):** sage area fill (low opacity) + 2px sage stroke + a single **gold endpoint dot** (the emphasized "where you are now"). Faint baseline only; no gridlines, no y-axis percentages — the axis is *sessions* (effort), the rise is *sounds learned*. Sparkline form in the top bar.
- **Mastery path:** horizontal grapheme nodes by level; states **learned** (sage fill), **today** (claret glow), **coming up** (cloth-grey dashed). Tap → plain-language detail ("a sound your reader knows well"), never a raw probability to a parent (raw % only in the deep "behind the scenes" view).
- **Running record:** the de-alarmed palette (§1.5); adult-only.
- **Rules:** color is never the sole encoder (shape/label too); every chart has a one-line plain-language caption stating what it means; no 3D, no gradients-as-decoration, no chartjunk. Charts get the same craft as type — emphasized endpoint, faint grid, considered fill.

---

## 13. Empty, loading & degraded states

These are **designed places in the journey, not error fallbacks** (Phase 1 §15.7).

- **First-run / empty shelf:** a warm illustrated empty shelf — *"This is where your reader's books will live. Let's make the first one."* + one CTA. Never an empty frame.
- **Journey with 0–1 sessions:** a single sage dot + *"Your line is just beginning."*
- **Loading a story ("forging"):** calm, count-**up** language — *"Making a story just for tonight…"* — with a paper-toned skeleton of the page (not a spinner of anxiety). The book "binds" into place.
- **Degraded (voice/illustration/export down):** a calm `--info` **Sign** card — *"Tonight we'll read with typing instead of the microphone — everything else works."* Dismissible; clears when the loop is healthy. Degradation is **calm and partial**, never a crash; each axis degrades alone.
- **No harsh error states for the child, ever.** System errors are adult-only, warm, and carry a next step.

---

## 14. Onboarding

The missing warm on-ramp (Phase 1 §15.3). Reassurance **before** data.

1. **"You found the right place."** — one calm screen: you're not alone; this is built on the science specialists use; we'll start with one short story tonight. (Sets emotional safety.)
2. **Who are we reading with?** — child's first name, age band (friendly picker), an interest (chips). One thing at a time.
3. **How this works (90 seconds).** — short, plain: ~15 minutes, a few nights a week; progress is about showing up, not scores; a specialist is the best next step and we'll help you find one (honesty up front).
4. **First story.** — straight into Tonight's Story. Time-to-first-value is the metric.

Tone: neighborly, specific, no jargon, no "mastery/grapheme." Skippable for returning users.

---

## 15. Motion & animation

### 15.1 Principles
Literary pacing: the page-turn and the gentle reveal. Motion **confirms and calms**, never excites or pressures. Timers count **up**. Celebration is earned and brief.

### 15.2 Tokens
- Durations: `--motion-fast` 160ms (state) · `--motion-base` 280ms (transitions) · `--motion-page` 420ms (page-turn/story open) · `--motion-celebrate` 900ms (earned moment).
- Easing: `--ease-standard` `cubic-bezier(.2,.7,.2,1)` · `--ease-settle` `cubic-bezier(.16,1,.3,1)` (book settling).
- Signature moments: **story opens** like a book; **finished story slides onto the shelf**; the **"what's next" adapt beat** — the gold/claret focus travels gently to the next sound *after the adult opts into the grown-up view* (privacy boundary preserved), with a plain-language caption ("Sam learned /sh/. Next we'll practice /ch/.").

### 15.3 Reduced motion & reader settings
- `prefers-reduced-motion: reduce` → all durations collapse to 0; page-turns become instant cross-fades; the adapt beat becomes a static state change. **Required, not optional.**
- **Reader Settings** (accessibility-first control, §2.1): reading typeface (serif default / sans option), text size (1×–1.6×), letter/word/line spacing, and a "calm" toggle that removes all non-essential motion. Persisted per learner.

---

## 16. Responsive behavior

- **Mobile-first** for the future app; the web demo is responsive desktop→phone today.
- Reading column never exceeds 34rem; on mobile it gets the full width minus `--sp-4` gutters and *increased* line-height.
- Top-bar growth meter collapses to the sparkline + Shelf icon on `sm`; the session arc becomes a compact stepper.
- Touch targets ≥44px on all touch viewports; hover-only affordances always have a tap/focus equivalent.
- **Print** (toolkits, take-home books): the system maps to print — claret/ink/cream survive grayscale (claret→dark grey, gold→mid-grey, sage→light grey all remain distinguishable by value, verified by the existing palette-verifier); reading text at 12–14pt min on standard paper; never rely on color alone in print.

---

## 17. Illustration system (AI-assisted, verifier-governed)

The approved model: per-story art generated AI-assisted, kept on-brand and affordable by the app's **existing palette-verifier + character-consistency (CharacterBible) machinery**. This is the brand's delight engine; it must stay disciplined.

- **Style spec:** dignified picture-book illustration (Sendak/Klassen/Blexbolex lineage) — warm, characterful, restrained; **never Disney-cute, never clip-art, never uncanny-AI**. Flat-ish shapes, honest texture, generous negative space.
- **Palette lock:** every generated image is verified against the brand palette (claret/gold/sage/cream/ink + a small per-book extension) by the deterministic `palette_verifier`; off-palette art is rejected/regenerated. **No image ships unverified.**
- **Character consistency:** a small recurring cast (the fox mascot + a rotating set) defined in a **CharacterBible**, enforced cross-page so a child's book feels authored, not stitched.
- **Hard rules:** illustration **never sits beneath reading text** (decode sacred); it frames, opens, and rewards — covers, spreads, the shelf, celebrations. Every image has alt text. Decorative art is `aria-hidden`. A deterministic fallback (text-only decodable book) always exists if generation fails — degradation stays calm.
- **Cost discipline:** generation is explicit/optional (not load-bearing on the read loop), batched, and cached per learner; reuse covers across sessions where possible.

---

## 18. Voice & tone (capsule — full guide in Phase 6/brand kit)

Two voices, one personality (the knowledgeable neighbor):
- **To the parent:** warm, plain, specific, honest. Names the exact fear, the exact technique, the exact age. Never clinical, never salesy, never "miracle." Specialist-first honesty stated plainly.
- **To/about the child:** gentle, success-first, story-led. Effort and wins, never scores. "Tough" is never "bad."
- **Forbidden words in user-facing copy:** mastery, grapheme, ZPD, BKT, decodability, objective, "loop," accuracy %, "wrong," "failing," "behind." (These live only in internal tooling / the optional deep adult view.)
- **Preferred:** "sounds," "the next sound your reader is ready for," "stories on the shelf," "sessions together," "let's start tonight."

---

## 19. Token implementation note (for Phase 6/7)

All tokens above become `:root` CSS custom properties in a new `app/web/static/tokens.css`, consumed by the existing components. Migration is **additive and incremental** (Phase 6 plan): introduce tokens → re-skin one component family per PR → never redesign multiple systems at once. The reading-face contrast and the no-shame/effort-only rules are **regression-test-worthy invariants**, not style preferences.

---

## 20. Self-critique (per process)

**What a Creative Director would challenge:**
- *"You recommend a serif for a dyslexia product — much dyslexia guidance favors humanist sans."* Acknowledged head-on: the system makes the *reading face user-selectable* with a research-backed sans (Lexend) and spacing controls, and mandates the final default be chosen against decoding criteria with the founder — not by my aesthetic preference. The serif romance is quarantined to chrome/covers. This is the single most important honesty in the system.
- *"Gold and sage fail text contrast — is the palette too pretty to be accessible?"* Caught and handled: their `-deep` variants are the text-safe forms; the pretty tones are graphics-only, documented with measured ratios. No essential information rides on a sub-4.5:1 color.
- *"A solo founder can't maintain a large system."* The set is deliberately small (named cards, a tight icon core, three faces, one accent that does the work). Tokens + additive migration keep maintenance low.

**What a first-time user (scared parent) would struggle with:** if Reader Settings is buried, a child who can't decode the default serif is stuck — so the spec elevates it and offers it in onboarding. The biggest residual risk.

**Assumptions to validate in Phase 5/6:** Literata vs. Lexend as the *default* reading face (test with the child); that warm book-craft reads premium-trustworthy to US parents, not old-fashioned; that the gold-only-for-earned rule survives contact with real screens (don't let it creep into decoration).

---

## 21. Gate

Phase 4 is complete: a full, token-first design system with verified contrast, derived from the approved direction. Companion: a visual reference sheet (artifact).

**Awaiting approval to proceed to Phase 5 — the UX Audit (`ui-audit.md`)**, a screen-by-screen audit of the current app against this system (what works / what's confusing / what changes / why / expected impact). The two open type/illustration validations above are flagged to resolve as we get into specifics.
