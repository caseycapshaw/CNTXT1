#!/usr/bin/env bash
# stale-initiatives.sh — list active initiatives overdue for a check-in.
# An initiative is stale when its frontmatter `updated:` date is older than
# the threshold (default 14 days; override with --days N). Archive/ and
# TEMPLATE files are excluded. Exit 0 always — this is a signal, not a gate.
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

# Epoch seconds for an ISO date, portable across BSD (macOS) and GNU date.
epoch() {
  date -j -f '%Y-%m-%d' "$1" '+%s' 2>/dev/null || date -d "$1" '+%s' 2>/dev/null
}
now="$(date '+%s')"

count=0
for f in CONTENT/Initiatives/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*) continue ;; esac
  status="$(awk '/^---$/{c++; next} c==1 && /^status:/{sub(/^status:[[:space:]]*/,""); sub(/[[:space:]]*#.*$/,""); print; exit} c==2{exit}' "$f")"
  [ "$status" = "active" ] || continue
  updated="$(awk '/^---$/{c++; next} c==1 && /^updated:/{sub(/^updated:[[:space:]]*/,""); sub(/[[:space:]]*#.*$/,""); print; exit} c==2{exit}' "$f")"
  slug="$(basename "$f" .md)"
  if ! printf '%s' "$updated" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
    printf '%s — no parsable updated: date (%s)\n' "[[$slug]]" "${updated:-missing}"
    count=$((count + 1))
    continue
  fi
  then_s="$(epoch "$updated")" || continue
  age=$(( (now - then_s) / 86400 ))
  if [ "$age" -gt "$days" ]; then
    printf '%s — updated %s (%s days ago)\n' "[[$slug]]" "$updated" "$age"
    count=$((count + 1))
  fi
done

[ "$count" -eq 0 ] && echo "(no active initiatives older than ${days} days)"
exit 0
