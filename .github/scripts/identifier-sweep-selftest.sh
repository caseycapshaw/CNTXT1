#!/bin/sh
# identifier-sweep-selftest.sh — exercises identifier-sweep.sh with SYNTHETIC
# patterns on every pull request (job `gate`), so the runner's GNU grep proves
# the script before the secret-bearing run on main ever uses it. No secret is
# involved; nothing sensitive can be printed. pr-gate.sh does not use this.
#
# Runs from the repo root. Exit 0 = every case returned its exact expected code.
set -u
cd "$(dirname "$0")/../.." || exit 2

fail=0
expect() { # $1=expected exit  $2=label  $3=pattern
  out=$(PERSONAL_IDENTIFIERS=$3 ./.github/scripts/identifier-sweep.sh 2>&1)
  got=$?
  if [ "$got" -eq "$1" ]; then
    printf 'PASS  self-test: %s (exit %s)\n' "$2" "$got"
  else
    printf 'FAIL  self-test: %s — expected exit %s, got %s. Sweep said:\n%s\n' "$2" "$1" "$got" "$out"; fail=1
  fi
}

# (a) a pattern that can never match (a word boundary that is also not one):
#     the whole tree is read and sweeps clean, with no grep error.
expect 0 "unmatchable pattern sweeps the tree clean" '\b\B'
# (b) a fixed generic string a tracked file outside .github/ must carry
#     (pr-gate.sh requires the {{NAME}} placeholder in CLAUDE.md): a hit.
expect 1 "placeholder pattern is found" '\{\{NAME\}\}'
# (c) an empty pattern: the sweep refuses to run.
expect 2 "empty pattern fails closed" ''

[ "$fail" -eq 0 ] && echo "SWEEP SELF-TEST: green" || echo "SWEEP SELF-TEST: failed"
exit "$fail"
