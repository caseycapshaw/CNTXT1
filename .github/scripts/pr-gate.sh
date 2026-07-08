#!/bin/sh
# pr-gate.sh — public-repo privacy & consistency gate for the CNTXT1 starter kit.
#
# CNTXT1 ships a FRAMEWORK. Instances built from it hold personal content;
# this repo must never. These are whole-tree invariants (not diff checks):
# if the tree violates one, the repo is wrong no matter which PR did it.
#
# Fork-safe: needs no secrets. If PERSONAL_IDENTIFIERS is set in the
# environment (a |-separated grep -E pattern, provided via a repo secret on
# same-repo runs), an extra maintainer-specific sweep runs — filenames only,
# so nothing sensitive lands in public CI logs.
#
# Runs from the repo root. Exit 0 = clean.
set -u
cd "$(dirname "$0")/../.." || exit 2

fail=0
ok()  { printf 'PASS  %s\n' "$1"; }
bad() { printf 'FAIL  %s\n' "$1"; fail=1; }

# ---- 1. Instance-content folders hold only their shipped template/example --
check_only() { # $1=dir  $2=allowed basename (empty = dir must be empty/absent)
  dir=$1; allowed=$2; extras=""
  if [ -d "$dir" ]; then
    for f in "$dir"/*; do
      [ -e "$f" ] || continue
      [ "$(basename "$f")" = "$allowed" ] && continue
      extras="$extras $(basename "$f")"
    done
  fi
  if [ -n "$extras" ]; then
    bad "$dir/ must ship only its template/example — personal/instance content never lands in this repo:$extras"
  else
    ok "$dir/ ships only its template/example"
  fi
}
check_only People "People TEMPLATE.md"
check_only raw    "2026-01-01-example-capture.md"
check_only daily  ""
check_only attachments ""

# Initiatives/ ships only the template (instances add real initiative notes).
check_only Initiatives "Initiative TEMPLATE.md"

# ---- 2. Placeholders intact (the kit stays a template) --------------------
grep -q '{{NAME}}' CLAUDE.md   && ok "CLAUDE.md keeps {{NAME}} placeholder"   || bad "CLAUDE.md lost its {{NAME}} placeholder — looks personalized"
grep -q '{{NAME}}' README.md   && ok "README.md keeps {{NAME}} placeholder"   || bad "README.md lost its {{NAME}} placeholder — looks personalized"

owners=$(grep -rn '^owner:' Jobs/*.md | grep -v 'owner: {{NAME}}' || true)
if [ -n "$owners" ]; then
  bad "Jobs/ runbooks must carry owner: {{NAME}}, found real values:
$owners"
else
  ok "all Jobs/ runbooks carry owner: {{NAME}}"
fi

grep -q '{{PERSONAL_IDENTIFIERS}}' "Jobs/Sync an improvement to CNTXT1.md" \
  && ok "sync runbook keeps its {{PERSONAL_IDENTIFIERS}} placeholder" \
  || bad "Jobs/Sync an improvement to CNTXT1.md lost {{PERSONAL_IDENTIFIERS}} — a real identifier list must never be committed here"

# ---- 3. Generic PII / credential patterns ----------------------------------
# Tuned to this tree: anything matching is either a leak or needs an explicit
# allowlist entry below. Filenames + line numbers only for credentials; full
# match display is fine for pattern names.
pii_scan() { # $1=label  $2=pattern  $3=extra grep -v filter (optional, applied to file list)
  hits=$(grep -rilE "$2" . \
    --exclude-dir=.git --exclude-dir=.github --exclude=LICENSE 2>/dev/null || true)
  [ -n "${3:-}" ] && hits=$(printf '%s\n' "$hits" | grep -vE "$3" || true)
  if [ -n "$hits" ]; then
    bad "$1 pattern matched in:$(printf ' %s' $hits)"
  else
    ok "no $1 patterns"
  fi
}
# Email needs an allowlist (example/anthropic/noreply domains), so it's two-step:
email_hits=$(grep -rioE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' . \
  --exclude-dir=.git --exclude-dir=.github --exclude=LICENSE 2>/dev/null \
  | grep -viE '@(example\.(com|org)|anthropic\.com|users\.noreply\.github\.com)' \
  | cut -d: -f1 | sort -u || true)
if [ -n "$email_hits" ]; then
  bad "real email addresses found in:$(printf ' %s' $email_hits)"
else
  ok "no real email addresses"
fi
pii_scan "US phone number"   '\b[0-9]{3}[-. ][0-9]{3}[-. ][0-9]{4}\b'
pii_scan "private IPv4"      '\b(10|192\.168|172\.(1[6-9]|2[0-9]|3[01]))(\.[0-9]{1,3}){2,3}\b'
pii_scan "credential/token"  '(sk-ant-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY)'

# ---- 4. Maintainer-specific identifier sweep (optional, secret-fed) --------
if [ -n "${PERSONAL_IDENTIFIERS:-}" ]; then
  id_hits=$(grep -rilE "$PERSONAL_IDENTIFIERS" . \
    --exclude-dir=.git --exclude-dir=.github --exclude=LICENSE 2>/dev/null || true)
  if [ -n "$id_hits" ]; then
    bad "maintainer identifier sweep matched (filenames only):$(printf ' %s' $id_hits)"
  else
    ok "maintainer identifier sweep clean"
  fi
else
  printf 'SKIP  maintainer identifier sweep (PERSONAL_IDENTIFIERS not set — expected on fork PRs)\n'
fi

# ---- 5. Consistency: new Jobs are indexed + link map is current ------------
for f in Jobs/*.md; do
  b=$(basename "$f" .md)
  [ "$b" = "Jobs TEMPLATE" ] && continue
  grep -q "\[\[$b\]\]" concepts/jobs.md || bad "Jobs/$b.md is not indexed in concepts/jobs.md"
done
ok "Jobs indexed in concepts/jobs.md (any misses listed above)"

if [ -x meta/bin/build-link-map.sh ]; then
  before=$(cat meta/link-map.md 2>/dev/null || true)
  ./meta/bin/build-link-map.sh >/dev/null 2>&1
  after=$(cat meta/link-map.md 2>/dev/null || true)
  if [ "$before" = "$after" ]; then
    ok "meta/link-map.md is current"
  else
    printf '%s\n' "$before" > meta/link-map.md
    bad "meta/link-map.md is stale — run meta/bin/build-link-map.sh and commit the result"
  fi
fi

echo
if [ "$fail" -eq 0 ]; then echo "PR GATE: green"; else echo "PR GATE: violations found"; fi
exit "$fail"
