---
type: concept
description: First-principles thinking and the DARE framework (Decompose, Audit, Recombine, Experiment) — reasoning from essentials instead of inherited assumptions, with AIM-structured prompts that force an AI off the conventional-wisdom average.
updated: 2026-09-28
status: current
tags: [concept, thinking, ai]
---

# First-principles thinking (and the DARE framework)

Reasoning from what is actually true and testable instead of by analogy to
inherited conventions. The core move: instead of accepting the story you (or
your industry, family, colleagues) already tell, ask — *What do I know for
sure? What am I assuming? What else could produce this result? Which part can
I test?*

**Why it matters now:** LLMs are pattern-matchers — the most *familiar* answer
surfaces as the "best" one, so unguided AI drags your thinking toward the
average, and the better it sounds, the less you check. First principles is the
counterweight: force the model off the conventional path, make it show its
work, and keep the judgment yourself.

## The DARE framework

Popularized by Sandeep Swadia. Each step gets an **AIM**-structured prompt —
**A**ctor (the role the model plays) · **I**ntention (context + constraints) ·
**M**ission (what done looks like).

1. **D — Decompose.** Break the problem into its smallest useful parts and show
   the hierarchy. Forbid advice, solutions, and reframing; if a deeper hidden
   question exists, name it and ask before proceeding. Stop when going deeper
   stops improving understanding.
2. **A — Audit assumptions.** For each part: fact, or an assumption that merely
   survived? Actor = a skeptical red-team analyst; every obvious part is presumed
   to hide a convention until evidence proves otherwise.
3. **R — Recombine.** Rebuild from the surviving pieces. Innovation is rarely a
   new building block — it is a new combination of the ones you have. Ask for
   several rebuilds that differ in *structure*, not detail.
4. **E — Experiment.** Design the cheapest, fastest real-world test before the
   idea costs anything real. For each test state what result kills the solution,
   what keeps it alive, and what is learned either way.

**Operating rule with AI:** every prompt forces the machine to show its work; the
AI does the work, the human keeps the decision. Failure calibration: the goal is
not to be right every time but to learn quickly why you were wrong.

## How this KB implements it

Integrated as **ambient stance + decision gates** — running DARE against
"every interaction" turned out to be itself an inherited assumption: the
*stance* is always on and cheap, the *process* binds to decision moments, and the
*artifacts* (recorded assumptions) are what a KB can do that a stateless chat
cannot.

- **Stance** — `AGENTS.md` § Conventions: in advisory answers, label load-bearing
  claims **fact / convention / unknown** and flag conventional wisdom.
- **Process** — [[Run a DARE Pass]] (`/dare`): the four-step chain as a runbook,
  used at project opens, purchases, rulings, and strategy refreshes.
- **Artifacts** — an optional `## Assumptions` section in a project note
  (numbered, most load-bearing first, labels inline), with the chosen experiments
  written as `#action` lines. A `fact` label cites its source (a `raw/` capture or
  ledger line) or it is an `unknown`.
- **Kill lines** — if `/dare` never flips a real decision, or the stance labels
  never appear unprompted, remove the machinery rather than accumulate dead rules.

## Source

- Sandeep Swadia — video *If You Don't Understand First Principles, You Can't Think
  Clearly*, and the free prompt pack at https://sandeepswadia.com/first-principles-prompts
  (his caveat: this is one way to prompt, not the only way — make the prompts your own).

## Related

- [[karpathy-method]] — this KB's compile-from-raw discipline is a cousin: distill to durable essentials, don't accumulate analogy.
- [[gtd]] — the DARE pass most often fires at a project open or an area review.
