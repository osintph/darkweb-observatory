import json
from datetime import datetime, timedelta
from collections import Counter

ALERT_HISTORY_FILE = "/var/www/html/alert_history.json"
ALERT_STATS_HTML = "/var/www/html/alert_statistics.html"

def load_alert_history():
    try:
        with open(ALERT_HISTORY_FILE, 'r') as f:
            data = json.load(f)
            # Ensure structure exists
            if 'all_alerts' not in data:
                data['all_alerts'] = []
            if 'last_alerts' not in data:
                data['last_alerts'] = {}
            return data
    except:
        return {'last_alerts': {}, 'all_alerts': []}

def generate_alert_statistics():
    """Generate alert statistics dashboard"""
    
    history = load_alert_history()
    all_alerts = history.get('all_alerts', [])
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not all_alerts:
        # Generate placeholder page
        html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Alert Statistics - Dark Web Observatory</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="300">
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0d0d0d; color: #e0e0e0; padding: 20px; }}
            h1 {{ color: #00ff00; text-transform: uppercase; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .back-link {{ color: #00aaff; text-decoration: none; }}
            .back-link:hover {{ text-decoration: underline; }}
            .placeholder {{ background: #1a1a1a; padding: 40px; text-align: center; border: 2px solid #333; margin: 40px 0; }}
            .placeholder h2 {{ color: #ffa500; margin-bottom: 20px; }}
            .placeholder p {{ color: #888; font-size: 1.1em; }}
        </style>
    </head>
    <body>
        <h1>📊 Alert Statistics Dashboard</h1>
        <p><a href="index.html" class="back-link">&larr; Back to Dashboard</a> | Last Updated: {timestamp}</p>
        
        <div class="placeholder">
            <h2>No Alert Data Yet</h2>
            <p>Alert statistics will appear here once the system has collected alert data.</p>
            <p>The scanner is running and will populate this page automatically.</p>
        </div>
        
        <p style="margin-top:50px; font-size: 0.8em; color: #555;">
            <i>Automated Threat Intelligence Sentinel | Alert Analytics Module</i>
        </p>
    </body>
    </html>
        """
        
        try:
            with open(ALERT_STATS_HTML, 'w') as f:
                f.write(html)
            print(f"[+] Alert statistics placeholder generated: {ALERT_STATS_HTML}")
        except Exception as e:
            print(f"[!] Failed to generate alert stats: {e}")
        return
    
    # Calculate statistics
    total_alerts = len(all_alerts)
    
    # Alert types breakdown
    alert_types = Counter([a['type'] for a in all_alerts])
    
    # Targets with most alerts
    target_alerts = Counter([a['target'] for a in all_alerts])
    
    # Recent alerts (last 24 hours)
    now = datetime.now()
    recent_alerts = [a for a in all_alerts 
                    if (now - datetime.fromisoformat(a['timestamp'])) < timedelta(hours=24)]
    
    # Alerts by hour (last 24h)
    hour_counts = {}
    for a in recent_alerts:
        hour = datetime.fromisoformat(a['timestamp']).hour
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Alert Statistics - Dark Web Observatory</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="300">
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0d0d0d; color: #e0e0e0; padding: 20px; }}
            h1 {{ color: #00ff00; text-transform: uppercase; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            h2 {{ color: #ffa500; margin-top: 30px; border-bottom: 1px solid #444; padding-bottom: 8px; }}
            .back-link {{ color: #00aaff; text-decoration: none; }}
            .back-link:hover {{ text-decoration: underline; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat-card {{ background: #1a1a1a; padding: 20px; border-left: 4px solid #00ff00; }}
            .stat-label {{ color: #888; font-size: 0.9em; text-transform: uppercase; }}
            .stat-value {{ color: #00ff00; font-size: 2em; font-weight: bold; margin-top: 5px; }}
            .chart-container {{ background: #1a1a1a; padding: 20px; margin: 20px 0; }}
            .bar-chart {{ margin: 20px 0; }}
            .bar-item {{ margin: 10px 0; }}
            .bar-label {{ color: #e0e0e0; display: inline-block; width: 200px; }}
            .bar-visual {{ display: inline-block; background: #00ff00; height: 20px; }}
            .bar-count {{ color: #00ff00; margin-left: 10px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #333; padding: 10px; text-align: left; }}
            th {{ background: #1a1a1a; color: #fff; text-transform: uppercase; }}
            tr:nth-child(even) {{ background: #111; }}
            .alert-down {{ color: #ff3333; }}
            .alert-recovery {{ color: #00ff00; }}
            .alert-iocs {{ color: #ffa500; }}
            .alert-change {{ color: #00aaff; }}
            .alert-uptime {{ color: #ffff00; }}
        </style>
    </head>
    <body>
        <h1>📊 Alert Statistics Dashboard</h1>
        <p><a href="index.html" class="back-link">&larr; Back to Dashboard</a> | Last Updated: {timestamp}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Alerts</div>
                <div class="stat-value">{total_alerts}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Alerts (24h)</div>
                <div class="stat-value">{len(recent_alerts)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Most Active Target</div>
                <div class="stat-value" style="font-size: 1.2em;">{target_alerts.most_common(1)[0][0] if target_alerts else 'N/A'}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Most Common Alert</div>
                <div class="stat-value" style="font-size: 1.2em;">{alert_types.most_common(1)[0][0].upper() if alert_types else 'N/A'}</div>
            </div>
        </div>
        
        <h2>Alert Types Breakdown</h2>
        <div class="chart-container">
            <div class="bar-chart">
    """
    
    # Alert types chart
    max_count = max(alert_types.values()) if alert_types else 1
    for alert_type, count in alert_types.most_common():
        bar_width = int((count / max_count) * 500)
        html += f"""
                <div class="bar-item">
                    <span class="bar-label">{alert_type.upper()}</span>
                    <span class="bar-visual" style="width: {bar_width}px;"></span>
                    <span class="bar-count">{count}</span>
                </div>
        """
    
    html += """
            </div>
        </div>
        
        <h2>Top 10 Targets by Alert Frequency</h2>
        <div class="chart-container">
            <div class="bar-chart">
    """
    
    # Targets chart
    for target, count in target_alerts.most_common(10):
        bar_width = int((count / max(target_alerts.values())) * 500)
        html += f"""
                <div class="bar-item">
                    <span class="bar-label">{target}</span>
                    <span class="bar-visual" style="width: {bar_width}px;"></span>
                    <span class="bar-count">{count}</span>
                </div>
        """
    
    html += """
            </div>
        </div>
        
        <h2>Recent Alerts (Last 50)</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 20%">Timestamp</th>
                    <th style="width: 15%">Type</th>
                    <th style="width: 25%">Target</th>
                    <th style="width: 40%">Message</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Recent alerts table
    for alert in reversed(all_alerts[-50:]):
        timestamp_str = datetime.fromisoformat(alert['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        alert_type = alert['type']
        color_class = f"alert-{alert_type}"
        
        html += f"""
                <tr>
                    <td>{timestamp_str}</td>
                    <td class="{color_class}">{alert_type.upper()}</td>
                    <td>{alert['target']}</td>
                    <td>{alert['message']}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <p style="margin-top:50px; font-size: 0.8em; color: #555;">
            <i>Automated Threat Intelligence Sentinel | Alert Analytics Module</i>
        </p>
    </body>
    </html>
    """
    
    # Save HTML
    try:
        with open(ALERT_STATS_HTML, 'w') as f:
            f.write(html)
        print(f"[+] Alert statistics generated: {ALERT_STATS_HTML}")
    except Exception as e:
        print(f"[!] Failed to generate alert stats: {e}")

if __name__ == "__main__":
    generate_alert_statistics()

