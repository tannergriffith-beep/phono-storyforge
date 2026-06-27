# Repository Design Audit

**Purpose:** Identify every source of *visual anchoring* in this repository ahead of a
ground-up product identity reboot. The goal is a **design-neutral implementation
repository**: product strategy, functionality, architecture, and engineering stay intact
and active; the previous visual identity (brand, color, type, design system, mockups,
visual rationale, rendered assets) is clearly separated from the active project.

**Status:** Audit only. No files have been moved, rewritten, or deleted to produce this
document. Recommendations below are proposals for Phases 2–6.

---

## How to read this

Each row is classified into one of four dispositions:

| Disposition | Meaning |
|---|---|
| **ARCHIVE** | Pure design document, visual rationale, or rendered visual asset. Not required to build or run the app. Move to `archive/legacy-design/` (preserve, don't delete). |
| **KEEP + FLAG** | Functional code or engineering doc that the running app/tests depend on, but which *embeds* specific visual-identity values (palette hexes, font names, aesthetic descriptors). Stays active — archiving it would break the build. Flagged so a redesign treats it as *implementation truth, not aesthetic prescription*. |
| **NEUTRALIZE** | Active documentation that mixes product/engineering (keep) with prescriptive visual identity (rewrite/remove the visual parts). |
| **KEEP (authoritative)** | Design-neutral product strategy. The intended starting point for the redesign. |

**Confidence** reflects how clear-cut the disposition is, not how important the file is.

---

## A. Pure design documents & rendered assets → ARCHIVE

| File | Why flagged | Recommendation | Confidence |
|---|---|---|---|
| `docs/DESIGN.md` | The canonical previous design source-of-truth. Locked color tokens (§10.1, 9 hexes), contrast tables, typography roles (Trebuchet/OpenDyslexic/Lexend), motion specs, component inventory, mockup/showcase references, and full aesthetic rationale ("the Adapt beat", karaoke glow, gold tint). This is the single largest visual anchor in the repo. | Archive to `archive/legacy-design/`. Not imported by any code. | **High** |
| `docs/illustration-style-guide.md` | Prescribes the illustration aesthetic: "cut-paper collage," 2px stroke, flat fills, the 6-color illustration palette, age-band visual modifiers, anti-gamification visual rationale. Pure visual style spec. | Archive. Not referenced by any code (the *functional* version of these rules lives in `app/brand.py`, which stays). | **High** |
| `app/web/static/styleguide.html` | A standalone "Phono StoryForge — Design System" gallery page: color swatches with hexes/roles, typography specimens, component showcase. It is **not linked or routed** by the app (no reference anywhere) — purely a design-system artifact. | Archive. It depends on `style.css` for rendering, so note in ARCHIVE.md that it won't render standalone; it is kept as a record of the prior design system. | **High** |
| `results/sample_book/page_01.png … page_06.png` | Six rendered storybook pages ("Sam the Fox") in the prior illustration aesthetic (cut-paper collage, legacy palette). These are *visual assets* expressing the old identity. They demonstrate a real capability (the pipeline produces decodable illustrated books) but their *appearance* is exactly the visual language being rebooted. | **Decision (kept active):** these stay in `results/` as capstone demo *evidence* (referenced as proof in `README.md`, `video-skeleton.md`, `writeup-skeleton.md`, `build-plan.md`). They are **flagged as legacy-look**: a note in `README.md` and `DESIGN_GUIDELINES.md` records that their appearance is the prior identity, not a target for the redesign. The reboot regenerates them from new brand values in `brand.py`. | **Medium → resolved (keep + flag)** |

---

## B. Functional code embedding visual identity → KEEP + FLAG

These are required to build, run, and test the application. Archiving any of them breaks
the app and the 260-test suite, which would violate the core preservation requirement.
They stay **active**; the redesign should read them as *what the implementation currently
does*, not as a design recommendation to preserve.

| File | What it embeds | Recommendation | Confidence |
|---|---|---|---|
| `app/brand.py` | The locked 8-color palette (name→hex→role), the cut-paper illustration style preamble, age-band visual modifiers. Single source of truth for illustration look. Imported by `illustrator.py`, `agent.py`, and 3 tests. | Keep active. Flag in `DESIGN_GUIDELINES.md` as the legacy palette/style a redesign will replace. A future redesign edits the *values* here; it does not delete the module. | **High (keep)** |
| `app/skills/palette_verifier.py` | Deterministic guardrail that snaps generated image colors to the brand palette. The *guardrail mechanism* is engineering; the *palette it enforces* is visual identity (sourced from `brand.py`). | Keep active (it's a real propose/verify guardrail + tested). Flag that the enforced palette is legacy. | **High (keep)** |
| `app/illustrator.py` | Composes brand style + character bible into image prompts; regenerates off-palette pages. Functional pipeline; references the cut-paper aesthetic via `brand.py`. | Keep active. Flag aesthetic descriptors as legacy. | **High (keep)** |
| `app/doc_export.py` | Google-Doc export styling: OpenDyslexic body, Poppins title, palette-tinted formatting. Functional exporter; carries specific font/color choices. | Keep active. Flag the font/color literals as legacy visual choices. | **High (keep)** |
| `app/web/static/style.css` | The live web app's full stylesheet — the entire current visual system (palette CSS vars, type, motion, layout). It *is* the running UI. | Keep active (the app needs it to render). This is the densest visual-identity surface in code; a redesign will largely replace it, but it must stay until then so the app runs. Flag prominently. | **High (keep)** |
| `app/web/static/index.html`, `render.js`, `components/*.js` (`loopRail`, `modeToggle`, `whyCard`, `masteryPath`, `journey`, `adaptBeat`, `degradeBanner`) | The live UI structure/behavior. Class names and structure express the current design language (and cite `DESIGN.md §` in comments). | Keep active (functional UI). Flag that structure/class naming encodes the legacy design language. | **High (keep)** |
| `app/web/viz.py` | Emits the data the UI renders (e.g. heatmap kinds, mastery values). Mostly data, light presentation coupling. | Keep active. Low visual-identity content; no action beyond awareness. | **High (keep)** |
| `app/tutor/illustrated_book.py`, `scripts/build_sample_book.py` | Drive the illustration pipeline; reference cut-paper/character-bible. Functional. | Keep active. Flag aesthetic descriptors as legacy. | **High (keep)** |
| `app/schemas.py` | Contains `CharacterBible` / `palette_colors` fields. Data contracts, not aesthetics per se. | Keep active. No action. | **High (keep)** |
| `tests/unit/test_brand.py`, `test_palette_verifier.py`, `test_illustrator.py` | Assert against the locked palette/style. | Keep active (part of the passing suite). If the redesign changes palette values, these tests update with the code — expected, not an anchor to remove now. | **High (keep)** |

> **Key tension recorded here:** `app/brand.py` + `style.css` + `doc_export.py` are
> simultaneously *engineering* (the app needs them) and *visual identity* (they hold the
> exact palette and fonts). The guiding rule "preserve strategy, archive visual
> implementation" cannot mean *delete the running stylesheet* — that breaks the app. The
> resolution: **keep them active, flag them loudly**, and let `DESIGN_GUIDELINES.md`
> direct the redesign to treat code as implementation-truth while sourcing *aesthetic*
> decisions only from product strategy.

---

## C. Active documentation to NEUTRALIZE

Keep the product/engineering substance; rewrite or remove prescriptive visual identity.

| File | Visual references found | Recommendation | Confidence |
|---|---|---|---|
| `README.md` | "locked Phono palette," "cut-paper art," "OpenDyslexic body, Poppins title," "on-brand-verified," `brand.py` description as "Locked Phono brand: palette, cut-paper style." | Rewrite the illustration/brand passages to describe the *mechanism* (LLM proposes art → deterministic palette verifier enforces a defined brand palette — a propose/verify guardrail) without enshrining the specific aesthetic as something to preserve. Keep all product/architecture/evidence content. Repoint `results/sample_book/` references to the archive. | **High** |
| `docs/integration-illustrated-book-loop.md` | Palette verifier, cut-paper, on-brand references (6 hits) — but in an *engineering* context (how the pipeline integrates). | Light neutralization: keep the integration engineering; soften aesthetic descriptors to "the brand palette / current illustration style (see `brand.py`)." | **Medium** |
| `docs/video-skeleton.md` | References `results/sample_book/*.png`, "cut-paper art," the design showcase artifact. It's a demo *script*. | Repoint asset paths to archive; soften aesthetic descriptors. Keep the demo structure. | **Medium** |
| `docs/writeup-skeleton.md` | References `results/sample_book/*.png` as proof artifacts. | Repoint asset paths to archive. | **Medium** |
| `docs/build-plan.md` | References `results/sample_book/`, on-brand claims. | Repoint asset paths; soften aesthetic descriptors. | **Medium** |
| `docs/stage-d-prime-flywheel.md` | 2 palette/brand mentions, engineering context. | Light touch; soften aesthetic descriptors if any prescribe identity. | **Low** |
| `GEMINI.md` | **None found.** Pure development-workflow guide. | No change. | **High (no change)** |

---

## D. Authoritative product strategy → KEEP (do not touch)

| Path | Why | Recommendation | Confidence |
|---|---|---|---|
| `design-context/**` (`design-brief.md`, `01`–`08`, `README.md`) | A **complete, already design-neutral** product/customer/business briefing, explicitly written for a rebrand ("no previous visual identity in it"). This is exactly the intended starting point for the redesign and the anchor for `DESIGN_GUIDELINES.md` Phase 5. | Keep as the authoritative source. **Note:** currently *untracked* in git (`?? design-context/`). Recommend committing it so it's durably part of the repo. `design-context/07-design-constraints.md` correctly states accessibility as functional requirements without prescribing visuals — preserve verbatim. | **High** |

---

## E. Not design-related (no action)

For completeness — confirmed clean of visual-identity prescription: all of `app/skills/`
except as noted, `app/store/`, `app/voice/`, `eval/**`, `tests/` (except the three brand
tests above), `docs/stage-d-independent-learner.md`, `pyproject.toml`, `Dockerfile`,
`agents-cli-manifest.yaml`. These are engineering/strategy and stay active untouched.

Untracked working dirs (`.phono-demo-data/`, `scratch/`, `artifacts/`) are not in git and
are out of scope for this audit.

---

## Summary of proposed dispositions

- **ARCHIVE (3 files):** `docs/DESIGN.md`, `docs/illustration-style-guide.md`,
  `app/web/static/styleguide.html`. *(The `results/sample_book/*.png` were considered for
  archiving but are kept active as capstone demo evidence, flagged as legacy-look.)*
- **KEEP + FLAG (functional code w/ embedded identity):** `app/brand.py`,
  `palette_verifier.py`, `illustrator.py`, `doc_export.py`, `style.css`, the web UI
  (`index.html`/`render.js`/`components/*`), `viz.py`, `illustrated_book.py`,
  `build_sample_book.py`, and the three brand tests.
- **NEUTRALIZE (docs):** `README.md` (primary), plus light touches to
  `integration-illustrated-book-loop.md`, `video-skeleton.md`, `writeup-skeleton.md`,
  `build-plan.md`, `stage-d-prime-flywheel.md`.
- **KEEP (authoritative):** `design-context/**` (recommend committing to git).
- **No change:** `GEMINI.md`, all engineering/strategy code and docs in section E.

**Nothing is recommended for deletion.** All archiving is *move*, preserving git history.

---

## Phase 6 — Verification (post-change review)

State after Phases 2–5 were executed.

### Done
- **Archived (git mv, history preserved):** `docs/DESIGN.md`, `docs/illustration-style-guide.md`,
  `app/web/static/styleguide.html` → `archive/legacy-design/`, with `ARCHIVE.md`.
- **Created:** `DESIGN_GUIDELINES.md` (root), `archive/legacy-design/ARCHIVE.md`,
  `repository-design-audit.md`.
- **Neutralized:** `README.md` (mechanism-only — palette/illustration described as a
  propose/verify guardrail; `app/brand.py`, `results/sample_book/` annotated as legacy +
  pointed at `DESIGN_GUIDELINES.md`; accessibility-motivated typeface preserved as a
  *function*, not a brand name). Light touches to `video-skeleton.md`,
  `writeup-skeleton.md`, `build-plan.md` (softened pure-aesthetic identity terms; kept
  accessibility and mechanism descriptions).
- **Repointed:** 7 `app/web/static/components/*.js` provenance comments from the moved
  `docs/DESIGN.md` to the archived path, labeled "(legacy, archived)".
- **Verified app integrity:** `app/web/static/styleguide.html` was unrouted/unreferenced —
  moving it broke nothing; no code referenced the moved docs. **`uv run pytest tests/unit`
  → 260 passed.**

### Remaining active files that still express visual identity — and the call on each

| Item | Why it still carries identity | Remain active? | Mitigation |
|---|---|---|---|
| `app/brand.py` | Holds the legacy palette hexes + illustration-style descriptors. | **Yes** — imported by `illustrator.py`, `agent.py`, 3 tests; the app/pipeline needs it. | Flagged in `DESIGN_GUIDELINES.md` §2 as values-to-replace, mechanism-to-keep. The redesign edits values here. |
| `app/web/static/style.css` | The live UI's entire visual system (palette vars, type, motion). | **Yes** — the app renders from it. Cannot archive without breaking the running demo. | Densest surface; flagged as the primary file a redesign will rework. |
| `app/web/static/index.html`, `render.js`, `components/*.js` | Class names/structure + provenance comments encode the prior design language. | **Yes** — functional UI. | Comments now clearly marked "(legacy, archived)"; structure is implementation, not prescription. |
| `app/doc_export.py` | Document typography/color literals (incl. a dyslexia-friendly body face — *accessibility*, preserve). | **Yes** — functional exporter. | Aesthetic literals flagged; accessibility intent preserved. |
| `app/skills/palette_verifier.py` (+ `illustrator.py`, `illustrated_book.py`, `build_sample_book.py`) | Enforce/compose the legacy palette + style. | **Yes** — guardrail + pipeline, tested. | Mechanism is identity-independent (enforces whatever `brand.py` defines). |
| `results/sample_book/*.png` | Rendered pages in the legacy illustration look. | **Yes** — kept as capstone *evidence* (your decision). | Annotated as legacy-look in `README.md` + `DESIGN_GUIDELINES.md`; regenerated from new values. |
| `tests/unit/test_brand.py`, `test_palette_verifier.py`, `test_illustrator.py` | Assert against the legacy palette/style. | **Yes** — part of the passing suite. | Update alongside `brand.py` when the redesign lands; not an anchor to remove now. |
| `docs/integration-illustrated-book-loop.md` | Engineering integration notes referencing the palette verifier / illustration. | **Yes** — accurate engineering record; references are to mechanism, not prescription. | Left intact by design; reads as "how the pipeline works." |

**Conclusion:** No *pure* design artifact remains in the active tree — all such documents
and the standalone design-system gallery are archived. The visual identity that remains is
confined to **functional code the app must build and run with**, every instance of which is
flagged and routed through `DESIGN_GUIDELINES.md` so a redesign treats it as replaceable
implementation, not as precedent. The redesign's starting point is `design-context/`.

### One open recommendation (not yet actioned)
`design-context/` is currently **untracked** in git (`?? design-context/`). It is the
authoritative redesign source; recommend `git add design-context/` so it is durably part of
the repository. Left untracked pending your confirmation (it may be intentionally external).
