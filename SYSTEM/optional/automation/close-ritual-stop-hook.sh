#!/usr/bin/env bash
# close-ritual-stop-hook.sh — Claude Code Stop-hook ACCELERANT for the close
# ritual (Skills/DO/Close a Session.md). Tier-3 per the portability
# rule (Skills/RULE/Keep Machinery Vendor-Portable.md): it only
# *reminds* — the ritual itself is carried by the skill + the 6pm
# daily-summary backstop, so removing this hook costs latency, never
# correctness.
#
# Default install: registered as a PROJECT Stop hook in `.claude/settings.json`.
#
# Behavior: fires when the agent stops; reminds AT MOST ONCE PER SESSION, and
# only when the vault working tree is dirty (i.e. the session probably wrote
# something worth closing over). Never blocks, never fails the stop.
set -u
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR/.git" ]; then
  vault="$CLAUDE_PROJECT_DIR"
else
  vault="$(cd "$(dirname "$0")/../../.." && pwd)"
fi

# session id from the hook's stdin JSON (Claude: session_id; Grok: sessionId)
session_id="$(python3 -c 'import json,sys
try:
    d=json.load(sys.stdin)
    print(d.get("session_id") or d.get("sessionId") or "")
except Exception:
    print("")' 2>/dev/null)"
[ -z "$session_id" ] && exit 0

sentinel="${TMPDIR:-/tmp}/close-ritual-reminded-${session_id}"
[ -e "$sentinel" ] && exit 0

# Only remind when the vault has uncommitted changes.
if ! git -C "$vault" status --porcelain 2>/dev/null | grep -q .; then
  exit 0
fi

touch "$sentinel"
printf '{"systemMessage": "Vault has uncommitted session work — say \\"close\\" when wrapping up to run the close ritual (log + decisions ledger + digest check)."}\n'
exit 0
