# Optional: automation appendix

The core KB method ([[AGENTS]]) is just **raw → compile → index → log** — no
automation required. This folder adds the *optional* machinery that makes the base
feel alive day to day. Adopt it once the basic habit has stuck; skip it entirely
and the KB still works.

Everything here is **macOS + Claude Code** specific (launchd, the SessionStart
hook). On Linux/Windows the ideas port but the glue (launchd) does not. Calendar
access uses the `gws` CLI (Google Calendar) rather than any local app, so it
ports to Linux/Windows as-is provided `gws` is installed there too.

## What's in the box

| Piece | File | What it does |
| :-- | :-- | :-- |
| **Session loader** | `sessionstart-hook.sh` | A Claude Code **SessionStart hook** that inlines your `index.md` map, the live inbox state, today's calendar, and a pointer to today's plan note — every time you open Claude Code in the vault. Auto-skips inside `~/dev` and any folder with its own `CLAUDE.md`. |
| **Calendar cache** | `calendar-fetch.sh` | Pulls today's events from Google Calendar (via [`gws`](https://github.com/googleworkspace/cli), the primary calendar only) into a cache file. The hook only *reads* the cache, so startup stays instant. |
| **Daily plan generator** | `daily-plan.sh` | Runs headless `claude -p` to write `daily/YYYY-MM-DD.md` — today's schedule + a **"From the inbox" Gmail digest** (via `gws`, read-only, last 2 days; auto-skipped if `gws` is absent) + a **live Tasks query** of focus actions + a priorities anchor. Idempotent, retries on network gaps, writes a fallback stub if the API is unreachable. |
| **Morning scheduler** | `com.example.daily-plan.plist` | A launchd job that runs `daily-plan.sh` at 08:00 daily. |
| **End-of-day summary** | `daily-summary.sh` | Runs the deterministic `meta/bin/lint.sh` for the mechanical lint, then headless `claude -p` to (1) add the **judgment-layer lint** (stale items, resolved questions, action hygiene) and (2) **append a "What we did today" recap** to the day's note — local inputs only, no network needed for content. Finishes with a **nightly git snapshot** (commit + best-effort push) so the KB always has a rollback point. Idempotent: re-runs replace the block, never duplicate. |
| **Evening scheduler** | `com.example.daily-summary.plist` | A launchd job that runs `daily-summary.sh` at 18:00 daily (companion to the 8am job). |

The result: every morning a fresh `daily/` note appears, every evening the KB is
linted and the day is recapped, and every Claude Code session in the vault starts
already knowing your map, your inbox, and your day.

> `daily/` is a **structural folder, not the inbox** — its notes are ephemeral
> working notes; never triage them into `raw/`. The daily note **queries** your
> `#action` tasks (it never copies them), so nothing is duplicated into
> `Actions.md`. Add `daily/` to the exclusions if you later add it to your vault.

---

## Prerequisites

1. **Claude Code** installed and working from the terminal (`claude -p "hi"` returns text).
2. **Obsidian Tasks plugin** (for the live `#action` query in the daily note and `Actions.md`).
3. **`gws`** (only for the calendar feature) installed and authenticated: `brew install googleworkspace-cli` — NOT the unrelated `gws` formula that also installs a `gws` binary (Homebrew will warn about the conflict; make sure `googleworkspace-cli` is what's installed). Then `gws auth setup` (requires `gcloud`) followed by `gws auth login`. Verify with `gws auth status`.

---

## Install (≈10 min)

> Replace `{{VAULT}}` with your KB's absolute path (e.g. `/Users/you/my-kb`) and
> `{{NAME}}` with your name everywhere below. Each script also has a **CONFIG block
> at the top** — edit it before first run.

1. **Copy the scripts into your Claude hooks dir:**
   ```sh
   mkdir -p ~/.claude/hooks ~/.claude/cache
   cp meta/optional/automation/sessionstart-hook.sh ~/.claude/hooks/knowledge-context.sh
   cp meta/optional/automation/calendar-fetch.sh    ~/.claude/hooks/
   cp meta/optional/automation/daily-plan.sh        ~/.claude/hooks/
   chmod +x ~/.claude/hooks/*.sh
   ```
   Then open each and set the CONFIG block (`VAULT`, `NAME`).

2. **Register the SessionStart hook** in `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "SessionStart": [
         { "hooks": [ { "type": "command", "command": "~/.claude/hooks/knowledge-context.sh" } ] }
       ]
     }
   }
   ```
   (Or just ask Claude Code: *"use the update-config skill to register knowledge-context.sh as a SessionStart hook."*)

3. **Copy the daily-summary script:**
   ```sh
   cp meta/optional/automation/daily-summary.sh ~/.claude/hooks/
   chmod +x ~/.claude/hooks/daily-summary.sh
   ```
   Open it and set the CONFIG block (`VAULT`, `NAME`) — same values as `daily-plan.sh`.

4. **Schedule both daily jobs:**
   ```sh
   cp meta/optional/automation/com.example.daily-plan.plist    ~/Library/LaunchAgents/
   cp meta/optional/automation/com.example.daily-summary.plist ~/Library/LaunchAgents/
   # Edit each plist: set Label, the script path, and the log paths to your username
   launchctl load ~/Library/LaunchAgents/com.example.daily-plan.plist
   launchctl load ~/Library/LaunchAgents/com.example.daily-summary.plist
   ```
   Test without waiting for the scheduled times:
   ```sh
   ~/.claude/hooks/daily-plan.sh --force    # generates today's note
   ~/.claude/hooks/daily-summary.sh         # lints + appends today's recap
   ```
   Logs land in `~/.claude/cache/daily-plan.log` and `~/.claude/cache/daily-summary.log`.

---

## How `daily-plan.sh` decides what to do

1. Refresh the calendar cache (best-effort).
2. **Idempotency:** if today's note already exists, do nothing (`--force` overrides).
3. Run headless `claude -p` to write the note from a fixed prompt (schedule + a verbatim Tasks query + a short priorities anchor).
4. On success, append one line to `meta/log.md`. On API-unreachable-after-retries, write a **stub** with a one-click retry instead of skipping the day.

The network retry exists because 8am-right-after-wake often beats your VPN coming
up — the stub + retry is what keeps a day from silently going missing.

---

## Extending it

The shipped `daily-plan.sh` covers calendar + a Gmail inbox digest (both via
`gws`, fetched off the hot path and injected into the prompt — the headless run
itself needs no Bash or MCP access) + actions + priorities. To add further live
digests (e.g. a *"From the channels & board"* section from **Slack** and **Jira**),
scope the headless run to just those MCP servers and ask the model to summarize
activity since the last working day:

- Generate a scoped MCP config (so you don't spawn all servers at 8am):
  ```sh
  jq '{mcpServers: {slack: .mcpServers.slack, jira: .mcpServers.jira}}' \
     ~/.claude.json > ~/.claude/hooks/daily-plan.mcp.json
  ```
- Pass `--mcp-config ~/.claude/hooks/daily-plan.mcp.json --strict-mcp-config` plus an
  `--allowedTools` allowlist of the specific Slack/Jira read tools to the `claude -p` call.
- Add a section to the prompt naming your channels, your Slack/Jira user IDs, and the
  JQL for your board. Tell it to **omit empty groups and never invent** activity.

Search `daily-plan.sh` for the `# OPTIONAL DIGEST` marker — the hook points are noted inline.
