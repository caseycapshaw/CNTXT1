#!/usr/bin/env python3
"""gardener.py — autonomous KB "gardener" for a CNTXT1 vault (optional
add-on). Python 3.11 stdlib only.

ISOLATION (non-negotiable): the live $VAULT folder is usually shared with a
sync tool (Syncthing, Obsidian Sync, ...) and an editor open on another
machine — human edits can land there uncommitted at any moment, including while gardener is mid-run. Gardener therefore NEVER
does stage work, guardrail reverts, or `git checkout --`/`reset` directly in
the live vault. Instead, each run:

  1. **checkpoint** — commits whatever's currently dirty in the live vault
     (attributed to the human — that's their in-progress edit, not gardener's),
     no-op if clean.
  2. **isolate** — adds a `git worktree` at that checkpoint commit, OUTSIDE
     the synced folder (default `~/.local/state/cntxt1/gardener-wt`), on its
     own branch (`gardener/run-<ts>` for apply, `gardener/proposal-<date>`
     for propose). Every stage — including guardrail enforcement — runs
     entirely inside that worktree. A stage's guardrail check only ever sees
     the diff the stage itself produced there.
  3. **merge back** (apply mode only) — in the LIVE vault: checkpoint again
     (catches any human edits that arrived during the run), then
     `git merge --no-edit <gardener branch>`. A real conflict aborts the
     merge (`git merge --abort`) and leaves the gardener branch in place for
     manual review — the run still exits 0. Propose mode skips this step
     entirely; the branch is left for a human to review/merge by hand.

Runs a fixed pipeline of stages inside the worktree: regen -> compile ->
lint -> inbox -> actions -> digest. Each stage is at most one commit
(`gardener(<stage>): <message>`); a stage with no diff makes no commit.

Guardrails run after every stage (LLM-driven or not, inside the worktree
only) and hard-reject any change that: edits existing raw/ content or adds a
new file under raw/ (except the exact generated-index paths in
`RAW_GENERATED_ALLOWLIST`, e.g. `raw/index.md`), touches a forbidden path
(SYSTEM/decisions.md, SYSTEM/Journal.md, Agents/life-coach/journal-log.md, AGENTS.md, CLAUDE.md,
SYSTEM/SCHEMA.md, .claude/**, .obsidian/**), alters or removes text inside a
`> [!human]` callout, deletes any file, or changes an already-checked-off
`- [x]` action line. Rejections are reverted (`git checkout --`/removal,
inside the worktree) and recorded in the run log + digest.

Usage:
  gardener/run.sh [--mode propose|apply] [--stage all|regen|compile|lint|inbox|actions|digest] [--max-llm-calls N]

Env:
  VAULT                    live vault path (default: the vault this add-on lives in,
                            i.e. three levels above this file, if it holds
                            SYSTEM/SCHEMA.md; otherwise VAULT is required)
  GARDENER_WT               isolated worktree path (default
                            $HOME/.local/state/cntxt1/gardener-wt) — must be
                            outside the Syncthing/Obsidian-Sync'd folder
  GARDENER_CHECKPOINT_AUTHOR git author for checkpoint commits of pending
                            human edits (default: the vault's `git config user.name/user.email`,
                            else "KB Owner <kb-owner@localhost>")
  NTFY_URL                  optional ntfy topic URL for the run summary
  CREDENTIALS_DIRECTORY     systemd-style credential dir; looks for claude-oauth-token
  CLAUDE_CODE_OAUTH_TOKEN   fallback token env var
  GARDENER_CLAUDE_CMD       override the `claude` binary/command (tests use a fake script)
  GARDENER_MAX_LLM_CALLS    overrides the default global LLM-call budget (12)
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_WORKTREE = str(Path.home() / ".local" / "state" / "cntxt1" / "gardener-wt")
FALLBACK_CHECKPOINT_AUTHOR = "KB Owner <kb-owner@localhost>"
DEFAULT_MAX_LLM_CALLS = 12
STAGE_LLM_CAPS = {"compile": 6, "lint": 3, "inbox": 3}
ACTIONS_MAX_STAMPS_PER_RUN = 50
LLM_TIMEOUT_SECONDS = 300
STAGE_ORDER = ["regen", "compile", "lint", "inbox", "actions", "digest"]

FORBIDDEN_EXACT = {
    "SYSTEM/decisions.md",
    "SYSTEM/Journal.md",
    "Agents/life-coach/journal-log.md",
    "AGENTS.md",
    "CLAUDE.md",
    "SYSTEM/SCHEMA.md",
}
FORBIDDEN_PREFIXES = (".claude/", ".obsidian/")

# Exact raw/ paths that ARE allowed to change — the regen stage's own
# generated indexes under raw/ (e.g. build_directory_indexes.py's
# raw/index.md), nothing else. Every other raw/ path stays append-only.
RAW_GENERATED_ALLOWLIST = {"raw/index.md"}

ROOT_ANCHORS = {"README.md", "index.md", "Actions.md", "CLAUDE.md", "AGENTS.md"}
ROOT_STRUCTURAL = {
    "05 concepts", "03 Projects", "02 Areas", "01 Horizons", "SYSTEM", "Agents",
    "raw", "00 daily", "04 People", "Skills", "attachments", "excalidraw", "docs",
}
ROOT_TOOLING = {"pyproject.toml", "uv.lock"}
ROOT_STANDING = {"Upstream kit updates (pending).md"}

GARDENER_SYSTEM_RULES = """You are the automated "gardener" for this KB, running unattended. Follow
SYSTEM/SCHEMA.md and AGENTS.md exactly. Hard rules, no exceptions:
- Never edit, rewrite, or delete anything under raw/ — it is append-only and
  read-only to you. Never create a new file under raw/ either — filing an
  item into raw/ is a `git mv`, never a copy that leaves the original in a
  new form.
