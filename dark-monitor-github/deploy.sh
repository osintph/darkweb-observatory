#!/usr/bin/env bash
# =============================================================================
# dark-onion-monitor — deploy.sh
# One-shot deploy on a fresh Ubuntu 22.04 / 24.04 install.
# Run as a non-root user with sudo access.
#
# Usage:
#   bash deploy.sh
#
# What this does:
#   1. Installs system packages (Tor, Nginx, Python, UFW)
#   2. Hardens the firewall (LAN SSH only, all inbound blocked)
#   3. Configures Tor hidden service + SOCKS proxy
#   4. Creates Python venv and installs dependencies
#   5. Fixes /var/www/html permissions
#   6. Runs the first scan
#   7. Installs cron jobs (3x daily scan + daily CTI feed refresh)
#   8. Prints your .onion address
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${CYAN}[*]${NC} $*"; }
ok()    { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
die()   { echo -e "${RED}[ERR]${NC} $*" >&2; exit 1; }

# ── Sanity checks ─────────────────────────────────────────────────────────────
[[ "$EUID" -eq 0 ]] && die "Do not run as root. Run as your normal user."
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${INSTALL_DIR}/venv"
PYTHON="${VENV}/bin/python3"
PIP="${VENV}/bin/pip"

info "Install directory: ${INSTALL_DIR}"
info "Running as: $(whoami)"

# ── Detect LAN subnet for firewall ────────────────────────────────────────────
LAN_SUBNET=$(ip route | awk '/src/ && !/^default/ {print $1}' | head -1)
[[ -z "$LAN_SUBNET" ]] && LAN_SUBNET="192.168.0.0/16"
info "Detected LAN subnet: ${LAN_SUBNET}"

# ── 1. System packages ────────────────────────────────────────────────────────
info "Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y \
    tor nginx \
    python3 python3-venv python3-pip python3-dev \
    ufw curl git build-essential \
    libssl-dev libffi-dev \
    --no-install-recommends -qq
ok "System packages installed"

# ── 2. Firewall ───────────────────────────────────────────────────────────────
info "Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from "${LAN_SUBNET}" to any port 22 comment "SSH LAN only"
# Allow local Flask manager on 127.0.0.1 only (no external exposure)
sudo ufw --force enable
ok "Firewall enabled (SSH from ${LAN_SUBNET} only)"

# ── 3. Tor hidden service ─────────────────────────────────────────────────────
info "Configuring Tor..."
TORRC="/etc/tor/torrc"

# Backup original
sudo cp -n "${TORRC}" "${TORRC}.orig" 2>/dev/null || true

# Idempotent: only add if not already present
if ! grep -q "HiddenServiceDir /var/lib/tor/onion_monitor" "${TORRC}"; then
    sudo tee -a "${TORRC}" > /dev/null <<'EOF'

# dark-onion-monitor
SocksPort 9050
HiddenServiceDir /var/lib/tor/onion_monitor/
HiddenServicePort 80 127.0.0.1:80
EOF
fi

sudo systemctl enable tor --quiet
sudo systemctl restart tor
sleep 3

ONION_ADDR=""
for i in {1..10}; do
    if sudo test -f /var/lib/tor/onion_monitor/hostname 2>/dev/null; then
        ONION_ADDR=$(sudo cat /var/lib/tor/onion_monitor/hostname)
        break
    fi
    sleep 2
done
[[ -z "$ONION_ADDR" ]] && warn "Tor hidden service address not yet generated — run: sudo cat /var/lib/tor/onion_monitor/hostname"
ok "Tor configured. Address: ${ONION_ADDR:-<pending>}"

# ── 4. Nginx ──────────────────────────────────────────────────────────────────
info "Configuring Nginx..."
sudo systemctl enable nginx --quiet
sudo systemctl start nginx
sudo chown -R "$(whoami)":"$(whoami)" /var/www/html
ok "Nginx running, /var/www/html owned by $(whoami)"

# ── 5. Python venv ────────────────────────────────────────────────────────────
info "Setting up Python virtual environment..."
python3 -m venv "${VENV}"
"${PIP}" install --upgrade pip --quiet
"${PIP}" install -r "${INSTALL_DIR}/requirements.txt" --quiet
ok "Python venv ready: ${VENV}"

# Verify imports
"${PYTHON}" -c "
import requests, socks, stem, urllib3, bs4, flask
print('  All imports OK')
" || die "Import check failed — check requirements.txt"

# ── 6. Config directory ───────────────────────────────────────────────────────
mkdir -p "${INSTALL_DIR}/config" "${INSTALL_DIR}/data" "${INSTALL_DIR}/logs"
ok "Config/data/logs directories created"

# ── 7. First scan ─────────────────────────────────────────────────────────────
info "Running first scan (fetching remote CTI feeds + full scan)..."
info "This takes 3-5 minutes on first run..."
cd "${INSTALL_DIR}"
"${PYTHON}" advanced_scanner.py --fetch-remote
ok "First scan complete"

# ── 8. Cron jobs ─────────────────────────────────────────────────────────────
info "Installing cron jobs..."
CRON_LOG="${INSTALL_DIR}/logs/cron.log"
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -v "dark-onion-monitor\|advanced_scanner" || true)

NEW_CRON="${EXISTING_CRON}
# dark-onion-monitor: scan 3x daily (6am, 2pm, 10pm)
0 6,14,22 * * * ${PYTHON} ${INSTALL_DIR}/advanced_scanner.py >> ${CRON_LOG} 2>&1
# dark-onion-monitor: refresh remote CTI feeds daily at 3am
0 3 * * * ${PYTHON} ${INSTALL_DIR}/advanced_scanner.py --fetch-remote >> ${CRON_LOG} 2>&1"

echo "$NEW_CRON" | crontab -
ok "Cron jobs installed (scans at 06:00, 14:00, 22:00 | CTI refresh at 03:00)"

# ── 9. Manager (optional) ─────────────────────────────────────────────────────
if [[ -f "${INSTALL_DIR}/manager.py" ]]; then
    info "Target manager available at http://127.0.0.1:5000 (run via SSH tunnel)"
    info "Start with: source venv/bin/activate && python manager.py"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  ${CYAN}Dashboard:${NC}     ${ONION_ADDR:-run: sudo cat /var/lib/tor/onion_monitor/hostname}"
echo -e "  ${CYAN}Install dir:${NC}   ${INSTALL_DIR}"
echo -e "  ${CYAN}Venv:${NC}          ${VENV}"
echo -e "  ${CYAN}Logs:${NC}          ${INSTALL_DIR}/logs/"
echo -e "  ${CYAN}Scan manually:${NC} ${PYTHON} ${INSTALL_DIR}/advanced_scanner.py"
echo -e "  ${CYAN}Force CTI sync:${NC} ${PYTHON} ${INSTALL_DIR}/advanced_scanner.py --fetch-remote"
echo ""
echo -e "  Open Tor Browser and navigate to your .onion address above."
echo ""
