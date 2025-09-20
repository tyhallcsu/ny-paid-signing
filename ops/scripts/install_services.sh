#!/usr/bin/env bash
set -euo pipefail

# Paths
BASE="/opt/ny-paid-signing-fixed"
SVC_DIR="/etc/systemd/system"
NGINX_AVAIL="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"

echo "[i] Copying systemd units..."
sudo cp systemd/ny-*.service "$SVC_DIR"/

echo "[i] Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable ny-flask ny-worker ny-bot

echo "[i] Copying nginx site..."
sudo cp nginx/ny-paid-signing.conf "$NGINX_AVAIL"/
if [ ! -e "$NGINX_ENABLED/ny-paid-signing.conf" ]; then
  sudo ln -s "$NGINX_AVAIL/ny-paid-signing.conf" "$NGINX_ENABLED/ny-paid-signing.conf"
fi

echo "[i] Testing nginx config..."
sudo nginx -t

echo "[i] Restarting services..."
sudo systemctl restart nginx
sudo systemctl start ny-flask ny-worker ny-bot

echo "Done. Remember to issue TLS certs with certbot if needed."
