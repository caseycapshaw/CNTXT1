#!/usr/bin/env bash
# lib/tests/test-env.sh — exercises lib/env.sh: VAULT/SERVICES defaults,
# core.env overlay, required VAULT, secret loading ($CREDENTIALS_DIRECTORY
# vs the dotenv fallback), run_with_timeout, claude_p's timeout arg parsing, and the
# portable_* shims. No real secrets or network involved.
# shellcheck disable=SC2016,SC2034  # eval-style check() strings; vars used in eval
set -u
LIB="$(cd "$(dirname "$0")/.." && pwd)/env.sh"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "ok   - $1"; }
bad()  { FAIL=$((FAIL+1)); echo "FAIL - $1"; }
check(){ if eval "$2"; then ok "$1"; else bad "$1"; fi }

TMP="$(mktemp -d)"
export CNTXT1_ENV_FILE=/nonexistent   # hermetic: never read a real /etc/cntxt1/core.env

# --- T1: VAULT is required — sourcing without it fails closed ---
out="$(HOME="$TMP/home1" CNTXT1_ENV_SKIP_SECRETS=1 env -u VAULT bash -c '. "'"$LIB"'"; echo sourced' 2>&1)"; rc=$?
check "sourcing without VAULT fails" '[ "$rc" -ne 0 ] && ! printf %s "$out" | grep -q "^sourced$"'

# --- T2: explicit VAULT/SERVICES win; SERVICES defaults under $HOME ---
out="$(HOME="$TMP/home1" VAULT="/custom/vault" SERVICES="/custom/services" CNTXT1_ENV_SKIP_SECRETS=1 \
  bash -c '. "'"$LIB"'"; echo "$VAULT|$SERVICES"')"
check "explicit VAULT/SERVICES override" '[ "$out" = "/custom/vault|/custom/services" ]'
out="$(HOME="$TMP/home1" VAULT="/custom/vault" CNTXT1_ENV_SKIP_SECRETS=1 env -u SERVICES bash -c '. "'"$LIB"'"; echo "$SERVICES"')"
check "SERVICES defaults under \$HOME" '[ "$out" = "'"$TMP"'/home1/services" ]'

# --- T2b: core.env overlay supplies VAULT; an explicit env var still wins ---
printf 'VAULT=/from/core-env\nTZ=UTC\n' > "$TMP/core.env"
out="$(HOME="$TMP/home1" CNTXT1_ENV_FILE="$TMP/core.env" CNTXT1_ENV_SKIP_SECRETS=1 env -u VAULT bash -c '. "'"$LIB"'"; echo "$VAULT"')"
check "core.env supplies VAULT" '[ "$out" = "/from/core-env" ]'
out="$(HOME="$TMP/home1" VAULT=/explicit CNTXT1_ENV_FILE="$TMP/core.env" CNTXT1_ENV_SKIP_SECRETS=1 bash -c '. "'"$LIB"'"; echo "$VAULT"')"
check "explicit VAULT beats core.env" '[ "$out" = "/explicit" ]'

# --- T3: run_with_timeout kills a hanging command within budget ---
start="$(date +%s)"
HOME="$TMP/home1" VAULT=/v CNTXT1_ENV_SKIP_SECRETS=1 bash -c '. "'"$LIB"'"; run_with_timeout 1 sleep 10' >/dev/null 2>&1
rc=$?
elapsed=$(( $(date +%s) - start ))
check "run_with_timeout kills within ~1-3s" '[ "$elapsed" -le 4 ]'
check "run_with_timeout returns nonzero on timeout" '[ "$rc" -ne 0 ]'

# --- T4: run_with_timeout passes through a fast command's exit + output ---
out="$(HOME="$TMP/home1" VAULT=/v CNTXT1_ENV_SKIP_SECRETS=1 bash -c '. "'"$LIB"'"; run_with_timeout 5 echo hi')"
check "run_with_timeout passes through output" '[ "$out" = "hi" ]'

# --- T5: claude_p's leading-integer arg is consumed as the timeout, not
#     forwarded to `claude` (stub `claude` on PATH records its argv). ---
mkdir -p "$TMP/bin"
cat > "$TMP/bin/claude" <<'FAKE'
#!/usr/bin/env bash
printf '%s\n' "$*" > "${CLAUDE_ARGV_LOG:?}"
FAKE
chmod +x "$TMP/bin/claude"
CLAUDE_ARGV_LOG="$TMP/argv.log" HOME="$TMP/home1" VAULT=/v PATH="$TMP/bin:$PATH" CNTXT1_ENV_SKIP_SECRETS=1 \
  bash -c '. "'"$LIB"'"; claude_p 5 "hello prompt" --add-dir /tmp' >/dev/null 2>&1
