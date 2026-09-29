# gardener — autonomous KB gardener

Optional add-on: an unattended nightly maintainer for a CNTXT1 vault. It runs the
generators, fixes what lint can fix mechanically, compiles unambiguous `raw/`
captures, files root-inbox strays, stamps action dates, and writes one digest
to the day's `00 daily/` note — all inside an isolated git worktree, behind
hard guardrails. This README documents the *job*; the KB's own conventions are in
`SYSTEM/SCHEMA.md` (§ Health checks — "the gardener").

**Start in propose-mode** (`--mode propose`, the shipped systemd default) and
review the `gardener/proposal-<date>` branch for a couple of weeks before you flip
the unit to `--mode apply`. Nothing in the core method depends on this add-on.

Runs on the cloud core via `core-jobs/bin/jobwrap gardener --timeout 2400 -- gardener/run.sh --mode propose`
(unit: `gardener/systemd/cntxt1-gardener.service`, rendered by
`core-jobs/install.sh --addons core-jobs,gardener`) and is testable directly on
macOS. See `../cloud-core/README.md` for the architecture.

## Isolation (read this first)

The live `$VAULT` folder is shared with a sync tool (Syncthing, Obsidian
Sync, ...) and an editor on another machine — a human edit can land there **uncommitted, at any moment**,
including while gardener is mid-run. Gardener therefore never does stage
work, guardrail reverts, or a `git checkout --`/`reset` directly in the live
vault. Every run instead:

1. **checkpoints** the live vault — `git add -A && git commit` whatever's
   currently dirty there, attributed to the human (`checkpoint()`,
   `--author` = the vault's own `git config user.name/user.email` by default,
   `GARDENER_CHECKPOINT_AUTHOR` to override) — a no-op if the tree is clean.
   That's their in-progress edit being preserved, not gardener's own work.
2. **isolates** — adds a `git worktree` (`setup_worktree()`) at that
   checkpoint commit, in `$GARDENER_WT`
   (default `~/.local/state/cntxt1/gardener-wt`, deliberately **outside**
   the synced folder), on its own branch (`gardener/run-<timestamp>` for
   apply, `gardener/proposal-<date>` for propose — reused same-day). Every
   stage, including all guardrail enforcement, runs entirely inside that
   worktree; a stage's guardrail check only ever sees the diff the stage
   itself produced there.
3. **merges back** (`merge_back()`, apply mode only) — in the live vault:
   checkpoints again (catches any human edit that arrived *during* the run),
   then `git merge --no-edit <gardener branch>`. A real conflict runs
   `git merge --abort` (the one sanctioned recovery path — never a manual
   file-level checkout/reset) and leaves the gardener branch in place for
   review; the run still exits 0 and ntfy's a conflict notice. Propose mode
   skips this step — the branch is left for a human to review/merge by hand.
