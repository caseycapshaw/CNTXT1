# mcp-remote

Stdlib-ish Python HTTP server: Streamable HTTP MCP endpoint (`POST /mcp`,
spec 2025-06-18 compatible, stateless JSON responses) plus an embedded
single-user OAuth 2.1 authorization server, so claude.ai's MCP connector can
reach your KB without Cloudflare's "Managed OAuth" — claude.ai's custom-connector
flow has a known bug with it, so this server carries its own small single-user
OAuth 2.1 authorization server and Cloudflare Access only guards `/authorize`.

**Single implementation, reused:** the five tools (`kb_index`, `kb_read`,
`kb_search`, `kb_actions`, `kb_capture`) and the whole JSON-RPC dispatch
(`handle()`) are imported directly from `$VAULT/SYSTEM/bin/kb-mcp-server.py`
via `importlib`. This file only adds the HTTP/OAuth transport. **Personalize the
`INSTRUCTIONS` block in `kb-mcp-server.py` first** (`{{NAME}}`, `{{SCOPE}}`) — the server
prints a warning at import if placeholders remain.

## Config (env vars)

| Var | Required | Example | Notes |
| :-- | :-- | :-- | :-- |
| `VAULT` | yes | `/home/<user>/vault` | No default. Used only to locate `SYSTEM/bin/kb-mcp-server.py` to import. |
| `MCP_PORT` | no | `8711` | Bind port on 127.0.0.1. |
| `PUBLIC_BASE_URL` | yes | `https://mcp.example.com` | No trailing slash. Used as OAuth `issuer` and in metadata. |
| `CF_TEAM` | yes | `myteam` | Cloudflare Access team subdomain, for verifying `/authorize`'s `Cf-Access-Jwt-Assertion`. |
| `CF_AUD_AUTHORIZE` | yes | `a1b2c3...` | AUD tag of the "KB MCP authorize" Access application. |
| `ALLOWED_EMAIL` | **yes — no default** | `you@example.com` | Only this email's Access JWT can complete `/authorize`. **Fail closed:** unset/empty authorizes nobody and the server refuses to start. |
| `DEV` | no | `1` | Also allow `http://localhost:*` as a valid `redirect_uri` (for local connector testing). Never set in production. |
| `MCP_OAUTH_DB` | no | — | Override sqlite path (tests use this). Default `~/.local/state/cntxt1/mcp-oauth.db`. |
| `MCP_DISABLED_PATH` | no | — | Override kill-switch file path (tests use this). Default `~/.local/state/cntxt1/mcp-disabled`. |
| `AUDIT_LOG_PATH` | no | — | Override audit log destination (tests use this). |
| `MCP_CLIENT_ID` / `MCP_CLIENT_SECRET` | fallback only | — | Used only if the `mcp-client-id`/`mcp-client-secret` credentials aren't present — local/dev runs. |

## Credentials (systemd `LoadCredential`)

| Credential name | Purpose |
| :-- | :-- |
| `mcp-client-id` | Static OAuth client ID you paste into claude.ai's "Advanced settings" (alternative to Dynamic Client Registration). |
| `mcp-client-secret` | Matching static client secret. |

## Kill switch

Create `~/.local/state/cntxt1/mcp-disabled` (any content, e.g. `touch`) to
make every route return `503 {"error": "service disabled"}` immediately,
without restarting the service. Delete the file to re-enable.

## OAuth design

- **Dynamic Client Registration** (`POST /register`, RFC 7591-ish): public
  clients only (`token_endpoint_auth_method: "none"`), PKCE S256 required.
  `redirect_uris` must match `https://claude.ai/api/mcp/auth_callback`,
  `https://claude.com/api/mcp/auth_callback`, or (with `DEV=1`)
  `http://localhost:*`.
- **Static client**: `mcp-client-id`/`mcp-client-secret` credentials, for
  pasting into claude.ai's "Advanced settings" instead of DCR. Treated as a
  confidential client with the same allowed redirect URIs.
- **`/authorize`**: protected at the Cloudflare edge by an Access
  application (Allow: `ALLOWED_EMAIL`, email OTP) — see dashboard setup
  below. This server independently re-verifies the `Cf-Access-Jwt-Assertion`
  header it receives (RS256 against the account's JWKS; `iss`, `aud`
  (`CF_AUD_AUTHORIZE`), and `email == ALLOWED_EMAIL`), then shows a minimal
  HTML consent page (Approve button, CSRF-protected POST) before issuing an
  authorization code and redirecting back to the client's `redirect_uri`.
