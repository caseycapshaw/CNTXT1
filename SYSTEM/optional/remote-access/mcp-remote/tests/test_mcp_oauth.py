#!/usr/bin/env python3
"""Integration tests for mcp-remote. No real network access — the Cloudflare
Access JWT is signed locally with a throwaway RSA key and verified through
an injected JWKS fetcher (server.JWKS_FETCHER), never a real HTTPS call.

kb_read/kb_search tests point VAULT at the vault this add-on sits in (or
$VAULT_FOR_TESTS) — read-only calls only; kb_read/kb_search never write.
kb_capture is never exercised here, so that vault is never written to.

The handful of tests that actually invoke a kb_* tool (via kbmcp(), which
imports the vault's SYSTEM/bin/kb-mcp-server.py) are skipped, with a message,
when that file can't be found.

Requires the `cryptography` package (pip install -r requirements.txt); the
module skips cleanly with a message when it isn't installed.
"""
import base64
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    import cryptography  # noqa: F401
except ImportError:
    raise unittest.SkipTest("mcp-remote tests skipped: 'cryptography' not installed (pip install cryptography)")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server  # noqa: E402

from cryptography.hazmat.primitives import hashes  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import padding, rsa  # noqa: E402


def _enclosing_vault():
    for parent in Path(__file__).resolve().parents:
        if (parent / "SYSTEM" / "SCHEMA.md").is_file():
            return parent
    return Path("/nonexistent-vault")


REAL_VAULT = Path(os.environ.get("VAULT_FOR_TESTS") or _enclosing_vault())
# kb_read/kb_search reuse the vault's own SYSTEM/bin/kb-mcp-server.py (single
# source of truth — see server.kbmcp()).
_VAULT_KBMCP_AVAILABLE = (REAL_VAULT / "SYSTEM" / "bin" / "kb-mcp-server.py").is_file()


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def sha256_b64url(data: bytes) -> str:
    return b64url(hashlib.sha256(data).digest())


