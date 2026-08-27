"""Mirror the canonical .claude/ machinery into the Obsidian-visible trees.

Truth direction (adopted 2026-08-27): `.claude/skills/<slug>/SKILL.md` and
`.claude/agents/<role>.md` are CANONICAL — full content, standard cross-vendor
frontmatter (name/description, auto-discovered by Claude Code, Grok Build, and
other SKILL.md-standard agents) with the org-schema keys under `metadata:`.
This generator rewrites the visible mirrors at their historical paths —
`Knowledge/Skills/<TYPE>/<Title>.md` and `Knowledge/Agents/<role>.md` — so
wikilinks, the graph, per-TYPE indexes, and the link map keep working.

Contract (Knowledge/Skills/RULE/Maintain Generated Sections.md + Keep Machinery
Vendor-Portable.md):
- Whole-file generated: mirrors carry `author_type: script` + a banner line.
  Never hand-edit a mirror — edit the canonical file and re-run.
- Fail loud, never partial: every canonical file is parsed before anything is
  written; any error -> exit 2, zero writes.
- Hand-edit guard: SYSTEM/.cache/claude-mirror-hashes.json records each
  mirror's last-generated hash. A mirror that matches neither its recorded
  hash nor the new expected content was hand-edited -> abort (exit 3) so the
  edit can be reconciled into the canonical file first. (No manifest entry =
  bootstrap/fresh checkout -> overwrite allowed.)
- Idempotent: unchanged mirrors are not rewritten (the Generated: stamp only
  moves when content moves); comparisons ignore the stamp date.
- Orphan detection: a visible skill/agent note with no canonical source is an
  error (a deleted canonical leaves its mirror flagged, never silently kept).

Usage: uv run python SYSTEM/bin/build_claude_mirrors.py [--check]
  --check: verify mirrors match canonical (lint mirror check); exit 1 on
  drift, write nothing.
"""

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

VAULT = Path(__file__).resolve().parent.parent.parent
Knowledge = VAULT / "Knowledge"   # kit layout; a live instance may flatten these to the root
MANIFEST = VAULT / "SYSTEM" / ".cache" / "claude-mirror-hashes.json"
TYPES = {"do": "DO", "check": "CHECK", "format": "FORMAT", "rule": "RULE"}
STAMP_RE = re.compile(r"Generated: \d{4}-\d{2}-\d{2}")


def fail(msg: str, code: int = 2) -> None:
    print(f"FAIL  {msg}", file=sys.stderr)
    sys.exit(code)


def split_frontmatter(text: str, path: Path):
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        fail(f"no frontmatter fence in {path}")
    end = text.index("\n---", 4)
    return text[4:end].rstrip("\n"), text[end + 4 :].lstrip("\n")


def metadata_block(fm_lines: str, path: Path) -> str:
    """Extract the metadata: sub-block verbatim, dedented 2 spaces."""
    lines = fm_lines.split("\n")
    try:
        start = next(i for i, ln in enumerate(lines) if ln.rstrip() == "metadata:")
    except StopIteration:
        fail(f"no metadata: block in {path}")
    block = []
    for ln in lines[start + 1 :]:
        if ln.strip() == "" or ln.startswith("  "):
            block.append(ln[2:] if ln.startswith("  ") else ln)
        else:
            break
    if not block:
        fail(f"empty metadata: block in {path}")
    return "\n".join(block).rstrip("\n")


def normalized(text: str) -> str:
    return STAMP_RE.sub("Generated: X", text)


def sha(text: str) -> str:
    return hashlib.sha256(normalized(text).encode("utf-8")).hexdigest()


