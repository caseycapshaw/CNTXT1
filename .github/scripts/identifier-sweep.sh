#!/bin/sh
# identifier-sweep.sh — the maintainer identifier sweep for the CNTXT1 kit.
#
# Greps the whole tree for PERSONAL_IDENTIFIERS (a |-separated grep -P (PCRE)
# pattern; in CI the `maintainer-secrets` environment secret). Reports file
# names only, never the pattern or the matched text, so nothing sensitive
# lands in public CI logs.
#
# This script runs with the secret in its environment, so it uses only
# sh, grep, sed and coreutils and executes no code from outside .github/
# (a CODEOWNERS rule guards .github/; nothing guards the rest of the tree).
# Keep it that way: never call SYSTEM/ scripts or a package runner from here.
# pr-gate.sh calls this script for local runs; this script calls nothing.
#
# Runs from the repo root. Exit 0 = clean, 1 = identifier found,
# 2 = cannot sweep (pattern unset, empty or invalid, or grep lacks -P): a sweep
# that cannot run fails.
set -u
cd "$(dirname "$0")/../.." || exit 2

if [ -z "${PERSONAL_IDENTIFIERS:-}" ]; then
  printf 'FAIL  maintainer identifier sweep: PERSONAL_IDENTIFIERS is unset or empty — refusing to pass without a pattern\n'
  exit 2
fi
# The tree scan below discards grep's errors (some greps echo the pattern in
# them), so a grep without -P, or a pattern it cannot compile, would pass
# silently. Check both first. (macOS's stock grep has no -P: use GNU grep.)
if ! printf 'x\n' | grep -qP 'x' >/dev/null 2>&1; then
  printf 'FAIL  maintainer identifier sweep: this grep has no -P (PCRE) support — use GNU grep\n'
  exit 2
fi
printf '' | grep -qP "$PERSONAL_IDENTIFIERS" >/dev/null 2>&1
if [ "$?" -eq 2 ]; then
  printf 'FAIL  maintainer identifier sweep: PERSONAL_IDENTIFIERS is not a valid grep -P pattern\n'
  exit 2
fi

# Known-public text is blanked out before matching (mirrors the "allowed
# hits" of the sync skill's grep gate): the repo's own slug (owner/name in
# upstream URLs — GITHUB_REPOSITORY is set by Actions) and the kit's
# placeholder home paths (/Users/you, /home/NAME, ...).
# (--exclude=.git also skips a worktree's .git pointer file.)
own="${GITHUB_REPOSITORY:-}"
id_hits=$(grep -rilP "$PERSONAL_IDENTIFIERS" . \
  --exclude-dir=.git --exclude=.git --exclude-dir=.github --exclude-dir=.venv --exclude=uv.lock --exclude=LICENSE 2>/dev/null || true)
if [ -n "$id_hits" ]; then
  id_hits=$(printf '%s\n' "$id_hits" | while IFS= read -r f; do
    sed -E "${own:+s#${own}##Ig; }s#/(Users|home)/(you|NAME|USER|<[^>]*>)([/\`'\") ]|\$)#/\3#g" "$f" \
      | grep -qiP "$PERSONAL_IDENTIFIERS" 2>/dev/null && printf '%s\n' "$f"
  done)
fi
if [ -n "$id_hits" ]; then
  printf 'FAIL  %s\n' "maintainer identifier sweep matched (filenames only):$(printf ' %s' $id_hits)"
  exit 1
fi
printf 'PASS  %s\n' "maintainer identifier sweep clean"
exit 0
