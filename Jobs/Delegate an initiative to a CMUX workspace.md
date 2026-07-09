---
type: job
domain: kb-meta
trigger: an initiative/task is ready to run in its own repo context, delegated from the main workspace
frequency: per-initiative
tools: cmux, Claude Code, git, Initiatives/
owner: {{NAME}}
status: active
tags: [job, env]
aliases: [Delegate to a workspace, Spin up a CMUX workspace, Delegate an initiative]
---

## Model — orchestrator: a capable model (Claude Code lead). Delegated workspace agent: a capable or cheaper model by task weight.

# Job — Delegate an initiative to a CMUX workspace

> **When:** the main workspace needs to hand a whole task/initiative to its own
> CMUX workspace (own repo/worktree, own agent) · **Frequency:** per-initiative ·
> **Tools:** `cmux` CLI, Claude Code, git, the initiative note
> **Outcome:** a dedicated, colour-coded CMUX workspace running its own Claude
> Code on the right `--cwd`, kicked off against an `Initiatives/<slug>.md` note
> that is the shared source of truth — with the dispatch recorded back in that note.

## When to run this
The unit of work is a **whole workstream** that wants its own repo context and
lifecycle — not a fan-out of sub-tasks within one session (that's
[[Spawn subagent panes in a CMUX workspace]]). You're operating from the **main
workspace** (Claude Code orchestrator, cwd = your vault root). This is an
**optional extension** — see `meta/AGENTS.md` § Optional extensions for the
two-interface model behind it (vault = memory/durable, CMUX = runtime/ephemeral;
state round-trips through the vault). **Precondition:** the initiative has a note
in `Initiatives/` (if not, run [[Run an initiative]] first) — that note is the
delegated workspace's `backlog.md`.

## Steps
1. **Preflight the socket.** `cmux identify --json` should succeed. If not, launch
   CMUX and poll:
   ```bash
   cmux identify --json >/dev/null 2>&1 || { open -a cmux; \
     for i in $(seq 1 30); do cmux identify --json >/dev/null 2>&1 && break; sleep 0.5; done; }
   ```
   (`cmux` = `/Applications/cmux.app/Contents/Resources/bin/cmux` — symlink it onto PATH once.)
2. **Pick the window.** Reuse the current one: `WIN=$(cmux list-windows --json | jq -r '.[0].id')`.
3. **Create the workspace on the initiative's cwd** — a repo checkout or a
   worktree. Capture the refs:
   ```bash
   read WS LEAD < <(cmux workspace create --window "$WIN" --name "<slug>" \
     --cwd "$HOME/dev/<repo-or-worktree>" --focus true --json \
     | jq -r '[.workspace_ref,.surface_ref]|@tsv')
   ```
   Add `--env-file ./.env` when the workspace needs credentials injected.
4. **Make it legible** — colour + status so it's scannable in the sidebar:
   ```bash
   cmux rename-tab --workspace "$WS" --surface "$LEAD" "🎯 <slug>"
   cmux workspace-action --action set-color --workspace "$WS" --color <Colour>
   cmux set-status initiative "<slug>" --workspace "$WS"
   ```
5. **Launch the delegated Claude Code** into the lead surface (pick the model by
   task weight — a cheaper model for well-scoped execution, a more capable one
   for heavy reasoning):
   ```bash
   cmux send --surface "$LEAD" "claude --model <model-id>"
   cmux send-key --surface "$LEAD" enter
   sleep 4
   ```
6. **Kick it off with a one-line brief** that points at the vault note as its
   source of truth and demands a sentinel on completion. **One line, no newlines:**
   ```bash
   cmux send --surface "$LEAD" "Read <vault>/Initiatives/<slug>.md; execute its Now-and-next; write decisions/actions back to that note; end with: DONE: <slug> | <summary>"
   cmux send-key --surface "$LEAD" enter
   ```
7. **Record the dispatch in the vault** *(this is the round-trip — do not skip)* —
   in `Initiatives/<slug>.md` add a dated Milestone ("delegated to CMUX workspace
   `<slug>` on `<cwd>`, <date>") and any `#action`s you're now waiting on.
8. **Coordinate to completion** (event-driven, not busy-poll):
   ```bash
   cmux events --category notification --reconnect | grep -m1 "$WS" >/dev/null
   cmux read-screen --surface "$LEAD" --scrollback --lines 60 | tail -30
   ```
   **Confirm the `DONE:` sentinel actually printed** before trusting it — a wake
   can mean "needs input", not "finished". If it's asking for input, `send` the
   answer + `send-key enter`.
9. **Close out.** When the initiative note reflects the outcome (results, decisions,
   next actions written back), tear the workspace down: `cmux workspace close
   --workspace "$WS"` (or keep it if work continues). The vault, not CMUX, is the record.

## Gotchas / rules
- **State lives in the vault, not the workspace.** A CMUX workspace is disposable;
  if the plan/result isn't written into `Initiatives/<slug>.md`, it's lost on
  teardown. Step 7 + step 9 are the whole point.
- **`send` types; `send-key enter` submits.** A `send` with no follow-up `enter`
  leaves the prompt unsent. **Never put a `\n` inside a `send`** — each newline
  fires a half-finished turn; keep briefs to one line and split if long.
- **Thread the refs.** Always capture `workspace_ref`/`surface_ref` from `--json`
  and reuse them — never guess a surface address.
- **Notify ≠ done.** Always `read-screen` and confirm the sentinel; agents notify
  when they need input too.
- **`socketControlMode: cmuxOnly` is fine** for an orchestrator running inside a
  CMUX pane (the default). Only raise to `allowAll` if you drive from outside CMUX.
- **One workspace = one repo context.** If the "delegation" is really N concurrent
  sub-tasks sharing one context, use panes instead → [[Spawn subagent panes in a CMUX workspace]].

## Done when
- [ ] A dedicated CMUX workspace is running its own Claude Code on the right `--cwd`, kicked off against the initiative note.
- [ ] The dispatch (and, at close, the outcome) is written back into `Initiatives/<slug>.md`.
- [ ] The `DONE:` sentinel was confirmed via `read-screen` (not assumed from a notification).

## Related
- `meta/AGENTS.md` § Optional extensions — the model + why (the two-interface split, the round-trip rule).
- [[Spawn subagent panes in a CMUX workspace]] — sibling runbook for pane-level fan-out.
- [[Run an initiative]] — creates/maintains the `Initiatives/` note this delegates against.
- [[AGENTS]]
