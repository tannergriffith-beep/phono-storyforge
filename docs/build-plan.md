# Build Plan — Closed-Loop Reading Tutor

**Deadline:** Mon **July 6, 2026**. **Internal ship date:** Sat **July 5** (1 day slack).
**Today:** June 24. **Assumption:** \~full-time solo effort + AI assist. Part-time? See "Compression" at bottom.

## Status dashboard

| Phase                                | Window    | Outcome                                        | Status |
| ------------------------------------ | --------- | ---------------------------------------------- | ------ |
| 1. Grapheme decomposition + verifier | Jun 24–25 | `decompose()` + sound-level fixes, tests green | ✅ Done |
| 2. Mastery model + store             | Jun 26–27 | BKT + LearnerProfile + planner                 | ✅ Done |
| 3. Simulated learner + evidence      | Jun 28–30 | **Closed loop + evidence chart** 🎯            | ✅ Done |
| 5. Illustrations                     | Jul 1–2   | Real illustrated book in a Doc                 | ⬜      |
| Stretch (audio OR thin UI)           | Jul 3     | Skippable                                      | ⬜      |
| Writeup + video + final eval         | Jul 4–5   | Submission package                             | ⬜      |
| Buffer / submit                      | Jul 6     | —                                              | ⬜      |

### Hard rules (the things that lose competitions)

1. **Jul 4–5 for writeup + video is non-negotiable.** Never borrow from it.
2. **GATE @ Jun 30:** if Phase 3 isn't done, drop Phases 5/stretch and go straight to writeup. Phases 1–3 alone is a winning thesis.
3. **Skip real audio (4) and full UI (6).** The simulated learner closes the loop; the video narrates over playground + illustrated book + the chart.

---

## Phase 1 — Grapheme decomposition + sound-level verifier (Jun 24–25)

The keystone. Everything depends on word→grapheme mapping.

**Day 1 (Jun 24)** ✅

- Create `app/skills/` package; move `tools.py` → `app/skills/decodability.py` (`tools.py` kept as re-export shim; `agent.py` import rewired)
- Define `GraphemeHit` and `WordDecomposition` dataclasses
- Implement `decompose(word)` — emit graphemes with `level` + char span
- Derive `is_decodable(word, mastered)` from `decompose()` — all 17 unit tests green

**Day 2 (Jun 25)** ✅

- Fix sound-vs-spelling bugs: welded `all`/nasal rimes (`glued_sounds`), `y`-as-vowel (`y_vowel`), inflectional `suffixes` (`-s/-es/-ed`; `-ing` via glued rime)
- Modeled as discrete structured-literacy skills in `phonics_db` + `schemas` Literal (feeds Phase 2 mastery model)
- Unit tests: glued sounds, y-as-vowel, suffixes + `ball` regression — 21 unit tests green
- Writer prompt updated additively so the loop converges on the new rules

**Done when:** `pytest tests/unit` green; `decompose("ship")` shows `sh@digraphs`; `decompose("ball")` flagged not-short-vowel. ✅
**Note (schwa to/a):** these are default sight words skipped by the checker; the judge flagged them only because the eval prompt isn't told about `DEFAULT_SIGHT_WORDS`. That's an eval-alignment fix — deferred to the Phase 3 eval-config work, not a decoder bug.

---

## Phase 2 — Mastery model + store (Jun 26–27)

**Day 3 (Jun 26)** ✅

- Schemas: `GraphemeMastery`, `LearnerProfile`, `Objective`, `MasteryDelta`
- `app/skills/mastery.py`: BKT `update_from_evidence(profile, grapheme_evidence) -> MasteryDelta`
- `phonics_db`: grapheme inventory (derived from `PHONICS_LEVELS`, one-directional) + `LEVEL_SEQUENCE` + BKT params (`p_init,p_transit,p_slip,p_guess`) + `MASTERY_THRESHOLD`
- Levels `decompose()` enforces structurally (blends, suffixes) get sentinel/namespaced grapheme keys (`_blend_`, `-s/-es/-ed/-ing`) so every level has a trackable unit

