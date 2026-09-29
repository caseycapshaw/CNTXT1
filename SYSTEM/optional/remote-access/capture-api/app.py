#!/usr/bin/env python3
"""capture-api — POST /capture writes a new dated note into your KB vault.

Binds 127.0.0.1:8710 only (see README.md). Exposed publicly only via a
Cloudflare Tunnel public hostname `capture.<domain>` -> 127.0.0.1:8710, with a
Cloudflare Access "Service Auth" application in front of it (service token
via CF-Access-Client-Id/Secret headers, checked at the edge). This process
adds a SECOND, independent check on top of that edge auth:

  1. `Cf-Access-Jwt-Assertion` header present -> verified as an RS256 JWT
     against the account's Access JWKS (iss/aud checked). This is the path
     Cloudflare Access itself sets on every request that passes the edge
     policy, so validating it here means a misconfigured/bypassed edge
     policy can't reach the vault.
  2. Otherwise `Authorization: Bearer <capture-token>` — for LAN/VPN
     clients that never cross the tunnel (e.g. a script on your home
     network), checked against a static shared token.

Format parity: this mirrors (not imports) `SYSTEM/bin/kb-mcp-server.py`'s
`tool_kb_capture` — same slug rule (`[^a-z0-9]+` -> `-`, lowered, stripped),
same `raw/YYYY-MM-DD-<slug>.md` naming with `-2`, `-3`, ... collision
handling, same `# <date> — <title>` + blockquote-Source header shape. It does
NOT call that function directly: its Source line is hardcoded to "Claude
Desktop conversation" (wrong here). Duplicating the ~15 lines of format logic
with a correct Source line was judged less confusing than importing a
function whose output would need post-editing every call.

VAULT is REQUIRED (no default): the service refuses to start without it.
"""
import base64
import hmac
import json
import mimetypes
import os
import re
import time
import uuid
from datetime import datetime, timezone
from email import policy as email_policy
from email.parser import BytesParser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

BIND_HOST = "127.0.0.1"
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_BODY_BYTES = MAX_IMAGE_BYTES + 1_000_000
SERVICE_NAME = "capture-api"
ALLOWED_KINDS = {"note", "url", "voice", "photo"}
ALLOWED_SOURCES = {"iphone-shortcut", "iphone", "iphone-share", "manual", "capture-api", "script"}


def env(name, default=""):
    return os.environ.get(name, default)


def vault_root():
    v = env("VAULT")
    if not v:
        raise RuntimeError("VAULT is not set (vault checkout path — required, no default)")
    return Path(v)


def credentials_dir():
    return env("CREDENTIALS_DIRECTORY") or None


def read_credential(name, env_fallback):
    d = credentials_dir()
    if d:
        p = Path(d) / name
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    return env(env_fallback)


def get_capture_token():
    return read_credential("capture-token", "CAPTURE_TOKEN")


# ---------------------------------------------------------------------------
# Cloudflare Access JWT (RS256) verification
# ---------------------------------------------------------------------------

def _b64url_decode(s):
    s = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def fetch_jwks(cf_team):
    url = f"https://{cf_team}.cloudflareaccess.com/cdn-cgi/access/certs"
    with urlopen(url, timeout=5) as r:  # noqa: S310 - fixed HTTPS host
        return json.loads(r.read())


_JWKS_CACHE = {}
JWKS_TTL_S = 600


def get_jwks(cf_team, fetcher):
    now = time.time()
    cached = _JWKS_CACHE.get(cf_team)
    if cached and now - cached[0] < JWKS_TTL_S:
        return cached[1]
    jwks = fetcher(cf_team)
    _JWKS_CACHE[cf_team] = (now, jwks)
    return jwks


def verify_rs256_jwt(token, issuer, audience, jwks_fetcher=fetch_jwks, leeway=60, now=None):
    """Verify a Cloudflare Access RS256 JWT. Returns the payload or raises ValueError.

    `jwks_fetcher` is injectable so tests can hand back a local RSA JWKS
    instead of hitting the network.
    """
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
    cf_team = issuer.rstrip("/").split("//", 1)[-1].split(".", 1)[0]
    jwks = get_jwks(cf_team, jwks_fetcher)
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


