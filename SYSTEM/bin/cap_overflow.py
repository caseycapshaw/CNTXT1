#!/usr/bin/env python3
"""cap_overflow.py — auto-drain an over-cap `## Milestones` section into its
note's trail file (SYSTEM/SCHEMA.md § Conventions, orientation caps).

Word caps (SYSTEM/bin/cap_check.py, surfaced by lint.sh) are WARN by
default — but a WARN a human never has to act on is just
noise, so this script is the mechanical remedy for the `## Milestones` half
of that WARN: it moves the OLDEST bullet entries (top of the section — the
convention is chronological, oldest first) out of the note and into
`Knowledge/Initiatives/trails/<slug>-trail.md`,
verbatim, exactly the move SYSTEM/SCHEMA.md already describes for a human
doing it by hand — until the section is back under cap. A pointer line is
left in its place. `## Now & next` is deliberately NOT touched here — that
section is rewritten prose (state, not a bulleted log), which is exactly
the shape an LLM pass (or you) should rewrite, not a mechanical mover.

Bullet unit = a top-level `- ` line plus any indented continuation lines
that follow it (mirrors SYSTEM/bin/actions.py's bullet-joining logic).
Multi-line bullets (blank-line-separated paragraphs under one leading `-`
line) are kept intact as one unit.

Deterministic, idempotent, dry-run by default.

Usage (vault root):
  python3 SYSTEM/bin/cap_overflow.py            # report what WOULD move
  python3 SYSTEM/bin/cap_overflow.py --write     # actually move it
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent
CONFIG = Path(__file__).resolve().parent / "cap_config.json"
HEADING = "## Milestones"
TRAIL_HEADING = "## Milestones (older entries, as written)"


def split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[4:end], text[end + 4:]
    return "", text


def fm_value(fm: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", fm, re.MULTILINE)
    return m.group(1) if m else None


def find_section(body: str, heading: str) -> tuple[int, int, int] | None:
    """Return (heading_line_idx, content_start_idx, content_end_idx) of the
    `## heading` section — indices are into body.splitlines(keepends=True)."""
    lines = body.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if line.rstrip("\n") == heading:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return start, start + 1, end


def parse_bullets(section_lines: list[str]) -> tuple[list[str], list[str]]:
    """Split section lines into (preamble_non_bullet_lines, bullet_units).
    A bullet unit is one or more raw lines (kept verbatim, newline-terminated)
    starting with a top-level `- `. Preamble = any leading non-bullet lines
    (e.g. a pointer note already left by a prior overflow run)."""
    preamble: list[str] = []
    units: list[list[str]] = []
    i = 0
    n = len(section_lines)
    # leading blank/non-bullet lines are preamble
    while i < n and not section_lines[i].startswith("- "):
        preamble.append(section_lines[i])
        i += 1
    while i < n:
        if section_lines[i].startswith("- "):
            unit = [section_lines[i]]
            i += 1
            # absorb continuation lines (indented, or blank line followed by
            # indented/non-bullet content) up to the next top-level bullet
            while i < n and not section_lines[i].startswith("- "):
                unit.append(section_lines[i])
                i += 1
            units.append(unit)
        else:
            i += 1
    return preamble, units


def word_count(lines: list[str]) -> int:
    return len(" ".join(l.strip() for l in lines).split())


def trail_path(note_path: Path) -> Path:
    parent = note_path.parent
    return parent / "trails" / f"{note_path.stem}-trail.md"


def build_new_trail(note_path: Path, fm: str, moved: list[str]) -> str:
    slug = note_path.stem
    desc_val = f'Append-only history moved out of {slug} by SYSTEM/bin/cap_overflow.py (Milestones over the {400}-word cap) — moved verbatim, nothing edited.'
    tags_m = re.search(r"^tags:\s*\[([^\]]*)\]", fm, re.MULTILINE)
    tags = "[trail" + (f", {tags_m.group(1)}" if tags_m else "") + "]"
    today = dt.date.today().isoformat()
    rel = note_path.relative_to(VAULT)
    header = (
        "---\n"
        "type: trail\n"
        f'of: "[[{slug}]]"\n'
        f"description: {desc_val}\n"
        f"updated: {today}\n"
        f"tags: {tags}\n"
        "---\n\n"
        f"# Trail — {slug} (history moved from the initiative note)\n\n"
        f"Moved verbatim on {today} by `SYSTEM/bin/cap_overflow.py` "
        "(SYSTEM/SCHEMA.md caps: Milestones ≤400 words). Nothing edited. "
        f"Live state: `{rel}`.\n\n"
        f"{TRAIL_HEADING}\n\n"
    )
    return header + "".join(moved)


def append_to_existing_trail(text: str, moved: list[str]) -> str:
    body_fm, body = split_frontmatter(text)
    sec = find_section(body, TRAIL_HEADING)
    addition = "".join(moved)
    if sec is None:
        # no matching heading yet — append a new section at the end
        if not body.endswith("\n"):
            body += "\n"
        body += f"\n{TRAIL_HEADING}\n\n{addition}"
    else:
        _, content_start, content_end = sec
        lines = body.splitlines(keepends=True)
        insert_at = content_end
        # insert before the section's trailing blank line if present
        while insert_at > content_start and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        lines[insert_at:insert_at] = [addition] if addition.endswith("\n") else [addition + "\n"]
        body = "".join(lines)
    # update updated: stamp
    today = dt.date.today().isoformat()
    if re.search(r"^updated:\s*.+$", body_fm, re.MULTILINE):
        body_fm = re.sub(r"^updated:\s*.+$", f"updated: {today}", body_fm, count=1, flags=re.MULTILINE)
    return "---\n" + body_fm + "\n---" + body


def process(note_path: Path, cap: int, write: bool) -> str | None:
    text = note_path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    sec = find_section(body, HEADING)
    if sec is None:
        return None
    _, content_start, content_end = sec
    lines = body.splitlines(keepends=True)
    section_lines = lines[content_start:content_end]
    words = word_count(section_lines)
    if words <= cap:
        return None

    preamble, units = parse_bullets(section_lines)
    if not units:
        return f"SKIP {note_path.relative_to(VAULT)}: over cap ({words}/{cap}) but no bullet units found — needs a human rewrite"

    to_move: list[list[str]] = []
    kept = list(units)
    while kept:
        remaining_words = word_count(preamble) + word_count([l for u in kept for l in u])
        if remaining_words <= cap:
            break
        to_move.append(kept.pop(0))

    if not to_move:
        return f"SKIP {note_path.relative_to(VAULT)}: over cap ({words}/{cap}) but moving whole bullets can't get it under cap — needs a human rewrite"

    tpath = trail_path(note_path)
    moved_lines = [l for u in to_move for l in u]
    slug = note_path.stem
    pointer = f"_Earlier milestones moved to [[{tpath.stem}]]._\n\n"

    msg = (
        f"{'WROTE' if write else 'WOULD MOVE'} {note_path.relative_to(VAULT)}: "
        f"{len(to_move)} oldest Milestones bullet(s) -> {tpath.relative_to(VAULT)} "
        f"({words} -> {word_count(preamble) + word_count([l for u in kept for l in u])} words)"
    )
    if not write:
        return msg

    # 1) update/create the trail file
    if tpath.exists():
        tpath.write_text(append_to_existing_trail(tpath.read_text(encoding="utf-8"), moved_lines), encoding="utf-8")
    else:
        tpath.parent.mkdir(parents=True, exist_ok=True)
        tpath.write_text(build_new_trail(note_path, fm, moved_lines), encoding="utf-8")

    # 2) rewrite the source note's Milestones section (preamble stays,
    #    pointer line first, then the kept bullets)
    new_section = [pointer] + preamble + [l for u in kept for l in u]
    lines[content_start:content_end] = new_section
    new_body = "".join(lines)
    new_text = f"---\n{fm}\n---{new_body}" if fm else new_body
    note_path.write_text(new_text, encoding="utf-8")
    return msg


def main() -> int:
    write = "--write" in sys.argv
    if not CONFIG.exists():
        print(f"FAIL cap_overflow: config missing ({CONFIG})")
        return 1
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cap = 400
    globs: list[str] = []
    for sec in cfg.get("sections", []):
        if sec.get("heading") == HEADING:
            cap = int(sec["cap_words"])
            globs = sec.get("globs", [])
            break
    if not globs:
        print("PASS cap_overflow: no Milestones section registered in cap_config.json")
        return 0

    any_over = False
    for glob in globs:
        for path in sorted(VAULT.glob(glob)):
            if path.name.endswith(" TEMPLATE.md"):
                continue
            result = process(path, cap, write)
            if result:
                any_over = True
                print(result)
    if not any_over:
        print("PASS cap_overflow: no Milestones sections over cap")
    elif not write:
        print("\n(dry run — re-run with --write to apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
