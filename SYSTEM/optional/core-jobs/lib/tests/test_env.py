"""lib/tests/test_env.py — exercises lib/env.py: required VAULT, SERVICES default,
secret() credential loading (systemd credential dir vs dotenv fallback), and
run_with_timeout. No real secrets or network.
"""
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import env  # noqa: E402


class _EnvCase(unittest.TestCase):
    def setUp(self):
        self._orig_environ = dict(os.environ)
        for k in ("VAULT", "SERVICES", "CREDENTIALS_DIRECTORY"):
            os.environ.pop(k, None)
        env._core_env_cache = {}  # pretend /etc/cntxt1/core.env is absent

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_environ)
        env._core_env_cache = None


class VaultServicesTests(_EnvCase):
    def test_vault_is_required(self):
        with self.assertRaises(KeyError):
            env.vault()

    def test_services_defaults_under_home(self):
        with tempfile.TemporaryDirectory() as home:
            os.environ["HOME"] = home
            self.assertEqual(env.services(), os.path.join(home, "services"))

    def test_explicit_env_wins(self):
        os.environ["VAULT"] = "/custom/vault"
        os.environ["SERVICES"] = "/custom/services"
        self.assertEqual(env.vault(), "/custom/vault")
        self.assertEqual(env.services(), "/custom/services")

    def test_core_env_supplies_vault(self):
        env._core_env_cache = {"VAULT": "/from/core-env"}
        self.assertEqual(env.vault(), "/from/core-env")


class SecretTests(_EnvCase):
    def test_credentials_directory_wins(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "my-token"), "w") as f:
                f.write("cred-token\n")
            os.environ["CREDENTIALS_DIRECTORY"] = d
            self.assertEqual(env.secret("my-token"), "cred-token")

    def test_legacy_file_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            legacy = os.path.join(d, "svc.env")
            with open(legacy, "w") as f:
                f.write("export SVC_URL=http://svc.example:8123\nSVC_TOKEN=legacy-tok\n")
            got = env.secret("svc-token", legacy_file=legacy, legacy_keys=["SVC_URL", "SVC_TOKEN"])
            self.assertEqual(got, {"SVC_URL": "http://svc.example:8123", "SVC_TOKEN": "legacy-tok"})

    def test_missing_returns_none(self):
        self.assertIsNone(env.secret("nope"))


class RunWithTimeoutTests(unittest.TestCase):
    def test_fast_command_passes_through(self):
        result = env.run_with_timeout(5, ["echo", "hi"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "hi")

    def test_slow_command_times_out(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            env.run_with_timeout(1, ["sleep", "10"])


if __name__ == "__main__":
    unittest.main()
