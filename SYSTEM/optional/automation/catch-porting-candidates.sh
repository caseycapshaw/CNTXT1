#!/usr/bin/env bash
# catch-porting-candidates.sh — Claude Code hook (PostToolUse + Stop) that
# nudges you when an edit touches something that probably belongs downstream:
# generic framework files → your public CNTXT1 clone; team-relevant content
# → a shared Teams repo (if you keep one).
#
# Wire it in .claude/settings.json (both events point at this same script):
#   "hooks": {
#     "PostToolUse": [{"matcher": "Edit|Write|MultiEdit",
#                      "hooks": [{"type": "command", "command": "SYSTEM/optional/automation/catch-porting-candidates.sh"}]}],
#     "Stop":        [{"hooks": [{"type": "command", "command": "SYSTEM/optional/automation/catch-porting-candidates.sh"}]}]
#   }
#
# No-op until configured: leave either variable blank to silence that half.
set -uo pipefail

# ===== CONFIG — edit these (blank = that nudge is off) =====
CNTXT1_CLONE=""   # absolute path to your local public-CNTXT1 clone, e.g. "$HOME/dev/CNTXT1"
TEAMS_REPO=""     # name/path of your shared Teams repo, e.g. "CNTXT-Teams-<TeamName>"
# ===========================================================

# Generic framework files — instance-agnostic, belongs in CNTXT1.
CNTXT1_PATTERNS='^SYSTEM/schemas/models\.py$|^SYSTEM/bin/.*\.(sh|py)$|^SYSTEM/AGENTS\.md$|^Knowledge/.*TEMPLATE\.md$|^Knowledge/Skills/Skills Index\.md$|^Knowledge/Skills/[A-Za-z]+/[A-Za-z]+ Index\.md$'

# Team-relevant (not personal) content — belongs in a Teams repo, if you have one.
TEAMS_PATTERNS='^Knowledge/Agents/.*\.md$|^Knowledge/Skills/.*/.*\.md$|^Knowledge/Initiatives/.*\.md$|^Knowledge/Concepts/.*\.md$'

# Fully unconfigured → pure no-op.
[ -z "$CNTXT1_CLONE" ] && [ -z "$TEAMS_REPO" ] && exit 0

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
input="$(cat 2>/dev/null || true)"

# Candidate paths (repo-relative): the edited file on PostToolUse, or every
# modified/untracked file on Stop (the event carries no file_path).
candidates=""
edited="$(printf '%s' "$input" \
  | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
if [ -n "$edited" ]; then
  candidates="${edited#"$repo_root"/}"
else
  candidates="$(cd "$repo_root" && git status --porcelain 2>/dev/null | cut -c4- )"
fi
[ -n "$candidates" ] || exit 0

cntxt1_hits=""; teams_hits=""
while IFS= read -r p; do
  [ -n "$p" ] || continue
  [ -n "$CNTXT1_CLONE" ] && printf '%s' "$p" | grep -qE "$CNTXT1_PATTERNS" && cntxt1_hits="$cntxt1_hits $p"
  [ -n "$TEAMS_REPO" ]   && printf '%s' "$p" | grep -qE "$TEAMS_PATTERNS"  && teams_hits="$teams_hits $p"
done <<< "$candidates"

[ -z "$cntxt1_hits" ] && [ -z "$teams_hits" ] && exit 0

{
  echo "Porting candidates detected:"
  [ -n "$cntxt1_hits" ] && echo "  generic framework (consider porting to CNTXT1 at $CNTXT1_CLONE):$cntxt1_hits"
  [ -n "$teams_hits" ]  && echo "  team-relevant content (consider sharing to $TEAMS_REPO):$teams_hits"
} >&2
exit 0