- Never touch SYSTEM/decisions.md, SYSTEM/Journal.md,
  Agents/life-coach/journal-log.md, AGENTS.md, CLAUDE.md, SYSTEM/SCHEMA.md, or
  anything under .claude/ or .obsidian/.
- Never delete any file (use `git mv` to relocate, never `rm`).
- Never edit or remove text inside a `> [!human]` callout — integrate around
  it, never rewrite the quoted words.
- Never un-check or edit the text of an already checked-off `- [x]` action line.
- Do not invent facts. Every claim traces to a raw/ capture or a file you
  actually read; flag gaps as open questions instead of guessing.
- Do not run `git commit` — the gardener commits your changes after checking
  them; just leave the working tree edited.
- Keep changes narrowly scoped to the task you were given.
"""

COMPILE_PROMPT = """Compile the raw capture at `{rel_path}` into this KB, following
`.claude/agents/compile.md` and `SYSTEM/SCHEMA.md` exactly (read both first).
Then read `{rel_path}` itself.

Create or update the matching compiled note(s) using the first-match-wins
routing in AGENTS.md (person/org -> 04 People/, completable work -> 03 Projects/,
ongoing responsibility -> 02 Areas/, procedure -> .claude/skills/, orientation ->
01 Horizons/, otherwise -> 05 concepts/). Update index.md's Quick map if you add
or rename a concept/project/area, and append one `SYSTEM/log.md` line describing
what you did (date + one sentence). If the capture is genuinely already covered
by an existing note, say so and make no change rather than forcing a duplicate.
"""

LINT_FIX_PROMPT = """The KB's mechanical linter (SYSTEM/bin/lint.sh) reported this
FAIL that a generator script cannot auto-fix:

{fail_line}