4. **tears down** the worktree (`teardown_worktree()`) either way, and — on
   a successful apply-mode merge only — deletes the now-merged transient
   branch (worktree removal has to happen first; git refuses to delete a
   branch that's still checked out in a linked worktree).

This means: the live vault's own checked-out branch is **never** switched by
gardener (worktree add/remove doesn't touch the main checkout), and a human
edit — before, during, or between runs — is always captured by a checkpoint
commit before anything gardener does could possibly interact with it.

## What it does (inside the isolated worktree)

One fixed pipeline, each stage at most one commit
(`gardener(<stage>): <message>`, skipped if the stage produced no diff):

1. **regen** — runs the vault's own `SYSTEM/bin/regen-all.sh` (every generator the
   kit ships, in dependency order — the gardener does not hardcode the list, so a
   new generator is picked up automatically). Deterministic, no LLM. Skipped with a
   note if `uv` isn't installed (regen-all shells out to `uv run`).
2. **compile** — finds `raw/YYYY-MM-DD-*.md` captures with no inbound
   wikilink from any compiled note (the same orphan-raw rule as `lint.sh`
   check 16), and for up to 6 of them per run invokes headless
   `claude -p` (`--permission-mode acceptEdits`, a narrow `--allowedTools`
   list, `--append-system-prompt` carrying the gardener rules below) with a
   300s hard timeout per call, asking it to compile that one capture per
   `.claude/agents/compile.md`.
3. **lint** — runs `SYSTEM/bin/lint.sh`; stale-generated-view findings (WARN, or
   FAIL under `LINT_STRICT=1`) are fixed by re-running `regen-all.sh`
   deterministically; every other FAIL gets a
   narrow `claude -p` call per finding, capped at 3 per run. Re-runs lint and
   records the before/after FAIL count.
4. **inbox** — root files outside the lint check-1 allow-list each get a
   `claude -p` call to file them per `.claude/skills/file-a-new-note/SKILL.md`
   (capped at 3 per run).
5. **actions** — deterministic Python: every open `- [ ] … #action` line
   missing a `➕ YYYY-MM-DD` created-date stamp gets one, derived from
   `git log -S` on that exact line text (same convention as
   `SYSTEM/bin/backfill-action-dates.sh`). Capped at **50 stamps per run**
   (`ACTIONS_MAX_STAMPS_PER_RUN`), **oldest-created-date first** — a two-pass
   discover-then-sort-then-cap, so an initial backlog of hundreds gets worked
   down over several reviewable runs instead of dumping one giant diff. No
   LLM call.
6. **digest** — writes a `## Gardener` block into today's
   `00 daily/YYYY-MM-DD.md`, inside `<!-- gardener:auto:start/end -->`
   markers (idempotent replace, never touches anything outside the block —
   including a `> [!human]` section above it), listing what each stage did
   plus a `git -C "$VAULT" revert <sha>` line per stage commit (referencing
   the live vault path — the shas are the same post-merge). The run's
   overall summary — including the merge/conflict outcome, decided *after*
   this stage — is POSTed to `$NTFY_URL` separately, once, at the very end
   of the run.

## Guardrails (enforced in code, not just prompted)

After **every** stage (LLM-driven or not, always inside the worktree),
`enforce_guardrails()` walks
`git status --porcelain=v1 --find-renames --untracked-files=all` and hard-
rejects — reverting the file (`git checkout --` for tracked paths, delete
for untracked ones — **inside the worktree only**) and recording the
rejection — any change that:

- creates a new file under `raw/`, or edits the content of an existing one
  (append-only, gardener-read-only) — **except** the exact paths in
  `RAW_GENERATED_ALLOWLIST` (currently just `raw/index.md`, the folder index
  `build_directory_indexes.py` regenerates — nothing else under `raw/` is
  exempt, and the allow-listed path is still subject to every *other* rule
  below: it can't be deleted, etc.);
- touches `SYSTEM/decisions.md`, `SYSTEM/Journal.md`, `Agents/life-coach/journal-log.md`,
  `AGENTS.md`, `CLAUDE.md`, `SYSTEM/SCHEMA.md`, or anything under
  `.claude/` or `.obsidian/`;
- alters or removes text inside a `> [!human]` callout block (every old
  block must still appear verbatim in the new file);
- deletes any tracked file;
- changes the text of an already-checked-off `- [x] …` action line.

A `git mv` (used by the inbox stage to relocate a root item into `raw/`, or
by the lint stage's cap-overflow fix moving text into a trail file) is
recognized as a rename (`--find-renames`), not a delete+new-file pair, so it
is never itself flagged — only the resulting content is checked against the
rules above.

One structural gotcha this code specifically handles: every content folder
in the numbered layout has a space in its name (`05 concepts`, `03 Projects`,
`00 daily`, …), and `git status --porcelain` **quotes** any path containing
one (`"05 concepts/foo.md"`) — `_unquote_git_path()` strips that quoting
before any path comparison, or every guardrail silently no-ops.

Budgets: a global max LLM calls per run (`--max-llm-calls`, default 12,
`GARDENER_MAX_LLM_CALLS` env override) shared across the compile/lint/inbox
stages, plus a per-stage cap (compile 6, lint 3, inbox 3) so one stage can't
eat the whole run's budget. A run stops spending once the global budget is
exhausted; later stages (actions, digest) still run — they don't need LLM
calls.

Concurrency: a non-blocking `fcntl.flock` on `$VAULT/.git/gardener.lock` — a
second concurrent invocation exits immediately rather than racing the first.

Every run writes a structured log to
`$VAULT/SYSTEM/.cache/gardener/last-run.json` (checkpoints, worktree/branch,
stages, commits, guardrail rejections, LLM call counts, lint before/after,
merge outcome).

## Modes

- `--mode apply` (default): checkpoint -> isolated worktree -> stages ->
  checkpoint again -> `git merge --no-edit` the gardener branch into the
  live vault's current branch -> delete the merged branch. A conflict aborts
  the merge and leaves the branch for review instead.
- `--mode propose`: same checkpoint + isolated worktree + stages, but the
  merge step is skipped entirely — the branch (`gardener/proposal-<date>`,
  reused across same-day re-runs) is left for a human to review and merge by
  hand. The live vault's own branch/HEAD is untouched beyond the initial
  pending-edit checkpoint (if any).

## Reverting

Every stage's digest entry in the daily note includes its own
`git -C "$VAULT" revert <sha>` line. Revert stages independently (they're
separate commits) — reverting `regen` doesn't touch `actions`, etc. These
shas are valid once the gardener branch has landed in the live vault's
history (apply mode's merge, or a manual merge of a propose-mode branch).

## Running

```
VAULT=/path/to/vault gardener/run.sh --mode apply
VAULT=/path/to/vault gardener/run.sh --mode propose --stage lint
VAULT=/path/to/vault gardener/run.sh --mode apply --max-llm-calls 4
GARDENER_WT=/custom/worktree/path VAULT=/path/to/vault gardener/run.sh
```

Env: `VAULT` (default: the vault this add-on is installed inside, else required),
`GARDENER_WT` (default `$HOME/.local/state/cntxt1/gardener-wt` — must stay outside any
synced folder), `GARDENER_CHECKPOINT_AUTHOR` (default: the vault's git identity),
`NTFY_URL` (optional run summary), `CREDENTIALS_DIRECTORY/claude-oauth-token` else
`CLAUDE_CODE_OAUTH_TOKEN` for the headless `claude -p` calls, `GARDENER_CLAUDE_CMD` to
point at a fake `claude` for testing, `GARDENER_MIN_RAW_AGE_MIN` (raw settle time, default 30).

## Tests

```
cd gardener && python3 -m unittest discover -s tests -p "test_*.py" -v
```

Uses a throwaway git-repo vault fixture (`tests/vaultfixture.py`) — never
touches a real vault; each isolation test also points `GARDENER_WT` at its
own throwaway directory so parallel test runs can't collide. The `claude`
CLI is mocked via `GARDENER_CLAUDE_CMD=tests/fake_claude.py` (reads
`FAKE_CLAUDE_ACTION` from the environment: `noop` / `write_file` /
`touch_raw` — the last one specifically simulates a guardrail-violating LLM
response so the rejection path itself gets exercised, not just the happy
path). `tests/test_propose_mode.py` covers the isolation redesign
specifically: the live vault's branch never changes, checkpoint attribution,
a human edit arriving *mid-run* (between worktree setup and merge-back)
surviving the merge untouched, and a genuine merge conflict aborting cleanly
(no conflict markers left in the live vault, the human's own edit preserved,
the gardener branch left intact for review).

## Known limits

- This code assumes `git`, `python3`, and (for most of `regen`/`lint`)
  `uv` are on `PATH`; a missing `uv` degrades gracefully (those generators
  skip with a note) rather than failing the run.
- `claude` itself must be on `PATH` and authenticated via
  `CLAUDE_CODE_OAUTH_TOKEN` (or the `CREDENTIALS_DIRECTORY` credential) —
  the systemd unit (`LoadCredential=claude-oauth-token`) wires that up, not this script.
- The digest stage only reports on stages that ran *in the same invocation*
  (`--stage all` gives the full picture; `--stage digest` alone reports "no
  stage data for this run"), and it's written *before* the merge step runs
  (merge happens after all worktree stages finish) — so the digest itself
  never states the merge/conflict outcome; that only goes to the final
  `notify()` call and `last-run.json`.
- `$GARDENER_WT` is reused across runs and forcibly cleared
  (`git worktree remove --force` + `rm -rf` fallback + `git worktree prune`)
  at both the start of `setup_worktree()` (in case a prior run crashed
  mid-flight) and the end of every run — don't point it at anything with
  state worth keeping between runs.
