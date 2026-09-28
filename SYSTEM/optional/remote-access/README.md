# remote-access — capture from your phone, read from claude.ai (optional)

Two small services that run on the always-on cloud core (see
[`../cloud-core/README.md`](../cloud-core/README.md)) and expose exactly two doors
into your vault, both through a **Cloudflare Tunnel** so the host needs **no open
inbound ports**:

| Service | Door | Who uses it | Edge auth | App-level auth |
| :-- | :-- | :-- | :-- | :-- |
| [`capture-api/`](capture-api/README.md) | `POST https://capture.<domain>/capture` writes a new note to `raw/` | an iOS Shortcut (share sheet / dictation), scripts | Cloudflare Access **service token** | re-verifies the Access JWT (RS256, `iss`, `aud`); or a static bearer token for LAN/VPN clients |
| [`mcp-remote/`](mcp-remote/README.md) | `https://mcp.<domain>/mcp` — the KB's five MCP tools (`kb_index`, `kb_read`, `kb_search`, `kb_actions`, `kb_capture`) as a claude.ai custom connector | claude.ai (web/mobile) | Cloudflare Access on **`/authorize` only** (email OTP) | its own embedded single-user OAuth 2.1 server (DCR + PKCE, rotating refresh tokens) |

Both bind `127.0.0.1` only, verify Cloudflare's JWT themselves (defence in depth: a
misconfigured edge policy still can't reach the vault), keep an audit log with no
secrets or bodies, and **fail closed** — no default vault, no default allowed email;
they refuse to start unconfigured.

> **Why the connector runs its own OAuth server.** Cloudflare Access has a "Managed
> OAuth" mode that would make an MCP server's auth entirely edge-side. claude.ai's
> custom-connector OAuth flow has a **known bug with it** (as of this writing), so the
> working pattern is: a tiny embedded OAuth authorization server in `mcp-remote`, with
> Cloudflare Access protecting only the `/authorize` step (that is where the human
> logs in) and everything else (`/mcp`, `/token`, `/register`, `/.well-known/*`)
> reachable without an Access login, protected by the server's own bearer tokens.
> If Cloudflare/Anthropic fix the interaction you can simplify later.

## Prerequisites

- The cloud core from `../core-jobs/` (users, `core.env`, `set-secret`, systemd
  rendering) — or any Linux host with systemd 250+.
- A domain on Cloudflare (free plan is enough) and Cloudflare Zero Trust enabled
  (free for small teams). Pick a Zero Trust **team name** — that is your `CF_TEAM`.
- The vault checked out on the host, and `SYSTEM/bin/kb-mcp-server.py` personalized
  (`{{NAME}}`, `{{SCOPE}}` in its `INSTRUCTIONS`, see `setup.md`).

## 1. Install the tunnel (outbound-only)

1. Zero Trust dashboard → Networks → Tunnels → **Create a tunnel** (Cloudflared).
2. Install `cloudflared` on the host from Cloudflare's apt repo and run the
   `cloudflared service install <token>` command the dashboard shows. **That token is
   a secret** — paste it only into the host's terminal; never into chat, the vault, or
   a unit file.
3. Add two **public hostnames** on the tunnel:
   - `capture.<domain>` → `http://127.0.0.1:8710`
   - `mcp.<domain>` → `http://127.0.0.1:8711`

## 2. Access application for capture (service token)

1. Zero Trust → Access → **Service Auth → Create Service Token**. Cloudflare shows a
   Client ID and Client Secret **once** — store them in a password manager; they go into
   the iOS Shortcut headers.
2. Access → Applications → Add → **Self-hosted**, domain `capture.<domain>`.
   Policy: action **Service Auth**, include that service token.
3. Copy the application's **Audience (AUD) tag** → `CF_AUD_CAPTURE` in
   `/etc/cntxt1/core.env`; set `CF_TEAM` to your team name.

## 3. Access application for the MCP `/authorize` path (email OTP)

1. Access → Applications → Add → **Self-hosted**, domain **`mcp.<domain>/authorize`** —
   path-scoped. Do **not** protect the whole hostname: claude.ai cannot complete an
   interactive Access login on `/mcp` or `/token`.
2. Policy: Allow → Emails → **your** address → email one-time PIN.
3. Copy the AUD tag → `CF_AUD_AUTHORIZE`; set `ALLOWED_EMAIL` to the same address and
   `PUBLIC_BASE_URL=https://mcp.<domain>` (no trailing slash) in `core.env`.
   `ALLOWED_EMAIL` has **no default** and the service will not start without it.

## 4. Host side

```bash
cd <vault>/SYSTEM/optional/remote-access
./setup-venvs.sh                                   # as the service user
sudo ../core-jobs/set-secret capture-token         # bearer for LAN/VPN clients (long random string)
sudo ../core-jobs/set-secret mcp-client-id         # static OAuth client (optional alternative to DCR)
sudo ../core-jobs/set-secret mcp-client-secret
$EDITOR /etc/cntxt1/core.env                       # CF_TEAM, CF_AUD_*, PUBLIC_BASE_URL, ALLOWED_EMAIL
sudo ../core-jobs/install.sh --user <job-user> --vault <vault-path> --addons core-jobs,remote-access
# uncomment the units you want in systemd/ENABLED, re-run install.sh (or):
sudo systemctl enable --now cntxt1-capture.service cntxt1-mcp.service
```

Smoke test from the host: `curl -s 127.0.0.1:8710/healthz`; from the internet the
capture endpoint must answer **403 from Cloudflare** without the service-token headers.

## 5. Use it

- **iOS Shortcuts** (share sheet + dictation): build guide in
  [`capture-api/SHORTCUT.md`](capture-api/SHORTCUT.md).
- **claude.ai connector**: Settings → Connectors → Add custom connector →
  `https://mcp.<domain>/mcp`. Let it try Dynamic Client Registration; otherwise paste the
  static client id/secret under Advanced. Approving opens `/authorize` behind Access
  (email OTP), then the server's own consent page. Full flow:
  [`mcp-remote/README.md`](mcp-remote/README.md).

## Operating it

- **Kill switch, fast**: `touch ~/.local/state/cntxt1/mcp-disabled` makes every MCP route
  return 503 without a restart; `make -C ../core-jobs kill-switch` stops both services
  and `cloudflared`.
- **Audit logs**: `/var/log/cntxt1/{capture-api,mcp-remote}-audit.jsonl` — one JSON line
  per request (`ts, service, client, route, status`), never bodies or tokens.
- **Rotate**: service token in the Zero Trust dashboard (+ update the Shortcut);
  `set-secret` new values and `systemctl restart`. Suspected leak of the tunnel token →
  roll it in the dashboard and re-run `cloudflared service install`.
- **Secrets hygiene**: see `SYSTEM/SCHEMA.md` (§ Secret hygiene).

## Privacy note

`mcp-remote` gives claude.ai read access to the whole vault (the tools honor no per-note
privacy). Only enable it if that is what you want, keep `ALLOWED_EMAIL` to yourself, and
remember the Anthropic-side connector retains whatever the conversation reads.

## Tests

Need the `cryptography` package; each test module **skips with a message** if it is
missing.

```bash
pip install cryptography            # or: uv run --no-project --with cryptography ...
(cd capture-api && python3 -m unittest discover -s tests -p 'test_*.py')
(cd mcp-remote  && python3 -m unittest discover -s tests -p 'test_*.py')
```
