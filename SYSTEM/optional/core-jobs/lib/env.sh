# shellcheck shell=bash
# lib/env.sh — shared bash environment for scheduled jobs, portable across a
# macOS edge host and the Linux "cloud core" (see ../README.md).
#
# Source (never execute) this near the top of a job, AFTER `set -u`:
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   . "$SCRIPT_DIR/../lib/env.sh"
#
# What it does, in order:
#   1. Loads /etc/cntxt1/core.env if present (non-secret host config: VAULT,
#      SERVICES, TZ, HC_PING_BASE, NTFY_URL) — never overrides anything already
#      set in the environment.
#   2. Requires VAULT (the vault checkout path). No default: a job that runs
#      against the wrong directory is worse than one that refuses to start.
#      SERVICES (this add-on's checkout) defaults to $HOME/services.
#   3. Loads secrets from $CREDENTIALS_DIRECTORY/<name> (systemd
#      LoadCredential) via `secret_load ENV_VAR credential-name`, plus the
#      Claude Code OAuth token if a `claude-oauth-token` credential exists.
#   4. Defines run_with_timeout, claude_p, notify_fail/notify, and small
#      GNU/BSD portability shims (portable_mtime, portable_sed_i,
#      portable_date_add_days, portable_mktemp_dir, portable_readlink_f).
#
# Callers may set CNTXT1_ENV_SKIP_SECRETS=1 before sourcing to skip step 3
# (used by tests that don't want real credentials touched).
#
# Deliberately generic: integration-specific loaders (home automation, capture
# endpoints, ...) belong in the job that needs them, built on `secret_load`.

# --- 1) host config overlay ----------------------------------------------------
: "${HOME:?lib/env.sh: HOME must be set}"
_cntxt1_env_file="${CNTXT1_ENV_FILE:-/etc/cntxt1/core.env}"
if [ -f "$_cntxt1_env_file" ]; then
  _cntxt1_prior_vault="${VAULT:-}"
  _cntxt1_prior_services="${SERVICES:-}"
  set -a
  # shellcheck disable=SC1090
  . "$_cntxt1_env_file"
  set +a
  # Don't let the file clobber a caller's explicit override.
  [ -n "$_cntxt1_prior_vault" ] && VAULT="$_cntxt1_prior_vault"
  [ -n "$_cntxt1_prior_services" ] && SERVICES="$_cntxt1_prior_services"
  unset _cntxt1_prior_vault _cntxt1_prior_services
fi
unset _cntxt1_env_file

# --- 2) VAULT (required) / SERVICES --------------------------------------------
: "${VAULT:?lib/env.sh: VAULT must be set (vault checkout path — see /etc/cntxt1/core.env)}"
: "${SERVICES:="$HOME/services"}"
export VAULT SERVICES

# --- 3) Secrets ------------------------------------------------------------------
# systemd LoadCredential drops secret files in $CREDENTIALS_DIRECTORY.
# secret_path NAME     -> prints the credential file path (exit 1 if absent)
# secret_load VAR NAME -> exports VAR with the credential's contents (exit 1 if absent)
secret_path() {
  if [ -n "${CREDENTIALS_DIRECTORY:-}" ] && [ -f "$CREDENTIALS_DIRECTORY/$1" ]; then
    printf '%s' "$CREDENTIALS_DIRECTORY/$1"
    return 0
  fi
  return 1
}

secret_load() {  # $1=ENV_VAR $2=credential-name
  local _f
  _f="$(secret_path "$2")" || return 1
  printf -v "$1" '%s' "$(cat "$_f")"
  export "${1?}"
}

if [ "${CNTXT1_ENV_SKIP_SECRETS:-0}" != 1 ]; then
  # Claude Code OAuth token (headless `claude -p`): the credential, else a
  # dotenv-style file that exports CLAUDE_CODE_OAUTH_TOKEN (Mac hosts).
  if ! secret_load CLAUDE_CODE_OAUTH_TOKEN claude-oauth-token \
     && [ -f "$HOME/.config/claude/oauth-token.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$HOME/.config/claude/oauth-token.env"
    set +a
  fi
fi

# --- 4a) run_with_timeout ----------------------------------------------------
# Bound a command to a hard wall-clock limit, killing its whole process group
# (not just the direct child). GNU coreutils' timeout(1) does this natively
# and is present on Ubuntu by default; macOS has no timeout(1) unless
# `brew install coreutils` (gtimeout) was run, so fall back to the
# process-group implementation used by earlier job scripts /
# other job scripts (keep one copy here — do not re-copy into callers).
run_with_timeout() {
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout --kill-after=1 "$secs" "$@"
    return $?
  fi
  if command -v gtimeout >/dev/null 2>&1; then
    gtimeout --kill-after=1 "$secs" "$@"
    return $?
  fi
  ( set -m
    "$@" &
    local pid=$!
    ( sleep "$secs"; kill -TERM -- -$pid 2>/dev/null; sleep 1; kill -KILL -- -$pid 2>/dev/null ) &
    local watcher=$!
    wait "$pid" 2>/dev/null
    local status=$?
    kill "$watcher" 2>/dev/null
    exit $status
  )
}

# --- 4b) claude_p -------------------------------------------------------------
# Wrap `claude -p` with a hard wall-clock timeout (default 300s; pass a
# different budget as $1 when the prompt/tool budget needs more). Everything
# after the (optional leading numeric) timeout is passed straight to
# `claude -p`. Relies on CLAUDE_CODE_OAUTH_TOKEN already being in the
# environment (set in step 3 above, or by the caller).
claude_p() {
  local secs="${CLAUDE_P_TIMEOUT:-300}"
  case "${1:-}" in
    ''|*[!0-9]*) : ;;   # not a bare integer — treat all args as the prompt/flags
    *) secs="$1"; shift ;;
  esac
  run_with_timeout "$secs" claude -p "$@"
}

