---
type: project
description: <one-line summary of the project — single-sources the index one-liner>
status: active        # pending | active | paused | done   (pending = Someday/Maybe: opened, waiting on a trigger)
started: YYYY-MM-DD
updated: YYYY-MM-DD   # bump on every meaningful rewrite (same rule as concepts)
area: "[[<area-slug>]]"   # REQUIRED up-link — the 02 Areas/ note this project serves
serves: "[[<goal-slug>]]"  # optional — a type: goal note (does not replace area:)
tags: [project, <domain>]
---

# Project — {Title}

> **Outcome:** _one or two lines — what "done" looks like, concretely. A project
> has a genuine endpoint (the endpoint test) — if it can never be "done", it's
> an area, not a project._

## Now & next
_The current state of the workstream, rewritten in place as it moves (this is
the part you read first when returning). What's true now; what happens next.
Capped at 500 words — script-measured (`SYSTEM/bin/cap_check.py`)._

## Actions
_Inline checkboxes, next to their context — they aggregate into `Actions.md`
automatically and group under this project's filename. An active project always
carries at least one open next action (`SYSTEM/bin/audit-project-next-actions.sh`)._

- [ ] _(first action)_ #action

## Decisions
_Dated, append-only. One line each: `- YYYY-MM-DD — decided X because Y.`_

## Open questions
_Unknowns to resolve (not tasks — when a question's answer is a task you
perform, write it as an `#action` above instead)._

## Milestones
_Dated one-liners as things land: `- YYYY-MM-DD — milestone.` Capped at 400
words — overflow moves verbatim to the trail (`SYSTEM/bin/cap_overflow.py`).
Close the project with a final entry, set `status: done` above, distill durable
knowledge into the relevant concept(s)/area(s), and `git mv` the note into
`03 Projects/archive/` — the note itself stays as the record (never delete)._

## Trail
_Optional — for long-running projects. Append-only, one line per working
session (`- YYYY-MM-DD — what moved`), written at the session close
([[Close a Session]]). "Now & next" stays the rewritten state — never mix the
two. When Now & next or Milestones outgrow their caps, history moves verbatim to
`03 Projects/trails/<slug>-trail.md` (see [[SCHEMA]] § Orientation caps +
trails). Delete this section for short-lived projects._

## Related
_[[concepts]], [[People]], the owning area, and `raw/` captures this draws on._
