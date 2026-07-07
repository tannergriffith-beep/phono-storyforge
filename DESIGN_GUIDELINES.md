# Design Guidelines — Start Here (for humans and AI agents)

This repository is a **design-neutral implementation repository**. The product strategy,
functionality, architecture, and engineering are intact and active. The previous visual
identity has been separated from the active project so that a redesign can begin from first
principles rather than inheriting prior aesthetic decisions.

If you are about to design, theme, brand, or restyle this product, read this first.

---

## Where each kind of truth lives

| You need… | Authoritative source | Notes |
|---|---|---|
| **Customer, product, business, goals, constraints** | `archive/rebrand-engagement/design-context/` | Start with `design-context/design-brief.md`, then `01`–`08`. Deliberately contains **no** prior visual identity. This is the starting point for the redesign. |
| **What the product does (functionality)** | The application code (`app/`, `eval/`, `scripts/`) and `README.md` | The code is the source of truth for behavior, workflows, and architecture — independent of how it looks. |
| **Accessibility requirements** | `archive/rebrand-engagement/design-context/07-design-constraints.md` | Functional, non-negotiable: legibility, read-aloud/audio support, no shame-inducing feedback, progress by effort not accuracy, low cognitive load. Validate against WCAG. These are requirements, not aesthetics — honor them in any design. |
| **The previous visual identity (reference only)** | `archive/legacy-design/` | Historical. **Do not use as a design input.** See its `ARCHIVE.md`. |

---

## Ground rules for redesign work

1. **Begin from product strategy, not previous visuals.** Design from `archive/rebrand-engagement/design-context/`.
   Do not open `archive/legacy-design/` to "see what we had" — that re-anchors the new
   identity to the old one and defeats the reboot.

2. **The code is functional truth, not aesthetic truth.** The app must build and run
   throughout the reboot, so some visual-identity values necessarily still live in active
   code. Treat these as *what the current implementation happens to do*, not as decisions
   to preserve:
   - `app/brand.py` — the current illustration palette + style descriptors (the reboot
     replaces these *values*; the module and its API stay).
   - `app/web/static/style.css` — the live UI's stylesheet (the densest visual surface).
   - `app/web/static/index.html`, `render.js`, `components/*.js` — UI structure/behavior;
     class names and structure encode the *current* design language.
   - `app/doc_export.py` — document typography/formatting for the exported storybook.
   - `app/skills/palette_verifier.py` — a guardrail that enforces *whatever* palette
     `brand.py` defines (the mechanism stays; the enforced palette is yours to redefine).
   - `results/sample_book/*.png` — rendered storybook pages kept as capstone *evidence*.
     **Their look is the legacy identity**, not a target; the pipeline regenerates them
     from new brand values.

3. **Preserve accessibility-motivated choices even when they look like styling.** Example:
   the reading surface uses a dyslexia-friendly typeface — that is an *accessibility*
   decision, not arbitrary branding. Re-derive such choices from the accessibility
   requirements, don't discard them as "old style."

4. **Document new design decisions in the new design system after approval.** Once the
   consultancy/agency converges on an identity, capture it as the new design system (a new
   doc and/or token set). Do not reintroduce material from `archive/legacy-design/`.

5. **Keep functionality and visual identity decoupled going forward.** When you add UI,
   express identity through tokens/variables (e.g. CSS custom properties, the `brand.py`
   palette dict) rather than hard-coding aesthetic values throughout, so the next reboot is
   cheaper.

---

## For AI agents specifically

- Your design starting context is `archive/rebrand-engagement/design-context/` + this file. Do **not** read
  `archive/legacy-design/**` as inspiration or precedent.
- When a task touches both function and look (e.g. "restyle the reading view"), preserve the
  behavior the code already implements and the accessibility constraints; change only the
  visual layer.
- If you are unsure whether something is product strategy or visual implementation, treat
  the **strategy** as authoritative and the **visual implementation** as replaceable.
- See `archive/rebrand-engagement/repository-design-audit.md` for the full inventory of
  where visual identity lives and how each item was dispositioned.
