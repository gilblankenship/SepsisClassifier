#!/usr/bin/env bash
# SepsisDx Deployment Script
# Usage: sudo bash deploy.sh
set -euo pipefail

APP_NAME="sepsis-dx"
APP_DIR="/opt/${APP_NAME}"
CONF_DIR="/etc/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"  # web/ parent = repo root

echo "=== SepsisDx Deployment ==="

# ── 1. System dependencies ──────────────────────────────────────────
echo "[1/9] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip nginx

# ── 2. Application user ─────────────────────────────────────────────
echo "[2/9] Creating application user..."
if ! id "$APP_NAME" &>/dev/null; then
    useradd --system --shell /usr/sbin/nologin --home-dir "$APP_DIR" "$APP_NAME"
fi

# ── 3. Install application files ────────────────────────────────────
echo "[3/9] Installing application files..."
mkdir -p "$APP_DIR"
rsync -a --delete \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='*.pyc' \
    --exclude='web/uploads/*' \
    "$REPO_DIR/" "$APP_DIR/"

# ── 4. Python virtual environment ───────────────────────────────────
echo "[4/9] Setting up Python virtual environment..."
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
"$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/web/requirements-web.txt"

# ── 5. Runtime directories ──────────────────────────────────────────
echo "[5/9] Creating runtime directories..."
mkdir -p "$LOG_DIR"
mkdir -p "$APP_DIR/web/uploads"
mkdir -p "$APP_DIR/models"
mkdir -p "$APP_DIR/data"
chown -R "$APP_NAME:$APP_NAME" "$APP_DIR"
chown -R "$APP_NAME:$APP_NAME" "$LOG_DIR"

# ── 6. Environment configuration ────────────────────────────────────
echo "[6/9] Setting up environment configuration..."
mkdir -p "$CONF_DIR"
if [ ! -f "$CONF_DIR/environment" ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > "$CONF_DIR/environment" <<ENVEOF
SECRET_KEY=${SECRET_KEY}
ACTIVE_MODEL=random_forest
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
ENVEOF
    chmod 600 "$CONF_DIR/environment"
    chown "$APP_NAME:$APP_NAME" "$CONF_DIR/environment"
    echo "  -> Generated new SECRET_KEY"
else
    echo "  -> Environment file already exists, skipping"
fi

# ── 7. Nginx ─────────────────────────────────────────────────────────
echo "[7/9] Configuring nginx..."
cp "$APP_DIR/web/deploy/nginx/sepsis-dx.conf" /etc/nginx/sites-available/sepsis-dx
ln -sf /etc/nginx/sites-available/sepsis-dx /etc/nginx/sites-enabled/sepsis-dx
nginx -t
systemctl reload nginx

# ── 8. Systemd service ──────────────────────────────────────────────
echo "[8/9] Installing systemd service..."
cp "$APP_DIR/web/deploy/systemd/sepsis-dx.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl restart "$APP_NAME"

# ── 9. Firewall ─────────────────────────────────────────────────────
echo "[9/9] Configuring firewall..."
if command -v ufw &>/dev/null; then
    ufw allow OpenSSH
    ufw --force enable
    echo "  -> UFW enabled (SSH only, HTTP via tunnel)"
fi

echo ""
echo "=== Deployment complete ==="
echo "  App:     $APP_DIR"
echo "  Logs:    $LOG_DIR"
echo "  Config:  $CONF_DIR/environment"
echo "  Service: systemctl status $APP_NAME"
echo ""
echo "Next steps:"
echo "  1. Configure cloudflared tunnel (see deploy/cloudflared/config.yml)"
echo "  2. Add CNAME records in Cloudflare DNS -> <TUNNEL_UUID>.cfargotunnel.com"
echo "  3. Ensure pre-trained models exist in $APP_DIR/models/"
