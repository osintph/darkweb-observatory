#!/bin/bash
#
# Auto-patch script for adding new dashboard features
# This will modify your advanced_scanner.py in place
#

SCANNER_FILE="advanced_scanner.py"

if [ ! -f "$SCANNER_FILE" ]; then
    echo "[!] Error: $SCANNER_FILE not found in current directory"
    exit 1
fi

echo "[*] Backing up original file..."
cp "$SCANNER_FILE" "${SCANNER_FILE}.backup.$(date +%s)"

echo "[*] Adding CSS styles..."
# Find the closing </style> tag and insert new CSS before it
sed -i '/<\/style>/i\
            /* NEW FEATURES: On-Demand Scanner + News Refresh */\
            .on-demand-scanner {\
                margin: 40px 0;\
                padding: 25px;\
                background: #1a1a1a;\
                border-left: 4px solid #00aaff;\
                border-radius: 5px;\
            }\
            .on-demand-scanner h2 {\
                color: #00aaff;\
                margin: 0 0 10px 0;\
                font-size: 1.4em;\
                text-transform: uppercase;\
            }\
            .scanner-input-row {\
                display: flex;\
                gap: 10px;\
            }\
            .ondemand-input {\
                flex: 1;\
                background: #0a0a0a;\
                border: 1px solid #333;\
                color: #e0e0e0;\
                padding: 12px 15px;\
                font-family: '"'"'Courier New'"'"', monospace;\
                font-size: 1em;\
            }\
            .ondemand-input:focus {\
                border-color: #00aaff;\
                outline: none;\
            }\
            .scan-btn {\
                background: #003366;\
                border: 1px solid #00aaff;\
                color: #00aaff;\
                padding: 12px 24px;\
                cursor: pointer;\
                font-family: '"'"'Courier New'"'"', monospace;\
                font-size: 1em;\
                font-weight: bold;\
                transition: all 0.3s;\
            }\
            .scan-btn:hover {\
                background: #004488;\
            }\
            .scan-btn:disabled {\
                opacity: 0.5;\
                cursor: not-allowed;\
            }\
            .scan-result-card {\
                background: #0a0a0a;\
                border: 1px solid #333;\
                padding: 20px;\
                margin-top: 15px;\
                border-left: 3px solid #00ff00;\
            }\
            .scan-error-card {\
                background: #1a0000;\
                border: 1px solid #ff3333;\
                padding: 20px;\
                color: #ff3333;\
                border-left: 3px solid #ff3333;\
            }\
            .refresh-news-btn {\
                background: #1a1000;\
                border: 1px solid #ffa500;\
                color: #ffa500;\
                padding: 8px 16px;\
                cursor: pointer;\
                font-family: '"'"'Courier New'"'"', monospace;\
                font-size: 0.9em;\
                transition: all 0.3s;\
            }\
            .refresh-news-btn:hover {\
                background: #2a2000;\
            }\
            .refresh-news-btn:disabled {\
                opacity: 0.5;\
                cursor: not-allowed;\
            }' "$SCANNER_FILE"

echo "[*] Adding On-Demand Scanner HTML..."
# Add on-demand scanner section before the news widget
sed -i '/<div class="news-widget">/i\
        <div class="on-demand-scanner">\
            <h2>🔍 On-Demand Deep Scan</h2>\
            <p style="color: #888; margin-bottom: 15px;">Enter any .onion URL to perform a one-time deep scan and generate an instant report.</p>\
            \
            <div class="scanner-input-row">\
                <input \
                    type="text" \
                    id="ondemandUrl" \
                    class="ondemand-input" \
                    placeholder="http://example.onion or https://example.onion"\
                    onkeypress="if(event.key==='"'"'Enter'"'"') startOnDemandScan()"\
                >\
                <button onclick="startOnDemandScan()" id="scanBtn" class="scan-btn">\
                    Scan Now →\
                </button>\
            </div>\
            \
            <div id="scanStatus" style="margin-top: 15px; display: none;"></div>\
            <div id="scanResults" style="margin-top: 20px;"></div>\
        </div>\
' "$SCANNER_FILE"

echo "[*] Adding News Refresh button..."
# Replace the news title line with one that includes the refresh button
sed -i 's|<h2 class="news-title">📰 Latest Cybersecurity News</h2>|<div style="display: flex; justify-content: space-between; align-items: center;">\
                    <h2 class="news-title" style="margin: 0;">📰 Latest Cybersecurity News</h2>\
                    <button onclick="refreshNewsFeed()" id="refreshNewsBtn" class="refresh-news-btn">\
                        🔄 Refresh Feed\
                    </button>\
                </div>|' "$SCANNER_FILE"

echo "[*] Adding JavaScript functions..."
# Add JavaScript functions before the closing </script> tag at the end
# First, find the line number of the last </script> before </body>
SCRIPT_LINE=$(grep -n '</script>' "$SCANNER_FILE" | tail -1 | cut -d: -f1)

