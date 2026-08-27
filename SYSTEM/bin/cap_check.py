#!/usr/bin/env python3
"""cap_check.py — script-measured digest caps ("never by model estimate").

Role digests are state-only files with a word cap (~2,000 vault-wide; see
SYSTEM/SCHEMA.md). This script is the measurement: registered digest files
(SYSTEM/bin/cap_config.json) are word-counted (body only, frontmatter
excluded) against the cap.

Semantics:
  - under cap                    -> PASS
  - over cap, frontmatter carries a dated `cap_exception:` -> WARN (declared)
  - over cap, no exception       -> FAIL (compact the digest — rewrite the
                                    state from what is still true — or
                                    declare a dated cap_exception)
  - registered file missing      -> FAIL (silence must be distinguishable
                                    from not-checked)

Per-file `cap_words:` frontmatter overrides the default cap. Stdlib only.

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
    """Return (frontmatter_text, body). Tolerant, stdlib-only."""
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


def main() -> int:
    default_cap = 2000
    targets: list[Path] = []
    args = [a for a in sys.argv[1:] if a != "--"]
    if args:
        targets = [(VAULT / a) if not Path(a).is_absolute() else Path(a) for a in args]
    else:
        if not CONFIG.exists():
            print(f"FAIL  cap_check: config missing ({CONFIG})")
            return 1
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        default_cap = int(cfg.get("default_cap_words", default_cap))
        targets = [VAULT / p for p in cfg.get("digests", [])]
        if not targets:
            print("PASS  cap_check: no digests registered (register them in cap_config.json)")
            return 0

    rc = 0
    for t in targets:
        status, msg = check(t, default_cap)
        print(f"{status}  {msg}")
        if status == "FAIL":
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
