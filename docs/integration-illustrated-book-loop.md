# Integration Plan — Fold the illustrated e-book pipeline into the live closed loop

> **Status:** IMPLEMENTED (MVP + Phase 2 shipped 2026-06-25; deviations recorded in §12). Self-contained brief for a fresh session that
> has none of the prior conversation context. Read this top-to-bottom before coding.
> Written 2026-06-25. Target: ~1 focused day for the MVP; deadline is comfortable.

## 0. TL;DR

Phono StoryForge currently has **two halves that don't touch**:

1. **The live closed-loop tutor** (`app/tutor`, `app/web`): generates a decodable
   *text* practice page to a child's target, scores the read, updates per-grapheme
   mastery (BKT), advances the target. This is what `scripts/tutor_web.py` serves.
2. **The illustrated e-book pipeline** (`app/agent.py` ADK `root_agent`): writes a
   story to a `PhonicsProfile`, runs a decodability QA guardrail loop, illustrates
   each page (Nano Banana), exports to Google Docs/Drive, drafts a Gmail parent
   report. Today it is invoked only by the standalone `scripts/build_sample_book.py`.

**Goal:** add an explicit, end-of-session action in the web tutor — "Generate
[child]'s illustrated take-home book for today's target" — that runs the existing
ADK pipeline, driven by the live loop's `Objective` + `LearnerProfile`, and surfaces
the resulting Google Doc (link + page-image preview) in the browser.

This is mostly **wiring**, not building: the expensive parts (story writing, the
decodability guardrail, illustration, Docs export) already exist and are verified.
It also resolves the project's biggest narrative risk — "two architectures, one
story" — by making the ADK pipeline consume the planner/mastery output.

## 1. Definition of done

- From the web demo, after recording a read (or at any point with a prepared
  session), the user can trigger illustrated-book generation for the current
  objective and receive, in the browser: a **Google Doc link** and a **preview**
  of the generated pages (text + images), with the book provably **decodable for
  that child's mastered levels** (the existing QA loop guarantees this).
- Generation runs **asynchronously** with **progress updates** streamed to the UI
  (it takes minutes; it must never block the per-page read loop).
- The feature is **opt-in and creds-gated** (a `--illustrated-book` flag, mirroring
  the existing `--llm-book`). With creds absent, the default offline web demo is
  unchanged and the button is hidden/disabled with a clear message.
- A new **unit test** covers the `Objective + LearnerProfile -> PhonicsProfile`
  adapter (deterministic, offline). The full generation path is creds/LLM-gated and
  exercised manually, not in the offline suite.
- `uv run python -m pytest tests/unit -q` stays green; the deterministic
  `eval.experiments.adaptive_vs_static` CSV still reproduces byte-for-byte.

## 2. Why it's tractable (the seams already exist)

- **The live loop has a swap-in seam.** `app/tutor/book_source.py` defines
  `BookProvider`, a Protocol whose single method is
  `__call__(objective: Objective, profile: LearnerProfile) -> BookLike`. The
  deterministic builder and the Stage-B verifier-gated LLM generator both implement
  it; `--llm-book` swaps providers. (Note: this seam returns the *text* page the
  child reads. The illustrated book is a *separate, slower deliverable* and should
  NOT be forced through this per-session synchronous seam — see Architecture.)
- **The ADK pipeline is profile-driven, not hardcoded.** `app/agent.py`'s
  `root_agent = SequentialAgent(intake -> story_planner -> writer_qa_loop(LoopAgent)
  -> illustrator -> export -> parent_report)` keys everything off a `phonics_profile`
  in ADK session state. (`build_sample_book.py`'s "Sam the Fox" is only in that demo
  script, not the agent.)
- **Both halves share the `decompose` / `check_decodability` keystone**
  (`app/skills/decodability.py`), so a book the pipeline emits is decodable by the
  exact same definition the live loop scores against. No semantic mismatch.

## 3. Schemas (verified — map cleanly)

`app/schemas.py`:
- `PhonicsProfile`: `target_level` and `mastered_levels` are `Literal` over
  `["short_vowels","digraphs","blends","silent_e","r_controlled","vowel_teams",
  "glued_sounds","y_vowel","suffixes"]`; `interest: str` (required); `age: int`
  (required). No `name` field (character naming happens via `CharacterBible`).
- `Objective`: `target_grapheme`, `target_level`, `mastered_levels`,
  `review_graphemes`.
- `LearnerProfile`: `learner_id`, `name` (default ""), `age` (default 6),
  `interest` (default ""), plus the mastery state.

