#!/usr/bin/env bash
# sync-from-upstream.sh — preview-first puller of FRAMEWORK files from this
# repo's upstream. Companion to the asymmetric-sync policy (see
# SYSTEM/SCHEMA.md § Privacy & content separation and the
# [[Pull Framework Updates from CNTXT1]] skill): the upstream remote is
# fetch-only (push URL DISABLED); this script only ever moves files INWARD,
# and it NEVER auto-commits — you always review the working tree and commit
# (or discard) yourself.
#
# Usage:
#   sync-from-upstream.sh            # fetch + show a preview diffstat, change nothing
#   sync-from-upstream.sh --apply    # checkout the framework paths from upstream
#                                    # into the working tree (still no commit)
set -uo pipefail
cd "$(dirname "$0")/../.."   # vault root

# ===== CONFIG — edit if your remote/branch differ =====
UPSTREAM_REMOTE="upstream"
UPSTREAM_BRANCH="main"
# Framework paths — instance-agnostic files that are safe to take verbatim.
# Populated/personal surfaces (CLAUDE.md, index.md, Knowledge notes other than
# templates) are deliberately NOT listed: port those by hand.
FRAMEWORK_PATHS=(
  "SYSTEM/SCHEMA.md"
  "SYSTEM/bin"
  "SYSTEM/schemas"
  "SYSTEM/optional"
  "pyproject.toml"
  "uv.lock"
  "Knowledge/Initiatives/Initiative TEMPLATE.md"
  "Knowledge/People/People TEMPLATE.md"
  "Knowledge/Skills/Skill TEMPLATE.md"
  "Knowledge/Agents/domain-advisor TEMPLATE.md"
)
# ======================================================

apply=0
case "${1:-}" in
  --apply) apply=1 ;;
  -h|--help) echo "usage: $(basename "$0") [--apply]   (preview-only without --apply)"; exit 0 ;;
  "") ;;
  *) echo "unknown flag: $1 (see --help)" >&2; exit 2 ;;
esac

# ---- preconditions --------------------------------------------------------
if ! git remote get-url "$UPSTREAM_REMOTE" >/dev/null 2>&1; then
  echo "FAIL  no '$UPSTREAM_REMOTE' remote configured. One-time setup:" >&2
  echo "      git remote add $UPSTREAM_REMOTE <upstream-url>" >&2
  echo "      git remote set-url --push $UPSTREAM_REMOTE DISABLED" >&2
  exit 1
fi
push_url="$(git remote get-url --push "$UPSTREAM_REMOTE" 2>/dev/null || true)"
if [ "$push_url" != "DISABLED" ]; then
  echo "WARN  '$UPSTREAM_REMOTE' push URL is not DISABLED — the asymmetric-sync" >&2
  echo "      policy expects a fetch-only upstream: git remote set-url --push $UPSTREAM_REMOTE DISABLED" >&2
fi

echo "Fetching $UPSTREAM_REMOTE..."
git fetch "$UPSTREAM_REMOTE" || exit 1
ref="$UPSTREAM_REMOTE/$UPSTREAM_BRANCH"

# ---- preview --------------------------------------------------------------
echo
echo "Framework diff vs $ref (inward direction only):"
if git diff --stat HEAD "$ref" -- "${FRAMEWORK_PATHS[@]}" | grep -q .; then
  git diff --stat HEAD "$ref" -- "${FRAMEWORK_PATHS[@]}"
else
  echo "  (no framework differences — already in sync)"
  exit 0
fi

if [ "$apply" = 0 ]; then
  echo
  echo "(preview only — re-run with --apply to bring these into the working tree;"
  echo " nothing is ever committed for you)"
  exit 0
fi

# ---- apply (working tree only, never commits) -----------------------------
echo
echo "Checking out framework paths from $ref into the working tree..."
git checkout "$ref" -- "${FRAMEWORK_PATHS[@]}" 2>/dev/null || true
echo
git status --short -- "${FRAMEWORK_PATHS[@]}"
echo
echo "Done — review with 'git diff --staged', then commit yourself (or discard"
echo "with 'git restore --staged --worktree <path>'). This script never commits."
exit 0
