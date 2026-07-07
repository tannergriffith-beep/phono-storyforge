# YouTube video description

> **Status: DRAFT.** Chapter timestamps are **PROVISIONAL** — they mirror the shot
> list in `archive/submission-prep/demo-narration-draft.md` (the authoritative narration) and must be
> re-stamped against the final recording before publishing. Fill the two
> back-links once the repo is public and the Kaggle write-up URL exists.
> Numbers are count-free per the Jun 29 test-count policy; evidence figures and
> the adapt chain are copied from `archive/submission-prep/demo-narration-draft.md`, never the stale
> `archive/submission-prep/video-skeleton.md`.

---

## Title

**Phono StoryForge — a closed-loop adaptive reading tutor (Google ADK · Agents for Good)**

(Alt, if a shorter title is needed: *Phono StoryForge: the reading tutor that closes the loop*)

---

## Summary (2–3 sentences)

Phono StoryForge is a closed-loop adaptive reading tutor for early and struggling
readers (dyslexia-aware), built on Google's Agent Development Kit. It keeps a
per-child mastery model, picks the next phonics skill from the child's own reading
evidence, generates a book guaranteed decodable at exactly that level, listens to
the read-aloud, attributes every miscue down to the specific grapheme, and lets the
*next* book change because of how this read went. In a de-circularized study,
adapting beat a fixed scope-and-sequence on **reading accuracy (+0.06)** and **true
mean latent mastery (+0.04)** — the loop measurably helps, and we show our work.

---

## Chapters (PROVISIONAL — re-stamp against the final cut)

```
0:00  The problem — "read decodable books at their level" has no loop
0:30  Live demo — the closed loop adapting (wh → ck → qu), in the real web app
2:15  Evidence — adaptive vs. a fixed sequence, and how we de-circularized it
3:45  The content engine — verifier-gated decodable-book generation
4:35  Close — one deterministic loop, built on ADK for Agents for Good
```

---

## What the numbers mean (so the description doesn't overclaim)

- **Two genuine, independent wins:** probe **accuracy +0.06** and **true mean latent
  mastery +0.04** (n=30, 40 sessions; paired, seeded simulated learners; same fixed
  benchmark probe each session).
- **+4.9 WCPM is derived, not a third independent win** — WCPM is a deterministic
  function of the error count, not an independent timing measurement, so it tracks
  the accuracy result rather than adding new evidence.
- **Rigor:** the simulated learner is built deliberately *unlike* what the tutor
  assumes (logistic/IRT emission with per-grapheme difficulty, no prerequisite gate,
  and forgetting). De-circularizing roughly halved the gaps but they stayed positive
  across all 12 cells of a forgetting-by-difficulty sweep. One honest wash: the count
  of graphemes pushed past a hard 0.95 mastery bar — logged in the CSV, not hidden.
- **Illustrated book (receipts only):** the deterministic Doc/Drive assembly is
  unit-tested and was live-export verified against a real account using **stubbed**
  images; the committed sample-book PNGs prove real illustration generation; a full
  real-image-into-real-Doc run is still pending.

---

## Links

- **Code (GitHub):** https://github.com/tannergriffith-beep/phono-storyforge
  *(confirm the repo is PUBLIC before publishing this video)*
- **Kaggle write-up:** `TODO — paste the Kaggle submission/write-up URL`
- Built for Google/Kaggle's **5-Day AI Agents Intensive — Vibe Coding Capstone**,
  Track: **Agents for Good** (education).

---

## Tags / keywords (optional, for the YouTube tags field)

`google adk` · `agents for good` · `reading tutor` · `phonics` · `dyslexia` ·
`gemini` · `bayesian knowledge tracing` · `mcp` · `kaggle` · `education`
