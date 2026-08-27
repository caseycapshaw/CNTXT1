#!/usr/bin/env python3
"""EXAMPLE domain status-dashboard generator — copy per domain, don't share.

Implements the generated-sections convention (Knowledge/Skills/RULE/Maintain
Generated Sections.md) for a "status.md" freshness dashboard over a folder of
data modules: recheck due-dates computed from a hand-edited config table,
plus per-feed staleness flags. Adapt DOMAIN_DIR/FEEDS to your domain (a
finance folder, a health folder, a project data lake) and schedule it
(launchd/cron). Stdlib-only, idempotent, fails loud.

The status file's shape:
  # <title>                      <- hand territory
  | Check | Last done | Interval wks | Note |   <- hand-edited config table
  <!-- generated -->             <- everything below is rewritten each run
"""
import os, re, sys
from datetime import date, timedelta

DOMAIN_DIR = os.path.expanduser("{{VAULT}}/Knowledge/raw/{{domain}}")
STATUS = os.path.join(DOMAIN_DIR, "status.md")
MARKER = "<!-- generated -->"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# feed name -> (file, section anchor to search for dates or None=whole file,
#               stale threshold in days). Add a row per data module.
FEEDS = [
    ("{{feed-1}}", "{{feed-1}}.md", None, 7),
    ("{{feed-2}}", "{{feed-2}}.md", "## Changelog", 90),
]


def read(path):
    with open(path) as f:
        return f.read()


def latest_date(text):
    ds = DATE_RE.findall(text)
    return max(ds) if ds else None


def section(text, anchor):
    if anchor is None:
        return text
    i = text.find(anchor)
    if i < 0:
        sys.exit(f"anchor {anchor!r} not found")  # fail loud, write nothing
    return text[i:]


def main():
    today = date.today()
    config = read(STATUS).split(MARKER)[0]

    # --- Rechecks from the hand-edited config table
    recheck_rows = []
    for line in config.splitlines():
        if not line.startswith("|") or set(line) <= {"|", "-", ":", " "}:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0] == "Check":
            continue
        check, last, interval, note = cells[:4]
        last_d, m = DATE_RE.search(last), re.search(r"\d+", interval)
        if last_d and m:
            due = date.fromisoformat(last_d.group()) + timedelta(weeks=int(m.group()))
            wks = (due - today).days / 7
            flag = f"⚠️ **OVERDUE ({-wks:.0f} wks)**" if wks < 0 else f"due in {wks:.0f} wks"
            recheck_rows.append(f"| {check} | {last} | {due.isoformat()} | {flag} |")
        else:
            recheck_rows.append(f"| {check} | {last} | — | {note or 'unscheduled'} |")
    if not recheck_rows:
        sys.exit("no recheck config rows found above the marker")

    # --- Feed freshness
    fresh = ["| Feed | Last data | Days since | Status |", "|---|---|---|---|"]
    for name, fname, anchor, thresh in FEEDS:
        path = os.path.join(DOMAIN_DIR, fname)
        last = latest_date(section(read(path), anchor)) if os.path.exists(path) else None
        if last is None:
            fresh.append(f"| {name} | — | — | ⚠️ **NO DATA** |")
            continue
        days = (today - date.fromisoformat(last)).days
        flag = f"⚠️ **STALE ({days}d > {thresh}d)**" if days > thresh else "ok"
        fresh.append(f"| {name} | {last} | {days} | {flag} |")

    out = "\n".join(
        [config.rstrip("\n"), "", MARKER, "",
         f"_Generated: {today.isoformat()} by status-gen — do not hand-edit below the marker._",
         "", "## Rechecks", "",
         "| Check | Last done | Due | Status |", "|---|---|---|---|",
         *recheck_rows, "", "## Feed freshness", "", *fresh, ""])
    with open(STATUS, "w") as f:
        f.write(out)
    print(f"wrote {STATUS}: {len(recheck_rows)} rechecks, {len(FEEDS)} feeds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
