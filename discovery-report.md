# Phono — Discovery Report (Phase 1)

*Prepared by the product design consultancy. This document captures understanding only — no visual identity decisions are made here. It establishes the foundation for inspiration research (Phase 2) and identity exploration (Phase 3).*

*Sources: the `design-context/` brief (authoritative for customer, vision, business, constraints) and a functional reading of the application source (authoritative for workflows, features, architecture). No prior or archived visual material was consulted, per the rebrand ground rules.*

---

## 0. A finding that frames everything: two "products" wearing one name

The two sources of truth do not describe the same thing, and the gap is the most important strategic fact in this report.

- **`design-context/` describes *Phono the company*** and its current commercial product: **printable, parent-led structured-literacy toolkits** (Foundation / Fluency / Independence / Summer). Software — a parent chatbot, an interactive session app, an AI tutoring agent, a specialist directory — is explicitly framed as *future roadmap (Phases 3–5)*.
- **The application is *Phono StoryForge*** — a fully working **closed-loop adaptive reading tutor**: it keeps a per-child phonics-mastery model, decides the next skill to teach from that child's own reading evidence, generates a book guaranteed decodable at exactly that level, listens to the child read it aloud, attributes every miscue to a specific grapheme, updates the model, and changes the next book accordingly.

In other words, **the application is the realized version of Phono's future roadmap**, not the toolkit business of today. An identity built here must serve the company mission (the source of trust and meaning) while being expressed through the software product (the actual surface being designed).

> ### ✅ Scope decisions (locked with stakeholder, Phase 1)
> - **Surface:** Design the **software app first**, but architect the identity/design system so it **extends cleanly to the full system** (marketing web + printable toolkits + future specialist directory). App is the proving ground; the system is built to scale to all surfaces.
> - **Name architecture:** **Phono is the parent brand over a family of distinctly-named products.**
>   - **Phono** — the company and meaning anchor (mission, trust, the "gap" story). Lends credibility to everything beneath it.
>   - **StoryForge** — *one specific product*: the adaptive story-building & reading **app** (the Google/Kaggle capstone). It is **not** a generic engine name for the whole system.
>   - **Toolkits** — separate products with **their own names**: *Foundation, Fluency, Independence, Summer* (printable, grade-banded). Not "Phono Fluency" — they stand as named members of the family.
>   - So the system is a **branded family**: Phono (parent) → { StoryForge (app), Foundation / Fluency / Independence / Summer (toolkits), + future specialist directory }. The identity must let Phono unify a credibility signature across products while each product holds a distinct name and personality. **This engagement designs the app (StoryForge) first, with the Phono parent system built to extend to the toolkits and beyond.**

---

## 1. Product summary

**Phono** stands "in the gap between struggling families and trained specialists." Roughly 1 in 5 children has dyslexia; most aren't identified until ~3rd grade; formal evaluation means 9–14 month waitlists and ~$2,000, and specialist tutoring runs $75–$100/session. The research window that matters most closes around age 8. So a parent who knows *tonight* that something is wrong is told to "wait and see" — and waiting has a real, unrecoverable cost.

Phono closes that gap by giving the parent **the same evidence-based, structured-literacy method a specialist would use**, translated into short, doable, shame-free home sessions — while honestly pointing them toward a real specialist as the better long-term outcome.

**The application (StoryForge)** is the adaptive engine that makes this real in software. Functionally, per child, per session:

