# CHANGELOG

Notable framework changes to the CNTXT1 starter kit. Newest first. (Your instance's
own history lives in its `SYSTEM/log.md`.)

## 2026-11-13 — secret-bearing CI on main only

- The maintainer identifier sweep moves out of the PR gate into its own workflow,
  `.github/workflows/identifier-sweep.yml`, which runs `.github/scripts/identifier-sweep.sh`
  (grep/sed only) on push to `main` and on dispatch, never on a pull request. It fails
  closed (unset, empty or invalid pattern, no grep with `-P`, or a grep error), skips
  only the root's `.git`, `.github`, `.venv`, `LICENSE` and `uv.lock`, and in Actions
  prints only the number of matching files. `pr-gate.sh` calls the same script for
  local runs (GNU `grep`, or `ggrep` on macOS).
- The `gate` job self-tests the sweep with synthetic patterns on every pull request
  (`.github/scripts/identifier-sweep-selftest.sh`).
- The Claude review workflow is removed. Its prompt is now the *Review checklist* in
  `.github/CONTRIBUTING.md`; the sync skill has a fresh subagent apply it to the staged
  diff before anything is pushed.
- New `.github/CODEOWNERS` (`/.github/`, `/.gitattributes`); Dependabot version updates go monthly.
- The repo settings this assumes (environment limited to `main`, code-owner review on
  `main`, pinned bypass merges) are in `.github/CONTRIBUTING.md` § For maintainers.

## 2026-11-04 — one log writer, applied to the kit's own jobs

- `core-jobs/bin/nightly-rollup`, `automation/daily-plan.sh`, `automation/daily-summary.sh`
  and `remote-access/capture-api` now log through `SYSTEM/bin/log-line` (direct append
  only for vaults older than it). capture-api has a test for the sidecar path.
- `core-jobs/bin/git-checkpoint` and `daily-summary.sh` run `fold_log.py` before they
  commit; off the writer host it refuses and the commit goes ahead.
- `daily-summary.sh` reads today's lines from `log.md` plus unfolded sidecars.

## 2026-11-03 — one log writer

For vaults replicated across machines by a file-sync tool: concurrent appends to
`SYSTEM/log.md` from two hosts become conflict copies that silently drop lines.

- **`SYSTEM/bin/log-line`** — the one way to log. Appends to `SYSTEM/log.md` on the
  writer host named in the new optional `SYSTEM/writer-host.conf` (`host=`); anywhere
  else to a per-host sidecar `SYSTEM/log.d/<YYYY-MM>.<host>.md`. No conf = single-machine
  vault, unchanged behaviour (every host writes `log.md`).
- **`SYSTEM/bin/fold_log.py`** — writer host only: folds sidecar lines into `log.md`
  (content-matched, idempotent, never edits a sidecar, retires archived past-month
  sidecars). Call it from your writer host's commit job.
- **Lint check 19** — FAILs on any `*.sync-conflict-*` copy in the vault.
- Tests in `SYSTEM/bin/tests/test_log_line.py`, now run in the PR gate. SCHEMA § One log
  writer; compile step 4 and the AGENTS log convention point at `log-line`.

## 2026-09-28 — optional cloud-core add-ons

New opt-in tree under `SYSTEM/optional/` (index: `SYSTEM/optional/README.md`); nothing
in the core method depends on it.

- **`core-jobs/`** — always-on Linux host running scheduled jobs: `jobwrap`
  (single-instance lock, healthchecks.io dead-man's-switch ping, hard timeout,
  ntfy on failure), `git-checkpoint` (opt-in push), `nightly-rollup`, restic
  `backup` to any S3-compatible store, shared `lib/env.{sh,py}` (required
  `VAULT`, `secret_load`), rendered systemd units + `install.sh`, `set-secret`
  (systemd `LoadCredential` / `/etc/credstore`), Makefile. Tests run in CI.
- **`gardener/`** — nightly autonomous maintainer: isolated worktree + checkpoint +
  merge-back, drives the kit's own `regen-all.sh` / `lint.sh`, `claude -p` compile of
  orphan `raw/` captures (30-min settle), inbox filing, capped action date-stamping,
  daily-note digest. Guardrails in code: `raw/` append-only (+ `raw/index.md`), `> [!human]`,
  decisions ledger, journals, AGENTS/SCHEMA/`.claude`/`.obsidian`, no deletions, checked-off
  actions. Ships in propose-mode. Tests (fake `claude`) run in CI.
- **`remote-access/`** — `capture-api` (iOS Shortcut / script → `raw/`, Cloudflare Access service
  token + JWT re-verification) and `mcp-remote` (the kit's `kb-mcp-server.py` over Streamable
  HTTP with an embedded single-user OAuth server, Access on `/authorize` only; fails closed —
  no default `ALLOWED_EMAIL` or vault). Tunnel + Access setup docs, iOS Shortcut build guide,
  systemd units. Tests need `cryptography` (skip with a message otherwise; CI installs it).
- **`cloud-core/`** — the "cloud core, home edge" architecture README tying the add-ons together
  (design rules, the full-disk-encryption lesson, SSH-behind-a-private-network guidance) and
  `vm-bootstrap.sh`: idempotent Ubuntu LTS bootstrap (required `--user` / `--vault-repo` /
  `--services-repo`, codename-agnostic apt repos, `ufw` deny-inbound + optional `--allow-rule`,
  unattended upgrades, swap, journald cap, `/etc/credstore`, optional `--path-parity-link`).

## 2026-09-28 — numbered GTD layout

**Breaking (layout).** The kit adopts a numbered GTD folder layout; `Knowledge/` is
gone. Existing users: see [`MIGRATING.md`](MIGRATING.md) and the helper
`SYSTEM/bin/migrate-to-numbered-layout.sh`.

- New folders `00 daily/`, `01 Horizons/` (Goals · vision · purpose & principles),
  `02 Areas/` (+ `Assets/`), `03 Projects/`, `04 People/`, `05 concepts/`; `raw/`,
  `Skills/`, `Agents/`, `excalidraw/`, `Actions.md` move to the root. Folder names
  single-source in `SYSTEM/bin/kb-folders.json`.
- **Initiative → Project** (`type: project`, `status: pending|active|paused|done`,
  required `area:` up-link). New templates: Area, Goal; People template gains
  `relation:` and a `type: org` variant.
- SCHEMA gains the GTD conventions: Projects/Areas/Horizons, the endpoint test,
  up-links only, relations frontmatter (`owner:` / `serviced-by:` / `relation:`),
  orientation caps + trails for projects and areas, attachments-by-ownership.
- Pydantic models for Project/Area/Goal/Horizon/Org; `.gitignore` rewritten with
  per-folder negation patterns; `pr-gate.sh` (`check_only`) updated to match.
- Scripts renamed: `*-initiatives.sh` → `active-projects.sh`, `stale-projects.sh`,
  `audit-project-next-actions.sh`; new `audit-area-reviews.sh`.

- **Boot bundle**: `SYSTEM/bin/build_boot_bundle.sh` — one generated orientation payload
  emitted by the SessionStart hook (with the old inline loader kept as a fallback);
  agents no longer re-read `index.md` at session start. New skills `file-a-new-note`
  and `review-an-area`; `initiative-worker` role → `project-worker`.

Earlier 2026-09-28 changes (rules, skills, layout-independent scripts) are listed in
`SYSTEM/log.md`.
