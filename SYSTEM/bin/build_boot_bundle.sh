#!/usr/bin/env bash
# build_boot_bundle.sh — the KB's boot sequence: one generated orientation
# bundle for the start of every agent session, identical on every machine.
#
# Emits to stdout (plain text, ≤ ~6k tokens):
#   HOST        which machine this session runs on + the scheduled jobs live here
#   POINTER     what the vault is and the rules that matter every session
#   TODAY       plan-note pointer + calendar (from the cache, never live)
#   MAP         index.md Quick-map skeleton only (not the rich sections)
#   INBOX       un-triaged root items
#   PRIORITY    open "#action #priority" lines with their home note
#   LOG TAIL    last 5 SYSTEM/log.md lines
#   KB STATS    the last kb_stats.py digest line, if present
#
# Called by the SessionStart hook (SYSTEM/optional/automation/sessionstart-hook.sh,
# registered in .claude/settings.json). Vault-generic: resolves the vault from
# its own location. Fail-safe: every block is best-effort; a missing input
# degrades, never errors. Budget check: `build_boot_bundle.sh --size` prints
# bytes + ~tokens and exits non-zero if over BUDGET_BYTES (kb_stats.py reads
# this for its boot-cost gauge). Documented in SYSTEM/SCHEMA.md § Boot bundle.
#
# Optional configuration (all env vars, all with neutral defaults):
#   VAULT                vault root (default: resolved from this script's location)
#   BUDGET_BYTES         size budget for --size (default 24000 ≈ 6k tokens)
#   CAL_CACHE            calendar cache file (default: SYSTEM/.cache/calendar-today.txt,
#                        else ~/.claude/cache/calendar-today.txt — what calendar-fetch.sh writes)
#   KB_LAUNCHD_PREFIX    macOS: launchd label prefix to list as "jobs on this machine"
#                        (default "com.example." — set to your own reverse-DNS prefix)
#   KB_TIMER_PREFIX      Linux: systemd timer unit prefix to list (default "kb-")
#   KB_PEERS             space-separated ~/.ssh/config Host names to list as reachable
#                        peers (default: none — nothing is read from ssh config unless listed)

set +e
VAULT="${VAULT:-$(cd "$(dirname "$0")/../.." && pwd)}"
BUDGET_BYTES="${BUDGET_BYTES:-24000}"   # ≈ 6k tokens at 4 bytes/token
KB_LAUNCHD_PREFIX="${KB_LAUNCHD_PREFIX:-com.example.}"
KB_TIMER_PREFIX="${KB_TIMER_PREFIX:-kb-}"
KB_PEERS="${KB_PEERS:-}"
if [ -z "${CAL_CACHE:-}" ]; then
  CAL_CACHE="$VAULT/SYSTEM/.cache/calendar-today.txt"
  [ -s "$CAL_CACHE" ] || CAL_CACHE="$HOME/.claude/cache/calendar-today.txt"
fi
today="$(date +%F 2>/dev/null)"

# ---------- HOST ----------
host="$(hostname -s 2>/dev/null || hostname)"
uname_s="$(uname -s 2>/dev/null)"
if [ "$uname_s" = "Linux" ]; then
  model="Linux"
  # Scheduled work on Linux is systemd timers named ${KB_TIMER_PREFIX}*.
  # `systemctl list-timers` needs the unit suffix; strip it and dedupe so this
  # reads like the macOS list.
  jobs="$(systemctl list-timers "${KB_TIMER_PREFIX}*" --all --no-legend --no-pager 2>/dev/null \
          | grep -oE "${KB_TIMER_PREFIX}[A-Za-z0-9_-]+\.timer" | sed "s/\.timer\$//; s/^${KB_TIMER_PREFIX}//" \
          | sort -u | tr '\n' ' ')"
  jobs_label="systemd timers (${KB_TIMER_PREFIX}*) live on this machine"
else
  model="$(sysctl -n hw.model 2>/dev/null)"
  prefix_re="$(printf '%s' "$KB_LAUNCHD_PREFIX" | sed 's/\./\\./g')"
  jobs="$(launchctl list 2>/dev/null | grep -oE "${prefix_re}[A-Za-z0-9_-]+" | sort -u | sed "s/^${prefix_re}//" | tr '\n' ' ')"
  jobs_label="launchd jobs (${KB_LAUNCHD_PREFIX}*) live on this machine"
fi
peers=""
for h in $KB_PEERS; do
  grep -qE "^Host[[:space:]]+$h(\$|[[:space:]])" "$HOME/.ssh/config" 2>/dev/null && peers="$peers ssh $h ·"
