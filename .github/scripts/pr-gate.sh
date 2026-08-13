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
      # generated per-directory index (SYSTEM/bin/build_directory_indexes.py)
      [ "$(basename "$f")" = "index.md" ] && continue
      extras="$extras $(basename "$f")"
    done
  fi
  if [ -n "$extras" ]; then
    bad "$dir/ must ship only its template/example — personal/instance content never lands in this repo:$extras"
  else
    ok "$dir/ ships only its template/example"
  fi
}
check_only CONTENT/People "People TEMPLATE.md"
check_only CONTENT/raw    "2026-01-01-example-capture.md"
check_only daily  ""
check_only attachments ""

# CONTENT/Initiatives/ ships only the template (instances add real initiative notes)
# plus the empty archive/ scaffold (done initiatives move there in instances).
extras=""
for f in CONTENT/Initiatives/*; do
  [ -e "$f" ] || continue
  b=$(basename "$f")
  [ "$b" = "Initiative TEMPLATE.md" ] && continue
  [ "$b" = "index.md" ] && continue   # generated per-directory index
  if [ "$b" = "archive" ]; then
    for g in CONTENT/Initiatives/archive/* CONTENT/Initiatives/archive/.[!.]*; do
      [ -e "$g" ] || continue
      [ "$(basename "$g")" = ".gitkeep" ] || extras="$extras archive/$(basename "$g")"
    done
    continue
  fi
  extras="$extras $b"
done
if [ -n "$extras" ]; then
  bad "CONTENT/Initiatives/ must ship only its template + empty archive/ — personal/instance content never lands in this repo:$extras"
else
  ok "CONTENT/Initiatives/ ships only its template + empty archive/"
fi

# ---- 2. Placeholders intact (the kit stays a template) --------------------
grep -q '{{NAME}}' CLAUDE.md   && ok "CLAUDE.md keeps {{NAME}} placeholder"   || bad "CLAUDE.md lost its {{NAME}} placeholder — looks personalized"
grep -q '{{NAME}}' README.md   && ok "README.md keeps {{NAME}} placeholder"   || bad "README.md lost its {{NAME}} placeholder — looks personalized"

owners=$(grep -rn '^owner:' CONTENT/Skills/*/*.md | grep -v 'owner: "{{NAME}}"' | grep -v 'owner: {{NAME}}' || true)
if [ -n "$owners" ]; then
  bad "CONTENT/Skills/ skills must carry owner: {{NAME}}, found real values:
$owners"
else
  ok "all CONTENT/Skills/ skills carry owner: {{NAME}}"
fi

grep -q '{{PERSONAL_IDENTIFIERS}}' "CONTENT/Skills/DO/Sync an Improvement to CNTXT1.md" \
  && ok "sync skill keeps its {{PERSONAL_IDENTIFIERS}} placeholder" \
  || bad "CONTENT/Skills/DO/Sync an Improvement to CNTXT1.md lost {{PERSONAL_IDENTIFIERS}} — a real identifier list must never be committed here"

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
for f in CONTENT/Skills/*/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*" Index.md") continue ;; esac
  slug=$(basename "$f" .md)
  aliases=$(grep -m1 '^aliases:' "$f" 2>/dev/null | sed -E 's/^aliases:[[:space:]]*\[//; s/\][[:space:]]*$//')
  found=0
  grep -q "\[\[$slug\]\]" CONTENT/Concepts/skills.md && found=1
  if [ "$found" -eq 0 ] && [ -n "$aliases" ]; then
    IFS=','; for a in $aliases; do
      a=$(printf '%s' "$a" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/^\"//; s/\"$//')
      [ -n "$a" ] && grep -qF "[[$a]]" CONTENT/Concepts/skills.md && found=1
    done; unset IFS
  fi
  [ "$found" -eq 0 ] && bad "CONTENT/Skills note \"$slug\" is not indexed in CONTENT/Concepts/skills.md"
done
ok "Skills indexed in CONTENT/Concepts/skills.md (any misses listed above)"

# Each <TYPE> Index.md table is generated by SYSTEM/bin/build_skills_indexes.py;
# fail the gate if a real skill file exists that isn't listed in its index yet.
for type_dir in CONTENT/Skills/DO CONTENT/Skills/CHECK CONTENT/Skills/FORMAT CONTENT/Skills/RULE; do
  [ -d "$type_dir" ] || continue
  idx="$type_dir/$(basename "$type_dir") Index.md"
  for f in "$type_dir"/*.md; do
    [ -e "$f" ] || continue
    case "$f" in *TEMPLATE*|*" Index.md") continue ;; esac
    slug=$(basename "$f" .md)
    if [ ! -f "$idx" ]; then
      bad "CONTENT/Skills note \"$slug\" exists but \"$idx\" is missing — run SYSTEM/bin/build_skills_indexes.py"
      continue
    fi
    grep -qF "[[$slug]]" "$idx" \
      || bad "CONTENT/Skills note \"$slug\" is not listed in \"$idx\" — run SYSTEM/bin/build_skills_indexes.py"
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

# ---- 6. Generated indexes are current (regenerate, byte-compare, restore) --
# SYSTEM/link-map.md and every folder's index.md are both regenerated scripts —
# fail the gate if committing them stale (i.e. the checked-in file doesn't
# match what running the generator right now would produce).
if command -v uv >/dev/null 2>&1; then
  snap=$(mktemp -d)
  i=0
  # snapshot every generated file, run the generators, byte-compare, restore
  for f in "CONTENT/Concepts/index.md" "CONTENT/Initiatives/index.md" "CONTENT/People/index.md" "CONTENT/Agents/index.md" "CONTENT/raw/index.md" "CONTENT/Excalidraw/index.md" "CONTENT/Skills/DO/DO Index.md" "CONTENT/Skills/CHECK/CHECK Index.md" "CONTENT/Skills/FORMAT/FORMAT Index.md" "CONTENT/Skills/RULE/RULE Index.md"; do
    i=$((i+1))
    [ -f "$f" ] && cp "$f" "$snap/$i" || : > "$snap/$i.absent"
  done
  uv run python SYSTEM/bin/build_directory_indexes.py >/dev/null 2>&1
  uv run python SYSTEM/bin/build_skills_indexes.py    >/dev/null 2>&1
  i=0; stale=""
  for f in "CONTENT/Concepts/index.md" "CONTENT/Initiatives/index.md" "CONTENT/People/index.md" "CONTENT/Agents/index.md" "CONTENT/raw/index.md" "CONTENT/Excalidraw/index.md" "CONTENT/Skills/DO/DO Index.md" "CONTENT/Skills/CHECK/CHECK Index.md" "CONTENT/Skills/FORMAT/FORMAT Index.md" "CONTENT/Skills/RULE/RULE Index.md"; do
    i=$((i+1))
    if [ -f "$snap/$i" ]; then
      if ! cmp -s "$snap/$i" "$f" 2>/dev/null; then stale="$stale $f"; fi
      cp "$snap/$i" "$f"   # restore — the gate never mutates the tree
    else
      # file didn't exist before; if a generator created it, it's stale-by-omission
      [ -f "$f" ] && { stale="$stale $f"; rm -f "$f"; }
    fi
  done
  rm -rf "$snap"
  if [ -n "$stale" ]; then
    bad "generated index files are stale — rerun the generators and commit:$stale"
  else
    ok "generated directory + skills indexes are current"
  fi
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