class FakeAccess:
    """A local RSA keypair standing in for Cloudflare Access's JWKS."""

    def __init__(self, team, aud, email="owner@example.com"):
        self.team = team
        self.aud = aud
        self.email = email
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.kid = "test-kid"

    def jwks(self, team):
        pub = self.key.public_key().public_numbers()
        n = pub.n.to_bytes((pub.n.bit_length() + 7) // 8, "big")
        e = pub.e.to_bytes((pub.e.bit_length() + 7) // 8, "big")
        return {"keys": [{"kty": "RSA", "kid": self.kid, "n": b64url(n), "e": b64url(e)}]}

    def token(self, **overrides):
        now = int(time.time())
        payload = {
            "iss": f"https://{self.team}.cloudflareaccess.com",
            "aud": self.aud,
            "email": self.email,
            "exp": now + 3600,
            "iat": now,
        }
        payload.update(overrides)
        header = {"alg": "RS256", "kid": self.kid}
        h_b64 = b64url(json.dumps(header).encode())
        p_b64 = b64url(json.dumps(payload).encode())
        signing_input = f"{h_b64}.{p_b64}".encode()
        sig = self.key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        return f"{h_b64}.{p_b64}.{b64url(sig)}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Don't auto-follow 30x — /authorize's redirect_uri points at a real
    external domain (claude.ai) that this sandboxed test run can't reach;
    we only want to inspect the Location header, never actually follow it.
    """

    def redirect_request(self, *args, **kwargs):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http(method, url, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with _OPENER.open(req, timeout=5) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        with e:
            return e.code, dict(e.headers or {}), e.read()


class MCPServerTestCase(unittest.TestCase):
    """Spins up a real mcp-remote HTTP server on 127.0.0.1:<ephemeral> per test."""

    def setUp(self):
        self.state_dir = Path(tempfile.mkdtemp(prefix="mcp-remote-test-"))
        self._env_backup = dict(os.environ)
        os.environ["MCP_OAUTH_DB"] = str(self.state_dir / "oauth.db")
        os.environ["MCP_DISABLED_PATH"] = str(self.state_dir / "mcp-disabled")
        os.environ["AUDIT_LOG_PATH"] = str(self.state_dir / "audit.jsonl")
        os.environ["VAULT"] = str(REAL_VAULT)
        os.environ["PUBLIC_BASE_URL"] = "https://mcp.example.test"
        os.environ["CF_TEAM"] = "example-team"
        os.environ["CF_AUD_AUTHORIZE"] = "aud-authorize-xyz"
        os.environ["ALLOWED_EMAIL"] = "owner@example.com"
        os.environ["MCP_CLIENT_ID"] = "static-test-client"
        os.environ["MCP_CLIENT_SECRET"] = "static-test-secret"
        os.environ.pop("CREDENTIALS_DIRECTORY", None)
        os.environ.pop("DEV", None)

        server.reset_kbmcp_cache()
        self.fake_access = FakeAccess("example-team", "aud-authorize-xyz")
        server.JWKS_FETCHER = self.fake_access.jwks
        server._JWKS_CACHE.clear()

        self.httpd = server.make_server(port=0)
        self.port = self.httpd.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        shutil.rmtree(self.state_dir, ignore_errors=True)
        os.environ.clear()
        os.environ.update(self._env_backup)

    def cf_headers(self, **overrides):
        return {"Cf-Access-Jwt-Assertion": self.fake_access.token(**overrides)}


class TestMetadata(MCPServerTestCase):
    def test_protected_resource_metadata(self):
        status, _, body = http("GET", f"{self.base}/.well-known/oauth-protected-resource")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data["resource"], "https://mcp.example.test/mcp")
        self.assertEqual(data["authorization_servers"], ["https://mcp.example.test"])

    def test_authorization_server_metadata(self):
        status, _, body = http("GET", f"{self.base}/.well-known/oauth-authorization-server")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data["issuer"], "https://mcp.example.test")
        self.assertIn("S256", data["code_challenge_methods_supported"])


class TestDCR(MCPServerTestCase):
    def test_register_valid_client(self):
        payload = json.dumps({
            "client_name": "Claude",
            "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
        }).encode()
        status, _, body = http(
            "POST", f"{self.base}/register",
            headers={"Content-Type": "application/json"}, data=payload,
        )
        self.assertEqual(status, 201)
        data = json.loads(body)
        self.assertTrue(data["client_id"].startswith("dcr-"))
        self.assertEqual(data["token_endpoint_auth_method"], "none")

    def test_register_rejects_bad_redirect_uri(self):
        payload = json.dumps({
            "client_name": "Evil",
            "redirect_uris": ["https://evil.example.com/callback"],
        }).encode()
        status, _, body = http(
            "POST", f"{self.base}/register",
            headers={"Content-Type": "application/json"}, data=payload,
        )
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"], "invalid_redirect_uri")


class TestFullOAuthFlow(MCPServerTestCase):
    def _pkce(self):
        verifier = b64url(os.urandom(32))
        challenge = sha256_b64url(verifier.encode())
        return verifier, challenge

    def _register_dcr_client(self):
        payload = json.dumps({
            "client_name": "Claude test",
            "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
        }).encode()
        status, _, body = http(
            "POST", f"{self.base}/register",
            headers={"Content-Type": "application/json"}, data=payload,
        )
        self.assertEqual(status, 201)
        return json.loads(body)["client_id"]

    def _authorize(self, client_id, verifier, challenge, redirect_uri="https://claude.ai/api/mcp/auth_callback"):
        q = (
            f"response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
            f"&code_challenge={challenge}&code_challenge_method=S256&state=xyz123"
        )
        status, _, body = http("GET", f"{self.base}/authorize?{q}", headers=self.cf_headers())
        self.assertEqual(status, 200, body)
        html = body.decode()
        request_id = re.search(r'name="request_id" value="([^"]+)"', html).group(1)
        csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)

        form = f"request_id={request_id}&csrf_token={csrf_token}&approve=yes".encode()
        status, headers, _ = http(
            "POST", f"{self.base}/authorize",
            headers={**self.cf_headers(), "Content-Type": "application/x-www-form-urlencoded"},
            data=form,
        )
        self.assertEqual(status, 302)
        location = headers["Location"]
        code = parse_qs(urlparse(location).query)["code"][0]
        state = parse_qs(urlparse(location).query)["state"][0]
        self.assertEqual(state, "xyz123")
        return code

    def _token_exchange(self, client_id, code, verifier, redirect_uri="https://claude.ai/api/mcp/auth_callback", client_secret=None):
        form = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "code_verifier": verifier,
        }
        if client_secret:
            form["client_secret"] = client_secret
        from urllib.parse import urlencode
        status, _, body = http(
            "POST", f"{self.base}/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=urlencode(form).encode(),
        )
        return status, json.loads(body)

    @unittest.skipUnless(
        _VAULT_KBMCP_AVAILABLE,
        f"vault's SYSTEM/bin/kb-mcp-server.py not found under {REAL_VAULT} "
        "(set VAULT_FOR_TESTS to a vault checkout to run this)",
    )
    def test_full_dcr_pkce_flow_and_mcp_call(self):
        client_id = self._register_dcr_client()
        verifier, challenge = self._pkce()
        code = self._authorize(client_id, verifier, challenge)
        status, tokens = self._token_exchange(client_id, code, verifier)
        self.assertEqual(status, 200, tokens)
        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)

        rpc = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
        status, _, body = http(
            "POST", f"{self.base}/mcp",
            headers={
                "Authorization": f"Bearer {tokens['access_token']}",
                "Content-Type": "application/json",
            },
            data=rpc,
        )
        self.assertEqual(status, 200)
        reply = json.loads(body)
        tool_names = {t["name"] for t in reply["result"]["tools"]}
        self.assertEqual(
            tool_names, {"kb_index", "kb_read", "kb_search", "kb_actions", "kb_capture"}
        )

    def test_static_client_flow(self):
        client_id = "static-test-client"
        verifier, challenge = self._pkce()
        code = self._authorize(client_id, verifier, challenge)
        status, tokens = self._token_exchange(client_id, code, verifier, client_secret="static-test-secret")
        self.assertEqual(status, 200, tokens)
        self.assertIn("access_token", tokens)

    def test_static_client_wrong_secret_rejected(self):
        client_id = "static-test-client"
        verifier, challenge = self._pkce()
        code = self._authorize(client_id, verifier, challenge)
        status, tokens = self._token_exchange(client_id, code, verifier, client_secret="WRONG")
        self.assertEqual(status, 401)
        self.assertEqual(tokens["error"], "invalid_client")

    def test_unknown_client_rejected(self):
        from urllib.parse import urlencode
        form = urlencode({
            "grant_type": "authorization_code", "code": "nope", "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
            "client_id": "does-not-exist", "code_verifier": "x",
        }).encode()
        status, _, body = http(
            "POST", f"{self.base}/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"}, data=form,
        )
        self.assertEqual(status, 401)
        self.assertEqual(json.loads(body)["error"], "invalid_client")

    def test_redirect_uri_rejection_at_authorize(self):
        client_id = self._register_dcr_client()
        verifier, challenge = self._pkce()
        q = (
            f"response_type=code&client_id={client_id}&redirect_uri=https://evil.example.com/cb"
            f"&code_challenge={challenge}&code_challenge_method=S256&state=xyz"
        )
        status, _, body = http("GET", f"{self.base}/authorize?{q}", headers=self.cf_headers())
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"], "invalid_redirect_uri")

    def test_authorize_without_cf_access_jwt_forbidden(self):
        status, _, body = http("GET", f"{self.base}/authorize?response_type=code&client_id=x&redirect_uri=y&code_challenge=z&code_challenge_method=S256")
        self.assertEqual(status, 403)

    def test_authorize_wrong_email_forbidden(self):
        client_id = self._register_dcr_client()
        verifier, challenge = self._pkce()
        q = (
            f"response_type=code&client_id={client_id}&redirect_uri=https://claude.ai/api/mcp/auth_callback"
            f"&code_challenge={challenge}&code_challenge_method=S256&state=xyz"
        )
        headers = {"Cf-Access-Jwt-Assertion": self.fake_access.token(email="someone-else@example.com")}
        status, _, body = http("GET", f"{self.base}/authorize?{q}", headers=headers)
        self.assertEqual(status, 403)

    def test_authorize_fails_closed_when_allowed_email_unset(self):
        # No ALLOWED_EMAIL configured => nobody is authorized, even with an
        # otherwise-valid Access JWT (and even one whose email claim is empty).
        os.environ.pop("ALLOWED_EMAIL", None)
        client_id = self._register_dcr_client()
        verifier, challenge = self._pkce()
        q = (
            f"response_type=code&client_id={client_id}&redirect_uri=https://claude.ai/api/mcp/auth_callback"
            f"&code_challenge={challenge}&code_challenge_method=S256&state=xyz"
        )
        for email in ("owner@example.com", ""):
            headers = {"Cf-Access-Jwt-Assertion": self.fake_access.token(email=email)}
            status, _, _ = http("GET", f"{self.base}/authorize?{q}", headers=headers)
            self.assertEqual(status, 403, f"email={email!r} must not be authorized when ALLOWED_EMAIL is unset")

    def test_server_has_no_default_allowed_email(self):
        os.environ.pop("ALLOWED_EMAIL", None)
        self.assertEqual(server.allowed_email(), "")

    def test_main_refuses_to_start_without_required_env(self):
        os.environ.pop("ALLOWED_EMAIL", None)
        with self.assertRaises(SystemExit) as ctx:
            server.main()
        self.assertIn("ALLOWED_EMAIL", str(ctx.exception))

    def test_refresh_token_rotation(self):
        client_id = self._register_dcr_client()
        verifier, challenge = self._pkce()
        code = self._authorize(client_id, verifier, challenge)
        status, tokens = self._token_exchange(client_id, code, verifier)
        self.assertEqual(status, 200)
        old_refresh = tokens["refresh_token"]

        from urllib.parse import urlencode
        form = urlencode({"grant_type": "refresh_token", "refresh_token": old_refresh, "client_id": client_id}).encode()
        status, _, body = http(
            "POST", f"{self.base}/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"}, data=form,
        )
        self.assertEqual(status, 200)
        new_tokens = json.loads(body)
        self.assertNotEqual(new_tokens["refresh_token"], old_refresh)

        # Reuse of the old (now-rotated) refresh token must fail, and revoke the family.
        status, _, body = http(
            "POST", f"{self.base}/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"}, data=form,
        )
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"], "invalid_grant")

        # The new access token issued in the rotation should now be revoked too (reuse detection).
        rpc = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
        status, _, _ = http(
            "POST", f"{self.base}/mcp",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}", "Content-Type": "application/json"},
            data=rpc,
        )
        self.assertEqual(status, 401)


class TestMCPAuth(MCPServerTestCase):
    def test_unauthenticated_401_with_www_authenticate(self):
        rpc = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
        status, headers, body = http(
            "POST", f"{self.base}/mcp", headers={"Content-Type": "application/json"}, data=rpc,
        )
        self.assertEqual(status, 401)
        self.assertIn("resource_metadata=", headers.get("WWW-Authenticate", ""))
        self.assertIn("oauth-protected-resource", headers["WWW-Authenticate"])

    def test_get_mcp_returns_405(self):
        status, _, _ = http("GET", f"{self.base}/mcp")
        self.assertEqual(status, 405)


class TestKillSwitch(MCPServerTestCase):
    def test_kill_switch_disables_every_route(self):
        Path(os.environ["MCP_DISABLED_PATH"]).write_text("disabled", encoding="utf-8")
        for method, path in (("GET", "/healthz"), ("GET", "/.well-known/oauth-authorization-server")):
            status, _, body = http(method, f"{self.base}{path}")
            self.assertEqual(status, 503, path)
            self.assertEqual(json.loads(body)["error"], "service disabled")


@unittest.skipUnless(
    _VAULT_KBMCP_AVAILABLE,
    f"vault's SYSTEM/bin/kb-mcp-server.py not found under {REAL_VAULT} "
    "(set VAULT_FOR_TESTS to a vault checkout to run this)",
)
class TestPathTraversal(MCPServerTestCase):
    def _authed_headers(self):
        client_id = "static-test-client"
        verifier = b64url(os.urandom(32))
        challenge = sha256_b64url(verifier.encode())
        q = (
            f"response_type=code&client_id={client_id}&redirect_uri=https://claude.ai/api/mcp/auth_callback"
            f"&code_challenge={challenge}&code_challenge_method=S256&state=s1"
        )
        status, _, body = http("GET", f"{self.base}/authorize?{q}", headers=self.cf_headers())
        html = body.decode()
        request_id = re.search(r'name="request_id" value="([^"]+)"', html).group(1)
        csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
        form = f"request_id={request_id}&csrf_token={csrf_token}&approve=yes".encode()
        status, headers, _ = http(
            "POST", f"{self.base}/authorize",
            headers={**self.cf_headers(), "Content-Type": "application/x-www-form-urlencoded"},
            data=form,
        )
        code = parse_qs(urlparse(headers["Location"]).query)["code"][0]
        from urllib.parse import urlencode
        form2 = urlencode({
            "grant_type": "authorization_code", "code": code,
            "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
            "client_id": client_id, "code_verifier": verifier,
            "client_secret": "static-test-secret",
        }).encode()
        status, _, body = http(
            "POST", f"{self.base}/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"}, data=form2,
        )
        tokens = json.loads(body)
        return {"Authorization": f"Bearer {tokens['access_token']}", "Content-Type": "application/json"}

    def test_kb_read_traversal_blocked(self):
        headers = self._authed_headers()
        rpc = json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "kb_read", "arguments": {"note": "../../../../../../etc/passwd"}},
        }).encode()
        status, _, body = http("POST", f"{self.base}/mcp", headers=headers, data=rpc)
        self.assertEqual(status, 200)  # tool errors come back as JSON-RPC results, not HTTP errors
        reply = json.loads(body)
        self.assertTrue(reply["result"]["isError"])

    def test_kb_read_legit_note_works(self):
        headers = self._authed_headers()
        rpc = json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "kb_read", "arguments": {"note": "index.md"}},
        }).encode()
        status, _, body = http("POST", f"{self.base}/mcp", headers=headers, data=rpc)
        self.assertEqual(status, 200)
        reply = json.loads(body)
        self.assertFalse(reply["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
