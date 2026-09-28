#!/usr/bin/env bash
# install.sh — render + install the cloud-core systemd units for one or more
# optional add-ons, then enable their timers. Idempotent; safe to re-run
# (`make deploy` calls it). Unit files in <addon>/systemd/ carry {{TOKENS}}:
#
#   {{USER}}          the unprivileged account that owns the vault checkout
#   {{HOME}}          that account's home directory
#   {{VAULT}}         absolute path of the vault checkout
#   {{TZ}}            IANA time zone for OnCalendar= (e.g. America/New_York)
#   {{OPTIONAL_DIR}}  absolute path of this SYSTEM/optional directory
#
# Usage:
#   sudo ./install.sh --user USER --vault /path/to/vault [--tz ZONE]
#                     [--addons core-jobs,gardener,remote-access]
#                     [--systemd-dir DIR] [--render-only]
#
#   --addons       comma list of SYSTEM/optional/<name> dirs (default: core-jobs)
#   --systemd-dir  where units are written (default /etc/systemd/system)
#   --render-only  write rendered units to --systemd-dir and stop — no root, no
#                  /etc changes, no systemctl. Use to review or test.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OPTIONAL_DIR="$(cd "$HERE/.." && pwd)"
USER_NAME="${CNTXT1_USER:-}"; VAULT_PATH="${VAULT:-}"
TZ_NAME="${TZ:-$(cat /etc/timezone 2>/dev/null || echo UTC)}"
ADDONS="core-jobs"; SYSTEMD_DIR="/etc/systemd/system"; RENDER_ONLY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --user) USER_NAME="$2"; shift 2 ;;
    --vault) VAULT_PATH="$2"; shift 2 ;;
    --tz) TZ_NAME="$2"; shift 2 ;;
    --addons) ADDONS="$2"; shift 2 ;;
    --systemd-dir) SYSTEMD_DIR="$2"; shift 2 ;;
    --render-only) RENDER_ONLY=1; shift ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) echo "install.sh: unknown argument: $1" >&2; exit 2 ;;
  esac
done

[ -n "$USER_NAME" ]  || { echo "install.sh: --user (or CNTXT1_USER) is required" >&2; exit 2; }
[ -n "$VAULT_PATH" ] || { echo "install.sh: --vault (or VAULT) is required" >&2; exit 2; }
for v in "$USER_NAME" "$VAULT_PATH" "$TZ_NAME" "$OPTIONAL_DIR"; do
  case "$v" in
    *[!A-Za-z0-9._/@:+-]*) echo "install.sh: unsupported characters in '$v' (no spaces/quotes/'|')" >&2; exit 2 ;;
  esac
done
if [ "$RENDER_ONLY" = 0 ]; then
  [ "$(id -u)" = 0 ] || { echo "install.sh: run as root (sudo), or use --render-only" >&2; exit 1; }
  HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"
  [ -n "$HOME_DIR" ] || { echo "install.sh: no such user: $USER_NAME" >&2; exit 1; }
else
  HOME_DIR="${HOME_DIR:-/home/$USER_NAME}"
fi

render() {  # render SRC DEST
  sed -e "s|{{USER}}|$USER_NAME|g" -e "s|{{HOME}}|$HOME_DIR|g" \
      -e "s|{{VAULT}}|$VAULT_PATH|g" -e "s|{{TZ}}|$TZ_NAME|g" \
      -e "s|{{OPTIONAL_DIR}}|$OPTIONAL_DIR|g" "$1" > "$2"
  if grep -q '{{' "$2"; then
    echo "install.sh: unrendered token left in $2" >&2; grep -n '{{' "$2" >&2; exit 1
  fi
}

if [ "$RENDER_ONLY" = 0 ]; then
  install -d -m 0755 /etc/cntxt1
  install -d -m 0700 /etc/credstore
  if [ ! -f /etc/cntxt1/core.env ]; then
    render "$HERE/core.env.example" /etc/cntxt1/core.env
    chown "root:$USER_NAME" /etc/cntxt1/core.env; chmod 0640 /etc/cntxt1/core.env   # HC_PING_BASE embeds a semi-private key
    echo "install.sh: wrote /etc/cntxt1/core.env — edit it (HC_PING_BASE, NTFY_URL, RESTIC_REPOSITORY)."
  fi
fi
mkdir -p "$SYSTEMD_DIR"

enable_list=()
IFS=',' read -r -a addon_arr <<< "$ADDONS"
for addon in "${addon_arr[@]}"; do
  sdir="$OPTIONAL_DIR/$addon/systemd"
  [ -d "$sdir" ] || { echo "install.sh: no systemd/ dir for add-on '$addon'" >&2; exit 1; }
  for f in "$sdir"/*.service "$sdir"/*.timer "$sdir"/*.path; do
    [ -e "$f" ] || continue
    render "$f" "$SYSTEMD_DIR/$(basename "$f")"
    echo "rendered $(basename "$f")"
  done
  if [ -f "$sdir/ENABLED" ]; then
    while read -r unit; do
      case "$unit" in ''|'#'*) continue ;; esac
      enable_list+=("$unit")
    done < "$sdir/ENABLED"
  fi
done

[ "$RENDER_ONLY" = 1 ] && { echo "install.sh: rendered to $SYSTEMD_DIR (render-only)."; exit 0; }

systemctl daemon-reload
for unit in "${enable_list[@]}"; do
  echo "enable --now $unit"
  systemctl enable --now "$unit"
done
echo "install.sh: done. Check: systemctl list-timers 'cntxt1-*' --all"
