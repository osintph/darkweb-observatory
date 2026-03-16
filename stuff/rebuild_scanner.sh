#!/usr/bin/env python3
"""
Complete the missing HTML generation in advanced_scanner.py
"""

# Find where the incomplete section is and add the complete HTML generation
incomplete_marker = "# (Rest of the HTML generation code continues - character limit reached)"

with open('/home/osint_lab/dark-monitor/advanced_scanner.py', 'r') as f:
    content = f.read()

if incomplete_marker not in content:
    print("[!] Incomplete marker not found. HTML generation might already be complete.")
    exit(1)

# Find the position
marker_pos = content.find(incomplete_marker)
end_of_function_pos = content.find("if __name__ == \"__main__\":", marker_pos)

# Create the complete HTML generation code
html_generation_code = '''
    
    # Generate main dashboard HTML (COMPLETE VERSION)
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dark Web Observatory - Threat Intelligence Platform</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="900">
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0d0d0d; color: #e0e0e0; padding: 20px; }}
            h1 {{ color: #00ff00; text-transform: uppercase; letter-spacing: 2px; border-bottom: 2px solid #00ff00; padding-bottom: 10px; }}
            .intel-link {{ color: #00aaff; text-decoration: none; margin: 0 5px; }}
            .intel-link:hover {{ text-decoration: underline; }}
            .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; padding: 20px; background: #0a0a0a; border-left: 4px solid #00ff00; }}
            .summary-box {{ background: #1a1a1a; padding: 15px; text-align: center; border: 1px solid #333; }}
            .summary-label {{ color: #888; font-size: 0.9em; text-transform: uppercase; }}
            .summary-value {{ color: #00ff00; font-size: 2em; font-weight: bold; margin-top: 5px; }}
            .filter-buttons {{ margin: 20px 0; }}
            .filter-btn {{ background: #1a1a1a; color: #888; border: 1px solid #333; padding: 8px 15px; margin: 5px; cursor: pointer; text-transform: uppercase; font-size: 0.9em; }}
            .filter-btn:hover {{ background: #222; color: #00ff00; }}
            .filter-btn.active {{ background: #003300; color: #00ff00; border-color: #00ff00; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #333; padding: 12px; text-align: left; }}
            th {{ background: #0a0a0a; color: #fff; text-transform: uppercase; position: sticky; top: 0; }}
            tr:nth-child(even) {{ background: #111; }}
            .status-up {{ color: #00ff00; font-weight: bold; }}
            .status-down {{ color: #ff3333; font-weight: bold; }}
            .status-issues {{ color: #ffa500; font-weight: bold; }}
            .uptime-bar {{ width: 100%; height: 20px; background: #1a1a1a; border: 1px solid #333; }}
            .uptime-fill {{ height: 100%; transition: width 0.3s; }}
            .change-badge {{ background: #ffa500; color: #000; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; font-weight: bold; }}
            .view-report-btn {{ background: #003300; color: #00ff00; padding: 5px 15px; text-decoration: none; border: 1px solid #00ff00; display: inline-block; }}
            .view-report-btn:hover {{ background: #004400; }}
        </style>
    </head>
    <body>
        <h1>DARK WEB OBSERVATORY - THREAT INTELLIGENCE PLATFORM</h1>
        
        <p>Last Scan: {timestamp} | <a href="intelligence.json" class="intel-link">Download Intel Feed (JSON)</a>{deep_scan_link}{ioc_link}{alert_stats_link}{trends_link}{threat_feed_link}</p>
        
        <div class="summary-grid">
            <div class="summary-box">
                <div class="summary-label">📊 Intelligence Summary (Last Scan)</div>
                <div class="summary-value" style="font-size: 1.2em; color: #ffa500;">STATUS OVERVIEW</div>
            </div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-box">
                <div class="summary-label">Total Targets</div>
                <div class="summary-value">{intel_summary['total_targets']}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">Targets UP</div>
                <div class="summary-value" style="color: #00ff00;">{intel_summary['up_targets']}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">Deep Scans Active</div>
                <div class="summary-value" style="color: #00aaff;">{intel_summary['deep_scan_count']}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">IOCs Discovered</div>
                <div class="summary-value" style="color: #ff3333;">{intel_summary['total_iocs']}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">Email Addresses</div>
                <div class="summary-value">{intel_summary['total_emails']}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">Bitcoin Addresses</div>
                <div class="summary-value" style="color: #ffa500;">{intel_summary['total_btc']}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">PGP Keys</div>
                <div class="summary-value">{intel_summary['total_pgp']}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">Changes Detected</div>
                <div class="summary-value" style="color: #ffa500;">{intel_summary['changes_detected']}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">Avg Response Time</div>
                <div class="summary-value" style="font-size: 1.5em;">{intel_summary['avg_latency']}s</div>
            </div>
        </div>
        
        <div class="filter-buttons">
            <strong style="color: #888;">FILTER BY CATEGORY:</strong>
            <button class="filter-btn active" onclick="filterTable('all')">ALL TARGETS {intel_summary['total_targets']}</button>
'''
    
    # Add category filter buttons
    for cat, count in intel_summary['categories'].items():
        html_generation_code += f'''            <button class="filter-btn" onclick="filterTable('{cat}')">{cat.upper()} {count}</button>\n'''
    
    html_generation_code += '''        </div>
        
        <table id="targetTable">
            <thead>
                <tr>
                    <th style="width: 12%">Target Name</th>
                    <th style="width: 25%">Onion Address</th>
                    <th style="width: 8%">Status</th>
                    <th style="width: 12%">Uptime (24h)</th>
                    <th style="width: 8%">Latency</th>
                    <th style="width: 10%">Server</th>
                    <th style="width: 12%">Last Changed</th>
                    <th style="width: 18%">Page Title / Error</th>
                    <th style="width: 10%">Deep Scan</th>
                </tr>
            </thead>
            <tbody>
'''
    
    html_generation_code += '''
    """
    
    # Generate table rows
    for item in all_results:
        result = item['result']
        status_class = "status-up" if result['status'] == "UP" else "status-down" if result['status'] == "DOWN" else "status-issues"
        
        # Uptime bar
        uptime = item.get('uptime_24h', 0)
        uptime_color = "#00ff00" if uptime >= 90 else "#ffa500" if uptime >= 70 else "#ff3333"
        uptime_bar = f'<div class="uptime-bar"><div class="uptime-fill" style="width: {uptime}%; background: {uptime_color};"></div></div>{uptime}%'
        
        # Change badge
        change_info = item.get('change_info', {})
        change_badge = ''
        if change_info.get('changed'):
            change_type = change_info.get('change_type', 'unknown').upper()
            change_badge = f'<span class="change-badge">{change_type}</span>'
        
        # Deep scan link
        if item['deep_scan_enabled']:
            filename = sanitize_filename(item['name'])
            deep_scan_cell = f'<a href="deep_scans/{filename}.html" class="view-report-btn">View Report →</a>'
        else:
            deep_scan_cell = '<span style="color: #555;">Not enabled</span>'
        
        last_changed = change_info.get('last_changed', '-')[:16].replace('T', ' ') if change_info.get('last_changed') else '-'
        
        html += f"""
                <tr data-category="{item['category']}">
                    <td><strong style="color: #00aaff;">[{item['category'].upper()}]</strong><br>{item['name']} {change_badge}</td>
                    <td style="word-break: break-all; font-size: 0.85em; color: #888;">{item['url']}</td>
                    <td class="{status_class}">{result['status']}</td>
                    <td>{uptime_bar}</td>
                    <td>{result['latency']}</td>
                    <td>{result['server']}</td>
                    <td>{last_changed}</td>
                    <td style="font-size: 0.9em;">{result['title']}</td>
                    <td>{deep_scan_cell}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <!-- Cybersecurity News Feed Widget -->
        <div style="background: #1a1a1a; padding: 20px; margin: 30px 0; border-left: 4px solid #ffa500;">
            <h2 style="color: #ffa500; border-bottom: 1px solid #444; padding-bottom: 8px; margin-top: 0;">
                📰 Latest Cybersecurity News
            </h2>
            <div id="news-feed-container">
                <p style="color: #888;">Loading news feed...</p>
            </div>
        </div>
        
        <script>
        function filterTable(category) {
            const rows = document.querySelectorAll('#targetTable tbody tr');
            const buttons = document.querySelectorAll('.filter-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            rows.forEach(row => {
                if (category === 'all' || row.dataset.category === category) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
        
        // Load news feed
        fetch('news_feed.json')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('news-feed-container');
                const articles = data.articles.slice(0, 5);
                
                if (!articles || articles.length === 0) {
                    container.innerHTML = '<p style="color: #888;">No news articles available.</p>';
                    return;
                }
                
                let html = '<div style="display: grid; gap: 15px;">';
                
                articles.forEach(article => {
                    const cleanTitle = (article.title || '').replace(/<[^>]*>/g, '');
                    const cleanDesc = (article.description || '').replace(/<[^>]*>/g, '').substring(0, 150) + '...';
                    const publishDate = article.published ? article.published.substring(0, 16) : 'Unknown';
                    
                    html += '<div style="background: #0a0a0a; padding: 15px; border-left: 3px solid #00aaff;">';
                    html += '<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">';
                    html += '<strong style="color: #00aaff; font-size: 1.05em;">' + cleanTitle + '</strong>';
                    html += '<span style="color: #666; font-size: 0.85em; white-space: nowrap; margin-left: 10px;">' + article.source + '</span>';
                    html += '</div>';
                    html += '<p style="color: #ccc; font-size: 0.9em; margin: 8px 0;">' + cleanDesc + '</p>';
                    html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">';
                    html += '<span style="color: #888; font-size: 0.85em;">📅 ' + publishDate + '</span>';
                    html += '<a href="' + article.link + '" target="_blank" style="color: #00ff00; text-decoration: none; font-size: 0.9em;" rel="noopener noreferrer">Read More →</a>';
                    html += '</div></div>';
                });
                
                html += '</div>';
                container.innerHTML = html;
            })
            .catch(error => {
                console.error('Error loading news feed:', error);
                document.getElementById('news-feed-container').innerHTML = '<p style="color: #ff3333;">Failed to load news feed.</p>';
            });
        </script>
        
        <p style="margin-top:50px; font-size: 0.8em; color: #555;">
            <i>Automated Threat Intelligence Sentinel | OSINT 24/7 | Powered by Tor Network</i>
        </p>
    </body>
    </html>
    """
    
    # Write main HTML
    try:
        with open(OUTPUT_HTML, 'w') as f:
            f.write(html)
        print(f"[+] Main dashboard generated: {OUTPUT_HTML}")
    except Exception as e:
        print(f"[!] Failed to write main HTML: {e}")
    
    # Write JSON feed
    json_data = {
        'scan_timestamp': timestamp,
        'intelligence_summary': intel_summary,
        'targets': all_results
    }
    
    try:
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(json_data, f, indent=2)
        print(f"[+] Intelligence JSON

