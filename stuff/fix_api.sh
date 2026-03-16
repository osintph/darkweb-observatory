#!/bin/bash
#
# Quick fix for API server
#

echo "[*] Fixing API server..."

# Stop the broken service
sudo systemctl stop darkweb-api

# Replace API server with working version
sudo cp api_server_fixed.py /var/www/html/api/api_server.py
sudo chmod +x /var/www/html/api/api_server.py

# Restart service
sudo systemctl restart darkweb-api

# Wait and check
sleep 3

if sudo systemctl is-active --quiet darkweb-api; then
    echo "[✓] API service is now running!"
    echo ""
    echo "Test it:"
    echo "  curl http://127.0.0.1:5000/api/health"
else
    echo "[!] Still having issues. Check logs:"
    echo ""
    sudo journalctl -u darkweb-api -n 20 --no-pager
fi