Read SYSTEM/SCHEMA.md for the relevant convention, then make the smallest
correct edit that resolves this specific finding. If it is an orientation-
section cap overflow (SCHEMA § "Orientation caps + trails"), move the oldest
content verbatim into the note's trail sibling
(`03 Projects/trails/<slug>-trail.md` / `02 Areas/trails/<slug>-trail.md`,
`type: trail`, `of: "[[slug]]"`, append-only) and rewrite the section to keep
only what's still true. If it is a broken wikilink, fix the link text only if
it's a clear typo/rename target that resolves to a real note or alias — a
`[[link]]` to a note that doesn't exist yet is allowed by SCHEMA and should be
left alone. Do not attempt to fix findings other than the one above.
"""

INBOX_PROMPT = """The file `{item}` sits un-triaged at the vault root (the
inbox). File it per `.claude/skills/file-a-new-note/SKILL.md` (read it first):
capture first (if it quotes a source) via `git mv "{item}" "raw/{today}-<topic>.md"`
(a rename, not a copy-then-delete — the guardrails hard-reject any actual
deletion), then walk the type branch (person/org -> 04 People/, work via the
endpoint test -> 03 Projects/ or 02 Areas/, procedure -> .claude/skills/,
orientation -> 01 Horizons/, otherwise -> 05 concepts/) to create or update the
compiled note, fill its frontmatter honestly, add it to index.md if its folder
is indexed there, and append a `SYSTEM/log.md` line. If no branch fits, leave
the item in place, add a `#action` naming the gap on `05 concepts/kb-systems.md`,
and say so — a forced-fit note is worse than a recorded fall-through.
"""

CLAUDE_ALLOWED_TOOLS = {
    "compile": "Read,Edit,Write,Grep,Glob,Bash(rg:*),Bash(SYSTEM/bin/*)",
    "lint": "Read,Edit,Write,Grep,Glob,Bash(rg:*),Bash(SYSTEM/bin/*)",
    "inbox": "Read,Edit,Write,Grep,Glob,Bash(rg:*),Bash(SYSTEM/bin/*),Bash(git mv:*)",
}

# The vault's own generator entry point (SYSTEM/bin/regen-all.sh) runs every
# generator the kit ships, in dependency order — the gardener never hardcodes
# the list, so a generator added to regen-all.sh is picked up automatically.
# regen-all.sh shells out to `uv run`, so the stage is skipped without uv.
REGEN_ALL = {"cmd": ["bash", "SYSTEM/bin/regen-all.sh"], "name": "regen-all", "needs_uv": True}
GENERATORS = [REGEN_ALL]

# A lint line mentioning any of these is a stale generated view: the mechanical
# fix is simply to re-run regen-all.sh (once per lint stage).
MECHANICAL_FIX_MAP = [
    (re.compile(r"stale generated view|link-map|\.claude.*mirror|index\.md Projects section|"
                r"contacts\.md service directory|directory indexes stale|horizon/goal serving lists", re.I),
     REGEN_ALL),
]

DATE_STAMP_RE = re.compile(r"➕ ?\d{4}-\d{2}-\d{2}")
CHECKED_RE = re.compile(r"^\s*- \[x\]")
OPEN_ACTION_RE = re.compile(r"^\s*- \[ \]")
ACTIONS_SCAN_DIRS = ["05 concepts", "03 Projects", "02 Areas", "04 People", "01 Horizons", "Agents"]

GARDENER_DIGEST_START = "<!-- gardener:auto:start -->"
GARDENER_DIGEST_END = "<!-- gardener:auto:end -->"


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def claude_cmd() -> str:
    return os.environ.get("GARDENER_CLAUDE_CMD", "claude")


def get_claude_auth_env() -> dict:
    cred_dir = os.environ.get("CREDENTIALS_DIRECTORY")
    if cred_dir:
        token_path = Path(cred_dir) / "claude-oauth-token"
        if token_path.exists():
            return {"CLAUDE_CODE_OAUTH_TOKEN": token_path.read_text(encoding="utf-8").strip()}
    tok = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if tok:
        return {"CLAUDE_CODE_OAUTH_TOKEN": tok}
    return {}


class Budget:
    def __init__(self, maximum: int):
        self.maximum = maximum
        self.used = 0

    def exhausted(self) -> bool:
        return self.used >= self.maximum

    def spend(self, n: int = 1) -> None:
        self.used += n


@contextmanager
def repo_lock(vault: Path):
    git_dir = Path(vault) / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)
    lock_path = git_dir / "gardener.lock"
    fh = open(lock_path, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        raise SystemExit("gardener: another run holds SYSTEM/../.git/gardener.lock — exiting")
    try:
        yield
    finally:
        try:
            fcntl.flock(fh, fcntl.LOCK_UN)
        finally:
            fh.close()


# ---------------------------------------------------------------------------
# git helpers
# ---------------------------------------------------------------------------


def git(vault: Path, *args: str, check: bool = True) -> str:
    res = subprocess.run(["git", "-C", str(vault), *args], capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout


def git_show_head(vault: Path, rel_path: str) -> Optional[str]:
    res = subprocess.run(["git", "-C", str(vault), "show", f"HEAD:{rel_path}"], capture_output=True, text=True)
    if res.returncode != 0:
        return None
    return res.stdout


def _unquote_git_path(path: str) -> str:
    """git quotes a path in the porcelain output (wrapped in `"..."`, with
    `\\"`/`\\\\`/octal escapes) whenever core.quotepath's default rules fire —
    which includes any path containing a space, and every folder in this
    vault has one (`05 concepts`, `03 Projects`, `00 daily`, ...). Strip that
    quoting back to a real relative path."""
    if len(path) >= 2 and path[0] == '"' and path[-1] == '"':
        inner = path[1:-1]
        out = []
        i = 0
        while i < len(inner):
            c = inner[i]
            if c == "\\" and i + 1 < len(inner):
                nxt = inner[i + 1]
                simple = {'"': '"', "\\": "\\", "t": "\t", "n": "\n"}
                if nxt in simple:
                    out.append(simple[nxt])
                    i += 2
                    continue
                if nxt.isdigit() and i + 3 < len(inner) + 1:
                    octal = inner[i + 1:i + 4]
                    try:
                        out.append(chr(int(octal, 8)))
                        i += 4
                        continue
                    except ValueError:
                        pass
            out.append(c)
            i += 1
        return "".join(out)
    return path


def git_status_entries(vault: Path) -> list[tuple[str, str]]:
    """Return (status, path) pairs. Renames are collapsed to (status, new_path)
    so a `git mv` never trips the deletion guardrail on its old path."""
    out = git(vault, "status", "--porcelain=v1", "--find-renames", "--untracked-files=all")
    entries = []
    for line in out.splitlines():
        if not line:
            continue
        status = line[:2].strip()
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append((status, _unquote_git_path(path)))
    return entries


def has_diff(vault: Path) -> bool:
    return bool(git(vault, "status", "--porcelain").strip())


def commit_stage(vault: Path, stage: str, message: str) -> Optional[str]:
    if not has_diff(vault):
        return None
    git(vault, "add", "-A")
    git(vault, "commit", "-m", f"gardener({stage}): {message}")
    return git(vault, "rev-parse", "HEAD").strip()


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------


def human_callout_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].strip().startswith("> [!human]"):
            block = [lines[i]]
            i += 1
            while i < n and lines[i].startswith(">"):
                block.append(lines[i])
                i += 1
            blocks.append("\n".join(block))
        else:
            i += 1
    return blocks


def checked_action_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if CHECKED_RE.match(line)]


def path_forbidden(rel_path: str) -> bool:
    if rel_path in FORBIDDEN_EXACT:
        return True
    for prefix in FORBIDDEN_PREFIXES:
        if rel_path == prefix.rstrip("/") or rel_path.startswith(prefix):
            return True
    return False


def is_raw_path(rel_path: str) -> bool:
    return rel_path == "raw" or rel_path.startswith("raw/")


def guardrail_reject_reason(rel_path: str, status: str, old_text: Optional[str], new_text: Optional[str]) -> Optional[str]:
    """Pure decision function (no I/O) so it's directly unit-testable."""
    if path_forbidden(rel_path):
        return f"forbidden path touched: {rel_path}"

    protected_raw = is_raw_path(rel_path) and rel_path not in RAW_GENERATED_ALLOWLIST
    if protected_raw:
        if status in ("??", "A") or old_text is None:
            return f"new file created under raw/ (append-only, never a new file): {rel_path}"
        if new_text is None:
            return f"raw/ capture deleted: {rel_path}"
        if old_text != new_text:
            return f"raw/ capture content modified (append-only): {rel_path}"
        return None

    # Everything else — including the raw/ generated-index allow-list — is
    # subject to the general rules: never deleted, never a callout/checked-
    # action edit.
    if status == "D" or (old_text is not None and new_text is None):
        return f"file deleted: {rel_path}"

    if old_text is not None and new_text is not None and old_text != new_text:
        old_blocks = human_callout_blocks(old_text)
        for block in old_blocks:
            if block not in new_text:
                return f"'> [!human]' callout altered or removed: {rel_path}"
        old_checked = checked_action_lines(old_text)
        new_lines = set(new_text.splitlines())
        for line in old_checked:
            if line not in new_lines:
                return f"checked-off action line changed: {rel_path}"

    return None


