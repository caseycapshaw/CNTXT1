#!/usr/bin/env python3
"""Unit tests for capture-api. No network access.

Vault safety: capture-writing tests NEVER touch a real vault — each test
that writes copies a minimal vault fixture (raw/, attachments/, SYSTEM/) into
a temp dir and points VAULT at that. Auth/parsing-only tests don't need a
vault at all.
"""
import base64
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path

try:
    import cryptography  # noqa: F401
except ImportError:
    raise unittest.SkipTest("capture-api tests skipped: 'cryptography' not installed (pip install cryptography)")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app  # noqa: E402

from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import padding, rsa  # noqa: E402
from cryptography.hazmat.primitives import hashes  # noqa: E402


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_rsa_keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key, key.public_key()


def jwk_from_public_key(pub, kid):
    numbers = pub.public_numbers()
    n = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    e = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    return {"kty": "RSA", "kid": kid, "n": b64url(n), "e": b64url(e)}


def sign_jwt(private_key, header, payload):
    header_b64 = b64url(json.dumps(header).encode())
    payload_b64 = b64url(json.dumps(payload).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    sig = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f"{header_b64}.{payload_b64}.{b64url(sig)}"


class FakeHeaders(dict):
    def get(self, key, default=None):
        for k, v in self.items():
            if k.lower() == key.lower():
                return v
        return default


class VaultFixture:
    """A temp-dir vault copy (never the real vault) with raw/ + SYSTEM/log.md."""

    def __enter__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="capture-api-test-vault-"))
        (self.dir / "raw").mkdir()
        (self.dir / "attachments").mkdir()
        (self.dir / "SYSTEM").mkdir()
        (self.dir / "SYSTEM" / "log.md").write_text("# log\n", encoding="utf-8")
        self._old_vault = os.environ.get("VAULT")
        os.environ["VAULT"] = str(self.dir)
        return self.dir

    def __exit__(self, *exc):
        if self._old_vault is None:
            os.environ.pop("VAULT", None)
        else:
            os.environ["VAULT"] = self._old_vault
        shutil.rmtree(self.dir, ignore_errors=True)


