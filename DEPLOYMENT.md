# SepsisDx — Jetson AGX Thor Deployment Guide

SepsisDx runs on the NVIDIA Jetson AGX Thor alongside the other Digital Biosciences / MDC Studio portfolio sites, all served through a shared Cloudflare Tunnel.

## Architecture

```
Browser → https://sepsis-dx.com
    ↓
Cloudflare Edge (SSL termination, DDoS protection)
    ↓
cloudflared tunnel (outbound connection, no inbound ports)
    ↓
nginx (127.0.0.1:8443) — static files, request buffering, server_name routing
    ↓
gunicorn (127.0.0.1:8082) — WSGI server (2 workers, 4 gthreads)
    ↓
Flask application (SepsisDx)
```

## Port Map (All Jetson Sites)

| Site | Gunicorn Port | Nginx Port | Domain |
|------|---------------|------------|--------|
| vitalmatch.ai | 8080 | 8443 | vitalmatch.ai |
| patent-man.com | 8081 | 8443 | patent-man.com |
| **sepsis-dx.com** | **8082** | **8443** | **sepsis-dx.com** |
| ccs-crm.com | 5050 | 8443 | ccs-crm.com |

All sites share nginx on port 8443 — nginx uses `server_name` to route each domain to its gunicorn backend. All sites share a single cloudflared tunnel.

## Quick Deploy

```bash
# On the Jetson, clone the repo and run deploy
cd /home/gil/Projects
git clone https://github.com/gilblankenship/SepsisClassifier.git
cd SepsisClassifier/web/deploy
sudo bash deploy.sh
```

The script handles steps 1–9 automatically. You only need to manually configure the Cloudflare Tunnel (step 10 below).

## Step-by-Step Manual Deployment

### 1. System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-dev python3-pip \
    build-essential nginx logrotate
```

### 2. Application User

```bash
sudo useradd --system --shell /usr/sbin/nologin --home-dir /opt/sepsis-dx sepsis-dx
```

### 3. Application Files

```bash
sudo mkdir -p /opt/sepsis-dx
sudo rsync -a --delete \
    --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
    --exclude='.env' --exclude='*.pyc' --exclude='web/uploads/*' \
    --exclude='References/' \
    /home/gil/Projects/SepsisClassifier/ /opt/sepsis-dx/

sudo mkdir -p /opt/sepsis-dx/{models,data,web/uploads}
sudo mkdir -p /var/log/sepsis-dx
sudo chown -R sepsis-dx:sepsis-dx /opt/sepsis-dx /var/log/sepsis-dx
```

### 4. Python Environment

```bash
sudo -u sepsis-dx bash -c '
cd /opt/sepsis-dx
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
pip install -r web/requirements-web.txt
'
```

### 5. Environment Config

```bash
sudo mkdir -p /etc/sepsis-dx
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sudo tee /etc/sepsis-dx/environment > /dev/null <<EOF
SECRET_KEY=${SECRET_KEY}
ACTIVE_MODEL=random_forest
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
EOF
sudo chmod 600 /etc/sepsis-dx/environment
sudo chown root:sepsis-dx /etc/sepsis-dx/environment
```

### 6. Nginx

```bash
sudo cp /opt/sepsis-dx/web/deploy/nginx/sepsis-dx.conf /etc/nginx/sites-available/sepsis-dx
sudo ln -sf /etc/nginx/sites-available/sepsis-dx /etc/nginx/sites-enabled/sepsis-dx
sudo nginx -t && sudo systemctl reload nginx
```

### 7. Systemd Service

```bash
sudo cp /opt/sepsis-dx/web/deploy/systemd/sepsis-dx.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sepsis-dx
sudo systemctl start sepsis-dx
```

### 8. Verify Local

```bash
# Check service status
sudo systemctl status sepsis-dx

# Test gunicorn directly
curl -s http://127.0.0.1:8082/api/health

# Test through nginx
curl -s -H "Host: sepsis-dx.com" http://127.0.0.1:8443/api/health
```

### 9. Add to Cloudflare Tunnel

Since all sites share one tunnel, edit the existing config:

```bash
sudo nano /etc/cloudflared/config.yml
```

Add these entries to the `ingress` section (before the catch-all `- service: http_status:404`):

```yaml
  - hostname: sepsis-dx.com
    service: http://127.0.0.1:8443
    originRequest:
      connectTimeout: 30s
      noTLSVerify: true
      keepAliveConnections: 10
      keepAliveTimeout: 90s

  - hostname: www.sepsis-dx.com
    service: http://127.0.0.1:8443
    originRequest:
      connectTimeout: 30s
      noTLSVerify: true
      keepAliveConnections: 10
      keepAliveTimeout: 90s
```

### 10. DNS Routes

```bash
# Add CNAME records pointing to the tunnel
TUNNEL_NAME="<your-tunnel-name>"  # same tunnel used by other sites

cloudflared tunnel route dns $TUNNEL_NAME sepsis-dx.com
cloudflared tunnel route dns $TUNNEL_NAME www.sepsis-dx.com

# Restart cloudflared to pick up the new ingress rules
sudo systemctl restart cloudflared
```

### 11. Pre-trained Models

Copy or generate the ML models:

```bash
# Option A: Copy existing models from dev machine
scp models/*.joblib gil@jetson:/opt/sepsis-dx/models/

# Option B: Generate from the web UI
# Navigate to https://sepsis-dx.com/train/ and train models
```

## Updates

To deploy updates after pushing to GitHub:

```bash
cd /home/gil/Projects/SepsisClassifier
git pull

# Re-run the deploy script
cd web/deploy
sudo bash deploy.sh
```

Or manually:

```bash
sudo rsync -a --delete \
    --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
    --exclude='.env' --exclude='*.pyc' --exclude='web/uploads/*' \
    /home/gil/Projects/SepsisClassifier/ /opt/sepsis-dx/

sudo chown -R sepsis-dx:sepsis-dx /opt/sepsis-dx
sudo systemctl restart sepsis-dx
```

## Troubleshooting

```bash
# Service logs
sudo journalctl -u sepsis-dx -n 50 -f

# Nginx logs
tail -f /var/log/nginx/sepsis-dx-*.log

# Gunicorn logs
tail -f /var/log/sepsis-dx/gunicorn-*.log

# Check all site services
for svc in lungct patent-man sepsis-dx; do
    echo "$svc: $(systemctl is-active $svc)"
done

# Check cloudflared tunnel status
sudo systemctl status cloudflared
cloudflared tunnel info
```

## File Locations

| Component | Path |
|-----------|------|
| Application | `/opt/sepsis-dx/` |
| Virtual env | `/opt/sepsis-dx/.venv/` |
| Models | `/opt/sepsis-dx/models/` |
| Uploads | `/opt/sepsis-dx/web/uploads/` |
| Environment | `/etc/sepsis-dx/environment` |
| Nginx config | `/etc/nginx/sites-available/sepsis-dx` |
| Systemd unit | `/etc/systemd/system/sepsis-dx.service` |
| Cloudflared | `/etc/cloudflared/config.yml` (shared) |
| Gunicorn logs | `/var/log/sepsis-dx/gunicorn-*.log` |
| Nginx logs | `/var/log/nginx/sepsis-dx-*.log` |
