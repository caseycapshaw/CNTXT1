#!/usr/bin/env bash
# rotate_log.sh — keep SYSTEM/log.md to the current month.
#
# SYSTEM/log.md is append-only and grows every session — anything that
# "reads the log" ends up one bad grep from blowing a context window. This moves every entry line (`- YYYY-MM-DD …`)
# dated before the current month into SYSTEM/log/YYYY-MM.md (append, in
# order), leaving the header + current-month lines in place. Idempotent —
# safe to run nightly (daily-summary.sh) or by hand. Appenders keep writing
# to SYSTEM/log.md unchanged; nothing is ever deleted, only moved.
#
# Usage: SYSTEM/bin/rotate_log.sh [--dry-run]
set -euo pipefail
VAULT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$VAULT/SYSTEM/log.md"
ARCH="$VAULT/SYSTEM/log"
cur="$(date +%Y-%m)"
dry=0; [ "${1:-}" = "--dry-run" ] && dry=1
[ -f "$LOG" ] || { echo "rotate_log: no $LOG"; exit 0; }
mkdir -p "$ARCH"

months="$(grep -oE '^(- )?20[0-9]{2}-[0-9]{2}' "$LOG" | sed 's/^- //' | sort -u | awk -v c="$cur" '$1 < c')"
[ -z "$months" ] && { echo "rotate_log: nothing to rotate (current month $cur)"; exit 0; }

tmp="$(mktemp)"; cp "$LOG" "$tmp"
for m in $months; do
  n="$(grep -cE "^(- )?$m-[0-9]{2}" "$tmp" || true)"
  [ "$n" -eq 0 ] && continue
  if [ $dry -eq 1 ]; then echo "would move $n lines dated $m → SYSTEM/log/$m.md"; continue; fi
  if [ ! -f "$ARCH/$m.md" ]; then
    printf '# Log — %s (rotated from SYSTEM/log.md)\n\nAppend-only archive of that month'"'"'s entries, moved verbatim by `SYSTEM/bin/rotate_log.sh`. The live log (current month) is `SYSTEM/log.md`.\n\n' "$m" > "$ARCH/$m.md"
  fi
  grep -E "^(- )?$m-[0-9]{2}" "$tmp" >> "$ARCH/$m.md"
  grep -vE "^(- )?$m-[0-9]{2}" "$tmp" > "$tmp.new" && mv "$tmp.new" "$tmp"
  echo "rotated $n lines dated $m → SYSTEM/log/$m.md"
done
if [ $dry -eq 0 ]; then
  # collapse runs of blank lines left behind, keep the header
  awk 'NF{blank=0; print; next} !blank{print; blank=1}' "$tmp" > "$LOG"
fi
rm -f "$tmp" "$tmp.new" 2>/dev/null || true
