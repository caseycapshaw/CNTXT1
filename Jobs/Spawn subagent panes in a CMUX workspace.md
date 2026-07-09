---
type: job
domain: kb-meta
trigger: one task decomposes into concurrent sub-tasks you want to run and watch as panes
frequency: ad-hoc
tools: cmux, Claude Code
owner: {{NAME}}
status: active
tags: [job, kb-meta]
aliases: [Spawn subagent panes, Fan out subagents, Subagent panes, Spawn workers in panes]
---

# Job — Spawn subagent panes in a CMUX workspace

> **When:** a single task fans out into concurrent sub-tasks you want visible and
> drivable as panes in the current workspace · **Frequency:** ad-hoc ·
> **Tools:** `cmux` CLI, Claude Code
> **Outcome:** N worker agents running in split panes, each driven by the session
> lead through the four-verb loop, each reporting a `DONE:` sentinel — torn down
> when finished.
> **Model:** lead — a capable model (coordinates, doesn't do the heavy edits);
> worker panes — a cheaper/faster model where appropriate.

## When to run this
The work is **one task with concurrent legs that share a context** (e.g.
research three sources at once; build + test in parallel), not a whole workstream
needing its own repo (that's [[Delegate an initiative to a CMUX workspace]]).
You're the **lead** in an existing workspace. This is an **optional extension** —
see `meta/AGENTS.md` § Optional extensions for the model + why (the two-interface
split, the four-verb loop, model policy). **The lead coordinates — it does not do
the heavy editing itself once workers exist.**

## Steps
1. **Know your own surface.** From the lead pane, `cmux identify --json` (socket
   check) and `cmux list-pane-surfaces` to see the workspace + your surface ref.
   Set `WS=<workspace_ref>` and `LEAD=<your surface_ref>`.
2. **Split off worker panes** — anchor each split on an existing surface; capture
   each new ref. E.g. three workers:
   ```bash
   W1=$(cmux new-split right --workspace "$WS" --surface "$LEAD" --json | jq -r .surface_ref)
   W2=$(cmux new-split down  --workspace "$WS" --surface "$W1"   --json | jq -r .surface_ref)
   W3=$(cmux new-split down  --workspace "$WS" --surface "$LEAD" --json | jq -r .surface_ref)
   ```
3. **Label them** so the grid is scannable: `cmux rename-tab --workspace "$WS"
   --surface "$W1" "🔬 research-A"` (repeat per worker); optional `cmux
   trigger-flash --surface "$W1"` to point at one.
4. **Launch an agent in each pane** (a cheaper/faster model for well-scoped legs).
   `send` the CLI line, then `send-key enter`, and give it a moment to boot:
   ```bash
   for S in "$W1" "$W2" "$W3"; do
     cmux send --surface "$S" "claude --model <model-id>"
     cmux send-key --surface "$S" enter
   done
   sleep 4
   ```
5. **Dispatch one single-line task per worker**, each ending in a sentinel. **One
   line, no embedded newlines:**
   ```bash
   cmux send --surface "$W1" "<worker A's task>. End with exactly: DONE: research-A | <summary>"
   cmux send-key --surface "$W1" enter
   # repeat for W2, W3
   ```
6. **Wait on the doorbell, then confirm** — block on the notification stream, then
   read the pane and check the sentinel actually printed:
   ```bash
   cmux events --category notification --reconnect | grep -m1 "$W1" >/dev/null
   cmux read-screen --surface "$W1" --scrollback --lines 80 | tail -30
   ```
   One event stream serves all workers for parallel dispatch. A wake can mean
   "needs input" — if so, `send` the answer + `send-key enter`, don't mark it done.
7. **Integrate + write back.** The lead collects each worker's result and folds it
   into the deliverable / the relevant vault note (concept, initiative, daily
   note). Route any failure back to the responsible worker with a follow-up `send`.
8. **Tear down** finished panes: `cmux close-surface --surface "$W1"` (repeat).
   Close a runaway the same way.

## Gotchas / rules
- **`send` types, `send-key enter` submits; never embed `\n`** — each newline
  fires a separate half-finished turn. One line per `send`.
- **Thread refs from `--json`** — capture every `surface_ref` at creation; never
  guess an address.
- **Notify ≠ done** — always `read-screen` and confirm the `DONE:` sentinel; agents
  notify when they need input too. Wait on events; **don't busy-poll**.
- **Lead doesn't do the heavy lifting** once workers exist — it decomposes,
  dispatches, integrates, reports. Keep its own edits to integration.
- **Panes share the workspace cwd/context** — if a leg needs a different repo, it's
  a workspace-level delegation instead → [[Delegate an initiative to a CMUX workspace]].
- **Claude Code's own Task/Agent subagents are in-process**, not CMUX panes. This
  runbook is the explicit-pane path (visible, drivable). Some CMUX versions can
  surface native subagents as panes automatically — untested; prefer explicit
  `new-split` for now.

## Done when
- [ ] N worker panes launched, labelled, and each dispatched a one-line task with a sentinel.
- [ ] Every worker's `DONE:` sentinel confirmed via `read-screen`; results integrated by the lead and written to the right vault note.
- [ ] Finished panes torn down with `close-surface`.

## Related
- `meta/AGENTS.md` § Optional extensions — the model + why (the four-verb loop, coordination patterns, model policy).
- [[Delegate an initiative to a CMUX workspace]] — sibling runbook for workspace-level (whole-task) delegation.
- [[AGENTS]]
