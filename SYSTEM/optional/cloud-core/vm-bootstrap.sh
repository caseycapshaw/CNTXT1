#!/usr/bin/env bash
# vm-bootstrap.sh — idempotent first-boot (and re-run-safe) setup for the
# "cloud core": a small always-on Ubuntu LTS VM that runs your KB's scheduled
# jobs (see README.md and ../core-jobs/). Run as root on the fresh host.
#
#   sudo ./vm-bootstrap.sh --user NAME --vault-repo URL --services-repo URL|vault [options]
#
# Required
#   --user NAME            unprivileged account that owns the checkouts and runs jobs
#   --vault-repo URL       git URL of YOUR PRIVATE vault repo (never a public one)
#   --services-repo URL    git URL of the repo holding the add-ons (core-jobs, gardener,
#                          remote-access), cloned to ~/services — or the word `vault` if
#                          you run them straight from the vault's SYSTEM/optional/ (no
#                          second clone)
# Optional
#   --vault-dir PATH       where to clone the vault (default: /home/NAME/vault)
#   --tz ZONE              IANA time zone (default: keep the host's current zone)
#   --swap-gb N            swapfile size in GiB (default 4; 0 = none)
#   --sudo                 add NAME to the sudo group (default: no — use your admin login)
#   --allow-rule 'RULE'    extra ufw rule, repeatable, e.g. --allow-rule '22/tcp'  or
#                          --allow-rule 'from 100.64.0.0/10 to any port 22 proto tcp'
#   --lock-ssh             remove the "SSH from anywhere" rule. ONLY after you have put SSH
#                          behind a VPN / zero-trust network and TESTED logging in that way
#                          (e.g. Tailscale or Twingate — see README.md § Network)
#   --path-parity-link L   create symlink L -> /home (e.g. /Users) so a vault path written
#                          on a Mac (/Users/you/...) resolves identically on this host.
#                          Optional; only useful if Mac and Linux share one vault path.
#   --with-cloudflared     install cloudflared (remote-access add-on)
#   --with-claude          install Node 22 + @anthropic-ai/claude-code (gardener / claude -p jobs)
#   -h, --help
#
# Distro-codename-agnostic: every third-party apt repo used (cloudflared, NodeSource)
# uses the vendor's codename-independent suite, so this is not pinned to one Ubuntu
# release. Safe to re-run: each step checks current state before acting.
set -euo pipefail

USER_NAME=""; VAULT_REPO=""; SERVICES_REPO=""; VAULT_DIR=""; TZ_NAME=""
SWAP_GB=4; ADD_SUDO=0; LOCK_SSH=0; PARITY_LINK=""; WITH_CF=0; WITH_CLAUDE=0
ALLOW_RULES=()

usage() { sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; }
die() { echo "vm-bootstrap: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --user) USER_NAME="${2:-}"; shift 2 ;;
    --vault-repo) VAULT_REPO="${2:-}"; shift 2 ;;
    --services-repo) SERVICES_REPO="${2:-}"; shift 2 ;;
    --vault-dir) VAULT_DIR="${2:-}"; shift 2 ;;
    --tz) TZ_NAME="${2:-}"; shift 2 ;;
    --swap-gb) SWAP_GB="${2:-}"; shift 2 ;;
    --sudo) ADD_SUDO=1; shift ;;
    --allow-rule) ALLOW_RULES+=("${2:-}"); shift 2 ;;
    --lock-ssh) LOCK_SSH=1; shift ;;
    --path-parity-link) PARITY_LINK="${2:-}"; shift 2 ;;
    --with-cloudflared) WITH_CF=1; shift ;;
    --with-claude) WITH_CLAUDE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1 (see --help)" ;;
  esac
done