1. **Plan** — pick the lowest unmastered phonics skill (the child's frontier / ZPD) from a Bayesian mastery estimate, plus a couple of spaced-review skills.
2. **Generate** — produce a short decodable story guaranteed to use only sounds the child has mastered, plus today's target; optionally illustrated and exported as a take-home Google Doc.
3. **Read** — the child reads aloud (voice via mic, or typed transcript).
4. **Assess** — align expected vs. spoken text, classify each miscue (substitution / omission / insertion / self-correction), and attribute errors down to the exact grapheme.
5. **Adapt** — update the per-grapheme knowledge state; the *next* book changes because of how *this* read went.
6. **Persist** — the learner profile and an append-only session log accumulate as longitudinal proof of growth.

The loop's brain is **deterministic, testable Python**; the LLM only *proposes* stories and *never decides what to teach* — a deterministic verifier guarantees decodability before anything reaches the child. **The loop, not one-shot generation, is the product.**

---

## 2. Customer understanding

Three audiences, two of whom must be served by the *same* surface — the central design tension.

**The buyer (primary) — the "Waiting-Room Parent."** A parent, usually a mother (~32–45), of a K–8 child who is dyslexic or visibly struggling. She is **scared, guilt-ridden, afraid of making it worse**, and afraid the child is absorbing shame ("I'm the dumb kid"). She's been told to "wait and see," may be on a waitlist, and can't easily afford per-session tutoring. She wants to act tonight but **doesn't feel qualified and is terrified of doing it wrong**. What she needs from the product: *confidence, credibility, reassurance, low time cost, and the sense that she is no longer guessing or alone.*

**The end user — the struggling child (K–8).** Often bright, verbal, creative — but a slow, effortful reader who carries **frustration, avoidance, and shame**. Needs short (≤5-min) multisensory tasks, immediate gentle feedback, instructional-level (not frustration-level) text, no guessing from pictures, and **frequent genuine wins**. Must *never* be signaled "wrong," "behind," or "failing."

**The influencer — educators** (teachers, reading specialists, SLPs aligned with the science of reading). Not buyers; they lend credibility and may share materials. They need claims that are demonstrably evidence-aligned and non-gimmicky enough to endorse.

**The defining design tension:** every experience must let an *untrained, anxious adult deliver it correctly* **and** be *engaging and shame-free for a struggling child* — often within the same screen, the same minute. The application already encodes this insight as a product pattern (see §3, "the two-faced surface").

**Jobs-to-be-done:** (1) bridge awareness → specialist help with something effective to do tonight; (2) validate what the parent is seeing and teach self-assessment; (3) make the science deliverable without training; (4) prevent summer regression; (5) protect the child's self-esteem.

---

## 3. How the application actually works (functional map)

A grounded inventory of what exists, so later phases design for the real surface area — not an imagined one.

**Surfaces / screens (current web demo):**
- **Setup / empty state** — learner identity (id, name, age, interest) → one "Begin" action.
- **Session — Reading face** (child-safe): the book title and the text to read; a read-aloud (mic) action with a quiet typed fallback; a celebration after scoring. **By design it shows no errors and no data to the child.**
- **Session — Insight face** (adult): a "Why this book?" rationale; a word-by-word running-record heatmap; fluency stats (accuracy, words-correct-per-minute); a "mastery path" of skills; an animated "adapt" moment showing the target advancing; the next-session target.
- **Journey** — longitudinal history: per-session targets, newly mastered skills, and a rising mean-mastery trend line (the proof of learning over time).
- **Take-home illustrated book** (optional, creds-gated): generates an illustrated, decodable story exported to a shareable Google Doc.
- **Persistent chrome:** a top bar with a mean-mastery meter; a six-node "loop rail" that lights up step-by-step; a dismissible "degrade banner" for graceful failures.

**The two-faced surface is the product's best idea.** A single session has a **Reading face** (calm, success-only, for the child) and an **Insight face** (instrumented, analytical, for the adult), with a deliberate **privacy boundary**: after scoring, the view *stays* on Reading so the child never automatically sees red marks; the adult must choose to cross over. This is the buyer↔user tension solved in interaction design. **Any new identity must protect and elevate this pattern.**

**Architecture worth knowing for design:**
- The whole thing runs over one WebSocket; state is `prepare → read → outcome`.
- Progress is modeled as **probabilistic mastery per grapheme** (BKT), surfaced as a percentage/meter and a "mastered/current/locked" path.
- Everything **degrades gracefully on independent axes** — voice can fail, illustration can fail, export can fail, and the core read loop survives each. (The identity should make degraded states feel calm and intentional, not broken.)
- Persistence is local JSON; this is pre-launch demo infrastructure, not a hosted account system yet.

**A candid observation:** much of the current UI is narrated for a *hackathon-judge / stakeholder* audience (the loop rail "narrates the architecture in real time"; the language is "mastery," "objective," "grapheme," "ZPD," "adapt climax"). That is a **demo artifact**, not a scared-parent product. The underlying capability is excellent; the *framing* currently serves engineers proving the loop works, not a frightened parent at the kitchen table. This is the single biggest opportunity (see §6, §10).

---

## 4. Strengths

1. **A genuine moat built on honesty.** "Specialist-first" — openly telling parents a trained specialist is the best outcome and helping them find one — is counter-intuitive and rare in edtech. It is the strongest possible trust signal, and it's defensible precisely because competitors won't copy something that looks like it costs a sale.
2. **Real evidence rigor.** Structured literacy, Orton-Gillingham sequencing, IDA standards, BKT mastery modeling, deterministic decodability verification. The substance is real; the brand gets to *reflect* credibility rather than manufacture it.
3. **The adaptive loop is differentiated and demonstrable.** "It changes the next book because of how this read went" is a concrete, screenshot-able proof most reading apps can't make. The Journey trend line is emotional evidence ("my child is actually getting better").
4. **The buyer↔user tension is already solved in product form** (the two-faced Reading/Insight surface + privacy boundary). Few products this early have this clarity.
5. **Founder–customer fit.** Built by a parent of dyslexic children. "Parent, not professor" is authentic, not positioning.
6. **Speed-to-value is real.** "Start tonight" isn't a slogan — a session is one doable action in ≤20 minutes with household materials.

---

## 5. Weaknesses

1. **Engineer-facing framing.** The current product talks like its own architecture diagram. A terrified parent meets "mastery," "objective," "grapheme," "adapt climax," and a "loop rail" before she meets reassurance. The emotional on-ramp the brief demands ("you found the right place") is largely absent from the built surface.
2. **The progress model risks contradicting the principle.** The product is emphatic that progress must be framed by **effort and consistency, not accuracy or comparison** — yet the Insight face leads with accuracy %, WCPM, and percentage "mastery meters." That's appropriate *for the adult, in the optional layer*, but the line is thin and currently blurred. Easy to drift into the exact shame mechanics the brief forbids.
3. **No coherent name/identity architecture.** "Phono" (mission/company) vs. "StoryForge" (engine) vs. "toolkits" (commercial product) are not yet one story.
4. **Two-product confusion.** Marketing/business context is about *printables sold by email funnel*; the application is *adaptive software*. A parent arriving from a social post about a printable kit would not recognize this app, and vice versa.
5. **Pre-launch fragility of assumptions.** Personas are explicitly hypotheses; the feedback log is empty; pricing is unresolved; there is no validated acquisition or conversion data. We are designing on a well-reasoned but unvalidated model.
6. **Accessibility is asserted, not yet specified.** It's named as core, but there is no stated conformance target, no defined read-aloud feature contract, and no print spec — all of which a real accessible identity must pin down.
7. **Operability risk.** The business is solo, lean, and AI-assisted by design. A design system that needs a studio to maintain will rot. Whatever we build must be operable by one non-designer with strong defaults.

---

## 6. Opportunities

1. **Re-center the surface on the parent's emotional journey, keep the rigor as a calm second layer.** Lead with reassurance and a single doable next action; let the analytical "insight" deepen on demand. The capability already supports this (the two faces) — it's a framing and hierarchy opportunity, not a rebuild.
2. **Make honesty visible as a brand behavior.** A product that will tell you the truth even when it's inconvenient ("this looks like a moment to see a specialist — here's how") is profoundly memorable. The specialist-first promise can be *designed*, not just stated.
3. **Turn "showing its work" into trust, not jargon.** "Why this book?" is a gift to an anxious parent — *if* it's said in plain language ("Tonight we practice the /sh/ sound, the next one your child is ready for"). The reasoning is the reassurance.
4. **Own a distinctive emotional register the category has abandoned** (see §7): warm + credible, neither clinical-corporate nor candy-gamified. There is open whitespace for something that feels like a *trusted independent children's bookshop crossed with a thoughtful pediatric practice.*
5. **Design progress as effort made beautiful.** Sessions completed, minutes invested, stories read, wins logged, a gently rising line — celebration without comparison. This is both a principle *and* a differentiator from streak/leaderboard apps.
6. **One identity that survives print, grayscale, web, and a future app**, across four grade-banded products and a future specialist directory — designed once, scaled cleanly.

---

## 7. Competitive landscape

| Alternative | What it offers | Where it falls short | What Phono can own |
|---|---|---|---|
| **Specialist tutors** ($75–100/session) | The gold standard | Expensive, waitlisted, inaccessible tonight | The honest *bridge* to them — not a rival |
| **Commercial OG / structured-literacy programs** | Comprehensive, rigorous | Costly, complex, jargon-heavy, long sessions; often visually clinical/institutional | Same rigor, radically lower friction and warmth |
| **Generic reading / gamified apps** | Accessible, fun, cheap | Not dyslexia-specific or evidence-aligned; rely on streaks, stars, leaderboards — the *exact* comparison/accuracy mechanics that shame struggling readers | Evidence-true *and* shame-free; calm instead of loud |
| **School intervention** | Free, in-system | Slow to start, inconsistent, "wait and see" | Something effective to do *tonight* |
| **Doing nothing / waiting** | The default | Loses the window that matters most | The end of "wait and see" |

**Aesthetic whitespace (functional read, not a visual decision):** the category splits into two tired poles — **clinical-institutional edtech** (sterile, corporate, cold; scares the anxious parent) and **candy-gamified kid apps** (loud cartoon mascots, confetti, points; parents distrust them as toys and they re-introduce shame through scores). Phono's positioning points to neither. The opportunity is a register that reads as **trustworthy, warm, handcrafted, and calm** — credible to an educator, reassuring to a parent, and safe for a child — which almost no competitor occupies.

---

## 8. Emotional goals

**For the parent — across one session:** *relief* (you found the right place; you're not alone) → *competence* (you can do this correctly without training) → *trust* (this tool tells me the truth) → *quiet hope* (I can see it working). The opposite feelings to design against: alarm, guilt, being sold to, being talked down to, being overwhelmed.

**For the child — across one session:** *safety* (nothing here will tell me I'm bad at this) → *capability* (I can do this) → *delight* (this is a story, not a test) → *pride* (I did it). Design against: pressure, comparison, the feeling of being measured.

**For the educator (glance test):** *that's legitimate* — within seconds, the work reads as evidence-aligned and non-gimmicky.

**The brand's signature emotional move:** holding **urgency and calm at the same time** — "this matters and the clock is real" *without* alarmism. And holding **rigor and warmth at the same time** — credible without being cold.

---

## 9. Product personality

A working hypothesis (to be sharpened in Phase 3), grounded in the principles, not yet in any visual choice:

- **The knowledgeable neighbor, not the professor.** Credible *because* she's a parent who did the homework, not because of a credential on the wall.
- **Steady and calm under fear.** The presence of a good pediatric specialist: unhurried, plain-spoken, never alarmist, never patronizing.
- **Honest to a fault.** Will tell you the inconvenient truth — that's the whole brand.
- **Warm but not soft.** Encouraging without false cheer; no miracle claims, no "dyslexia is a superpower" oversell.
- **Quietly confident.** The rigor is felt, not shouted. Lets the evidence and the rising line speak.
- **Handcrafted, not mass-produced.** Feels made by a person who cares, for one family at a time.

Two voices, one personality: **plain, warm, specific language for the adult**; **gentle, success-first, story-led tone for the child.**

---

## 10. What absolutely should NOT change

These are load-bearing. Any identity that weakens one of them has failed, regardless of how good it looks.

1. **Specialist-first honesty and the whole trust hierarchy.** The bridge-not-replacement promise is the moat. Never design anything that over-promises outcomes or undercuts it.
2. **Evidence credibility and standards alignment.** Structured literacy / Orton-Gillingham / IDA. The identity must *reinforce*, never dilute or "cute-ify," the rigor.
3. **Shame-free, effort-over-accuracy framing for the child.** No accuracy percentages, comparisons, leaderboards, streaks-as-pressure, or "wrong/failing" states in child-facing surfaces. Progress = consistency, effort, time, wins.
4. **The buyer↔user dual surface and its privacy boundary.** The Reading face (calm, success-only, child) vs. the Insight face (analytical, adult), with the child never auto-shown errors. Protect and elevate this; do not collapse it.
5. **"Start tonight" / low-friction, no-training-required.** One doable action this evening, deliverable by an untrained adult, with household materials.
6. **"Show your work" as reassurance.** Keep the "Why this book?" reasoning and the Journey growth proof — they are trust, not decoration. (Translate the *language*, keep the *substance*.)
7. **Accessibility as a ground-up requirement.** Maximally legible/decodable child reading content, read-aloud support, low cognitive load, low time-pressure (count-up, not down), graceful (calm) degradation.
8. **The "Phono" mission and name as the anchor of meaning.** (The *sub-brand* and visual system are open; the mission and the company's reason for existing are not.)

## 11. What absolutely SHOULD change

1. **Everything visual.** The entire visual identity is to be designed fresh — the explicit mandate of this engagement.
2. **The engineer/stakeholder framing of the product surface.** Re-center on the parent's emotional journey. The "loop rail narrating the architecture," "adapt climax," and demo-grade self-narration are artifacts of a hackathon judging context, not a parent product.
3. **The technical vocabulary in parent/child-facing surfaces.** "Mastery," "objective," "grapheme," "ZPD," "BKT," "decodability," "loop" → translated to plain, warm language. Keep precise terms only in an optional, clearly-adult "insight/details" layer or internal tooling.
4. **The first 30 seconds.** Replace a data-and-controls entry with reassurance and one obvious action ("you found the right place" → "let's read one story tonight").
5. **The progress presentation.** Lead with effort/consistency/wins and a gentle growth line; demote accuracy %/WCPM into the optional adult layer where they can't read as a report card.
6. **Name/identity architecture.** Resolve Phono (mission) ↔ StoryForge (engine) ↔ toolkits (commercial line) into one coherent system. (Decision needed — see closing.)
7. **The one-product story.** Bridge the "printable toolkit business" and the "adaptive software" into a single, legible product narrative for the parent.
8. **Failure/empty/loading states.** Make degraded and empty states feel calm, intentional, and reassuring rather than like errors.

---

## 12. Assumptions I am making (flagging for validation)

1. **The identity's primary surface is the StoryForge software application** (the interactive session app / AI-tutor experience), expressed under the Phono mission — *not* primarily the printable toolkit PDFs. **✅ Confirmed (§0): app first, system built to extend to web + print + directory.**
2. Personas are **well-reasoned hypotheses, not validated data** (pre-launch, empty feedback log). The model is sound enough to design from, but we should design to be *correctable* once real parents are observed.
3. **WCAG 2.1 AA** is the working accessibility target until told otherwise (none is stated in the brief).
4. **English / US-first**, with no choices that foreclose later internationalization.
5. The **specialist-first, honest** positioning is permanent and central.
6. The design system must be **operable by a solo, non-designer, AI-assisted founder** — strong defaults, low maintenance burden.

## 13. Unanswered questions (to resolve before/at Phase 2–3)

- ~~**Brand scope & name architecture**~~ — **✅ Resolved:** Phono = parent brand over a branded *family* — StoryForge (the app), and separately-named toolkits (Foundation / Fluency / Independence / Summer). StoryForge is one product, not an engine name.
- ~~**Surface scope of this engagement**~~ — **✅ Resolved:** app first; design system built to extend to web + print + specialist directory.
- **Accessibility conformance target** — confirm AA (or higher)?
- **Read-aloud / audio:** is in-product TTS a committed feature, or do we rely on third-party audiobooks? (Affects the identity's audio/voice and iconography of "listen.")
- **Pricing & commerce surfaces:** unresolved pricing and one-time-vs-subscription affects any pricing/CTA design.
- **The "insight" layer audience:** how much of the analytical layer is genuinely parent-facing vs. internal/educator/demo? (Affects how far we translate vs. preserve technical language.)
- **Print medium reality:** color vs. grayscale home printing, paper size, page budgets — undocumented and needed if printables are in scope.

---

## 14. Self-critique (per the process)

**What an experienced Creative Director would challenge:**
- *"You've fallen in love with the 'two products' framing — make sure it's a real fork, not an excuse to defer the naming decision."* Fair: I've surfaced it as the lead question rather than guessing, which I believe is correct given how much it changes downstream, but I should not let it stall Phase 2 — much of the discovery (customer, emotion, competitive whitespace) holds regardless of the answer.
- *"Your 'whitespace' claim (warm + credible) is asserted from the brief, not from looking at competitors' actual screens."* True — Phase 2 inspiration research must validate it against real reference work, not assume it.
- *"Personality risks being generic-wholesome."* Watch for it; "knowledgeable neighbor / steady pediatric calm / honest to a fault" must produce *specific* visual and verbal decisions in Phase 3, or it's just adjectives.

**What a first-time user (the scared parent) would struggle with right now:**
- The current product's vocabulary and analytics-forward entry would *increase* her anxiety, not lower it. The discovery correctly prioritizes fixing the first 30 seconds.

**Assumptions most likely to be wrong:**
- That the app (not the printables) is the primary surface (#12.1) — hence I'm asking, not assuming.
- That the persona is accurate — it's unvalidated; the identity should be emotionally robust to a somewhat different real parent.

---

## 15. Structural / IA & workflow recommendations (not just visual)

The existing organization was built to *prove a closed loop to judges*, not to *guide a frightened parent*. Treating it as correct simply because it's implemented would be a mistake. Candidate structural changes to carry forward (to be validated in Phases 5–6):

1. **Invert the information hierarchy of a session.** Today the session is "Reading face ↔ Insight face" as peer tabs with engineering chrome (loop rail) on top. Recommend: the **parent/child reading experience is the home**; analytics become a *progressive-disclosure* layer ("See why" / "Details") that an adult opts into — never the default surface, never co-equal chrome.

2. **Replace the architecture narration with a human session arc.** The six-node "loop rail" narrates *the system's* steps (Plan/Generate/Verify/Read/Assess/Adapt). A parent's mental model is a *human* arc: *Tonight's story → Read together → How it went → What's next.* Recommend re-mapping navigation to the parent's journey, and relegating the technical loop to an optional/educator/internal view.

3. **Add the missing on-ramp.** There is no reassurance/onboarding step — the product opens on a data form. Recommend a short, warm first-run flow ("you found the right place" → set up your child → one story tonight), as the brief's envisioned onboarding describes.

4. **Promote "Journey" from a hidden modal to a first-class, emotionally-led space.** The longitudinal growth proof is the parent's deepest motivation ("it's working"). Recommend it be a primary, always-reachable place framed around effort, consistency, wins, and a gentle rising line — not a stats table behind a button.

5. **Reframe the session-complete moment around feeling, not scoring.** The roadmap already envisions mood capture (smooth / good / tough / tired, where "tough" ≠ "bad"). Recommend the end-of-session state lead with that and the celebration, with accuracy/WCPM demoted into the opt-in adult layer.

6. **Unify the two product narratives into one IA.** If both the toolkit line and the adaptive app persist, the parent needs a single coherent map (screener → start tonight → sessions → progress → specialist path), not two disconnected products. The specialist-directory and screener (today described only in marketing flows) should have a *designed home* in the product, because they are the trust promise made tangible.

7. **Give degraded/empty/loading states a designed place in the IA**, so "voice unavailable," "first session," and "still building this skill" feel like intentional, calm parts of the journey rather than error fallbacks.

*These are recommendations to explore and pressure-test, not yet decisions. The full screen-by-screen audit happens in Phase 5 (`ui-audit.md`).*

## 16. Recommendation & gate

Discovery is complete and the model is strong enough to proceed. Before Phase 2 (Inspiration Research), I recommend we lock the **brand scope / name architecture** and the **surface scope**, because they change what references and directions are worth exploring.

**Awaiting your approval to proceed to Phase 2 — and your answers to the scope questions below.**
