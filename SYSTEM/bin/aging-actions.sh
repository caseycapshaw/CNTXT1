#!/usr/bin/env bash
# aging-actions.sh — list open `#action` checkboxes older than a threshold.
# For each open action line found in the content folders + index.md:
#   - an explicit "➕ YYYY-MM-DD" stamp on the line (see
#     backfill-action-dates.sh) is the authoritative created date — its age
#     is printed as "NNd".
#   - with NO ➕ stamp, age is genuinely UNKNOWN — SYSTEM/bin/actions.py's
#     census does not guess an age from git blame or an embedded date (that
#     guess undercounts staleness when many open actions carry no date). This
#     script keeps the git-log first-commit date as a best-effort ESTIMATE for
#     a human skimming the terminal — printed with a `~` prefix so it's never
#     confused with a real ➕ stamp — and tallies both counts separately in the
#     summary line. Neither this script nor actions.py ever writes a ➕ stamp;
#     that's backfill-action-dates.sh's job.
# Default threshold 14 days; override with --days N. Exit 0 always — this is
# a signal, not a gate.
set -uo pipefail
_BIN="$(cd "$(dirname "$0")" && pwd)"
cd "$_BIN/../.."   # vault root
# shellcheck source=kb-folders.sh
. "$_BIN/kb-folders.sh"

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
stamped=0
unknown=0
while IFS=: read -r file line text; do
  [ -n "$file" ] || continue
  # authoritative: explicit ➕ created-date stamp on the line
  created="$(printf '%s' "$text" | grep -oE '➕ ?[0-9]{4}-[0-9]{2}-[0-9]{2}' | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)"
  if [ -n "$created" ]; then
    stamped=$((stamped + 1))
    then_s="$(epoch "$created")" || continue
    age=$(( (now - then_s) / 86400 ))
    if [ "$age" -gt "$days" ]; then
      printf '%3sd   %s:%s  %s\n' "$age" "$file" "$line" "$text"
      count=$((count + 1))
    fi
    continue
  fi
  # no ➕ stamp: genuinely unknown age. Best-effort git-blame ESTIMATE only,
  # never treated as a real created date — prefixed "~" and tallied apart.
  unknown=$((unknown + 1))
  estimate="$(git log --format='%ad' --date=short --reverse -S "$text" -- "$file" 2>/dev/null | head -1)"
  if [ -z "$estimate" ]; then
    printf '??    %s:%s  %s\n' "$file" "$line" "$text"
    continue
  fi
  then_s="$(epoch "$estimate")" || continue
  age=$(( (now - then_s) / 86400 ))
  if [ "$age" -gt "$days" ]; then
    printf '~%3sd  %s:%s  %s\n' "$age" "$file" "$line" "$text"
  fi
done < <(grep -rnE '^[[:space:]]*- \[ \] .*#action' --include='*.md' "$KB_CONCEPTS" "$KB_PROJECTS" "$KB_AREAS" "$KB_HORIZONS" "$KB_PEOPLE" Skills Agents index.md 2>/dev/null \
           | grep -v 'TEMPLATE' \
           | sed -E 's/^([^:]+):([0-9]+):[[:space:]]*- \[ \][[:space:]]*/\1:\2:/')

echo
echo "$stamped ➕-stamped (exact age) · $unknown unknown age (no ➕ stamp — ~estimates above are git-blame best-effort, not authoritative)"
[ "$count" -eq 0 ] && echo "(no ➕-stamped open #actions older than ${days} days)"
exit 0
