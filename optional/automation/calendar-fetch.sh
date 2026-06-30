#!/usr/bin/env bash
# calendar-fetch.sh — fetch TODAY's macOS Calendar events into a cache file.
#
# Slow (~15s; AppleScript Calendar filtering). Run OFF the hot path — from launchd
# or by hand — NEVER inside the SessionStart hook. The hook only READS the cache.
#
# Cache file: ~/.claude/cache/calendar-today.txt
#   line 1 : ISO date (date +%F) — staleness marker the hook compares against today
#   line 2+: "HH:MM  Summary [  — location]"  (time-sorted; all-day events first)
#            or the single line "No events today."
#
# Fail-safe: on any osascript error it still writes the date line + an error marker,
# so the hook degrades gracefully instead of showing stale/yesterday data.
#
# Portable as-is — no per-user config needed. First run prompts for Calendar access.

set -uo pipefail

cache_dir="$HOME/.claude/cache"
cache="$cache_dir/calendar-today.txt"
today="$(date +%F)"
mkdir -p "$cache_dir"

# Edit skipCals below to drop noisy/auto calendars (speeds the query up).
raw="$(osascript <<'EOF' 2>/dev/null
set d0 to current date
set hours of d0 to 0
set minutes of d0 to 0
set seconds of d0 to 0
set d1 to d0 + (1 * days)
set out to ""
set skipCals to {"Holidays in United States", "US Holidays", "Birthdays", "Siri Suggestions"}
tell application "Calendar"
  repeat with c in calendars
    if (name of c) is in skipCals then
      -- skip noisy/auto calendars
    else
    set evs to (every event of c whose start date ≥ d0 and start date < d1)
    repeat with e in evs
      set sd to start date of e
      set theSummary to summary of e
      set loc to ""
      try
        if location of e is not missing value then set loc to location of e
      end try
      set isAllDay to false
      try
        set isAllDay to allday event of e
      end try
      if isAllDay then
        set sortkey to "0000"
        set tstr to "all-day"
      else
        set hpad to text -2 thru -1 of ("0" & (hours of sd))
        set mpad to text -2 thru -1 of ("0" & (minutes of sd))
        set sortkey to hpad & mpad
        set tstr to hpad & ":" & mpad
      end if
      set disp to tstr & "  " & theSummary
      if loc is not "" then set disp to disp & "  — " & loc
      set out to out & sortkey & tab & disp & linefeed
    end repeat
    end if
  end repeat
end tell
return out
EOF
)"
status=$?

# osascript failed (e.g. TCC/Automation denied) — record it, keep the date line.
if [ "$status" -ne 0 ]; then
  { echo "$today"; echo "(calendar fetch error — osascript exit $status)"; } > "$cache"
  exit 0
fi

if [ -n "$raw" ]; then
  body="$(printf '%s' "$raw" | sort -u | cut -f2-)"
else
  body="No events today."
fi

{
  echo "$today"
  printf '%s\n' "$body"
} > "$cache"
