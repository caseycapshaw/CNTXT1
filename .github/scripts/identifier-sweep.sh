#!/bin/sh
# identifier-sweep.sh — the maintainer identifier sweep for the CNTXT1 kit.
#
# Greps the whole tree for PERSONAL_IDENTIFIERS (a |-separated grep -P (PCRE)
# pattern; in CI the `maintainer-secrets` environment secret). Never prints
# the pattern or the matched text. In GitHub Actions it prints only the NUMBER
# of matching files: names in a public log would let anyone who can merge a
# file of candidate words learn which ones are on the list. Run it locally
# (private) to see the names.
#
# This script runs with the secret in its environment, so it uses only
# sh, grep, sed and coreutils and executes no code from outside .github/
# (a CODEOWNERS rule guards .github/ and /.gitattributes; nothing guards the rest
# of the tree).
# Keep it that way: never call SYSTEM/ scripts or a package runner from here.
# pr-gate.sh calls this script for local runs; this script calls nothing.
# identifier-sweep-selftest.sh exercises it with synthetic patterns on every PR.
#
# Runs from the repo root. Exit 0 = clean, 1 = identifier found,
# 2 = cannot sweep (pattern unset, empty or invalid, no grep with -P, or grep
# itself errored): a sweep that cannot run fails, it never passes.
set -u
cd "$(dirname "$0")/../.." || exit 2

cannot() { printf 'FAIL  maintainer identifier sweep: %s\n' "$1"; exit 2; }

[ -n "${PERSONAL_IDENTIFIERS:-}" ] \
  || cannot 'PERSONAL_IDENTIFIERS is unset or empty — refusing to pass without a pattern'

# grep's stderr is always discarded below (some greps echo the pattern in
# their errors); its exit status is checked instead. Find a grep with -P:
# GNU grep in CI; on macOS the stock grep has none, so try ggrep.
GREP=""
for g in grep ggrep; do
  command -v "$g" >/dev/null 2>&1 || continue
  if printf 'x\n' | "$g" -qP -e 'x' >/dev/null 2>&1; then GREP=$g; break; fi
done
[ -n "$GREP" ] || cannot 'no grep with -P (PCRE) support found (tried grep, ggrep) — install GNU grep'

printf '' | "$GREP" -qP -e "$PERSONAL_IDENTIFIERS" >/dev/null 2>&1
[ "$?" -eq 2 ] && cannot 'PERSONAL_IDENTIFIERS is not a valid grep -P pattern'

tmp=$(mktemp -d) || cannot 'could not create a temporary directory'
trap 'rm -rf "$tmp"' EXIT

# Search roots: every top-level entry except the root's own .git (a directory,
# or a worktree's pointer file), .github, .venv, LICENSE and uv.lock. Exclusions
# are anchored here, at the root, on purpose: grep's --exclude* options match at
# any depth, which would make a nested .github/ or LICENSE a hiding place.
set --
for p in ./* ./.[!.]* ./..?*; do
  # Top-level symlinks are skipped: grep follows a symlink named on its command
  # line (unlike those it meets under -r), so a link out of the tree would be read.
  [ -L "$p" ] && continue
  [ -e "$p" ] || continue
  case "$p" in ./.git|./.github|./.venv|./LICENSE|./uv.lock) continue ;; esac
  set -- "$@" "$p"
done
set -f  # no globbing from here on; every expansion below is quoted anyway
[ "$#" -gt 0 ] || cannot 'nothing to sweep (empty tree)'

# Pass 1: candidate files. grep: 0 = matches, 1 = none, 2 = error (fail closed).
"$GREP" -rilP -e "$PERSONAL_IDENTIFIERS" -- "$@" >"$tmp/candidates" 2>/dev/null
rc=$?
[ "$rc" -le 1 ] || cannot 'grep failed while scanning the tree (unreadable file or PCRE limit)'

# Pass 2: known-public text is blanked out before matching again (mirrors the
# "allowed hits" of the sync skill's grep gate): the repo's own slug
# (owner/name in upstream URLs — GITHUB_REPOSITORY is set by Actions) and the
# kit's placeholder home paths (/Users/you, /home/NAME, ...).
own="${GITHUB_REPOSITORY:-}"
: >"$tmp/hits"
while IFS= read -r f; do
  sed -E "${own:+s#${own}##Ig; }s#/(Users|home)/(you|NAME|USER|<[^>]*>)([/\`'\") ]|\$)#/\3#g" "$f" \
    >"$tmp/blanked" 2>/dev/null || cannot 'sed failed while reading a candidate file'
  "$GREP" -qiP -e "$PERSONAL_IDENTIFIERS" "$tmp/blanked" >/dev/null 2>&1
  rc=$?
  case "$rc" in
    0) printf '%s\n' "$f" >>"$tmp/hits" ;;
    1) ;;
    *) cannot 'grep failed while re-checking a candidate file (PCRE limit?)' ;;
  esac
done <"$tmp/candidates"

n=$(wc -l <"$tmp/hits" | tr -d ' ')
if [ "$n" -gt 0 ]; then
  if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
    printf 'FAIL  maintainer identifier sweep: %s file(s) matched; run the sweep locally to see which\n' "$n"
  else
    printf 'FAIL  maintainer identifier sweep: %s file(s) matched (filenames only):\n' "$n"
    while IFS= read -r f; do printf '        %s\n' "$f"; done <"$tmp/hits"
  fi
  exit 1
fi
printf 'PASS  %s\n' "maintainer identifier sweep clean"
exit 0
