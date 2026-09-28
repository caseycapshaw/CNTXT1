"""lib/env.py — shared Python environment for scheduled jobs, portable across
a macOS edge host and the Linux "cloud core".

Mirrors lib/env.sh. Import (never copy) this:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
    import env as cntxt1_env

or, for scripts already next to lib/, just `import env`.

What it provides:
  - vault() -> str                          VAULT path (REQUIRED — $VAULT or
                                            /etc/cntxt1/core.env; raises KeyError
                                            if neither is set, fail closed).
  - services() -> str                       SERVICES path, default $HOME/services.
  - load_core_env() -> dict                 parsed /etc/cntxt1/core.env (or {}).
  - secret(name, legacy_file=None,
           legacy_keys=None) -> dict|str    credential loader: $CREDENTIALS_DIRECTORY/<name>
                                            (systemd LoadCredential) else a
                                            dotenv-style file on hosts without
                                            systemd.
  - run_with_timeout(secs, argv) -> CompletedProcess   subprocess with a hard
                                            wall-clock timeout (kills the
                                            process group on expiry).
"""
from __future__ import annotations

import os
import signal
import subprocess


def _read_dotenv(path):
    """Parse a simple `export KEY=value` / `KEY=value` file. Never raises."""
    env = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    line = line[len("export "):]
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("'\"")
    except FileNotFoundError:
        pass
    return env


_CORE_ENV_FILE = os.environ.get("CNTXT1_ENV_FILE", "/etc/cntxt1/core.env")
_core_env_cache = None


def load_core_env():
    """Parsed /etc/cntxt1/core.env (non-secret host config), cached. {} if absent."""
    global _core_env_cache
    if _core_env_cache is None:
        _core_env_cache = _read_dotenv(_CORE_ENV_FILE)
    return _core_env_cache


def vault():
    """VAULT path: explicit $VAULT env wins, else core.env. No default — raises
    KeyError when unset so a job never silently runs against the wrong tree."""
    if os.environ.get("VAULT"):
        return os.environ["VAULT"]
    hv = load_core_env().get("VAULT")
    if hv:
        return hv
    raise KeyError("VAULT not set (expected in the environment or /etc/cntxt1/core.env)")


def services():
    """SERVICES path: explicit $SERVICES env wins, else core.env, else $HOME/services."""
    if os.environ.get("SERVICES"):
        return os.environ["SERVICES"]
    hs = load_core_env().get("SERVICES")
    if hs:
        return hs
    return os.path.join(os.path.expanduser("~"), "services")


def credentials_dir():
    return os.environ.get("CREDENTIALS_DIRECTORY")


def secret(name, legacy_file=None, legacy_keys=None):
    """Load a secret two ways:
      1. systemd: $CREDENTIALS_DIRECTORY/<name> (systemd LoadCredential) — a bare
         token file; returned stripped as a string.
      2. Fallback for hosts without systemd: `legacy_file` (a dotenv-style
         file, e.g. ~/.config/myservice/.env) — if `legacy_keys` is given, returns a dict of
         just those keys; otherwise returns the whole parsed dict.

    Returns None if neither source is available.
    """
    cred_dir = credentials_dir()
    if cred_dir:
        path = os.path.join(cred_dir, name)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                return f.read().strip()
    if legacy_file and os.path.isfile(os.path.expanduser(legacy_file)):
        parsed = _read_dotenv(os.path.expanduser(legacy_file))
        if legacy_keys:
            return {k: parsed.get(k) for k in legacy_keys}
        return parsed
    return None


def run_with_timeout(secs, argv, **kwargs):
    """subprocess.run(argv, **kwargs) bounded by a hard wall-clock timeout,
    killing the whole process group on expiry (mirrors lib/env.sh's bash
    run_with_timeout — a plain subprocess timeout only kills the direct
    child, which can leave orphaned grandchildren behind, e.g. ssh -> a
    hung remote command)."""
    kwargs.setdefault("start_new_session", True)
    try:
        return subprocess.run(argv, timeout=secs, **kwargs)
    except subprocess.TimeoutExpired:
        raise
