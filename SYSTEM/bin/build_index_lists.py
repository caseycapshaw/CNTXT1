#!/usr/bin/env python3
"""build_index_lists.py — generate the `## Concepts` and `## Areas` list
sections of index.md from each note's frontmatter.

The Concepts and Areas sections of index.md are fully derivable — one bullet
per note, 1:1 with the folder contents. This script generates them the same
way build_index_projects.py generates the Projects section: between
`<!-- ...-auto:start -->` / `...:end` markers, hand prose above/below untouched.

- Concepts: `- **[[slug]]** — {description}.` for every `05 concepts/*.md`
  (excluding TEMPLATE/index).
- Areas: `- **[[slug]]** {🔒 if tags: includes "private"} *({review:}
  cadence)* — {description}.` for every `02 Areas/*.md` (excluding
  TEMPLATE/index; `Assets/` sub-areas are NOT listed here — they're the
  parent area note's own body).

`description:` IS the index line; edit it in the note, not in index.md.

People and Skills sections are NOT generated: both list a curated subset,
not a 1:1 derivable list — the full directories already exist elsewhere
(05 concepts/contacts.md, the generated Skills/<TYPE>/<TYPE> Index.md files).
The Horizons section (a nested goal tree with hand-ordered children) is also
hand-maintained.

Usage (vault root):  uv run python SYSTEM/bin/build_index_lists.py [--check]
  --check  exit 1 if either generated block is stale, write nothing.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
FOLDERS = json.loads((Path(__file__).resolve().parent / "kb-folders.json").read_text())
CONCEPTS = ROOT / FOLDERS["concepts"]
AREAS = ROOT / FOLDERS["areas"]
INDEX = ROOT / "index.md"

C_START, C_END = "<!-- concepts:auto:start -->", "<!-- concepts:auto:end -->"
A_START, A_END = "<!-- areas:auto:start -->", "<!-- areas:auto:end -->"


def _fm(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    try:
        return yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return {}


def _desc(fm: dict) -> str:
    d = str(fm.get("description", "")).strip()
    return d.rstrip(".")


def _concepts_block() -> list[str]:
    lines = []
    for path in sorted(CONCEPTS.glob("*.md")):
        if path.name.endswith(" TEMPLATE.md") or path.name == "index.md":
            continue
        fm = _fm(path)
        desc = _desc(fm)
        if not desc:
            continue
        lines.append(f"- **[[{path.stem}]]** — {desc}.")
    return lines


def _areas_block() -> list[str]:
    lines = []
    for path in sorted(AREAS.glob("*.md")):
        if path.name.endswith(" TEMPLATE.md") or path.name == "index.md":
            continue
        fm = _fm(path)
        desc = _desc(fm)
        if not desc:
            continue
        tags = fm.get("tags") or []
        lock = " 🔒" if isinstance(tags, list) and "private" in tags else ""
        cadence = fm.get("review")
        cad = f" *({cadence})*" if cadence else ""
        lines.append(f"- **[[{path.stem}]]**{lock}{cad} — {desc}.")
    return lines


def _block(start: str, end: str, generator: str, source: str, body_lines: list[str]) -> str:
    stamp = dt.date.today().isoformat()
    return "\n".join([
        start,
        f"_Generated {stamp} by `SYSTEM/bin/{generator}` from each note's `description:` frontmatter — "
        f"do not hand-edit between the markers. To change an entry, edit that {source}'s `description:` "
        "and regenerate (SYSTEM/bin/regen-all.sh)._",
        "",
        *body_lines,
        end,
    ])


def _splice(text: str, start: str, end: str, new_block: str) -> tuple[str, bool]:
    if start not in text or end not in text:
        return text, False
    pre, rest = text.split(start, 1)
    _, post = rest.split(end, 1)
    current = start + rest.split(end, 1)[0] + end
    strip = lambda s: re.sub(r"_Generated \d{4}-\d{2}-\d{2}", "_Generated", s)
    if strip(current) == strip(new_block):
        return text, True  # already current, no write needed
    return pre + new_block + post, False


def main() -> int:
    check = "--check" in sys.argv
    text = INDEX.read_text(encoding="utf-8")

    missing = [m for m in (C_START, C_END, A_START, A_END) if m not in text]
    if missing:
        print(f"FAIL index.md: missing marker(s): {', '.join(missing)}")
        return 1

    concepts_block = _block(C_START, C_END, "build_index_lists.py", "concept note", _concepts_block())
    areas_block = _block(A_START, A_END, "build_index_lists.py", "area note", _areas_block())

    rc = 0
    for name, start, end, block in (
        ("Concepts", C_START, C_END, concepts_block),
        ("Areas", A_START, A_END, areas_block),
    ):
        new_text, current = _splice(text, start, end, block)
        if current:
            print(f"PASS  index.md {name} section current")
            continue
        if check:
            print(f"FAIL  index.md {name} section stale (run: uv run python SYSTEM/bin/build_index_lists.py)")
            rc = 1
            continue
        text = new_text
        print(f"wrote index.md {name} section")

    if not check and rc == 0:
        INDEX.write_text(text, encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())
