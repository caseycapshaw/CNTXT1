#!/usr/bin/env bash
# migrate-to-numbered-layout.sh — one-shot helper for moving an existing kit
# instance from the old `Knowledge/…` layout to the numbered GTD layout
# (00 daily … 05 concepts). Read MIGRATING.md first.
#
#   Knowledge/Concepts/    -> 05 concepts/
#   Knowledge/Initiatives/ -> 03 Projects/         (Initiative -> Project)
#   Knowledge/People/      -> 04 People/
#   Knowledge/Skills/      -> Skills/
#   Knowledge/Agents/      -> Agents/
#   Knowledge/raw/         -> raw/
#   Knowledge/Excalidraw/  -> excalidraw/
#   Knowledge/Actions.md   -> Actions.md
#   daily/                 -> 00 daily/
#
# Merge-safe: never overwrites a file that already exists at the destination
# (e.g. scaffolding a `git pull` already created) — collisions are listed for
# you to resolve by hand. Uses `git mv` for tracked files, plain `mv` otherwise
# (clone-mode users' notes are untracked). Then it rewrites old path prefixes
# in your markdown, flips `type: initiative` -> `type: project`, and lists
# live projects still missing the required `area:` up-link.
#
# Usage (vault root):
#   SYSTEM/bin/migrate-to-numbered-layout.sh            # dry run — prints the plan
#   SYSTEM/bin/migrate-to-numbered-layout.sh --apply    # do it
set -uo pipefail
_BIN="$(cd "$(dirname "$0")" && pwd)"
cd "$_BIN/../.."   # vault root
apply=0
case "${1:-}" in --apply) apply=1 ;; "") ;; *) echo "usage: $0 [--apply]" >&2; exit 2 ;; esac

MAP=(
  "Knowledge/Concepts|05 concepts"
  "Knowledge/Initiatives|03 Projects"
  "Knowledge/People|04 People"
  "Knowledge/Skills|Skills"
  "Knowledge/Agents|Agents"
  "Knowledge/raw|raw"
  "Knowledge/Excalidraw|excalidraw"
  "daily|00 daily"
)

collisions=()
moved=0
is_tracked() { git ls-files --error-unmatch -- "$1" >/dev/null 2>&1; }

do_move() { # $1=src file  $2=dest file
  local src="$1" dest="$2"
  if [ -e "$dest" ]; then collisions+=("$src -> $dest (destination exists — resolve by hand)"); return; fi
  moved=$((moved + 1))
  if [ "$apply" = 1 ]; then
    mkdir -p "$(dirname "$dest")"
    if is_tracked "$src"; then git mv -- "$src" "$dest" 2>/dev/null || mv -n -- "$src" "$dest"; else mv -n -- "$src" "$dest"; fi
  else
    echo "  mv  $src  ->  $dest"
  fi
}

echo "== move files =="
for pair in "${MAP[@]}"; do
  src="${pair%%|*}"; dst="${pair##*|}"
  [ -d "$src" ] || continue
  while IFS= read -r -d '' f; do
    rel="${f#"$src"/}"
    do_move "$f" "$dst/$rel"
  done < <(find "$src" -type f ! -name .DS_Store -print0)
done
[ -f Knowledge/Actions.md ] && { [ -f Actions.md ] && collisions+=("Knowledge/Actions.md -> Actions.md (exists)") || do_move Knowledge/Actions.md Actions.md; }

# Renames inside the new layout: Initiative -> Project artifacts.
ren() { # $1=old  $2=new
  [ -e "$1" ] || return 0
  [ -e "$2" ] && { collisions+=("$1 -> $2 (destination exists)"); return; }
  if [ "$apply" = 1 ]; then
    if is_tracked "$1"; then git mv -- "$1" "$2" 2>/dev/null || mv -n -- "$1" "$2"; else mv -n -- "$1" "$2"; fi
  else echo "  mv  $1  ->  $2"; fi
}
ren "03 Projects/Initiative TEMPLATE.md" "03 Projects/Project TEMPLATE.md"
ren "Agents/initiative-worker.md" "Agents/project-worker.md"
ren ".claude/agents/initiative-worker.md" ".claude/agents/project-worker.md"
ren "Skills/DO/Run an Initiative.md" "Skills/DO/Run a Project.md"
ren "Skills/DO/Delegate an Initiative to a CMUX Workspace.md" "Skills/DO/Delegate a Project to a CMUX Workspace.md"
ren ".claude/skills/run-an-initiative" ".claude/skills/run-a-project"
ren ".claude/skills/delegate-an-initiative-to-a-cmux-workspace" ".claude/skills/delegate-a-project-to-a-cmux-workspace"

