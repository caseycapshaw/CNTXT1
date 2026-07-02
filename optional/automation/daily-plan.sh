#!/usr/bin/env bash
# daily-plan.sh — generate the morning planning note in the knowledge base.
#
# Invoked by launchd at 08:00. Steps:
#   1. Set a sane HOME/PATH (launchd's environment is sparse).
#   2. Refresh today's calendar cache (calendar-fetch.sh, ~30s).
#   3. Idempotency: if today's note already exists, do nothing (no clobber).
#   4. Run headless `claude -p` to write <VAULT>/daily/<DATE>.md from the calendar
#      + a live #action query + current priorities.
#   5. Append a one-line entry to meta/log.md (or write a retry stub on failure).
#
# All output is captured by the launchd plist into ~/.claude/cache/daily-plan.log.

export HOME="${HOME:-/Users/CHANGE_ME}"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# ===== CONFIG — edit this =====
VAULT="$HOME/my-kb"          # absolute path to your KB
NAME="your name"             # how the note addresses you
# ==============================

daily_dir="$VAULT/daily"
today="$(date +%F)"
note="$daily_dir/$today.md"
cache="$HOME/.claude/cache/calendar-today.txt"
fetch="$HOME/.claude/hooks/calendar-fetch.sh"

# --force regenerates even if a note exists (used by the retry link in a stub).
force=0
[ "${1:-}" = "--force" ] && force=1

echo "=== daily-plan run $(date)${force:+ (force=$force)} ==="
mkdir -p "$daily_dir"

# 2) Refresh calendar cache (best-effort; the prompt degrades if it's missing).
[ -x "$fetch" ] && "$fetch"

# 3) Idempotency guard — never overwrite a note already written today (unless --force).
if [ -f "$note" ] && [ "$force" -ne 1 ]; then
  echo "Note already exists for $today; skipping (pass --force to regenerate)."
  exit 0
fi
[ "$force" -eq 1 ] && rm -f "$note"

cal="$(cat "$cache" 2>/dev/null | tail -n +2)"   # drop the date marker line
[ -z "$cal" ] && cal="(calendar unavailable)"

