#!/usr/bin/env bash
# audit-area-reviews.sh — the GTD area/horizon review-cadence audit.
# Rule: every area (02 Areas/, 02 Areas/Assets/) and horizon (01 Horizons/) carries
# review:+reviewed: frontmatter, and reviewed: is within its cadence window
# (weekly=7d, monthly=31d, quarterly=92d, yearly=366d). Areas don't owe next
# actions (that's projects — audit-project-next-actions.sh); they owe a
# recent, honest look ([[Review an Area]]).
# Output: one line per note (silence must be distinguishable from
# not-checked). Exit 0 = all current, 1 = overdue/missing (lint check 12
# surfaces a non-zero exit as WARN, not FAIL — an overdue review is a nudge,
# not a broken vault).
set -uo pipefail
_BIN="$(cd "$(dirname "$0")" && pwd)"
cd "$_BIN/../.."   # vault root
# shellcheck source=kb-folders.sh
. "$_BIN/kb-folders.sh"
today_s="$(date +%s)"
overdue=0 checked=0

fm() { awk -v k="$2" '/^---$/{c++; next} c==1 && $0 ~ "^"k":"{sub("^"k":[[:space:]]*",""); print; exit} c==2{exit}' "$1"; }

for f in "$KB_AREAS"/*.md "$KB_AREAS"/Assets/*.md "$KB_HORIZONS"/*.md "$KB_HORIZON_GOALS/index.md"; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*) continue ;; esac
  # Child goal notes have no review: — only the H3 index does.
  if [ "$f" != "$KB_HORIZON_GOALS/index.md" ]; then
    case "$f" in */index.md) continue ;; esac
  fi
  checked=$((checked+1))
  review="$(fm "$f" review)"; reviewed="$(fm "$f" reviewed)"
  if [ -z "$review" ] || [ -z "$reviewed" ]; then
    printf 'FAIL  %s — missing review:/reviewed: frontmatter\n' "$f"; overdue=$((overdue+1)); continue
  fi
  case "$review" in
    weekly) win=7 ;; monthly) win=31 ;; quarterly) win=92 ;; yearly) win=366 ;;
    *) printf 'FAIL  %s — unknown review cadence %s\n' "$f" "$review"; overdue=$((overdue+1)); continue ;;
  esac
  rev_s="$(date -j -f '%Y-%m-%d' "$reviewed" +%s 2>/dev/null || date -d "$reviewed" +%s 2>/dev/null || echo 0)"
  age=$(( (today_s - rev_s) / 86400 ))
  if [ "$age" -le "$win" ]; then
    printf 'PASS  %s (reviewed %s, %sd ago, cadence %s)\n' "$f" "$reviewed" "$age" "$review"
  else
    printf 'OVERDUE  %s — reviewed %s (%sd ago > %sd %s window)\n' "$f" "$reviewed" "$age" "$win" "$review"
    overdue=$((overdue+1))
  fi
done

echo
if [ "$overdue" -eq 0 ]; then
  echo "AREA-REVIEW AUDIT: green ($checked areas/horizons all within cadence)"
  exit 0
else
  echo "AREA-REVIEW AUDIT: $overdue of $checked areas/horizons overdue or misconfigured — run Review an Area"
  exit 1
fi