# Create temp file with the JavaScript
cat > /tmp/new_functions.js << 'JSEOF'
        // ON-DEMAND SCANNER (NGINX VERSION)
        function startOnDemandScan() {
            const url = document.getElementById('ondemandUrl').value.trim();
            const btn = document.getElementById('scanBtn');
            const statusDiv = document.getElementById('scanStatus');
            const resultsDiv = document.getElementById('scanResults');
            
            if (!url) {
                alert('Please enter a .onion URL');
                return;
            }
            
            if (!url.includes('.onion')) {
                alert('Invalid URL: Must be a .onion address');
                return;
            }
            
            btn.disabled = true;
            btn.innerHTML = '⏳ Scanning...';
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = '<p style="color: #ffa500;">🔄 Scanning target... This may take up to 90 seconds.</p>';
            resultsDiv.innerHTML = '';
            
            fetch('/api/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: url })
            })
            .then(response => response.json())
            .then(data => {
                btn.disabled = false;
                btn.innerHTML = 'Scan Now →';
                statusDiv.style.display = 'none';
                
                if (data.success) {
                    displayScanResults(data);
                } else {
                    resultsDiv.innerHTML = '<div class="scan-error-card"><h3 style="margin-top: 0;">❌ Scan Failed</h3><p><strong>Error:</strong> ' + data.error + '</p></div>';
                }
            })
            .catch(error => {
                btn.disabled = false;
                btn.innerHTML = 'Scan Now →';
                statusDiv.style.display = 'none';
                resultsDiv.innerHTML = '<div class="scan-error-card"><h3>❌ Request Failed</h3><p>' + error.message + '</p></div>';
            });
        }

        function displayScanResults(data) {
            const resultsDiv = document.getElementById('scanResults');
            const timestamp = new Date(data.timestamp).toLocaleString();
            
            let html = '<div class="scan-result-card"><h3 style="color: #00ff00; margin-top: 0;">✓ Scan Complete</h3>';
            html += '<div style="margin: 15px 0; padding: 10px; background: #0d0d0d; border-left: 3px solid #333;">';
            html += '<p style="margin: 5px 0;"><strong>URL:</strong> ' + data.url + '</p>';
            html += '<p style="margin: 5px 0;"><strong>Scanned:</strong> ' + timestamp + '</p>';
            html += '<p style="margin: 5px 0;"><strong>HTTP Status:</strong> ' + data.http_code + '</p>';
            html += '<p style="margin: 5px 0;"><strong>Page Title:</strong> ' + data.title + '</p></div>';
            
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 20px 0;">';
            html += '<div style="background: #0d0d0d; padding: 12px; text-align: center; border: 1px solid #333;"><div style="color: #888; font-size: 0.85em;">EMAILS</div><div style="color: ' + (data.emails.length > 0 ? '#ff3333' : '#00ff00') + '; font-size: 1.5em; font-weight: bold;">' + data.emails.length + '</div></div>';
            html += '<div style="background: #0d0d0d; padding: 12px; text-align: center; border: 1px solid #333;"><div style="color: #888; font-size: 0.85em;">BITCOIN</div><div style="color: ' + (data.bitcoin_addresses.length > 0 ? '#ff3333' : '#00ff00') + '; font-size: 1.5em; font-weight: bold;">' + data.bitcoin_addresses.length + '</div></div>';
            html += '<div style="background: #0d0d0d; padding: 12px; text-align: center; border: 1px solid #333;"><div style="color: #888; font-size: 0.85em;">LINKED ONIONS</div><div style="color: #00aaff; font-size: 1.5em; font-weight: bold;">' + data.linked_onions.length + '</div></div>';
            html += '<div style="background: #0d0d0d; padding: 12px; text-align: center; border: 1px solid #333;"><div style="color: #888; font-size: 0.85em;">TECHNOLOGIES</div><div style="color: #00ff00; font-size: 1.5em; font-weight: bold;">' + data.technologies.length + '</div></div></div>';
            
            if (data.emails.length > 0) {
                html += '<h4 style="color: #ffa500; margin-top: 20px;">📧 Email Addresses</h4><div style="background: #0d0d0d; padding: 10px;">';
                data.emails.forEach(email => { html += '<div style="padding: 5px; color: #ff3333;">• ' + email + '</div>'; });
                html += '</div>';
            }
            
            if (data.bitcoin_addresses.length > 0) {
                html += '<h4 style="color: #ffa500; margin-top: 20px;">₿ Bitcoin Addresses</h4><div style="background: #0d0d0d; padding: 10px;">';
                data.bitcoin_addresses.forEach(btc => { html += '<div style="padding: 5px; color: #ff3333;">• ' + btc + '</div>'; });
                html += '</div>';
            }
            
            if (data.linked_onions.length > 0) {
                html += '<h4 style="color: #ffa500; margin-top: 20px;">🧅 Linked Onions</h4><div style="background: #0d0d0d; padding: 10px;">';
                data.linked_onions.forEach(onion => { html += '<div style="padding: 5px; color: #00aaff;">• ' + onion + '</div>'; });
                html += '</div>';
            }
            
            html += '<p style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #333; color: #666; font-size: 0.85em;"><em>One-time scan. Not stored.</em></p></div>';
            resultsDiv.innerHTML = html;
        }

        // NEWS REFRESH (NGINX VERSION)
        function refreshNewsFeed() {
            const btn = document.getElementById('refreshNewsBtn');
            const originalText = btn.innerHTML;
            
            btn.disabled = true;
            btn.innerHTML = '⏳ Refreshing...';
            
            fetch('/api/refresh-news', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    btn.innerHTML = '✓ Updated!';
                    setTimeout(() => { location.reload(); }, 1000);
                } else {
                    btn.innerHTML = '✗ Failed';
                    setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 2000);
                }
            })
            .catch(error => {
                btn.innerHTML = '✗ Error';
                setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 2000);
            });
        }
JSEOF

# Insert the JavaScript before the </script> tag
sed -i "${SCRIPT_LINE}r /tmp/new_functions.js" "$SCANNER_FILE"

# Clean up
rm /tmp/new_functions.js

echo ""
echo "[✓] Patch complete!"
echo ""
echo "Changes made:"
echo "  • Added CSS for on-demand scanner and news refresh button"
echo "  • Added on-demand scanner HTML section"
echo "  • Added news refresh button to news widget"
echo "  • Added JavaScript functions for both features"
echo ""
echo "Backup saved to: ${SCANNER_FILE}.backup.*"
echo ""
echo "Now run: ./run_scanner.sh"
echo ""
