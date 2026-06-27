# 04 — Features & Functionality

This describes **what the product does** and **the value and workflow of each feature**, with no discussion of how anything looks. "Tool" = one instructional activity/resource inside a toolkit.

---

## A. The Toolkit (current core product)

**Purpose:** A complete, parent-led reading-intervention program a family can run at home.

**Structure:**
- **20 tools** per toolkit, grouped into **4 skill units**.
- Grade-banded products: Foundation (K–2), Fluency (3–5, built), Independence (6–8), Summer (cross-grade K–8).
- Full toolkits span ~30 weeks / ~60 sessions; the Summer toolkit is lighter (~10 weeks / 20 sessions, ~2 sessions/week).

**Unit pattern (Summer toolkit example):**
1. **Sound Play** (5 tools) — phonological awareness: segmenting/blending sounds, rhyming, syllables.
2. **Word Work** (5 tools) — decoding and spelling with manipulatives (sound boxes, letter tiles, syllable types, prefixes/suffixes, word families).
3. **Read & Fluency** (5 tools) — connected-text reading, partner/shared reading, repeated reading, audio-assisted reading.
4. **Comprehension** (5 tools) — story elements, retelling, vocabulary, dialogic ("wondering") reading, making connections.

(The Fluency 3–5 toolkit uses the units Decoding, Word Study, Fluency, Comprehension, plus support tools.)

**User value:** A parent gets a structured, sequenced program — not a pile of worksheets — that tells them exactly what to do each session and in what order.

---

## B. The Tool (the atomic unit)

**Purpose:** One self-contained activity a parent can run, correctly, without training.

**Functional anatomy (what every tool contains — described by function, not appearance):**
- **Labeling:** age/grade band, skill focus, estimated time.
- **Parent Guide:** step-by-step instructions, including a script ("what to say"), the teaching moves, and what to do when the child makes an error. Built around "I do, we do, you do."
- **Dual-track guidance (in cross-grade tools):** a **Younger Reader (K–2)** path and an **Older Reader (3–8)** path for the same tool; the parent picks based on their child.
- **Activity content:** the practice material itself (e.g., word chains, tiles to build, passages to read, retell prompts), often provided at two difficulty levels.
- **Coaching notes:** the single most important move for that tool, and tips like "model first," "stop at frustration," "celebrate every small win."
- **Answer guide / parent notes:** expected responses, plus the "why" behind the skill so the parent understands what they're building.

**User value:** An untrained adult can deliver an evidence-based activity correctly and confidently, and adapt it to their child's level.

**Example (Letter Tile Decoder):** the parent builds a word tile-by-tile, blends it, then changes one tile at a time ("cat → sat → sit → hit"); older readers use digraph tiles and add prefixes/suffixes ("read → reread → rereading"). The parent note explains the point: tiles turn spelling into a building problem, so the child stops guessing and starts decoding.

---

## C. Session structure

**Purpose:** Give the family a repeatable 15–20 minute routine.

**Workflow (Summer model):**
- **0–5 min — Sound Play:** parent models a phonological task, child attempts, effort is celebrated.
- **5–10 min — Word Work:** parent models with manipulatives; "I do, we do, you do"; child builds/spells words.
- **10–20 min — Read & Fluency:** child reads instructional-level text aloud; parent corrects immediately; may reread for fluency.
- **Woven in — Comprehension:** scaffolded questions during/after reading (retell, "wonder" prompts, story elements).
- **Supplemental (outside session):** 10–15 min of daily audiobook / audio-assisted reading (child follows printed text while listening).

**User value:** The parent never has to design a lesson; the structure is built in and time-boxed.

---

## D. Progress tracking, celebration & motivation

**Purpose:** Make invisible learning visible, sustain motivation, and protect confidence.

**Features:**
- **Repeated Reading Tracker:** records 3 timed reads of a passage in one session (cold → practiced → performance), surfacing the typical gain so growth is visible. Younger readers can track "Felt easier? Y/N" instead of timing.
- **Progress Tracker & Celebration Log** (in the Fluency toolkit) has three parts:
  1. **Weekly session log** — track consistency.
  2. **Skills checklist** — mark skills as mastered, unit by unit.
  3. **Celebration log** — free space to record wins together.
- Designed to be displayed where the child can see it daily.

**Guiding rule:** progress is framed around **effort and consistency**, not accuracy scores or comparison — children with dyslexia often feel they aren't progressing even when they are, so making real growth visible changes how they feel about reading.

**User value:** Motivation and confidence for the child; evidence of progress and a consistency nudge for the parent.

---

## E. Lesson plans, passages & home-session guides

**Purpose:** Deeper support for parents who want fuller structure.

**Features:**
- **Time-blocked lesson plans** — minute-by-minute session scripts (review → introduce → guided practice → independent application), with an overview of age/skill/time/materials and "why it matters."
- **Decodable / fluency passages** — short, age-appropriate stories aligned to the skills being taught, with running word counts and a words-correct-per-minute tracking grid, plus expression/phrasing guidance and post-reading discussion prompts.
- **Home reading session guide** — how to run a reading session: timing, materials, error-correction scripts, and how to choose instructional-level text.

**User value:** Turns "read with your kid" into a structured, correctable, trackable practice.

---

## F. Free reading-check screener (lead magnet & triage)

**Purpose:** Help a parent decide whether to watch, look closer, or act — and serve as the top of the marketing funnel.

**Workflow:**
- Age-banded checklists (4–6, 6–8, 8+) of early warning signs, plus at-any-age emotional red flags.
- A simple scoring rule: **0–2 items** = keep watching; **3–5** = worth a closer look; **6+** = signs worth acting on now.
- Each tier gives next steps, including how to request a school evaluation in writing and to start structured practice at home.
- Distributed via social comment-keyword → auto-message → email opt-in → tool delivered (see `05-user-flows.md`).

**User value:** Removes guesswork and reduces fear; gives the parent an immediate, credible next action.

---

## G. Planned software features (future phases — functional intent only)

> These are envisioned, not built. Described by function/flow only. Specific interface behaviors and any visual treatments are out of scope.

- **Parent-guide chatbot:** answers parents' questions 24/7, grounded in the toolkit content; escalates complex or edge cases to a human.
- **Interactive session app:** guides a parent through a session, including:
  - choosing the day's tool, browsing the tool library with filters, and viewing tool detail (overview / practice / quick reference).
  - an **active-session mode** with a timer that **counts up** (to reduce time pressure) and collapsible tips.
  - a **session-complete capture** of how it went via a mood selection (e.g., smooth / good / tough / tired) plus optional notes — where "tough" is explicitly not "bad."
  - a **progress view** (weekly summary, skill progress, milestones) framed around sessions and time rather than accuracy.
  - a **guide** section of context-aware articles tagged by intent (how-to / what-if / why-this).
  - a short onboarding flow that opens with reassurance ("you found the right place").
- **AI tutoring agent:** works directly with the child on structured-literacy activities.
- **Specialist directory:** lets parents search vetted tutors by location, certification, age specialty, price, and format (in-person / online / both).

**User value (future):** Moves the family from self-directed printables toward guided, adaptive, supported practice and a path to a real specialist.
