#!/usr/bin/env python3
"""fold_log.py — fold per-host log sidecars into SYSTEM/log.md, on the writer host only.

    SYSTEM/bin/fold_log.py            # call it from the writer host's commit job, before each commit

Appends every `- YYYY-MM-DD …` line from SYSTEM/log.d/*.md that isn't already in SYSTEM/log.md or a
monthly archive (SYSTEM/log/*.md). Matching is by content, so reruns and lost state can't duplicate.
Never edits a sidecar (its host is its only writer). A previous month's sidecar is deleted once every
line in it sits in that month's archive, i.e. after rotate_log.sh moved it; nothing writes it any more.
Exit 0 always on the writer host (a fold problem must not block the commit); refuses elsewhere.
Rule: SYSTEM/SCHEMA.md § One log writer.
"""
import datetime as dt
import importlib.machinery
import importlib.util
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent
ENTRY = re.compile(r"^- \d{4}-\d{2}-\d{2} ")
SIDECAR = re.compile(r"^(\d{4}-\d{2})\.(.+)\.md$")


def _lines(path):
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def fold(vault, today=None):
    vault = Path(vault)
    today = today or dt.date.today()
    out = {"added": 0, "removed": [], "skipped": []}
    d = vault / "SYSTEM/log.d"
    if not d.is_dir():
        return out
    log = vault / "SYSTEM/log.md"
    archived = set()
    for a in sorted((vault / "SYSTEM/log").glob("*.md")):
        archived.update(_lines(a))
    have = set(_lines(log)) | archived
    new = []
    sidecars = sorted(p for p in d.glob("*.md") if SIDECAR.match(p.name))
    for p in sidecars:
        for line in _lines(p):
            if not line.strip():
                continue
            if not ENTRY.match(line):
                out["skipped"].append("%s: %s" % (p.name, line[:80]))
                continue
            if line not in have:
                new.append(line)
                have.add(line)
    if new:
        text = log.read_text(encoding="utf-8") if log.exists() else ""
        with open(log, "a", encoding="utf-8") as f:
            f.write(("\n" if text and not text.endswith("\n") else "") + "\n".join(new) + "\n")
        out["added"] = len(new)
    this_month = today.strftime("%Y-%m")
    for p in sidecars:
        month = SIDECAR.match(p.name).group(1)
        entries = [l for l in _lines(p) if ENTRY.match(l)]
        if month < this_month and all(l in archived for l in entries):
            p.unlink()
            out["removed"].append(p.name)
    return out


def _writer_check():
    spec = importlib.util.spec_from_loader("log_line", importlib.machinery.SourceFileLoader(
        "log_line", str(Path(__file__).resolve().parent / "log-line")))
    ll = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ll)
    w = ll.writer_host(VAULT)
    return w is None or ll.this_host() == w, w


def main():
    ok, w = _writer_check()
    if not ok:
        print("fold_log: refused — only the writer host (%s) folds" % w, file=sys.stderr)
        return 2
    try:
        r = fold(VAULT)
    except Exception as e:  # never block the commit
        print("fold_log: failed: %s" % e, file=sys.stderr)
        return 0
    print("fold_log: %d line(s) folded, %d sidecar(s) retired%s" % (
        r["added"], len(r["removed"]), (", %d malformed skipped" % len(r["skipped"])) if r["skipped"] else ""))
    for s in r["skipped"]:
        print("  skipped %s" % s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
