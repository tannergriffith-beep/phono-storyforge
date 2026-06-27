# Legacy Design Archive

This folder holds the **previous visual identity** of Phono StoryForge, quarantined ahead
of a ground-up product identity reboot.

## What's here

| File | What it was |
|---|---|
| `DESIGN.md` | The prior design source-of-truth: locked color tokens, contrast tables, typography roles, motion specs, component inventory, and the full visual/UX rationale for the previous UI. |
| `illustration-style-guide.md` | The prior illustration aesthetic spec: cut-paper collage style, the 6-color illustration palette, stroke/fill rules, and age-band visual modifiers. |
| `styleguide.html` | A standalone "Design System" gallery page (color swatches, type specimens, component showcase). It depended on the live app's `style.css` and **will not render standalone** from here — it is kept only as a record of the prior design system. |

## Why these are archived (and not deleted)

- **Retained for historical reference.** They preserve the reasoning and decisions of the
  previous identity. Git history for each file is intact (moved, not recreated).
- **They are NOT part of the current design effort.** The product is being redesigned from
  first principles.
- **They must NOT be used as inputs for future design work.** Opening these to "see what we
  had" defeats the purpose of the reboot — it re-anchors the new identity to the old one.

## Where to start instead

> Future design work begins from **product strategy**, not previous visual implementations.

- **`design-context/`** (repo root) — the authoritative, design-neutral briefing on the
  customer, product, business, goals, and constraints. Start there.
- **`DESIGN_GUIDELINES.md`** (repo root) — onboarding for humans and AI agents on how to
  approach the redesign and where each kind of truth lives.
- The **application code** remains the authoritative source for *functionality* (what the
  product does), separate from *visual identity* (how it should look).

## A note on visual identity still living in active code

Some visual-identity values necessarily remain in **active, running code** because the app
must build and run during the reboot — most notably the palette and illustration style in
`app/brand.py`, the live stylesheet `app/web/static/style.css`, and document typography in
`app/doc_export.py`. Those files are *implementation truth* (what the current build does),
not a *design prescription* to preserve. A redesign replaces their values; it does not
treat them as the target. See `DESIGN_GUIDELINES.md`.
