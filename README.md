# Phono StoryForge

Phono StoryForge is a **closed-loop adaptive reading tutor** for early and struggling readers (dyslexia-aware), built on Google's Agent Development Kit (ADK). It doesn't just generate a decodable storybook once — it keeps a per-child mastery model, decides what phonics skill to teach next from that child's own reading evidence, generates a book guaranteed decodable at exactly that level, listens to the child read it, attributes every miscue down to the specific grapheme, updates the mastery model, and lets the *next* book change because of how this read went.

Built as the capstone project for Google/Kaggle's **5-Day AI Agents Intensive — Vibe Coding Capstone**, Track: **Agents for Good** (education).

## The Problem

Parents of dyslexic and struggling readers are told to "read decodable books at their level," but (1) decodable books at the *exact* combination of phonics level + interests + age a given child needs are scarce and generic, and (2) nothing adapts: there's no loop that watches what the child actually misreads and chooses what to practice next. Phono StoryForge closes that loop — content generation guaranteed decodable for *this* child, plus an evidence-driven tutor that targets their real gaps and adapts session over session.

## The thesis: a closed loop, not a one-shot generator

The spine of the project is one loop, run per child, per session:

```mermaid
graph LR
    Store[(LearnerProfile<br/>persistent mastery)] --> Plan["select_objective()<br/>ZPD target from BKT"]
    Plan -->|Objective| Gen["generate decodable book"]
    Gen --> Read["child reads aloud"]
    Read -->|transcript| Assess["assess()<br/>miscue analysis +<br/>grapheme attribution"]
    Assess -->|grapheme_evidence| BKT["update_from_evidence()<br/>Bayesian Knowledge Tracing"]
    BKT --> Store
    BKT -.->|next session's target has shifted| Plan
```

Everything load-bearing here is **deterministic, non-LLM Python** that the project already implements and unit-tests:

| Step | Module | What it does |
|---|---|---|
| Plan | `app/skills/planner.py` `select_objective` | Picks the lowest unmastered grapheme (ZPD) from the child's BKT estimate, plus spaced-review picks. |
| Decode/verify | `app/skills/decodability.py` `decompose` | The keystone: maps any word → ordered graphemes tagged by phonics level. Powers decodability, targeting, and miscue attribution from one source of truth. |
| Assess | `app/skills/alignment.py` `assess` | Aligns expected vs. spoken text (running-record miscue types), then attributes each error down to the exact grapheme → `grapheme_evidence`. |
| Update | `app/skills/mastery.py` `update_from_evidence` | 4-parameter Bayesian Knowledge Tracing; turns evidence into an updated per-grapheme knowledge state. |
| Persist | `app/store/` | `LearnerProfile` (current mastery) + append-only `SessionLog` history. |

**The same code that runs the product loop is the code the evidence experiment exercises** (see *Evidence* below) — so the simulation isn't a detached toy; it's a calibration/regression harness for the production brain.

## Status (honest)

- **Closed-loop tutor — a real, stateful product (Stage A, done).** `app/tutor/TutorSession` runs the full loop above against a persistent `LearnerStore`, exposed through a typed-transcript entry path (`scripts/tutor_cli.py`). Run it twice for a child with strong reads and the target visibly advances (e.g. `a` → `e` → `i`), mastery rises, and everything persists across processes.
- **Voice read-aloud + verifier-gated LLM books (Stage B, done).** Gemini Live transcribes the child's read-aloud (`app/voice/`, with a `FakeTranscriber` for offline tests) and feeds the *unchanged* `record_read()`; a verifier-gated LLM generator (`app/tutor/llm_book.py`, propose → `check_decodability` → revise) is wired into the loop as an optional content source behind the same `BookProvider` seam (`--llm-book`). Voice is creds-gated and degrades to typed input if Gemini Live is unavailable.
- **Web read-along + live mastery viz (Stage C, done).** A FastAPI + vanilla-JS app (`app/web/`, launched via `scripts/tutor_web.py`) drives the real loop in the browser over a WebSocket: a miscue heatmap lights per word, mastery bars animate as BKT updates, and the next-target panel shifts on screen. Browser-mic voice is layered on additively; the typed path stands alone if voice is flaky.
- **Decodable-book generation pipeline — implemented and verified end-to-end.** A multi-stage ADK `SequentialAgent` writes a phonically-decodable story, illustrates it (real cut-paper art, on-brand-verified), and exports it to Google Docs/Drive with a Gmail parent report. The Docs/Drive and Gmail write paths are verified against real accounts.
- **What's honestly *not* done.** The live per-session loop generates decodable *text* (deterministic builder by default, or the verifier-gated LLM generator); the richer *illustrated* ADK pipeline is not yet folded into the per-session loop. The de-circularized evidence study (Stage D) is done; see *Evidence*. **249 offline unit tests pass** (`uv run pytest tests/unit`).

