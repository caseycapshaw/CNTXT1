#!/usr/bin/env bash
# lint.sh — deterministic KB health check (the mechanical half of the lint).
# Checks: (1) root inbox clean, (2) all wikilinks resolve (incl. aliases),
# (3) index complete, (4) 05 concepts/03 Projects/02 Areas/01 Horizons/04 People/Skills
# carry frontmatter, (5) concepts + projects + areas + horizons carry a
# non-empty description:, (6) attachments owned, (7) no stray non-.md files
# in note folders, (8) index Quick map fits the SessionStart injection
# budget, (9) Pydantic frontmatter schema validation, (10) every active
# project has an open next action, (11) registered role digests under their
# word cap (or a declared cap_exception), (12) areas/horizons reviewed
# within cadence (WARN-only), (13) .claude mirrors in sync, (14) horizon
# serves lists, (15/15a/15b/15c) generated index Projects + Concepts/Areas +
# contacts directory + per-folder directory indexes, (16) orphan-raw WARN,
# (17) link-map no duplicate keys / no [[aliases:]], (18) Quick map skeleton
# has no ISO dates or status words. Exit 0 = pass, 1 = problems.
#
# Generated-view checks (13, 14, 15/15a/15b/15c) and word caps (11) are
# WARN, not FAIL, by default — a stale generated view or an over-cap section
# is a `SYSTEM/bin/regen-all.sh` / `SYSTEM/bin/cap_overflow.py --write` away,
# not a human decision. Set LINT_STRICT=1 to make them FAIL again (the
# maintainer's own pre-commit gate runs regen-all.sh first, so it should
# rarely see either red even under LINT_STRICT=1).
#
# Scheduled runs should use lint-delta.sh (alarms on the DELTA, not the
# total — a permanently-red check is an invisible check).
# The LLM lint keeps only the judgment checks (stale facts, resolved questions).
#
# Link scan ignores: TEMPLATE files, and any [[link]] inside an inline `code`
# span (those are illustrative examples, not real links).
set -uo pipefail
_BIN="$(cd "$(dirname "$0")" && pwd)"
cd "$_BIN/../.."   # vault root
# shellcheck source=kb-folders.sh
. "$_BIN/kb-folders.sh"
# Skip generated/template indexes — but 01 Horizons/Goals/index.md is the H3
# horizon note (aliases: [goals]), not a generated dir index.
skip_index_or_template() {
  case "$1" in
    *TEMPLATE*) return 0 ;;
    "$KB_HORIZON_GOALS/index.md") return 1 ;;
    */index.md) return 0 ;;
  esac
  return 1
}
fail=0
note() { printf '  %s\n' "$1"; }
ok()   { printf 'PASS  %s\n' "$1"; }
bad()  { printf 'FAIL  %s\n' "$1"; fail=1; }
# Regenerate-then-check a "stale generated view" is not
# a decision a human needs to make — it's a `SYSTEM/bin/regen-all.sh` away.
# staleFAIL/staleWARN route a generated-view or cap-overflow mismatch to WARN
# by default (still visible, never blocks) and only to FAIL when the caller
# sets LINT_STRICT=1 (CI / the maintainer's pre-commit gate). Judgment-shaped
# checks (broken links, missing frontmatter, schema violations) always use
# bad() — those are exactly what "red only for things a human must decide"
# means lint should still stop on.
: "${LINT_STRICT:=0}"
softFAIL() {
  # $1 = message, $2 = the remedy suffix appended only in WARN mode.
  if [ "$LINT_STRICT" = 1 ]; then
    bad "$1"
  else
    printf 'WARN  %s — %s\n' "$1" "$2"
  fi
}
staleFAIL() { softFAIL "$1" "stale generated view — run SYSTEM/bin/regen-all.sh"; }
capFAIL()   { softFAIL "$1" "over cap — run SYSTEM/bin/cap_overflow.py --write (Milestones) or rewrite the prose (Now & next)"; }

