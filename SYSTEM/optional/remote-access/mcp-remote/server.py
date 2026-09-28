#!/usr/bin/env python3
"""mcp-remote — Streamable HTTP MCP server (spec 2025-06-18 compatible,
stateless JSON responses) fronting your KB, with an embedded single-user
OAuth 2.1 authorization server. Cloudflare's "Managed OAuth" is deliberately
NOT used: claude.ai's custom-connector flow has a known bug with it, so the
OAuth server lives here and Cloudflare Access only guards /authorize.

Binds 127.0.0.1:8711 only. Exposed publicly only via a Cloudflare Tunnel
public hostname `mcp.<domain>` -> 127.0.0.1:8711. Only `/authorize` has a
Cloudflare Access application in front of it (email-OTP, ALLOWED_EMAIL only);
everything else on mcp.<domain> is protected by this server's own OAuth
(bearer tokens on /mcp, DCR/static-client + PKCE on /authorize + /token).

Single implementation, reused: the five MCP tools (kb_index, kb_read,
kb_search, kb_actions, kb_capture) and the whole JSON-RPC method dispatch
(`handle()`) are imported directly from the vault's own stdio MCP server,
`$VAULT/SYSTEM/bin/kb-mcp-server.py`, via importlib — this file adds nothing
tool-shaped of its own, only the HTTP/OAuth transport around it.

Fail closed: the server refuses to start unless ALLOWED_EMAIL, PUBLIC_BASE_URL,
CF_TEAM, CF_AUD_AUTHORIZE and VAULT are set. ALLOWED_EMAIL has NO default — an
empty value never authorizes anyone.
"""
import base64
import hashlib
import hmac
import html
import importlib.util
import json
import os
import re
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen

BIND_HOST = "127.0.0.1"
SERVICE_NAME = "mcp-remote"

ACCESS_TOKEN_TTL = 3600
REFRESH_TOKEN_TTL = 30 * 24 * 3600
AUTH_CODE_TTL = 300
PENDING_AUTHZ_TTL = 600
RATE_LIMIT_PER_MIN = 60
ALLOWED_REDIRECT_PREFIXES = (
    "https://claude.ai/api/mcp/auth_callback",
    "https://claude.com/api/mcp/auth_callback",
)


def env(name, default=""):
    return os.environ.get(name, default)


def is_dev():
    return env("DEV") == "1"


def credentials_dir():
    return env("CREDENTIALS_DIRECTORY") or None


def read_credential(name, env_fallback):
    d = credentials_dir()
    if d:
        p = Path(d) / name
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    return env(env_fallback)


def public_base_url():
    return env("PUBLIC_BASE_URL", "").rstrip("/")


def allowed_email():
    return env("ALLOWED_EMAIL").strip()


def cf_team():
    return env("CF_TEAM")


def cf_aud_authorize():
    return env("CF_AUD_AUTHORIZE")


def static_client_id():
    return read_credential("mcp-client-id", "MCP_CLIENT_ID")


def static_client_secret():
    return read_credential("mcp-client-secret", "MCP_CLIENT_SECRET")


def kill_switch_path():
    return Path(env("MCP_DISABLED_PATH", str(Path.home() / ".local" / "state" / "cntxt1" / "mcp-disabled")))


def is_disabled():
    return kill_switch_path().exists()


# ---------------------------------------------------------------------------
# Cloudflare Access JWT (RS256) verification — same approach as capture-api.
# JWKS_FETCHER is a module-level global (not a default arg) so tests can
# monkeypatch `server.JWKS_FETCHER = fake` and have every call pick it up.
# ---------------------------------------------------------------------------

def _b64url_decode(s):
    s = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def fetch_jwks(team):
    url = f"https://{team}.cloudflareaccess.com/cdn-cgi/access/certs"
    with urlopen(url, timeout=5) as r:  # noqa: S310 - fixed HTTPS host
        return json.loads(r.read())


JWKS_FETCHER = fetch_jwks

_JWKS_CACHE = {}
JWKS_TTL_S = 600


def get_jwks(team):
    now = time.time()
    cached = _JWKS_CACHE.get(team)
    if cached and now - cached[0] < JWKS_TTL_S:
        return cached[1]
    jwks = JWKS_FETCHER(team)
    _JWKS_CACHE[team] = (now, jwks)
    return jwks


