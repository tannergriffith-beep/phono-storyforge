# Stage D — Independent Learner Model (✅ RESOLVED 2026-06-24)

> **RESOLVED.** Both circularity leaks are now closed (branch
> `stage-d-independent-learner`). The brief below is preserved for context; the
> outcome is summarized in **"What shipped"** immediately after it.

## What shipped (result)

Both leaks broken in `eval/simulated_learner.py`:

1. **Emission ≠ BKT.** `_p_correct` is now a 4PL/IRT logistic,
   `P = guess + (1 − slip − guess)·σ(a·(m − b_g))`, with a per-grapheme difficulty
   `b_g` (`GRAPHEME_DIFFICULTY`, seeded, same for the whole population). It is
   non-linear in mastery and keyed on item difficulty that BKT's *level-uniform*
   slip/guess cannot represent — the tutor now estimates mastery under a real
   model mismatch.
   - **Mismatch, one sentence:** the learner emits via a logistic with per-grapheme
     item difficulty; BKT inverts a linear slip/guess with no item difficulty, so
     its measurement model is structurally wrong for this child.
2. **No ZPD gate; forgetting instead.** `_readiness` is deleted. Practice now
   raises mastery directly (no prerequisite gate), and `_apply_forgetting` decays
   every grapheme *not* rehearsed that session (`m *= 1 − decay`, learn-only so the
   probe never perturbs the trajectory).
   - **Mismatch, one sentence:** the planner assumes prerequisites unlock learning;
     the learner has no such gate and instead forgets unpracticed skills, so
     adaptive can only win by revisiting each child's *decaying frontier*, not by
     satisfying its own ZPD premise.

**Re-run (n=30, 40 sessions), results/adaptive\_vs\_static.{png,csv} regenerated:**

| metric                    | old (circular) | new (independent)  |
| ------------------------- | -------------- | ------------------ |
| probe accuracy gap        | +0.14          | **+0.06**          |
| true mean mastery gap     | +0.09          | **+0.04**          |
| WCPM gap                  | +16            | **+4.9**           |
| num\_mastered (≥0.95) gap | positive       | **−0.47 (a wash)** |

**Honest interpretation (writeup-ready):** de-circularizing roughly *halved* every
gap but did not erase it. Adaptive still beats the fixed sequence on real reading
accuracy, mean latent mastery, and fluency — and a forgetting × discrimination
sweep (`decay ∈ {0, .02, .03, .05}` × `a ∈ {5, 7, 9}`, **12 configs**) keeps the
accuracy gap **positive in all 12**, ranging from +0.098 down to +0.002. The
baseline cell (`decay=0.03, a=7.0`) reproduces the headline +0.0605 exactly, and
the smallest gap, +0.002, sits at the harshest corner (`decay=0.05, a=9.0`: most
forgetting, sharpest emission) — so the win is consistently positive but narrows
toward a knife-edge under heavy forgetting, not robust by a wide margin there. The
sweep is reproducible: `uv run python -m eval.experiments.robustness_sweep` regenerates
`eval/experiments/results/robustness_sweep.csv`. The one place adaptive does
*not* win is the count of graphemes pushed past a hard 0.95 mastery bar: under
forgetting the fixed drill over-concentrates practice on a few graphemes and ties
or slightly edges adaptive there — the `num_mastered` gap is ≤0 in most cells of
the sweep too, corroborating the headline −0.47. That is a credible, nuanced
result — a smaller but defensible win, no longer a self-consistency artifact. The
remaining caveat is that the learner's constants are reasonable but uncalibrated,
and WCPM is still `errors → seconds`, not an independent timing measurement.

