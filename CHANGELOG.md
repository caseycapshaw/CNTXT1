# CHANGELOG

Notable framework changes to the CNTXT1 starter kit. Newest first. (Your instance's
own history lives in its `SYSTEM/log.md`.)

## 2026-09-28 — optional cloud-core add-ons

New opt-in tree under `SYSTEM/optional/` (index: `SYSTEM/optional/README.md`); nothing
in the core method depends on it.

- **`core-jobs/`** — always-on Linux host running scheduled jobs: `jobwrap`
  (single-instance lock, healthchecks.io dead-man's-switch ping, hard timeout,
  ntfy on failure), `git-checkpoint` (opt-in push), `nightly-rollup`, restic
  `backup` to any S3-compatible store, shared `lib/env.{sh,py}` (required
  `VAULT`, `secret_load`), rendered systemd units + `install.sh`, `set-secret`
  (systemd `LoadCredential` / `/etc/credstore`), Makefile. Tests run in CI.

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
