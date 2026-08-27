---
type: check
domain: kb-meta
trigger: on request, or automatically at end of day if automated
frequency: weekly manual / daily automated
tools: ["Grep", "Glob", "Read"]
owner: "{{NAME}}"
status: active
tags: [check, kb-meta]
aliases: ["Run the KB health check", "run-the-kb-health-check"]
summary: Produces a green/issues verdict on KB mechanical health (broken links, stale actions, inbox pile-up).
author_type: script
---

> _Generated from `.claude/skills/run-the-kb-health-check/SKILL.md` by `SYSTEM/bin/build_claude_mirrors.py` — edit the canonical file, never this mirror. Generated: 2026-08-27_

# Skill — Run the KB health check

> **When:** on request ("run the knowledge health check") or on a schedule
> **Outcome:** a verdict (green / issues) + a list of any real problems to fix

## When to run this
- Weekly as a manual habit.
- Automatically at 6pm if you've installed the `SYSTEM/optional/automation/daily-summary.sh` job.
- Any time you suspect the KB has drifted (broken links, stale actions, inbox pile-up).

## Steps
1. **Mechanical half — run `SYSTEM/bin/lint.sh`.** Do NOT hand-re-derive its
   checks; the script is the single source of truth for what "mechanically
   sound" means (inbox clean incl. registered exceptions, wikilinks + aliases
   resolve, index complete, frontmatter present + Pydantic-valid,
   descriptions present, no stray non-`.md` files, Quick map within the
   SessionStart injection budget). Exit 0 = mechanical green; on failure the
   script names each offender.
2. **Judgment half — the checks a script can't run:**
   - **Stale facts:** any always-loaded claim (index one-liners, `CLAUDE.md`)
     contradicted by a fresher note? (Deep version: [[Audit State Freshness]].)
   - **Resolved open questions:** any note's Open questions actually answered
     elsewhere?
   - **Actions real:** spot-check open `#action`s — genuinely still open?
     Completed ones checked, not deleted? (`SYSTEM/bin/aging-actions.sh`
     lists the old ones.)
   - **Initiatives current:** `SYSTEM/bin/stale-initiatives.sh` — any active
     note weeks-stale, or done-in-substance but not archived?
   - **Raw provenance (spot-check):** a concept with zero `[[Knowledge/raw/…]]`
     cites is a soft warning, not a hard failure.
   - **Generated sections alive:** stamps within cadence AND the generating
     jobs' logs clean — a fresh stamp can hide a failing generator.
3. **Report.** State: `green — <one clause>` or `issues — <sub-bullet per real
   problem>`. Log a one-line entry in `SYSTEM/log.md`.

## Gotchas / rules
- **Never hand-copy lint's rule lists into this note** — copied rules drift
  stale the moment the script evolves. Reference the script; let it carry the
  details.
- `daily/` notes are ephemeral working notes; judgment checks skip them.
- A missing `Knowledge/raw/` citation is a soft warning, not a hard failure.
- If a *judgment* finding recurs, consider promoting it to a mechanical
  `lint.sh` check — that's the [[Audit the KB System]] feedback rule.

## Done when
- [ ] `lint.sh` run and its verdict recorded.
- [ ] Judgment layer done: stale facts, open questions, actions, initiatives,
      generated-section logs.
- [ ] Verdict reported: `green` or `issues — <list>`.
- [ ] One-line entry appended to `SYSTEM/log.md` with the verdict.

## Related
[[karpathy-method]] · [[SCHEMA]] · [[Capture a meeting or conversation into the KB]]