class TestSlugAndDest(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(app.slugify("Boat Trailer VRS!!"), "boat-trailer-vrs")
        self.assertEqual(app.slugify(""), "capture")

    def test_collision_suffix(self):
        with VaultFixture() as vault:
            date_str = "2026-09-28"
            p1 = app.dest_path(vault, date_str, "test-note")
            p1.write_text("x", encoding="utf-8")
            p2 = app.dest_path(vault, date_str, "test-note")
            self.assertNotEqual(p1, p2)
            self.assertEqual(p2.name, "2026-09-28-test-note-2.md")
            p2.write_text("x", encoding="utf-8")
            p3 = app.dest_path(vault, date_str, "test-note")
            self.assertEqual(p3.name, "2026-09-28-test-note-3.md")


class TestCaptureWrite(unittest.TestCase):
    def test_write_note_and_log(self):
        with VaultFixture() as vault:
            data = {"text": "Test note body", "title": "My Test Note", "source": "manual"}
            date_str = "2026-09-28"
            title = app.make_title(data)
            slug = app.slugify(title)
            dest = app.dest_path(vault, date_str, slug)
            body = app.build_body(date_str, title, data)
            dest.write_text(body, encoding="utf-8")
            app.append_kb_log(vault, date_str, str(dest.relative_to(vault)), "manual")

            self.assertTrue(dest.exists())
            text = dest.read_text(encoding="utf-8")
            self.assertIn("# 2026-09-28 — My Test Note", text)
            self.assertIn("Test note body", text)
            self.assertIn("Source: capture-api (manual)", text)

            log_text = (vault / "SYSTEM" / "log.md").read_text(encoding="utf-8")
            self.assertIn("capture-api", log_text)
            self.assertIn("#auto", log_text)

    def test_never_overwrites(self):
        with VaultFixture() as vault:
            date_str = "2026-09-28"
            dest1 = app.dest_path(vault, date_str, "dup")
            dest1.write_text("first", encoding="utf-8")
            dest2 = app.dest_path(vault, date_str, "dup")
            dest2.write_text("second", encoding="utf-8")
            self.assertEqual(dest1.read_text(encoding="utf-8"), "first")
            self.assertEqual(dest2.read_text(encoding="utf-8"), "second")


class TestMultipart(unittest.TestCase):
    def test_parse_multipart_image_and_fields(self):
        boundary = "----testboundary123"
        image_bytes = b"\xff\xd8\xff\xe0fakejpeg"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="title"\r\n\r\n'
            f"Photo title\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="photo.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()
        fields, image = app.parse_multipart(
            f"multipart/form-data; boundary={boundary}", body
        )
        self.assertEqual(fields["title"], "Photo title")
        self.assertIsNotNone(image)
        filename, ctype, payload = image
        self.assertEqual(filename, "photo.jpg")
        self.assertEqual(ctype, "image/jpeg")
        self.assertEqual(payload, image_bytes)


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.key, self.pub = make_rsa_keypair()
        self.kid = "test-kid-1"
        self.jwks = {"keys": [jwk_from_public_key(self.pub, self.kid)]}
        self._env_backup = dict(os.environ)
        os.environ["CF_TEAM"] = "example-team"
        os.environ["CF_AUD_CAPTURE"] = "aud-capture-123"
        app._JWKS_CACHE.clear()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env_backup)

    def fake_fetcher(self, cf_team):
        return self.jwks

    def _token(self, **overrides):
        now = int(time.time())
        payload = {
            "iss": "https://example-team.cloudflareaccess.com",
            "aud": "aud-capture-123",
            "email": "owner@example.com",
            "exp": now + 3600,
            "iat": now,
        }
        payload.update(overrides)
        return sign_jwt(self.key, {"alg": "RS256", "kid": self.kid}, payload)

    def test_valid_cf_jwt_authorizes(self):
        headers = FakeHeaders({"Cf-Access-Jwt-Assertion": self._token()})
        ok, client = app.authorize_request(headers, jwks_fetcher=self.fake_fetcher)
        self.assertTrue(ok)
        self.assertEqual(client, "owner@example.com")

    def test_expired_jwt_rejected(self):
        token = self._token(exp=int(time.time()) - 1000)
        headers = FakeHeaders({"Cf-Access-Jwt-Assertion": token})
        ok, reason = app.authorize_request(headers, jwks_fetcher=self.fake_fetcher)
        self.assertFalse(ok)
        self.assertIn("expired", reason)

    def test_wrong_audience_rejected(self):
        token = self._token(aud="some-other-aud")
        headers = FakeHeaders({"Cf-Access-Jwt-Assertion": token})
        ok, reason = app.authorize_request(headers, jwks_fetcher=self.fake_fetcher)
        self.assertFalse(ok)
        self.assertIn("mismatch", reason)

    def test_wrong_issuer_rejected(self):
        token = self._token(iss="https://evil-team.cloudflareaccess.com")
        headers = FakeHeaders({"Cf-Access-Jwt-Assertion": token})
        ok, reason = app.authorize_request(headers, jwks_fetcher=self.fake_fetcher)
        self.assertFalse(ok)
        self.assertIn("issuer", reason)

    def test_tampered_signature_rejected(self):
        token = self._token()
        h, p, s = token.split(".")
        bad_sig = base64.urlsafe_b64encode(b"garbage-signature-bytes").rstrip(b"=").decode()
        tampered = f"{h}.{p}.{bad_sig}"
        headers = FakeHeaders({"Cf-Access-Jwt-Assertion": tampered})
        ok, reason = app.authorize_request(headers, jwks_fetcher=self.fake_fetcher)
        self.assertFalse(ok)

    def test_bearer_lan_token_authorizes(self):
        os.environ["CAPTURE_TOKEN"] = "supersecret-lan-token"
        headers = FakeHeaders({"Authorization": "Bearer supersecret-lan-token"})
        ok, client = app.authorize_request(headers)
        self.assertTrue(ok)
        self.assertEqual(client, "lan-token")

    def test_bearer_wrong_token_rejected(self):
        os.environ["CAPTURE_TOKEN"] = "supersecret-lan-token"
        headers = FakeHeaders({"Authorization": "Bearer wrong"})
        ok, reason = app.authorize_request(headers)
        self.assertFalse(ok)

    def test_no_credentials_rejected(self):
        headers = FakeHeaders({})
        ok, reason = app.authorize_request(headers)
        self.assertFalse(ok)

    def test_credentials_directory_file_used(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "capture-token").write_text("from-credential-file\n", encoding="utf-8")
            os.environ["CREDENTIALS_DIRECTORY"] = d
            os.environ.pop("CAPTURE_TOKEN", None)
            headers = FakeHeaders({"Authorization": "Bearer from-credential-file"})
            ok, client = app.authorize_request(headers)
            self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
