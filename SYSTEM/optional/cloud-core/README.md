# cloud core, home edge — the optional always-on architecture

Your KB works fine on one laptop. This tree is for when you want it to **keep
working while the laptop is closed**: nightly maintenance, backups, phone capture,
and a claude.ai connector that reaches the vault at 2 a.m. It splits your setup into
two roles.

```
                       ┌──────────────── cloud core (always-on Ubuntu LTS VM) ────────────────┐
  phone (iOS Shortcut) │  cloudflared ──► capture-api :8710 ──► raw/         (remote-access)  │
  claude.ai connector ─┼─►(outbound-only  mcp-remote  :8711 ──► kb_* tools   (remote-access)  │
   via Cloudflare      │   tunnel; no inbound ports)                                          │
   Tunnel + Access     │  systemd timers ► jobwrap ► git-checkpoint · nightly-rollup ·        │
                       │                            gardener · backup            (core-jobs,  │
                       │  vault checkout = the sole unattended git writer         gardener)   │
                       └───────┬──────────────────────────────────────┬───────────────────────┘
        healthchecks.io ◄──────┘ start/end pings (dead-man's-switch)  │ restic (encrypted)
        ntfy ◄── failure alerts                                        ▼ S3-compatible bucket
                                                        private git remote ◄──► home edge
                                                                                (laptop + Obsidian + Claude Code,
                                                                                 launchd automation, phone)
```

- **Cloud core** — a small VM. Runs the scheduled jobs, owns unattended git writes, exposes
  the two remote doors through an outbound-only tunnel, and is watched by a dead-man's switch.
  It has no GUI, no inbound ports, and nothing you edit by hand.
- **Home edge** — the machines you actually work on (laptop, phone). Interactive Claude Code
  sessions, Obsidian, and the macOS-only [`automation/`](../automation/README.md) live here.
  The edge and the core meet in **git** (a *private* remote you control) or in whatever file-sync
  tool you already use; only the core makes *unattended* commits, so automation never races you.

## The pieces, in build order

| # | Add-on | What it adds | Read |
| :-- | :-- | :-- | :-- |
| 1 | [`vm-bootstrap.sh`](vm-bootstrap.sh) (this folder) | hardened base: user, `ufw` deny-inbound, unattended upgrades, swap, journald cap, `/etc/credstore`, checkouts | below |
| 2 | [`core-jobs/`](../core-jobs/README.md) | `jobwrap` (lock + timeout + healthchecks + ntfy), 15-min `git-checkpoint`, `nightly-rollup`, restic `backup`, rendered systemd units, `set-secret` | its README |
| 3 | [`gardener/`](../gardener/README.md) | nightly autonomous maintainer in an isolated worktree, hard guardrails, **propose-mode first** | its README |
| 4 | [`remote-access/`](../remote-access/README.md) | `capture-api` (phone → `raw/`) and `mcp-remote` (claude.ai connector), Cloudflare Tunnel + Access, fail-closed | its README |

Each layer is optional and stands on the ones before it only where noted (the gardener and
remote-access units are rendered by `core-jobs/install.sh --addons core-jobs,gardener,remote-access`).

## Design rules (why it looks like this)

1. **One unattended writer.** Two machines auto-committing the same vault is how you get
   conflicts in your notes. The core owns unattended commits; edges commit deliberately.
2. **Silence is a failure.** Every job pings a healthchecks.io-style check on start and end;
   a job that never runs (host down, timer dead) goes *late* and the service alerts you.
   `jobwrap` adds an ntfy push on nonzero exit. Test the alarm once, on purpose.
3. **Hard limits everywhere.** `jobwrap --timeout` kills the process group, a lock makes
   overlap a no-op, units set `TimeoutStartSec` / `MemoryMax` / `Nice`. A hung `claude -p`
   can't wedge the host.
