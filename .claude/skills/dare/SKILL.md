---
name: dare
description: Run the four-step DARE first-principles chain (Decompose, Audit assumptions, Recombine, Experiment) against a named problem or decision, writing the audit into the owning note. Use at decision moments — initiative open, big purchase, pending ruling, strategy refresh — or when {{NAME}} says "dare", "/dare", or "first-principles this".
metadata:
  title: Run a DARE Pass
  type: do
  domain: thinking
  trigger: "a decision moment (initiative open, purchase, ruling, strategy) or {{NAME}} says 'dare' / '/dare' / 'first-principles this'"
  frequency: ad-hoc
  tools: "Read, Grep, Edit, Write"
  owner: "{{NAME}}"
  status: active
  version: "1.0"
  tags: [do, thinking]
  aliases: [Run a DARE Pass, dare, DARE pass, First principles pass, run-a-dare-pass]
  summary: The four-prompt DARE chain as a KB runbook — decompose, audit fact/convention/unknown, recombine 3 structures, design kill-line experiments; audit lands in the owning note.
  updated: 2026-09-28
---


# Skill — Run a DARE Pass

> **When:** a real decision moment, or on request · **Frequency:** ad-hoc ·
> **Outcome:** the problem decomposed, its assumptions labeled **fact / convention / unknown** with KB evidence, ≥3 structurally different rebuilds, and the cheapest kill-line test for each — recorded in the owning note, not just the chat.

## When to run this

Decision-shaped moments only: opening an initiative, a significant purchase, a
ruling {{NAME}} owes, a strategy-artifact refresh, or an explicit "/dare". Never
on mechanical ops (captures, lint, triage) — there it's noise.

## Steps

1. **Name the problem and its owning note.** One sentence, {{NAME}}'s words. The
   owner is the initiative/concept note the decision lives in; if none
   exists, a dated `Knowledge/raw/` capture will hold the record.
2. **D — Decompose (decomposition only).** Break the problem into its smallest
   useful parts and show the hierarchy (problem → components → elements), each
   with what it contains and how it connects. No advice, no solutions, no
   reframing. **If a deeper or hidden question appears, name it in one sentence
   and ask {{NAME}} which to decompose — do not continue until they choose.** Stop
   when going deeper stops improving understanding.
3. **A — Audit.** For each block, on its own line: name the assumption; label
   it **fact / convention / unknown** — *with KB evidence*: a `fact` label
   cites its source (raw capture, ledger line, verified data), or it's an
   `unknown`; state what breaks or opens if eliminated, and what changes if
   **inverted**; order most load-bearing first.
4. **R — Recombine.** From the blocks that survived, produce **3 solutions
   that differ in underlying structure, not detail**. Each names: the blocks
   it's built from, the discarded convention it refuses to obey, and its
   single biggest point of failure. Any new block is labeled a new assumption.
5. **E — Experiment.** For each surviving solution, the smallest concrete
   real-world test (least time/money/effort/social risk): what result rules it
   out, what keeps it alive, what's learned either way — and which block to
   revisit if all tests fail. Kill lines are mandatory; a test nothing can
   fail is not a test.
6. **Record.** Initiative owner → write/refresh its `## Assumptions` section
   (numbered, most load-bearing first, labels inline) and drop the chosen
   experiments as `#action` lines; non-initiative owner → the audit goes in the
   note or a raw capture. Rulings follow the `SYSTEM/decisions.md` trigger rules
   ({{NAME}}'s explicit word only). One line in `SYSTEM/log.md`.

## Gotchas / rules

- **{{NAME}} stays in the loop at the D→A and R→E boundaries** — the deeper-
  question choice and the pick of which solutions to test are theirs, not the
  model's.
- **Classification, not defiance.** A convention that is cheap and correct
  survives its audit; the failure mode is performative rule-breaking.
- **KB evidence beats model memory.** This chain's edge over a stateless
  prompt-pack is that fact labels resolve against the vault — grep before you
  label.

## Done when

- [ ] Hierarchy shown; deeper-question check done ({{NAME}} chose if one surfaced)
- [ ] Every block labeled fact/convention/unknown with evidence, ordered by load
- [ ] 3 structurally different rebuilds, each with blocks + refused convention + failure point
- [ ] Kill-line experiments recorded as actions; `## Assumptions` / owning note updated; log line appended

## Related

[[Run an Initiative]] · [[SCHEMA]] (decisions-ledger trigger rules).
