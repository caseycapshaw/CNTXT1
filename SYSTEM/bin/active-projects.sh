#!/usr/bin/env bash
# active-projects.sh — list every active project + its next open action.
# Scans 03 Projects/*.md (archive/ and TEMPLATE files excluded) for
# frontmatter `status: active`, then prints each note's first open `#action`
# checkbox (or "(no open actions)" if none). Feeds the daily-plan rollup.
# Exit 0 always (an empty list is not an error).
set -uo pipefail
_BIN="$(cd "$(dirname "$0")" && pwd)"
cd "$_BIN/../.."   # vault root
# shellcheck source=kb-folders.sh
. "$_BIN/kb-folders.sh"

count=0
for f in "$KB_PROJECTS"/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*) continue ;; esac
  # frontmatter status: active (first block only; strip trailing comment)
  status="$(awk '/^---$/{c++; next} c==1 && /^status:/{sub(/^status:[[:space:]]*/,""); sub(/[[:space:]]*#.*$/,""); print; exit} c==2{exit}' "$f")"
  [ "$status" = "active" ] || continue
  count=$((count + 1))
  slug="$(basename "$f" .md)"
  next="$(grep -m1 -E '^[[:space:]]*- \[ \] .*#action' "$f" | sed -E 's/^[[:space:]]*- \[ \][[:space:]]*//')"
  printf '%s\n' "[[$slug]]"
  if [ -n "$next" ]; then
    printf '  next: %s\n' "$next"
  else
    printf '  next: (no open actions)\n'
  fi
done

[ "$count" -eq 0 ] && echo "(no active projects)"
exit 0
