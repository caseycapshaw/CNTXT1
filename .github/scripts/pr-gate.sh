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

# ---- 1. Instance-content folders hold only their shipped scaffolding ------
# The kit adopts the numbered GTD layout (00 daily … 05 concepts). User notes
# in these folders are git-ignored (.gitignore negation patterns keep only the
# shipped scaffolding); this gate is the belt to that suspender.
# $1=dir  $2="|"-separated allowed basenames (empty = dir must be empty/absent).
# Dotfiles (.gitkeep) are never listed by the glob and are always allowed.
check_only() {
  dir=$1; allowed=$2; extras=""
  if [ -d "$dir" ]; then
    for f in "$dir"/*; do
      [ -e "$f" ] || continue
      b=$(basename "$f")
      case "|$allowed|" in *"|$b|"*) continue ;; esac
      extras="$extras $b"
    done
  fi
  if [ -n "$extras" ]; then
    bad "$dir/ must ship only its scaffolding — personal/instance content never lands in this repo:$extras"
  else
    ok "$dir/ ships only its scaffolding"
  fi
}
# index.md = generated per-directory index (SYSTEM/bin/build_directory_indexes.py)
check_only "00 daily"                  ""
check_only "01 Horizons"               "Goals|vision.md|purpose-principles.md"
check_only "01 Horizons/Goals"         "Goal TEMPLATE.md|index.md"
check_only "02 Areas"                  "Area TEMPLATE.md|Assets|trails|index.md"
check_only "02 Areas/Assets"           "index.md"
check_only "02 Areas/trails"           ""
check_only "03 Projects"               "Project TEMPLATE.md|archive|trails|index.md"
check_only "03 Projects/archive"       ""
check_only "03 Projects/trails"        ""
check_only "04 People"                 "People TEMPLATE.md|index.md"
check_only "raw"                       "2026-01-01-example-capture.md|index.md"
check_only "attachments"               ""

# ---- 2. Placeholders intact (the kit stays a template) --------------------
grep -q '{{NAME}}' CLAUDE.md   && ok "CLAUDE.md keeps {{NAME}} placeholder"   || bad "CLAUDE.md lost its {{NAME}} placeholder — looks personalized"
grep -q '{{NAME}}' AGENTS.md   && ok "AGENTS.md keeps {{NAME}} placeholder"   || bad "AGENTS.md lost its {{NAME}} placeholder — looks personalized"
grep -q '{{NAME}}' README.md   && ok "README.md keeps {{NAME}} placeholder"   || bad "README.md lost its {{NAME}} placeholder — looks personalized"

owners=$(grep -rn '^owner:' Skills/*/*.md | grep -v 'owner: "{{NAME}}"' | grep -v 'owner: {{NAME}}' || true)
if [ -n "$owners" ]; then
  bad "Skills/ skills must carry owner: {{NAME}}, found real values:
$owners"
else
  ok "all Skills/ skills carry owner: {{NAME}}"
fi

