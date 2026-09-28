# capture-api

Stdlib Python HTTP service. `POST /capture` writes a new dated note into
your KB vault (`raw/YYYY-MM-DD-<slug>.md`), matching the format that
`SYSTEM/bin/kb-mcp-server.py`'s `kb_capture` tool and the existing `raw/`
notes already use. `GET /healthz` for liveness.

## Config (env vars)

| Var | Required | Example | Notes |
| :-- | :-- | :-- | :-- |
| `VAULT` | yes | `/home/<user>/vault` | Vault root. **No default** — the service refuses to start without it. Read fresh per request so tests can point elsewhere. |
| `CAPTURE_PORT` | no | `8710` | Bind port on 127.0.0.1. |
| `CF_TEAM` | for CF Access path | `myteam` | Your Cloudflare Access team subdomain (`<team>.cloudflareaccess.com`). |
| `CF_AUD_CAPTURE` | for CF Access path | `a1b2c3...` | AUD tag of the "KB capture" Access application (Access app → Overview → Application Audience (AUD) Tag). |
| `AUDIT_LOG_PATH` | no | — | Override audit log destination (tests use this). |
| `CAPTURE_TOKEN` | fallback only | — | Used only if `CREDENTIALS_DIRECTORY/capture-token` isn't present — for local/dev runs. |

## Credentials (systemd `LoadCredential`)

| Credential name | Purpose |
| :-- | :-- |
| `capture-token` | Static bearer token for LAN/VPN clients (scripts, home-network devices) that never cross the Cloudflare Tunnel. |

Systemd unit should set `LoadCredential=capture-token:/path/to/secret` and
`VAULT`, `CF_TEAM` and `CF_AUD_CAPTURE` from `/etc/cntxt1/core.env` (the shipped unit
already does this). The app reads `$CREDENTIALS_DIRECTORY/capture-token`
first, falling back to `$CAPTURE_TOKEN` only when `CREDENTIALS_DIRECTORY`
isn't set (local test runs).

## Auth (two independent layers)

1. **Cloudflare Access service token**, enforced at the edge (Access
   application policy — see below). Cloudflare then attaches a signed
   `Cf-Access-Jwt-Assertion` header to every request that passes.
2. **This service independently re-verifies that JWT**: RS256 signature
   against the account's JWKS (`https://<CF_TEAM>.cloudflareaccess.com/cdn-cgi/access/certs`),
   plus `iss` and `aud` (`CF_AUD_CAPTURE`). A request that somehow reaches
   this process without a valid JWT (edge misconfigured, tunnel bypassed)
   is rejected here too — defense in depth.
3. **OR**, for LAN/VPN clients that never cross the tunnel:
   `Authorization: Bearer <capture-token>` checked against the
   `capture-token` credential.

Either path being valid authorizes the request (they're not both required).

## Request format

`POST /capture`, either:

- `Content-Type: application/json` — body:
  ```json
  {"text": "...", "url": "https://...", "title": "...",
   "source": "iphone-shortcut|manual|script|capture-api",
   "kind": "note|url|voice|photo"}
  ```
  At least one of `text`, `url`, or an image (multipart) is required.
- `Content-Type: multipart/form-data` — same fields as form parts, plus one
  file part (any field name) carrying an image, ≤15MB. Images go to
  `attachments/<slug>/` and are embedded in the note as `![[...]]`.

Response: `201 {"path": "raw/2026-09-28-my-note.md"}` or `4xx {"error": "..."}`.

Never overwrites: filename collisions get `-2`, `-3`, ... suffixes.

## Audit log

One JSON line per request to `/var/log/cntxt1/capture-api-audit.jsonl` if
writable, else `~/.local/state/cntxt1/capture-api-audit.jsonl`:
`{ts, service, client, route, status, note?}` — `note` is the capture title,
truncated to 80 chars. Never logs secrets or full request bodies.

## Cloudflare dashboard setup

1. **Tunnel public hostname:** `capture.<domain>` → `http://127.0.0.1:8710`
   (Cloudflare Zero Trust → Networks → Tunnels → your tunnel → Public
   Hostname).
2. **Access application "KB capture"** on `capture.<domain>`:
   - Zero Trust → Access → Applications → Add an application → Self-hosted.
   - Application domain: `capture.<domain>`.
   - Policy: **Service Auth** — generate a service token (Zero Trust →
     Access → Service Auth → Create Service Token). Cloudflare gives you a
     Client ID + Client Secret; clients send these as
     `CF-Access-Client-Id` / `CF-Access-Client-Secret` headers.
   - Note the application's **Audience (AUD) Tag** (Application → Overview)
     → set as `CF_AUD_CAPTURE`.

## Local test run

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
VAULT=/path/to/test-vault CAPTURE_TOKEN=devtoken CAPTURE_PORT=8710 .venv/bin/python app.py
curl -X POST http://127.0.0.1:8710/capture \
  -H "Authorization: Bearer devtoken" -H "Content-Type: application/json" \
  -d '{"text":"hello","title":"Test"}'
```

## Tests

```
python3 -m venv .venv-test && .venv-test/bin/pip install -r requirements.txt
.venv-test/bin/python -m unittest discover -s tests -v
```

Writes only ever go to a temp-dir vault fixture (`tests/test_capture.py`'s
`VaultFixture`) — never the real vault.

See `SHORTCUT.md` for the iOS Shortcut you build against this endpoint, and `../README.md` for the
Cloudflare Tunnel + Access setup.
