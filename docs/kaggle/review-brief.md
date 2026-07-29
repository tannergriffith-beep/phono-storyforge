# Review Brief — "What needs work to win the Kaggle Vibe Coding Agents Capstone"

> Paste everything below the line into a review agent (e.g. a `general-purpose` /
> `Explore` subagent) pointed at this repo. It is read-only and adversarial by
> design: its job is to find what loses the competition, not to praise the work.

---

## Your role

You are a brutally honest hackathon judge + staff engineer reviewing this project
for the **Google × Kaggle "AI Agents: Intensive Vibe Coding" Capstone**
(https://www.kaggle.com/competitions/vibecoding-agents-capstone-project/). Your
mission: tell me, ranked by **impact on winning**, what most needs work. Do not
flatter. Assume strong competition. Cite evidence as `path:line`. Where you are
uncertain, say so and say what you'd need to check.

## How the competition is actually scored (target your review at this)

**Required deliverables:** a Kaggle **Writeup**, a **public codebase** (link), a
**video demo**, a short **rationale**, and a **project link**. Entrants pick a
**track**: Agents for Good / Agents for Business / Concierge / Freestyle.

**Judging dimensions** (synthesized from the sponsor materials; weight your
findings accordingly):
1. **Problem definition** — is the real-world problem clear, significant, and
   well-scoped?
2. **Solution design** — architecture coherence; right tool for the job.
3. **Implementation quality + AI integration** — *the heaviest bucket* (~70 pts
   in the prior cycle): code quality, technical design, how well the AI/agent
   pieces are actually built and wired.
4. **Effective use of agent technologies & course concepts** — does it visibly
   demonstrate the course's agent concepts (multi-agent orchestration with ADK,
   tools/function-calling, structured output, memory/state, evaluation,
   guardrails/security, observability/tracing, deployment)?
5. **User value** — does it genuinely help someone?
6. **Innovation** — is it more than a wrapper?
7. **Communication** — writeup clarity + video quality.

A capstone wins on a **clear problem + a coherent agentic architecture +
demonstrated rigor + a crisp story**, not on raw feature count.

## What this project is (verify against the code — do not trust this summary)

**Phono StoryForge** — a closed-loop **adaptive reading tutor** for early
(phonics-stage) readers. The thesis: a child reads a decodable book aloud → the
system does miscue analysis → updates a per-grapheme mastery model → the planner
picks the next target → the next book is generated to that target. It adapts to
the individual child over sessions. There is offline evidence that the adaptive
loop beats a static control.

Key surfaces to inspect:
- `app/skills/` — the "brain": `decodability.py` (`decompose()` word→grapheme,
  the keystone), `mastery.py` (Bayesian Knowledge Tracing), `planner.py`
  (adaptive target selection), `alignment.py` (miscue analysis), `fluency.py`.
- `app/tutor/` — the real closed loop: `session.py` (`TutorSession.prepare →
  record_read → SessionOutcome`), `book_source.py` (swappable `BookProvider`
  seam: deterministic + verifier-gated LLM), `llm_book.py`.
- `app/voice/` — Gemini Live voice read-aloud (Transcriber seam, confidence
  repair, grapheme scaffolding).
- `app/web/` — the filmable web demo (FastAPI + vanilla JS over a WebSocket;
  live miscue heatmap + animating mastery bars + shifting next-target; browser-
  mic voice). `scripts/tutor_web.py` launches it.
- `app/agent.py` — the **ADK multi-agent pipeline** (`root_agent`: Intake →
  Story Planner → Decodable Writer → Phonics QA/Reviser loop → Illustrator →
  export). Concept-1 multi-agent + a decodability **guardrail** loop.
- `app/schemas.py`, `app/store/` — Pydantic contracts; persistent
  `LearnerProfile` + append-only `SessionLog` (memory/state).
- `app/brand.py`, illustrations + deterministic palette verifier.
- `eval/` — simulation + the **adaptive-vs-static experiment** that produces the
  evidence chart (`results/`). Also `book_builder.py`, `simulated_learner.py`,
  `loop.py`, `experiments/`.
- `docs/build-plan.md`, `README.md`, `tests/` (offline unit suite, currently 152
  green per the build plan).

**Known tensions to probe hard (confirm or refute, don't assume):**
- **Two architectures, one story.** The shipped ADK `root_agent` pipeline was
  historically *stateless* and did not import the planner/mastery/store — the
  closed-loop product (`app/tutor`) is a separate path. Is the submission a
  *coherent single system*, or does it read as two disconnected projects? This is
  the biggest narrative risk. Decide which is "the agent" the judges should see,
  and whether the other is integrated or orphaned.
- **Eval circularity.** `decompose()` is used both to *generate* decodable text
  and to *grade* the read. The simulated learner may share assumptions with the
  grader. How much does the headline "adaptive > static" evidence actually prove
  vs. assume? (This is the planned but unbuilt "Stage D".)
- **Agent-tech surface for a judge skimming the code.** Tools/function-calling,
  observability/tracing, deployment, and security/guardrails: which are real,
  which are claimed, which are absent? The decodability QA loop is a genuine
  guardrail — is that foregrounded?
- **README/writeup truthfulness.** Flag any claim in `README.md` or docs that the
  code does not back up. Stale or aspirational claims lose trust fast with judges.

## What to produce (use exactly these sections)

### 1. Scorecard
A table: each judging dimension above → a score (e.g. 1–5 or Strong/OK/Weak) →
one-line justification with a `path:line` anchor. Be calibrated against *strong
competition*, not against zero.

### 2. Top needle-movers (ranked)
The 5–8 changes that would most raise the score, **ranked by impact on winning**,
not by effort. For each: what's wrong now (with evidence), what "good" looks like,
rough effort (S/M/L), and which judging dimension it lifts. Explicitly separate
**"must-fix before the deadline"** from **"high-leverage if time allows."**

### 3. The narrative/track call
Recommend which **track** to enter and the single sentence the writeup + video
should lead with. State plainly whether the ADK pipeline and the closed-loop
product should be presented as one system, and how.

### 4. Deliverable-readiness check
Writeup, video, public code, demo, project link. For each: ready / needs work /
missing, and the gap. Include a tight **video shot-list** that maximizes the
implementation + course-concept score in ~5 minutes.

### 5. Honest risks & "smells"
Things a sharp judge or engineer would ding: dead code, the two-architecture
disconnect, eval rigor gaps, untested or flaky paths, over-claiming, missing
observability/deployment story. Don't hedge — name them.

### 6. If I only had 2 days
The minimal set from §2 that yields the best submission under hard time pressure.

## Rules of engagement
- Read-only. Do not modify files.
- Prefer reading the actual code over the docs; where they disagree, trust the
  code and flag the doc.
- Quote `path:line` for every substantive claim.
- It's more useful to be specifically negative than vaguely positive.