canon_owners=$(grep -rn '^  owner:' .claude/skills/*/SKILL.md 2>/dev/null | grep -v 'owner: "{{NAME}}"' | grep -v 'owner: {{NAME}}' || true)
if [ -n "$canon_owners" ]; then
  bad "canonical .claude/skills must carry owner: {{NAME}}, found real values:
$canon_owners"
else
  ok "all canonical .claude/skills carry owner: {{NAME}}"
fi

grep -q '{{PERSONAL_IDENTIFIERS}}' "Skills/DO/Sync an Improvement to CNTXT1.md" \
  && ok "sync skill keeps its {{PERSONAL_IDENTIFIERS}} placeholder" \
  || bad "Skills/DO/Sync an Improvement to CNTXT1.md lost {{PERSONAL_IDENTIFIERS}} — a real identifier list must never be committed here"

# ---- 3. Generic PII / credential patterns ----------------------------------
# Tuned to this tree: anything matching is either a leak or needs an explicit
# allowlist entry below. Filenames + line numbers only for credentials; full
# match display is fine for pattern names.
pii_scan() { # $1=label  $2=pattern  $3=extra grep -v filter (optional, applied to file list)
  hits=$(grep -rilE "$2" . \
    --exclude-dir=.git --exclude-dir=.github --exclude-dir=.venv --exclude=uv.lock --exclude=LICENSE 2>/dev/null || true)
  [ -n "${3:-}" ] && hits=$(printf '%s\n' "$hits" | grep -vE "$3" || true)
  if [ -n "$hits" ]; then
    bad "$1 pattern matched in:$(printf ' %s' $hits)"
  else
    ok "no $1 patterns"
  fi
}
# Email needs an allowlist (example/anthropic/noreply domains), so it's two-step:
email_hits=$(grep -rioE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' . \
  --exclude-dir=.git --exclude-dir=.github --exclude-dir=.venv --exclude=uv.lock --exclude=LICENSE 2>/dev/null \
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
    --exclude-dir=.git --exclude-dir=.github --exclude-dir=.venv --exclude=uv.lock --exclude=LICENSE 2>/dev/null || true)
  if [ -n "$id_hits" ]; then
    bad "maintainer identifier sweep matched (filenames only):$(printf ' %s' $id_hits)"
  else
    ok "maintainer identifier sweep clean"
  fi
else
  printf 'SKIP  maintainer identifier sweep (PERSONAL_IDENTIFIERS not set — expected on fork PRs)\n'
fi

# ---- 5. Consistency: new Skills are indexed + link map is current ---------
for f in Skills/*/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*" Index.md") continue ;; esac
  slug=$(basename "$f" .md)
  aliases=$(grep -m1 '^aliases:' "$f" 2>/dev/null | sed -E 's/^aliases:[[:space:]]*\[//; s/\][[:space:]]*$//')
  found=0
  grep -q "\[\[$slug\]\]" "05 concepts/skills.md" && found=1
  if [ "$found" -eq 0 ] && [ -n "$aliases" ]; then
    IFS=','; for a in $aliases; do
      a=$(printf '%s' "$a" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/^\"//; s/\"$//')
      [ -n "$a" ] && grep -qF "[[$a]]" "05 concepts/skills.md" && found=1
    done; unset IFS
  fi
  [ "$found" -eq 0 ] && bad "Skills note \"$slug\" is not indexed in 05 concepts/skills.md"
done
ok "Skills indexed in 05 concepts/skills.md (any misses listed above)"

# Each <TYPE> Index.md table is generated by SYSTEM/bin/build_skills_indexes.py;
# fail the gate if a real skill file exists that isn't listed in its index yet.
for type_dir in Skills/DO Skills/CHECK Skills/FORMAT Skills/RULE; do
  [ -d "$type_dir" ] || continue
  idx="$type_dir/$(basename "$type_dir") Index.md"
  for f in "$type_dir"/*.md; do
    [ -e "$f" ] || continue
    case "$f" in *TEMPLATE*|*" Index.md") continue ;; esac
    slug=$(basename "$f" .md)
    if [ ! -f "$idx" ]; then
      bad "Skills note \"$slug\" exists but \"$idx\" is missing — run SYSTEM/bin/build_skills_indexes.py"
      continue
    fi
    grep -qF "[[$slug]]" "$idx" \
      || bad "Skills note \"$slug\" is not listed in \"$idx\" — run SYSTEM/bin/build_skills_indexes.py"
  done
done
ok "Skills indexed in their <TYPE> Index.md (any misses listed above)"

if [ -x SYSTEM/bin/build-link-map.sh ]; then
  before=$(cat SYSTEM/link-map.md 2>/dev/null || true)
  ./SYSTEM/bin/build-link-map.sh >/dev/null 2>&1
  after=$(cat SYSTEM/link-map.md 2>/dev/null || true)
  if [ "$before" = "$after" ]; then
    ok "SYSTEM/link-map.md is current"
  else
    printf '%s\n' "$before" > SYSTEM/link-map.md
    bad "SYSTEM/link-map.md is stale — run SYSTEM/bin/build-link-map.sh and commit the result"
  fi
fi

# ---- 6. Generated indexes are current --------------------------------------
# Per-folder + skills indexes and the folder-scoped generators carry a
# `_Generated: DATE_` stamp, so they are drift-checked by their own --check
# mode (stamp-insensitive) rather than byte-compared. The gate never mutates
# the tree.
if command -v uv >/dev/null 2>&1; then
  if uv run python SYSTEM/bin/build_directory_indexes.py --check >/dev/null 2>&1; then
    ok "per-folder directory indexes are current"
  else
    bad "per-folder directory indexes are stale — run SYSTEM/bin/build_directory_indexes.py --write and commit"
  fi
  # Skills indexes have no stamp: snapshot, regenerate, byte-compare, restore.
  snap=$(mktemp -d); i=0
  for f in "Skills/DO/DO Index.md" "Skills/CHECK/CHECK Index.md" "Skills/FORMAT/FORMAT Index.md" "Skills/RULE/RULE Index.md"; do
    i=$((i+1)); [ -f "$f" ] && cp "$f" "$snap/$i" || : > "$snap/$i.absent"
  done
  uv run python SYSTEM/bin/build_skills_indexes.py >/dev/null 2>&1
  i=0; stale=""
  for f in "Skills/DO/DO Index.md" "Skills/CHECK/CHECK Index.md" "Skills/FORMAT/FORMAT Index.md" "Skills/RULE/RULE Index.md"; do
    i=$((i+1))
    if [ -f "$snap/$i" ]; then
      cmp -s "$snap/$i" "$f" 2>/dev/null || stale="$stale $f"
      cp "$snap/$i" "$f"
    else
      [ -f "$f" ] && { stale="$stale $f"; rm -f "$f"; }
    fi
  done
  rm -rf "$snap"
  if [ -n "$stale" ]; then
    bad "skills indexes are stale — run SYSTEM/bin/build_skills_indexes.py and commit:$stale"
  else
    ok "skills indexes are current"
  fi
  # GTD generators (index Projects/Concepts/Areas, contacts, horizon serves)
  # each expose --check; run those that exist.
  for gen in build_index_projects.py build_index_lists.py build_contacts_directory.py build_horizon_serves.py; do
    [ -f "SYSTEM/bin/$gen" ] || continue
    if uv run python "SYSTEM/bin/$gen" --check >/dev/null 2>&1; then
      ok "$gen output is current"
    else
      bad "$gen output is stale — run SYSTEM/bin/regen-all.sh and commit"
    fi
  done
else
  printf 'SKIP  generated-index staleness check (uv not installed)\n'
fi

# ---- 7. Frontmatter validation (Pydantic schemas) ---------------------------
if command -v uv >/dev/null 2>&1; then
  if uv run python SYSTEM/bin/validate_frontmatter.py; then
    ok "frontmatter validates against SYSTEM/schemas models"
  else
    bad "frontmatter validation failed (see FAIL lines above)"
  fi
else
  printf 'SKIP  frontmatter validation (uv not installed)\n'
fi

echo
if [ "$fail" -eq 0 ]; then echo "PR GATE: green"; else echo "PR GATE: violations found"; fi
exit "$fail"