echo
echo "== rewrite old path prefixes + Initiative terminology in markdown =="
if [ "$apply" = 1 ]; then
  python3 - <<'PY'
import re, pathlib
ROOT = pathlib.Path(".")
PATHS = [
  ("Knowledge/Concepts", "05 concepts"), ("Knowledge/Initiatives", "03 Projects"),
  ("Knowledge/People", "04 People"), ("Knowledge/Skills", "Skills"),
  ("Knowledge/Agents", "Agents"), ("Knowledge/raw", "raw"),
  ("Knowledge/Excalidraw", "excalidraw"), ("Knowledge/Actions.md", "Actions.md"),
]
SKIP = {".git", ".venv", "node_modules", ".obsidian", "attachments"}
changed = 0
for p in ROOT.rglob("*.md"):
    if any(part in SKIP for part in p.parts) or p.name == "MIGRATING.md":
        continue
    s0 = p.read_text(encoding="utf-8", errors="replace")
    s = s0
    for a, b in PATHS:
        s = s.replace(a, b)
    s = re.sub(r"(?<![\w/])daily/", "00 daily/", s)          # bare daily/ path refs
    s = re.sub(r"\b([Aa])n [Ii]nitiative", lambda m: m.group(1) + " project", s)
    s = s.replace("Initiatives", "Projects").replace("initiatives", "projects")
    s = s.replace("Initiative", "Project").replace("initiative", "project")
    s = s.replace("run-an-project", "run-a-project").replace("delegate-an-project-to", "delegate-a-project-to")
    if s != s0:
        p.write_text(s, encoding="utf-8"); changed += 1
print(f"  rewrote {changed} markdown file(s)")
PY
else
  echo "  (dry run — would rewrite Knowledge/<X>/ path prefixes, daily/ -> 00 daily/, Initiative -> Project)"
fi

echo
echo "== projects: frontmatter check =="
for f in "03 Projects"/*.md "03 Projects"/archive/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *TEMPLATE*|*/index.md) continue ;; esac
  if [ "$apply" = 1 ]; then
    sed -i.bak -E 's/^type:[[:space:]]*initiative[[:space:]]*$/type: project/; s/^(tags:.*)initiative/\1project/' "$f" && rm -f "$f.bak"
  fi
  st="$(awk '/^---$/{c++; next} c==1 && /^status:/{sub(/^status:[[:space:]]*/,""); sub(/[[:space:]]*#.*$/,""); print; exit} c==2{exit}' "$f")"
  if [ "$st" != "done" ] && ! awk '/^---$/{c++; next} c==1 && /^area:/{f=1} c==2{exit} END{exit !f}' "$f"; then
    echo "  NEEDS area: up-link -> $f   (add: area: \"[[<02 Areas slug>]]\")"
  fi
done

echo
if [ "${#collisions[@]}" -gt 0 ]; then
  echo "== collisions (not overwritten) =="; printf '  %s\n' "${collisions[@]}"; echo
fi
if [ "$apply" = 1 ]; then
  # tidy: drop now-empty old dirs
  find Knowledge daily -type d -empty -delete 2>/dev/null || true
  [ -d Knowledge ] && find Knowledge -name .DS_Store -delete 2>/dev/null && rmdir Knowledge 2>/dev/null || true
  echo "moved $moved file(s). Next: create 02 Areas/ notes for your projects' area: up-links,"
  echo "then SYSTEM/bin/build-link-map.sh && SYSTEM/bin/regen-all.sh && SYSTEM/bin/lint.sh (see MIGRATING.md)."
else
  echo "dry run: $moved file(s) would move. Re-run with --apply."
fi