**Adapter mapping** (`Objective` + `LearnerProfile` -> `PhonicsProfile`):
- `target_level   <- objective.target_level`
- `mastered_levels <- objective.mastered_levels`  (so the book is decodable for THIS child)
- `interest       <- profile.interest`  (fall back to a safe default like "animals" if blank)
- `age            <- profile.age`

**VERIFY FIRST (open question):** confirm `objective.target_level` /
`objective.mastered_levels` values are a subset of the `PhonicsProfile` `Literal`
set above. The planner/`phonics_db` level names must match exactly or Pydantic will
reject the profile. Check `app/phonics_db.py` `LEVEL_SEQUENCE` against the Literal.
If they diverge, add a small level-name normalization in the adapter and unit-test it.

## 4. Architecture of the integration

Do **not** make the illustrated book the per-page read material (latency = minutes;
the read loop needs a lightweight page now). Instead:

```
[web read loop, unchanged]  prepare -> read -> record_read -> mastery++ -> next target
                                                   |
                                                   v  (explicit user action)
                                  "Generate [child]'s illustrated book"
                                                   |
            Objective + LearnerProfile --adapter--> PhonicsProfile
                                                   |
                                       run ADK root_agent (async worker)
                       intake* -> planner -> writer+QA(decodability guardrail)
                                  -> illustrator -> Docs export -> (parent report)
                                                   |
                              export_result {doc_id, shareable_url} + page images
                                                   |
                          stream progress -> browser; show link + page previews
```

\*The `intake_agent` exists to turn *raw* profile text into a `PhonicsProfile`.
Since we already have structured data, prefer **seeding `phonics_profile` directly
into ADK session state and starting the run from `story_planner`** (skip intake),
OR keep intake but feed it a deterministic prompt built from the profile. Decide
during implementation; seeding state is cleaner and avoids an extra LLM hop.

### Running the ADK agent from the web server
- Use the ADK `Runner` + `InMemorySessionService`. Create a session, set initial
  state `{"phonics_profile": profile.model_dump()}`, run the agent, and collect the
  final `export_result` state (the export callback at `app/agent.py` saves
  `{"doc_id","shareable_url"}` there) plus the generated pages/images.
- The agent is **synchronous and slow**. Run it in `asyncio.to_thread(...)` (the web
  server already does this for voice transcription — see `app/web/server.py`
  `_transcribe`). Emit progress events over the existing WebSocket as stages
  complete (planning / writing / checking decodability / illustrating page i/N /
  exporting). Even coarse stage messages are fine for the MVP.

## 5. Implementation steps

### Step 1 — Adapter (small)
New module `app/tutor/illustrated_book.py` (or extend `book_source.py`):
- `objective_to_phonics_profile(objective: Objective, profile: LearnerProfile) -> PhonicsProfile`
  with the mapping in section 3, an interest fallback, and level-name validation.
- Unit test in `tests/unit/test_illustrated_book.py`: a couple of objectives/profiles
  -> expected `PhonicsProfile`; assert it validates and round-trips. Offline, fast.

### Step 2 — Generation function (medium)
In `app/tutor/illustrated_book.py`:
- `async def generate_illustrated_book(objective, profile, *, progress_cb=None) -> IllustratedBookResult`
  that builds the profile, runs `root_agent` via the Runner in a worker thread,
  pushes stage strings through `progress_cb`, and returns a small dataclass:
  `{ shareable_url, doc_id, pages: [{text, image_ref}], decodable: bool, source }`.
- Image handling for preview: the illustrator produces images (saved to a results
  dir like `build_sample_book` does, or base64). For the MVP, returning the Doc
  `shareable_url` is enough; page-image thumbnails are a nice-to-have (Phase 2).
- Reuse `check_decodability` to set `decodable` defensively from the final pages.

### Step 3 — Web wiring (medium)
- `app/web/server.py`: add a WebSocket action `{"action":"generate_book"}` handled
  when a session is prepared. It calls `generate_illustrated_book(...)`, forwards
  progress as `{"type":"book_progress","message":...}`, and on completion sends
  `{"type":"book_ready","shareable_url":...,"pages":[...]}` (or `{"type":"error"}`).
- `create_app(...)`: accept an `illustrated_enabled: bool` (or an injected generator)
  so the feature is gated. Keep the default (no creds) path identical to today.
- `scripts/tutor_web.py`: add `--illustrated-book` (mirror `--llm-book`); when set,
  enable the feature in `create_app`. The launcher already calls `load_dotenv(app/.env)`.

### Step 4 — UI (small/medium)
- `app/web/static/index.html` + `app.js`: add a "Generate [name]'s book" button in
  the session panel (shown only when the feature is enabled), a progress line, and a
  result panel with the Doc link and (Phase 2) page thumbnails. Match existing brand
  styles in `style.css`.
