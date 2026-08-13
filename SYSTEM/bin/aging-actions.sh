#!/usr/bin/env bash
# aging-actions.sh — list open `#action` checkboxes older than a threshold.
# For each open action line found in CONTENT/ + index.md, the created date is:
#   1. an explicit "➕ YYYY-MM-DD" stamp on the line (see
#      backfill-action-dates.sh), if present; otherwise
#   2. the author date of the first commit that introduced the line
#      (`git log -S` on the exact line text — best-effort, slow-ish).
# Default threshold 14 days; override with --days N. Exit 0 always — this is
# a signal, not a gate.
set -uo pipefail
cd "$(dirname "$0")/../.."   # vault root

days=14
while [ $# -gt 0 ]; do
  case "$1" in
    --days) days="${2:?--days needs a number}"; shift 2 ;;
    -h|--help) echo "usage: $(basename "$0") [--days N]   (default: 14)"; exit 0 ;;
    *) echo "unknown flag: $1 (see --help)" >&2; exit 2 ;;
  esac
done

epoch() {
  date -j -f '%Y-%m-%d' "$1" '+%s' 2>/dev/null || date -d "$1" '+%s' 2>/dev/null
}
now="$(date '+%s')"

count=0
while IFS=: read -r file line text; do
  [ -n "$file" ] || continue
  # 1. explicit created-date stamp on the line
  created="$(printf '%s' "$text" | grep -oE '➕ ?[0-9]{4}-[0-9]{2}-[0-9]{2}' | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)"
  # 2. fall back to the first commit that introduced this exact line
  if [ -z "$created" ]; then
    created="$(git log --format='%ad' --date=short --reverse -S "$text" -- "$file" 2>/dev/null | head -1)"
  fi
  if [ -z "$created" ]; then
    printf '??  %s:%s  %s\n' "$file" "$line" "$text"
    continue
  fi
  then_s="$(epoch "$created")" || continue
  age=$(( (now - then_s) / 86400 ))
  if [ "$age" -gt "$days" ]; then
    printf '%3sd  %s:%s  %s\n' "$age" "$file" "$line" "$text"
    count=$((count + 1))
  fi
done < <(grep -rnE '^[[:space:]]*- \[ \] .*#action' --include='*.md' CONTENT index.md 2>/dev/null \
           | grep -v 'TEMPLATE' \
           | sed -E 's/^([^:]+):([0-9]+):[[:space:]]*- \[ \][[:space:]]*/\1:\2:/')

[ "$count" -eq 0 ] && echo "(no open #actions older than ${days} days)"
exit 0
