---
name: audit-state-freshness
description: Audit the always-loaded surfaces for stale state-shaped claims and fix drift in place — use monthly with the optimize pass, when the index Quick map feels behind reality, or on request.
type: skill
domain: kb-meta
tools: Read, Grep, Edit
owner: {{NAME}}
status: active
tags: [skill]
aliases: [Audit state freshness, state freshness audit, second brain audit]
updated: 2026-08-11
---

# Skill — Audit state freshness

> **When:** monthly alongside [[Optimize the knowledge base]], or whenever the
> always-loaded surfaces "feel" behind reality
> **Outcome:** every state-shaped claim on the always-loaded surfaces is
> confirmed against its source or fixed in place; unresolvables become
> `#action`s in their home notes

## When to run this

This is the **judgment layer** of lint that `meta/bin/lint.sh` can't do —
adapted from Cole Medin's
[second-brain-audit](https://github.com/coleam00/skills/tree/main/.claude/skills/second-brain-audit)
skill. Core distinction: **state** (current values — replaced in place; here
`concepts/` and initiative "Now & next" sections) vs **events** (dated
occurrences — append-only; here `raw/`, logs, Decisions/Milestones). Stale
*state* on an always-loaded surface poisons every session that starts from it.

## Steps

1. **Enumerate the always-loaded surfaces** — what every session reads before
   any note: the `index.md` Quick map (if you run the SessionStart hook, it
   injects the head of this file), `CLAUDE.md`, any agent auto-memory index,
   and today's `daily/` note if you use daily notes.
2. **Extract every state-shaped claim** from those surfaces — balances,
   statuses (OPEN/DONE/ordered/pending), "next:" items, counts, dates that
   have since passed, "as of" figures. Events (dated milestones) are exempt.
3. **Verify each claim against its source**: the owning concept/initiative
   note first, then the freshest `raw/` capture or attachment. Sort into
   **confirmed / contradicted / unsupported**.
4. **Sweep frontmatter staleness**: any note whose body carries entries newer
   than its `updated:` stamp; any live initiative whose Quick-map one-liner
   predates its latest "Now & next".
5. **Fix contradictions in place**: rewrite the stale Quick-map line or claim
   (don't append a correction under it — state gets *replaced*), bump
   `updated:` on touched notes, refresh the index footer date.
6. **Escalate what can't be resolved from the vault** as an inline `#action`
   in the owning note (e.g. two credible sources disagree — that's a
   reconcile task for a human, not an edit).
7. **Report, leading with the single most damaging finding** — the one that
   would have misled the next session worst.
8. **Log** one line to `meta/log.md`; run `meta/bin/lint.sh` to confirm the
   mechanical checks are still green.

## Gotchas / rules

- The Quick map duplicates state on purpose (injection budget) — duplication
  is fine, *drift* is the bug. Every one-liner must match its source note.
- Don't "fix" a surprising number by overwriting it; if evidence conflicts,
  it's step 6 (escalate), not step 5.
- "As of YYYY-MM-DD" qualifiers make a claim an event-shaped snapshot —
  acceptable, but check whether fresher data exists.

## Done when

- [ ] Every state claim on the always-loaded surfaces is confirmed or fixed
- [ ] Unresolvables have `#action`s in their home notes
- [ ] `meta/bin/lint.sh` green, one-line entry in `meta/log.md`

## Related

[[Run the KB health check]] (mechanical sibling) · [[Optimize the knowledge base]] ·
[[karpathy-method]] (the lint stage this job deepens)
