# Write-up — ROUGH FIRST DRAFT (edit Jul 4–5)

> **Intentionally ugly.** Bullets + rough paragraphs, real numbers/refs, `[CITE:…]` / TODO placeholders.
> Structure follows `docs/writeup-skeleton.md`. Final prose written Jul 4–5 — do NOT polish here.
> NUMBERS LOCKED: **267 tests** (skeleton 3d says 260 — stale, use 267); evidence **+0.06 / +0.04 / +4.9**;
> adapt chain wh→ck→qu. Do NOT claim never-punish confidence repair fires live.

---

## 1. Problem

- Parents of dyslexic / struggling readers get one instruction: "read decodable books at their level." Two gaps make that hollow:
  - **(1) Scarcity + generic fit.** A decodable book at the *exact* phonics level × interests × age a given child needs is scarce and generic. [CITE: README.md:7–9]
  - **(2) No adaptation.** Nothing watches what the child actually *misreads* to choose what to practice next. No loop.
- Framing line: **Phono StoryForge closes that loop** — content generation guaranteed decodable for *this* child, plus an evidence-driven tutor that targets their real gaps and adapts session over session.
- Context to state up front: Google/Kaggle **5-Day AI Agents Intensive — Vibe Coding Capstone**, Track **Agents for Good** (education). [CITE: README.md:5]

---

## 2. Architecture

### 2a. The closed loop (the spine)
- One loop, run per child per session:
  `LearnerProfile (store) → select_objective() → generate decodable book → child reads aloud → assess() (miscue + grapheme attribution) → update_from_evidence() (BKT) → store`
  ...with the dashed feedback edge **"next session's target has shifted" → Plan**. [CITE: README mermaid README.md:15–24]
- **Key claim:** everything load-bearing is **deterministic, non-LLM Python**, implemented and unit-tested. The LLM proposes; deterministic code decides.

### 2b. Deterministic modules table (the "skills") — cite verbatim
| Step | Module | Role |
|---|---|---|
| Plan | `app/skills/planner.py` `select_objective` | lowest unmastered grapheme (ZPD) from BKT estimate + spaced review |
| Decode/verify | `app/skills/decodability.py` `decompose` | **keystone**: word → ordered graphemes tagged by phonics level; one source of truth for decodability, targeting, miscue attribution |
| Assess | `app/skills/alignment.py` `assess` | aligns expected vs spoken (running-record miscue types) → attributes each error to exact grapheme → `grapheme_evidence` |
| Update | `app/skills/mastery.py` `update_from_evidence` | 4-parameter Bayesian Knowledge Tracing → updated per-grapheme knowledge state |
| Persist | `app/store/` | `LearnerProfile` (current mastery) + append-only `SessionLog` history |

- Point to land: **the same code that runs the product loop is the code the evidence experiment exercises** [CITE: README.md:36] — the simulation is a calibration/regression harness for the production brain, not a detached toy.

### 2c. Illustrated book folded into the live loop
- **Commit e7d815b** `feat: fold the illustrated e-book pipeline into the live web tutor` — generation is no longer a standalone path; the live per-session loop triggers it from the web UI, reusing the same `story_planner` / QA-loop agents. [CITE: README.md:43]
- Export distinction (state precisely): live web flow exports the Doc **deterministically** via `app/doc_export.py`; the agentic LLM-drives-MCP export (`formatter_export_agent`) stays in `root_agent` for `adk web` / integration tests but isn't reliable standalone. [CITE: README.md:69]

### 2d. The propose/verify thesis (LLM proposes, deterministic Python verifies)
Three concrete instances of one pattern [CITE: content-engine mermaid README.md:50–64]:
- **Decodability QA loop.** A `LoopAgent` wrapping a custom `BaseAgent` re-runs the writer until `check_decodability` (same `decompose` engine) confirms **zero** violations or halts — an undecodable word can't ship. In the per-session loop this is `app/tutor/llm_book.py` (propose → check → feed violations back; decodability is a HARD gate that raises rather than returning a violation). [CITE: README.md:66]
- **Palette verifier.** `app/skills/palette_verifier.py` proves every Nano Banana (`gemini-2.5-flash-image` via Vertex) page stays on the `app/brand.py` palette via `nearest_brand_color` (tol 80 / 10% budget); reject-and-regenerate or snap on drift. [CITE: README.md:67]
- **Doc export.** Deterministic Doc assembly in `app/doc_export.py` — LLM writes text, deterministic code assembles the Doc (dyslexia-friendly body typeface, display title, real images embedded inline). [CITE: README.md:69]
- Three independent **guardrails** that halt rather than silently continue: phonics decodability loop, export-result validator, Gmail-draft validator. [CITE: README.md:101]

### 2e. ADK / capstone concepts to name-check [CITE: README.md:93–102]
- Multi-agent `SequentialAgent` + `LoopAgent`-wrapped `BaseAgent` QA guardrail; agent skills (the deterministic engines); closed-loop memory (`LearnerProfile`); Gemini Live voice (`app/voice`); live web app (`app/web`, FastAPI + WebSocket); MCP via `gws` stdio (Drive/Docs/Gmail); OpenTelemetry/GenAI telemetry + Dockerfile/Cloud Run path (NOT deployed live — say so).

---

