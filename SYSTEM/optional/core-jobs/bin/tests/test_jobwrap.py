#!/usr/bin/env python3
"""Tests for bin/jobwrap. No network access: HC/NTFY endpoints are local
http.server instances. Run: python3 -m unittest discover -s bin/tests"""
import importlib.machinery
import importlib.util
import os
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
JOBWRAP_PATH = os.path.join(HERE, "..", "jobwrap")

spec = importlib.util.spec_from_loader(
    "jobwrap", importlib.machinery.SourceFileLoader("jobwrap", JOBWRAP_PATH)
)
jobwrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jobwrap)


class RecordingHandler(BaseHTTPRequestHandler):
    """Records every request (method, path, body) onto the class's server."""

    def _record(self, method):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""
        self.server.requests.append(
            {
                "method": method,
                "path": self.path,
                "body": body,
                "headers": dict(self.headers.items()),
            }
        )
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self._record("GET")

    def do_POST(self):
        self._record("POST")

    def log_message(self, fmt, *args):  # noqa: A003 -- silence test noise
        pass


def start_server():
    server = HTTPServer(("127.0.0.1", 0), RecordingHandler)
    server.requests = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


class ScrubTests(unittest.TestCase):
    def test_bearer_token_redacted(self):
        out = jobwrap.scrub("auth: Bearer abc123.def456-ghi")
        self.assertNotIn("abc123", out)
        self.assertIn("[REDACTED]", out)

    def test_jwt_redacted(self):
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        out = jobwrap.scrub(f"token={jwt}")
        self.assertNotIn(jwt, out)

    def test_long_hex_redacted(self):
        hexstr = "a" * 40
        out = jobwrap.scrub(f"key={hexstr}")
        self.assertNotIn(hexstr, out)

    def test_ordinary_text_untouched(self):
        text = "daily-plan: wrote 00 daily/2026-09-28.md ok"
        self.assertEqual(jobwrap.scrub(text), text)