**Day 4 (Jun 27)** ✅

- `app/store/learner_store.py`: `LearnerStore` interface + `JSONLearnerStore` (atomic writes, id sanitization, `get_or_create`); SQLite skipped per fallback
- `app/skills/planner.py` curriculum planner: deterministic ZPD target + spaced-review picks → `Objective`
- Unit tests: mastery rises on correct / falls on errors; planner picks lowest unmastered; profile round-trips through store

**Done when:** evidence → sane mastery update; planner returns next target; profile round-trips through store. ✅ — 42 unit tests green.
**If behind:** JSON store only (skip SQLite); planner rule = "lowest unmastered grapheme," skip spaced review.

---

## Phase 3 — Simulated learner + miscue analysis + experiment (Jun 28–30) 🎯

**Day 5 (Jun 28)** ✅

- `app/skills/alignment.py`: `align(expected, spoken)` (difflib) → classified ops; self-correction/hesitation recovered from opcodes
- Miscue classification: substitution/omission/insertion/self\_correction/hesitation
- Attribution: diff decompositions → implicated graphemes → `grapheme_evidence` (incl. `_blend_` / `-s/-es/-ed/-ing` sentinels)
- `AssessmentResult` + `Miscue` schemas; `assess()`; WCPM/accuracy in `app/skills/fluency.py` — 18 unit tests

**Day 6 (Jun 29)** ✅

- `eval/book_builder.py`: deterministic decodable book for an Objective (target + review within budget); `UNTEACHABLE_GRAPHEMES` ({ng, ph}) computed dynamically
- `eval/simulated_learner.py`: latent-mastery child (seeded RNG), TRUE mastery separate from BKT estimate; readiness/ZPD-gated learning; `read(book)` emits miscues tracking mastery
- `eval/loop.py`: arm-agnostic closed loop objective→book→read→miscue→BKT update→persist — 16 unit tests

**Day 7 (Jun 30) — GATE** ✅

- `eval/experiments/adaptive_vs_static.py`: adaptive (planner) vs static control over N paired learners; tracks TRUE mastery + a FIXED benchmark probe (fair accuracy/WCPM)
- Evidence chart (`results/adaptive_vs_static.png`) + CSV fallback (`results/adaptive_vs_static.csv`) — 5 unit tests

**Done when:** chart proves adaptive > static. ✅ — n=30: probe accuracy +0.14, true mean mastery +0.09, WCPM +16, gaps widen over sessions. **This is the minimum winning submission.**
**Note:** headline metrics are the fixed-probe reading accuracy/WCPM and true mean latent mastery (all robustly adaptive, widening). `num_mastered` is breadth-vs-depth ambiguous (static spreads thin) so it's logged in the CSV but not headlined.

---

## Phase 5 — Illustrations (Jul 1–2)

**Day 8 (Jul 1)**

- Illustrator agent calls Imagen from existing prompts; character-bible state key for consistency
- Embed generated images into the Google Doc export (real images, not text placeholders)

**Day 9 (Jul 2)**

- Produce one full illustrated sample book end-to-end; polish style cohesion

**Done when:** a real illustrated decodable book opens in Google Docs.
**If behind:** skip entirely — go to writeup.

---

## Jul 3 — Stretch (skippable)

Pick ONE only if Phases 1–3+5 are solid: minimal audio upload→transcript, **or** a thin Streamlit read-along. If any doubt, skip.

---

## Jul 4–5 — Submission package (non-negotiable)

- Writeup: problem → architecture → **the evidence result**
- Record video (\~5 min): input → illustrated book → simulated read → miscue highlight → mastery chart → adapted next book
- Update README to match the new system; remove stale claims
- Final eval run + commit artifacts
- Submit (Jul 5; Jul 6 = buffer)

---

## Compression (evenings only, \~3–4 hrs/day)

Cut to **Phases 1–3 + writeup/video only.** Drop illustrations and stretch. Shift dates: P1 Jun 24–26, P2 Jun 27–29, P3 Jun 30–Jul 3, writeup/video Jul 4–5. Same thesis, fewer visuals.