check "claude_p strips the leading timeout int" 'grep -qF -- "-p hello prompt --add-dir /tmp" "$TMP/argv.log"'

# --- T6: secrets — $CREDENTIALS_DIRECTORY wins over the dotenv fallback ---
mkdir -p "$TMP/creds" "$TMP/home2/.config/claude"
echo -n "cred-token" > "$TMP/creds/claude-oauth-token"
printf 'export CLAUDE_CODE_OAUTH_TOKEN=legacy-token\n' > "$TMP/home2/.config/claude/oauth-token.env"
out="$(HOME="$TMP/home2" VAULT=/v CREDENTIALS_DIRECTORY="$TMP/creds" bash -c '. "'"$LIB"'"; echo "$CLAUDE_CODE_OAUTH_TOKEN"')"
check "CREDENTIALS_DIRECTORY secret wins" '[ "$out" = "cred-token" ]'

# --- T7: secrets — dotenv fallback used when no CREDENTIALS_DIRECTORY ---
out="$(HOME="$TMP/home2" VAULT=/v bash -c '. "'"$LIB"'"; echo "$CLAUDE_CODE_OAUTH_TOKEN"')"
check "legacy oauth-token.env used as fallback" '[ "$out" = "legacy-token" ]'

# --- T8: CNTXT1_ENV_SKIP_SECRETS=1 loads neither ---
out="$(HOME="$TMP/home2" VAULT=/v CREDENTIALS_DIRECTORY="$TMP/creds" CNTXT1_ENV_SKIP_SECRETS=1 \
  bash -c '. "'"$LIB"'"; echo "${CLAUDE_CODE_OAUTH_TOKEN:-unset}"')"
check "CNTXT1_ENV_SKIP_SECRETS=1 skips secret loading" '[ "$out" = "unset" ]'

# --- T9: secret_load exports a credential under any name; missing => nonzero ---
echo -n "svc-secret" > "$TMP/creds/svc-token"
out="$(HOME="$TMP/home1" VAULT=/v CREDENTIALS_DIRECTORY="$TMP/creds" bash -c '. "'"$LIB"'"; secret_load SVC_TOKEN svc-token; echo "$SVC_TOKEN"')"
check "secret_load exports the credential" '[ "$out" = "svc-secret" ]'
HOME="$TMP/home1" VAULT=/v CREDENTIALS_DIRECTORY="$TMP/creds" bash -c '. "'"$LIB"'"; secret_load X no-such-cred' >/dev/null 2>&1
check "secret_load of a missing credential fails" '[ "$?" -ne 0 ]'

# --- T10: portable_mtime returns an integer for an existing file ---
touch "$TMP/mtimefile"
out="$(HOME="$TMP/home1" VAULT=/v CNTXT1_ENV_SKIP_SECRETS=1 bash -c '. "'"$LIB"'"; portable_mtime "'"$TMP"'/mtimefile"')"
check "portable_mtime returns an integer" 'case "$out" in ""|*[!0-9]*) false;; *) true;; esac'

# --- T11: portable_date_add_days handles positive and negative offsets ---
out="$(HOME="$TMP/home1" VAULT=/v CNTXT1_ENV_SKIP_SECRETS=1 bash -c '. "'"$LIB"'"; portable_date_add_days 1 2026-01-01')"
check "portable_date_add_days +1 from 2026-01-01" '[ "$out" = "2026-01-02" ]'
out="$(HOME="$TMP/home1" VAULT=/v CNTXT1_ENV_SKIP_SECRETS=1 bash -c '. "'"$LIB"'"; portable_date_add_days -1 2026-01-01')"
check "portable_date_add_days -1 from 2026-01-01" '[ "$out" = "2025-12-31" ]'

# --- T12: portable_sed_i edits a file in place on this platform ---
printf 'foo\n' > "$TMP/sedfile"
HOME="$TMP/home1" VAULT=/v CNTXT1_ENV_SKIP_SECRETS=1 bash -c '. "'"$LIB"'"; portable_sed_i "s/foo/bar/" "'"$TMP"'/sedfile"'
check "portable_sed_i edits in place" '[ "$(cat "$TMP/sedfile")" = "bar" ]'

rm -rf "$TMP"
echo; echo "$PASS passed, $FAIL failed"; [ "$FAIL" -eq 0 ]
