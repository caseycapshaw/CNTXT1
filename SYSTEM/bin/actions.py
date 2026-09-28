#!/usr/bin/env python3
"""actions.py — the action scheduler's census.

The Obsidian Tasks plugin renders Actions.md for you; an agent cannot see
that render. This script gives both the same dashboard: it scans every open
`- [ ] … #action` line in the content folders and rewrites the block between

    <!-- actions:auto:start -->  …  <!-- actions:auto:end -->

in Actions.md with counts, the #priority list, per-home totals, machine-made
(#auto) share, and the STALE list (open actions whose ➕ created-date stamp
is older than --stale-days, default 30) — the weekly aging pass reads that
list. Age is measured from the ➕ stamp specifically (backfill-action-dates.sh
/ aging-actions.sh), not from any other date the line happens to mention (a
📅 due date, a quoted fact). A line with no ➕ stamp has UNKNOWN age — it is
reported as its own count, never silently folded into "not stale" (an
embedded-date grep as an age proxy undercounts staleness: undated actions
would be invisibly excluded from the stale list). This script never
bulk-adds dates; that's the backfill script's job. Stdlib only;
never edits an action line itself.

Usage (vault root):
  python3 SYSTEM/bin/actions.py            # report to stdout
  python3 SYSTEM/bin/actions.py --write    # rewrite the Actions.md block
                                           # (Actions.md must already contain the
                                           #  two marker lines below)
  python3 SYSTEM/bin/actions.py --json
  python3 SYSTEM/bin/actions.py --stale-days 45 --write
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent
# Actions.md is a root anchor in a live instance; the starter ships it at Knowledge/Actions.md.
ACTIONS_MD = next((p for p in (VAULT / "Actions.md", VAULT / "Knowledge" / "Actions.md") if p.exists()), VAULT / "Actions.md")
START, END = "<!-- actions:auto:start -->", "<!-- actions:auto:end -->"
# ===== Folder names — edit here if your instance renames the content folders =====
SCAN = ["Knowledge/Concepts", "Knowledge/Initiatives", "Knowledge/People", "Knowledge/Agents", "Knowledge/raw", "daily"]
# Root-level files outside SCAN that are registered #action homes in their own
# right (AGENTS.md § Inbox rule): the upstream-kit-updates queue can carry a
# real open #action, and root files are otherwise out of scope.
EXTRA_FILES = ["Upstream kit updates (pending).md"]
SKIP_PARTS = {"trails", "archive"}
CHECKBOX_RE = re.compile(r"^\s*- \[ \] (.*)$")
CONTINUATION_RE = re.compile(r"^\s+\S")  # indented, non-blank — a wrapped continuation line
# ➕ YYYY-MM-DD is the created-date stamp (see backfill-action-dates.sh /
# aging-actions.sh). Age is measured from THIS, not from any date mentioned
# in the line's prose (a 📅 due date, a date in a quoted fact, etc. is not
# when the action was created). A line with no ➕ stamp has genuinely UNKNOWN
# age — it must not fall through into "not stale" via a same-line date grep,
# which is how a census can under-report staleness while many open actions
# carry no date at all.
CREATED_RE = re.compile(r"➕\s*(20\d{2}-\d{2}-\d{2})")
TAG_RE = re.compile(r"\s*#(action|priority|auto)\b")


def iter_action_bullets(lines: list[str]):
    """Yield (start_line_no, joined_text) for every open checkbox bullet that
    carries #action, joining indented continuation lines that wrap the tag
    onto a following line — a same-line-only regex would silently drop any
    bullet whose #action tag lands on a wrapped continuation, undercounting
    real open actions."""
    i = 0
    n = len(lines)
    while i < n:
        m = CHECKBOX_RE.match(lines[i])
        if not m:
            i += 1
            continue
        start = i
        parts = [m.group(1)]
        j = i + 1
        while j < n and CONTINUATION_RE.match(lines[j]) and not CHECKBOX_RE.match(lines[j]):
            parts.append(lines[j].strip())
            j += 1
        joined = " ".join(parts)
        if "#action" in joined:
            yield start, joined
        i = j if j > i + 1 else i + 1


def _scan_file(p: Path, today: dt.date) -> list[dict]:
    rel = str(p.relative_to(VAULT))
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    rows = []
    for line_no, text in iter_action_bullets(lines):
        m = CREATED_RE.search(text)
        created = m.group(1) if m else None
        age = (today - dt.date.fromisoformat(created)).days if created else None
        rows.append({
            "home": rel, "line": line_no + 1, "text": TAG_RE.sub("", text).strip(),
            "priority": "#priority" in text, "auto": "#auto" in text,
            "date": created, "age_days": age,
        })
    return rows


def scan() -> list[dict]:
    rows = []
    today = dt.date.today()
    for folder in SCAN:
        root = VAULT / folder
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.md")):
            if SKIP_PARTS & set(p.relative_to(VAULT).parts) or p.name.endswith(" TEMPLATE.md"):
                continue
            rows += _scan_file(p, today)
    for name in EXTRA_FILES:
        p = VAULT / name
        if p.is_file():
            rows += _scan_file(p, today)
    return rows


def summarize(rows: list[dict], stale_days: int) -> dict:
    homes: dict[str, dict] = {}
    for r in rows:
        h = homes.setdefault(r["home"], {"open": 0, "priority": 0, "auto": 0})
        h["open"] += 1; h["priority"] += r["priority"]; h["auto"] += r["auto"]
    dated = [r for r in rows if r["age_days"] is not None]
    # #auto lines are excluded as machine-written queues UNLESS also #priority:
    # a job can auto-write a line that surfaces a real human task (e.g. an
    # email-triage #action), and #priority is the human curation signal that
    # says so — otherwise a stale, important line stays permanently invisible.
    stale = sorted((r for r in dated if r["age_days"] > stale_days and (not r["auto"] or r["priority"])), key=lambda r: -r["age_days"])
    # Rows with no ➕ created stamp have genuinely UNKNOWN age — they are NOT
    # "not stale", they're unmeasured. Surfaced as its own count (never
    # silently folded into "not stale"); the #priority ones are the most worth
    # a human's attention since they're both important AND un-aged. Never
    # bulk-dated here — that's backfill-action-dates.sh's job; this script
    # only measures and reports.
    unknown = [r for r in rows if r["age_days"] is None]
    unknown_priority = [r for r in unknown if r["priority"] and not r["auto"]]
    return {
        "date": dt.date.today().isoformat(), "open": len(rows),
        "priority": sum(r["priority"] for r in rows), "auto": sum(r["auto"] for r in rows),
        "homes": len(homes), "dated": len(dated), "undated": len(rows) - len(dated),
        "unknown_age": len(unknown), "unknown_age_priority": len(unknown_priority),
        "stale_days": stale_days, "stale": len(stale),
        "top_homes": sorted(homes.items(), key=lambda kv: -kv[1]["open"])[:12],
        "priority_list": [r for r in rows if r["priority"]],
        "stale_list": stale[:25],
        "unknown_priority_list": unknown_priority[:25],
        "auto_homes": sorted(((h, v["auto"]) for h, v in homes.items() if v["auto"]), key=lambda kv: -kv[1]),
    }


def _link(r: dict) -> str:
    # EXTRA_FILES entries are ephemeral/no-frontmatter root files (not
    # registered link-map targets) — render as a path, not a wikilink, so a
    # real open action there doesn't produce a broken-link lint failure.
    if r["home"] in EXTRA_FILES:
        return f"`{r['home']}`"
    return f"[[{Path(r['home']).stem}]]"


def _clip(s: str, n: int = 140) -> str:
    s = re.sub(r"\s+", " ", s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def block(s: dict) -> str:
    L = [START,
         f"_Generated {s['date']} by `SYSTEM/bin/actions.py` — do not hand-edit between the markers. Same numbers Claude sees; the Tasks-plugin views below stay the click-to-complete surface._",
         "",
         f"**{s['open']} open** in {s['homes']} notes · **{s['priority']} #priority** · {s['auto']} machine-made (`#auto`) · "
         f"{s['dated']} carry a ➕ created date · **{s['stale']} stale** (>{s['stale_days']}d old) · "
         f"**{s['unknown_age']} unknown age** (no ➕ stamp — not counted as stale, not counted as fresh; backfill-action-dates.sh dates them)",
         "",
         "**Priority**"]
    L += [f"- {_clip(r['text'])} ← {_link(r)}" for r in s["priority_list"]] or ["- _none flagged_"]
    L += ["", f"**Stale (>{s['stale_days']} days, oldest first — the weekly aging pass: do, re-date, or drop with a reason)**"]
    L += [f"- {r['age_days']}d · {_clip(r['text'], 110)} ← {_link(r)}" for r in s["stale_list"]] or ["- _none_"]
    L += ["", f"**Unknown age, #priority (worth dating first — {s['unknown_age']} total unknown-age actions exist; this is the #priority subset)**"]
    L += [f"- {_clip(r['text'], 110)} ← {_link(r)}" for r in s["unknown_priority_list"]] or ["- _none_"]
    L += ["", "**Where they live**", "", "| Home | Open | #priority | #auto |", "| :-- | --: | --: | --: |"]
    L += [f"| [[{Path(h).stem}]] | {v['open']} | {v['priority']} | {v['auto']} |" for h, v in s["top_homes"]]
    if s["auto_homes"]:
        L += ["", "_Machine-made (`#auto`) actions are queues written by jobs (e.g. an email-triage sweep); they are excluded from the stale list and are worked in their home note, not here — unless also `#priority`, which signals a real human task a job happened to surface._"]
    L.append(END)
    return "\n".join(L)


def main() -> int:
    args = sys.argv[1:]
    stale_days = 30
    if "--stale-days" in args:
        stale_days = int(args[args.index("--stale-days") + 1])
    s = summarize(scan(), stale_days)
    if "--json" in args:
        print(json.dumps({k: v for k, v in s.items() if not k.endswith("_list")}, ensure_ascii=False, indent=1)); return 0
    if "--write" in args:
        text = ACTIONS_MD.read_text(encoding="utf-8")
        if START not in text or END not in text:
            print(f"FAIL Actions.md: missing {START}/{END} markers"); return 1
        pre, rest = text.split(START, 1); _, post = rest.split(END, 1)
        ACTIONS_MD.write_text(pre + block(s) + post, encoding="utf-8")
        print(f"wrote Actions.md census: {s['open']} open · {s['priority']} #priority · {s['auto']} #auto · {s['stale']} stale · {s['unknown_age']} unknown age")
        return 0
    print(block(s)); return 0


if __name__ == "__main__":
    sys.exit(main())
