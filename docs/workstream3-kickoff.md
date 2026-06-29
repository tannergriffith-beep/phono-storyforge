# Workstream 3 kickoff — Submission Drafting (handoff brief)

> Handoff from the Demo-Readiness session (Jun 28). Purpose: let a fresh session
> start drafting with **zero cold-start re-discovery**. This is a working brief,
> not a deliverable.

## Mission (one session, two rough deliverables)
Eliminate blank pages. Produce **intentionally ugly first drafts** to be edited Jul 4–5 — NOT polished prose.
1. **Demo narration draft** — fill the spoken beats of `docs/video-skeleton.md` with actual words, timed to ≈5:00.
2. **Write-up first draft** — fill `docs/writeup-skeleton.md` in bullets/rough paragraphs.

Ugliness rules: bullets over prose, leave `[SCREENSHOT: …]` / `[CITE: …]` / `TODO:` placeholders, do NOT optimize wording. Goal is structure + ideas, not style.

## Source of truth (read these first)
- `docs/demo-runbook.md` — **verified** click-by-click demo script (current UI). Narration must match this, not the stale parts of video-skeleton.
- `docs/video-skeleton.md` — shot order + timing + rough beats. ORDER and TIMING still valid; Shot 1's on-screen choreography is superseded by the runbook.
- `docs/writeup-skeleton.md` — write-up structure to fill.
- `docs/voice-lexicon.md` — brand voice for narration tone.
- `README.md` — feature/architecture claims (audited Jun 28, high integrity).

## Verified facts the drafts MUST reflect (don't re-derive)
- **267 unit tests pass** (NOT 260 — video-skeleton Shot 5 is stale on this).
- **Live demo adapt chain: wh → ck → qu** on the seeded `ada` profile; each strong read masters the current digraph and advances the target.
- **Use the "One miscue" preset** in the demo: it lights the heatmap (1 red cell) + shows a scaffold cue + advances the target, all in one read. ("Perfect" = no miscues to narrate; "Struggling" = target holds.)
- **UI is post-rebrand:** mastery is a **node PATH** (not bars); the running-record heatmap + analysis live in the **Insight face** reached by tapping **"For grown-ups"**; operator presets are collapsed; the ADK loop rail shows only with `?loop`.
- **Evidence (verified vs CSV):** n=30, 40 sessions, adaptive vs static — probe accuracy **+0.06**, true mean mastery **+0.04**, **+4.9 WCPM**. De-circularized (logistic/IRT learner, no ZPD gate, forgets); gaps held positive across all 12 sweep cells. Honest wash: count past the hard 0.95 bar.
- **Illustrated book:** `results/sample_book/page_01..06.png` — "Sam the Fox", 6 decodable pages; LLM-proposes / Python-verifies decodability + palette + deterministic Doc assembly.
- **Do NOT claim** the never-punish confidence repair "fires live" — it's a no-op on the Gemini Live path (no per-word confidence).

## Boundaries (orchestrator notes)
- This session does NOT finish the demo. The **live visual dry run + recording** are unfinished Workstream 1, done by the human at the demo machine — keep them as a separate track.
- After both drafts exist, the natural next workstream is **Workstream 4 (Final Submission Review)** closer to the deadline.
- Tiny leftover truth fix (cheap, optional): correct "260 tests" → "267" wherever it appears.