## 3. Evidence: adaptive beats a fixed sequence

### 3a. The experiment
- `eval/experiments/adaptive_vs_static.py`: two arms over the **same paired, seeded** simulated learners — **adaptive** (`select_objective` picks each session's target from the child's BKT estimate) vs **static** (fixed scope-and-sequence ignoring evidence). Both close the identical loop; both read the **same fixed benchmark probe** each session so the fluency comparison is fair. Fully deterministic + LLM-free → reproduces exactly.

### 3b. Headline numbers — de-circularized (Stage D), n=30, 40 sessions [CITE: stage-d-independent-learner.md:29–37]
| metric | old (circular) | **headline (independent learner)** |
|---|---|---|
| probe accuracy gap | +0.14 | **+0.06** (exactly +0.0605) |
| true mean latent mastery gap | +0.09 | **+0.04** |
| WCPM gap | +16 | **+4.9** |
| num_mastered (≥0.95) gap | positive | **−0.47 — a wash** |

- **Frame honestly:** de-circularizing roughly *halved* every gap but did not erase it. Adaptive still wins on real reading accuracy, mean latent mastery, and fluency.

### 3c. Why the result is credible (de-circularization — the rigor beat) [CITE: stage-d-independent-learner.md:9–27; README.md:79,110]
- Two deliberate model mismatches in `eval/simulated_learner.py`:
  - **(1) Emission ≠ BKT.** Learner emits via a 4PL/IRT logistic `P = guess + (1 − slip − guess)·σ(a·(m − b_g))` with per-grapheme item difficulty `b_g` — non-linear, item-keyed; BKT inverts a *level-uniform* linear slip/guess and cannot represent it. Genuine measurement-model mismatch.
  - **(2) No ZPD gate; forgetting instead.** `_readiness` deleted. Practice raises mastery directly (no prerequisite gate); `_apply_forgetting` decays every unrehearsed grapheme. The planner's *own* thesis (prereqs unlock learning) is **not** what the learner does — so adaptive can only win by revisiting each child's *decaying frontier*.
- **Robustness sweep:** `eval/experiments/robustness_sweep.py`, `decay ∈ {0,.02,.03,.05}` × `a ∈ {5,7,9}` = **12 configs**. Accuracy gap **positive in all 12**, from **+0.098 down to +0.002** at the harshest corner (`decay=0.05, a=9.0`). Baseline cell (`decay=0.03, a=7.0`) reproduces headline **+0.0605** exactly. State plainly: positive everywhere but narrows to a knife-edge under heavy forgetting — not robust by a wide margin there.

### 3d. Honest caveats to keep in (don't bury)
- `num_mastered` (count past hard 0.95 bar) is a **wash / slightly negative** — fixed drill over-concentrates practice; logged in CSV, not headlined. [CITE: README.md:79]
- Learner constants are reasonable but **uncalibrated**; WCPM is still a deterministic `errors → seconds` function, not an independent timing measurement. [CITE: stage-d doc:54–55]
- Externally-validated segmenter (other Stage D half): `tests/unit/test_decompose_corpus.py` — 58-word hand-verified truth set + tiling laws over `/usr/share/dict/words`; tiling+reconstruction on **209,743/210,773** words. Two test-pinned known findings: trailing-`e` drop (1,030/210,773 = 0.49%, real bug, pinned <1%) and split-vowel span overlap (representational choice). [CITE: build-plan Stage D:198–224]
- **267 offline unit tests pass** (`uv run pytest tests/unit`). [CITE: README.md:44 — confirmed Jun 28: README + both skeletons now read 267]

### 3e. Artifacts + exact regeneration commands
- Chart: `eval/experiments/results/adaptive_vs_static.png` ✅ git-tracked.
- CSV: `eval/experiments/results/adaptive_vs_static.csv` ✅; Sweep: `eval/experiments/results/robustness_sweep.csv` ✅.
- Regenerate chart + CSV: `uv run python -m eval.experiments.adaptive_vs_static`
- Regenerate sweep: `uv run python -m eval.experiments.robustness_sweep`
- Sample book: `results/sample_book/page_01.png … page_06.png` ✅ (6 pages, "Sam the Fox").

---

## 4. Status / Roadmap (rough — decide scope Jul 4)
- Built & verified: closed loop live in web app; de-circularized evidence; illustrated book folded into loop; 267 tests green.
- NOT live: Cloud Run deployment (path exists, not deployed); never-punish confidence repair is a no-op on the Gemini Live path today (no per-word confidence) — state as known limitation, not a feature.
- TODO: decide whether to name **D′ (flywheel)** as explicitly planned/deferred (`docs/stage-d-prime-flywheel.md`) here or leave to README roadmap table only.

---

## Open TODOs (do NOT invent in final draft)
- TODO: capture a static **screenshot/GIF of the live web demo** (Reading face → Insight face heatmap + mastery PATH + target shift) during Jul 4 rehearsal — none exists in repo for embedding.
- TODO: confirm chart PNG regenerated from current de-circularized learner; eyeball gaps match +0.06 / +0.04 / +4.9.
- ~~TODO: confirm README test count reads 267~~ DONE Jun 28: README:44 = 267; fixed stale "260" in video-skeleton:64 + writeup-skeleton:101.