# ---- 1. Root inbox clean -------------------------------------------------
anchors="README.md index.md Actions.md CLAUDE.md AGENTS.md"
structural="${KB_CONCEPTS} ${KB_PROJECTS} ${KB_AREAS} ${KB_HORIZONS} SYSTEM Agents raw ${KB_DAILY} ${KB_PEOPLE} Skills attachments docs excalidraw"
# Template-only artifacts (present in the starter kit; absent in a live vault — harmless either way).
template_extras="setup.md LICENSE MIGRATING.md CHANGELOG.md"
# Python tooling files (schema validation layer, managed by uv).
tooling="pyproject.toml uv.lock"
# Standing root files (machinery write-targets, not inbox items) — one per line.
standing="Upstream kit updates (pending).md"
inbox=()
for e in *; do
  case " $anchors $structural $template_extras $tooling " in *" $e "*) continue ;; esac
  while IFS= read -r s; do [ "$e" = "$s" ] && continue 2; done <<< "$standing"
  inbox+=("$e")
done
if [ ${#inbox[@]} -eq 0 ]; then ok "root inbox clean"; else bad "root inbox has un-triaged items:"; for i in "${inbox[@]}"; do note "$i"; done; fi

# ---- content files (exclude template files) ------------------------------
files=()
for f in "$KB_CONCEPTS"/*.md "$KB_PROJECTS"/*.md "$KB_PROJECTS"/archive/*.md "$KB_AREAS"/*.md "$KB_AREAS"/Assets/*.md "$KB_HORIZONS"/*.md "$KB_HORIZON_GOALS"/*.md Skills/*/*.md "$KB_PEOPLE"/*.md index.md; do
  [ -e "$f" ] || continue
  skip_index_or_template "$f" && continue
  files+=("$f")
done

# ---- valid wikilink-name set (canonical names + aliases + outside anchors) ----
valid="$(mktemp)"
for f in "$KB_CONCEPTS"/*.md "$KB_PROJECTS"/*.md "$KB_PROJECTS"/archive/*.md "$KB_PROJECTS"/trails/*.md "$KB_AREAS"/*.md "$KB_AREAS"/Assets/*.md "$KB_AREAS"/trails/*.md "$KB_HORIZONS"/*.md "$KB_HORIZON_GOALS"/*.md excalidraw/*.md; do
  [ -e "$f" ] || continue
  skip_index_or_template "$f" && continue
  # Goals/index.md is registered via aliases: [goals], never as [[index]]
  [ "$f" = "$KB_HORIZON_GOALS/index.md" ] || basename "$f" .md >> "$valid"
  extract_aliases "$f" >> "$valid"
done
for f in "$KB_PEOPLE"/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*/index.md) continue ;; esac
  basename "$f" .md >> "$valid"
  extract_aliases "$f" >> "$valid"
done
for f in Skills/*/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*" Index.md") continue ;; esac
  basename "$f" .md >> "$valid"
  extract_aliases "$f" >> "$valid"
done
# real link targets that live outside the four scanned dirs (root/meta anchors)
for p in log AGENTS SCHEMA Actions decisions; do echo "$p" >> "$valid"; done
# raw/ captures referenced via path-style links: [[raw/YYYY-MM-DD-topic]],
# including subfolders
find raw -name '*.md' -type f 2>/dev/null | sed 's/\.md$//' >> "$valid"
sort -u "$valid" -o "$valid"

# ---- 2. Wikilinks resolve (strip inline-code spans and image embeds first) --
# Embeds (![[file.png]]) aren't navigation wikilinks and the valid-target set
# is note basenames only — strip them first or every image embed false-positives.
broken="$(mktemp)"
cat "${files[@]}" 2>/dev/null \
  | sed -E 's/`[^`]*`//g' \
  | sed -E 's/!\[\[[^]]*\]\]//g' \
  | grep -oE '\[\[[^]]+\]\]' \
  | sed -E 's/\[\[//; s/\]\]//; s/\|.*//' \
  | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' \
  | sort -u \
  | while IFS= read -r link; do
      [ -z "$link" ] && continue
      grep -qxF "$link" "$valid" || echo "$link" >> "$broken"
    done
if [ ! -s "$broken" ]; then ok "all wikilinks resolve"; else bad "broken wikilinks:"; while IFS= read -r b; do note "[[$b]]"; done < "$broken"; fi

# ---- 3. Index completeness ----------------------------------------------
missing=""
for f in "$KB_CONCEPTS"/*.md "$KB_PROJECTS"/*.md "$KB_PROJECTS"/archive/*.md "$KB_AREAS"/*.md "$KB_AREAS"/Assets/*.md "$KB_HORIZONS"/*.md "$KB_HORIZON_GOALS"/*.md; do
  [ -e "$f" ] || continue   # skip the literal glob when a dir is empty (else slug becomes '*')
  skip_index_or_template "$f" && continue
  slug="$(basename "$f" .md)"
  [ "$slug" = "index" ] && continue  # H3 door is listed as [[goals]]
  grep -qF "[[$slug]]" index.md || missing="$missing $slug"
done
if [ -z "$missing" ]; then ok "index lists every concept + project + area + horizon + goal"; else bad "not linked from index.md:"; for m in $missing; do note "$m"; done; fi

# ---- 4. Frontmatter present ---------------------------------------------
fm_fail=""
for f in "$KB_CONCEPTS"/*.md "$KB_PROJECTS"/*.md "$KB_PROJECTS"/archive/*.md "$KB_AREAS"/*.md "$KB_AREAS"/Assets/*.md "$KB_HORIZONS"/*.md "$KB_HORIZON_GOALS"/*.md "$KB_PEOPLE"/*.md Skills/*/*.md; do
  [ -e "$f" ] || continue   # skip literal glob for empty dirs
  case "$f" in *TEMPLATE*|*" Index.md") continue ;; esac
  skip_index_or_template "$f" && continue
  [ "$(head -1 "$f")" = "---" ] || fm_fail="$fm_fail $f"
