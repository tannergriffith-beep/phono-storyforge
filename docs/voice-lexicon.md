# Phono / StoryForge — Voice Lexicon

*The plain-language glossary for all user-facing copy (design-system §18). Every
redesign PR honors this; `tests/unit/test_copy_invariants.py` enforces the
child-facing and chrome parts automatically.*

## The rule
Two voices, one personality (the knowledgeable neighbor):
- **To the parent:** warm, plain, specific, honest. Names the exact fear, the exact
  technique, the exact age. Never clinical, never salesy, never "miracle."
- **To/about the child:** gentle, success-first, story-led. Effort and wins, never
  scores. "Tough" is never "bad."

## Forbidden → preferred

| Don't say (user-facing) | Say instead |
|---|---|
| mastery / mastered | "sounds learned", "sounds your reader knows well" |
| grapheme | "sound" (e.g. "the /sh/ sound") |
| target / objective | "the next sound your reader is ready for", "tonight's sound" |
| ZPD / BKT / P(L) | *(never shown; internal only)* |
| decodability / decodable | "made from sounds they already know" |
| accuracy %, WCPM, "errors" | *(adult-only; never the headline — see below)* |
| "the loop adapted" / "closed-loop" | "what's next", "the next story changes for them" |
| "session #0" (zero-indexed) | "your first story together", "story 3 together" |
| "learner id" / "learner" | "your reader", the child's first name |
| "Score read" | "How did it go?" (an adult action, off the child's page) |
| "generation source: deterministic/llm" | *(hidden; quiet reassurance only)* |

## Where technical terms are still allowed
- **Internal tooling, logs, and the optional "behind the scenes" adult/educator view.**
- The planner's `Objective.rationale` (brain-generated) may stay technical — but it is
  **never echoed verbatim** to a parent. The Why card composes its own plain sentence
  from structured fields (PR7).
- Accuracy / WCPM may appear in the adult "For grown-ups" view, clearly labelled as a
  teacher's metric and **demoted below** the effort framing — never in child-facing
  surfaces, never as a percentage in persistent chrome.

## Preferred phrases (reach for these)
"Let's read one story tonight." · "Tonight we practice the /sh/ sound." ·
"Stories on the shelf." · "Sessions together." · "Sounds we've practiced." ·
"They fixed it themselves." · "A five-minute win beats a fifteen-minute fight."
