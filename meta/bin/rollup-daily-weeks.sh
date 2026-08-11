#!/usr/bin/env bash
# rollup-daily-weeks.sh — archive past daily notes into weekly folders.
# daily/YYYY-MM-DD.md older than the current week moves into a folder named
# for its week's Monday: daily/YYYY-MM-DD/ (e.g. 2026-07-13/ holds Jul 13-19).
# Current-week notes stay loose so the day-to-day workflow
# (daily-plan/daily-summary appends, Obsidian quick-open) is untouched.
# Obsidian wikilinks resolve by filename, so moving files breaks nothing.
# Idempotent + deterministic — safe to run nightly (e.g. from a snapshot job).
set -euo pipefail
VAULT="${VAULT:-$(cd "$(dirname "$0")/../.." && pwd)}"   # meta/bin -> vault root
DAILY="$VAULT/daily"
[ -d "$DAILY" ] || exit 0

# Monday of a given YYYY-MM-DD (BSD date on macOS, GNU fallback)
monday_of() {
  local d="$1" u epoch
  if u="$(date -j -f %Y-%m-%d "$d" +%u 2>/dev/null)"; then
    epoch="$(date -j -f %Y-%m-%d "$d" +%s)"
    date -j -v-"$((u - 1))"d -r "$epoch" +%F
  else
    u="$(date -d "$d" +%u)" && date -d "$d -$((u - 1)) days" +%F
  fi
}

current_monday="$(monday_of "$(date +%F)")"
moved=0
for f in "$DAILY"/????-??-??.md; do
  [ -e "$f" ] || continue
  base="$(basename "$f" .md)"
  week="$(monday_of "$base")" || continue
  [ "$week" = "$current_monday" ] && continue
  mkdir -p "$DAILY/$week"
  mv "$f" "$DAILY/$week/"
  moved=$((moved + 1))
done
echo "rollup-daily-weeks: current week starts $current_monday — moved $moved note(s)."
