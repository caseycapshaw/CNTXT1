"""Generate the service directory below the <!-- generated --> marker in
05 concepts/contacts.md from 04 People/ frontmatter (relations frontmatter):
every `type: org` note plus every
person whose `relation:` marks an operational class (service provider, tenant,
school contact). Makes an un-indexed vendor mechanically visible — the
hand-curated go-to map above the marker is never touched.

Usage:
  uv run python SYSTEM/bin/build_contacts_directory.py          # write
  uv run python SYSTEM/bin/build_contacts_directory.py --check  # lint mode

Contract (Maintain Generated Sections): idempotent; fails loud and writes
nothing on any unparseable frontmatter; --check compares content ignoring the
stamp line.
"""

import json
import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FOLDERS = json.loads((Path(__file__).resolve().parent / "kb-folders.json").read_text())
PEOPLE = REPO_ROOT / _FOLDERS["people"]
CONTACTS = REPO_ROOT / _FOLDERS["concepts"] / "contacts.md"
MARKER = "<!-- generated -->"
STAMP_PREFIX = "_Generated:"
# relation: values whose class (text before the first " — ") is one of these
# land in the operational-contacts table; everything else is social territory
# covered by the hand-curated tables above the marker.
OPERATIONAL = {"service provider", "tenant", "school contact"}


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path.name}: no frontmatter block")
    data = yaml.safe_load(text.split("---", 2)[1])
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: frontmatter is not a mapping")
    return data


def build_block() -> str:
    orgs, ops = [], []
    for path in sorted(PEOPLE.glob("*.md")):
        if path.name.endswith(" TEMPLATE.md") or path.name == "index.md":
            continue
        data = frontmatter(path)
        note_type = data.get("type")
        if note_type not in ("person", "org"):
            raise ValueError(f"{path.name}: unexpected type {note_type!r}")
        name = path.stem
        if note_type == "org":
            orgs.append(
                f"| [[{name}]] | {data.get('role') or '—'} | "
                f"{data.get('location') or '—'} | {data.get('found-by') or '—'} |"
            )
        else:
            relation = data.get("relation") or ""
            cls = relation.split("—")[0].strip().lower()
            if cls in OPERATIONAL:
                orgfield = data.get("org") or "—"
                ops.append(f"| [[{name}]] | {relation} | {orgfield} |")

    lines = [
        MARKER,
        "",
        "## 🏢 Service directory (generated)",
        "",
        f"{STAMP_PREFIX} {date.today().isoformat()} by SYSTEM/bin/build_contacts_directory.py — "
        f"from {_FOLDERS['people']}/ frontmatter; edit the notes, not this block._",
        "",
        "### Orgs & vendors (`type: org`)",
        "",
        "| Org | Role | Location | Found by |",
        "| :-- | :-- | :-- | :-- |",
        *orgs,
        "",
        "### Operational contacts (`relation:` service provider / tenant / school)",
        "",
        "| Person | Relation | Org |",
        "| :-- | :-- | :-- |",
        *ops,
        "",
    ]
    return "\n".join(lines)


def strip_stamp(block: str) -> str:
    return "\n".join(l for l in block.splitlines() if not l.startswith(STAMP_PREFIX))


def split_doc(text: str):
    """Split on the marker as its own line (a prose mention of the marker
    string mid-line must not count)."""
    i = text.find("\n" + MARKER + "\n")
    if i == -1:
        return text, None
    return text[: i + 1], text[i + 1 :]


def main() -> int:
    check = "--check" in sys.argv
    text = CONTACTS.read_text(encoding="utf-8")
    head, current = split_doc(text)
    new_block = build_block()
    if check:
        if current is None:
            print("contacts.md: generated marker missing")
            return 1
        if strip_stamp(current) != strip_stamp(new_block):
            print("contacts.md service directory stale")
            return 1
        return 0
    if current is None:
        head = text.rstrip("\n") + "\n\n"
    CONTACTS.write_text(head + new_block, encoding="utf-8")
    print(f"wrote contacts.md service directory ({new_block.count('[[')} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
