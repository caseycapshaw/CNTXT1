"""Throwaway git-repo vault fixture for gardener tests. Mirrors the shape of
a real CNTXT1 vault just enough to exercise guardrails, the actions
stage, and the digest stage without touching a real KB.
"""
from __future__ import annotations
import os as _os; _os.environ.setdefault("GARDENER_MIN_RAW_AGE_MIN", "0")  # fixtures create fresh captures

import subprocess
import tempfile
from pathlib import Path


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(vault: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(vault), *args], check=True, capture_output=True, text=True)


def make_vault(prefix: str = "gardener-vault-") -> Path:
    """A minimal but real git repo with the vault's structural folders,
    one concept with a human callout + a checked action, one open action
    lacking a created-date stamp, SYSTEM/decisions.md, a raw/ capture, and
    the lint.sh/regen-all.sh scripts stubbed out so stages that shell
    out to them don't explode (tests stub GARDENER_CLAUDE_CMD separately)."""
    root = Path(tempfile.mkdtemp(prefix=prefix))

    _write(root / "README.md", "# README\n")
    _write(root / "index.md", "# Index\n\n## Quick map\n\n- [[example-concept]]\n")
    _write(root / "Actions.md", "# Actions\n")
    _write(root / "CLAUDE.md", "# CLAUDE\n\n" + "@" + "AGENTS.md\n")
    _write(root / "AGENTS.md", "# AGENTS\n")

    _write(
        root / "05 concepts" / "example-concept.md",
        "---\n"
        "type: concept\n"
        "description: An example concept for tests.\n"
        "updated: 2026-09-01\n"
        "status: current\n"
        "tags: [concept]\n"
        "---\n\n"
        "# Example Concept\n\n"
        "> [!human]\n"
        "> This is The owner's own note, verbatim. Do not touch it.\n\n"
        "## Actions\n"
        "- [x] already done #action\n"
        "- [ ] still open, no date #action\n",
    )

    _write(
        root / "raw" / "2026-09-01-example-capture.md",
        "# 2026-09-01 — Example capture\n\nSource: conversation.\n\nSome durable fact.\n",
    )

    _write(root / "SYSTEM" / "decisions.md", "# Decisions\n\n- 2026-09-01 — an example ruling.\n")
    _write(root / "SYSTEM" / "log.md", "# Log\n\n- 2026-09-01 — vault created for tests.\n")

    _write(root / "Agents" / "life-coach" / "journal-log.md", "## 2026-09-01 08:00\nverbatim journal text\n")

    for d in ["03 Projects", "02 Areas", "01 Horizons", "04 People", "Skills", "attachments", "excalidraw", "docs", "00 daily"]:
        (root / d).mkdir(parents=True, exist_ok=True)
        gk = root / d / ".gitkeep"
        gk.write_text("", encoding="utf-8")

    # Minimal SYSTEM/bin so stages that shell out don't crash the fixture —
    # real generators/lint.sh are NOT copied in (tests exercise the pure
    # Python guardrail/actions/digest logic directly, not the vault's bash tooling).
    bin_dir = root / "SYSTEM" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    _write(bin_dir / "lint.sh", "#!/usr/bin/env bash\necho 'LINT: green (mechanical checks)'\nexit 0\n")
    (bin_dir / "lint.sh").chmod(0o755)
    _write(bin_dir / "regen-all.sh", "#!/usr/bin/env bash\necho 'regen-all: ok'\nexit 0\n")
    (bin_dir / "regen-all.sh").chmod(0o755)

    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Gardener Test")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "initial vault fixture")
    return root