# 3b) Gmail digest (best-effort; read-only). Requires the `gws` CLI authenticated
#     (`gws auth status`). Pulls headers+snippets of the last 2 days of inbox mail
#     so the note can carry a "From the inbox" digest. Degrades to no section if
#     gws is absent or errors — the core plan never depends on it.
digest=""
if command -v gws >/dev/null 2>&1; then
  ids="$(gws gmail users messages list \
    --params '{"userId":"me","q":"in:inbox newer_than:2d","maxResults":20}' 2>/dev/null \
    | jq -r '.messages[]?.id' 2>/dev/null)"
  while IFS= read -r id; do
    [ -z "$id" ] && continue
    line="$(gws gmail users messages get \
      --params "{\"userId\":\"me\",\"id\":\"$id\",\"format\":\"metadata\",\"metadataHeaders\":[\"From\",\"Subject\",\"Date\"]}" 2>/dev/null \
      | jq -r '[
          ([.payload.headers[]? | select(.name=="Date")    | .value] | first // "?"),
          ([.payload.headers[]? | select(.name=="From")    | .value] | first // "?"),
          ([.payload.headers[]? | select(.name=="Subject") | .value] | first // "(no subject)"),
          (.snippet // "" | .[0:140])
        ] | join(" | ")' 2>/dev/null)"
    [ -n "$line" ] && digest="${digest}${line}"$'\n'
  done <<< "$ids"
  echo "gmail digest: $(printf '%s' "$digest" | grep -c . ) messages fetched"
fi
[ -z "$digest" ] && digest="(no emails fetched)"

read -r -d '' prompt <<EOF
You are writing ${NAME}'s morning planning note in the Obsidian knowledge base at
$VAULT. Follow the conventions in $VAULT/meta/AGENTS.md (read it if unsure) and use
[[wikilinks]] to link concepts.

TODAY is $today. Today's calendar (already fetched for you):
---
$cal
---

Recent inbox email, last 2 days (already fetched for you; format:
Date | From | Subject | snippet):
---
$digest
---

Do the following, then WRITE the result to exactly this path: $note

1. For context only, you MAY scan open priority / time-sensitive actions to inform
   the anchor below — Grep $VAULT for "#priority" and for "📅" dates <= $today.
   But DO NOT copy any "#action" checkboxes into the note: the Focus section is a
   LIVE QUERY (step 3), and copying would duplicate tasks in the Actions dashboard.
2. Skim $VAULT/index.md for the current concepts/work to anchor the day.
3. Write the note with EXACTLY these sections (skip "From the inbox" entirely if
   the email list above is "(no emails fetched)" or contains nothing noteworthy):
   # $today — Daily plan
   ## Schedule
   (today's events as a clean time-ordered list, from the calendar above)
   ## From the inbox
   (digest the email list above: one line per NOTEWORTHY item, grouped under bold
   mini-headers only when a group has entries — **Money & bills**, **Kids & school**,
   **Appointments & logistics**, **Other notable**. Skip marketing, newsletters,
   notifications-of-no-consequence. NEVER invent an email; if nothing is noteworthy,
   omit this whole section. Do not mark anything as an action — just surface it.)
   ## Focus / open actions
   (paste this fenced block VERBATIM as the entire section — nothing else):
   \`\`\`tasks
   not done
   tags include #action
   (tags include #priority) OR (due before tomorrow)
   path does not include daily
   sort by due
   short mode
   \`\`\`
   ## Priorities anchor
   (2-4 bullets on what today moves forward, with [[wikilinks]])

   # OPTIONAL DIGEST — to add further live digests (Slack/Jira via scoped MCP
   # servers, etc.), insert a section here and pass the scoped MCP config + tool
   # allowlist in the claude call below. See this folder's README.md ("Extending it").

   ## Notes
   (leave a short empty space for the day's running notes)

Keep it tight — a working plan, not an essay. Do NOT write any "- [ ] … #action"
checkboxes anywhere (they would duplicate tasks). Use only what the calendar and KB
contain; don't invent events. Write the file and stop.
EOF

# 4) Generate the note unattended. Your ~/.claude/settings.json supplies auth + base
#    URL; ensure Write to your vault is allow-listed there. acceptEdits + an explicit
#    tool allowlist keep the run non-interactive without skip-perms.
cd "$VAULT" || exit 1

# If your API base URL is internal/VPN-only, 8am-right-after-wake may beat the
# network coming up. So: wait for reachability and retry rather than failing.
base_url="${ANTHROPIC_BASE_URL:-$(jq -r '.env.ANTHROPIC_BASE_URL // empty' "$HOME/.claude/settings.json" 2>/dev/null)}"
attempts="${DAILY_PLAN_ATTEMPTS:-6}"
delay="${DAILY_PLAN_DELAY:-120}"

# Core run: file tools only. (For the OPTIONAL DIGEST, add --mcp-config + --strict-mcp-config
# and the extra mcp__… tools to this array — see README.md "Extending it".)
tools=(--allowedTools "Read" "Glob" "Grep" "Write" "Edit")

rc=1
for n in $(seq 1 "$attempts"); do
  if [ -n "$base_url" ] && ! curl -s --max-time 10 -o /dev/null "$base_url"; then
    echo "preflight: $base_url unreachable (attempt $n/$attempts)"
  else
    claude -p "$prompt" --add-dir "$VAULT" --permission-mode acceptEdits "${tools[@]}"
    rc=$?
    echo "claude exit: $rc (attempt $n/$attempts)"
    [ -f "$note" ] && break
  fi
  [ "$n" -lt "$attempts" ] && { echo "retrying in ${delay}s…"; sleep "$delay"; }
done

# 5) Log the run (only if the note was actually written); else write a retry stub.
if [ -f "$note" ]; then
  printf -- '- %s — auto-generated daily plan note `daily/%s.md` (launchd 8am).\n' \
    "$today" "$today" >> "$VAULT/meta/log.md"
  echo "Wrote $note and logged it."
else
  cat > "$note" <<STUB
# $today — Daily plan  ⚠️ auto-generation incomplete

> The 8am job reached your calendar but couldn't reach the API (likely VPN/network
> not up yet), so the full plan wasn't generated. Your schedule is below. **Retry**
> to fill in open #actions + priorities:
>
> \`\`\`sh
> ~/.claude/hooks/daily-plan.sh --force
> \`\`\`
> In Claude Code, run it inline: \`! ~/.claude/hooks/daily-plan.sh --force\`

## Schedule
$cal

## Focus / open actions
\`\`\`tasks
not done
tags include #action
(tags include #priority) OR (due before tomorrow)
path does not include daily
sort by due
short mode
\`\`\`

## Priorities anchor
_Pending — retry above to populate (open #actions render live above)._

## Notes


<!-- daily-plan: STUB (generation failed after $attempts attempts; retry with --force) -->
STUB
  printf -- '- %s — daily plan STUB written (API unreachable after %s attempts); awaiting retry.\n' \
    "$today" "$attempts" >> "$VAULT/meta/log.md"
  echo "Wrote fallback STUB with retry instructions: $note"
fi
