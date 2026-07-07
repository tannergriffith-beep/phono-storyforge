# Writeup skeleton — capstone written submission

> **Skeleton only.** Structure + real facts/numbers/refs to cite. Final prose is written in the
> Jul 4–5 window. Order follows build-plan.md "Jul 4–5": **problem → architecture → the evidence result.**
> Every number below is pulled from the repo as of Jun 25 — do not re-estimate or round generously when
> drafting; the honest figures are the point.

---

## 1. Problem

_Source: README "The Problem" (README.md:7–9)._

- Parents of dyslexic / struggling readers are told to "read decodable books at their level" — but two gaps:
  - **(1) Scarcity + generic fit.** Decodable books at the *exact* combination of phonics level + interests + age a given child needs are scarce and generic.
  - **(2) No adaptation.** Nothing watches what the child actually *misreads* and chooses what to practice next — there is no loop.
- Framing line: Phono StoryForge closes that loop — content generation guaranteed decodable for *this* child + an evidence-driven tutor that targets their real gaps and adapts session over session.
- Track / context to state: Google/Kaggle **5-Day AI Agents Intensive — Vibe Coding Capstone**, Track **Agents for Good** (education). (README.md:5)

---

## 2. Architecture

_Sources: README loop diagram (README.md:15–24), deterministic-modules table (README.md:28–34),
content-engine section (README.md:46–71), commit e7d815b._

### 2a. The closed loop (the spine)

- One loop, run per child per session. Cite the mermaid diagram:
  `LearnerProfile (store) → select_objective() → generate decodable book → child reads aloud → assess() (miscue + grapheme attribution) → update_from_evidence() (BKT) → store`, with the dashed feedback edge **"next session's target has shifted" → Plan**.
- Key claim to make: **everything load-bearing is deterministic, non-LLM Python** that is implemented and unit-tested.

### 2b. Deterministic modules table (cite verbatim — these are the "skills")

| Step | Module | Role |
|---|---|---|
| Plan | `app/skills/planner.py` `select_objective` | lowest unmastered grapheme (ZPD) from BKT estimate + spaced review |
| Decode/verify | `app/skills/decodability.py` `decompose` | **keystone**: word → ordered graphemes tagged by phonics level; one source of truth for decodability, targeting, miscue attribution |
| Assess | `app/skills/alignment.py` `assess` | aligns expected vs spoken (running-record miscue types) → attributes each error to exact grapheme → `grapheme_evidence` |
| Update | `app/skills/mastery.py` `update_from_evidence` | 4-parameter Bayesian Knowledge Tracing → updated per-grapheme knowledge state |
| Persist | `app/store/` | `LearnerProfile` (current mastery) + append-only `SessionLog` history |

- Point to land: **the same code that runs the product loop is the code the evidence experiment exercises** (README.md:36) — the simulation is a calibration/regression harness for the production brain, not a detached toy.

### 2c. Illustrated book folded into the live loop (commit e7d815b)

- Cite **commit e7d815b** `feat: fold the illustrated e-book pipeline into the live web tutor` — the generation pipeline is no longer a standalone path; the live per-session loop can trigger it directly from the web UI, reusing the same `story_planner`/QA-loop agents. (README.md:43)
- Export distinction to make precise: live web flow exports the Doc **deterministically** via `app/doc_export.py`; the agentic LLM-drives-MCP export (`formatter_export_agent`) stays in `root_agent` for `adk web` / integration tests but isn't reliable standalone. (README.md:69)

### 2d. The propose/verify thesis (LLM proposes, deterministic Python verifies)

_Cite the content-engine mermaid (README.md:50–64) — three concrete instances of the same pattern:_

- **Decodability QA loop.** A `LoopAgent` wrapping a custom `BaseAgent` re-runs the writer until `check_decodability` (same `decompose` engine) confirms **zero** violations or halts — an undecodable word can't ship. In the per-session loop this is `app/tutor/llm_book.py` (propose → `check_decodability` → feed violations back; decodability is a HARD gate that raises rather than returning a violation). (README.md:66, build-plan Stage B Part 1)
- **Palette verifier.** `app/skills/palette_verifier.py` proves every Nano Banana (`gemini-2.5-flash-image` via Vertex) page stays on the brand palette defined in `app/brand.py` via `nearest_brand_color` (tol 80 / 10% budget); reject-and-regenerate or snap on drift. (README.md:67, build-plan Phase 5)
- **Doc export.** Deterministic Doc assembly in `app/doc_export.py` — LLM writes the text, deterministic code assembles the Doc (dyslexia-friendly body typeface for legibility / display title; real images embedded inline). (README.md:69)
- Three independent **guardrails** that halt rather than silently continue: phonics decodability loop, export-result validator, Gmail-draft validator. (README.md:101)

### 2e. ADK / capstone concepts to name-check (README.md:93–102)

- Multi-agent `SequentialAgent` + `LoopAgent`-wrapped `BaseAgent` QA guardrail; agent skills (the deterministic engines); closed-loop memory (`LearnerProfile`); Gemini Live voice (`app/voice`); live web app (`app/web`, FastAPI + WebSocket); MCP via `gws` stdio (Drive/Docs/Gmail); OpenTelemetry/GenAI telemetry + Dockerfile/Cloud Run path (not deployed live).

