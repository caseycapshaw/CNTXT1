#!/usr/bin/env bash
# SessionStart hook — load your knowledge base into context at the start of every
# Claude Code session, EXCEPT inside code projects: the ~/dev tree, or any directory
# that has its own CLAUDE.md (a self-contained repo with its own context).
#
# Beyond a static pointer, this inlines the live vault map (index.md), a computed
# inbox listing, today's calendar (from the cache), and a pointer to today's plan
# note — so the map + inbox + day are in context at startup without relying on the
# model remembering to read them.
#
# Install as ~/.claude/hooks/knowledge-context.sh and register under SessionStart in
# ~/.claude/settings.json. See this folder's README.md.
#
# Fail-safe: on any unexpected error, emit nothing rather than erroring the session.

# ===== CONFIG — edit this =====
VAULT="$HOME/my-kb"          # absolute path to your KB
# ==============================

payload="$(cat 2>/dev/null)"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null)"
[ -z "$cwd" ] && cwd="$PWD"

# 1) Never inject inside the dev tree.
case "$cwd" in
  "$HOME"/dev | "$HOME"/dev/*) exit 0 ;;
esac

# 2) Never inject if the working tree is a self-contained project (own CLAUDE.md),
#    walking from cwd up to $HOME. (Your KB's own CLAUDE.md is handled by Claude
#    Code directly; this guard is for OTHER projects — so keep the vault out of
#    ~/dev, or this hook will also skip it. If your KB lives somewhere with its own
#    CLAUDE.md and you still want the inlining, remove this block.)
dir="$cwd"
while [ -n "$dir" ] && [ "$dir" != "/" ]; do
  [ -f "$dir/CLAUDE.md" ] && [ "$dir" != "$VAULT" ] && exit 0
  [ "$dir" = "$HOME" ] && break
  dir="$(dirname "$dir")"
done

# 3) Bail quietly if the vault isn't present.
[ -d "$VAULT" ] || exit 0

read -r -d '' pointer <<EOF
A personal knowledge base (Karpathy "knowledge-base-as-compiler" method) lives at $VAULT — your durable project memory.

For any non-code / knowledge task, BEFORE answering: read $VAULT/meta/AGENTS.md (how the base works). The map (index.md) and the live inbox state are inlined below — use them as your starting point. Keep the base current per AGENTS.md — capture new material to raw/, compile durable facts into concepts/, update index.md, append meta/log.md, use Obsidian [[wikilinks]] for backlinks.

The vault ROOT is the inbox: new notes/files land at the root, and anything there other than the pinned anchors (README.md, index.md, Actions.md, CLAUDE.md) is an un-triaged item — offer to file it into raw/ and compile.

Read and write $VAULT using absolute paths regardless of the current working directory.
EOF

# --- Live vault map: inline index.md (truncated defensively) ---
map=""
if [ -f "$VAULT/index.md" ]; then
  map="$(head -c 8000 "$VAULT/index.md" 2>/dev/null)"
fi

# --- Live inbox: root entries other than the pinned anchors and structural folders ---
inbox_items=""
while IFS= read -r entry; do
  name="$(basename "$entry")"
  case "$name" in
    README.md|index.md|Actions.md|CLAUDE.md) continue ;;   # pinned anchors
    concepts|Initiatives|meta|raw|People|Jobs|attachments|Excalidraw) continue ;;  # structural folders
    daily) continue ;;                                      # auto-generated plan notes
    setup.md) continue ;;                                   # starter-kit artifact
    .*) continue ;;                                         # hidden (.obsidian, .DS_Store)
  esac
  if [ -d "$entry" ]; then
    inbox_items="${inbox_items}- ${name}/ (directory)
"
  else
    inbox_items="${inbox_items}- ${name}
"
  fi
done < <(find "$VAULT" -maxdepth 1 -mindepth 1 2>/dev/null | sort)

if [ -n "$inbox_items" ]; then
  inbox="INBOX — un-triaged items at the vault root (offer to file into raw/ and compile):
${inbox_items}"
else
  inbox="INBOX — empty (root holds only the anchors + structural folders). Nothing to triage."
fi

# --- Today's calendar: read the cache ONLY (instant). Never run osascript here. ---
cal_block=""
cache="$HOME/.claude/cache/calendar-today.txt"
today="$(date +%F 2>/dev/null)"
if [ -f "$cache" ]; then
  cal_date="$(head -n 1 "$cache" 2>/dev/null)"
  cal_body="$(tail -n +2 "$cache" 2>/dev/null)"
  if [ "$cal_date" = "$today" ]; then
    cal_block="
=== TODAY'S CALENDAR (${today}) ===
${cal_body}"
  else
    cal_block="
=== TODAY'S CALENDAR — stale cache (dated ${cal_date:-unknown}; auto-refreshes 8am) ==="
  fi
fi

# --- Pointer to today's auto-generated daily plan note, if it exists. ---
plan_block=""
plan_note="$VAULT/daily/$today.md"
if [ -f "$plan_note" ]; then
  if grep -q "daily-plan: STUB" "$plan_note" 2>/dev/null; then
    plan_block="
Today's plan note ($plan_note) is a STUB — the 8am job reached the calendar but the API was unreachable, so open #actions + priorities aren't filled in. Offer to regenerate: ~/.claude/hooks/daily-plan.sh --force"
  else
    plan_block="
Today's plan note: $plan_note — the day's schedule, open #actions, and priorities. Read it first."
  fi
fi

# --- Assemble ---
ctx="$pointer
${plan_block}
${cal_block}

=== VAULT MAP ($VAULT/index.md, live) ===
${map}

=== ${inbox} ==="

jq -n --arg ctx "$ctx" \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
