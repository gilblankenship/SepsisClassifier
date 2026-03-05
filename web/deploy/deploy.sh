#!/usr/bin/env bash
# ==============================================================================
# SepsisDx - Jetson AGX Thor Deployment Script
#
# This script sets up the SepsisDx web application for production on an
# NVIDIA Jetson AGX Thor alongside the other portfolio sites.
#
# Usage:
#   sudo bash deploy.sh
#
# Prerequisites:
#   - JetPack SDK installed on the Jetson
#   - Internet connectivity
#   - This repository cloned to the Jetson
# ==============================================================================

set -euo pipefail

# --- Configuration ---
APP_NAME="sepsis-dx"
APP_DIR="/opt/${APP_NAME}"
APP_USER="sepsis-dx"
LOG_DIR="/var/log/${APP_NAME}"
CONF_DIR="/etc/${APP_NAME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"  # deploy/ -> web/ -> repo root

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# --- Pre-flight checks ---
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (sudo)."
    exit 1
fi

if ! uname -m | grep -q 'aarch64'; then
    log_warn "This script is intended for ARM64 (aarch64) systems."
    log_warn "Detected architecture: $(uname -m)"
    read -rp "Continue anyway? [y/N] " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || exit 1
fi

log_info "Starting SepsisDx deployment on $(hostname)..."

# ==============================================================================
# Step 1: System dependencies
# ==============================================================================
log_info "Step 1: Installing system dependencies..."

apt-get update -qq
apt-get install -y -qq \
    python3 python3-venv python3-dev python3-pip \
    build-essential \
    nginx \
    logrotate

# ==============================================================================
# Step 2: Create application user
# ==============================================================================
log_info "Step 2: Setting up application user..."

if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /usr/sbin/nologin --home-dir "$APP_DIR" "$APP_USER"
    log_info "Created user: $APP_USER"
else
    log_info "User $APP_USER already exists."
fi

# ==============================================================================
# Step 3: Application directory structure
# ==============================================================================
log_info "Step 3: Setting up application directory..."

mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/models"
mkdir -p "$APP_DIR/data"
mkdir -p "$APP_DIR/web/uploads"
mkdir -p "$LOG_DIR"
mkdir -p "$CONF_DIR"

# Copy application files
rsync -a --delete \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='*.pyc' \
    --exclude='web/uploads/*' \
    --exclude='References/' \
    "$REPO_DIR/" "$APP_DIR/"

chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chown -R "$APP_USER:$APP_USER" "$LOG_DIR"

# ==============================================================================
# Step 4: Python virtual environment and dependencies
# ==============================================================================
log_info "Step 4: Setting up Python virtual environment..."

sudo -u "$APP_USER" bash <<'VENV_SETUP'
cd /opt/sepsis-dx
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
pip install -r web/requirements-web.txt
VENV_SETUP

log_info "Python dependencies installed."

# ==============================================================================
# Step 5: Environment configuration
# ==============================================================================
log_info "Step 5: Configuring environment..."

if [ ! -f "$CONF_DIR/environment" ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > "$CONF_DIR/environment" <<EOF
SECRET_KEY=${SECRET_KEY}
ACTIVE_MODEL=random_forest
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
EOF
    chmod 600 "$CONF_DIR/environment"
    chown root:"$APP_USER" "$CONF_DIR/environment"
    log_info "Environment file created at $CONF_DIR/environment"
else
    log_info "Environment file already exists, skipping."
fi

# ==============================================================================
# Step 6: Nginx configuration
# ==============================================================================
log_info "Step 6: Configuring nginx..."

cp "$APP_DIR/web/deploy/nginx/sepsis-dx.conf" /etc/nginx/sites-available/sepsis-dx
ln -sf /etc/nginx/sites-available/sepsis-dx /etc/nginx/sites-enabled/sepsis-dx

nginx -t
systemctl reload nginx
systemctl enable nginx

log_info "Nginx configured and reloaded."

# ==============================================================================
# Step 7: Systemd service
# ==============================================================================
log_info "Step 7: Installing systemd service..."

cp "$APP_DIR/web/deploy/systemd/sepsis-dx.service" /etc/systemd/system/sepsis-dx.service

# Log rotation
cat > /etc/logrotate.d/sepsis-dx <<'LOGROTATE'
/var/log/sepsis-dx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 sepsis-dx sepsis-dx
    sharedscripts
    postrotate
        systemctl reload sepsis-dx > /dev/null 2>&1 || true
    endscript
}
LOGROTATE

systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl start "$APP_NAME"

log_info "Service $APP_NAME enabled and started."

# ==============================================================================
# Step 8: Install cloudflared (if not already present)
# ==============================================================================
log_info "Step 8: Checking cloudflared..."

if ! command -v cloudflared &>/dev/null; then
    curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb" \
        -o /tmp/cloudflared-linux-arm64.deb
    dpkg -i /tmp/cloudflared-linux-arm64.deb
    rm -f /tmp/cloudflared-linux-arm64.deb
    log_info "cloudflared installed: $(cloudflared --version)"
else
    log_info "cloudflared already installed: $(cloudflared --version)"
fi

# ==============================================================================
# Step 9: Firewall (skip if already configured by another app)
# ==============================================================================
log_info "Step 9: Checking firewall..."

if command -v ufw &>/dev/null; then
    if ufw status | grep -q "Status: active"; then
        log_info "UFW already active (configured by another app)."
    else
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow from 192.168.0.0/16 to any port 22 comment "SSH from LAN"
        ufw allow from 10.0.0.0/8 to any port 22 comment "SSH from LAN"
        ufw --force enable
        log_info "Firewall configured (SSH from LAN only)."
    fi
fi

# ==============================================================================
# Step 10: Verification
# ==============================================================================
log_info "Step 10: Verifying deployment..."

echo ""
echo "======================================================================"
echo " SepsisDx Deployment Summary"
echo "======================================================================"
echo ""

# Check services
for svc in nginx sepsis-dx; do
    if systemctl is-active --quiet "$svc"; then
        echo -e "  ${GREEN}[OK]${NC}  $svc service is running"
    else
        echo -e "  ${RED}[FAIL]${NC} $svc service is NOT running"
        echo "        Check with: sudo journalctl -u $svc -n 50"
    fi
done

# Check gunicorn responds
if curl -sf http://127.0.0.1:8082/api/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}[OK]${NC}  gunicorn responding on port 8082"
else
    echo -e "  ${YELLOW}[WAIT]${NC} gunicorn may still be starting up"
fi

# Check nginx proxy
if curl -sf -H "Host: sepsis-dx.com" http://127.0.0.1:8443/api/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}[OK]${NC}  nginx proxy responding on port 8443"
else
    echo -e "  ${YELLOW}[WAIT]${NC} nginx proxy may still be initializing"
fi

# Check cloudflared
if command -v cloudflared &>/dev/null; then
    echo -e "  ${GREEN}[OK]${NC}  cloudflared is installed"
else
    echo -e "  ${RED}[FAIL]${NC} cloudflared is NOT installed"
fi

echo ""
echo "======================================================================"
echo " Port Map (all Jetson sites)"
echo "======================================================================"
echo ""
echo "  vitalmatch.ai   → gunicorn :8080 → nginx :8443 → cloudflared"
echo "  patent-man.com  → gunicorn :8081 → nginx :8443 → cloudflared"
echo "  sepsis-dx.com   → gunicorn :8082 → nginx :8443 → cloudflared"
echo "  ccs-crm.com     → gunicorn :5050 → nginx :8443 → cloudflared"
echo ""
echo "======================================================================"
echo " Next Steps"
echo "======================================================================"
echo ""
echo "  1. Add sepsis-dx.com to the shared Cloudflare Tunnel:"
echo "     Edit /etc/cloudflared/config.yml and add:"
echo ""
echo "       - hostname: sepsis-dx.com"
echo "         service: http://127.0.0.1:8443"
echo "         originRequest:"
echo "           connectTimeout: 30s"
echo "           noTLSVerify: true"
echo ""
echo "       - hostname: www.sepsis-dx.com"
echo "         service: http://127.0.0.1:8443"
echo "         originRequest:"
echo "           connectTimeout: 30s"
echo "           noTLSVerify: true"
echo ""
echo "  2. Add DNS routes:"
echo "     cloudflared tunnel route dns <TUNNEL_NAME> sepsis-dx.com"
echo "     cloudflared tunnel route dns <TUNNEL_NAME> www.sepsis-dx.com"
echo ""
echo "  3. Restart cloudflared:"
echo "     sudo systemctl restart cloudflared"
echo ""
echo "  4. Ensure pre-trained models exist in $APP_DIR/models/"
echo ""
echo "  See DEPLOYMENT.md for detailed instructions."
echo "======================================================================"