class LockTests(unittest.TestCase):
    def test_second_lock_fails_while_first_held(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["TMPDIR"] = tmp
            # Force fallback path (no /run/cntxt1 on most dev machines is fine
            # too, but be explicit and portable across CI containers).
            path = os.path.join(tmp, "cntxt1-testjob.lock")
            fh1 = open(path, "a+")
            import fcntl

            fcntl.flock(fh1.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fh2 = open(path, "a+")
            with self.assertRaises(OSError):
                fcntl.flock(fh2.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fh1.close()
            fh2.close()

    def test_acquire_lock_reenters_after_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["TMPDIR"] = tmp
            job = "reentrant-job"
            lock1 = jobwrap.acquire_lock(job)
            self.assertIsNotNone(lock1)
            import fcntl

            fcntl.flock(lock1.fileno(), fcntl.LOCK_UN)
            lock1.close()
            lock2 = jobwrap.acquire_lock(job)
            self.assertIsNotNone(lock2)
            lock2.close()


class RunChildTests(unittest.TestCase):
    def test_success_exit_code_and_output_captured(self):
        code, tail = jobwrap.run_child(
            [sys.executable, "-c", "print('hello-jobwrap')"], timeout=10
        )
        self.assertEqual(code, 0)
        self.assertIn(b"hello-jobwrap", tail)

    def test_nonzero_exit_propagates(self):
        code, _ = jobwrap.run_child([sys.executable, "-c", "import sys; sys.exit(7)"], timeout=10)
        self.assertEqual(code, 7)

    def test_timeout_kills_and_returns_124(self):
        start = time.time()
        code, _ = jobwrap.run_child(
            [sys.executable, "-c", "import time; time.sleep(30)"], timeout=1
        )
        elapsed = time.time() - start
        self.assertEqual(code, jobwrap.TIMEOUT_EXIT_CODE)
        self.assertLess(elapsed, 15)  # well under the 10s grace + slack

    def test_tail_buffer_capped(self):
        code, tail = jobwrap.run_child(
            [sys.executable, "-c", "print('x' * 20000)"], timeout=10
        )
        self.assertEqual(code, 0)
        self.assertLessEqual(len(tail), jobwrap.TAIL_BYTES + 1)  # +1 for trailing newline slack


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.server, self.thread = start_server()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)

    def test_hc_start_pings_slug_with_create(self):
        jobwrap.hc_start(self.base, "daily-plan")
        time.sleep(0.2)
        self.assertEqual(len(self.server.requests), 1)
        req = self.server.requests[0]
        self.assertEqual(req["method"], "GET")
        self.assertIn("/daily-plan/start", req["path"])
        self.assertIn("create=1", req["path"])

    def test_hc_end_posts_scrubbed_tail(self):
        jobwrap.hc_end(self.base, "daily-plan", 0, b"Bearer supersecrettoken1234567890 ok")
        time.sleep(0.2)
        self.assertEqual(len(self.server.requests), 1)
        req = self.server.requests[0]
        self.assertEqual(req["method"], "POST")
        self.assertIn("/daily-plan/0", req["path"])
        self.assertNotIn(b"supersecrettoken1234567890", req["body"])

    def test_ntfy_fail_sends_priority_high_and_no_secrets(self):
        jobwrap.ntfy_fail(self.base, "vps1", "backup", 1)
        time.sleep(0.2)
        self.assertEqual(len(self.server.requests), 1)
        req = self.server.requests[0]
        self.assertEqual(req["method"], "POST")
        self.assertEqual(req["headers"].get("Priority"), "high")
        self.assertIn(b"vps1 backup failed (exit 1)", req["body"])

    def test_network_failure_never_raises(self):
        # Port 1 should refuse the connection near-instantly.
        try:
            jobwrap.hc_start("http://127.0.0.1:1", "job")
            jobwrap.ntfy_fail("http://127.0.0.1:1", "host", "job", 1)
        except Exception as exc:  # noqa: BLE001
            self.fail(f"network helpers must never raise: {exc}")

    def test_no_hc_base_is_noop(self):
        jobwrap.hc_start(None, "job")
        jobwrap.hc_end(None, "job", 0, b"output")
        jobwrap.ntfy_fail(None, "host", "job", 1)
        # No exception, and (since no server was hit) nothing to assert further.


class ArgParseTests(unittest.TestCase):
    def test_parses_job_timeout_and_cmd(self):
        job, timeout, no_hc, cmd = jobwrap.parse_args(
            ["daily-plan", "--timeout", "300", "--", "echo", "hi"]
        )
        self.assertEqual(job, "daily-plan")
        self.assertEqual(timeout, 300.0)
        self.assertFalse(no_hc)
        self.assertEqual(cmd, ["echo", "hi"])

    def test_no_hc_flag(self):
        job, timeout, no_hc, cmd = jobwrap.parse_args(["job", "--no-hc", "--", "true"])
        self.assertTrue(no_hc)

    def test_missing_command_raises(self):
        with self.assertRaises(SystemExit):
            jobwrap.parse_args(["job", "--timeout", "10"])

    def test_no_args_raises(self):
        with self.assertRaises(SystemExit):
            jobwrap.parse_args([])


class EndToEndTests(unittest.TestCase):
    """Drive main() through a subprocess so the lock-already-running and
    full ping sequence get exercised end to end."""

    def setUp(self):
        self.server, self.thread = start_server()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.tmp = tempfile.TemporaryDirectory()
        self.env = dict(os.environ)
        self.env["TMPDIR"] = self.tmp.name
        self.env["HC_PING_BASE"] = self.base
        self.env["NTFY_URL"] = self.base
        self.env.pop("HOME_HC_DISABLE", None)

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def _run(self, args):
        import subprocess

        return subprocess.run(
            [sys.executable, JOBWRAP_PATH] + args,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_successful_job_pings_start_and_zero(self):
        result = self._run(["e2e-ok", "--", sys.executable, "-c", "print('done')"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("done", result.stdout)
        time.sleep(0.2)
        paths = [r["path"] for r in self.server.requests]
        self.assertTrue(any("/e2e-ok/start" in p for p in paths))
        self.assertTrue(any("/e2e-ok/0" in p for p in paths))

    def test_failing_job_pings_ntfy(self):
        result = self._run(
            ["e2e-fail", "--", sys.executable, "-c", "import sys; sys.exit(3)"]
        )
        self.assertEqual(result.returncode, 3)
        time.sleep(0.2)
        paths_and_bodies = [(r["path"], r["body"]) for r in self.server.requests]
        self.assertTrue(any("/e2e-fail/3" in p for p, _ in paths_and_bodies))
        self.assertTrue(any(b"failed (exit 3)" in b for _, b in paths_and_bodies))

    def test_no_hc_flag_skips_all_network(self):
        result = self._run(
            ["e2e-nohc", "--no-hc", "--", sys.executable, "-c", "import sys; sys.exit(1)"]
        )
        self.assertEqual(result.returncode, 1)
        time.sleep(0.2)
        self.assertEqual(len(self.server.requests), 0)


if __name__ == "__main__":
    unittest.main()
