#!/usr/bin/env python3
"""kb_stats.py — the KB's own telemetry.

Measures the kernel gauges the Optimize-the-Knowledge-Base skill used to
collect by hand, so they trend instead of being one-offs:

  boot      tokens the always-loaded files cost every session (+ the boot bundle,
            if your instance has SYSTEM/bin/build_boot_bundle.sh)
  paging    initiative notes over their section caps (cap_check.py), the
            biggest Now & next / Milestones sections, biggest notes
  scheduler open #action count, #priority count, machine-made share
            (#auto), oldest embedded date, top homes
  syslog    SYSTEM/log.md bytes / lines / lines this month
  gc        Knowledge/raw/ captures with zero inbound links (compile debt)
  lint      SYSTEM/bin/lint.sh wall-clock + verdict
  corpus    file counts + bytes per content folder; index.md size

Stdlib only. Usage (vault root):
  python3 SYSTEM/bin/kb_stats.py            # markdown report to stdout
  python3 SYSTEM/bin/kb_stats.py --json     # one JSON object
  python3 SYSTEM/bin/kb_stats.py --write    # append a JSON line to
        SYSTEM/stats/kb-stats.jsonl and rewrite SYSTEM/kb-stats.md below its
        <!-- generated --> marker (current gauges + last-7-runs trend)
  python3 SYSTEM/bin/kb_stats.py --line     # one-line digest for the 6pm summary
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent
BIN = VAULT / "SYSTEM" / "bin"
# ===== Folder names — edit here if your instance renames the content folders =====
CONCEPTS = "Knowledge/Concepts"
INITIATIVES = "Knowledge/Initiatives"
PEOPLE = "Knowledge/People"
RAW = "Knowledge/raw"
DAILY = "daily"
SKILLS_MIRROR = "Knowledge/Skills"
# ==================================================================================
STATS_DIR = VAULT / "SYSTEM" / "stats"
JSONL = STATS_DIR / "kb-stats.jsonl"
REPORT = VAULT / "SYSTEM" / "kb-stats.md"
MARKER = "<!-- generated -->"
CONTENT = [CONCEPTS, INITIATIVES, PEOPLE, RAW, DAILY, ".claude/skills"]
CHECKBOX_RE = re.compile(r"^\s*- \[ \] (.*)$")
CONTINUATION_RE = re.compile(r"^\s+\S")  # indented, non-blank — a wrapped continuation line
DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
SKIP_DIRS = {".git", ".obsidian", ".venv", ".stfolder", ".superpowers", "node_modules", "__pycache__", "attachments"}
ACTION_SKIP_PARTS = {"trails", "archive"}  # match actions.py's scan scope — archived/historical isn't "open"


def iter_action_bullets(lines: list[str]):
    """Yield (start_line_no, joined_text) for every open checkbox bullet that
    carries #action, joining indented continuation lines that wrap the tag
    onto a following line (same-line-only matching would silently drop any
    bullet whose #action tag wraps). Scan scope matches actions.py — archived
    and trail files aren't "open" — so the two dashboards agree."""
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


def md_files(root: Path):
    for p in root.rglob("*.md"):
        if any(part in SKIP_DIRS for part in p.relative_to(VAULT).parts):
            continue
        yield p


def tokens(nbytes: int) -> int:
    return nbytes // 4


# ---------- boot ----------
def gauge_boot() -> dict:
    out = {"bundle_bytes": None, "bundle_tokens": None,
           "hook_present": (VAULT / ".claude" / "settings.json").exists()
           or os.path.exists(os.path.expanduser("~/.claude/hooks/knowledge-context.sh"))}
    bundle = BIN / "build_boot_bundle.sh"   # optional — not shipped in the base kit
    if bundle.exists():
        try:
            r = subprocess.run([str(bundle), "--size"], capture_output=True, text=True, timeout=30)
            m = re.search(r"(\d+) bytes ≈ (\d+) tokens", r.stdout)
            if m:
                out["bundle_bytes"], out["bundle_tokens"] = int(m.group(1)), int(m.group(2))
        except Exception:
            pass
    # what AGENTS.md still tells a session to read at start (bytes → tokens)
    always = {}
    for rel in ("AGENTS.md", "index.md", "SYSTEM/SCHEMA.md"):
        p = VAULT / rel
        always[rel] = tokens(p.stat().st_size) if p.exists() else None
    out["always_loaded_tokens"] = always
    return out


# ---------- paging ----------
def _section_words(text: str, heading: str) -> int | None:
    m = re.search(rf"^{re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return len(m.group(1).split()) if m else None


def gauge_paging() -> dict:
    over = []
    try:
        r = subprocess.run([sys.executable, str(BIN / "cap_check.py")], capture_output=True, text=True, timeout=60, cwd=VAULT)
        over = [ln for ln in r.stdout.splitlines() if ln.startswith(("FAIL", "WARN"))]
    except Exception:
        pass
    notes = []
    for folder in (INITIATIVES,):
        for p in (VAULT / folder).glob("**/*.md"):
            if "trails" in p.parts or "archive" in p.parts or p.name.endswith(" TEMPLATE.md") or p.name == "index.md":
                continue
            t = p.read_text(encoding="utf-8", errors="replace")
            notes.append({
                "note": str(p.relative_to(VAULT)), "bytes": p.stat().st_size,
                "now_next_words": _section_words(t, "## Now & next"),
                "milestones_words": _section_words(t, "## Milestones"),
            })
    notes.sort(key=lambda n: -n["bytes"])
    return {
        "over_cap": len(over), "over_cap_lines": over,
        "biggest_notes": [(n["note"], n["bytes"]) for n in notes[:5]],
        "biggest_now_next": sorted(((n["now_next_words"] or 0, n["note"]) for n in notes), reverse=True)[:3],
        "biggest_milestones": sorted(((n["milestones_words"] or 0, n["note"]) for n in notes), reverse=True)[:3],
    }


# ---------- scheduler ----------
def gauge_actions() -> dict:
    total = prio = auto = 0
    homes: dict[str, int] = {}
    dates: list[str] = []
    for p in md_files(VAULT):
        rel = str(p.relative_to(VAULT))
        if rel.startswith(("SYSTEM/", SKILLS_MIRROR + "/", ".claude/", "docs/", "Knowledge/Excalidraw/")):
            continue
        # Skip Actions.md's own example fences and *TEMPLATE.md placeholder
        # bullets — they are not real open actions (actions.py excludes both).
        if p.name == "Actions.md" or p.name.endswith(" TEMPLATE.md"):
            continue
        if ACTION_SKIP_PARTS & set(p.relative_to(VAULT).parts):
            continue
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        for _, text in iter_action_bullets(lines):
            total += 1
            prio += "#priority" in text
            auto += "#auto" in text
            homes[rel] = homes.get(rel, 0) + 1
            dates += DATE_RE.findall(text)
    top = sorted(homes.items(), key=lambda kv: -kv[1])[:5]
    return {"open": total, "priority": prio, "auto": auto, "homes": len(homes), "top_homes": top,
            "oldest_embedded_date": min(dates) if dates else None}


# ---------- syslog ----------
def gauge_log() -> dict:
    p = VAULT / "SYSTEM" / "log.md"
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8", errors="replace")
    month = dt.date.today().strftime("%Y-%m")
    lines = text.count("\n")
    this_month = len(re.findall(rf"^- {month}-", text, re.M))
    arch = sorted((VAULT / "SYSTEM" / "log").glob("20*.md"))
    return {"bytes": p.stat().st_size, "tokens": tokens(p.stat().st_size), "lines": lines, "lines_this_month": this_month,
            "archived_months": len(arch), "archived_bytes": sum(a.stat().st_size for a in arch)}


# ---------- gc ----------
def gauge_orphan_raw() -> dict:
    raw = VAULT / RAW
    caps = [p for p in raw.glob("20*.md")]
    corpus = ""
    for p in md_files(VAULT):
        rel = p.relative_to(VAULT).parts
        if rel[0] == "SYSTEM" or "/".join(rel).startswith(RAW + "/"):
            continue
        corpus += p.read_text(encoding="utf-8", errors="replace")
    orphans = [p.stem for p in caps if f"raw/{p.stem}" not in corpus]
    return {"captures": len(caps), "orphans": len(orphans), "orphan_list": sorted(orphans)}


# ---------- lint ----------
def gauge_lint() -> dict:
    t0 = time.time()
    try:
        r = subprocess.run(["bash", str(BIN / "lint.sh")], capture_output=True, text=True, timeout=300, cwd=VAULT)
        verdict = "green" if "LINT: green" in r.stdout else "problems"
        fails = len(re.findall(r"^FAIL", r.stdout, re.M))
    except Exception:
        verdict, fails = "error", None
    return {"seconds": round(time.time() - t0, 2), "verdict": verdict, "fails": fails}


# ---------- corpus ----------
def gauge_corpus() -> dict:
    out = {}
    for d in CONTENT:
        root = VAULT / d
        if not root.is_dir():
            continue
        files = list(root.rglob("*.md"))
        out[d] = {"files": len(files), "bytes": sum(p.stat().st_size for p in files)}
    idx = VAULT / "index.md"
    out["index.md"] = {"bytes": idx.stat().st_size, "tokens": tokens(idx.stat().st_size)}
    return out


def collect() -> dict:
    return {
        "date": dt.date.today().isoformat(),
        "host": os.uname().nodename.split(".")[0],
        "boot": gauge_boot(), "paging": gauge_paging(), "actions": gauge_actions(),
        "log": gauge_log(), "gc": gauge_orphan_raw(), "lint": gauge_lint(), "corpus": gauge_corpus(),
    }


def digest_line(s: dict) -> str:
    b, a, l, g, li = s["boot"], s["actions"], s["log"], s["gc"], s["lint"]
    return (f"📊 KB stats {s['date']} ({s['host']}): boot {b.get('bundle_tokens')} tok · over-cap {s['paging']['over_cap']} · "
            f"open actions {a['open']} ({a['priority']} #priority, {a['auto']} #auto) · log {l.get('lines')} lines/{l.get('tokens')} tok · "
            f"orphan raw {g['orphans']}/{g['captures']} · lint {li['verdict']} {li['seconds']}s")


def history() -> list[dict]:
    if not JSONL.exists():
        return []
    rows = []
    for ln in JSONL.read_text().splitlines():
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError:
            pass
    return rows


def report(s: dict, hist: list[dict]) -> str:
    b, p, a, l, g, li, c = s["boot"], s["paging"], s["actions"], s["log"], s["gc"], s["lint"], s["corpus"]
    L = [f"_Generated {s['date']} on {s['host']} by `SYSTEM/bin/kb_stats.py` — do not hand-edit below the marker._", ""]
    L += ["| Gauge | Now |", "| :-- | --: |",
          f"| Boot bundle | {(str(b.get('bundle_tokens')) + ' tokens (' + str(b.get('bundle_bytes')) + ' B)') if b.get('bundle_tokens') else 'n/a (no build_boot_bundle.sh)'}; hook {'present' if b['hook_present'] else 'MISSING'} |",
          f"| Always-loaded (AGENTS / index / SCHEMA) | {b['always_loaded_tokens'].get('AGENTS.md')} / {b['always_loaded_tokens'].get('index.md')} / {b['always_loaded_tokens'].get('SYSTEM/SCHEMA.md')} tokens |",
          f"| Notes over section cap | {p['over_cap']} |",
          f"| Biggest Now & next | " + " · ".join(f"{n} ({w}w)" for w, n in p["biggest_now_next"]) + " |",
          f"| Biggest Milestones | " + " · ".join(f"{n} ({w}w)" for w, n in p["biggest_milestones"]) + " |",
          f"| Biggest notes | " + " · ".join(f"{n} ({sz//1024}KB)" for n, sz in p["biggest_notes"]) + " |",
          f"| Open #action | {a['open']} in {a['homes']} notes · {a['priority']} #priority · {a['auto']} #auto · oldest date {a['oldest_embedded_date']} |",
          f"| Top action homes | " + " · ".join(f"{h} ({n})" for h, n in a["top_homes"]) + " |",
          f"| log.md (live) | {l.get('lines')} lines · {l.get('tokens')} tokens · {l.get('lines_this_month')} this month · {l.get('archived_months')} archived month(s) in SYSTEM/log/ ({(l.get('archived_bytes') or 0)//1024}KB) |",
          f"| Orphan raw captures | {g['orphans']} / {g['captures']} |",
          f"| Lint | {li['verdict']} ({li['fails']} FAIL) in {li['seconds']}s |",
          f"| index.md | {c['index.md']['tokens']} tokens |",
          "| Corpus | " + " · ".join(f"{d} {v['files']}f/{v['bytes']//1024}KB" for d, v in c.items() if d != "index.md") + " |"]
    rows = (hist + [s])[-7:]
    L += ["", "**Trend (last 7 runs)**", "",
          "| Date | Host | Boot tok | Over cap | Open | #priority | Log lines | Orphan raw | Lint s |",
          "| :-- | :-- | --: | --: | --: | --: | --: | --: | --: |"]
    for r in rows:
        L.append(f"| {r['date']} | {r.get('host','')} | {r['boot'].get('bundle_tokens')} | {r['paging']['over_cap']} | {r['actions']['open']} | {r['actions']['priority']} | {r['log'].get('lines')} | {r['gc']['orphans']} | {r['lint']['seconds']} |")
    if p["over_cap_lines"]:
        L += ["", "**Over cap:**"] + [f"- {x}" for x in p["over_cap_lines"]]
    if g["orphan_list"]:
        L += ["", "**Orphan raw captures (never linked from a compiled note):**"] + [f"- `{RAW}/{x}.md`" for x in g["orphan_list"]]
    return "\n".join(L) + "\n"


def write(s: dict) -> None:
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    hist = history()
    slim = {k: v for k, v in s.items()}
    slim["paging"] = {k: v for k, v in s["paging"].items() if k != "over_cap_lines"}
    slim["gc"] = {k: v for k, v in s["gc"].items() if k != "orphan_list"}
    with JSONL.open("a") as fh:
        fh.write(json.dumps(slim, ensure_ascii=False) + "\n")
    (STATS_DIR / "latest.txt").write_text(digest_line(s) + "\n")  # read by build_boot_bundle.sh
    head = ""
    if REPORT.exists() and MARKER in REPORT.read_text():
        head = REPORT.read_text().split(MARKER, 1)[0]
    else:
        head = ("# KB stats — the kernel gauges\n\nNightly self-telemetry: what every session pays to boot, "
                "whether orientation surfaces are inside their caps, the state of the action scheduler, log growth, and compile debt. "
                "History: `SYSTEM/stats/kb-stats.jsonl` (append-only). Producer: `SYSTEM/bin/kb_stats.py --write` (run it from a scheduled job if you want the trend). "
                "Skill: [[Optimize the Knowledge Base]].\n\n")
    REPORT.write_text(head + MARKER + "\n" + report(s, hist), encoding="utf-8")


def main() -> int:
    s = collect()
    if "--json" in sys.argv:
        print(json.dumps(s, ensure_ascii=False, indent=1))
    elif "--line" in sys.argv:
        print(digest_line(s))
    elif "--write" in sys.argv:
        write(s)
        print(digest_line(s))
    else:
        print(report(s, history()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
