#!/usr/bin/env bash
# run.sh — thin shim for gardener.py. Runs on the Linux cloud core (jobwrap/systemd)
# and on macOS (manual testing). Locking, guardrails, and stage logic all
# live in gardener.py (pure Python stdlib, fcntl-based lock — portable to
# both platforms without depending on the Linux-only `flock(1)` binary).
#
# Usage: gardener/run.sh [--mode propose|apply] [--stage all|regen|compile|lint|inbox|actions|digest] [--max-llm-calls N]
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON="${GARDENER_PYTHON:-python3}"
exec "$PYTHON" "$DIR/gardener.py" "$@"