def verify_rs256_jwt(token, issuer, audience, leeway=60, now=None):
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("malformed JWT")
    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
        sig = _b64url_decode(sig_b64)
    except Exception as e:
        raise ValueError(f"malformed JWT segment: {e}")
    if header.get("alg") != "RS256":
        raise ValueError(f"unsupported alg: {header.get('alg')}")
    team = issuer.rstrip("/").split("//", 1)[-1].split(".", 1)[0]
    jwks = get_jwks(team)
    keys = jwks.get("keys") or jwks.get("public_certs") or []
    kid = header.get("kid")
    jwk = next((k for k in keys if k.get("kid") == kid), None) or (keys[0] if keys else None)
    if jwk is None:
        raise ValueError("no matching JWKS key")
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    n = int.from_bytes(_b64url_decode(jwk["n"]), "big")
    e = int.from_bytes(_b64url_decode(jwk["e"]), "big")
    public_key = rsa.RSAPublicNumbers(e, n).public_key()
    signing_input = f"{header_b64}.{payload_b64}".encode()
    try:
        public_key.verify(sig, signing_input, padding.PKCS1v15(), hashes.SHA256())
    except Exception:
        raise ValueError("bad signature")
    now = time.time() if now is None else now
    if "exp" in payload and now > payload["exp"] + leeway:
        raise ValueError("token expired")
    if "nbf" in payload and now < payload["nbf"] - leeway:
        raise ValueError("token not yet valid")
    if payload.get("iss") != issuer:
        raise ValueError(f"issuer mismatch: {payload.get('iss')!r} != {issuer!r}")
    aud = payload.get("aud")
    auds = aud if isinstance(aud, list) else [aud]
    if audience not in auds:
        raise ValueError("audience mismatch")
    return payload


def check_cf_access(headers):
    """Validate the Cf-Access-Jwt-Assertion header for /authorize.

    Returns (True, email) or (False, reason). This is a second, independent
    check on top of the Cloudflare Access application already gating this
    path at the edge (Allow: ALLOWED_EMAIL, email OTP).
    """
    token = headers.get("Cf-Access-Jwt-Assertion")
    if not token:
        return False, "missing Cf-Access-Jwt-Assertion"
    team, aud = cf_team(), cf_aud_authorize()
    if not team or not aud:
        return False, "CF Access not configured (CF_TEAM/CF_AUD_AUTHORIZE)"
    try:
        payload = verify_rs256_jwt(token, issuer=f"https://{team}.cloudflareaccess.com", audience=aud)
    except ValueError as e:
        return False, f"invalid Cf-Access-Jwt-Assertion: {e}"
    allowed = allowed_email()
    if not allowed:
        return False, "ALLOWED_EMAIL not configured"
    email = payload.get("email")
    if not isinstance(email, str) or email.lower() != allowed.lower():
        return False, f"email not allowed: {email!r}"
    return True, email