# --- 4c) notify -----------------------------------------------------------
# Cross-platform "tell the owner" — macOS uses osascript (local GUI notification);
# Linux (a headless host has no GUI session) posts to ntfy (NTFY_URL from
# core.env). Never includes secrets in $2/$3 — callers must pass
# secret-free text. Silent best-effort: a notify failure must never fail
# the calling job.
notify() {  # $1=title $2=message
  local title="$1" message="$2"
  if [ "$(uname)" = Darwin ]; then
    command -v osascript >/dev/null 2>&1 || return 0
    osascript -e "display notification $(printf '%q' "$message") with title $(printf '%q' "$title")" \
      >/dev/null 2>&1 || true
  elif [ -n "${NTFY_URL:-}" ]; then
    run_with_timeout 8 curl -fsS -m 6 \
      -H "Title: $title" \
      -d "$message" \
      "$NTFY_URL" >/dev/null 2>&1 || true
  fi
  return 0
}

# notify_fail: the standard "a job failed" alert. jobwrap (bin/jobwrap) already
# pings healthchecks + alerts on nonzero exit for the job as a whole — this is
# for a job that wants to surface a SPECIFIC failure reason inline (e.g. "gws
# auth dead") in addition to just exiting nonzero.
notify_fail() {  # $1=job-name $2=reason
  notify "cntxt1: $1 failed" "${2:-see logs}"
}

# --- 4d) portability shims ----------------------------------------------------
# GNU vs BSD date/sed/stat/mktemp/readlink differ enough between Ubuntu and
# macOS that call sites need a single portable spelling.

# portable_mtime PATH — file modification time as a Unix epoch integer, or
# empty if the file doesn't exist. (BSD: stat -f %m · GNU: stat -c %Y)
#
# Branched on `uname`, not `||`-chained: GNU stat's `-f` flag means
# "report on the filesystem", not "use this format string" — `stat -f %m`
# on Linux exits 0 and prints the literal, non-numeric text "m" instead of
# failing, so a `stat -f %m || stat -c %Y` fallback never reaches the GNU
# spelling and callers doing integer comparisons on the result silently
# break (a real bug we hit).
portable_mtime() {
  case "$(uname)" in
    Darwin|*BSD)
      stat -f %m "$1" 2>/dev/null ;;
    *)
      stat -c %Y "$1" 2>/dev/null ;;
  esac
}

# portable_sed_i SED_ARGS... FILE — in-place edit that works with both BSD
# sed (requires -i '') and GNU sed (bare -i). Usage mirrors `sed -i`:
#   portable_sed_i 's/foo/bar/' file.txt
portable_sed_i() {
  if sed --version >/dev/null 2>&1; then   # GNU sed
    sed -i "$@"
  else                                      # BSD/macOS sed
    sed -i '' "$@"
  fi
}

# portable_date_add_days N [FROM_DATE] — YYYY-MM-DD N days after FROM_DATE
# (default today). N may be negative. (BSD: date -v[+-]Nd · GNU: date -d
# "FROM N days")
portable_date_add_days() {
  local n="$1" from="${2:-}" sign="+"
  case "$n" in -*) sign="-"; n="${n#-}" ;; esac
  if date -v+1d +%F >/dev/null 2>&1; then   # BSD date
    if [ -n "$from" ]; then
      date -j -f '%Y-%m-%d' -v"${sign}${n}"d "$from" +%F
    else
      date -v"${sign}${n}"d +%F
    fi
  else                                        # GNU date
    date -d "${from:-today} ${sign}${n} days" +%F
  fi
}

# portable_mktemp_dir — mktemp -d works identically on both platforms in
# practice, but macOS mktemp requires a template with trailing X's for some
# flags; this wrapper is the one safe spelling to use everywhere.
portable_mktemp_dir() {
  mktemp -d "${TMPDIR:-/tmp}/cntxt1.XXXXXX"
}

# portable_readlink_f PATH — resolve a path to its canonical absolute form,
# following symlinks (needed when a script runs through a symlink, so $0's
# dirname is the symlink's directory, not the real one). GNU readlink -f is native; macOS readlink has no -f, so walk
# the link chain by hand.
portable_readlink_f() {
  if readlink -f "$1" >/dev/null 2>&1; then
    readlink -f "$1"
    return 0
  fi
  local target="$1" dir base
  while [ -L "$target" ]; do
    dir="$(cd "$(dirname "$target")" && pwd)"
    target="$(readlink "$target")"
    case "$target" in /*) ;; *) target="$dir/$target" ;; esac
  done
  dir="$(cd "$(dirname "$target")" && pwd)"
  base="$(basename "$target")"
  printf '%s/%s\n' "$dir" "$base"
}
