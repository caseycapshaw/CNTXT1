---
type: initiative
status: active        # active | paused | done
started: YYYY-MM-DD
updated: YYYY-MM-DD   # bump on every meaningful rewrite (same rule as concepts)
tags: [initiative, <domain>]
---

# Initiative — {Title}

> **Outcome:** _one or two lines — what "done" looks like, concretely._

## Now & next
_The current state of the workstream, rewritten in place as it moves (this is
the part you read first when returning). What's true now; what happens next._

## Decisions
_Dated, append-only. One line each: `- YYYY-MM-DD — decided X because Y.`_

## Open questions
_Unknowns to resolve (not tasks — when a question's answer is a task you
perform, write it as an `#action` below instead)._

## Actions
_Inline checkboxes, next to their context — they aggregate into `Actions.md`
automatically and group under this initiative's filename._

- [ ] _(first action)_ #action

## Milestones
_Dated one-liners as things land: `- YYYY-MM-DD — milestone.` Close the
initiative with a final entry, set `status: done` above, and distill any
durable knowledge into the relevant concept(s) — the note itself stays as the
record (never delete)._

## Related
_[[concepts]], [[People]], [[Jobs]], and `raw/` captures this draws on._
