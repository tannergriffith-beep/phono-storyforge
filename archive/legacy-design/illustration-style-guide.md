# Illustration Style Guide — Agent 5 (Illustration Prompt Agent)

Source of truth for the artistic style baked into every `image_prompt` the
Illustration Prompt Agent generates. Derived from Phono's documented brand
illustration direction (`Brand Guide — Locked Decisions.md`, Illustration
Direction section) plus an age-banding rule added during plan review
(2026-06-22) to avoid producing books that read as "for younger kids" when
the target reader is an older struggling reader.

Do not replace this with a generic AI-art style description (e.g. "cute
watercolor, simple cartoon, highly engaging"). That phrasing was a
placeholder from the original capstone brief, not a brand-derived choice,
and it conflicts with the rules below.

## Base style (apply to every page, every age)

> Warm, loose, hand-illustrated style — not stock-perfect, not generic clip
> art. Flat color fills only, no gradients, 2px stroke weight. Real,
> expressive faces — not generic smiley faces. Home and everyday settings
> (kitchen table, living room, backyard) — not classrooms. Consistent
> character appearance across every page.

**Color palette — restrict to these six brand colors only, no new colors
introduced inside illustrations:**

| Name | Hex |
|---|---|
| Deep Navy | `#192255` |
| Japonica | `#DB7E65` |
| Warm Gold | `#EBBA7A` |
| Strikemaster | `#9C6D8B` |
| Pearl Bush | `#ECE5DB` |
| Tundora | `#483E45` |

## Age-band modifier — select based on `phonics_profile.age`

Append exactly one of these to the base style, chosen by the child's age:

- **Ages 5–7 (K–2):** "Rounder shapes, simpler scenes, larger character
  proportions, gentle and playful energy."
- **Ages 8–10 (Grades 3–5):** "Fuller scene detail, age-proportionate
  characters (not toddler-round), adventure/narrative energy."
- **Ages 11–13 (Grades 6–8):** "Graphic-novel/editorial illustration energy,
  more realistic proportions, dynamic compositions. Deliberately avoid
  anything that reads as an 'early reader' picture-book look."

## Why this matters (for whoever maintains this agent)

Phono's brand explicitly rejects gamification elements (streaks, confetti)
because visual cues that feel babyish or performance-anxious backfire when
a kid's relationship with reading is already loaded with shame. A fixed
"cute cartoon" style applied uniformly regardless of age has the same
failure mode for an 11–13 year old: it reads as a book for a much younger
child, which is exactly what an older struggling reader doesn't want handed
to them. The age-band modifier exists to prevent that, not just to vary
visual flavor.

## Full brand context

This is a condensed, code-relevant excerpt. The full brand voice, archetype,
and trust-hierarchy docs live in the Phono Obsidian vault under
`Dyslexia Toolkit Vault/Business/` (Brand Guide — Locked Decisions, Phono
Brand Identity, Phono - Brand Foundation) if deeper context is ever needed.