- Keep it additive; the typed/preset/voice flows and the mastery viz are untouched.

### Step 5 — Creds gating + graceful failure (medium)
- The pipeline needs: **Vertex** (`GOOGLE_GENAI_USE_VERTEXAI=1` + gcloud ADC — the
  working backend; see Environment), the **image model** (Nano Banana,
  `gemini-2.5-flash-image` via Vertex), and the **`gws` MCP** for Docs/Drive/Gmail
  export (`~/.config/gws/client_secret.json`; see README setup).
- If creds/quota fail at any stage, catch it, send a clear `error` to the UI, and
  leave the read loop fully usable. Never crash the server. Consider a "skip export,
  show pages only" degraded mode if Docs export is the only thing missing.

### Step 6 — Tests + verification
- `uv run python -m pytest tests/unit -q` green (adapter test added; nothing else
  regressed; offline default web demo still imports and runs with no creds).
- Manual end-to-end: `uv run python -m scripts.tutor_web --illustrated-book`,
  complete a session, click generate, confirm a real Doc link + decodable pages.
- Confirm `uv run python -m eval.experiments.adaptive_vs_static` still reproduces the
  committed CSV exactly (this change must not touch the experiment).

## 6. Constraints & guardrails (do not violate)

- **Do not break the offline default.** With no creds and no `--illustrated-book`,
  `scripts/tutor_web.py` must behave exactly as today. The feature is strictly opt-in.
- **Do not put illustrated generation inline in the read loop.** It is an explicit,
  async, end-of-session action. The per-page read must stay instant.
- **Do not modify `app/skills/mastery.py`** (BKT) or the eval experiment harness.
  Keep the deterministic experiment reproducible.
- **Preserve the decodability guarantee.** The book must be decodable for the
  child's `mastered_levels`; the QA `LoopAgent` already enforces this — keep it in
  the path and assert the final result.
- **Voice path is unrelated** — don't touch `app/voice` for this work.

## 7. Environment notes the new session needs

- **Backend = Vertex AI.** `app/.env` has `GOOGLE_GENAI_USE_VERTEXAI=1`,
  `GOOGLE_CLOUD_PROJECT=agy-capstone`, `GOOGLE_CLOUD_LOCATION=us-central1`, and
  auth is gcloud ADC (`gcloud auth application-default login`, already done). The
  Developer-API path is dead: AI Studio now issues `AQ.`-prefix auth keys that
  currently 401 on the native endpoint, so an API key is NOT a viable path here.
  Everything (LLM + images) must run through Vertex.
- **`gws` MCP creds** are required for Docs/Drive/Gmail export
  (`~/.config/gws/client_secret.json`; pinned `gws` 0.7.0 — see README). Without
  them, export fails; design the degraded mode accordingly.
- **Run tests** with `uv run python -m pytest tests/unit -q`.
- **Markdown gotcha:** the editor (SlashMD) can corrupt `.md` files when the
  Edit/Write tools write through the IDE while a `.md` is open in it (it mangles
  mermaid fences, links, code blocks). Mitigation already applied:
  `workbench.editorAssociations: {"*.md": "default"}` in VSCode user settings. If a
  `.md` still gets mangled, write/patch it via a Bash heredoc instead of the Edit
  tool. Code files (`.py`, `.js`, `.html`, `.css`) are unaffected.
- **ADK deprecations:** `SequentialAgent`/`LoopAgent` emit deprecation warnings in
  google-adk 2.x. They still work; don't get blocked refactoring them for this task.

## 8. Risks & open questions (resolve early)

1. **Level-name match** between `Objective`/`phonics_db` and the `PhonicsProfile`
   `Literal` (section 3). Verify before writing the adapter.
2. **Running ADK `root_agent` inside async FastAPI.** Confirm the Runner +
   `InMemorySessionService` pattern; run in a worker thread; make sure the agent's
   own async/event-loop use doesn't conflict. Look at how `build_sample_book.py`
   drives the agent for a working reference.
3. **Latency & Vertex quota.** Image generation + Docs export take minutes and the
   Vertex Live/image quota on a new project can throttle (`RESOURCE_EXHAUSTED`).
   Stream progress, time out gracefully, and surface a clear retry message.
4. **Image preview transport.** Decide MVP (Doc link only) vs Phase 2 (inline page
   thumbnails as base64/static files). Don't block the MVP on thumbnails.
5. **Where images are written.** `build_sample_book` writes under a results dir;
   decide whether the web flow reuses that or returns images inline.

## 9. Phasing

