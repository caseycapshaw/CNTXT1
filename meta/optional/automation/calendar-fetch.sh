#!/usr/bin/env bash
# calendar-fetch.sh — fetch TODAY's Google Calendar events (via `gws`) into a cache file.
#
# Uses the `gws` CLI (https://github.com/googleworkspace/cli) against the
# signed-in account's primary Google Calendar — NOT the local macOS Calendar app.
# Run OFF the hot path — from launchd or by hand — NEVER inside the SessionStart
# hook. The hook only READS the cache.
#
# Cache file: ~/.claude/cache/calendar-today.txt
#   line 1 : ISO date (date +%F) — staleness marker the hook compares against today
#   line 2+: "HH:MM  Summary [  — location]"  (time-sorted; all-day events first)
#            or the single line "No events today."
#
# Fail-safe: on any gws/auth error it still writes the date line + an error marker,
# so the hook degrades gracefully instead of showing stale/yesterday data.
#
# Scope note: only the signed-in account's "primary" calendar is queried — auto
# calendars like "Holidays in United States" and any secondary/work calendars
# are intentionally excluded. Edit calendarId below to add others.
#
# Requires: `gws` installed and authenticated (`gws auth login`). See
# `gws auth status`.

set -uo pipefail

# Homebrew isn't on launchd's PATH by default.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

cache_dir="$HOME/.claude/cache"
cache="$cache_dir/calendar-today.txt"
today="$(date +%F)"
mkdir -p "$cache_dir"

if ! command -v gws >/dev/null 2>&1; then
  { echo "$today"; echo "(calendar fetch error — gws not installed)"; } > "$cache"
  exit 0
fi

# Local-time RFC3339 bounds for [today 00:00, tomorrow 00:00).
tz="$(date +%z)"                       # e.g. -0600
tz_colon="${tz:0:3}:${tz:3:2}"         # e.g. -06:00
tmin="${today}T00:00:00${tz_colon}"
tmax="$(date -v+1d +%F)T00:00:00${tz_colon}"

params="$(jq -nc --arg tmin "$tmin" --arg tmax "$tmax" \
  '{calendarId: "primary", timeMin: $tmin, timeMax: $tmax, singleEvents: true, orderBy: "startTime"}')"

raw="$(gws calendar events list --params "$params" 2>/dev/null)"
status=$?

# gws failed (e.g. token expired, network down) — record it, keep the date line.
if [ "$status" -ne 0 ] || [ -z "$raw" ] || ! printf '%s' "$raw" | jq -e '.items' >/dev/null 2>&1; then
  { echo "$today"; echo "(calendar fetch error — gws exit $status)"; } > "$cache"
  exit 0
fi

body="$(printf '%s' "$raw" | jq -r '
  .items[]?
  | select(.status != "cancelled")
  | (.summary // "(no title)") as $summary
  | (.location // "") as $loc
  | if .start.dateTime then
      (.start.dateTime[11:16]) as $t
      | ($t | gsub(":";"")) + "\t" + $t + "  " + $summary + (if $loc != "" then "  — " + $loc else "" end)
    else
      "0000" + "\t" + "all-day" + "  " + $summary + (if $loc != "" then "  — " + $loc else "" end)
    end
' | sort -u | cut -f2-)"

[ -z "$body" ] && body="No events today."

{
  echo "$today"
  printf '%s\n' "$body"
} > "$cache"
