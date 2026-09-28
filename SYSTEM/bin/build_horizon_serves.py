#!/usr/bin/env python3
"""Rewrite generated serving lists on horizon and goal notes from serves: up-links.

Reads area/project `serves:` frontmatter and writes markdown below
`<!-- generated -->` on:
  - 01 Horizons/Goals/index.md  (the outcome notes)
  - 01 Horizons/Goals/<slug>.md (areas + live projects serving that goal)
  - 01 Horizons/vision.md / purpose-principles.md (anyone serving the whole horizon)

Default is dry-run (print drift, exit 1 if any). --write applies. --check is
an alias of dry-run for lint.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FOLDERS = json.loads((Path(__file__).resolve().parent / "kb-folders.json").read_text())
HORIZONS = REPO_ROOT / _FOLDERS["horizons"]
GOALS_DIR = REPO_ROOT / _FOLDERS["horizon_goals"]
AREAS = REPO_ROOT / _FOLDERS["areas"]
PROJECTS = REPO_ROOT / _FOLDERS["projects"]
MARKER = "<!-- generated -->"
STAMP_PREFIX = "_Generated:"
TOOL = "build_horizon_serves.py"
HORIZON_SLUGS = {"goals", "vision", "purpose-principles"}


def _fm(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    data = yaml.safe_load(parts[1])
    return data if isinstance(data, dict) else {}


def _slug(wikilink: str) -> str:
    s = wikilink.strip()
    if s.startswith("[[") and s.endswith("]]"):
        s = s[2:-2]
    return s.split("|", 1)[0].strip()


def _serves_slugs(data: dict) -> list[str]:
    raw = data.get("serves")
    if raw is None:
        return []
    items = raw if isinstance(raw, list) else [raw]
    return [_slug(x) for x in items if x]


def _notes(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        p for p in folder.glob("*.md")
        if not p.name.endswith(" TEMPLATE.md")
    )


def _collect() -> tuple[dict, dict, dict, set[str]]:
    """areas, projects, goals keyed by slug; plus the allowed serves targets."""
    areas: dict[str, dict] = {}
    for p in _notes(AREAS) + _notes(AREAS / "Assets"):
        data = _fm(p)
        slug = p.stem
        data["_path"] = p
        data["_link"] = f"[[{slug}]]"
        areas[slug] = data

    projects: dict[str, dict] = {}
    for p in _notes(PROJECTS):
        data = _fm(p)
        if data.get("status") == "done":
            continue
        slug = p.stem
        data["_path"] = p
        data["_link"] = f"[[{slug}]]"
        projects[slug] = data

    goals: dict[str, dict] = {}
    for p in _notes(GOALS_DIR):
        if p.name == "index.md":
            continue
        data = _fm(p)
        if data.get("type") != "goal":
            continue
        slug = p.stem
        data["_path"] = p
        data["_link"] = f"[[{slug}]]"
        goals[slug] = data

    allowed = set(goals) | HORIZON_SLUGS
    return areas, projects, goals, allowed


def _serving(areas: dict, projects: dict, target: str) -> tuple[list[dict], list[dict]]:
    a = [v for v in areas.values() if target in _serves_slugs(v)]
    p = [v for v in projects.values() if target in _serves_slugs(v)]
    a.sort(key=lambda x: x["_link"].lower())
    p.sort(key=lambda x: x["_link"].lower())
    return a, p


def _list_line(items: list[dict], empty: str) -> str:
    if not items:
        return empty
    return " · ".join(i["_link"] for i in items)


def _goal_body(goal: dict, areas: dict, projects: dict) -> str:
    slug = goal["_path"].stem
    a, p = _serving(areas, projects, slug)
    live_p = [x for x in p if x.get("status") != "pending"]
    pending_p = [x for x in p if x.get("status") == "pending"]
    lines = [
        f"{STAMP_PREFIX} {dt.date.today().isoformat()} by {TOOL} — do not hand-edit below the marker._",
        "",
        "## Serving this goal",
        "",
        f"**Areas:** {_list_line(a, '_(none)_')}",
        f"**Projects (live):** {_list_line(live_p, '_(none)_')}",
    ]
    if pending_p:
        lines.append(f"**Projects (pending):** {_list_line(pending_p, '_(none)_')}")
    lines.append("")
    return "\n".join(lines)


def _index_body(goals: dict) -> str:
    ordered = sorted(goals.values(), key=lambda g: (int(g.get("order") or 99), g["_path"].stem))
    lines = [
        f"{STAMP_PREFIX} {dt.date.today().isoformat()} by {TOOL} — do not hand-edit below the marker._",
        "",
        "## Goals",
        "",
    ]
    for g in ordered:
        n = g.get("order") or "?"
        desc = (g.get("description") or "").rstrip(".")
        lines.append(f"{n}. **{g['_link']}** — {desc}.")
        lines.append("")
    lines.append("_Each goal note has the live serving list. This index is the H3 door._")
    lines.append("")
    return "\n".join(lines)


def _horizon_body(slug: str, areas: dict, projects: dict) -> str:
    a, p = _serving(areas, projects, slug)
    lines = [
        f"{STAMP_PREFIX} {dt.date.today().isoformat()} by {TOOL} — do not hand-edit below the marker._",
        "",
        "## Serving this horizon",
        "",
        f"**Areas:** {_list_line(a, '_(none)_')}",
        f"**Projects:** {_list_line(p, '_(none)_')}",
        "",
    ]
    return "\n".join(lines)


def _strip_stamp(block: str) -> str:
    return "\n".join(l for l in block.splitlines() if not l.startswith(STAMP_PREFIX))


def _split(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    if MARKER not in text:
        raise SystemExit(f"FAIL {path.relative_to(REPO_ROOT)}: missing `{MARKER}` marker")
    head, _tail = text.split(MARKER, 1)
    return head, text


def _apply(path: Path, new_below: str, write: bool) -> bool:
    head, original = _split(path)
    new_text = head + MARKER + "\n\n" + new_below
    if not new_text.endswith("\n"):
        new_text += "\n"
    # Compare ignoring the date stamp so a --check on a later day than the
    # last --write isn't a false "stale" (the stamp always differs by a day).
    if write:
        changed = new_text != original
    else:
        changed = _strip_stamp(new_text) != _strip_stamp(original)
    if not changed:
        return False
    rel = path.relative_to(REPO_ROOT)
    if write:
        path.write_text(new_text, encoding="utf-8")
        print(f"wrote {rel}")
    else:
        print(f"FAIL {rel}: generated section stale")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="apply writes (default: dry-run)")
    parser.add_argument("--check", action="store_true", help="lint mode: exit 1 on drift")
    args = parser.parse_args()
    write = bool(args.write) and not args.check

    areas, projects, goals, allowed = _collect()
    unknown: list[str] = []
    for kind, bag in (("area", areas), ("project", projects)):
        for slug, data in bag.items():
            for target in _serves_slugs(data):
                if target not in allowed:
                    unknown.append(f"{kind} [[{slug}]] serves:[[{target}]]")
    if unknown:
        print("FAIL unknown serves: target(s) (not a goal slug or horizon):")
        for u in unknown:
            print(f"  FAIL {u}")
        return 1

    drifted = False
    index = GOALS_DIR / "index.md"
    if index.exists():
        drifted = _apply(index, _index_body(goals), write) or drifted
    for g in goals.values():
        drifted = _apply(g["_path"], _goal_body(g, areas, projects), write) or drifted
    for name in ("vision.md", "purpose-principles.md"):
        p = HORIZONS / name
        if p.exists():
            drifted = _apply(p, _horizon_body(p.stem, areas, projects), write) or drifted

    if write:
        return 0
    if drifted or unknown:
        return 1
    print("horizon/goal serving lists: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