[ -n "$USER_NAME" ]     || die "--user is required"
[ -n "$VAULT_REPO" ]    || die "--vault-repo is required (your PRIVATE vault repo URL)"
[ -n "$SERVICES_REPO" ] || die "--services-repo is required (a repo URL, or the word 'vault')"
case "$USER_NAME" in *[!a-z0-9_-]*|'') die "--user must be a plain lowercase account name" ;; esac
case "$SWAP_GB" in ''|*[!0-9]*) die "--swap-gb must be a whole number" ;; esac
[ -z "$PARITY_LINK" ] || case "$PARITY_LINK" in /*) ;; *) die "--path-parity-link must be an absolute path" ;; esac
[ "$(id -u)" -eq 0 ] || die "must run as root (sudo ./vm-bootstrap.sh …)"

# shellcheck disable=SC1091
. /etc/os-release
CODENAME="${VERSION_CODENAME:-unknown}"
HOME_DIR="/home/$USER_NAME"
: "${VAULT_DIR:=$HOME_DIR/vault}"
log() { echo "bootstrap: $*"; }
log "detected distro: ${ID:-?} ${VERSION_ID:-?} (codename: $CODENAME)"

# --- 1) apt update/upgrade ----------------------------------------------------
log "apt update && upgrade…"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

# --- 2) unattended security upgrades (auto-reboot 04:00) ----------------------
log "unattended-upgrades…"
apt-get install -y -qq unattended-upgrades update-notifier-common
cat > /etc/apt/apt.conf.d/52-cntxt1-unattended-upgrades <<'CONF'
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:00";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
CONF
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'CONF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
CONF

# --- 3) service user ----------------------------------------------------------
if ! id "$USER_NAME" >/dev/null 2>&1; then
  log "creating user $USER_NAME…"
  useradd -m -s /bin/bash "$USER_NAME"
else
  log "user $USER_NAME already exists."
fi
if [ "$ADD_SUDO" -eq 1 ]; then usermod -aG sudo "$USER_NAME"; fi
install -d -m 700 -o "$USER_NAME" -g "$USER_NAME" "$HOME_DIR/.ssh"
if [ -f /root/.ssh/authorized_keys ] && [ ! -f "$HOME_DIR/.ssh/authorized_keys" ]; then
  log "copying root's authorized_keys to $USER_NAME…"
  install -m 600 -o "$USER_NAME" -g "$USER_NAME" /root/.ssh/authorized_keys "$HOME_DIR/.ssh/authorized_keys"
fi

# Optional path parity (see --help): /Users -> /home so a Mac-style absolute vault
# path resolves the same on this host. Off unless asked for.
if [ -n "$PARITY_LINK" ]; then
  if [ ! -e "$PARITY_LINK" ]; then
    log "symlinking $PARITY_LINK -> /home (path parity)…"
    ln -s /home "$PARITY_LINK"
  elif [ -L "$PARITY_LINK" ] && [ "$(readlink "$PARITY_LINK")" = "/home" ]; then
    log "$PARITY_LINK -> /home already present."
  else
    log "WARNING: $PARITY_LINK exists and is not a symlink to /home — leaving it alone." >&2
  fi
fi

# --- 4) firewall: deny all inbound --------------------------------------------
# The core needs NO inbound ports: jobs run locally, the remote-access add-on uses an
# outbound-only Cloudflare Tunnel, and admin SSH should sit behind your VPN /
# zero-trust network of choice. SSH stays open from anywhere ONLY until you have
# confirmed the private path works, then re-run with --lock-ssh.
log "configuring ufw (default deny inbound)…"
apt-get install -y -qq ufw
ufw --force default deny incoming
ufw --force default allow outgoing
for rule in "${ALLOW_RULES[@]+"${ALLOW_RULES[@]}"}"; do
  log "ufw allow $rule"
  # shellcheck disable=SC2086  # a ufw rule is intentionally word-split
  ufw allow $rule
done
if [ "$LOCK_SSH" -eq 1 ]; then
  log "--lock-ssh: removing the public SSH rule. Make sure your private path to SSH works!"
  ufw delete allow OpenSSH 2>/dev/null || ufw delete allow 22/tcp 2>/dev/null || true
else
  log "allowing SSH from anywhere TEMPORARILY — put SSH behind your VPN, test it, then re-run with --lock-ssh."
  ufw allow OpenSSH
fi
ufw --force enable

# --- 5) packages ----------------------------------------------------------------
log "installing base packages…"
apt-get install -y -qq git curl jq ripgrep python3 python3-venv python3-pip chrony gnupg ca-certificates restic

if ! command -v uv >/dev/null 2>&1; then
  log "installing uv…"
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
else
  log "uv already installed."
fi

if [ "$WITH_CLAUDE" -eq 1 ]; then
  if ! command -v node >/dev/null 2>&1 || [ "$(node -v | sed 's/^v//' | cut -d. -f1)" -lt 22 ]; then
    log "installing Node.js 22 (NodeSource; its repo uses the codename-independent 'nodistro' suite)…"
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y -qq nodejs
  fi
  if ! command -v claude >/dev/null 2>&1; then
    log "installing @anthropic-ai/claude-code (npm global)…"
    npm i -g @anthropic-ai/claude-code
  else
    log "claude-code already installed."
  fi
fi

if [ "$WITH_CF" -eq 1 ] && ! command -v cloudflared >/dev/null 2>&1; then
  log "installing cloudflared (Cloudflare apt repo, codename-independent 'any' suite)…"
  mkdir -p /usr/share/keyrings
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg -o /usr/share/keyrings/cloudflare-main.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main" \
    > /etc/apt/sources.list.d/cloudflared.list
  apt-get update -qq
  apt-get install -y -qq cloudflared
fi

# --- 6) timezone ------------------------------------------------------------------
if [ -n "$TZ_NAME" ]; then
  log "setting timezone to $TZ_NAME…"
  timedatectl set-timezone "$TZ_NAME"
fi

# --- 7) journald cap --------------------------------------------------------------
log "capping journald at 1G…"
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/cntxt1.conf <<'CONF'
[Journal]
SystemMaxUse=1G
CONF
systemctl restart systemd-journald

# --- 8) swap ----------------------------------------------------------------------
if [ "$SWAP_GB" -gt 0 ]; then
  if [ ! -f /swapfile ]; then
    log "creating ${SWAP_GB}G swapfile…"
    fallocate -l "${SWAP_GB}G" /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=$((SWAP_GB * 1024))
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  else
    log "swapfile already present."
  fi
  echo 'vm.swappiness=10' > /etc/sysctl.d/60-cntxt1-swappiness.conf
  sysctl -p /etc/sysctl.d/60-cntxt1-swappiness.conf >/dev/null
fi

# --- 9) config + credential directories -----------------------------------------
log "creating /etc/cntxt1, /etc/credstore, /run/cntxt1 (tmpfiles.d)…"
install -d -m 755 /etc/cntxt1
install -d -m 700 -o root -g root /etc/credstore
echo "d /run/cntxt1 0755 $USER_NAME $USER_NAME -" > /etc/tmpfiles.d/cntxt1.conf
systemd-tmpfiles --create /etc/tmpfiles.d/cntxt1.conf

# --- 10) checkouts ----------------------------------------------------------------
clone() {  # clone URL DIR — as the service user; failure is a warning (deploy keys come later)
  local url="$1" dir="$2"
  if [ -d "$dir/.git" ]; then log "$dir already a git checkout — skipping clone."; return 0; fi
  install -d -o "$USER_NAME" -g "$USER_NAME" "$(dirname "$dir")"
  if ! sudo -u "$USER_NAME" git clone "$url" "$dir"; then
    log "WARNING: clone of $url failed (auth?). Set up a deploy key / credential for $USER_NAME, then:" >&2
    log "         sudo -u $USER_NAME git clone $url $dir" >&2
  fi
}
clone "$VAULT_REPO" "$VAULT_DIR"
if [ "$SERVICES_REPO" = "vault" ]; then
  SERVICES_DIR="$VAULT_DIR/SYSTEM/optional"
else
  SERVICES_DIR="$HOME_DIR/services"
  clone "$SERVICES_REPO" "$SERVICES_DIR"
fi

cat <<CHECKLIST

=============================================================================
vm-bootstrap done. Manual steps still required:

  [ ] Put SSH behind your VPN / zero-trust network (Tailscale, Twingate, WireGuard, ...),
      confirm you can log in that way, then re-run this script with --lock-ssh to close
      public SSH. Until then SSH is open to the internet.
  [ ] Render + enable the jobs (as root):
        cd $SERVICES_DIR/core-jobs && ./install.sh --user $USER_NAME --vault $VAULT_DIR
      then edit /etc/cntxt1/core.env (HC_PING_BASE, NTFY_URL, RESTIC_REPOSITORY).
  [ ] Store credentials with core-jobs/set-secret (values are prompted, never on argv):
        restic-password  backup-key-id  backup-secret-key  claude-oauth-token ...
  [ ] If you installed claude: \`claude setup-token\` as $USER_NAME, then set-secret the token.
  [ ] Remote access (optional): see $SERVICES_DIR/remote-access/README.md
  [ ] Prove the dead-man's-switch: pause a job / timer and watch the alert arrive.

See README.md next to this script for the architecture and the reasoning.
=============================================================================
CHECKLIST
