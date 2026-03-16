import json
import os
import datetime

# Configuration
UPTIME_HISTORY_FILE = "/var/www/html/uptime_history.json"
CHANGE_HISTORY_FILE = "/var/www/html/change_history.json"
OUTPUT_HTML = "/var/www/html/historical_trends.html"

def load_json(filepath):
    if not os.path.exists(filepath): return {}
    try:
        with open(filepath, 'r') as f: return json.load(f)
    except: return {}

def generate_historical_trends():
    print("[*] Generating historical trends analysis...")
    
    uptime_data = load_json(UPTIME_HISTORY_FILE)
    change_data = load_json(CHANGE_HISTORY_FILE)
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Historical Intelligence Trends</title>
        <style>
            body { font-family: 'Courier New', monospace; background: #0d0d0d; color: #e0e0e0; padding: 20px; }
            h1 { color: #00ff00; border-bottom: 2px solid #333; padding-bottom: 10px; }
            .chart-container { background: #1a1a1a; padding: 20px; margin-bottom: 20px; border-left: 4px solid #00aaff; }
            .trend-card { background: #111; padding: 15px; margin-bottom: 10px; border: 1px solid #333; }
            .trend-title { color: #ffa500; font-weight: bold; margin-bottom: 5px; }
            .bar-container { background: #333; height: 20px; width: 100%; margin-top: 5px; }
            .bar-fill { height: 100%; background: #00ff00; transition: width 0.5s; }
            .timestamp { color: #666; font-size: 0.8em; float: right; }
            .back-link { color: #00aaff; text-decoration: none; margin-bottom: 20px; display: inline-block; }
        </style>
    </head>
    <body>
        <a href="index.html" class="back-link">&larr; Back to Dashboard</a>
        <h1>📉 Historical Intelligence Trends</h1>
        <p>Analysis of target stability and content volatility over time.</p>
    """

    # --- UPTIME TRENDS ---
    html += '<div class="chart-container"><h2>Target Stability (Uptime Consistency)</h2>'
    
    for target, data in uptime_data.items():
        checks = data.get('checks', [])
        if not checks: continue
        
        # Calculate uptime percentage
        up_count = sum(1 for c in checks if c.get('up', False))
        total = len(checks)
        percentage = round((up_count / total) * 100, 1) if total > 0 else 0
        
        # Color coding
        color = "#00ff00"
        if percentage < 90: color = "#ffa500"
        if percentage < 70: color = "#ff3333"
        
        html += f"""
        <div class="trend-card">
            <div class="trend-title">{target} <span style="float:right; color:{color}">{percentage}%</span></div>
            <div style="font-size: 0.8em; color: #888;">Based on last {total} scans</div>
            <div class="bar-container">
                <div class="bar-fill" style="width: {percentage}%; background: {color};"></div>
            </div>
        </div>
        """
    html += '</div>'

    # --- VOLATILITY TRENDS (CHANGES) ---
    html += '<div class="chart-container" style="border-left-color: #ff3333;"><h2>Content Volatility (Change Frequency)</h2>'
    
    for target, data in change_data.items():
        changes = data.get('changes', [])
        count = len(changes)
        last_change = "Never"
        
        if changes:
            # Handle both 'timestamp' and 'ts' keys safely
            last_ts = changes[-1].get('timestamp') or changes[-1].get('ts')
            if last_ts:
                last_change = last_ts.replace('T', ' ')[:16]
        
        html += f"""
        <div class="trend-card">
            <div class="trend-title">{target}</div>
            <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                <span>Total Detected Changes: <strong style="color: #fff;">{count}</strong></span>
                <span class="timestamp">Last Change: {last_change}</span>
            </div>
        </div>
        """
        
    html += """
    </div>
    <p style="text-align: center; color: #555; margin-top: 30px;">Dark Web Observatory | Historical Analysis Module</p>
    </body>
    </html>
    """
    
    try:
        with open(OUTPUT_HTML, 'w') as f:
            f.write(html)
        print(f"[+] Historical trends generated: {OUTPUT_HTML}")
    except Exception as e:
        print(f"[!] Failed to write trends HTML: {e}")

if __name__ == "__main__":
    generate_historical_trends()