## The content engine: verifier-gated decodable-book generation

The illustrated-book pipeline is the "generate decodable book" node of the loop, and it embodies the project's core pattern — **an LLM/image model proposes, deterministic Python verifies**:

```mermaid
graph TD
    Profile([PhonicsProfile]) --> Planner[Story Planner]
    Planner -->|StoryOutline| Loop

    subgraph Loop["Writer + Phonics QA Loop"]
        Writer["Decodable Writer"] -->|StoryDraft| QA{"Phonics QA<br/>(deterministic check_decodability)"}
        QA -->|violations| Writer
        QA -->|100% decodable| Done["Finalized Story"]
    end

    Done --> Illust["Illustrator: Nano Banana art<br/>+ palette verifier"]
    Illust --> Export["Docs/Drive export (MCP)"]
    Export --> Report["Gmail parent report (MCP)"]
```

- **Phonics QA guardrail:** a `LoopAgent` wrapping a custom `BaseAgent` re-runs the writer until `check_decodability` (the same `decompose`-based engine) confirms **zero** violations, or it halts. An undecodable word can't ship.
- **On-brand illustration:** a per-book character bible + **Nano Banana** (`gemini-2.5-flash-image`, via Vertex) render each page as cut-paper collage; a **deterministic palette verifier** (`app/skills/palette_verifier.py`) proves every image stays on the locked Phono palette — the same propose/verify pattern as the phonics gate. Real images are embedded inline in the Doc (OpenDyslexic body, Poppins title).
- **MCP write paths + guardrails:** Google's official `@googleworkspace/cli` (`gws`) in MCP stdio mode exposes Drive/Docs/Gmail; export and Gmail-draft callbacks validate the real `doc_id`/`shareable_url`/draft-ID before the pipeline continues.
  - **Note — export path for the live web flow:** the illustrated-book action folded into the live tutor exports the Doc **deterministically** via `app/doc_export.py` (the same propose/verify discipline as the decodability QA loop and palette verifier — the LLM writes the text, deterministic code assembles the Doc), since the agentic LLM-drives-MCP export (`formatter_export_agent`) remains in `root_agent` for `adk web` / integration tests but is not reliable standalone.

Run `python -m scripts.build_sample_book` to produce a full illustrated decodable book end-to-end in Google Docs (sample committed under `results/sample_book/`).

## Evidence: adaptive beats a fixed sequence

`eval/experiments/adaptive_vs_static.py` runs two arms over the same paired, seeded simulated learners: **adaptive** (`select_objective` chooses each session's target from the child's BKT estimate) vs. **static** (a fixed scope-and-sequence that ignores the evidence). Both close the identical loop; both children read the same fixed benchmark probe each session so the fluency comparison is fair.

Result (n=30, 40 sessions): **probe accuracy +0.06, true mean latent mastery +0.04, +4.9 WCPM**. Fully deterministic and LLM-free, so it reproduces exactly. Chart + CSV under `eval/experiments/results/`.

