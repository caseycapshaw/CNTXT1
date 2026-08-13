#!/usr/bin/env bash
# backfill-action-dates.sh — ONE-TIME best-effort backfill of created dates
# onto existing open `#action` checkboxes.
#
# For each open action line without a "➕ YYYY-MM-DD" stamp, walks
# `git log -S` to find the first commit that introduced the line, then appends
# " ➕ YYYY-MM-DD" (the Obsidian Tasks created-date marker) so
# aging-actions.sh no longer needs a git walk per line.
#
# Squashed-history guard: if every discovered date collapses to a single
# commit date (the telltale of a squashed/imported history, where git can only
# "see" one giant commit), the dates are meaningless — warn and abort instead
# of stamping every action with the same false birthday.
#
# Dry-run by default; pass --apply to actually edit files.
set -uo pipefail
cd "$(dirname "$0")/../.."   # vault root

apply=0
case "${1:-}" in
  --apply) apply=1 ;;
  -h|--help) echo "usage: $(basename "$0") [--apply]   (dry-run without --apply)"; exit 0 ;;
  "") ;;
  *) echo "unknown flag: $1 (see --help)" >&2; exit 2 ;;
esac

# ---- pass 1: discover a created date per unstamped action line -----------
plan="$(mktemp)"; dates="$(mktemp)"
trap 'rm -f "$plan" "$dates"' EXIT
while IFS=: read -r file line text; do
  [ -n "$file" ] || continue
  printf '%s' "$text" | grep -qE '➕ ?[0-9]{4}-[0-9]{2}-[0-9]{2}' && continue   # already stamped
  created="$(git log --format='%ad' --date=short --reverse -S "$text" -- "$file" 2>/dev/null | head -1)"
  [ -n "$created" ] || { printf '  skip (no git history): %s:%s\n' "$file" "$line"; continue; }
  printf '%s\t%s\t%s\t%s\n' "$file" "$line" "$created" "$text" >> "$plan"
  echo "$created" >> "$dates"
done < <(grep -rnE '^[[:space:]]*- \[ \] .*#action' --include='*.md' CONTENT index.md 2>/dev/null \
           | grep -v 'TEMPLATE' \
           | sed -E 's/^([^:]+):([0-9]+):[[:space:]]*- \[ \][[:space:]]*/\1:\2:/')

if [ ! -s "$plan" ]; then
  echo "Nothing to backfill (no unstamped open #actions with git history)."
  exit 0
fi

# ---- squashed-history guard ----------------------------------------------
n_actions="$(wc -l < "$plan" | tr -d ' ')"
n_dates="$(sort -u "$dates" | wc -l | tr -d ' ')"
if [ "$n_actions" -gt 1 ] && [ "$n_dates" -eq 1 ]; then
  echo "ABORT: all $n_actions discovered dates collapse to a single commit date" \
       "($(sort -u "$dates")) — this looks like a squashed/imported history," \
       "so the dates are meaningless. Not stamping anything."
  exit 1
fi

# ---- pass 2: stamp (or preview) ------------------------------------------
while IFS=$'\t' read -r file line created text; do
  printf '%s ' "$([ "$apply" = 1 ] && echo STAMP || echo would-stamp)"
  printf '%s:%s  ➕ %s  %s\n' "$file" "$line" "$created" "$text"
  if [ "$apply" = 1 ]; then
    # append the stamp to that exact line (BSD/GNU-portable via a temp file)
    awk -v n="$line" -v d="$created" 'NR==n{$0=$0" ➕ "d} {print}' "$file" > "$file.tmp" \
      && mv "$file.tmp" "$file"
  fi
done < "$plan"

[ "$apply" = 1 ] || echo "(dry run — re-run with --apply to write the stamps)"
exit 0
