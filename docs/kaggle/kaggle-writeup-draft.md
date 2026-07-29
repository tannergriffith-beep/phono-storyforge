# Phono StoryForge

### A multi-agent pipeline that writes decodable storybooks a struggling reader can actually read

---

*Draft for the Kaggle "AI Agents: Intensive Vibe Coding Capstone Project" Writeup — Track: Agents for Good. Copy into the Kaggle Writeup editor and trim/adjust tone as needed. ~1,050 words, well under the 2,500-word cap, so there's room to expand any section (e.g. a results/demo walkthrough once the video exists) if you want more detail.*

---

## The problem

I'm building Phono, a literacy support company for parents of dyslexic kids, alongside this capstone. The single biggest gap I keep running into in that world: every reading specialist will tell you a struggling reader needs decodable books — stories built *only* from the phonics patterns and sight words that child has already mastered, so they can read independently instead of guessing or memorizing. The problem is supply. Decodable books that match a specific child's exact phonics level, age, and interests basically don't exist at scale. Parents get generic workbooks, or they get books that are decodable in theory but boring enough that a reluctant reader won't open them twice.

Phono StoryForge is my attempt to solve the supply problem with agents instead of a slow human content pipeline: describe a child once, and get back a story written specifically for them, phonics-checked against their exact profile, illustrated, and delivered with a parent-facing progress note — in minutes, not weeks.

## What it does

Tell it a child's age, current phonics target (say, consonant blends), the levels they've already mastered, their known sight words, and what they're into (space, dinosaurs, soccer — whatever), and a 7-agent pipeline:

1. **Intake Agent** turns that free-text description into a structured reading profile.
2. **Story Planner Agent** designs a plot, characters, and setting that fit the phonics constraints *before* a single page is written.
3. **Decodable Writer Agent** writes the story page by page.
4. **Phonics QA Agent** — a security guardrail — runs a deterministic, non-LLM checker against every word in the draft. If anything violates the child's profile, it kicks the draft back to the writer with specifics. It loops until the story is 100% decodable, or halts the pipeline entirely if it can't converge, rather than ever shipping a story that isn't actually safe for that reader.
5. **Illustration Prompt Agent** generates page-by-page art direction from a locked style guide, with age-band rules so a book for a 12-year-old doesn't look like it's for a toddler.
6. **Formatter/Export Agent** assembles the finished book and exports it to Google Docs and Drive via MCP — and is gated by a second guardrail that verifies both the document ID *and* the shareable link are real before letting anything downstream happen.
7. **Parent Report Agent** writes a warm, specific progress note (what patterns the story reinforced, which sight words to practice) and drafts it as a real Gmail email — gated by a third guardrail that confirms the draft was actually created, not just claimed.

## Why the guardrails matter as much as the agents

The thing I kept coming back to while building this: an LLM-generated story that's *almost* decodable is worse than no story at all, because a parent has no way to spot-check 200 words of text against an Orton-Gillingham phonics sequence. The system has to be the check, not the parent. Same logic applies downstream — if export silently fails, the worst outcome isn't an error message, it's a confident parent email linking to a broken document. So every handoff between agents that touches the outside world (a real document, a real email) has an explicit guardrail that raises and halts rather than degrading gracefully into something that *looks* fine. I found and closed one gap in this during the build: the export guardrail originally checked that the document ID was real, but not that the shareable link was — so a doc could "succeed" with a broken link in the parent's inbox. Caught it with a regression test, fixed it, verified all tests green.

## Concepts demonstrated

- **Multi-agent systems (ADK)** — a `SequentialAgent` orchestrating six stages, including a `LoopAgent` wrapping a custom revise-until-correct guardrail agent.
- **MCP server integration** — Google's official Workspace CLI, run as an MCP server, gives the formatter and parent-report agents real write access to Docs, Drive, and Gmail.
- **Security features** — three independent guardrails (phonics QA loop, export validator, Gmail-draft validator), each tested with unit and integration tests, each one designed to halt the pipeline rather than continue on bad output.
- **Agent skills** — the phonics checker is a deterministic Python skill, not an LLM guess. I didn't want "is this decodable" to be a judgment call an LLM makes about itself.
- **Antigravity** — I built this in Antigravity end to end. The most useful lesson from that process wasn't a feature, it was a habit: I stopped trusting "it worked" from the coding agent and started checking the real system directly — the actual Drive folder, the actual Gmail drafts — every time a write-path claim came up. More than once that habit caught a claim that didn't hold up under direct verification.
- **Deployability** — a Dockerfile and `agents-cli deploy`/`infra` path exist for Cloud Run; not deployed live for this submission, since a public repo with real setup instructions satisfies the project-link requirement without one.

## Verified, not assumed

Both real-world write paths — the Google Doc export and the Gmail draft — are confirmed working against real accounts, not just mocked test runs. That mattered enough to me that I treated "the agent said it worked" as worth nothing until I checked the actual Drive folder and the actual Gmail drafts folder myself.

## What's still rough, on purpose left visible

Two things I'm not hiding: the Google Workspace MCP integration is pinned to an older CLI version, because the current version dropped MCP support entirely — a deliberate, documented trade-off rather than a silent one. And the automated eval-grading harness has an unrelated JSON-parsing bug on certain judge responses, which affects scoring runs but not the agent's actual behavior (unit and integration tests, which don't depend on that harness, pass cleanly).

## Why this is the project I wanted to build

This isn't a toy problem I picked for the capstone — it's the actual product gap I'm trying to close at Phono. Building it as a multi-agent system instead of a single prompt forced me to be honest about where judgment needs a deterministic check instead of a vibe, which is exactly the discipline I want in anything that ends up in front of a struggling reader and their parent.

**Repo:** https://github.com/tannergriffith-beep/phono-storyforge