> **On rigor (Stage D, de-circularized).** Those numbers are from an *independent* learner whose generative process is deliberately **not** what the tutor assumes — so the experiment is no longer self-validating. Two mismatches were introduced (`eval/simulated_learner.py`): (1) **emission** is a logistic/IRT curve with per-grapheme item difficulty, not the linear slip/guess that BKT inverts — the tutor must estimate mastery under a model it cannot represent; (2) **learning has no prerequisite/ZPD gate** (the planner's own thesis) — skills are learned by direct practice and *forget* when unpracticed, so adaptive can only win by revisiting each child's decaying frontier. The gaps roughly halve versus the earlier self-consistent learner (which reported +0.14 / +0.09 / +16) but stay positive, and the accuracy advantage holds across all 12 cells of a forgetting/discrimination sweep (`eval/experiments/robustness_sweep.py`; narrowing to +0.002 at the harshest corner) — a smaller, more credible win. One honest wrinkle: on the count of graphemes pushed past a hard 0.95 mastery bar, adaptive and static are a wash (the fixed drill over-concentrates practice), even though adaptive wins on real reading accuracy, mean mastery, and fluency.

## Roadmap

| Stage | Scope | Status |
|---|---|---|
| **A** | Wire the closed loop into a real stateful product (`app/tutor`, `SessionLog`, typed-transcript entry path) | ✅ Done |
| **B** | Gemini Live voice read-aloud → transcript (replaces typed input); verifier-gated LLM book generator wired into the loop as an optional content source | ✅ Done |
| **C** | Web read-along UI + live mastery-graph visualization (the filmable demo) | ✅ Done |
| **D** | De-circularized evidence study (independent learner + externally-validated `decompose`) | ✅ Done |
| **D′** | Self-improving content flywheel (every real session → an eval datapoint) | ⬜ Planned |

The voice loop (Stage B) drops in behind the existing `TutorSession.record_read(prepared, spoken)` signature unchanged — `spoken` simply arrives from ASR instead of stdin.

## Capstone concepts demonstrated

- **Multi-agent systems (ADK)** — a `SequentialAgent` orchestrating the generation pipeline, including a `LoopAgent` wrapping a custom `BaseAgent` QA guardrail.
- **Agent skills** — the deterministic `decompose`/`check_decodability` decodability engine, the BKT mastery model, the miscue-alignment assessor, and the ZPD planner are non-LLM skills the system reasons with.
- **Closed-loop / memory** — `LearnerProfile` is cross-session memory; `app/tutor` makes the tutor stateful and adaptive rather than one-shot.
- **Voice (Gemini Live)** — `app/voice` streams the child's read-aloud to Gemini Live for transcription and feeds the unchanged assessment loop; a confidence-repair hook and grapheme-localized scaffolding sit on top.
- **Live web app** — `app/web` (FastAPI + WebSocket) drives the real loop in a browser with a live miscue heatmap and animating mastery bars (the filmable demo).
- **MCP server integration** — `gws` over MCP stdio exposes Drive/Docs/Gmail write tools.
- **Security / guardrails** — three independent guardrails halt rather than silently continue: the phonics decodability loop, the export-result validator, and the Gmail-draft validator.
- **Observability + deployability** — OpenTelemetry/GenAI telemetry wired at the FastAPI entrypoint (`app/app_utils/telemetry.py`, called from `app/fast_api_app.py`); `Dockerfile` + `agents-cli deploy` path to Cloud Run (not deployed live for this submission).

## Known Limitations

Documented honestly rather than glossed over:

- **The loop generates decodable *text*, not yet the *illustrated* book.** The verifier-gated LLM generator is wired into the per-session loop (Stage B), but the richer illustrated-book ADK pipeline (Nano Banana art + Docs export) is still a separate path; folding illustration into the live loop is future work.
- **Voice is creds-gated and not exercised in CI.** Gemini Live transcription is real (`app/voice`) but requires Live access; without it the web/CLI paths degrade to typed input. The "never-punish" confidence repair is currently a no-op on the live path (Live returns no per-word confidence today) — it only fires in tests via `FakeTranscriber`.
- **The evidence experiment has been de-circularized (Stage D, both halves done).** Previously the simulated learner and planner shared a ZPD assumption, making the result partly self-validating. Both leaks are now closed: the **segmenter half** — `decompose`/`_segment` (the basis of the "guaranteed decodable" claim) is externally validated against a hand-verified grapheme truth set and structural tiling laws swept over `/usr/share/dict/words` (~210k words) in `tests/unit/test_decompose_corpus.py`; and the **learner-model half** — the simulated learner now uses a logistic/IRT emission with per-grapheme difficulty (not BKT's linear slip/guess) and learning with no prerequisite gate plus forgetting (not the planner's ZPD thesis), so the tutor faces a genuine model mismatch. Adaptive still beats static on reading accuracy, mean mastery, and fluency (gaps ~halved but positive across all 12 cells of a parameter sweep); it does *not* reliably win the count past a hard 0.95 mastery bar. The remaining honesty caveat: the learner's constants are reasonable but uncalibrated, and WCPM is still a deterministic function of error count, not an independent timing measurement.
- **`gws` CLI is pinned to `0.7.0`.** Google removed MCP server mode in `0.8.0` ([PR #275](https://github.com/googleworkspace/cli/pull/275)). The pin works today but is a deliberate pin to a version its maintainers moved past.
- **The eval grading harness has a JSON-parsing bug** unrelated to the agent: when the LLM-judge's `explanation` contains raw newlines, `agents-cli eval grade` fails to parse it. This affects automated eval scoring, not agent behavior — `tests/unit` and `tests/integration` pass cleanly (modulo live-API rate limits).

## Project Structure

```
agy-capstoneproject/
├── app/
│   ├── agent.py            # ADK generation pipeline, guardrail callbacks, MCP wiring
│   ├── schemas.py          # Pydantic contracts (incl. LearnerProfile, SessionLog)
│   ├── phonics_db.py        # Grapheme inventory, level sequence, BKT params
│   ├── brand.py            # Locked Phono brand: palette, cut-paper style, prompt composers
│   ├── illustrator.py      # Real illustrations: character bible + Nano Banana + verify/regen
│   ├── doc_export.py       # Embed real images into the Google Doc
│   ├── tutor/              # ★ Stage A: the closed loop as a stateful product
│   │   ├── session.py        #   TutorSession: prepare() -> record_read()
│   │   ├── book_source.py    #   swappable content seam (deterministic + LLM provider)
│   │   └── llm_book.py       #   Stage B: verifier-gated LLM book generator
│   ├── voice/              # ★ Stage B: Gemini Live read-aloud (transcriber + scaffold)
│   ├── web/               # ★ Stage C: FastAPI + JS live read-along demo
│   ├── skills/
│   │   ├── decodability.py   #   decompose() — the keystone grapheme engine
│   │   ├── planner.py        #   select_objective() — ZPD target selection
│   │   ├── mastery.py        #   update_from_evidence() — Bayesian Knowledge Tracing
│   │   ├── alignment.py      #   assess() — miscue analysis + grapheme attribution
│   │   └── palette_verifier.py
│   └── store/
│       ├── learner_store.py  #   JSON LearnerProfile persistence (current state)
│       └── session_log.py    #   JSONL append-only session history
├── eval/                   # Simulated learner + the adaptive-vs-static experiment
├── scripts/
│   ├── tutor_cli.py          # ★ typed-transcript entry path for the real loop
│   ├── tutor_web.py          # ★ Stage C: live web read-along server
│   ├── tutor_voice_cli.py    # ★ Stage B: Gemini Live voice entry path
│   └── build_sample_book.py  # End-to-end illustrated decodable book in Docs
├── results/sample_book/    # Sample generated illustrated book (page PNGs)
├── tests/                  # unit (incl. tutor loop), integration, eval datasets
├── Dockerfile
└── pyproject.toml
```

## Requirements

- **Python** 3.11–3.13
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — dependency management
- **Node.js / npm** (provides `npx`) — required to run the `gws` MCP server
- **[agents-cli](https://github.com/googleapis/agents-cli)** — `uv tool install google-agents-cli`
- **Google Cloud SDK** — for `gcloud auth application-default login` (required by `agents-cli eval`)
- A Google Cloud project with Vertex AI enabled, and a Google AI Studio API key

## Setup

1. Clone and install:
   ```bash
   git clone https://github.com/tannergriffith-beep/phono-storyforge.git
   cd phono-storyforge
   agents-cli install
   ```

2. Create `app/.env`:
   ```
   GOOGLE_API_KEY=<your AI Studio API key>
   GOOGLE_GENAI_USE_VERTEXAI=0
   GOOGLE_CLOUD_PROJECT=<your GCP project ID>
   GOOGLE_CLOUD_LOCATION=global
   LOG_LEVEL=INFO
   ```

3. Authenticate `gcloud` for eval/ADC:
   ```bash
   gcloud auth application-default login
   ```

4. Set up `gws` credentials for real Docs/Drive/Gmail export (the MCP subprocess only inherits a safe-list of env vars, so credentials must go in the default file location):
   ```bash
   mkdir -p ~/.config/gws
   cp /path/to/your/client_secret_xxx.json ~/.config/gws/client_secret.json
   ```

## Running it

**The closed-loop tutor (Stage A — no API keys needed, fully offline):**
```bash
uv run python -m scripts.tutor_cli --learner ada --interest dinosaurs --age 6
# shows the planner's target + a decodable book; type what the child read
# (or '=' for a perfect read). Run again to watch the target adapt.
```

**The live web read-along (Stage C — the filmable demo, offline by default):**
```bash
uv run python -m scripts.tutor_web            # → http://127.0.0.1:8000
# Begin a session, read a page (type/preset, or the 🎤 browser mic), and watch
# the miscue heatmap, mastery bars, and next-target panel update live.
uv run python -m scripts.tutor_web --llm-book # use the verifier-gated LLM books
```

**Voice read-aloud over Gemini Live (Stage B — needs Live access):**
```bash
uv run python -m scripts.tutor_voice_cli --learner ada   # speak the page aloud
# Requires the `voice` extra for mic capture: uv sync --extra voice
```

**The illustrated-book generation pipeline (live LLM + MCP):**
```bash
agents-cli playground            # interactive
python -m scripts.build_sample_book   # full illustrated book in Google Docs
```

**The evidence experiment:**
```bash
uv run python -m eval.experiments.adaptive_vs_static   # writes chart + CSV
```

## Testing

```bash
uv run pytest tests/unit tests/integration
```

Integration tests set `INTEGRATION_TEST=TRUE`, swapping the real `gws` MCP toolset for mocked tools (works around an ADK limitation introspecting a live `McpToolset`). Real MCP export/Gmail behavior is exercised through `agents-cli playground`. The `tests/unit` suite (incl. the `app/tutor` closed loop) is fully offline and deterministic.

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

`Dockerfile` builds a standalone FastAPI image (`app/fast_api_app.py`) suitable for Cloud Run. Not deployed live for this submission — see Known Limitations.
