# core-jobs — the "cloud core" job runner (optional)

An opt-in add-on. Nothing in the KB method depends on it. It gives your vault an
**always-on Linux host that runs the scheduled jobs and is the sole git writer**,
so your laptop can sleep, travel, or die without the KB going quiet.

Part of the cloud-core architecture — read [`../cloud-core/README.md`](../cloud-core/README.md)
for how this add-on fits with the gardener, remote access and the VM bootstrap.

## What "cloud core" means

- **One always-on host** (a small Ubuntu LTS VM) holds the canonical checkout of
  the vault. Scheduled jobs run there under **systemd timers**.
- **The core is the sole git writer** for unattended commits: `git-checkpoint`
  makes a safety-net commit every 15 minutes. Edge machines (your laptop, phone)
  sync content in and out, but unattended automation never races them for
  commits.
- **Dead-man's-switch monitoring.** Every job runs through `bin/jobwrap`, which
  pings a [healthchecks.io](https://healthchecks.io)-style URL at start and end.
  If a job *doesn't run at all* (host down, timer broken) the check goes late and
  *the service* alerts you — silence is detected, not just failure. On a nonzero
  exit, `jobwrap` also posts a secret-free "job failed" line to an
  [ntfy](https://ntfy.sh) topic.
- **Hard limits.** `jobwrap --timeout` kills the whole process group (SIGTERM,
  then SIGKILL after 10 s; exit 124), a non-blocking `flock` makes overlapping
  runs a no-op, and each unit sets `TimeoutStartSec`, `MemoryMax` and `Nice`.
  A runaway `claude -p` cannot wedge the host.
- **Credentials via systemd `LoadCredential`.** Secrets live in `/etc/credstore`
  (root, 0600), are handed to exactly the unit that declares them, and appear to
  the job as files under `$CREDENTIALS_DIRECTORY`. No secret in the environment
  file, in `ps`, or in the unit.

> **Lesson learned — a laptop or desktop is not an unattended server.** A machine
> with full-disk encryption and a pre-boot unlock prompt (FileVault, LUKS, a
> BitLocker PIN, ...) stops at that prompt after *any* reboot — a power blip, an
> OS update — and no job runs until a human types a passphrase. Don't fight it;
> run the core on a cloud VM (or a machine whose disk unlock is genuinely
> unattended and physically secured) and keep the encrypted personal machines as
> edges.

## What's here

| Path | Purpose |
| :-- | :-- |
| `bin/jobwrap` | lock + healthchecks ping + hard timeout + ntfy-on-failure wrapper. Stdlib-only Python 3.9+, works on Linux and macOS. |
| `bin/git-checkpoint` | safety-net vault commit; push is **opt-in** (`CHECKPOINT_PUSH=1`) and only to a private `origin`. |
| `bin/nightly-rollup` | upstream-kit update check (uses `SYSTEM/bin/sync-from-upstream.sh --reconcile`) + `SYSTEM/bin/rollup-daily-weeks.sh`. Deterministic, no LLM. |
| `bin/backup` | `restic` to any S3-compatible store (AWS S3, Cloudflare R2, Backblaze B2, MinIO ...). Daily backup, weekly prune, monthly integrity check. |
| `lib/env.sh`, `lib/env.py` | shared environment for job scripts: `VAULT` (required, no default), `/etc/cntxt1/core.env` overlay, `secret_load`/`secret()` credential loaders, `run_with_timeout`, `claude_p`, `notify`, GNU/BSD portability shims. Source or import — never copy. |
| `systemd/` | unit + timer templates (`{{USER}}`, `{{TZ}}`, `{{OPTIONAL_DIR}}` ...) and the `ENABLED` list. |
| `install.sh` | renders the templates and enables the timers (idempotent). |
| `set-secret` | writes one credential into `/etc/credstore` without touching argv/history. |
| `core.env.example` | the non-secret host config (`/etc/cntxt1/core.env`). |
| `Makefile` | `deploy`, `render`, `status`, `test`, `kill-switch`. |

## Setup

Assumes an Ubuntu LTS host (or run [`../cloud-core/vm-bootstrap.sh`](../cloud-core/vm-bootstrap.sh)
first — it does users, firewall, swap, credstore and the git checkouts).

1. **Put the vault on the host** as the unprivileged job user, e.g.
   `git clone <your-private-vault-remote> ~/vault`. This add-on runs from the
   kit's `SYSTEM/optional/` inside that checkout (or a copy of it in a separate
   services repo — `install.sh` renders paths from wherever it lives).
2. **Create the monitoring endpoints.** In healthchecks.io make a project and
   copy its ping base URL (`https://hc-ping.com/<project-ping-key>`); jobwrap
   auto-creates one check per job (`?create=1`). Pick an unguessable ntfy topic
   and subscribe your phone.
3. **Render + install** (as root):
   ```bash
   cd <vault>/SYSTEM/optional/core-jobs
   sudo ./install.sh --user <job-user> --vault <vault-path> --tz <Area/City>
   # or: sudo make deploy USER_NAME=<job-user> VAULT_PATH=<vault-path> TZ_NAME=<Area/City>
   ```
   Use `make render` first to inspect the units without touching `/etc`.
4. **Edit `/etc/cntxt1/core.env`**: set `HC_PING_BASE`, `NTFY_URL`, and (if you
   use `backup`) `RESTIC_REPOSITORY`. Set `CHECKPOINT_PUSH=1` only if `origin` is
   a **private** remote.
5. **Store credentials** (values are prompted for, never on the command line):
   ```bash
   sudo ./set-secret restic-password        # backup — also keep a copy OFF this host
   sudo ./set-secret backup-key-id
   sudo ./set-secret backup-secret-key
   sudo ./set-secret claude-oauth-token     # only for jobs that run `claude -p`
   ```
6. **Verify**: `make status`, then run a job by hand:
   `sudo systemctl start cntxt1-git-checkpoint.service && journalctl -u cntxt1-git-checkpoint -n 20`.
   Kill a timer for a day (or just pause the check in healthchecks.io) to watch the
   dead-man alert fire once — an untested alarm is not an alarm.

`make kill-switch` stops every `cntxt1-*` timer and the internet-facing services.

## Adding your own job

Write the script against `lib/env.sh`, copy `systemd/cntxt1-git-checkpoint.service` +
`.timer` to a new name, change the `ExecStart` (keep it wrapped in `jobwrap <name> --timeout N --`),
add the credential names you need as `LoadCredential=<name>`, and list the timer in
`ENABLED`. Keep `MemoryMax`/`TimeoutStartSec` — they are the seatbelts.

## Secrets hygiene

Credentials never go in the vault, in `core.env`, in unit files, or on a command
line. `jobwrap` scrubs Bearer tokens, JWTs and long hex/base64 runs from the tail it
sends to healthchecks, but that is a backstop, not a licence to print secrets. The
rules are in `SYSTEM/SCHEMA.md` (§ Secret hygiene) — follow those.

## Tests

```bash
make test            # or, individually:
python3 -m unittest discover -s bin/tests
python3 -m unittest discover -s lib/tests -p 'test_*.py'
bash lib/tests/test-env.sh
```
