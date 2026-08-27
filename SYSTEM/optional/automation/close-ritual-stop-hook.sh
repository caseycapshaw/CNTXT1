#!/usr/bin/env bash
# close-ritual-stop-hook.sh — Claude Code Stop-hook ACCELERANT for the close
# ritual (Knowledge/Skills/DO/Close a Session.md). Tier-3 per the portability
# rule (Knowledge/Skills/RULE/Keep Machinery Vendor-Portable.md): it only
# *reminds* — the ritual itself is carried by the skill + the 6pm
# daily-summary backstop, so removing this hook costs latency, never
# correctness.
#
# Behavior: fires when Claude stops; reminds AT MOST ONCE PER SESSION, and
# only when the vault working tree is dirty (i.e. the session probably wrote
# something worth closing over). Never blocks, never fails the stop.
set -u
vault="$(cd "$(dirname "$0")/../../.." && pwd)"

# session_id from the hook's stdin JSON (stdlib python3 — no jq dependency)
session_id="$(python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("session_id",""))
except Exception: print("")' 2>/dev/null)"
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