4. **Credentials are handed out, not left lying around.** `/etc/credstore` (root, 0600) +
   `LoadCredential=` gives each unit only its own secrets as files under
   `$CREDENTIALS_DIRECTORY`; nothing in the environment file, the vault, or `ps`.
   Hygiene rules: `SYSTEM/SCHEMA.md` (§ Secret hygiene).
5. **No inbound ports.** Jobs run locally; remote doors use an outbound tunnel; admin SSH sits
   behind a private network. `vm-bootstrap.sh` sets `ufw` to deny all inbound.
6. **Fail closed, start in propose-mode.** The remote services refuse to start without an
   explicit vault and allowed email; the gardener proposes on a branch before it ever applies.
7. **Personal content stays private.** The vault only ever goes to a *private* remote. The
   checkpoint push is opt-in (`CHECKPOINT_PUSH=1`).

> **Lesson learned — a laptop or desktop is not an unattended server.** If the machine has
> full-disk encryption with a pre-boot unlock (FileVault, LUKS, BitLocker PIN), any reboot —
> power blip, OS update — parks it at a passphrase prompt and every job stops until you type
> it. Use a cloud VM (or hardware with genuinely unattended, physically secured unlock) for the
> core, and keep your encrypted personal machines as edges.

## Network: SSH behind a private path, then close it

`vm-bootstrap.sh` leaves SSH open to the internet **temporarily** so you can't lock yourself
out. Then:

1. Put the host on a private network of your choice — a mesh VPN or zero-trust product
   (Tailscale, Twingate, WireGuard, Cloudflare WARP/Access for SSH, ...). Vendor setup is out of
   scope here and none is required by the kit.
2. From your edge, confirm you can SSH **over that path**.
3. Re-run `sudo ./vm-bootstrap.sh … --lock-ssh` (same flags) to remove the public SSH rule.
   If your VPN needs an inbound rule (some do, some are outbound-only), add it with
   `--allow-rule '<ufw rule>'`.

Keep the provider's web console/recovery access in mind: it is your way back in if you get the
private path wrong.

## Path parity (optional)

If your Mac vault lives at `/Users/you/vault` and notes or scripts contain that absolute path,
pass `--path-parity-link /Users` and give the core user the same name: `/Users` becomes a symlink
to `/home`, so the identical path resolves on both hosts. Skip it if you use `$VAULT`/relative
paths (recommended for new setups — the core-jobs scripts do).

## Bring-up checklist

```bash
# On the fresh Ubuntu LTS VM, as root:
sudo ./vm-bootstrap.sh --user <name> --vault-repo <private-vault-git-url> \
     --services-repo vault --tz <Area/City> --with-claude
# (--services-repo <url> if the add-ons live in their own private repo with the same layout as
#  SYSTEM/optional/; add --with-cloudflared for remote-access)

cd <vault>/SYSTEM/optional/core-jobs
sudo ./install.sh --user <name> --vault <vault-dir> --tz <Area/City> \
     --addons core-jobs            # add ,gardener ,remote-access when ready
sudoedit /etc/cntxt1/core.env      # HC_PING_BASE, NTFY_URL, RESTIC_REPOSITORY, ...
sudo ./set-secret restic-password  # + backup-key-id, backup-secret-key, claude-oauth-token
make status
```

Then: SSH behind your private network → `--lock-ssh`; gardener in propose-mode for a couple of
weeks → flip to apply; remote-access only if you want the phone/claude.ai doors.

## What it costs / what it needs

A 2 vCPU / 4–8 GB VM is plenty (jobs are bursty; the gardener's `claude -p` calls are the
heavy part and are capped). Ongoing: the VM, a healthchecks.io project (free tier is fine), an
S3-compatible bucket for backups, a Cloudflare account if you use remote-access, and your Claude
subscription for headless runs.

## Tests

```bash
bash tests/test-vm-bootstrap.sh    # argument validation only — never touches the system
```
The add-ons carry their own tests (`make -C ../core-jobs test`, gardener, remote-access).
