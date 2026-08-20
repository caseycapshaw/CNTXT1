#!/usr/bin/env bash
# lint-delta.sh — scheduled-run wrapper for lint.sh that alarms on the DELTA.
#
# Rationale: lint.sh exits 1 on ANY finding, so a standing known issue makes a
# scheduled job permanently red — and a permanently-red check is an invisible
# check (a clean vault becomes indistinguishable from a regression). The useful
# scheduled signal is the delta: exit 0 when the finding count is flat or
# falling, 1 only on an increase. Interactive runs should keep using lint.sh
# directly (full detail, hard gate).
#
# State: SYSTEM/.cache/lint-delta-state (gitignored; "could not parse" is
# itself treated as failure — silence must be distinguishable from not-checked).
set -uo pipefail
cd "$(dirname "$0")/../.."   # vault root

state_dir="SYSTEM/.cache"
state_file="$state_dir/lint-delta-state"
mkdir -p "$state_dir"

out="$(./SYSTEM/bin/lint.sh 2>&1)"
count="$(printf '%s\n' "$out" | grep -c '^FAIL')"
if ! printf '%s' "$count" | grep -qE '^[0-9]+$'; then
  echo "LINT-DELTA: could not parse a finding count — treating as failure"
  printf '%s\n' "$out" | tail -20
  exit 1
fi

prev=""
[ -f "$state_file" ] && prev="$(cat "$state_file")"
printf '%s\n' "$count" > "$state_file"

if [ -z "$prev" ]; then
  echo "LINT-DELTA: baseline seeded at $count finding(s) (first run — no delta to judge)"
  printf '%s\n' "$out" | grep '^FAIL' || true
  exit 0
fi

if [ "$count" -gt "$prev" ]; then
  echo "LINT-DELTA: REGRESSION — findings $prev -> $count"
  printf '%s\n' "$out" | grep '^FAIL' || true
  exit 1
fi
echo "LINT-DELTA: ok — findings $prev -> $count (flat or falling)"
exit 0
