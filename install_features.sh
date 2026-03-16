#!/bin/bash
#
# Installation for Dashboard Features - NGINX VERSION
#

set -e

echo "[*] Installing new dashboard features for nginx..."

# Create API directory
echo "[*] Creating API directory..."
sudo mkdir -p /var/www/html/api

# Copy scripts
echo "[*] Copying scripts..."
sudo cp on_demand_scan.py /var/www/html/api/
sudo cp refresh_news.py /var/www/html/api/

# Create simple Flask API server
echo "[*] Creating API server..."
sudo tee /var/www/html/api/api_server.py > /dev/null <<'EOFAPI'
#!/usr/bin/env python3
"""
Simple Flask API for Dashboard Features
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.insert(0, '/var/www/html/api')
from on_demand_scan import perform_deep_scan
from refresh_news import fetch_news

app = Flask(__name__)
CORS(app)

@app.route('/api/scan', methods=['POST'])
def scan():
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'})
        
        result = perform_deep_scan(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/refresh-news', methods=['POST'])
def refresh():
    try:
        success = fetch_news()
        return jsonify({
            'success': success,
            'message': 'News feed updated' if success else 'Failed to update'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
EOFAPI

sudo chmod +x /var/www/html/api/api_server.py

# Install Flask if needed
echo "[*] Checking Python dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "    [!] Installing Flask..."
    pip3 install flask flask-cors --break-system-packages
else
    echo "    [+] Flask already installed"
fi

if ! python3 -c "import feedparser" 2>/dev/null; then
    echo "    [!] Installing feedparser..."
    pip3 install feedparser --break-system-packages
else
    echo "    [+] feedparser already installed"
fi

# Create systemd service for API
echo "[*] Creating systemd service..."
sudo tee /etc/systemd/system/darkweb-api.service > /dev/null <<'EOFSVC'
[Unit]
Description=Dark Web Observatory API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/html/api
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /var/www/html/api/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFSVC

# Start and enable service
echo "[*] Starting API service..."
sudo systemctl daemon-reload
sudo systemctl enable darkweb-api
sudo systemctl restart darkweb-api

# Check if service is running
sleep 2
if sudo systemctl is-active --quiet darkweb-api; then
    echo "    [+] API service is running on http://127.0.0.1:5000"
else
    echo "    [!] Warning: API service may not have started properly"
    sudo systemctl status darkweb-api --no-pager
fi

# Configure nginx reverse proxy
echo "[*] Configuring nginx..."
NGINX_CONF="/etc/nginx/sites-available/default"

# Check if proxy is already configured
if ! sudo grep -q "location /api/" "$NGINX_CONF" 2>/dev/null; then
    echo "    [*] Adding API proxy to nginx config..."
    
    # Backup original config
    sudo cp "$NGINX_CONF" "${NGINX_CONF}.backup"
    
    # Add proxy configuration before the closing brace of server block
    sudo sed -i '/^[[:space:]]*location \/ {/i\
    # Dark Web Observatory API\
    location /api/ {\
        proxy_pass http://127.0.0.1:5000;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
    }\
' "$NGINX_CONF"
    
    echo "    [+] Nginx config updated"
    
    # Test and reload nginx
    if sudo nginx -t 2>/dev/null; then
        sudo systemctl reload nginx
        echo "    [+] Nginx reloaded"
    else
        echo "    [!] Nginx config test failed, restoring backup"
        sudo cp "${NGINX_CONF}.backup" "$NGINX_CONF"
        sudo systemctl reload nginx
    fi
else
    echo "    [+] API proxy already configured in nginx"
fi

# Generate initial news feed
echo "[*] Generating initial news feed..."
cd /var/www/html/api
sudo -u www-data python3 refresh_news.py || python3 refresh_news.py

echo ""
echo "[✓] Installation complete!"
echo ""
echo "Services:"
echo "  • API Server: http://127.0.0.1:5000 (systemd service: darkweb-api)"
echo "  • Nginx proxy: /api/* → http://127.0.0.1:5000/api/*"
echo ""
echo "Check API status:"
echo "  sudo systemctl status darkweb-api"
echo ""
echo "Next steps:"
echo "1. Follow SIMPLE_PATCH_GUIDE.txt to update advanced_scanner.py"
echo "   (Change API endpoints from /cgi-bin/ to /api/)"
echo "2. Run ./run_scanner.sh"
echo "3. Test at http://localhost/"
echo ""