def build_expected():
    """Parse every canonical file -> {mirror relpath: content}. Fail-loud."""
    expected = {}
    today = date.today().isoformat()

    skills_root = VAULT / ".claude" / "skills"
    if not skills_root.is_dir():
        fail("missing .claude/skills/")
    for skill in sorted(skills_root.glob("*/SKILL.md")):
        slug = skill.parent.name
        text = skill.read_text(encoding="utf-8")
        fm_lines, body = split_frontmatter(text, skill)
        meta_raw = metadata_block(fm_lines, skill)
        try:
            meta = yaml.safe_load(meta_raw)
        except yaml.YAMLError as e:
            fail(f"unparseable metadata in {skill}: {e}")
        if "alias_of" in meta:
            continue  # alias stub — no mirror
        title, typ = meta.get("title"), meta.get("type")
        if not title or typ not in TYPES:
            fail(f"{skill}: metadata needs title: and type: (do|check|format|rule)")
        mirror_fm = "\n".join(
            ln for ln in meta_raw.split("\n") if not ln.startswith("title:")
        )
        banner = (
            f"> _Generated from `.claude/skills/{slug}/SKILL.md` by "
            f"`SYSTEM/bin/build_claude_mirrors.py` — edit the canonical file, "
            f"never this mirror. Generated: {today}_"
        )
        rel = f"Knowledge/Skills/{TYPES[typ]}/{title}.md"
        expected[rel] = f"---\n{mirror_fm}\nauthor_type: script\n---\n\n{banner}\n\n{body}"

    agents_root = VAULT / ".claude" / "agents"
    if agents_root.is_dir():
        for agent in sorted(agents_root.glob("*.md")):
            text = agent.read_text(encoding="utf-8")
            fm_lines, body = split_frontmatter(text, agent)
            meta_raw = metadata_block(fm_lines, agent)
            try:
                meta = yaml.safe_load(meta_raw)
            except yaml.YAMLError as e:
                fail(f"unparseable metadata in {agent}: {e}")
            role = meta.get("role") or meta.get("name")
            if not role:
                fail(f"{agent}: metadata needs role: or name:")
            # Lift harness-enforced top-level keys (tools:/model:) into the
            # mirror — single-sourced from the canonical file, skipped if
            # metadata already carries the key.
            lifted = "".join(
                f"{ln}\n"
                for ln in fm_lines.split("\n")
                if re.match(r"^(tools|model): ", ln)
                and f"\n{ln.split(':')[0]}:" not in f"\n{meta_raw}"
            )
            banner = (
                f"> _Generated from `.claude/agents/{agent.name}` by "
                f"`SYSTEM/bin/build_claude_mirrors.py` — edit the canonical file, "
                f"never this mirror. Generated: {today}_"
            )
            rel = f"Knowledge/Agents/{role}.md"
            expected[rel] = (
                f"---\n{meta_raw}\n{lifted}author_type: script\n---\n\n{banner}\n\n{body}"
            )
    return expected


def visible_notes():
    """All visible notes the generator owns (mirror candidates), for orphan checks."""
    found = set()
    for d in (Knowledge / "Skills").iterdir():
        if not d.is_dir():
            continue
        for f in d.glob("*.md"):
            if f.name.endswith(" TEMPLATE.md") or f.name == f"{d.name} Index.md":
                continue
            found.add(f.relative_to(VAULT).as_posix())
    for f in (Knowledge / "Agents").glob("*.md"):
        if f.name.endswith(" TEMPLATE.md") or f.name == "index.md":
            continue
        found.add(f.relative_to(VAULT).as_posix())
    return found


def main() -> None:
    check_only = "--check" in sys.argv
    expected = build_expected()

    orphans = visible_notes() - set(expected)
    if orphans:
        for o in sorted(orphans):
            print(f"FAIL  orphan mirror (no canonical .claude source): {o}", file=sys.stderr)
        sys.exit(1 if check_only else 2)

    if check_only:
        drift = []
        for rel, content in sorted(expected.items()):
            p = VAULT / rel
            if not p.exists():
                drift.append(f"missing mirror: {rel}")
            elif normalized(p.read_text(encoding="utf-8")) != normalized(content):
                drift.append(f"mirror out of date: {rel}")
        if drift:
            for d in drift:
                print(f"FAIL  {d}", file=sys.stderr)
            sys.exit(1)
        print(f"OK  {len(expected)} mirrors in sync with .claude/")
        return

    manifest = {}
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            fail(f"unparseable manifest {MANIFEST} — delete it to re-bootstrap", 3)

    # Hand-edit guard before any write.
    for rel, content in expected.items():
        p = VAULT / rel
        if p.exists() and rel in manifest:
            on_disk = sha(p.read_text(encoding="utf-8"))
            if on_disk != manifest[rel] and on_disk != sha(content):
                fail(
                    f"{rel} was hand-edited since last generation — reconcile the "
                    f"edit into its canonical .claude file, then delete this "
                    f"mirror and re-run",
                    3,
                )

    written = 0
    for rel, content in sorted(expected.items()):
        p = VAULT / rel
        if not (p.exists() and normalized(p.read_text(encoding="utf-8")) == normalized(content)):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            written += 1
        manifest[rel] = sha(content) if not p.exists() else sha(p.read_text(encoding="utf-8"))
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    print(f"mirrors: {len(expected)} total, {written} (re)written")


if __name__ == "__main__":
    main()