done
peers="${peers% ·}"
host_block="=== HOST ===
This session runs on: ${host} (${model:-unknown model}). Verify with \`hostname\` before any machine-specific or SSH-trust action — the vault path can be identical on several machines, so the path alone never tells you where you are.
${jobs_label}: ${jobs:-none detected}
Other machines reachable from here:${peers:- none configured (set KB_PEERS to list ~/.ssh/config Host names)}"

# ---------- POINTER ----------
pointer="=== VAULT ===
A personal knowledge base (Karpathy \"knowledge-base-as-compiler\" method) lives at $VAULT — your durable project memory. Session rules are in $VAULT/AGENTS.md (auto-loaded); the full schema is $VAULT/SYSTEM/SCHEMA.md — read it when a task touches conventions, structure, or compilation, not by reflex. The map, inbox, priorities, and recent log are inlined below — do NOT re-read index.md at start; open it only to navigate to a section you need.
The vault ROOT is the inbox: anything there other than the pinned anchors (README.md, index.md, Actions.md, CLAUDE.md, AGENTS.md) is un-triaged — offer to file it into raw/ and compile.
Read and write $VAULT using absolute paths regardless of the current working directory."

# ---------- TODAY ----------
today_block="=== TODAY (${today}) ==="
plan_note="$VAULT/00 daily/$today.md"
if [ -f "$plan_note" ]; then
  if grep -q "daily-plan: STUB" "$plan_note" 2>/dev/null; then
    today_block="$today_block
Plan note $plan_note is a STUB (the morning job reached the calendar but not the API). Offer to regenerate: $VAULT/SYSTEM/optional/automation/daily-plan.sh --force"
  else
    today_block="$today_block
Plan note: $plan_note — schedule, open #actions, priorities. Read it first for day-level context."
  fi
else
  today_block="$today_block
No plan note yet for today."
fi
if [ -f "$CAL_CACHE" ]; then
  cal_date="$(head -n 1 "$CAL_CACHE" 2>/dev/null)"
  if [ "$cal_date" = "$today" ]; then
    today_block="$today_block
Calendar:
$(tail -n +2 "$CAL_CACHE" 2>/dev/null)"
  else
    today_block="$today_block
Calendar: cache stale (dated ${cal_date:-unknown}; refreshed by the morning job)."
  fi
fi

# ---------- MAP (Quick-map skeleton only) ----------
map=""
if [ -f "$VAULT/index.md" ]; then
  # Everything up to the first H2 that is not "## Quick map" (i.e. the
  # Start-here callout + the skeleton), never the rich sections below it.
  # Same cut as lint check 8 (injection budget) and check 18 (no status log).
  map="$(awk '/^## / && !/^## Quick map/ {exit} {print}' "$VAULT/index.md" 2>/dev/null)"
fi
map_block="=== MAP ($VAULT/index.md — Quick-map skeleton; rich sections live in the file) ===
${map:-index.md missing}"

# ---------- INBOX ----------
# Root entries other than the pinned anchors, structural folders and kit/tooling
# files. Mirror of SYSTEM/bin/lint.sh check 1 (the single source of truth).
inbox_items=""
while IFS= read -r entry; do
  name="$(basename "$entry")"
  case "$name" in
    README.md|index.md|Actions.md|CLAUDE.md|AGENTS.md) continue ;;
    "00 daily"|"01 Horizons"|"02 Areas"|"03 Projects"|"04 People"|"05 concepts"|SYSTEM|Agents|raw|Skills|attachments|docs|excalidraw) continue ;;
    setup.md|LICENSE|MIGRATING.md|CHANGELOG.md) continue ;;
    pyproject.toml|uv.lock|"Upstream kit updates (pending).md") continue ;;
    .*) continue ;;
  esac
  [ -d "$entry" ] && inbox_items="${inbox_items}- ${name}/ (directory)
" || inbox_items="${inbox_items}- ${name}
"
done < <(find "$VAULT" -maxdepth 1 -mindepth 1 2>/dev/null | sort)
if [ -n "$inbox_items" ]; then
  inbox_block="=== INBOX — un-triaged root items (offer to file into raw/ and compile) ===
${inbox_items}"
else
  inbox_block="=== INBOX — empty ==="
fi

# ---------- PRIORITY ACTIONS ----------
prio="$(grep -rnE '^\s*- \[ \] .*#action' --include='*.md' \
        --exclude-dir=SYSTEM --exclude-dir=Skills --exclude-dir=.claude --exclude-dir=raw --exclude-dir=docs \
        --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.obsidian --exclude-dir=node_modules \
        --exclude=Actions.md --exclude='*TEMPLATE.md' \
        "$VAULT" 2>/dev/null | grep '#priority' \
      | sed -E "s#^$VAULT/##; s#^([^:]+):[0-9]+:[[:space:]]*- \[ \] (.*)\$#- \2  ← \1#" \
      | sed -E 's/ #(action|priority)( |$)/\2/g' | head -n 15)"
prio_count="$(printf '%s' "$prio" | grep -c . 2>/dev/null)"
prio_block="=== PRIORITY (open #action #priority — ${prio_count:-0}; every open action: $VAULT/Actions.md) ===
${prio:-none flagged}"

# ---------- LOG TAIL ----------
logtail="$(tail -n 5 "$VAULT/SYSTEM/log.md" 2>/dev/null | cut -c1-300)"
log_block="=== LOG TAIL (last 5 of $VAULT/SYSTEM/log.md) ===
${logtail:-no log}"

# ---------- KB STATS (last kb_stats.py run, one line) ----------
stats_block=""
if [ -f "$VAULT/SYSTEM/stats/latest.txt" ]; then
  stats_block="=== KB STATS (SYSTEM/kb-stats.md) ===
$(head -c 400 "$VAULT/SYSTEM/stats/latest.txt")"
fi

# ---------- ASSEMBLE ----------
bundle="$host_block

$pointer

$today_block

$map_block

$inbox_block

$prio_block

$log_block

$stats_block"

if [ "${1:-}" = "--size" ]; then
  bytes=$(printf '%s' "$bundle" | wc -c | tr -d ' ')
  printf 'boot bundle: %d bytes ≈ %d tokens (budget %d bytes)\n' "$bytes" $((bytes/4)) "$BUDGET_BYTES"
  [ "$bytes" -le "$BUDGET_BYTES" ]; exit $?
fi
printf '%s\n' "$bundle"
