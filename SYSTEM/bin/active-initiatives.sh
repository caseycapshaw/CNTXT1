#!/usr/bin/env bash
# active-initiatives.sh — list every active initiative + its next open action.
# Scans CONTENT/Initiatives/*.md (archive/ and TEMPLATE files excluded) for
# frontmatter `status: active`, then prints each note's first open `#action`
# checkbox (or "(no open actions)" if none). Feeds the daily-plan rollup.
# Exit 0 always (an empty list is not an error).
set -uo pipefail
cd "$(dirname "$0")/../.."   # vault root

count=0
for f in CONTENT/Initiatives/*.md; do
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

[ "$count" -eq 0 ] && echo "(no active initiatives)"
exit 0
