# Decision: Stage D′ — Self-Improving Content Flywheel

**Status:** Planned, deliberately deferred. Not a "skip" — a sequencing call.

## What it is

Every real tutoring session automatically becomes an eval datapoint; `check_decodability`
runs as an always-on judge over real usage. Extends the project's evidence discipline from
the synthetic simulated-learner study (Stage D, done) to live data — the system polices and
improves itself in production, not just in a one-off offline experiment.

## Why it's worth building (not just competition polish)

This project is dual-purpose: a Kaggle capstone submission **and** a real product Tanner
intends to keep building. For the real-product track, D′ isn't optional — a tutor that
generates content for real kids needs an automatic check that it's still working as new
content and new usage patterns accumulate. That's a standing need independent of the
competition deadline.

For the competition specifically, the case is good but quieter:
- High real-world usefulness, high technical sophistication, high educational value
  (on-theme with the course's own eval tooling, already used in dev via `agents-cli eval`).
- But low demo quality (a "trending number" doesn't have a live moment) and it's invisible
  to judges unless deliberately surfaced — full reasoning in chat, 2026-06-25.
- ROI estimate at decision time: Impact 6/10, Effort 6/10 (M–L, 4–15h scope-dependent),
  ROI ≈ 1.0, confidence medium.

## The decision: sequencing, not skipping

**Build D′ only after the writeup and skeleton video are done.**

Why: nothing graded depends on D′, and it's invisible in the video unless explicitly
surfaced. The writeup + video are 0% started and are what's actually scored. Building D′
first risks the classic trap — doing the interesting, personally-motivating work instead of
the work that's scored — especially given Tanner's stated north star (AI engineer) makes
this exact feature unusually tempting.

Once the writeup/video skeleton exists, revisit: build the **minimal** version first (log +
judge + simple report, leaning on the existing `SessionLog` persistence and
`check_decodability` — both already built), not the full dashboard/`agents-cli eval`
integration version, unless real slack remains.

## Reference

Full 8-step competition-ROI evaluation run 2026-06-25 — see chat history in this project for
complete Judge Simulation / Cost Analysis detail if revisiting this call.
