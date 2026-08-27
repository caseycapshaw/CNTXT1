#!/usr/bin/env bash
# audit-initiative-next-actions.sh — the per-initiative next-action audit (GTD).
# Rule: every ACTIVE initiative carries >=1 open next action (`- [ ] ... #action`).
# An active workstream with no open action is stalled-by-definition — it needs a
# Now & next rewrite, a new action, `status: paused`, or a close.
# Paused/done initiatives are exempt (paused = deliberately no current action).
#
# Output: one explicit line per active initiative (silence must be
# distinguishable from not-checked). Exit 0 = all covered, 1 = violations.
set -uo pipefail
cd "$(dirname "$0")/../.."   # vault root

viol=0 checked=0
for f in Knowledge/Initiatives/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*/index.md) continue ;; esac
  status="$(awk '/^---$/{c++; next} c==1 && /^status:/{sub(/^status:[[:space:]]*/,""); sub(/[[:space:]]+#.*$/,""); print; exit} c==2{exit}' "$f")"
  [ "$status" = "active" ] || continue
  checked=$((checked+1))
  if grep -qE '^\s*- \[ \] .*#action' "$f"; then
    printf 'PASS  %s (has an open next action)\n' "$f"
  else
    printf 'FAIL  %s — active but no open #action (rewrite Now & next, add an action, pause, or close)\n' "$f"
    viol=$((viol+1))
  fi
done

echo
if [ "$viol" -eq 0 ]; then
  echo "NEXT-ACTION AUDIT: green ($checked active initiatives, all with an open next action)"
  exit 0
else
  echo "NEXT-ACTION AUDIT: $viol of $checked active initiatives lack an open next action"
  exit 1
fi
