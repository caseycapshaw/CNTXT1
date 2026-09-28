# kb-folders.sh — numbered content-folder names (Obsidian file-explorer sort).
# Source after cd to the vault root. Keep in lockstep with kb-folders.json.
# shellcheck disable=SC2034
KB_DAILY="00 daily"
KB_HORIZONS="01 Horizons"
KB_HORIZON_GOALS="01 Horizons/Goals"
KB_AREAS="02 Areas"
KB_PROJECTS="03 Projects"
KB_PEOPLE="04 People"
KB_CONCEPTS="05 concepts"

# Emit one alias per line from a note's frontmatter. Understands both
# `aliases: [a, b]` and YAML block lists (`aliases:\n  - a`). The old
# grep -m1 + strip-brackets parser treated a block list's `aliases:` key
# as a wikilink target (see 2026-09-08 system audit).
extract_aliases() {
  python3 - "$1" <<'PY'
import re, sys
path = sys.argv[1]
try:
    text = open(path, encoding="utf-8").read()
except OSError:
    sys.exit(0)
if not text.startswith("---"):
    sys.exit(0)
parts = text.split("---", 2)
if len(parts) < 3:
    sys.exit(0)
fm = parts[1]
m = re.search(r"(?m)^aliases:\s*\[(.*?)\]\s*$", fm)
if m:
    inner = m.group(1).strip()
    if inner:
        for a in inner.split(","):
            a = a.strip().strip("'\"")
            if a:
                print(a)
    sys.exit(0)
m = re.search(r"(?m)^aliases:\s*\n((?:[ \t]+-[ \t]+.+\n?)*)", fm)
if not m:
    sys.exit(0)
for line in m.group(1).splitlines():
    item = re.sub(r"^\s*-\s*", "", line).strip().strip("'\"")
    if item:
        print(item)
PY
}
