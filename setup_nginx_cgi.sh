#!/bin/bash
# Setup CGI for nginx

echo "[*] Setting up CGI support for nginx..."

# Install fcgiwrap (CGI wrapper for nginx)
sudo apt-get update
sudo apt-get install -y fcgiwrap

# Copy scripts to dark-monitor directory
cp on_demand_scan_fcgi.py ~/dark-monitor/on_demand_scan.py
cp refresh_news_fcgi.py ~/dark-monitor/refresh_news.py

chmod +x ~/dark-monitor/on_demand_scan.py
chmod +x ~/dark-monitor/refresh_news.py

# Create CGI directory
sudo mkdir -p /var/www/html/cgi-bin

# Create symlinks
sudo ln -sf ~/dark-monitor/on_demand_scan.py /var/www/html/cgi-bin/on_demand_scan.py
sudo ln -sf ~/dark-monitor/refresh_news.py /var/www/html/cgi-bin/refresh_news.py

# Create nginx CGI config
sudo tee /etc/nginx/conf.d/cgi.conf > /dev/null << 'NGINX_CONF'
location ~ ^/cgi-bin/.*\.py$ {
    gzip off;
    root /var/www/html;
    fastcgi_pass unix:/var/run/fcgiwrap.socket;
    include fastcgi_params;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
}
NGINX_CONF

# Start fcgiwrap
sudo systemctl enable fcgiwrap
sudo systemctl restart fcgiwrap

# Restart nginx
sudo systemctl restart nginx

echo ""
echo "[✓] CGI setup complete!"
echo ""
echo "Files installed:"
echo "  - ~/dark-monitor/on_demand_scan.py"
echo "  - ~/dark-monitor/refresh_news.py"
echo ""
echo "Test at: http://localhost/"