done
if [ -z "$fm_fail" ]; then ok "concepts/Projects/Areas/Horizons/People/Skills all carry frontmatter"; else bad "missing frontmatter:"; for m in $fm_fail; do note "$m"; done; fi

# ---- 5. description: present on concepts + projects --------------------
desc_fail=""
for f in "$KB_CONCEPTS"/*.md "$KB_PROJECTS"/*.md "$KB_PROJECTS"/archive/*.md "$KB_AREAS"/*.md "$KB_AREAS"/Assets/*.md "$KB_HORIZONS"/*.md "$KB_HORIZON_GOALS"/*.md; do
  [ -e "$f" ] || continue
  skip_index_or_template "$f" && continue
  awk '/^---$/{c++; next} c==1 && /^description:[[:space:]]*[^[:space:]]/{found=1} c==2{exit} END{exit !found}' "$f" || desc_fail="$desc_fail $f"
done
if [ -z "$desc_fail" ]; then ok "concepts + projects + areas + horizons carry a description:"; else bad "missing/empty description: frontmatter:"; for m in $desc_fail; do note "$m"; done; fi

# ---- 6. Attachments owned ------------------------------------------------
# Every top-level entry in attachments/ must be a directory named after the
# note that owns it (a concept/project/skill/person slug) or a registered
# standing folder. No loose files at attachments/ top level.
att_standing="README.md"   # README.md = folder documentation; add skill-owned standing folders here
att_fail=""
for e in attachments/*; do
  [ -e "$e" ] || continue
  name="$(basename "$e")"
  case " $att_standing " in *" $name "*) continue ;; esac
  if [ ! -d "$e" ]; then att_fail="$att_fail $name(loose-file)"; continue; fi
  if [ -e "$KB_CONCEPTS/$name.md" ] || [ -e "$KB_PROJECTS/$name.md" ] || [ -e "$KB_PROJECTS/archive/$name.md" ] \
     || [ -e "$KB_AREAS/$name.md" ] || [ -e "$KB_AREAS/Assets/$name.md" ] || [ -e "$KB_HORIZONS/$name.md" ] \
     || [ -e "$KB_HORIZON_GOALS/$name.md" ] \
     || ls Skills/*/"$name".md >/dev/null 2>&1 || grep -qE "^aliases:.*[\[, ]$name[,\]]" Skills/*/*.md 2>/dev/null || [ -e "$KB_PEOPLE/$name.md" ] || [ -e "Agents/$name.md" ]; then continue; fi
  att_fail="$att_fail $name(no-owning-note)"
done
if [ -z "$att_fail" ]; then ok "attachments all owned (slug-named folders, no loose files)"; else bad "attachments not owned by a note:"; for m in $att_fail; do note "$m"; done; fi

# ---- 7. No stray non-markdown files in note folders -----------------------
# Leftover .tmp/.bak/editor droppings in content folders are invisible to the
# wikilink checks (which glob *.md) — a renamed note can leave a committed
# .tmp behind while its links dangle. Fail loud on anything that isn't .md.
stray=""
for f in "$KB_CONCEPTS"/* "$KB_PROJECTS"/* "$KB_PROJECTS"/archive/* "$KB_AREAS"/* "$KB_AREAS"/Assets/* "$KB_HORIZONS"/* "$KB_HORIZON_GOALS"/* "$KB_PEOPLE"/* Skills/*/* Agents/*; do
  [ -f "$f" ] || continue
  case "$f" in *.md|*.base) continue ;; esac   # .base = Obsidian Bases dashboards
  stray="$stray $f"
done
if [ -z "$stray" ]; then ok "no stray non-.md files in note folders"; else bad "stray non-.md files (leftover temp/rename artifacts?):"; for m in $stray; do note "$m"; done; fi

# ---- 8. Quick map fits the SessionStart injection budget -------------------
# build_boot_bundle.sh inlines the Quick map skeleton via awk (everything
# up to the first H2 that is not "## Quick map"). Same cut as this check:
# everything before the second "## " heading in index.md. Must fit 8000
# bytes or the injected map is silently truncated.
skel_bytes="$(awk '/^## /{c++; if(c==2) exit} {print}' index.md | wc -c | tr -d ' ')"
budget=8000
if [ "$skel_bytes" -le "$budget" ]; then
  ok "index Quick map skeleton fits injection budget ($skel_bytes/$budget bytes)"
else
  bad "index Quick map skeleton overflows injection budget ($skel_bytes/$budget bytes) — SessionStart injection truncates; tighten the skeleton"
fi

# ---- 9. Pydantic frontmatter schema validation ----------------------------
if command -v uv >/dev/null 2>&1; then
  if uv run python SYSTEM/bin/validate_frontmatter.py; then
    ok "frontmatter validates against SYSTEM/schemas (Pydantic)"
  else
    bad "frontmatter schema validation failed (see errors above)"
  fi
else
  printf 'WARN  uv not installed — skipping Pydantic frontmatter validation (install: brew install uv)\n'
fi

# ---- 10. Every active project has an open next action -------------------
# The GTD next-action audit (SYSTEM/bin/audit-project-next-actions.sh);
# an active project with no open #action is stalled-by-definition.
if ./SYSTEM/bin/audit-project-next-actions.sh >/dev/null 2>&1; then
  ok "every active project has an open next action"
else
  bad "active project(s) without an open next action (run SYSTEM/bin/audit-project-next-actions.sh for the list)"
fi

# ---- 11. Role digests + orientation sections under cap (or declared exception) ----
# Script-measured, never model-estimated (SYSTEM/bin/cap_check.py). A dated
# cap_exception: in frontmatter downgrades a breach to a declared WARN.
# An over-cap section is a
# `SYSTEM/bin/cap_overflow.py --write` away (Milestones — moves oldest
# bullets to the trail) or the maintainer's next Now & next rewrite (prose,
# stays a WARN always) — not a human decision, so it's WARN by default and
# only FAILs under LINT_STRICT=1 (staleFAIL).
capout="$(python3 SYSTEM/bin/cap_check.py 2>&1)"
if [ $? -eq 0 ]; then
  if printf '%s' "$capout" | grep -q '^WARN'; then
    ok "role digests under cap (with declared exceptions):"
    printf '%s\n' "$capout" | grep '^WARN' | while IFS= read -r w; do note "$w"; done
  else
    ok "role digests + orientation sections (Now & next ≤500, Milestones ≤400) under cap"
  fi
else
  capFAIL "role digest/section over cap without a declared exception:"
  printf '%s\n' "$capout" | grep '^FAIL' | while IFS= read -r w; do note "$w"; done
fi

# ---- 12. Areas/Horizons reviewed within cadence (WARN-only) ----------------
# GTD: projects owe a next action (check 10); areas/horizons owe a recent
# review (SYSTEM/bin/audit-area-reviews.sh, runbook Skills/DO/Review an
# Area.md). Overdue = WARN, never FAIL — a due review is a nudge, not a
# broken vault.
if ./SYSTEM/bin/audit-area-reviews.sh >/dev/null 2>&1; then
  ok "areas/horizons all reviewed within cadence"
else
  printf 'WARN  area/horizon review(s) overdue (run SYSTEM/bin/audit-area-reviews.sh for the list)\n'
fi

# ---- 13. .claude canonical ↔ visible mirrors in sync -----------------------
# Truth direction: .claude/skills/ and
# .claude/agents/ are canonical; Skills/<TYPE>/ and Agents/*.md are generated
# mirrors (SYSTEM/bin/build_claude_mirrors.py). Drift/hand-edits/orphans = red.
if mirrout=$(uv run python SYSTEM/bin/build_claude_mirrors.py --check 2>&1); then
  ok ".claude canonical and visible mirrors in sync"
else
  staleFAIL ".claude/visible mirror drift (run: uv run python SYSTEM/bin/build_claude_mirrors.py):"
  printf '%s\n' "$mirrout" | grep '^FAIL' | while IFS= read -r w; do note "$w"; done
fi

# ---- 14. Horizon/goal serving lists match up-links ------------------------
# Downward views on 01 Horizons/ (Goals/index.md, each goal note, vision,
# purpose) are generated from serves: up-links. Drift = forgot to regen.
if servesout=$(uv run python SYSTEM/bin/build_horizon_serves.py --check 2>&1); then
  ok "horizon/goal serving lists match serves: up-links"
else
  staleFAIL "horizon/goal serving lists stale (run: uv run python SYSTEM/bin/build_horizon_serves.py --write):"
  printf '%s\n' "$servesout" | grep '^FAIL' | while IFS= read -r w; do note "$w"; done
fi

rm -f "$valid" "$broken"
# ---- 15. index.md Projects section generated + current ----------------------
# The Pending/Live/Done lists between the
# <!-- projects:auto --> markers are built from each project's frontmatter +
# first Now & next paragraph (SYSTEM/bin/build_index_projects.py).
if projout=$(uv run python SYSTEM/bin/build_index_projects.py --check 2>&1); then
  ok "index.md Projects section current (generated)"
else
  staleFAIL "index.md Projects section stale (run: uv run python SYSTEM/bin/build_index_projects.py)"
fi

# ---- 15a. index.md Concepts + Areas sections generated + current ------------
# The Concepts + Areas lists are generated 1:1 from each note's own
# description: (SYSTEM/bin/build_index_lists.py).
if listsout=$(uv run python SYSTEM/bin/build_index_lists.py --check 2>&1); then
  ok "index.md Concepts + Areas sections current (generated)"
else
  staleFAIL "index.md Concepts/Areas sections stale (run: uv run python SYSTEM/bin/build_index_lists.py):"
  printf '%s\n' "$listsout" | grep '^FAIL' | while IFS= read -r w; do note "$w"; done
fi

# ---- 15b. contacts.md service directory generated + current -----------------
# Relations frontmatter: the block below the
# <!-- generated --> marker in 05 concepts/contacts.md is built from 04 People/
# frontmatter (type: org + operational relation: classes) so an un-indexed
# vendor is mechanically visible.
if contactsout=$(uv run python SYSTEM/bin/build_contacts_directory.py --check 2>&1); then
  ok "contacts.md service directory current (generated)"
else
  staleFAIL "contacts.md service directory stale (run: uv run python SYSTEM/bin/build_contacts_directory.py)"
fi

# ---- 15c. Per-folder directory indexes generated + current -----------------
# The folder-scoped index.md files (Concepts, Projects, Areas, Assets, People,
# Agents, raw) carry a freshness stamp and are drift-checked here.
if dirixout=$(uv run python SYSTEM/bin/build_directory_indexes.py --check 2>&1); then
  ok "per-folder directory indexes current (generated)"
else
  staleFAIL "per-folder directory indexes stale (run: uv run python SYSTEM/bin/build_directory_indexes.py --write):"
  printf '%s\n' "$dirixout" | grep '^FAIL' | while IFS= read -r w; do note "$w"; done
fi

# ---- 16. Compile debt: raw captures never linked from a compiled note (WARN) ----
# Compile-debt gauge. A raw/ capture that no concept/project/area/
# person/daily note links is un-compiled knowledge. WARN-only: raw/ is
# append-only and some captures are legitimately reference-only.
orphans=""; ncap=0
corpus_tmp="$(mktemp)"
find . -name '*.md' -not -path './raw/*' -not -path './SYSTEM/*' -not -path './.git/*' -not -path './.obsidian/*' -not -path './.venv/*' -print0 2>/dev/null \
  | xargs -0 cat 2>/dev/null > "$corpus_tmp"
for f in raw/20*.md; do
  [ -e "$f" ] || continue
  ncap=$((ncap+1)); b="$(basename "$f" .md)"
  grep -qF "raw/$b" "$corpus_tmp" || orphans="$orphans $b"
done
rm -f "$corpus_tmp"
norph=$(printf '%s' "$orphans" | wc -w | tr -d ' ')
if [ "$norph" -eq 0 ]; then ok "every raw/ capture is linked from a compiled note (0/$ncap orphans)"
else printf 'WARN  %s of %s raw/ captures have no inbound link from a compiled note (compile or link them; full list: SYSTEM/kb-stats.md):\n' "$norph" "$ncap"; for o in $orphans; do note "raw/$o.md"; done | head -8; fi

# ---- 17. Link-map: no duplicate keys, no parser-landmine [[aliases:]] ------
# YAML block-list aliases used to emit a bogus [[aliases:]] row and drop the
# real nicknames. Duplicate keys mean two notes claim the
# same [[target]] (e.g. an org and a person sharing a name as an alias).
lm="SYSTEM/link-map.md"
if [ ! -f "$lm" ]; then
  bad "SYSTEM/link-map.md missing (run SYSTEM/bin/build-link-map.sh)"
else
  lm_fail=""
  if grep -qF '| `[[aliases:]]` |' "$lm"; then
    lm_fail="$lm_fail aliases-landmine"
  fi
  lm_dups="$(awk -F'`' '/^\| `/ {print $2}' "$lm" | sort | uniq -d)"
  if [ -n "$lm_dups" ]; then
    lm_fail="$lm_fail duplicates"
  fi
  if [ -z "$lm_fail" ]; then
    ok "link-map has unique keys and no [[aliases:]] landmine"
  else
    bad "link-map keys unhealthy (run SYSTEM/bin/build-link-map.sh after fixing aliases):"
    [ -n "$lm_dups" ] && printf '%s\n' "$lm_dups" | while IFS= read -r d; do note "duplicate $d"; done
    printf '%s' "$lm_fail" | grep -q aliases-landmine && note "bogus [[aliases:]] row (YAML block-list parser bug)"
  fi
fi

# ---- 18. Quick map skeleton is not a status log ----------------------------
# One-liners single-source from stable description: fields. ISO dates and
# status words in the injected skeleton are how the Quick map turns back into
# a dashboard and overflows the injection budget.
# Detail belongs in the generated Projects section.
skel="$(awk '/^## /{c++; if(c==2) exit} {print}' index.md)"
qm_fail=""
if printf '%s' "$skel" | grep -qE '[0-9]{4}-[0-9]{2}-[0-9]{2}'; then
  qm_fail="$qm_fail iso-dates"
fi
if printf '%s' "$skel" | grep -qiE 'overdue|awaiting|ADOPTED|follow up'; then
  qm_fail="$qm_fail status-words"
fi
if [ -z "$qm_fail" ]; then
  ok "index Quick map skeleton has no volatile status (ISO dates / overdue / awaiting / ADOPTED)"
else
  bad "index Quick map skeleton looks like a status log ($qm_fail) — one-liners must be stable description: essence; status lives in each note + the generated Projects section"
fi

echo
if [ "$fail" = 0 ]; then echo "LINT: green (mechanical checks)"; else echo "LINT: problems found"; fi
echo "(judgment checks — stale facts, resolved open questions, actions still open — remain a manual/LLM pass)"
exit $fail
