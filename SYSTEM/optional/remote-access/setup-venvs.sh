#!/usr/bin/env bash
# setup-venvs.sh — create the per-service virtualenvs (the only third-party
# dependency is `cryptography`, for verifying Cloudflare Access RS256 JWTs).
# Run as the service user, never as root:   ./setup-venvs.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
for d in capture-api mcp-remote; do
  echo "venv $d"
  (cd "$HERE/$d" && { [ -x .venv/bin/python3 ] || python3 -m venv .venv; } && .venv/bin/pip install -q -r requirements.txt)
done
echo "done. Systemd units use $HERE/<service>/.venv/bin/python3"