---

## 3. Evidence: adaptive beats a fixed sequence

_Sources: README "Evidence" (README.md:73–79), docs/stage-d-independent-learner.md (the de-circularized
re-run), eval/experiments/results/._

### 3a. The experiment

- `eval/experiments/adaptive_vs_static.py`: two arms over the **same paired, seeded** simulated learners — **adaptive** (`select_objective` picks each session's target from the child's BKT estimate) vs **static** (fixed scope-and-sequence ignoring evidence). Both close the identical loop; both read the **same fixed benchmark probe** each session so the fluency comparison is fair. Fully deterministic + LLM-free → reproduces exactly.

### 3b. Headline numbers — **de-circularized (Stage D), n=30, 40 sessions**

_Cite docs/stage-d-independent-learner.md:29–37. These are the numbers to lead with._

| metric | old (circular) | **headline (independent learner)** |
|---|---|---|
| probe accuracy gap | +0.14 | **+0.06** (exactly +0.0605) |
| true mean latent mastery gap | +0.09 | **+0.04** |
| WCPM gap | +16 | **+4.9** |
| num_mastered (≥0.95) gap | positive | **−0.47 — a wash** |

- **Frame honestly:** de-circularizing roughly *halved* every gap but did not erase it. Adaptive still wins on real reading accuracy, mean latent mastery, and fluency.

### 3c. Why the result is credible (de-circularization — the rigor beat)

_Cite docs/stage-d-independent-learner.md:9–27 and README.md:79, 110._

- Two deliberate model mismatches introduced in `eval/simulated_learner.py`:
  - **(1) Emission ≠ BKT.** Learner emits via a 4PL/IRT logistic `P = guess + (1 − slip − guess)·σ(a·(m − b_g))` with per-grapheme item difficulty `b_g` — non-linear, item-keyed; BKT inverts a *level-uniform* linear slip/guess and cannot represent it. Genuine measurement-model mismatch.
  - **(2) No ZPD gate; forgetting instead.** `_readiness` deleted. Practice raises mastery directly (no prerequisite gate); `_apply_forgetting` decays every unrehearsed grapheme. The planner's *own* thesis (prereqs unlock learning) is **not** what the learner does, so adaptive can only win by revisiting each child's *decaying frontier*.
- **Robustness sweep:** `eval/experiments/robustness_sweep.py`, `decay ∈ {0,.02,.03,.05}` × `a ∈ {5,7,9}` = **12 configs**. Accuracy gap **positive in all 12**, from **+0.098 down to +0.002** at the harshest corner (`decay=0.05, a=9.0`). Baseline cell (`decay=0.03, a=7.0`) reproduces the headline **+0.0605** exactly. State plainly: positive everywhere but narrows to a knife-edge under heavy forgetting — not robust by a wide margin there.

### 3d. Honest caveats to keep in (don't bury)

- `num_mastered` (count past hard 0.95 bar) is a **wash / slightly negative** — fixed drill over-concentrates practice; logged in CSV, not headlined. (build-plan Phase 3 note, README.md:79)
- Learner constants are reasonable but **uncalibrated**; WCPM is still a deterministic `errors → seconds` function, not an independent timing measurement. (stage-d doc:54–55)
- Externally-validated segmenter (the other Stage D half): `tests/unit/test_decompose_corpus.py` — a hand-verified grapheme truth set + tiling laws over `/usr/share/dict/words`; tiling+reconstruction on **209,743/210,773** words. Two test-pinned known findings: trailing-`e` drop (1,030/210,773 = 0.49%, real bug, pinned <1%) and split-vowel span overlap (representational choice). (build-plan Stage D:198–224)
- **The full offline `tests/unit` suite passes** (`uv run pytest tests/unit`). (README.md:44)

### 3e. Artifacts + exact regeneration commands

- Chart: `eval/experiments/results/adaptive_vs_static.png` ✅ exists + git-tracked (110 KB, Jun 25).
- CSV: `eval/experiments/results/adaptive_vs_static.csv` ✅ tracked. Sweep: `eval/experiments/results/robustness_sweep.csv` ✅ tracked.
- Regenerate chart + CSV: `uv run python -m eval.experiments.adaptive_vs_static`
- Regenerate sweep: `uv run python -m eval.experiments.robustness_sweep`
- Sample illustrated book artifacts: `results/sample_book/page_01.png … page_06.png` ✅ tracked (6 pages, "Sam the Fox", on-brand first try).

---

## TODOs (things a section needs that don't exist yet — do NOT invent in final draft)

- TODO: No static **screenshot / GIF of the live web demo** (`scripts/tutor_web.py` — miscue heatmap + animating mastery bars + next-target panel) exists in the repo for embedding in the writeup. Capture one during the Jul 4 rehearsal.
- TODO: Confirm the chart PNG is regenerated from the **current** de-circularized learner before submission (file is dated Jun 25; re-run 3e command and eyeball that the plotted gaps match the +0.06 / +0.04 / +4.9 headline).
- TODO: Decide whether to mention **D′ (flywheel)** as explicitly *planned/deferred* (docs/stage-d-prime-flywheel.md) in the Status/Roadmap paragraph, or leave it to the README roadmap table only.
