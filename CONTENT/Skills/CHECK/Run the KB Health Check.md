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
---

# Skill — Run the KB health check

> **When:** on request ("run the knowledge health check") or on a schedule
> **Outcome:** a verdict (green / issues) + a list of any real problems to fix

## When to run this
- Weekly as a manual habit.
- Automatically at 6pm if you've installed the `SYSTEM/optional/automation/daily-summary.sh` job.
- Any time you suspect the KB has drifted (broken links, stale actions, inbox pile-up).

## Steps
1. **Inbox check.** List the vault root. Flag anything that isn't: `README.md`, `index.md`, `Actions.md`, `CLAUDE.md`, or a registered structural folder (`CONTENT/Concepts/`, `CONTENT/Initiatives/`, `SYSTEM/`, `CONTENT/raw/`, `daily/`, `CONTENT/People/`, `CONTENT/Skills/`, `attachments/`, `CONTENT/Excalidraw/`). Each un-filed item is a lint failure.
2. **Wikilink check.** Grep all `[[wikilinks]]` across the vault. For each target, confirm a `.md` file with that basename exists. Report any that don't — filtering known false positives (e.g. convention-example links in `AGENTS.md` and `CLAUDE.md`).
3. **Index completeness.** Scan `CONTENT/Concepts/` and `CONTENT/Initiatives/`. Every file there should appear in `index.md`. Report any that don't.
4. **Raw provenance.** Every fact in a concept article should trace to a `CONTENT/raw/` capture. Spot-check if asked; flag any concept with no raw citation.
5. **Actions audit.** Grep `#action` checkboxes across all non-daily notes. Every open `- [ ]` should be real and still open; every completed `- [x]` should be checked, not deleted.
6. **People links.** Grep `[[Person Name]]` wikilinks across all notes. Each should resolve to a `CONTENT/People/<Person Name>.md` file.
7. **Skills index.** Verify every skill under `CONTENT/Skills/<TYPE>/*.md` is listed in `CONTENT/Concepts/skills.md`.
8. **Report.** State: `green — <one clause>` or `issues — <sub-bullet per real problem>`. Log a one-line entry in `SYSTEM/log.md`.

## Gotchas / rules
- Convention examples in `AGENTS.md` / `CLAUDE.md` (`[[note-name]]`, `[[wikilink]]`) are documented false positives — don't flag them.
- `daily/` notes are ephemeral working notes; don't lint their wikilinks against the main vault.
- A missing `CONTENT/raw/` citation is a soft warning, not a hard failure — flag it but don't block on it.

## Done when
- [ ] All eight checks run.
- [ ] Verdict reported: `green` or `issues — <list>`.
- [ ] One-line entry appended to `SYSTEM/log.md` with the verdict.

## Related
[[karpathy-method]] · [[AGENTS]] · [[Capture a meeting or conversation into the KB]]