def authorize_request(headers, jwks_fetcher=fetch_jwks):
    """Returns (True, client_label) or (False, reason)."""
    cf_jwt = headers.get("Cf-Access-Jwt-Assertion")
    if cf_jwt:
        cf_team = env("CF_TEAM")
        cf_aud = env("CF_AUD_CAPTURE")
        if not cf_team or not cf_aud:
            return False, "CF Access not configured (CF_TEAM/CF_AUD_CAPTURE)"
        try:
            payload = verify_rs256_jwt(
                cf_jwt,
                issuer=f"https://{cf_team}.cloudflareaccess.com",
                audience=cf_aud,
                jwks_fetcher=jwks_fetcher,
            )
        except ValueError as e:
            return False, f"invalid Cf-Access-Jwt-Assertion: {e}"
        return True, payload.get("email") or "cf-access"
    auth = headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[len("Bearer "):].strip()
        expected = get_capture_token()
        if expected and hmac.compare_digest(token, expected):
            return True, "lan-token"
    return False, "missing/invalid credentials"


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def audit_log_path(service=SERVICE_NAME):
    override = env("AUDIT_LOG_PATH")
    if override:
        return Path(override)
    for candidate in (Path("/var/log/cntxt1") / f"{service}-audit.jsonl",):
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            probe = candidate.parent / f".write-test-{uuid.uuid4().hex}"
            probe.touch()
            probe.unlink()
            return candidate
        except OSError:
            continue
    fallback_dir = Path(env("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))) / "cntxt1"
    fallback_dir.mkdir(parents=True, exist_ok=True)
    return fallback_dir / f"{service}-audit.jsonl"


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
        pass  # audit logging must never break the request path


# ---------------------------------------------------------------------------
# Capture logic
# ---------------------------------------------------------------------------

SLUG_RE = re.compile(r"[^a-z0-9]+")


SLUG_MAX = 60
EXT_RE = re.compile(r"^\.[a-z0-9]{1,5}$")


def slugify(text):
    slug = SLUG_RE.sub("-", (text or "").lower()).strip("-")[:SLUG_MAX].strip("-")
    return slug or "capture"


def safe_ext(ext):
    """Only a short alphanumeric extension may come from client input."""
    ext = (ext or "").lower()
    return ext if EXT_RE.match(ext) else ".bin"


def contained(root, path):
    """Resolve `path` and refuse anything that escapes `root` (path-injection guard)."""
    root_r = root.resolve()
    path_r = path.resolve()
    if path_r != root_r and root_r not in path_r.parents:
        raise ValueError(f"refusing path outside {root_r}")
    return path_r


def make_title(data):
    if data.get("title"):
        return data["title"].strip()
    if data.get("text"):
        words = data["text"].strip().split()
        title = " ".join(words[:8])
        if title:
            return title
    if data.get("url"):
        return urlparse(data["url"]).netloc or "url-capture"
    return "capture"


def dest_path(vault, date_str, slug):
    base = contained(vault, vault / "raw")
    base.mkdir(parents=True, exist_ok=True)
    dest = contained(base, base / f"{date_str}-{slug}.md")
    n = 2
    while dest.exists():
        dest = contained(base, base / f"{date_str}-{slug}-{n}.md")
        n += 1
    return dest


def build_body(date_str, title, data, image_rel=None):
    source = data.get("source") or "capture-api"
    kind = data.get("kind") or ("photo" if image_rel else ("url" if data.get("url") else "note"))
    lines = [f"# {date_str} — {title}", "", f"> Source: capture-api ({source}), kind={kind}.", ""]
    if data.get("url"):
        lines += [f"URL: {data['url']}", ""]
    text = (data.get("text") or "").strip()
    if text:
        lines += [text, ""]
    if image_rel:
        lines += [f"![[{image_rel}]]", ""]
    return "\n".join(lines).rstrip() + "\n"


def append_kb_log(vault, date_str, rel_path, source):
    log_path = vault / "SYSTEM" / "log.md"
    line = (
        f"- {date_str} — Captured `{rel_path}` via capture-api ({source}); "
        f"awaiting compile in Claude Code. #auto\n"
    )
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass  # KB log is best-effort; the raw note write already succeeded


IMAGE_EXT_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/heic": ".heic",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


def parse_multipart(content_type, body_bytes):
    """Return (fields: dict, image: (filename, content_type, bytes) | None)."""
    m = re.search(r'boundary="?([^";]+)"?', content_type)
    if not m:
        raise ValueError("multipart request missing boundary")
    boundary = m.group(1)
    raw = (
        f"Content-Type: multipart/form-data; boundary={boundary}\r\n\r\n"
    ).encode() + body_bytes
    msg = BytesParser(policy=email_policy.compat32).parsebytes(raw)
    fields, image = {}, None
    if not msg.is_multipart():
        raise ValueError("not multipart")
    for part in msg.get_payload():
        name = None
        disp = part.get("Content-Disposition", "")
        pm = re.search(r'name="?([^";]+)"?', disp)
        if pm:
            name = pm.group(1)
        filename = None
        fm = re.search(r'filename="?([^";]*)"?', disp)
        if fm and fm.group(1):
            filename = fm.group(1)
        payload = part.get_payload(decode=True) or b""
        if filename:
            image = (filename, part.get_content_type(), payload)
        elif name:
            fields[name] = payload.decode("utf-8", errors="replace")
    return fields, image


class Handler(BaseHTTPRequestHandler):
    server_version = "capture-api/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # quiet default stderr logging
        pass

    def _send_json(self, status, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            self._send_json(200, {"status": "ok", "service": SERVICE_NAME})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/capture":
            self._send_json(404, {"error": "not found"})
            return
        ok, client = authorize_request(self.headers)
        if not ok:
            audit("/capture", client, 401)
            self._send_json(401, {"error": "unauthorized", "detail": client})
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY_BYTES:
            audit("/capture", client, 400, "bad content-length")
            self._send_json(400, {"error": "invalid or oversized body"})
            return
        body_bytes = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")

        try:
            if content_type.startswith("multipart/form-data"):
                fields, image = parse_multipart(content_type, body_bytes)
                data = dict(fields)
                image_bytes = image[2] if image else None
                image_ct = image[1] if image else None
                image_name = image[0] if image else None
                if image_bytes and len(image_bytes) > MAX_IMAGE_BYTES:
                    raise ValueError("image exceeds 15MB limit")
            elif content_type.startswith("application/json"):
                data = json.loads(body_bytes.decode("utf-8"))
                image_bytes = image_ct = image_name = None
            else:
                raise ValueError(f"unsupported Content-Type: {content_type!r}")

            if not isinstance(data, dict):
                raise ValueError("body must be a JSON object")
            if not data.get("text") and not data.get("url") and not image_bytes:
                raise ValueError("one of text, url, or an image file is required")
            kind = data.get("kind")
            if kind and kind not in ALLOWED_KINDS:
                raise ValueError(f"invalid kind: {kind!r}")
            source = data.get("source")
            if source and source not in ALLOWED_SOURCES:
                raise ValueError(f"invalid source: {source!r}")
        except ValueError as e:
            audit("/capture", client, 400, str(e))
            self._send_json(400, {"error": str(e)})
            return
        except Exception as e:
            audit("/capture", client, 400, f"parse error: {e}")
            self._send_json(400, {"error": f"could not parse request: {e}"})
            return

        vault = vault_root()
        date_str = datetime.now().strftime("%Y-%m-%d")
        title = make_title(data)
        slug = slugify(title)
        dest = dest_path(vault, date_str, slug)
        final_slug = dest.stem[len(date_str) + 1:]

        image_rel = None
        if image_bytes:
            ext = safe_ext(IMAGE_EXT_BY_CONTENT_TYPE.get(image_ct) or (
                Path(image_name).suffix if image_name else ""
            ) or mimetypes.guess_extension(image_ct or "") or ".bin")
            attach_root = contained(vault, vault / "attachments")
            attach_dir = contained(attach_root, attach_root / final_slug)
            attach_dir.mkdir(parents=True, exist_ok=True)
            img_path = contained(attach_dir, attach_dir / f"{final_slug}{ext}")
            n = 2
            while img_path.exists():
                img_path = contained(attach_dir, attach_dir / f"{final_slug}-{n}{ext}")
                n += 1
            img_path.write_bytes(image_bytes)
            image_rel = str(img_path.relative_to(vault))

        body_md = build_body(date_str, title, data, image_rel=image_rel)
        dest.write_text(body_md, encoding="utf-8")
        rel_path = str(dest.relative_to(vault))
        append_kb_log(vault, date_str, rel_path, data.get("source") or "capture-api")

        audit("/capture", client, 201, title)
        self._send_json(201, {"path": rel_path})


def make_server(port=None):
    port = port if port is not None else int(env("CAPTURE_PORT", "8710"))
    return ThreadingHTTPServer((BIND_HOST, port), Handler)


def main():
    try:
        vault_root()
    except RuntimeError as e:
        raise SystemExit(f"capture-api: {e}")
    server = make_server()
    print(f"capture-api listening on {BIND_HOST}:{server.server_address[1]} (vault={vault_root()})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