# ---------------------------------------------------------------------------
# sqlite storage — clients, pending consent requests, auth codes, tokens.
# A fresh connection per call (personal single-user server; correctness and
# env-var-driven testability matter far more here than connection reuse).
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
  client_id TEXT PRIMARY KEY,
  client_secret_hash TEXT,
  redirect_uris TEXT NOT NULL,
  client_type TEXT NOT NULL,
  client_name TEXT,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS pending_authz (
  request_id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  redirect_uri TEXT NOT NULL,
  code_challenge TEXT NOT NULL,
  code_challenge_method TEXT NOT NULL,
  state TEXT,
  scope TEXT,
  csrf_token TEXT NOT NULL,
  expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_codes (
  code_hash TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  redirect_uri TEXT NOT NULL,
  code_challenge TEXT NOT NULL,
  code_challenge_method TEXT NOT NULL,
  expires_at REAL NOT NULL,
  used INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tokens (
  token_hash TEXT PRIMARY KEY,
  client_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  expires_at REAL NOT NULL,
  refresh_family TEXT,
  revoked INTEGER NOT NULL DEFAULT 0,
  created_at REAL NOT NULL
);
"""

_DB_LOCK = threading.Lock()


def db_path():
    return Path(env("MCP_OAUTH_DB", str(Path.home() / ".local" / "state" / "cntxt1" / "mcp-oauth.db")))


def connect_db():
    p = db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False, timeout=5)
    conn.executescript(SCHEMA)
    return conn


def h(s):
    return hashlib.sha256(s.encode()).hexdigest()


def redirect_uri_allowed(uri):
    if any(uri.startswith(p) for p in ALLOWED_REDIRECT_PREFIXES):
        return True
    if is_dev() and uri.startswith("http://localhost"):
        return True
    return False


def get_client(client_id):
    sid, ssecret = static_client_id(), static_client_secret()
    if sid and client_id == sid:
        prefixes = list(ALLOWED_REDIRECT_PREFIXES) + (["http://localhost"] if is_dev() else [])
        return {
            "client_id": client_id,
            "client_type": "confidential",
            "redirect_uris": prefixes,
            "secret_hash": h(ssecret) if ssecret else None,
        }
    with _DB_LOCK:
        conn = connect_db()
        try:
            row = conn.execute(
                "SELECT client_id, client_secret_hash, redirect_uris, client_type FROM clients WHERE client_id=?",
                (client_id,),
            ).fetchone()
        finally:
            conn.close()
    if not row:
        return None
    return {
        "client_id": row[0],
        "secret_hash": row[1],
        "redirect_uris": json.loads(row[2]),
        "client_type": row[3],
    }


def create_client(redirect_uris, client_name=None):
    client_id = "dcr-" + secrets.token_urlsafe(16)
    with _DB_LOCK:
        conn = connect_db()
        try:
            conn.execute(
                "INSERT INTO clients (client_id, client_secret_hash, redirect_uris, client_type, client_name, created_at)"
                " VALUES (?,?,?,?,?,?)",
                (client_id, None, json.dumps(redirect_uris), "public", client_name, time.time()),
            )
            conn.commit()
        finally:
            conn.close()
    return client_id


def store_pending_authz(client_id, redirect_uri, code_challenge, code_challenge_method, state, scope):
    request_id = secrets.token_urlsafe(24)
    csrf_token = secrets.token_urlsafe(24)
    with _DB_LOCK:
        conn = connect_db()
        try:
            conn.execute(
                "INSERT INTO pending_authz (request_id, client_id, redirect_uri, code_challenge,"
                " code_challenge_method, state, scope, csrf_token, expires_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    request_id, client_id, redirect_uri, code_challenge, code_challenge_method,
                    state, scope, csrf_token, time.time() + PENDING_AUTHZ_TTL,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    return request_id, csrf_token


def pop_pending_authz(request_id):
    with _DB_LOCK:
        conn = connect_db()
        try:
            row = conn.execute(
                "SELECT client_id, redirect_uri, code_challenge, code_challenge_method, state, scope,"
                " csrf_token, expires_at FROM pending_authz WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if row:
                conn.execute("DELETE FROM pending_authz WHERE request_id=?", (request_id,))
                conn.commit()
        finally:
            conn.close()
    if not row:
        return None
    keys = ("client_id", "redirect_uri", "code_challenge", "code_challenge_method", "state", "scope", "csrf_token", "expires_at")
    d = dict(zip(keys, row))
    if time.time() > d["expires_at"]:
        return None
    return d


def create_auth_code(client_id, redirect_uri, code_challenge, code_challenge_method):
    code = secrets.token_urlsafe(32)
    with _DB_LOCK:
        conn = connect_db()
        try:
            conn.execute(
                "INSERT INTO auth_codes (code_hash, client_id, redirect_uri, code_challenge,"
                " code_challenge_method, expires_at) VALUES (?,?,?,?,?,?)",
                (h(code), client_id, redirect_uri, code_challenge, code_challenge_method, time.time() + AUTH_CODE_TTL),
            )
            conn.commit()
        finally:
            conn.close()
    return code


def consume_auth_code(code):
    with _DB_LOCK:
        conn = connect_db()
        try:
            row = conn.execute(
                "SELECT client_id, redirect_uri, code_challenge, code_challenge_method, expires_at, used"
                " FROM auth_codes WHERE code_hash=?",
                (h(code),),
            ).fetchone()
            if row and not row[5]:
                conn.execute("UPDATE auth_codes SET used=1 WHERE code_hash=?", (h(code),))
                conn.commit()
        finally:
            conn.close()
    if not row:
        return None
    client_id, redirect_uri, code_challenge, code_challenge_method, expires_at, used = row
    if used or time.time() > expires_at:
        return None
    return {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
    }


def issue_tokens(client_id, refresh_family=None):
    access = secrets.token_urlsafe(32)
    refresh = secrets.token_urlsafe(32)
    now = time.time()
    family = refresh_family or secrets.token_urlsafe(12)
    with _DB_LOCK:
        conn = connect_db()
        try:
            conn.execute(
                "INSERT INTO tokens (token_hash, client_id, kind, expires_at, refresh_family, created_at) VALUES (?,?,?,?,?,?)",
                (h(access), client_id, "access", now + ACCESS_TOKEN_TTL, family, now),
            )
            conn.execute(
                "INSERT INTO tokens (token_hash, client_id, kind, expires_at, refresh_family, created_at) VALUES (?,?,?,?,?,?)",
                (h(refresh), client_id, "refresh", now + REFRESH_TOKEN_TTL, family, now),
            )
            conn.commit()
        finally:
            conn.close()
    return access, refresh


def revoke_family(family):
    with _DB_LOCK:
        conn = connect_db()
        try:
            conn.execute("UPDATE tokens SET revoked=1 WHERE refresh_family=?", (family,))
            conn.commit()
        finally:
            conn.close()


def rotate_refresh_token(presented_refresh, client_id):
    """Consume a refresh token and issue a new access+refresh pair.

    Rotating: the presented refresh token is revoked immediately. If a
    revoked (already-used) refresh token is presented again — reuse, a sign
    of token theft — the whole token family is revoked. Returns
    (access, refresh) or None on any failure.
    """
    token_hash = h(presented_refresh)
    with _DB_LOCK:
        conn = connect_db()
        try:
            row = conn.execute(
                "SELECT client_id, expires_at, revoked, refresh_family FROM tokens WHERE token_hash=? AND kind='refresh'",
                (token_hash,),
            ).fetchone()
        finally:
            conn.close()
    if not row:
        return None
    row_client_id, expires_at, revoked, family = row
    if row_client_id != client_id:
        return None
    if revoked:
        revoke_family(family)  # reuse detected
        return None
    if time.time() > expires_at:
        return None
    with _DB_LOCK:
        conn = connect_db()
        try:
            conn.execute("UPDATE tokens SET revoked=1 WHERE token_hash=?", (token_hash,))
            conn.commit()
        finally:
            conn.close()
    return issue_tokens(client_id, refresh_family=family)


def verify_access_token(token):
    with _DB_LOCK:
        conn = connect_db()
        try:
            row = conn.execute(
                "SELECT client_id, expires_at, revoked FROM tokens WHERE token_hash=? AND kind='access'",
                (h(token),),
            ).fetchone()
        finally:
            conn.close()
    if not row:
        return None
    client_id, expires_at, revoked = row
    if revoked or time.time() > expires_at:
        return None
    return client_id


def pkce_ok(verifier, challenge, method):
    if method != "S256" or not verifier:
        return False
    digest = hashlib.sha256(verifier.encode()).digest()
    calc = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return hmac.compare_digest(calc, challenge)


# ---------------------------------------------------------------------------
# Rate limiting — 60 req/min per access token (in-memory; single process).
# ---------------------------------------------------------------------------

_RATE_LOCK = threading.Lock()
_RATE_BUCKETS = {}


def rate_limited(token_hash):
    now = time.time()
    with _RATE_LOCK:
        bucket = _RATE_BUCKETS.setdefault(token_hash, [])
        bucket[:] = [t for t in bucket if now - t < 60]
        if len(bucket) >= RATE_LIMIT_PER_MIN:
            return True
        bucket.append(now)
        return False


# ---------------------------------------------------------------------------
# Reuse the vault's own MCP tool implementation, single source of truth.
# ---------------------------------------------------------------------------

_KBMCP = None


def kbmcp():
    global _KBMCP
    if _KBMCP is None:
        if not env("VAULT"):
            raise RuntimeError("VAULT is not set (vault checkout path — required, no default)")
        vault = Path(env("VAULT"))
        path = vault / "SYSTEM" / "bin" / "kb-mcp-server.py"
        spec = importlib.util.spec_from_file_location("kb_mcp_server", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if "{{" in getattr(mod, "INSTRUCTIONS", ""):
            import sys
            print("mcp-remote: WARNING — kb-mcp-server.py INSTRUCTIONS still contains {{placeholders}}; "
                  "personalize it (see setup.md) before exposing this server", file=sys.stderr)
        _KBMCP = mod
    return _KBMCP


def reset_kbmcp_cache():
    """Test hook: force the next kbmcp() call to re-import (VAULT changed)."""
    global _KBMCP
    _KBMCP = None


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def audit_log_path():
    override = env("AUDIT_LOG_PATH")
    if override:
        return Path(override)
    candidate = Path("/var/log/cntxt1") / f"{SERVICE_NAME}-audit.jsonl"
    try:
        candidate.parent.mkdir(parents=True, exist_ok=True)
        probe = candidate.parent / f".write-test-{secrets.token_hex(8)}"
        probe.touch()
        probe.unlink()
        return candidate
    except OSError:
        pass
    fallback_dir = Path(env("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))) / "cntxt1"
    fallback_dir.mkdir(parents=True, exist_ok=True)
    return fallback_dir / f"{SERVICE_NAME}-audit.jsonl"


def audit(route, client, status, note=None):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "service": SERVICE_NAME,
        "client": client,
        "route": route,
        "status": status,
    }
    if note:
        entry["note"] = note[:80]
    try:
        with audit_log_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

CONSENT_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Authorize MCP access</title></head>
<body style="font-family: -apple-system, sans-serif; max-width: 32rem; margin: 4rem auto;">
<h1>Authorize MCP access</h1>
<p>Client <code>{client_id}</code> is requesting access to your KB MCP server
(<code>{base_url}</code>) as <strong>{email}</strong>.</p>
<form method="POST" action="/authorize">
  <input type="hidden" name="request_id" value="{request_id}">
  <input type="hidden" name="csrf_token" value="{csrf_token}">
  <button type="submit" name="approve" value="yes" style="font-size:1.1rem;padding:0.6rem 1.2rem;">Approve</button>
</form>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "mcp-remote/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    # -- helpers -------------------------------------------------------
    def _send_json(self, status, obj, extra_headers=None):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status, body_str):
        body = body_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length > 0 else b""

    def _bearer_token(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[len("Bearer "):].strip()
        return None

    # -- routing ---------------------------------------------------------
    def do_GET(self):
        if is_disabled():
            self._send_json(503, {"error": "service disabled"})
            return
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/healthz":
            self._send_json(200, {"status": "ok", "service": SERVICE_NAME})
        elif path == "/.well-known/oauth-protected-resource":
            self.handle_protected_resource_metadata()
        elif path == "/.well-known/oauth-authorization-server":
            self.handle_authorization_server_metadata()
        elif path == "/authorize":
            self.handle_authorize_get(parse_qs(parsed.query))
        elif path == "/mcp":
            self._send_json(405, {"error": "GET not supported; POST JSON-RPC to /mcp"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if is_disabled():
            self._send_json(503, {"error": "service disabled"})
            return
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/register":
            self.handle_register()
        elif path == "/authorize":
            self.handle_authorize_post()
        elif path == "/token":
            self.handle_token()
        elif path == "/mcp":
            self.handle_mcp()
        else:
            self._send_json(404, {"error": "not found"})

    # -- metadata ----------------------------------------------------
    def handle_protected_resource_metadata(self):
        base = public_base_url()
        self._send_json(200, {"resource": f"{base}/mcp", "authorization_servers": [base]})

    def handle_authorization_server_metadata(self):
        base = public_base_url()
        self._send_json(200, {
            "issuer": base,
            "authorization_endpoint": f"{base}/authorize",
            "token_endpoint": f"{base}/token",
            "registration_endpoint": f"{base}/register",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
        })

    # -- DCR -----------------------------------------------------------
    def handle_register(self):
        try:
            data = json.loads(self._read_body().decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "invalid_client_metadata"})
            return
        redirect_uris = data.get("redirect_uris") or []
        if not redirect_uris or not all(redirect_uri_allowed(u) for u in redirect_uris):
            self._send_json(400, {"error": "invalid_redirect_uri"})
            return
        client_name = data.get("client_name")
        client_id = create_client(redirect_uris, client_name=client_name)
        audit("/register", client_name or "dcr", 201, client_id)
        self._send_json(201, {
            "client_id": client_id,
            "client_id_issued_at": int(time.time()),
            "redirect_uris": redirect_uris,
            "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "client_name": client_name,
        })

    # -- /authorize ------------------------------------------------------
    def handle_authorize_get(self, q):
        ok, email_or_reason = check_cf_access(self.headers)
        if not ok:
            audit("/authorize", "unknown", 403, email_or_reason)
            self._send_json(403, {"error": "forbidden", "detail": email_or_reason})
            return
        email = email_or_reason
        client_id = (q.get("client_id") or [None])[0]
        redirect_uri = (q.get("redirect_uri") or [None])[0]
        response_type = (q.get("response_type") or [None])[0]
        code_challenge = (q.get("code_challenge") or [None])[0]
        code_challenge_method = (q.get("code_challenge_method") or [None])[0]
        state = (q.get("state") or [None])[0]
        scope = (q.get("scope") or [None])[0]

        if response_type != "code":
            self._send_json(400, {"error": "unsupported_response_type"})
            return
        if not client_id or get_client(client_id) is None:
            self._send_json(400, {"error": "invalid_client"})
            return
        client = get_client(client_id)
        uri_known = bool(redirect_uri) and (
            redirect_uri in client["redirect_uris"] or redirect_uri_allowed(redirect_uri)
        )
        if not uri_known:
            self._send_json(400, {"error": "invalid_redirect_uri"})
            return
        if code_challenge_method != "S256" or not code_challenge:
            self._send_json(400, {"error": "invalid_request", "detail": "PKCE S256 required"})
            return

        request_id, csrf_token = store_pending_authz(
            client_id, redirect_uri, code_challenge, code_challenge_method, state, scope
        )
        audit("/authorize", email, 200, client_id)
        self._send_html(200, CONSENT_PAGE.format(
            client_id=html.escape(client_id),
            base_url=html.escape(public_base_url()),
            email=html.escape(email),
            request_id=html.escape(request_id),
            csrf_token=html.escape(csrf_token),
        ))

    def handle_authorize_post(self):
        ok, email_or_reason = check_cf_access(self.headers)
        if not ok:
            audit("/authorize", "unknown", 403, email_or_reason)
            self._send_json(403, {"error": "forbidden", "detail": email_or_reason})
            return
        email = email_or_reason
        body = self._read_body().decode("utf-8")
        form = parse_qs(body)
        request_id = (form.get("request_id") or [None])[0]
        csrf_token = (form.get("csrf_token") or [None])[0]
        approve = (form.get("approve") or [None])[0]

        pending = pop_pending_authz(request_id) if request_id else None
        if not pending:
            self._send_json(400, {"error": "invalid_request", "detail": "expired or unknown request_id"})
            return
        if not csrf_token or not hmac.compare_digest(csrf_token, pending["csrf_token"]):
            self._send_json(403, {"error": "invalid_csrf_token"})
            return
        if approve != "yes":
            self._send_redirect(f"{pending['redirect_uri']}?error=access_denied&state={pending['state'] or ''}")
            return

        code = create_auth_code(
            pending["client_id"], pending["redirect_uri"], pending["code_challenge"], pending["code_challenge_method"]
        )
        audit("/authorize", email, 302, pending["client_id"])
        params = {"code": code}
        if pending["state"]:
            params["state"] = pending["state"]
        self._send_redirect(f"{pending['redirect_uri']}?{urlencode(params)}")

    # -- /token ------------------------------------------------------
    def handle_token(self):
        content_type = self.headers.get("Content-Type", "")
        if "application/x-www-form-urlencoded" not in content_type:
            self._send_json(400, {"error": "invalid_request", "detail": "expected application/x-www-form-urlencoded"})
            return
        form = parse_qs(self._read_body().decode("utf-8"))
        get = lambda k: (form.get(k) or [None])[0]  # noqa: E731

        grant_type = get("grant_type")
        client_id = get("client_id")
        client_secret = get("client_secret")

        client = get_client(client_id) if client_id else None
        if client is None:
            audit("/token", client_id or "unknown", 401, "invalid_client")
            self._send_json(401, {"error": "invalid_client"})
            return
        if client["client_type"] == "confidential":
            if not client_secret or not client.get("secret_hash") or not hmac.compare_digest(h(client_secret), client["secret_hash"]):
                audit("/token", client_id, 401, "invalid_client")
                self._send_json(401, {"error": "invalid_client"})
                return

        if grant_type == "authorization_code":
            code = get("code")
            redirect_uri = get("redirect_uri")
            code_verifier = get("code_verifier")
            if not code:
                self._send_json(400, {"error": "invalid_request"})
                return
            entry = consume_auth_code(code)
            if not entry or entry["client_id"] != client_id:
                audit("/token", client_id, 400, "invalid_grant")
                self._send_json(400, {"error": "invalid_grant"})
                return
            if entry["redirect_uri"] != redirect_uri:
                self._send_json(400, {"error": "invalid_grant", "detail": "redirect_uri mismatch"})
                return
            if not pkce_ok(code_verifier or "", entry["code_challenge"], entry["code_challenge_method"]):
                audit("/token", client_id, 400, "pkce_failed")
                self._send_json(400, {"error": "invalid_grant", "detail": "PKCE verification failed"})
                return
            access, refresh = issue_tokens(client_id)
            audit("/token", client_id, 200, "authorization_code")
            self._send_json(200, {
                "access_token": access,
                "token_type": "Bearer",
                "expires_in": ACCESS_TOKEN_TTL,
                "refresh_token": refresh,
            })
            return

        if grant_type == "refresh_token":
            refresh_token = get("refresh_token")
            if not refresh_token:
                self._send_json(400, {"error": "invalid_request"})
                return
            result = rotate_refresh_token(refresh_token, client_id)
            if result is None:
                audit("/token", client_id, 400, "invalid_grant (refresh)")
                self._send_json(400, {"error": "invalid_grant"})
                return
            access, refresh = result
            audit("/token", client_id, 200, "refresh_token")
            self._send_json(200, {
                "access_token": access,
                "token_type": "Bearer",
                "expires_in": ACCESS_TOKEN_TTL,
                "refresh_token": refresh,
            })
            return

        self._send_json(400, {"error": "unsupported_grant_type"})

    # -- /mcp ------------------------------------------------------------
    def handle_mcp(self):
        token = self._bearer_token()
        base = public_base_url()
        www_auth = f'Bearer resource_metadata="{base}/.well-known/oauth-protected-resource"'
        if not token:
            audit("/mcp", "unknown", 401)
            self._send_json(401, {"error": "unauthorized"}, extra_headers={"WWW-Authenticate": www_auth})
            return
        client_id = verify_access_token(token)
        if client_id is None:
            audit("/mcp", "unknown", 401)
            self._send_json(401, {"error": "unauthorized"}, extra_headers={"WWW-Authenticate": www_auth})
            return
        if rate_limited(h(token)):
            audit("/mcp", client_id, 429)
            self._send_json(429, {"error": "rate_limited"})
            return

        try:
            msg = json.loads(self._read_body().decode("utf-8"))
        except Exception:
            self._send_json(400, {"jsonrpc": "2.0", "error": {"code": -32700, "message": "parse error"}})
            return

        method = msg.get("method", "")
        params = msg.get("params") or {}
        reply = {"jsonrpc": "2.0"}
        if "id" in msg:
            reply["id"] = msg["id"]
        try:
            reply["result"] = kbmcp().handle(method, params)
        except KeyError:
            reply["error"] = {"code": -32601, "message": f"method not found: {method}"}
        except FileNotFoundError as e:
            reply["error"] = {"code": -32602, "message": f"not found: {e}"}
        except Exception as e:
            reply["error"] = {"code": -32603, "message": str(e)}
        audit("/mcp", client_id, 200, method)
        self._send_json(200, reply)


def make_server(port=None):
    port = port if port is not None else int(env("MCP_PORT", "8711"))
    return ThreadingHTTPServer((BIND_HOST, port), Handler)


REQUIRED_ENV = ("VAULT", "ALLOWED_EMAIL", "PUBLIC_BASE_URL", "CF_TEAM", "CF_AUD_AUTHORIZE")


def main():
    missing = [k for k in REQUIRED_ENV if not env(k).strip()]
    if missing:
        raise SystemExit("mcp-remote: refusing to start, required env not set: " + ", ".join(missing))
    server = make_server()
    print(f"mcp-remote listening on {BIND_HOST}:{server.server_address[1]} (base={public_base_url() or '(unset)'})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
