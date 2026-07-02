---
type: job
domain: kb-meta
trigger: an outcome needs multiple actions over time (rule of thumb - 3+ actions or more than a week)
frequency: ad-hoc (start/close) + whenever the workstream moves (update)
tools: Write, Edit, Read
owner: {{NAME}}
status: active
tags: [job]
aliases: [Start an initiative, Close an initiative, Open an initiative]
---

# Job — Run an initiative

> **When:** a goal is bigger than a single `#action` — multiple actions over
> time, accreting decisions and state · **Outcome:** one initiative note in
> `concepts/` that carries the whole workstream from open to done
> **Design note:** an initiative is a *kind of concept* (`type: initiative`),
> not a separate folder — transitions between concept ↔ initiative are
> frontmatter-only, so links never break. Conventions in [[AGENTS]].

## Start

1. Copy `concepts/Initiative TEMPLATE.md` → `concepts/<kebab-slug>.md`.
2. Fill frontmatter (`status: active`, `started:` today) and the **Outcome**
   line — if you can't state "done" in two lines, it isn't an initiative yet.
3. Seed **Actions** with the first concrete `- [ ] … #action` (add
   `#priority` if it's a focus item).
4. Index it: add the initiative to `index.md`'s **Initiatives (live)** Quick-map
   line *and* its Initiatives section (one-line summary).
5. Regenerate the link map (`meta/bin/build-link-map.sh`); append one line to
   `meta/log.md`.

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
   line. Log the close in `meta/log.md`.

## Gotchas / rules

- **Not every project is an initiative** — a single action stays an `#action`
  in its home note; a recurring procedure is a [[jobs|Job]], not an initiative.
- **Actions live IN the initiative note** (they aggregate to `Actions.md` and
  group under the initiative's filename automatically) — never keep a separate
  task list for the initiative.
- **Don't let Now & next become a diary** — it's rewritten state; history
  belongs in Decisions/Milestones.
- A concept that turns out to be goal-shaped is *converted in place* — swap
  frontmatter to `type: initiative`, add the missing sections. No file move.

## Done when

- [ ] Initiative note exists in `concepts/` with `type: initiative` frontmatter and a two-line Outcome.
- [ ] Listed in `index.md` (Quick map live line + Initiatives section).
- [ ] At least one `#action` seeded inline.
- [ ] Link map regenerated; `meta/log.md` entry appended.

## Related
[[jobs]] (runbook index) · [[AGENTS]] (conventions) · [[Optimize the knowledge base]] (initiatives are part of the index-budget review)
