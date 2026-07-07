# 07 — Design Constraints (Objective)

Only objective, functional constraints are listed here — accessibility, devices, platforms, performance, compliance, and localization. **No previous visual/design choices are referenced.** Where the source material expressed a constraint as a specific visual treatment, it has been re-stated here as the underlying *requirement* only.

## Accessibility (the defining constraint set)

The end user of the reading content is, by definition, a child who struggles to read. Accessibility is a core product requirement, not an enhancement.

1. **Maximally legible, easy-to-decode reading content.** Any text the child is asked to read must be highly legible and dyslexia-friendly. (This is a functional requirement; the specific visual implementation is for the agency to determine.)
2. **Read-aloud / audio support.** The methodology relies on audio-assisted reading (child follows printed text while listening). Audio/text-to-speech support is a functional need, especially for child-facing content.
3. **No shame-inducing feedback.** Error and progress states must never label the child as "wrong," "failing," or behind. Incorrect responses get gentle, non-punitive handling.
4. **Progress framed by effort, not accuracy.** Show consistency and time invested (e.g., sessions completed, minutes practiced), **not** accuracy percentages or peer comparisons.
5. **Low cognitive load and low pressure.** Short tasks, minimal simultaneous demands, and time framing that reduces pressure (e.g., counting up rather than down) rather than adding it.
6. **Strengths-positive.** Surface and celebrate small wins and non-reading strengths.
7. **Plain language for adults; decodable content for children.** The adult-facing reading level and the child-facing reading level are different and must be handled distinctly.

These should be validated against recognized accessibility standards (e.g., WCAG) during redesign; the source material does not state a specific conformance level — see `08-open-questions.md`.

## Supported devices & platforms

- **Print:** Current products are **printable documents** delivered as a downloadable bundle. They must remain usable when printed at home (standard home printer, standard paper). This is the primary delivery medium today.
- **Web:** A website is planned for marketing and automated sales; must work across desktop, tablet, and mobile browsers.
- **Mobile app:** A future interactive session app is envisioned (mobile-first, with iOS referenced). Treat mobile, touch-based use as a target for the app phase.
- **Offline use:** Printed toolkits are inherently offline. Any app should not assume constant connectivity for core session use where avoidable (not formally specified — see open questions).

## Responsiveness

- Web and app surfaces must be responsive across phone, tablet, and desktop. Parents are expected to use the product in everyday home settings, frequently on a phone.

## Performance

- No formal performance budgets are documented. Functional implication: printable assets must be lightweight enough to download and print easily; future web/app surfaces should load quickly for low-friction "start tonight" use. (Specific targets are an open question.)

## Compliance

- **Children's privacy (COPPA):** Future child-facing software (app, AI tutor) will involve users under 13 → verifiable parental consent and child-data protections are required. Data must be encrypted and secured.
- **Intellectual property:** Toolkit content is proprietary/copyrighted; not open-source. Any contributor (contractor/designer) must assign IP to the company in writing. A redesign must preserve the proprietary nature of the content.
- **Sales tax / digital goods:** Digital products are taxable in some jurisdictions; marketplace platforms handle this where used. (Operational, not a design constraint, but relevant to checkout flows.)
- **Educational standards alignment:** Content must remain aligned to recognized standards (IDA Knowledge & Practice Standards, structured literacy, Orton-Gillingham). A redesign must not dilute or misrepresent this alignment.
- **No medical/diagnostic claims:** The product helps and screens but does not diagnose or treat a medical condition; claims must stay on the right side of that line. (Legal review noted as pending.)
- **FERPA:** Would become relevant only if the business partners with schools (future).

## Localization

- **Language:** English, US-focused initially. No localization requirements are currently defined. International expansion is undecided; do not assume multi-language support is in scope, but avoid choices that would make it impossible later.

## Materials constraint (for printable products)

- Sessions are meant to use **minimal, common household materials** (paper, letter tiles, craft sticks, a timer). The product should not require special equipment.
