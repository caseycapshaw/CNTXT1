#!/usr/bin/env bash
# lint.sh — deterministic KB health check (the mechanical half of the lint).
# Checks: (1) root inbox clean, (2) all wikilinks resolve (incl. aliases),
# (3) index complete, (4) CONTENT Concepts/Initiatives/People/Skills notes
# carry frontmatter, (5) concepts + initiatives carry a non-empty
# description:, (6) no stray non-.md files in note folders, (7) index Quick
# map fits the SessionStart injection budget, (8) Pydantic frontmatter
# schema validation. Exit 0 = pass, 1 = problems.
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
# Python tooling files (schema validation layer, managed by uv).
tooling="pyproject.toml uv.lock"
# Standing root files (machinery write-targets, not inbox items) — one per line.
standing=""
inbox=()
for e in *; do
  case " $anchors $structural $template_extras $tooling " in *" $e "*) continue ;; esac
  while IFS= read -r s; do [ -n "$s" ] && [ "$e" = "$s" ] && continue 2; done <<< "$standing"
  inbox+=("$e")
done
if [ ${#inbox[@]} -eq 0 ]; then ok "root inbox clean"; else bad "root inbox has un-triaged items:"; for i in "${inbox[@]}"; do note "$i"; done; fi

# ---- content files (exclude template files) ------------------------------
files=()
for f in CONTENT/Concepts/*.md CONTENT/Initiatives/*.md CONTENT/Initiatives/archive/*.md CONTENT/Skills/*/*.md CONTENT/People/*.md CONTENT/Agents/*.md index.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*" Index.md"|*/index.md) continue ;; esac
  files+=("$f")
done

# ---- valid wikilink-name set (canonical names + aliases + outside anchors) ----
valid="$(mktemp)"
for f in CONTENT/Concepts/*.md CONTENT/Initiatives/*.md CONTENT/Initiatives/archive/*.md CONTENT/Excalidraw/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*/index.md) continue ;; esac
  basename "$f" .md >> "$valid"
  al="$(grep -m1 '^aliases:' "$f" 2>/dev/null | sed -E 's/^aliases:[[:space:]]*\[//; s/\][[:space:]]*$//')"
  [ -z "$al" ] && continue
  IFS=','; for a in $al; do a="$(printf '%s' "$a" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/^\"//; s/\"$//')"; [ -n "$a" ] && echo "$a" >> "$valid"; done; unset IFS
done
for f in CONTENT/People/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*/index.md) continue ;; esac
  basename "$f" .md >> "$valid"
  al="$(grep -m1 '^aliases:' "$f" 2>/dev/null | sed -E 's/^aliases:[[:space:]]*\[//; s/\][[:space:]]*$//')"
  [ -z "$al" ] && continue
  IFS=','; for a in $al; do a="$(printf '%s' "$a" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/^\"//; s/\"$//')"; [ -n "$a" ] && echo "$a" >> "$valid"; done; unset IFS
done
for f in CONTENT/Skills/*/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*" Index.md"|*/index.md) continue ;; esac
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
  case "$f" in *TEMPLATE*|*/index.md) continue ;; esac
  slug="$(basename "$f" .md)"
  grep -qF "[[$slug]]" index.md || missing="$missing $slug"
done
if [ -z "$missing" ]; then ok "index lists every concept + initiative"; else bad "not linked from index.md:"; for m in $missing; do note "$m"; done; fi

# ---- 4. Frontmatter present ---------------------------------------------
fm_fail=""
for f in CONTENT/Concepts/*.md CONTENT/Initiatives/*.md CONTENT/Initiatives/archive/*.md CONTENT/People/*.md CONTENT/Skills/*/*.md; do
  [ -e "$f" ] || continue   # skip literal glob for empty dirs
  case "$f" in *TEMPLATE*|*" Index.md"|*/index.md) continue ;; esac
  [ "$(head -1 "$f")" = "---" ] || fm_fail="$fm_fail $f"
done
if [ -z "$fm_fail" ]; then ok "Concepts/Initiatives/People/Skills all carry frontmatter"; else bad "missing frontmatter:"; for m in $fm_fail; do note "$m"; done; fi

# ---- 5. description: present on concepts + initiatives --------------------
desc_fail=""
for f in CONTENT/Concepts/*.md CONTENT/Initiatives/*.md CONTENT/Initiatives/archive/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*/index.md) continue ;; esac
  awk '/^---$/{c++; next} c==1 && /^description:[[:space:]]*[^[:space:]]/{found=1} c==2{exit} END{exit !found}' "$f" || desc_fail="$desc_fail $f"
done
if [ -z "$desc_fail" ]; then ok "concepts + initiatives carry a description:"; else bad "missing/empty description: frontmatter:"; for m in $desc_fail; do note "$m"; done; fi

# ---- 6. No stray non-markdown files in note folders -----------------------
# Leftover .tmp/.bak/editor droppings in content folders are invisible to the
# wikilink checks (which glob *.md) — a renamed note can leave a committed
# .tmp behind while its links dangle. Fail loud on anything that isn't .md.
stray=""
for f in CONTENT/Concepts/* CONTENT/Initiatives/* CONTENT/Initiatives/archive/* CONTENT/People/* CONTENT/Skills/*/* CONTENT/Agents/*; do
  [ -f "$f" ] || continue
  case "$f" in *.md|*.base) continue ;; esac   # .base = Obsidian Bases dashboards
  stray="$stray $f"
done
if [ -z "$stray" ]; then ok "no stray non-.md files in note folders"; else bad "stray non-.md files (leftover temp/rename artifacts?):"; for m in $stray; do note "$m"; done; fi

# ---- 7. Quick map fits the SessionStart injection budget -------------------
# The optional SessionStart hook inlines `head -c 8000` of index.md; the Quick
# map skeleton (everything before the second "## " heading) must fit or the
# injected map is silently truncated mid-line and everything after the cut —
# typically the Actions/log pointers — never reaches a session.
skel_bytes="$(awk '/^## /{c++; if(c==2) exit} {print}' index.md | wc -c | tr -d ' ')"
budget=8000
if [ "$skel_bytes" -le "$budget" ]; then
  ok "index Quick map skeleton fits injection budget ($skel_bytes/$budget bytes)"
else
  bad "index Quick map skeleton overflows injection budget ($skel_bytes/$budget bytes) — SessionStart injection truncates; tighten the skeleton"
fi

# ---- 8. Pydantic frontmatter schema validation ----------------------------
if command -v uv >/dev/null 2>&1; then
  if uv run python SYSTEM/bin/validate_frontmatter.py; then
    ok "frontmatter validates against SYSTEM/schemas (Pydantic)"
  else
    bad "frontmatter schema validation failed (see errors above)"
  fi
else
  printf 'WARN  uv not installed — skipping Pydantic frontmatter validation (install: brew install uv)\n'
fi

rm -f "$valid" "$broken"
echo
if [ "$fail" = 0 ]; then echo "LINT: green (mechanical checks)"; else echo "LINT: problems found"; fi
echo "(judgment checks — stale facts, resolved open questions, actions still open — remain a manual/LLM pass)"
exit $fail