- **`/token`**: `application/x-www-form-urlencoded` only.
  `authorization_code` (verifies PKCE) and `refresh_token` (rotating —
  presenting an already-rotated refresh token revokes its whole token
  family, standard reuse-detection practice) grants. Opaque random tokens;
  only their SHA-256 hash is ever stored (sqlite,
  `~/.local/state/cntxt1/mcp-oauth.db`). Access TTL 1h, refresh TTL 30d.
  Unknown `client_id`, or a confidential client with the wrong secret, gets
  `401 {"error": "invalid_client"}`.
- **`/mcp`**: requires `Authorization: Bearer <access_token>`. Missing or
  invalid → `401` with
  `WWW-Authenticate: Bearer resource_metadata="<base>/.well-known/oauth-protected-resource"`.
  Rate-limited to 60 requests/min per token (in-memory; single process).
  `GET /mcp` → `405` (this server is stateless JSON-only, no SSE
  streaming).
- Path traversal on `kb_read` is guarded by the imported `kb-mcp-server.py`
  itself (`vault_path()` refuses anything resolving outside `VAULT`); tool
  errors come back as JSON-RPC results (`isError: true`), not HTTP errors —
  that's the vault server's existing behavior, reused as-is.

## Cloudflare dashboard setup

1. **Tunnel public hostname:** `mcp.<domain>` → `http://127.0.0.1:8711`.
2. **Access application "KB MCP authorize"** — narrowly scoped to the
   `/authorize` path only:
   - Zero Trust → Access → Applications → Add an application → Self-hosted.
   - Application domain: `mcp.<domain>/authorize` (path-scoped — do **not**
     apply this to all of `mcp.<domain>`).
   - Policy: Allow → Emails → your address (same as `ALLOWED_EMAIL`) → Email OTP (or your
     existing Access login method).
   - Note the Audience (AUD) Tag → set as `CF_AUD_AUTHORIZE`.
3. **No Access application on the rest of `mcp.<domain>`** — `/mcp`,
   `/token`, `/register`, and the `/.well-known/*` metadata endpoints must
   stay reachable by claude.ai without an Access login; they're protected by
   this server's own OAuth instead. Applying Access more broadly would break
   the connector (claude.ai can't complete an interactive Access login).

## claude.ai connector setup

1. claude.ai → Settings → Connectors → Add custom connector.
2. URL: `https://mcp.<domain>/mcp`.
3. Let claude.ai attempt Dynamic Client Registration first (no further
   input needed) — if that doesn't work, open **Advanced settings** and
   paste the static `mcp-client-id` / `mcp-client-secret` credential values.
4. Approve the connector — this opens `/authorize` behind Cloudflare Access
   (log in as your `ALLOWED_EMAIL` via email OTP if prompted), then
   shows this server's consent page. Click **Approve**.

## Local test run

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
VAULT=/path/to/vault PUBLIC_BASE_URL=http://127.0.0.1:8711 \
  ALLOWED_EMAIL=you@example.com CF_TEAM=myteam CF_AUD_AUTHORIZE=devaud DEV=1 \
  MCP_CLIENT_ID=dev MCP_CLIENT_SECRET=devsecret \
  .venv/bin/python server.py
```

## Tests

```
python3 -m venv .venv-test && .venv-test/bin/pip install -r requirements.txt
.venv-test/bin/python -m unittest discover -s tests -v
```

Spins up a real server on an ephemeral 127.0.0.1 port per test class, signs
a fake Cloudflare Access JWT with a local throwaway RSA key (verified
through an injected `server.JWKS_FETCHER` — no real network calls), and
drives the full DCR + PKCE + consent + token + refresh-rotation flow end to
end. `kb_read`/`kb_search` calls point `VAULT` at the vault this add-on sits in (or
`$VAULT_FOR_TESTS`) — **read-only**; `kb_capture` is never exercised in these tests. The test
module skips itself with a message when `cryptography` isn't installed.

Note for test authors: the test HTTP client (`tests/test_mcp_oauth.py`'s
`http()` helper) deliberately disables automatic redirect-following — the
`/authorize` `redirect_uri` points at a real external domain
(`claude.ai`/`claude.com`) that a sandboxed test run generally can't (and
shouldn't try to) reach; the test only needs to inspect the `Location`
header of the `302`, never follow it.