def revert_path(vault: Path, rel_path: str, status: str) -> None:
    full = Path(vault) / rel_path
    if status == "??":
        if full.is_dir():
            shutil.rmtree(full, ignore_errors=True)
        elif full.exists():
            full.unlink()
        return
    # tracked (modified/deleted/renamed-away-from-baseline) -> restore from index/HEAD
    subprocess.run(["git", "-C", str(vault), "checkout", "--", rel_path], capture_output=True, text=True)


def enforce_guardrails(vault: Path, stage: str) -> list[dict]:
    rejected = []
    for status, rel_path in git_status_entries(vault):
        full = Path(vault) / rel_path
        old_text = git_show_head(vault, rel_path)
        if full.exists() and full.is_file():
            try:
                new_text = full.read_text(encoding="utf-8", errors="replace")
            except Exception:
                new_text = None
        else:
            new_text = None
        reason = guardrail_reject_reason(rel_path, status, old_text, new_text)
        if reason:
            revert_path(vault, rel_path, status)
            rejected.append({"path": rel_path, "reason": reason, "stage": stage})
    return rejected


# ---------------------------------------------------------------------------
# Claude headless invocation
# ---------------------------------------------------------------------------


def run_claude(vault: Path, prompt: str, tool_key: str, timeout: int = LLM_TIMEOUT_SECONDS) -> dict:
    env = os.environ.copy()
    env.update(get_claude_auth_env())
    cmd = [
        claude_cmd(),
        "-p", prompt,
        "--permission-mode", "acceptEdits",
        "--allowedTools", CLAUDE_ALLOWED_TOOLS[tool_key],
        "--append-system-prompt", GARDENER_SYSTEM_RULES,
    ]
    try:
        res = subprocess.run(cmd, cwd=str(vault), env=env, capture_output=True, text=True, timeout=timeout)
        return {"returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": 124, "stdout": (exc.stdout or ""), "stderr": f"timed out after {timeout}s", "timed_out": True}
    except FileNotFoundError as exc:
        return {"returncode": 127, "stdout": "", "stderr": str(exc), "timed_out": False}


# ---------------------------------------------------------------------------
# Stage: regen
# ---------------------------------------------------------------------------


def do_regen(vault: Path) -> dict:
    ran, skipped, failed = [], [], []
    uv_available = shutil.which("uv") is not None
    for gen in GENERATORS:
        if gen["needs_uv"] and not uv_available:
            skipped.append(gen["name"] + " (uv not installed)")
            continue
        res = subprocess.run(gen["cmd"], cwd=str(vault), capture_output=True, text=True)
        if res.returncode == 0:
            ran.append(gen["name"])
        else:
            failed.append({"name": gen["name"], "stderr": res.stderr[-2000:]})
    rejections = enforce_guardrails(vault, "regen")
    sha = commit_stage(vault, "regen", f"regenerate derived indexes ({', '.join(ran) or 'no diff'})")
    return {
        "name": "regen", "commit": sha, "ran": ran, "skipped": skipped, "failed": failed,
        "rejections": rejections, "llm_calls": 0,
    }


# ---------------------------------------------------------------------------
# Stage: compile
# ---------------------------------------------------------------------------


