#!/usr/bin/env python3

# Read the current file
with open('advanced_scanner.py', 'r') as f:
    lines = f.readlines()

# Find line 1598 (the line after threat_feed_link definition)
insert_pos = None
for i, line in enumerate(lines):
    if 'threat_feed_link = \' | <a href="threat_feeds.html"' in line:
        insert_pos = i + 1
        break

if insert_pos is None:
    print("Could not find insertion point!")
    exit(1)

# The complete HTML generation code
html_code = '''
    # Generate main dashboard HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Dark Web Threat Intelligence - Dashboard</title>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Courier New', monospace; background: #0d0d0d; color: #e0e0e0; padding: 20px; }}
        .header {{ text-align: center; padding: 30px 0; border-bottom: 2px solid #333; margin-bottom: 30px; }}
        h1 {{ color: #00ff00; text-transform: uppercase; }}
        .nav-links {{ margin-top: 15px; }}
        .nav-links a {{ color: #00aaff; text-decoration: none; margin: 0 10px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 30px 0; }}
        .summary-box {{ background: #1a1a1a; padding: 20px; border-left: 4px solid #00ff00; }}
        .summary-label {{ color: #888; text-transform: uppercase; }}
        .summary-value {{ color: #00ff00; font-size: 2em; font-weight: bold; }}
        .controls {{ margin: 20px 0; padding: 15px; background: #1a1a1a; }}
        .filter-btn {{ background: #0a0a0a; color: #00aaff; border: 1px solid #00aaff; padding: 8px 15px; margin: 5px; cursor: pointer; }}
        .filter-btn.active {{ background: #003366; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: #1a1a1a; }}
        th {{ background: #0a0a0a; color: #fff; padding: 15px; border: 1px solid #333; }}
        td {{ padding: 12px; border: 1px solid #333; }}
        tr:nth-child(even) {{ background: #151515; }}
        .status {{ padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
        .status-up {{ background: #003300; color: #00ff00; }}
        .status-down {{ background: #330000; color: #ff3333; }}
        .status-issues {{ background: #332200; color: #ffaa00; }}
        .uptime-bar {{ width: 100%; height: 20px; background: #0a0a0a; border: 1px solid #333; }}
        .uptime-fill {{ height: 100%; }}
        .view-report-btn {{ background: #003300; color: #00ff00; padding: 5px 12px; text-decoration: none; border: 1px solid #00ff00; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dark Web Threat Intelligence Platform</h1>
        <div class="nav-links">
            Last Scan: {timestamp} | 
            <a href="intelligence.json" download>Download JSON</a>{deep_scan_link}{ioc_link}{alert_stats_link}{trends_link}{threat_feed_link}
        </div>
    </div>
    <div class="summary-grid">
        <div class="summary-box"><div class="summary-label">Targets</div><div class="summary-value">{summary['total_targets']}</div></div>
        <div class="summary-box"><div class="summary-label">Online</div><div class="summary-value">{summary['up_targets']}</div></div>
        <div class="summary-box"><div class="summary-label">Offline</div><div class="summary-value">{summary['down_targets']}</div></div>
        <div class="summary-box"><div class="summary-label">Uptime</div><div class="summary-value">{summary['uptime_percentage']}%</div></div>
    </div>
    <div class="controls">
        <strong>Filter:</strong>
        <button class="filter-btn active" onclick="filterTable('all')">ALL</button>
"""
    for cat in sorted(summary['categories'].keys()):
        html += f'        <button class="filter-btn" onclick="filterTable(\\'{cat}\\')">{cat.upper()}</button>\\n'
    
    html += """    </div>
    <table id="targetsTable">
        <thead><tr><th>Target</th><th>Category</th><th>Status</th><th>Latency</th><th>Server</th><th>Uptime</th><th>Deep Scan</th></tr></thead>
        <tbody>
"""
    for result in all_results:
        status_class = 'status-up' if result['status'] == 'UP' else 'status-down' if result['status'] == 'DOWN' else 'status-issues'
        uptime = result.get('uptime_24h', 0)
        uptime_color = '#00ff00' if uptime >= 90 else '#ffaa00' if uptime >= 70 else '#ff3333'
        
        deep_scan_cell = ''
        if result.get('deep_scan_enabled'):
            filename = sanitize_filename(result['name'])
            deep_scan_cell = f'<a href="deep_scans/{filename}.html" class="view-report-btn">View</a>'
        else:
            deep_scan_cell = 'N/A'
        
        html += f"""        <tr data-category="{result['category']}">
            <td>{result['name']}</td><td>{result['category']}</td>
            <td><span class="status {status_class}">{result['status']}</span></td>
            <td>{result['latency_seconds']}</td><td>{result['server']}</td>
            <td><div class="uptime-bar"><div class="uptime-fill" style="width:{uptime}%;background:{uptime_color}"></div></div>{uptime}%</td>
            <td>{deep_scan_cell}</td>
        </tr>
"""
    
    html += """        </tbody>
    </table>
    <script>
    function filterTable(cat) {{
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        event.target.classList.add('active');
        document.querySelectorAll('#targetsTable tbody tr').forEach(r => {{
            r.style.display = (cat === 'all' || r.dataset.category === cat) ? '' : 'none';
        }});
    }}
    </script>
</body>
</html>"""
    
    with open(OUTPUT_HTML, 'w') as f:
        f.write(html)
    
    json_feed = {{'scan_timestamp': timestamp, 'summary': summary, 'targets': all_results}}
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(json_feed, f, indent=2)
    
    print(f"[+] Dashboard generated: {{OUTPUT_HTML}}")

if __name__ == "__main__":
    generate_report()
'''

# Remove the corrupted section (lines after insert_pos)
lines = lines[:insert_pos]

# Add the new code
lines.append(html_code)

# Write back
with open('advanced_scanner.py', 'w') as f:
    f.writelines(lines)

print(f"Fixed! Inserted HTML generation at line {insert_pos}")
