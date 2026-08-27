---
type: do
domain: kb-meta
trigger: "an outcome needs multiple actions over time (rule of thumb: 3+ actions or more than a week)"
frequency: ad-hoc
tools: ["Write", "Edit", "Read"]
owner: "{{NAME}}"
status: active
tags: [do, kb-meta]
aliases: ["Run an initiative", "Start an initiative", "Close an initiative", "Open an initiative", "run-an-initiative"]
summary: Opens, updates, or closes a Knowledge/Initiatives/ note that carries a multi-action workstream from start to done.
author_type: script
---

> _Generated from `.claude/skills/run-an-initiative/SKILL.md` by `SYSTEM/bin/build_claude_mirrors.py` — edit the canonical file, never this mirror. Generated: 2026-08-27_

# Skill — Run an initiative

> **When:** a goal is bigger than a single `#action` — multiple actions over
> time, accreting decisions and state · **Outcome:** one initiative note in
> `Knowledge/Initiatives/` that carries the whole workstream from open to done
> **Design note:** initiatives keep concept mechanics (`type: initiative`
> frontmatter, evergreen Now & next) but live in their own top-level folder
> for Obsidian-view prominence. Conventions in [[SCHEMA]].

## Start

1. Copy `Knowledge/Initiatives/Initiative TEMPLATE.md` → `Knowledge/Initiatives/<kebab-slug>.md`.
2. Fill frontmatter (`status: active`, `started:` today) and the **Outcome**
   line — if you can't state "done" in two lines, it isn't an initiative yet.
3. Seed **Actions** with the first concrete `- [ ] … #action` (add
   `#priority` if it's a focus item).
4. Index it: add the initiative to `index.md`'s **Initiatives (live)** Quick-map
   line *and* its Initiatives section (one-line summary).
5. Regenerate the link map (`SYSTEM/bin/build-link-map.sh`); append one line to
   `SYSTEM/log.md`.

## Keep it current (whenever the workstream moves)

- Rewrite **Now & next** in place — it's the return-point summary, not a log.
- Append dated one-liners to **Decisions** and **Milestones** as they happen.
- Add/check off `#action`s inline. Bump `updated:`.
- New durable *general* knowledge discovered along the way still compiles into
  regular concepts — the initiative links to them, it doesn't hoard them.

## Close

1. Check off or explicitly drop every open `#action` (dropped ones get a
   one-line reason — don't delete silently).
2. Final **Milestones** entry stating the outcome; set `status: done`
   (or `paused` with a why, if shelved).
3. Distill any durable knowledge into the relevant concept(s) if it isn't
   already there. The initiative note **stays in place as the record** —
   never delete it.
4. Move its `index.md` entry from the live line/list to the section's Done
   line. Log the close in `SYSTEM/log.md`.

## Gotchas / rules

- **Not every project is an initiative** — a single action stays an `#action`
  in its home note; a recurring procedure is a [[skills|Skill]], not an initiative.
- **Actions live IN the initiative note** (they aggregate to `Actions.md` and
  group under the initiative's filename automatically) — never keep a separate
  task list for the initiative.
- **Don't let Now & next become a diary** — it's rewritten state; history
  belongs in Decisions/Milestones.
- A concept that turns out to be goal-shaped converts by `git mv` into
  `Knowledge/Initiatives/` + frontmatter swap to `type: initiative` + the missing
  sections + link-map regen (wikilinks are basename-based, so existing links
  keep resolving).

## Done when

- [ ] Initiative note exists in `Knowledge/Initiatives/` with `type: initiative` frontmatter and a two-line Outcome.
- [ ] Listed in `index.md` (Quick map live line + Initiatives section).
- [ ] At least one `#action` seeded inline.
- [ ] Link map regenerated; `SYSTEM/log.md` entry appended.

## Related
[[skills]] (skill index) · [[SCHEMA]] (conventions) · [[Optimize the knowledge base]] (initiatives are part of the index-budget review)
