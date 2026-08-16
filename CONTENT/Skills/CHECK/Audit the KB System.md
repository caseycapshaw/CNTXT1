---
type: check
domain: kb-meta
trigger: "you ask for a high-level / full-system / architectural audit of the KB and its connected systems"
frequency: quarterly
tools: "parallel read-only subagents, Bash, SYSTEM/bin/lint.sh"
owner: "{{NAME}}"
status: active
tags: [check, kb-meta]
aliases: [Audit the KB system, audit-the-kb-system, system audit]
summary: Full-system architectural audit — parallel auditors over structure/UX, interlinking, consistency, and connected systems, producing a ranked report + phased fix plan executed phase-by-phase.
updated: 2026-08-16
---

# Skill — Audit the KB System

> **When:** on request ("step back and audit the KB"), or ~quarterly · **Frequency:** quarterly
> **Outcome:** a dated `CONTENT/raw/YYYY-MM-DD-kb-system-audit.md` report — architecture
> diagram, ranked findings, phased fix plan — then phases executed one at a time on your go.

## When to run this

When the KB "feels off" at the architecture level, after a major structural change
(taxonomy migration, folder refactor, new automation), or quarterly. This is the
**wide** audit; for narrower cadences use the siblings: [[Run the KB Health Check]]
(mechanical + judgment lint), [[Optimize the Knowledge Base]] (LLM-speed/efficiency),
[[Audit State Freshness]] (stale claims on always-loaded surfaces).

## Steps

1. **Baseline:** run `SYSTEM/bin/lint.sh` — record the mechanical verdict first so
   qualitative findings are clearly *beyond* what lint sees.
2. **Fan out 4 parallel read-only subagents**, one per dimension (each returns raw
   structured findings with paths/counts/evidence, most-damaging first):
   - **Structure/UX** — folder inventory + misplacements; `index.md` quality (measure
     the Quick-map skeleton vs the `head -c 8000` injection budget — lint now guards
     this); redundancy/drift across `CLAUDE.md` / `SYSTEM/AGENTS.md` / `index.md`;
     root-inbox items vs the registered exceptions; naming collisions; folders lacking
     READMEs.
   - **Interlinking** — orphan notes (zero content inbound links); dead-end concepts
     (zero outbound / no Related / no raw cite); link-map health (count, duplicates,
     stale aliases); raw→concept traceability sampling; plain-text people mentions
     that should be `[[Full Name]]`; whether `daily/` links into the graph.
   - **Consistency/staleness** — `updated:` vs contradicting facts; initiative
     lifecycle (active-but-stale >3wks, done-but-unarchived, index Quick-map line vs
     real statuses); index one-liners vs `description:` fields; open `#action` reality
     check; log format; uncommitted git state; naming-convention drift.
   - **Connected systems** — Skills notes ↔ any agent-CLI shims in sync; `SYSTEM/bin`
     documented; scheduled jobs *actually loaded* vs documented (check the scheduler,
     e.g. `launchctl list`, not just the README — and note which machine owns which
     job if you run more than one); hook files/symlinks resolve; generated-section
     stamps fresh *and their generators actually succeeding* (read the job logs — a
     green stamp can hide a failing ingest); vault git remotes match your
     privacy/content-separation policy; machinery write-target files draining.
3. **Verify the top findings yourself** before reporting — subagents trust surfaces
   that can themselves be stale (an index blurb can contradict the note it
   summarizes). Re-read the primary source for anything ranked critical.
4. **Write the report** to `CONTENT/raw/YYYY-MM-DD-kb-system-audit.md`: ASCII
   architecture diagram (inputs → vault folders → connected systems), verdict line,
   findings ranked critical/high/medium + a "healthy (verified)" list, and a
   **phased fix plan** (Phase 1 = silent failures, then doc drift, then content
   hygiene, then naming/UX) with inline `#action` checkboxes.
5. **Execute phase-by-phase on your go**, checking off the plan in the raw note as
   phases land. Every fix that closes a *class* of problem should also add a lint
   check so recurrence is mechanical, not vigilance.
6. **Close the loop each phase:** lint green → `SYSTEM/log.md` one-liner → link-map
   regen if anything was added/renamed → bump `updated:` on touched notes.

## Gotchas / rules

- **Lint green ≠ healthy.** The audit's job is the gap between mechanical checks and
  reality — and to shrink that gap by adding checks. Classic invisible-to-lint
  failures: an injection-budget overflow, a rename without `aliases:` leaving links
  dangling, a data feed failing behind a fresh status stamp.
- **Generated-green is not pipeline-green:** always read the job *logs*, not just
  the output stamps.
- If your automation code lives in a separate repo, fix it there (edit → commit →
  push), never by hand-patching deployed copies.
- Actions only the human can do (payments, OS permission grants, outbound messages,
  deletions of people-notes) get **prepped to the decision point** and filed as
  `#action`s — don't block a phase on them.
- Real user decisions (renames of structural vocabulary, repo policy changes) go to
  the human as explicit options with a recommendation — don't decide unilaterally.

## Done when

- [ ] Report exists in `CONTENT/raw/` with diagram, ranked findings, and a phased plan.
- [ ] All phases either executed (checked off in the report) or explicitly parked
      with an owner.
- [ ] `lint.sh` green, including any new checks added by the audit.
- [ ] `SYSTEM/log.md` has one line per phase; link map regenerated if needed.

## Related

[[AGENTS]] (the schema being audited) · [[karpathy-method]] (why lint is
non-negotiable) · [[Run the KB Health Check]] · [[Optimize the Knowledge Base]] ·
[[Audit State Freshness]].