Tests updated/added in `tests/unit/test_simulated_learner.py` (logistic emission,
difficulty ordering, no-prereq-gate, forgetting, probe-is-inert) and
`tests/unit/test_experiment.py` (`test_advantage_emerges_from_a_tied_start`
replaces the old `test_gap_widens_over_time`, which encoded the circular "gap
always widens" narrative). Full `tests/unit` suite green (`uv run pytest tests/unit`).

---

## Original brief (for context)

> Parked task. Written 2026-06-24 so I don't lose it. This is the **harder, riskier
> half** of Stage D — do it at a desk with a clear head, NOT in a stolen hour.
> The *other* half (validate `decompose()` against an external corpus) is being
> done separately and is safe/additive.

## The one-sentence problem

Our evidence chart (adaptive > static: `+0.14` acc, `+0.09` mastery, `+16` WCPM)
is **partly self-validating** because the simulated learner is built from the same
assumptions the planner exploits. We want a learner whose dynamics are *not* the
planner's assumptions, re-run the experiment, and see if adaptive still wins.

## Why it's circular right now (the two leaks)

1. **Emission model ≡ BKT inference model.**
   - Learner reads correctly with prob `m·(1−slip) + (1−m)·guess`
     — [`eval/simulated_learner.py:98`](../eval/simulated_learner.py) (`_p_correct`).
   - BKT *inverts that exact equation* to estimate mastery
     — [`app/skills/mastery.py:54-60`](../app/skills/mastery.py).
   - So the tutor's model of the child is, by construction, a perfect model of the
     simulated child. No model mismatch = unrealistically easy.
2. **\_readiness hard-codes the planner's ZPD premise.**
   - Learner only consolidates a grapheme well once its *prerequisites* are mastered
     — [`eval/simulated_learner.py:113-134`](../eval/simulated_learner.py).
   - The adaptive planner's whole strategy is "target the lowest unmastered grapheme,"
     which is *exactly* the thing the learner rewards. The experiment is rigged in the
     planner's favor at the assumption level, not just the outcome level.

Also worth noting: the win is governed by **hand-set, uncalibrated constants**
(`slip=0.04`, `guess=0.10`, `learn_rate=0.18`, `fail_learn_factor=0.15`,
`readiness_floor=0.05` — [`simulated_learner.py:43-60`](../eval/simulated_learner.py))
and WCPM is a **fabricated** deterministic function of error count
([`eval/loop.py:38-39`](../eval/loop.py)), not an independent measurement.

## What "de-circularized" actually requires

Build a learner whose generative process is **deliberately different** from what BKT
assumes, then check the planner still helps. Candidate moves (pick 1–2, don't boil
the ocean):

- **Different emission model.** Replace the linear slip/guess with something BKT
  does *not* assume — e.g. logistic/IRT-style `P(correct) = sigmoid(a·(m − b))`, or
  add per-word difficulty, or context effects (fatigue across a page, momentum from
  prior word). The point: BKT now has a model mismatch and must cope.
- **Different learning dynamics.** Replace the ZPD-prerequisite gate with an
  independent mechanism — spaced-repetition forgetting curves, interference between
  similar graphemes, or a forgetting term so unpracticed skills decay. Critically,
  the learning rule should NOT be "prereqs unlock learning," because that's the
  planner's own thesis.
- **Calibrate the constants against the corpus work** (Stage D other half) instead of
  hand-picking them, so the realism isn't just asserted.
- **Independent fluency/WCPM** rather than `errors → seconds` via fabricated constants.

## The real risk (read before starting)

**This can flip or shrink the headline result.** If an independent learner makes
adaptive ≈ static, the README's `+0.14 / +0.09 / +16` numbers are contradicted and
the whole evidence narrative needs rewriting. Therefore:

- Do this on a **branch**, never on top of the submission state.
- Treat a *smaller but still-positive* gap as a **win** (more credible).
- Treat a *flat/negative* result as **information, not failure** — but only adopt it
  if there's time to re-chart, re-validate, and rewrite the writeup. Two weeks out is
  fine; three days out is not.
- Re-run the full `n=30` experiment + regenerate `eval/experiments/results/adaptive_vs_static.png`
  and the CSV before believing anything.

## Done-when

- Learner's emission **and/or** learning rule is provably not the BKT/planner
  assumption (documented: "here's the mismatch we introduced").
- `eval/experiments/adaptive_vs_static.py` re-run at n=30 on the new learner.
- New chart + CSV regenerated; result interpreted honestly in the writeup.
- Unit tests updated for the new learner dynamics.

## If I run out of time

The corpus-validation slice (other half of Stage D) + the **honest disclosure already
in the README** ([`README.md:108`](../README.md)) is an acceptable floor. Framing the
current result as *"a self-consistency proof the loop is wired correctly, not an
efficacy claim"* is defensible on its own. This independent-learner work is **upside,
not a gate** — the video + writeup come first.

## Key files

- [`eval/simulated_learner.py`](../eval/simulated_learner.py) — the learner to replace/fork
- [`app/skills/mastery.py`](../app/skills/mastery.py) — BKT (don't change; this is the thing being tested)
- [`eval/loop.py`](../eval/loop.py) — closed loop + WCPM fabrication
- [`eval/experiments/adaptive_vs_static.py`](../eval/experiments/adaptive_vs_static.py) — the experiment to re-run
- `eval/experiments/results/adaptive_vs_static.{png,csv}` — artifacts to regenerate
