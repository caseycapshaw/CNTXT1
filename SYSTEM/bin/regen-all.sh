#!/usr/bin/env bash
# regen-all.sh — run every generator lint.sh verifies, in the right order, so
# a scheduled maintainer (or you) can make lint green before having to guess
# at intent. Deterministic, fail-loud: any generator's non-zero exit is
# reported and the run ends non-zero, same spirit as the generators
# themselves (SYSTEM/SCHEMA.md § Generated sections — "pin expected input
# headers and exit non-zero rather than write partial or silently-wrong
# output").
#
# Order matters: link map and mirrors first (other generators may read
# wikilink/skill state), then the content-derived indexes, then the action
# census last since it can reflect any #action lines the earlier steps touched.
#
# Every generator the starter ships is wired below.
#
# Usage: SYSTEM/bin/regen-all.sh
#   Exit 0 = every generator ran clean. Exit 1 = at least one failed (see the
#   per-step FAIL lines above the summary).
set -uo pipefail
_BIN="$(cd "$(dirname "$0")" && pwd)"
cd "$_BIN/../.."   # vault root

rc=0
step() {
  local name="$1"; shift
  echo "== $name =="
  if "$@"; then
    echo "OK    $name"
  else
    echo "FAIL  $name (exit $?)"
    rc=1
  fi
  echo
}
skip() { echo "SKIP  $1"; echo; }

step "link-map"              ./SYSTEM/bin/build-link-map.sh
step ".claude mirrors"       uv run python SYSTEM/bin/build_claude_mirrors.py
step "directory indexes"     uv run python SYSTEM/bin/build_directory_indexes.py --write
step "skills indexes"        uv run python SYSTEM/bin/build_skills_indexes.py
# The census needs the <!-- actions:auto:start/end --> marker pair in Actions.md
# (opt-in — see SYSTEM/bin/README.md); skip cleanly until you add it.
if grep -qs 'actions:auto:start' Actions.md; then
  step "actions census"      python3 SYSTEM/bin/actions.py --write
else
  skip "actions census (no actions:auto markers in Actions.md)"
fi

echo
if [ "$rc" = 0 ]; then
  echo "regen-all: all generators ran clean — run SYSTEM/bin/lint.sh to verify."
else
  echo "regen-all: one or more generators FAILED (see above) — a human must look; lint will still be red under LINT_STRICT=1."
fi
exit "$rc"
