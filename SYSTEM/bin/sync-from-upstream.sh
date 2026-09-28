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
#   sync-from-upstream.sh --reconcile
#       "Upstream kit updates (pending).md" would otherwise re-list every
#       commit between the adopted baseline and upstream/main each night, even
#       ones YOU authored from this vault and pushed OUT to the public kit via
#       the Sync-an-improvement skill — already reflected here by construction,
#       just never marked adopted because that workflow doesn't round-trip
#       through this repo's own history. --reconcile classifies each pending
#       upstream commit:
#         APPLIED  — author email matches `git config user.email` here
#                    (self-originated: it left this vault, it isn't new to
#                    it) OR its patch-id matches a commit already in this
#                    vault's own `git log`.
#         PENDING  — genuinely foreign — a real framework change to review.
#       It regenerates the pending note with ONLY the PENDING commits (the
#       queue drains instead of re-showing the same self-authored commits
#       forever), and — only when EVERY commit in range reconciles as
#       APPLIED — advances the adopted baseline to upstream's tip and removes
#       the note. Baseline file: ~/.claude/cache/cntxt1-upstream-adopted (the
#       same one the optional daily-summary.sh job uses). Never commits,
#       never pushes (upstream stays fetch-only); classification is read-only.
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
reconcile=0
case "${1:-}" in
  --apply) apply=1 ;;
  --reconcile) reconcile=1 ;;
  -h|--help) echo "usage: $(basename "$0") [--apply|--reconcile]   (preview-only with neither)"; exit 0 ;;
  "") ;;
  *) echo "unknown flag: $1 (see --help)" >&2; exit 2 ;;
esac

if [ "$reconcile" = 1 ]; then
  UPNOTE="Upstream kit updates (pending).md"
  ADOPTED_F="$HOME/.claude/cache/cntxt1-upstream-adopted"
  self_email="$(git config user.email || true)"

  if ! git remote get-url "$UPSTREAM_REMOTE" >/dev/null 2>&1; then
    echo "FAIL  no '$UPSTREAM_REMOTE' remote configured" >&2
    exit 1
  fi
  git fetch "$UPSTREAM_REMOTE" --quiet || { echo "FAIL  fetch failed (offline?)"; exit 1; }
  tip="$(git rev-parse "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH")"
  adopted="$(cat "$ADOPTED_F" 2>/dev/null || true)"
  mkdir -p "$(dirname "$ADOPTED_F")"
  if [ -z "$adopted" ]; then
    printf '%s\n' "$tip" > "$ADOPTED_F"
    echo "reconcile: bootstrapped baseline to $tip (first run) — nothing pending."
    [ -f "$UPNOTE" ] && rm -f "$UPNOTE"
    exit 0
  fi
  if [ "$adopted" = "$tip" ]; then
    echo "reconcile: baseline already current — nothing pending."
    [ -f "$UPNOTE" ] && rm -f "$UPNOTE" && echo "  (removed stale pending note)"
    exit 0
  fi

  shas="$(git log --format='%H' --reverse "$adopted..$tip" 2>/dev/null)"
  applied_lines=()
  pending_lines=()
  while IFS= read -r sha; do
    [ -n "$sha" ] || continue
    subj="$(git log -1 --format='%s' "$sha")"
    email="$(git log -1 --format='%ae' "$sha")"
    short="$(printf '%.7s' "$sha")"
    is_applied=0
    if [ -n "$self_email" ] && [ "$email" = "$self_email" ]; then
      is_applied=1
    else
      # secondary check: does an equivalent change already exist in this
      # vault's own history (patch-id match)? Best-effort — a patch-id needs
      # a real diff, so this only fires for non-merge commits.
      up_pid="$(git show "$sha" | git patch-id --stable 2>/dev/null | awk '{print $1}')"
      if [ -n "$up_pid" ]; then
        local_pid="$(git log --format='%H' -- . | while IFS= read -r h; do
                       git show "$h" 2>/dev/null | git patch-id --stable 2>/dev/null
                     done | awk -v want="$up_pid" '$1==want{print; exit}')"
        [ -n "$local_pid" ] && is_applied=1
      fi
    fi
    if [ "$is_applied" = 1 ]; then
      applied_lines+=("- \`$short\` $subj  _(applied — self-originated: $email)_")
    else
      pending_lines+=("- \`$short\` $subj")
    fi
  done <<< "$shas"

  n_applied=${#applied_lines[@]}
  n_pending=${#pending_lines[@]}
  echo "reconcile: $((n_applied + n_pending)) commit(s) in range, $n_applied applied (self-originated), $n_pending genuinely pending."

  if [ "$n_pending" -eq 0 ]; then
    printf '%s\n' "$tip" > "$ADOPTED_F"
    [ -f "$UPNOTE" ] && rm -f "$UPNOTE"
    echo "reconcile: all reconciled — baseline advanced to $tip, pending note removed."
    exit 0
  fi

  {
    echo "# Upstream kit updates (pending)"
    echo
    echo "> Auto-generated by sync-from-upstream.sh --reconcile — do not edit;"
    echo "> rewritten each run. Commits you authored from this vault (already"
    echo "> reflected here by construction) are reconciled out automatically —"
    echo "> only genuinely foreign commits remain below."
    echo
    echo "The public CNTXT1 kit has **$n_pending commit(s)** this vault genuinely"
    echo "hasn't adopted (of $((n_applied + n_pending)) total in range; $n_applied"
    echo "auto-reconciled as self-originated):"
    echo
    printf '%s\n' "${pending_lines[@]}"
    echo
    echo "**Next session:** ask Claude to *\"review the pending upstream kit updates\"* —"
    echo "it should interview you commit-by-commit (adopt / skip / defer), apply the"
    echo "keepers via [[Pull framework updates from CNTXT1]], update the baseline file"
    echo "(\`~/.claude/cache/cntxt1-upstream-adopted\`), push the vault to its private"
    echo "origin, and delete this note."
    echo
    echo "- [ ] Review $n_pending pending upstream kit commit(s) #action #auto"
  } > "$UPNOTE"
  echo "reconcile: wrote $UPNOTE ($n_pending pending)."
  exit 0
fi

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
