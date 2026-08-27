---
type: rule
domain: kb-meta
trigger: "any file a script rewrites, any new data feed, any 'always current' requirement"
frequency: ad-hoc
tools: ["<!-- generated --> marker", "per-domain generator scripts", "launchd/cron"]
owner: "{{NAME}}"
status: active
tags: [rule, kb-meta]
aliases: [Maintain Generated Sections, maintain-generated-sections, generated-sections]
summary: The standing convention for machine-maintained file sections — config above a marker, generated content below, fail loud, never hand-edit below the line.
updated: 2026-08-14
author_type: script
---

> _Generated from `.claude/skills/maintain-generated-sections/SKILL.md` by `SYSTEM/bin/build_claude_mirrors.py` — edit the canonical file, never this mirror. Generated: 2026-08-27_

# Skill — Maintain Generated Sections

> **When:** any time a file needs to "always stay current" via a script ·
> **Outcome:** a file that is simultaneously hand-editable (config) and
> machine-fresh (data), with drift impossible by construction.

## The rule

A file that machines rewrite splits at a **`<!-- generated -->`** marker:

1. **Above the marker — human territory.** Config tables, annotations,
   header prose. Scripts preserve this region byte-for-byte; humans edit
   schedules and notes here without fear.
2. **Below the marker — machine territory.** Rewritten wholesale on every
   run, opening with a visible stamp: `_Generated: YYYY-MM-DD by <tool>_`.
   Never hand-edit below the marker; annotations go above it or in the
   owning note.

## Generator contract

- **One tool, one job** — small per-domain scripts (~100 lines, stdlib
  only), not a shared configurable engine. Copy the shape, not the code
  (`SYSTEM/optional/automation/status-gen-example.py` is a starting point).
- **Idempotent** — safe on any schedule; same inputs → same output.
- **Fail loud, never partial** — pin expected input headers/columns; on
  any mismatch exit non-zero and write nothing. A missing update is
  visible (stale stamp); a silently-wrong table is poison.
- **Stamp = health check** — a stamp older than the job's cadence means
  the job missed. Readers say so instead of trusting or guessing.
- **Chain, don't merge** — multiple generators run in sequence via a tiny
  wrapper (`a.py; b.py` — later stages run even if earlier ones fail, so
  staleness flags stay current on bad-input days).

## Gotchas / rules

- Config-above/generated-below is what lets "always current" coexist with
  append-only norms: humans never lose edits, machines never fight them.
- Obsidian `![[embeds]]` of generated files don't render for CLI agents —
  playbooks must order a direct read of the generated file, not the embed.
- Generators that read other generated files must read *below* the
  source's marker (split on the marker, take the last part).

## Done when (for a new generated file)

- [ ] Marker in place; config/header above; generator writes only below
- [ ] Stamp line present and dated on every run
- [ ] Generator pins input headers and exits non-zero on mismatch
- [ ] Scheduled (launchd/cron) and run once by hand to verify
- [ ] Its readers (agent roles, skills) know the cadence and check the stamp

## Related

Worked examples: `SYSTEM/bin/build_directory_indexes.py` (per-folder
indexes) · `SYSTEM/optional/automation/status-gen-example.py` (domain
status dashboard). Schema home: `SYSTEM/SCHEMA.md` § Conventions ·
[[skills]]
