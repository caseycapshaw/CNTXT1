# SYSTEM/optional — opt-in add-ons

The core method (raw → compile → index → log, see `SYSTEM/SCHEMA.md`) needs none of
this. Each add-on below is independent unless noted; `setup.md` (Phase 5 / 5b) offers
them one at a time.

| Add-on | Runs on | What it is |
| :-- | :-- | :-- |
| [`automation/`](automation/README.md) | your Mac (+ Claude Code) | session-start loader, daily plan/summary, calendar cache, close-ritual hook (launchd) |
| [`core-jobs/`](core-jobs/README.md) | always-on Linux host | systemd timers + `jobwrap` (lock, timeout, dead-man's-switch, alerts), git checkpoints, backups, `LoadCredential` secrets |
| [`gardener/`](gardener/README.md) | always-on Linux host (or any machine) | nightly unattended KB maintainer in an isolated worktree; hard guardrails; propose-mode first |
| [`remote-access/`](remote-access/README.md) | always-on Linux host + Cloudflare | `capture-api` (phone → `raw/`) and `mcp-remote` (claude.ai connector), both via Cloudflare Tunnel + Access, fail-closed |

Conventions shared by the Linux add-ons: templates carry `{{TOKENS}}` rendered at
install time; host config is `/etc/cntxt1/core.env`; secrets are systemd credentials
in `/etc/credstore` (never the environment, never the vault); every scheduled job runs
under `jobwrap`.
