# Speaker Notes — for practice, not for the desk

> Read this out loud a few times in the days before recording. On recording day, put it away
> and use only the cheat sheet. Total runtime ≈ 5:00.
>
> **Voice:** the knowledgeable neighbor. Warm, plain, honest. You built this for a real kid.
> You're showing a friend, not defending a thesis.
>
> **Four things to never say:**
> 1. A specific test count. Say "the whole offline suite passes."
> 2. "The mastery bars fill." There are no bars anymore. Say "the path lights up" or "the target moves."
> 3. That the confidence repair "fires live." It doesn't. Just don't bring it up.
> 4. "Story" for the in-app reading. There are two book-shaped things in this demo, so the words
>    are split: what Ada reads in the app is always a **book** (it pays off Screen 1's "the right
>    book doesn't exist" — we generate it); **story** is reserved for the illustrated export in
>    Screen 6 — the thing StoryForge forges. Bonus: the on-screen Why card says "Why this book?",
>    which now matches you. One on-screen mismatch remains: the Session Arc is labeled "Tonight's
>    story" — don't echo it; keep saying "book."
>
> **One rule that beats all others:** silence is a feature. The demo has a two-second animation
> that is the whole point of the video. Let it play. Say nothing. Then speak.

---

## Screen 1 — Title card (~30s)

**Goal:** Make the audience feel the problem before they hear the product name.

**Key message:** Parents get advice they can't actually follow — and nothing adapts.

**Suggested wording:**

"If your child struggles to read, you get one piece of advice: decodable books, at their level."

(Pause. Let that sit — most people have heard this.)

"Two problems. The right book — your kid's phonics level, their age, their interests — basically doesn't exist on a shelf. And nothing is watching *what* they misread to decide what to practice next. There's no loop."

(Small pause. This is the thesis of the whole video.)

"Phono StoryForge closes that loop. It generates the book, listens to the read, and moves the target itself."

**Transition:** "Let me show you — running live." (Cut to the browser.)

**Duration:** ~30 seconds. If you finish early, good. Don't fill it.

---

## Screen 2 — Ada's book, reading view (~25s)

**Goal:** Establish that this is the real product, not a mockup.

**Key message:** The book on screen was built for this specific child, from her own mastery data.

**Suggested wording:**

"This is the actual product running live — the same code the experiment runs."

"Ada's book tonight is built from the sounds she's ready for. See the soft underlines? Those are her targets."

(Now do the scoring clicks. It's fine to talk while clicking:)

"She reads the page — I'll score a typical read from the keyboard, so it's repeatable on camera."

That last line is your honesty beat for the whole voice question. Say it comfortably, not apologetically. Keyboard scoring is the documented, approved path.

**Transition:** "First — what the kid sees."

**Duration:** ~25 seconds including the clicks.

---

## Screen 3 — Kid view, then grown-up view (~45s)

**Goal:** The payoff. One read produces: attribution, an update, and a moved target.

**Key message:** The child sees celebration; the adult sees evidence. Same read, two faces.

**Suggested wording:**

"First, the kid view — a clean win. No scores, no red ink."

(Give them a second to see it's genuinely gentle.)

"Now the grown-up view."

(Switch. The animation plays the moment you enter — it waits for you, so don't rush the switch. Then: SAY NOTHING for about two seconds. Let the pop and the glow land.)

(Now, calmly:)

"It didn't pick this book at random — here's why it chose this sound and this book."

"And the running record: that red cell is the exact sound she stumbled on. Not 'she got 95%' — *this grapheme*."

"And the path — the sound she just nailed lit up, and the target moved. wh to ck."

(Don't read the on-screen caption aloud. It resolves on its own; your job is to point, not narrate every pixel.)

"One read: miscue attributed, mastery updated, tomorrow's target moved."

**Transition:** "One read. Is this a loop, or a party trick? Let's read again."

**Duration:** ~45 seconds, including the two seconds of deliberate silence.

---

## Screen 4 — Second read (~35s)

**Goal:** Prove it's a loop — the target moves *twice*, live.

**Key message:** Adaptation happened twice in front of them. Nobody mocks that up.

**Suggested wording:**

"Once more, on the new book."

(Do the clicks. A little quiet here is fine — the audience knows the rhythm now.)

"And the target moves again — ck to qu. The loop adapted twice, live."

(Pause. Smile. This is the moment you earned.)

"That rail along the top — Plan, Generate, Verify, Read, Assess, Adapt — that's the ADK loop you just watched fire."

**Transition:** "Does adapting actually help, or does it just look clever? We tested it."

**Duration:** ~35 seconds including clicks.

---

## Screen 5 — Evidence chart (~90s, only ~50s of talking)

**Goal:** Show rigor. This screen is where a skeptical judge decides to trust you.

**Key message:** The result survived an experiment designed to break it.

**Suggested wording — the result:**

"Same paired, seeded simulated learners. Same fixed benchmark probe every session. Adaptive — which picks each session's target from the child's own estimate — versus a fixed scope-and-sequence that ignores the evidence."

"n of thirty, forty sessions: probe accuracy up point-oh-six. True mean mastery up point-oh-four. Almost five more words correct per minute."

(Let the chart breathe. The audience is reading it. Give them a few seconds.)

**The rigor beat — do not skip this:**

"And we didn't let it grade its own homework. The simulated learner was built deliberately *unlike* what the tutor assumes — a logistic reader with per-sound difficulty, no prerequisite gate, and it *forgets*."

"De-circularizing roughly halved the gaps. But they stayed positive — across all twelve cells of the sweep."

**The honesty beat — keep it, it reads as credible:**

"One place it's a wash: the count of sounds pushed past a hard zero-point-nine-five bar. We log that. We don't hide it."

**Transition:** "So it works. Can it also be something a kid wants to hold?"

**Duration:** ~90 seconds total; roughly 50 seconds of speech. The slack is for the chart to linger. Do not fill the slack.

---

## Screen 6 — The illustrated story (~50s, only ~30s of talking)

**Goal:** Show polish backed by the same engineering discipline.

**Key message:** One pattern, three times — the LLM proposes, deterministic code verifies.

(Here the word flips, once: Ada's nightly reads were "books"; this illustrated, exportable
thing is the **story** — it's what StoryForge forges.)

**Suggested wording:**

"And here's the story it forges — fully illustrated. Every page is guaranteed made from sounds they know. An LLM proposes the words; deterministic Python verifies."

(Let a page or two turn in silence.)

"Same discipline, three times: a decodability check that won't let an undecodable word ship. A palette verifier that proves every illustration stays on brand. And a Doc assembled deterministically."

"Three guardrails that halt instead of quietly shipping something wrong."

"And as of last week, this is folded into the live loop — not a separate path."

**Transition:** "So — what did you just watch?"

**Duration:** ~50 seconds; let the pages carry ~20 of them.

---

## Screen 7 — Close (~25s)

**Goal:** Land it in one breath.

**Key message:** One loop, wired into a real product, proven honestly.

**Suggested wording:**

"One deterministic loop — plan, generate, listen, attribute, update — wired into a real product."

"Proven by a de-circularized study. Now forging illustrated stories inside that same loop."

"The whole offline suite passes green. Built on ADK, for Agents for Good."

(Pause. Then the locked line, word for word:)

"A five-minute win beats a fifteen-minute fight — at scale."

(Hold for a beat. Done.)

**Duration:** ~25 seconds.

---

## Practice plan

1. Read this whole doc aloud twice, seated, no screen.
2. Then run it with the app, cheat sheet only, three times (the director's runbook has the setup).
3. Stopwatch the third run — word-count timing doesn't capture breath or clicks.
4. The only two things to drill until automatic: the Screen 5 numbers, and the closing line.
