#!/usr/bin/env bash
# Argument-validation tests for vm-bootstrap.sh. Everything here fails BEFORE the
# script touches the system (validation runs ahead of the root check and any
# install step), so it is safe to run anywhere, as any user.
set -u
S="$(cd "$(dirname "$0")/.." && pwd)/vm-bootstrap.sh"
PASS=0; FAIL=0
expect_fail() {  # expect_fail DESC PATTERN args...
  local desc="$1" pat="$2"; shift 2
  local out rc
  out="$("$S" "$@" 2>&1)"; rc=$?
  if [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q -- "$pat"; then PASS=$((PASS+1)); echo "ok   - $desc"
  else FAIL=$((FAIL+1)); echo "FAIL - $desc (rc=$rc): $out"; fi
}
expect_fail "no args -> --user required"        "--user is required"
expect_fail "missing --vault-repo"               "--vault-repo is required" --user u
expect_fail "missing --services-repo"            "--services-repo is required" --user u --vault-repo x
expect_fail "bad user name"                      "plain lowercase" --user 'Bad Name' --vault-repo x --services-repo y
expect_fail "bad swap size"                      "whole number" --user u --vault-repo x --services-repo y --swap-gb ten
expect_fail "relative parity link rejected"      "absolute path" --user u --vault-repo x --services-repo y --path-parity-link Users
expect_fail "unknown flag"                       "unknown argument" --nope
if [ "$(id -u)" -ne 0 ]; then
  expect_fail "valid args but not root -> refuses" "must run as root" --user u --vault-repo x --services-repo vault
fi
out="$("$S" --help)"; if printf '%s' "$out" | grep -q -- '--lock-ssh'; then PASS=$((PASS+1)); echo "ok   - --help documents --lock-ssh"; else FAIL=$((FAIL+1)); echo "FAIL - --help"; fi
echo; echo "$PASS passed, $FAIL failed"; [ "$FAIL" -eq 0 ]
