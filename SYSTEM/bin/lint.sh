#!/usr/bin/env bash
# lint.sh — deterministic KB health check (the mechanical half of the lint).
# Checks: (1) root inbox clean, (2) all wikilinks resolve, (3) index complete,
# (4) CONTENT Concepts/Initiatives/People/Skills notes carry frontmatter, (5) concepts +
# initiatives carry a non-empty description:. Exit 0 = pass, 1 = problems.
# The LLM lint keeps only the judgment checks (stale facts, resolved questions).
#
# Link scan ignores: TEMPLATE files, and any [[link]] inside an inline `code`
# span (those are illustrative examples, not real links).
set -uo pipefail
cd "$(dirname "$0")/../.."   # vault root
fail=0
note() { printf '  %s\n' "$1"; }
ok()   { printf 'PASS  %s\n' "$1"; }
bad()  { printf 'FAIL  %s\n' "$1"; fail=1; }

# ---- 1. Root inbox clean -------------------------------------------------
anchors="README.md index.md Actions.md CLAUDE.md"
structural="CONTENT SYSTEM daily attachments docs Writing"
# Template-only artifacts (present in kb-starter; absent in a live vault — harmless either way).
template_extras="setup.md LICENSE"
# Standing root files (machinery write-targets, not inbox items) — one per line.
standing=""
inbox=()
for e in *; do
  case " $anchors $structural $template_extras " in *" $e "*) continue ;; esac
  while IFS= read -r s; do [ -n "$s" ] && [ "$e" = "$s" ] && continue 2; done <<< "$standing"
  inbox+=("$e")
done
if [ ${#inbox[@]} -eq 0 ]; then ok "root inbox clean"; else bad "root inbox has un-triaged items:"; for i in "${inbox[@]}"; do note "$i"; done; fi

# ---- content files (exclude template files) ------------------------------
files=()
for f in CONTENT/Concepts/*.md CONTENT/Initiatives/*.md CONTENT/Initiatives/archive/*.md CONTENT/Skills/*/*.md CONTENT/People/*.md CONTENT/Agents/*.md index.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*" Index.md") continue ;; esac
  files+=("$f")
done

# ---- valid wikilink-name set (canonical names + aliases + outside anchors) ----
valid="$(mktemp)"
for f in CONTENT/Concepts/*.md CONTENT/Initiatives/*.md CONTENT/Initiatives/archive/*.md CONTENT/Excalidraw/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*) continue ;; esac
  basename "$f" .md >> "$valid"
done
for f in CONTENT/People/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*) continue ;; esac
  basename "$f" .md >> "$valid"
  al="$(grep -m1 '^aliases:' "$f" 2>/dev/null | sed -E 's/^aliases:[[:space:]]*\[//; s/\][[:space:]]*$//')"
  [ -z "$al" ] && continue
  IFS=','; for a in $al; do a="$(printf '%s' "$a" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/^\"//; s/\"$//')"; [ -n "$a" ] && echo "$a" >> "$valid"; done; unset IFS
done
for f in CONTENT/Skills/*/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*" Index.md") continue ;; esac
  basename "$f" .md >> "$valid"
  al="$(grep -m1 '^aliases:' "$f" 2>/dev/null | sed -E 's/^aliases:[[:space:]]*\[//; s/\][[:space:]]*$//')"
  [ -z "$al" ] && continue
  IFS=','; for a in $al; do a="$(printf '%s' "$a" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/^\"//; s/\"$//')"; [ -n "$a" ] && echo "$a" >> "$valid"; done; unset IFS
done
# real link targets that live outside the four scanned dirs (root/SYSTEM anchors)
for p in log AGENTS Actions; do echo "$p" >> "$valid"; done
# CONTENT/raw/ captures referenced via path-style links: [[CONTENT/raw/YYYY-MM-DD-topic]],
# including subfolders
find CONTENT/raw -name '*.md' -type f 2>/dev/null | sed 's/\.md$//' >> "$valid"
sort -u "$valid" -o "$valid"

# ---- 2. Wikilinks resolve (strip inline-code spans first) ----------------
broken="$(mktemp)"
cat "${files[@]}" 2>/dev/null \
  | sed -E 's/`[^`]*`//g' \
  | grep -oE '\[\[[^]]+\]\]' \
  | sed -E 's/\[\[//; s/\]\]//; s/\|.*//' \
  | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/^\"//; s/\"$//' \
  | sort -u \
  | while IFS= read -r link; do
      [ -z "$link" ] && continue
      grep -qxF "$link" "$valid" || echo "$link" >> "$broken"
    done
if [ ! -s "$broken" ]; then ok "all wikilinks resolve"; else bad "broken wikilinks:"; while IFS= read -r b; do note "[[$b]]"; done < "$broken"; fi

# ---- 3. Index completeness ----------------------------------------------
missing=""
for f in CONTENT/Concepts/*.md CONTENT/Initiatives/*.md CONTENT/Initiatives/archive/*.md; do
  [ -e "$f" ] || continue   # skip the literal glob when a dir is empty (else slug becomes '*')
  case "$f" in *TEMPLATE*) continue ;; esac
  slug="$(basename "$f" .md)"
  grep -qF "[[$slug]]" index.md || missing="$missing $slug"
done
if [ -z "$missing" ]; then ok "index lists every concept + initiative"; else bad "not linked from index.md:"; for m in $missing; do note "$m"; done; fi

# ---- 4. Frontmatter present ---------------------------------------------
fm_fail=""
for f in CONTENT/Concepts/*.md CONTENT/Initiatives/*.md CONTENT/Initiatives/archive/*.md CONTENT/People/*.md CONTENT/Skills/*/*.md; do
  [ -e "$f" ] || continue   # skip literal glob for empty dirs
  case "$f" in *TEMPLATE*|*" Index.md") continue ;; esac
  [ "$(head -1 "$f")" = "---" ] || fm_fail="$fm_fail $f"
done
if [ -z "$fm_fail" ]; then ok "Concepts/Initiatives/People/Skills all carry frontmatter"; else bad "missing frontmatter:"; for m in $fm_fail; do note "$m"; done; fi

# ---- 5. description: present on concepts + initiatives --------------------
desc_fail=""
for f in CONTENT/Concepts/*.md CONTENT/Initiatives/*.md CONTENT/Initiatives/archive/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*) continue ;; esac
  awk '/^---$/{c++; next} c==1 && /^description:[[:space:]]*[^[:space:]]/{found=1} c==2{exit} END{exit !found}' "$f" || desc_fail="$desc_fail $f"
done
if [ -z "$desc_fail" ]; then ok "concepts + initiatives carry a description:"; else bad "missing/empty description: frontmatter:"; for m in $desc_fail; do note "$m"; done; fi

rm -f "$valid" "$broken"
echo
if [ "$fail" = 0 ]; then echo "LINT: green (mechanical checks)"; else echo "LINT: problems found"; fi
echo "(judgment checks — stale facts, resolved open questions, actions still open — remain a manual/LLM pass)"
exit $fail
