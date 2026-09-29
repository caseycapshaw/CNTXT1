#!/usr/bin/env python3
"""cap_check.py — script-measured digest caps ("never by model estimate").

Role digests are state-only files with a word cap (~2,000 vault-wide; see
SYSTEM/SCHEMA.md § Conventions). This script is the measurement: registered
digest files (SYSTEM/bin/cap_config.json) are word-counted (body only,
frontmatter excluded) against the cap.

Semantics:
  - under cap                    -> PASS
  - over cap, frontmatter carries a dated `cap_exception:` -> WARN (declared)
  - over cap, no exception       -> FAIL (compact the digest — rewrite the
                                    state from what is still true — or
                                    declare a dated cap_exception)
  - registered file missing      -> FAIL (silence must be distinguishable
                                    from not-checked)

Per-file `cap_words:` frontmatter overrides the default cap. Stdlib only.

Section caps: cap_config.json `sections` entries cap ONE `## heading` inside
every note matching a glob — the orientation surfaces of projects
(`## Now & next`, `## Milestones`). Over cap → move history verbatim to the
note's `trails/<slug>-trail.md` sibling and rewrite the section as current
state (SYSTEM/SCHEMA.md § Conventions, orientation caps). A dated
`cap_exception:` in frontmatter downgrades any breach to WARN.

Usage (from the vault root):
  python3 SYSTEM/bin/cap_check.py            # check all registered digests
  python3 SYSTEM/bin/cap_check.py FILE...    # check specific files
"""

import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent
CONFIG = Path(__file__).resolve().parent / "cap_config.json"


def split_frontmatter(text: str):
    """Return (frontmatter_dict_lines, body). Tolerant, stdlib-only."""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            fm = text[4:end]
            body = text[end + 4 :]
            return fm, body
    return "", text


def fm_value(fm: str, key: str):
    m = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", fm, re.MULTILINE)
    return m.group(1) if m else None


def check(path: Path, default_cap: int) -> tuple[str, str]:
    """Return (status, message) for one digest file."""
    rel = path.relative_to(VAULT) if path.is_absolute() else path
    if not path.exists():
        return "FAIL", f"registered digest missing: {rel}"
    text = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    cap_raw = fm_value(fm, "cap_words")
    try:
        cap = int(cap_raw) if cap_raw else default_cap
    except ValueError:
        cap = default_cap
    words = len(body.split())
    if words <= cap:
        return "PASS", f"{rel} ({words}/{cap} words)"
    exception = fm_value(fm, "cap_exception")
    if exception:
        return "WARN", f"{rel} over cap ({words}/{cap}) — declared: cap_exception: {exception}"
    return (
        "FAIL",
        f"{rel} over cap ({words}/{cap}) — compact (rewrite state from what is "
        "still true) or declare a dated cap_exception: in frontmatter",
    )


def section_words(body: str, heading: str) -> int | None:
    """Word count of one `## heading` section (None if the heading is absent)."""
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i + 1
            break
    if start is None:
        return None
    out: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        out.append(line)
    return len(" ".join(out).split())


def check_section(path: Path, heading: str, cap: int) -> tuple[str, str] | None:
    """Return (status, message) for one capped section, or None if absent."""
    rel = path.relative_to(VAULT) if path.is_absolute() else path
    text = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    words = section_words(body, heading)
    if words is None:
        return None
    if words <= cap:
        return "PASS", f"{rel} `{heading}` ({words}/{cap} words)"
    exception = fm_value(fm, "cap_exception")
    if exception:
        return "WARN", f"{rel} `{heading}` over cap ({words}/{cap}) — declared: cap_exception: {exception}"
    return (
        "FAIL",
        f"{rel} `{heading}` over cap ({words}/{cap}) — move history verbatim to "
        f"trails/<slug>-trail.md and rewrite as current state, or declare a dated cap_exception:",
    )


def main() -> int:
    default_cap = 2000
    targets: list[Path] = []
    args = [a for a in sys.argv[1:] if a not in ("--", "--verbose")]
    if args:
        targets = [(VAULT / a) if not Path(a).is_absolute() else Path(a) for a in args]
    else:
        if not CONFIG.exists():
            print(f"FAIL  cap_check: config missing ({CONFIG})")
            return 1
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        default_cap = int(cfg.get("default_cap_words", default_cap))
        targets = [VAULT / p for p in cfg.get("digests", [])]
        if not targets and not cfg.get("sections"):
            print("PASS  cap_check: no digests registered (register them in cap_config.json)")
            return 0

    rc = 0
    for t in targets:
        status, msg = check(t, default_cap)
        print(f"{status}  {msg}")
        if status == "FAIL":
            rc = 1

    # Section caps (only in config mode — explicit FILE args check digests only)
    if not args and CONFIG.exists():
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        quiet = "--verbose" not in sys.argv
        for sec in cfg.get("sections", []):
            heading, cap = sec["heading"], int(sec["cap_words"])
            for glob in sec.get("globs", []):
                for path in sorted(VAULT.glob(glob)):
                    if path.name.endswith(" TEMPLATE.md"):
                        continue
                    res = check_section(path, heading, cap)
                    if res is None:
                        continue
                    status, msg = res
                    if status == "PASS" and quiet:
                        continue
                    print(f"{status}  {msg}")
                    if status == "FAIL":
                        rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
