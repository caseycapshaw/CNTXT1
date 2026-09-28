#!/usr/bin/env python3
"""build_index_projects.py — generate the `## Projects` section of index.md.

The section between the markers
    <!-- projects:auto:start -->  …  <!-- projects:auto:end -->
is rewritten from every project note's own frontmatter + the first paragraph
of its `## Now & next` (03 Projects/*.md live/pending, 03 Projects/archive/
done). Hand prose above/below the markers is untouched. This is the
"downward views are generated, never hand-maintained" rule applied to the
index itself — it removes the duplicated status
paragraphs that went stale beside each note's Now & next.

The Quick-map Projects (live) line at the top of index.md stays HAND-written:
its glosses are curated judgment and it is what the boot bundle injects.

Usage (vault root):  uv run python SYSTEM/bin/build_index_projects.py [--check]
  --check  exit 1 if the generated block is stale (lint check 15), write nothing.
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
PROJECTS = ROOT / FOLDERS["projects"]
INDEX = ROOT / "index.md"
START, END = "<!-- projects:auto:start -->", "<!-- projects:auto:end -->"
NOW_WORDS = 60  # words of Now & next quoted per live/pending project


def _fm_and_body(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    try:
        fm = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, text[end + 4 :]


def _now_snippet(body: str) -> str:
    """First paragraph of `## Now & next`, clipped to NOW_WORDS words."""
    m = re.search(r"^## Now & next\s*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    if not m:
        return ""
    para = ""
    for block in re.split(r"\n\s*\n", m.group(1).strip()):
        block = block.strip()
        if block and not block.startswith("_") and not block.startswith("###"):
            para = block
            break
    para = re.sub(r"\s+", " ", para)
    words = para.split()
    if len(words) > NOW_WORDS:
        para = " ".join(words[:NOW_WORDS]).rstrip(",;:—-") + " …"
    return para


def _link(v) -> str:
    """Normalise an up-link value ('[[x]]' or list) to ' · '-joined wikilinks."""
    if not v:
        return ""
    items = v if isinstance(v, list) else [v]
    return " · ".join(str(i).strip() for i in items if str(i).strip())


def _entry(path: Path, fm: dict, body: str) -> str:
    slug = path.stem
    status = str(fm.get("status", "?"))
    started = fm.get("started", "?")
    updated = fm.get("updated", "")
    desc = str(fm.get("description", "")).strip().rstrip(".")
    if status == "done":
        span = f"{started} → {updated}" if updated else f"{started}"
        return f"- **[[{slug}]]** *(done, {span})* — {desc}."
    now = _now_snippet(body)
    ups = []
    if fm.get("area"):
        ups.append(f"Up-link: {_link(fm['area'])}")
    if fm.get("serves"):
        ups.append(f"serves {_link(fm['serves'])}")
    tail = f" {' · '.join(ups)}." if ups else ""
    now_part = f" **Now:** {now}" if now else ""
    return f"- **[[{slug}]]** *({status}, started {started}; updated {updated})* — {desc}.{now_part}{tail}"


def _collect() -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {"pending": [], "live": [], "done": []}
    for folder, want_done in ((PROJECTS, False), (PROJECTS / "archive", True)):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            if path.name.endswith(" TEMPLATE.md") or path.name == "index.md":
                continue
            fm, body = _fm_and_body(path)
            if fm.get("type") != "project":
                continue
            status = str(fm.get("status", ""))
            if want_done or status == "done":
                groups["done"].append((str(fm.get("updated", "")), _entry(path, fm, body)))
            elif status == "pending":
                groups["pending"].append((str(fm.get("started", "")), _entry(path, fm, body)))
            else:
                groups["live"].append((str(fm.get("updated", "")), _entry(path, fm, body)))
    # live + done: most recently updated first; pending: newest first
    return {k: [e for _, e in sorted(v, reverse=True)] for k, v in groups.items()}


def _block() -> str:
    g = _collect()
    stamp = dt.date.today().isoformat()
    lines = [
        START,
        f"_Generated {stamp} by `SYSTEM/bin/build_index_projects.py` from each note's frontmatter + first paragraph of Now & next — do not hand-edit between the markers. Live/done ordered by `updated:`._",
        "",
        "**Pending** (opened but not yet actively worked — waiting on a trigger):",
        *(g["pending"] or ["- _none_"]),
        "",
        "**Live:**",
        *(g["live"] or ["- _none_"]),
        "",
        "**Done** (archived in `03 Projects/archive/`):",
        *(g["done"] or ["- _none_"]),
        END,
    ]
    return "\n".join(lines)


def main() -> int:
    check = "--check" in sys.argv
    text = INDEX.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print(f"FAIL index.md: missing {START} / {END} markers")
        return 1
    pre, rest = text.split(START, 1)
    _, post = rest.split(END, 1)
    new_block = _block()
    # Compare ignoring the date stamp so a --check on a later day isn't "stale".
    strip = lambda s: re.sub(r"_Generated \d{4}-\d{2}-\d{2}", "_Generated", s)
    current = START + rest.split(END, 1)[0] + END
    if strip(current) == strip(new_block):
        print("PASS  index.md Projects section current")
        return 0
    if check:
        print("FAIL  index.md Projects section stale (run: uv run python SYSTEM/bin/build_index_projects.py)")
        return 1
    INDEX.write_text(pre + new_block + post, encoding="utf-8")
    print("wrote index.md Projects section")
    return 0


if __name__ == "__main__":
    sys.exit(main())