- **MVP (target):** adapter + async `generate_book` action + progress + return the
  Google Doc `shareable_url`; button in the UI; creds-gated; adapter unit test.
- **Phase 2 (polish):** inline page-image thumbnails in the result panel; richer
  per-page progress; "skip export / pages-only" degraded mode; optional parent-report
  link.

## 10. Key files

- `app/tutor/book_source.py` — the `BookProvider` seam (reference for gating pattern)
- `app/tutor/session.py` — `TutorSession.prepare` / `record_read`
- `app/web/server.py` — WebSocket actions; `_transcribe` shows the async-worker pattern
- `app/web/static/{index.html,app.js,style.css}` — UI
- `app/web/viz.py` — payload builders
- `scripts/tutor_web.py` — launcher + flag wiring (`--llm-book` is the template)
- `app/agent.py` — the ADK `root_agent` pipeline + export callback (`export_result`)
- `app/schemas.py` — `Objective`, `LearnerProfile`, `PhonicsProfile`, `StoryOutline`, etc.
- `app/skills/decodability.py` — `decompose` / `check_decodability` (shared keystone)
- `scripts/build_sample_book.py` — working reference for driving the illustrated pipeline
- `tests/unit/` — add `test_illustrated_book.py`

## 11. Kickoff prompt for the new session

Paste this into a fresh session at the repo root:

---
Read `docs/integration-illustrated-book-loop.md` in full first — it is the
self-contained plan and the source of truth for this task. Then implement the MVP it
describes: connect the illustrated e-book pipeline (`app/agent.py` `root_agent`) into
the live web tutor as an explicit, async, creds-gated "Generate [child]'s illustrated
book for today's target" action that surfaces the resulting Google Doc link in the UI.

Constraints (from the plan): keep the offline default web demo unchanged and the
feature strictly opt-in (`--illustrated-book`, mirroring `--llm-book`); do NOT put
generation inline in the read loop (it's async/end-of-session); do NOT modify
`app/skills/mastery.py` or the eval experiment; preserve the decodability guarantee
via the existing QA loop; the backend is Vertex (`GOOGLE_GENAI_USE_VERTEXAI=1` + gcloud
ADC — API keys are dead). Run `uv run python -m pytest tests/unit -q` before and after
and keep it green; add the adapter unit test. Resolve the section-8 open questions
(especially the level-name match) before writing the adapter.

Work on a new branch off the current one. Start by confirming the section-3/section-8
facts against the code, then go step by step (adapter -> generation fn -> web action
-> UI -> gating -> tests). Show me the adapter + a working Doc-link round-trip before
polishing the page-thumbnail preview.
---

## 12. Implementation deviations (as-built, 2026-06-25)

The MVP + Phase 2 shipped. Two deviations from this plan, both forced by reality
and verified end-to-end on Vertex (ratified):

1. **Model: `gemini-flash-lite-latest` → `gemini-2.5-flash`** (`app/agent.py`).
   Two reasons: (a) the `-latest` alias is a Developer-API name that **404s as a
   Vertex publisher model**, so the whole ADK pipeline was already broken on the
   mandated Vertex backend; (b) the flash-lite tier (`gemini-2.5-flash-lite`,
   which *does* resolve) could **not** reliably satisfy the decodability guardrail
   — the writer kept emitting out-of-budget words and the QA `LoopAgent` rejected
   it. `gemini-2.5-flash` resolves and converges. This is a global change to
   `root_agent` (also fixes `adk web` / integration on Vertex); eval is untouched.

2. **Deterministic Doc export instead of the LLM export agent.** The plan said to
   read `export_result` from `root_agent`'s `formatter_export_agent`, but that
   LLM-drives-MCP-then-hand-formats-JSON step **consistently returned
   `doc_id="unknown"`** and tripped its own guardrail. The live web flow instead
   exports the Doc **deterministically** via `app/doc_export.py` (the
   `build_sample_book` path) — the same propose/verify discipline as the
   decodability QA loop and the palette verifier: the LLM writes the (QA-gated)
   text, deterministic code assembles the Doc, so a real link is produced every
   time the export creds are present. `formatter_export_agent` is left **unchanged**
   in `root_agent` for `adk web` / integration tests, but is not reliable standalone.

As-built notes (within the planned scope): illustration is driven directly via
`app/illustrator.py` (Nano Banana + palette verifier, CharacterBible from the
planner outline) rather than the prompt-only `illustration_prompt_agent`, which is
dropped from the seeded pipeline; page thumbnails are returned as inline base64;
and there are two independent degrade axes (illustration-unavailable → text-only;
Docs-export-unavailable → pages-only), surfaced via `IllustratedBookResult.source`.