def find_orphan_raw(vault: Path) -> list[Path]:
    corpus_parts = []
    for p in Path(vault).rglob("*.md"):
        rel = p.relative_to(vault)
        top = rel.parts[0] if rel.parts else ""
        if top in ("raw", "SYSTEM", ".git", ".obsidian", ".venv"):
            continue
        try:
            corpus_parts.append(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
    corpus = "\n".join(corpus_parts)
    raw_dir = Path(vault) / "raw"
    if not raw_dir.exists():
        return []
    # Settle time: skip captures committed less than GARDENER_MIN_RAW_AGE_MIN
    # minutes ago, so a path-triggered run doesn't race an interactive session
    # that is compiling the same capture. Worktree mtimes are checkout times,
    # so age comes from the capture's first commit.
    min_age = int(os.environ.get("GARDENER_MIN_RAW_AGE_MIN", "30")) * 60
    now = time.time()
    orphans = []
    for p in sorted(raw_dir.glob("20*.md")):
        if f"raw/{p.stem}" in corpus:
            continue
        if min_age > 0:
            r = subprocess.run(
                ["git", "-C", str(vault), "log", "--diff-filter=A", "--format=%ct", "-1", "--", f"raw/{p.name}"],
                capture_output=True, text=True, timeout=30,
            )
            added = int(r.stdout.strip() or now)
            if now - added < min_age:
                continue
        orphans.append(p)
    return orphans


def do_compile(vault: Path, budget: Budget) -> dict:
    orphans = find_orphan_raw(vault)
    cap = STAGE_LLM_CAPS["compile"]
    compiled, skipped_budget, calls = [], [], 0
    for p in orphans:
        if calls >= cap or budget.exhausted():
            skipped_budget.append(p.name)
            continue
        rel = p.relative_to(vault).as_posix()
        prompt = COMPILE_PROMPT.format(rel_path=rel)
        result = run_claude(vault, prompt, "compile")
        calls += 1
        budget.spend()
        compiled.append({"raw": rel, "returncode": result["returncode"], "timed_out": result["timed_out"]})
    rejections = enforce_guardrails(vault, "compile")
    sha = commit_stage(vault, "compile", f"compile {len(compiled)} raw capture(s) ({', '.join(c['raw'] for c in compiled) or 'no diff'})")
    return {
        "name": "compile", "commit": sha, "orphans_found": [p.name for p in orphans],
        "compiled": compiled, "skipped_budget": skipped_budget, "rejections": rejections,
        "llm_calls": calls,
    }


# ---------------------------------------------------------------------------
# Stage: lint
# ---------------------------------------------------------------------------


def run_lint(vault: Path) -> tuple[int, list[str], str]:
    res = subprocess.run(["bash", "SYSTEM/bin/lint.sh"], cwd=str(vault), capture_output=True, text=True)
    fails = [line for line in (res.stdout + res.stderr).splitlines() if line.startswith("FAIL")]
    return res.returncode, fails, res.stdout + res.stderr


def do_lint(vault: Path, budget: Budget) -> dict:
    rc_before, fails_before, out_before = run_lint(vault)

    fixed_by = []
    already_run = set()
    # Mechanical fixes: stale generated views surface as WARN (default) or FAIL
    # (LINT_STRICT=1). Either way the fix is to re-run the generators.
    findings = [ln for ln in out_before.splitlines() if ln.startswith(("FAIL", "WARN"))]
    for line in findings:
        for pattern, gen in MECHANICAL_FIX_MAP:
            if pattern.search(line) and gen["name"] not in already_run:
                already_run.add(gen["name"])
                if gen["needs_uv"] and shutil.which("uv") is None:
                    continue
                subprocess.run(gen["cmd"], cwd=str(vault), capture_output=True, text=True)
                fixed_by.append(gen["name"])
    # Whatever FAIL lines the generators didn't cover go to the LLM (capped).
    remaining_fails = [ln for ln in fails_before
                       if not any(p.search(ln) for p, _ in MECHANICAL_FIX_MAP)]

    cap = STAGE_LLM_CAPS["lint"]
    calls = 0
    llm_fixed = []
    for fail_line in remaining_fails:
        if calls >= cap or budget.exhausted():
            break
        prompt = LINT_FIX_PROMPT.format(fail_line=fail_line)
        result = run_claude(vault, prompt, "lint")
        calls += 1
        budget.spend()
        llm_fixed.append({"fail": fail_line, "returncode": result["returncode"], "timed_out": result["timed_out"]})

    rejections = enforce_guardrails(vault, "lint")
    rc_after, fails_after, _ = run_lint(vault)
    sha = commit_stage(
        vault, "lint",
        f"fix {len(fixed_by)} mechanical + {len(llm_fixed)} narrow lint finding(s) "
        f"(FAILs {len(fails_before)} -> {len(fails_after)})",
    )
    return {
        "name": "lint", "commit": sha,
        "fails_before": len(fails_before), "fails_after": len(fails_after),
        "fail_lines_before": fails_before, "fail_lines_after": fails_after,
        "mechanical_fixes": fixed_by, "llm_fixes": llm_fixed, "rejections": rejections,
        "llm_calls": calls,
    }


# ---------------------------------------------------------------------------
# Stage: inbox
# ---------------------------------------------------------------------------


def find_inbox_items(vault: Path) -> list[str]:
    allow = ROOT_ANCHORS | ROOT_STRUCTURAL | ROOT_TOOLING | ROOT_STANDING
    items = []
    for e in sorted(Path(vault).iterdir()):
        name = e.name
        if name in allow or name.startswith("."):
            continue
        items.append(name)
    return items


def do_inbox(vault: Path, budget: Budget) -> dict:
    items = find_inbox_items(vault)
    cap = STAGE_LLM_CAPS["inbox"]
    today = dt.date.today().isoformat()
    filed, skipped_budget, calls = [], [], 0
    for item in items:
        if calls >= cap or budget.exhausted():
            skipped_budget.append(item)
            continue
        prompt = INBOX_PROMPT.format(item=item, today=today)
        result = run_claude(vault, prompt, "inbox")
        calls += 1
        budget.spend()
        filed.append({"item": item, "returncode": result["returncode"], "timed_out": result["timed_out"]})
    rejections = enforce_guardrails(vault, "inbox")
    sha = commit_stage(vault, "inbox", f"file {len(filed)} root inbox item(s) ({', '.join(f['item'] for f in filed) or 'no diff'})")
    return {
        "name": "inbox", "commit": sha, "items_found": items, "filed": filed,
        "skipped_budget": skipped_budget, "rejections": rejections, "llm_calls": calls,
    }


# ---------------------------------------------------------------------------
# Stage: actions (deterministic — no LLM)
# ---------------------------------------------------------------------------


def git_log_created_date(vault: Path, rel_path: str, pickaxe_text: str) -> Optional[str]:
    res = subprocess.run(
        ["git", "-C", str(vault), "log", "--format=%ad", "--date=short", "--reverse", "-S", pickaxe_text, "--", rel_path],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return None
    lines = [l for l in res.stdout.splitlines() if l.strip()]
    return lines[0] if lines else None


def _find_unstamped_action_candidates(vault: Path) -> list[dict]:
    """Discover every open, unstamped `#action` line across the scan dirs,
    each with its git-log-derived created date — but don't write anything.
    Two-pass design so the caller can sort oldest-first before capping."""
    candidates = []
    for d in ACTIONS_SCAN_DIRS:
        base = Path(vault) / d
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.md")):
            rel = p.relative_to(vault).as_posix()
            if "/trails/" in rel or "/archive/" in rel or "TEMPLATE" in p.name:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines()):
                if OPEN_ACTION_RE.match(line) and "#action" in line and not DATE_STAMP_RE.search(line):
                    created = git_log_created_date(vault, rel, line.strip())
                    if created:
                        candidates.append({"rel": rel, "line_index": i, "created": created})
    return candidates


def do_actions(vault: Path, max_stamps: int = ACTIONS_MAX_STAMPS_PER_RUN) -> dict:
    candidates = _find_unstamped_action_candidates(vault)
    # Oldest first, so the first several runs work through the backlog in a
    # reviewable order rather than dumping hundreds of stamps into one digest.
    candidates.sort(key=lambda c: c["created"])
    chosen = candidates[:max_stamps]
    skipped_budget = len(candidates) - len(chosen)

    by_file: dict[str, list[dict]] = {}
    for c in chosen:
        by_file.setdefault(c["rel"], []).append(c)

    changed_files = []
    for rel, items in by_file.items():
        p = Path(vault) / rel
        text = p.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for item in items:
            i = item["line_index"]
            lines[i] = f"{lines[i]} ➕ {item['created']}"
        newline_end = "\n" if text.endswith("\n") else ""
        p.write_text("\n".join(lines) + newline_end, encoding="utf-8")
        changed_files.append(rel)

    rejections = enforce_guardrails(vault, "actions")
    sha = commit_stage(
        vault, "actions",
        f"backfill created-dates on {len(chosen)} action line(s) across {len(changed_files)} file(s) "
        f"(oldest-first, {skipped_budget} left for a future run)",
    )
    return {
        "name": "actions", "commit": sha, "files_changed": sorted(changed_files),
        "actions_stamped": len(chosen), "candidates_total": len(candidates),
        "skipped_budget": skipped_budget, "rejections": rejections, "llm_calls": 0,
    }


# ---------------------------------------------------------------------------
# Stage: digest
# ---------------------------------------------------------------------------


def _revert_command(vault: Path, sha: Optional[str]) -> str:
    if not sha:
        return "(no commit — nothing to revert)"
    return f'git -C "{vault}" revert {sha}'


def build_digest_block(display_vault: Path, run_result: dict) -> str:
    """`display_vault` is the LIVE vault path — used only to spell out the
    human-facing `git -C <live vault> revert <sha>` commands. The commits
    themselves were made inside the isolated worktree and land in the live
    vault's history via the end-of-run merge (or stay on the review branch
    in propose mode) — either way the sha is the same, so the revert command
    is valid once merged."""
    lines = [GARDENER_DIGEST_START, "## Gardener", ""]
    stages = run_result.get("stages", [])
    if not stages:
        lines.append("_No stage data for this run (invoked with `--stage digest` alone)._")
    for s in stages:
        if s["name"] == "digest":
            continue
        lines.append(f"### {s['name']}")
        sha = s.get("commit")
        lines.append(f"- commit: `{sha or '(none — no diff)'}`")
        if s.get("llm_calls"):
            lines.append(f"- LLM calls: {s['llm_calls']}")
        if s["name"] == "regen":
            lines.append(f"- regenerated: {', '.join(s.get('ran', [])) or '(none)'}")
            if s.get("skipped"):
                lines.append(f"- skipped: {', '.join(s['skipped'])}")
            if s.get("failed"):
                lines.append(f"- FAILED: {', '.join(f['name'] for f in s['failed'])}")
        elif s["name"] == "compile":
            lines.append(f"- orphan captures found: {len(s.get('orphans_found', []))}")
            lines.append(f"- compiled this run: {', '.join(c['raw'] for c in s.get('compiled', [])) or '(none)'}")
        elif s["name"] == "lint":
            lines.append(f"- lint FAILs: {s.get('fails_before')} -> {s.get('fails_after')}")
            lines.append(f"- mechanical fixes: {', '.join(s.get('mechanical_fixes', [])) or '(none)'}")
            lines.append(f"- narrow LLM fixes: {len(s.get('llm_fixes', []))}")
        elif s["name"] == "inbox":
            lines.append(f"- root items found: {', '.join(s.get('items_found', [])) or '(none)'}")
            lines.append(f"- filed this run: {', '.join(f['item'] for f in s.get('filed', [])) or '(none)'}")
        elif s["name"] == "actions":
            extra = f" ({s['skipped_budget']} more left for a future run)" if s.get("skipped_budget") else ""
            lines.append(f"- action lines dated: {s.get('actions_stamped', 0)} across {len(s.get('files_changed', []))} file(s){extra}")
        rej = s.get("rejections", [])
        if rej:
            lines.append(f"- guardrail rejections: {len(rej)}")
            for r in rej:
                lines.append(f"  - {r['path']}: {r['reason']}")
        lines.append(f"- revert: `{_revert_command(display_vault, sha)}`")
        lines.append("")
    branch = run_result.get("branch")
    if run_result.get("mode") == "propose" and branch:
        lines.append(f"_Proposal branch: `{branch}` — review and merge by hand; gardener never merges in propose mode._")
        lines.append("")
    merge = run_result.get("merge")
    if merge and merge.get("conflict"):
        lines.append(f"_MERGE CONFLICT bringing `{branch}` into the live vault — left for manual review; nothing above was lost, it's all on that branch._")
        lines.append("")
    lines.append(GARDENER_DIGEST_END)
    return "\n".join(lines)


def write_digest(work_dir: Path, run_result: dict, display_vault: Optional[Path] = None) -> Path:
    if display_vault is None:
        display_vault = work_dir
    daily_dir = Path(work_dir) / "00 daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    note = daily_dir / f"{today}.md"
    if not note.exists():
        note.write_text(f"# {today} — Daily plan\n\n", encoding="utf-8")
    text = note.read_text(encoding="utf-8")

    out_lines = []
    skip = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == GARDENER_DIGEST_START:
            skip = True
            continue
        if stripped == GARDENER_DIGEST_END:
            skip = False
            continue
        if not skip:
            out_lines.append(line)
    while out_lines and out_lines[-1].strip() == "":
        out_lines.pop()

    block = build_digest_block(display_vault, run_result)
    new_text = "\n".join(out_lines) + "\n\n" + block + "\n"
    note.write_text(new_text, encoding="utf-8")
    return note


def notify(message: str) -> None:
    ntfy_url = os.environ.get("NTFY_URL")
    if not ntfy_url:
        return
    try:
        req = urllib.request.Request(ntfy_url, data=message.encode("utf-8"), method="POST")
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def do_digest(work_dir: Path, run_result: dict, display_vault: Optional[Path] = None) -> dict:
    """Runs inside the worktree, like every other stage — the digest commit
    merges back into the live vault along with the rest at end-of-run. The
    merge/conflict outcome itself isn't known yet at this point (it happens
    after all stages finish); the final notify() in run() covers that."""
    note_path = write_digest(work_dir, run_result, display_vault)
    rel = note_path.relative_to(work_dir).as_posix()
    rejections = enforce_guardrails(work_dir, "digest")
    sha = commit_stage(work_dir, "digest", f"write run digest to {rel}")
    return {"name": "digest", "commit": sha, "note": rel, "rejections": rejections, "llm_calls": 0}


# ---------------------------------------------------------------------------
# Isolation: checkpoint the live vault, do all work in a separate worktree,
# merge (or leave for review) at the end. NEVER `git checkout --`/`reset`
# in the live vault — that's what the worktree + guardrail-revert machinery
# is for, and it never runs against the live vault's own working copy.
# ---------------------------------------------------------------------------


def checkpoint_author(vault: Optional[Path] = None) -> str:
    """Author for checkpoint commits of pending human edits: explicit env, else
    the vault's own git identity, else a neutral placeholder."""
    explicit = os.environ.get("GARDENER_CHECKPOINT_AUTHOR")
    if explicit:
        return explicit
    if vault is not None:
        def cfg(key: str) -> str:
            r = subprocess.run(["git", "-C", str(vault), "config", key], capture_output=True, text=True)
            return r.stdout.strip() if r.returncode == 0 else ""
        name, email = cfg("user.name"), cfg("user.email")
        if name and email:
            return f"{name} <{email}>"
    return FALLBACK_CHECKPOINT_AUTHOR


def checkpoint(vault: Path, label: str) -> Optional[str]:
    """Commit whatever's currently dirty in the LIVE vault, attributed to the
    human (Syncthing/Obsidian Sync can deliver an edit there uncommitted at
    any moment — including mid-gardener-run) so it's never at risk of being
    silently overwritten by anything gardener does next. No-op if clean."""
    if not has_diff(vault):
        return None
    git(vault, "add", "-A")
    git(vault, "commit", "--author", checkpoint_author(vault), "-m", f"checkpoint: {label} ({iso_now()})")
    return git(vault, "rev-parse", "HEAD").strip()


def worktree_path() -> Path:
    return Path(os.environ.get("GARDENER_WT", DEFAULT_WORKTREE)).expanduser()


def _worktree_teardown(vault: Path, wt: Path) -> None:
    subprocess.run(["git", "-C", str(vault), "worktree", "remove", "--force", str(wt)], capture_output=True, text=True)
    if wt.exists():
        shutil.rmtree(wt, ignore_errors=True)
    subprocess.run(["git", "-C", str(vault), "worktree", "prune"], capture_output=True, text=True)


def setup_worktree(vault: Path, mode: str) -> tuple[Path, str, str]:
    """Adds an isolated `git worktree` (outside the synced live vault
    folder) at the vault's current HEAD (post-checkpoint), on its own
    branch. Returns (worktree_path, branch_name, start_commit)."""
    wt = worktree_path()
    wt.parent.mkdir(parents=True, exist_ok=True)
    _worktree_teardown(vault, wt)  # clear any stale worktree from a crashed prior run
    start_commit = git(vault, "rev-parse", "HEAD").strip()
    if mode == "propose":
        branch = f"gardener/proposal-{dt.date.today().isoformat()}"
    else:
        branch = f"gardener/run-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    existing = git(vault, "branch", "--list", branch).strip()
    if existing:
        # Same-day propose re-run: continue on the existing review branch
        # rather than forking a second one.
        git(vault, "worktree", "add", str(wt), branch)
    else:
        git(vault, "worktree", "add", "-b", branch, str(wt), start_commit)
    return wt, branch, start_commit


def teardown_worktree(vault: Path, wt: Path) -> None:
    _worktree_teardown(vault, wt)


def merge_back(vault: Path, branch: str) -> dict:
    """Bring the gardener branch's work into the LIVE vault. Checkpoints any
    human edits that landed since the run started (so the merge is a true
    3-way merge against the latest human state, not a fast-forward that
    could silently shadow them), then merges. A genuine conflict aborts
    (`git merge --abort` — the one sanctioned recovery path; never a manual
    checkout/reset of individual files) and leaves the branch for review."""
    pre_merge_checkpoint = checkpoint(vault, f"pre-merge (gardener {branch})")
    res = subprocess.run(["git", "-C", str(vault), "merge", "--no-edit", branch], capture_output=True, text=True)
    if res.returncode != 0:
        subprocess.run(["git", "-C", str(vault), "merge", "--abort"], capture_output=True, text=True)
        return {
            "merged": False, "conflict": True, "branch": branch,
            "pre_merge_checkpoint": pre_merge_checkpoint,
            "stdout": res.stdout[-2000:], "stderr": res.stderr[-2000:],
        }
    head = git(vault, "rev-parse", "HEAD").strip()
    return {"merged": True, "conflict": False, "branch": branch, "pre_merge_checkpoint": pre_merge_checkpoint, "head": head}


# ---------------------------------------------------------------------------
# Run log
# ---------------------------------------------------------------------------


def write_run_log(vault: Path, result: dict) -> Path:
    cache_dir = Path(vault) / "SYSTEM" / ".cache" / "gardener"
    cache_dir.mkdir(parents=True, exist_ok=True)
    out_path = cache_dir / "last-run.json"
    out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(vault: Path, mode: str, stage_arg: str, max_llm_calls: int) -> dict:
    result = {
        "started": iso_now(), "vault": str(vault), "mode": mode, "stage_arg": stage_arg,
        "max_llm_calls": max_llm_calls, "stages": [],
    }

    # (a) checkpoint any pending human edits already sitting in the live
    # vault before touching anything.
    result["pre_checkpoint"] = checkpoint(vault, "pre-gardener")

    # (b) isolate: all stage work + guardrail enforcement happens in a
    # separate worktree, never in the live vault.
    wt, branch, start_commit = setup_worktree(vault, mode)
    result["branch"] = branch
    result["worktree"] = str(wt)
    result["start_commit"] = start_commit

    budget = Budget(max_llm_calls)
    stages_to_run = STAGE_ORDER if stage_arg == "all" else [stage_arg]
    dispatch = {
        "regen": lambda: do_regen(wt),
        "compile": lambda: do_compile(wt, budget),
        "lint": lambda: do_lint(wt, budget),
        "inbox": lambda: do_inbox(wt, budget),
        "actions": lambda: do_actions(wt),
        "digest": lambda: do_digest(wt, result, display_vault=vault),
    }
    for stage in stages_to_run:
        result["stages"].append(dispatch[stage]())
    result["llm_calls"] = budget.used

    # (c) bring results into the live vault (apply mode only).
    if mode == "apply":
        merge_result = merge_back(vault, branch)
        result["merge"] = merge_result
    else:
        merge_result = None
        result["merge"] = {
            "merged": False, "conflict": False, "branch": branch,
            "note": "propose mode — not merged, branch left for review",
        }

    # Worktree must go away BEFORE deleting a merged branch — git refuses to
    # delete a branch that's still checked out in a linked worktree.
    teardown_worktree(vault, wt)
    if mode == "apply" and merge_result and merge_result["merged"]:
        subprocess.run(["git", "-C", str(vault), "branch", "-d", branch], capture_output=True, text=True)
    result["finished"] = iso_now()

    total_rejections = sum(len(s.get("rejections", [])) for s in result["stages"])
    summary = (
        f"gardener {mode} run on {branch}: {len(result['stages'])} stage(s), "
        f"{budget.used} LLM call(s), {total_rejections} guardrail rejection(s). "
    )
    if mode == "apply":
        if result["merge"]["merged"]:
            summary += f"merged into the live vault at {result['merge']['head'][:8]}."
        else:
            summary += "MERGE CONFLICT — proposal left on the branch for manual review."
    else:
        summary += "proposal left on the branch for manual review (not merged)."
    result["summary"] = summary
    notify(summary)

    write_run_log(vault, result)
    return result


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="gardener", description=__doc__)
    parser.add_argument("--mode", choices=["propose", "apply"], default="apply")
    parser.add_argument("--stage", choices=["all"] + STAGE_ORDER, default="all")
    parser.add_argument(
        "--max-llm-calls", type=int,
        default=int(os.environ.get("GARDENER_MAX_LLM_CALLS", DEFAULT_MAX_LLM_CALLS)),
    )
    return parser.parse_args(argv)


def resolve_vault() -> Optional[Path]:
    """$VAULT, else the vault this add-on is installed in (SYSTEM/optional/gardener
    -> three levels up) when that looks like a vault. No other default."""
    env = os.environ.get("VAULT")
    if env:
        return Path(env).expanduser().resolve()
    candidate = Path(__file__).resolve().parents[3]
    if (candidate / "SYSTEM" / "SCHEMA.md").exists():
        return candidate
    return None


def main(argv=None) -> int:
    args = parse_args(argv)
    vault = resolve_vault()
    if vault is None:
        print("gardener: VAULT is not set and this add-on is not inside a vault checkout — refusing to run", file=sys.stderr)
        return 2
    if not (vault / ".git").exists():
        print(f"gardener: {vault} is not a git repo (no .git) — refusing to run", file=sys.stderr)
        return 2
    with repo_lock(vault):
        result = run(vault, args.mode, args.stage, args.max_llm_calls)
    print(json.dumps({
        "mode": result["mode"], "stages": [s["name"] for s in result["stages"]],
        "llm_calls": result.get("llm_calls", 0),
        "rejections": sum(len(s.get("rejections", [])) for s in result["stages"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
