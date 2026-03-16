import requests
import json
import csv
from datetime import datetime, timedelta
import time

# Output files
FEED_DATABASE = "/var/www/html/threat_feeds.json"
FEED_DASHBOARD = "/var/www/html/threat_feeds.html"

# Feed URLs (all free, no API keys required)
FEEDS = {
    'urlhaus': {
        'name': 'URLhaus (Abuse.ch)',
        'url': 'https://urlhaus.abuse.ch/downloads/csv_recent/',
        'type': 'csv',
        'description': 'Malware distribution URLs',
        'category': 'malware_urls'
    },
    'threatfox': {
        'name': 'ThreatFox IOCs (Abuse.ch)',
        'url': 'https://threatfox.abuse.ch/export/csv/recent/',
        'type': 'csv',
        'description': 'Recent IOCs from various sources',
        'category': 'mixed_iocs'
    },
    'feodotracker': {
        'name': 'Feodo Tracker (Abuse.ch)',
        'url': 'https://feodotracker.abuse.ch/downloads/ipblocklist.csv',
        'type': 'csv',
        'description': 'Botnet C2 IP addresses',
        'category': 'c2_ips'
    },
    'sslbl': {
        'name': 'SSL Blacklist (Abuse.ch)',
        'url': 'https://sslbl.abuse.ch/blacklist/sslblacklist.csv',
        'type': 'csv',
        'description': 'Malicious SSL certificates',
        'category': 'ssl_certs'
    }
}

def fetch_urlhaus_feed():
    """Fetch URLhaus malware distribution URLs"""
    try:
        print("  [*] Fetching URLhaus feed...")
        resp = requests.get(FEEDS['urlhaus']['url'], timeout=30)
        resp.raise_for_status()
        
        lines = resp.text.strip().split('\n')
        
        # Skip comments
        data_lines = [line for line in lines if not line.startswith('#')]
        
        threats = []
        for line in data_lines[1:100]:  # Skip header, limit to 100
            try:
                parts = line.split('","')
                if len(parts) >= 7:
                    # Clean quotes
                    parts = [p.strip('"') for p in parts]
                    
                    threats.append({
                        'id': parts[0],
                        'date_added': parts[1],
                        'url': parts[2],
                        'url_status': parts[3],
                        'threat_type': parts[4],
                        'tags': parts[5] if len(parts) > 5 else '',
                        'source': 'URLhaus'
                    })
            except Exception as e:
                continue
        
        print(f"    [+] Retrieved {len(threats)} malware URLs")
        return threats
    except Exception as e:
        print(f"    [!] Failed to fetch URLhaus: {e}")
        return []

def fetch_threatfox_feed():
    """Fetch ThreatFox IOCs"""
    try:
        print("  [*] Fetching ThreatFox feed...")
        resp = requests.get(FEEDS['threatfox']['url'], timeout=30)
        resp.raise_for_status()
        
        lines = resp.text.strip().split('\n')
        data_lines = [line for line in lines if not line.startswith('#')]
        
        threats = []
        for line in data_lines[1:100]:  # Skip header, limit to 100
            try:
                parts = line.split('","')
                if len(parts) >= 6:
                    parts = [p.strip('"') for p in parts]
                    
                    threats.append({
                        'date_added': parts[0],
                        'ioc': parts[1],
                        'ioc_type': parts[2],
                        'threat_type': parts[3],
                        'malware': parts[4],
                        'confidence': parts[5] if len(parts) > 5 else 'N/A',
                        'source': 'ThreatFox'
                    })
            except Exception as e:
                continue
        
        print(f"    [+] Retrieved {len(threats)} IOCs")
        return threats
    except Exception as e:
        print(f"    [!] Failed to fetch ThreatFox: {e}")
        return []

def fetch_feodotracker_feed():
    """Fetch Feodo Tracker botnet C2 IPs"""
    try:
        print("  [*] Fetching Feodo Tracker feed...")
        resp = requests.get(FEEDS['feodotracker']['url'], timeout=30)
        resp.raise_for_status()
        
        lines = resp.text.strip().split('\n')
        data_lines = [line for line in lines if not line.startswith('#')]
        
        threats = []
        for line in data_lines[1:100]:  # Skip header, limit to 100
            try:
                parts = line.split(',')
                if len(parts) >= 5:
                    threats.append({
                        'date_added': parts[0],
                        'ip_address': parts[1],
                        'port': parts[2],
                        'status': parts[3],
                        'malware': parts[4] if len(parts) > 4 else 'Unknown',
                        'source': 'Feodo Tracker'
                    })
            except Exception as e:
                continue
        
        print(f"    [+] Retrieved {len(threats)} C2 IPs")
        return threats
    except Exception as e:
        print(f"    [!] Failed to fetch Feodo Tracker: {e}")
        return []

def fetch_sslbl_feed():
    """Fetch SSL Blacklist"""
    try:
        print("  [*] Fetching SSL Blacklist feed...")
        resp = requests.get(FEEDS['sslbl']['url'], timeout=30)
        resp.raise_for_status()
        
        lines = resp.text.strip().split('\n')
        data_lines = [line for line in lines if not line.startswith('#')]
        
        threats = []
        for line in data_lines[1:100]:  # Skip header, limit to 100
            try:
                parts = line.split(',')
                if len(parts) >= 3:
                    threats.append({
                        'date_added': parts[0],
                        'sha1_hash': parts[1],
                        'reason': parts[2] if len(parts) > 2 else 'Malicious SSL',
                        'source': 'SSL Blacklist'
                    })
            except Exception as e:
                continue
        
        print(f"    [+] Retrieved {len(threats)} SSL threats")
        return threats
    except Exception as e:
        print(f"    [!] Failed to fetch SSL Blacklist: {e}")
        return []

def aggregate_all_feeds():
    """Fetch all threat feeds"""
    
    print("[*] Starting threat feed aggregation...")
    
    all_feeds = {
        'urlhaus': fetch_urlhaus_feed(),
        'threatfox': fetch_threatfox_feed(),
        'feodotracker': fetch_feodotracker_feed(),
        'sslbl': fetch_sslbl_feed()
    }
    
    # Calculate statistics
    total_threats = sum(len(threats) for threats in all_feeds.values())
    
    feed_data = {
        'last_updated': datetime.now().isoformat(),
        'total_threats': total_threats,
        'feeds': all_feeds,
        'feed_info': FEEDS
    }
    
    # Save JSON
    try:
        with open(FEED_DATABASE, 'w') as f:
            json.dump(feed_data, f, indent=2)
        print(f"[+] Saved threat feed database: {total_threats} total threats")
    except Exception as e:
        print(f"[!] Failed to save feed database: {e}")
    
    return feed_data

def generate_feed_dashboard(feed_data):
    """Generate threat feed dashboard HTML"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_threats = feed_data['total_threats']
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Public Threat Intelligence Feeds - Dark Web Observatory</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="3600">
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0d0d0d; color: #e0e0e0; padding: 20px; }}
            h1 {{ color: #00ff00; text-transform: uppercase; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            h2 {{ color: #ffa500; margin-top: 30px; border-bottom: 1px solid #444; padding-bottom: 8px; }}
            .back-link {{ color: #00aaff; text-decoration: none; }}
            .back-link:hover {{ text-decoration: underline; }}
            .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
            .summary-box {{ background: #1a1a1a; padding: 20px; border-left: 4px solid #ff3333; }}
            .summary-label {{ color: #888; font-size: 0.9em; text-transform: uppercase; }}
            .summary-value {{ color: #ff3333; font-size: 2em; font-weight: bold; margin-top: 5px; }}
            .feed-section {{ background: #1a1a1a; padding: 20px; margin: 20px 0; border-left: 4px solid #00ff00; }}
            .feed-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            .feed-title {{ color: #00ff00; font-size: 1.3em; font-weight: bold; }}
            .feed-count {{ color: #ffa500; font-size: 1.1em; }}
            .feed-description {{ color: #888; font-size: 0.9em; margin-bottom: 15px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; font-size: 0.85em; }}
            th, td {{ border: 1px solid #333; padding: 8px; text-align: left; }}
            th {{ background: #0a0a0a; color: #fff; text-transform: uppercase; position: sticky; top: 0; }}
            tr:nth-child(even) {{ background: #111; }}
            .threat-url {{ color: #ff3333; word-break: break-all; }}
            .threat-ioc {{ color: #ffa500; font-family: monospace; }}
            .threat-ip {{ color: #00aaff; }}
            .threat-hash {{ color: #ffa500; font-size: 0.8em; font-family: monospace; word-break: break-all; }}
            .status-online {{ color: #00ff00; }}
            .status-offline {{ color: #888; }}
            .confidence-high {{ color: #ff3333; font-weight: bold; }}
            .confidence-medium {{ color: #ffa500; }}
            .confidence-low {{ color: #ffff00; }}
            .search-box {{ background: #1a1a1a; padding: 20px; margin: 20px 0; border: 1px solid #333; }}
            .search-input {{ width: 100%; background: #0a0a0a; border: 1px solid #333; color: #e0e0e0; padding: 10px; font-family: 'Courier New', monospace; font-size: 1em; }}
            .search-input:focus {{ border-color: #00ff00; outline: none; }}
            .download-btn {{ display: inline-block; background: #003300; color: #00ff00; padding: 10px 20px; text-decoration: none; border: 1px solid #00ff00; margin: 10px 5px; cursor: pointer; }}
            .download-btn:hover {{ background: #004400; }}
            .info-banner {{ background: #1a1a1a; border-left: 4px solid #00aaff; padding: 15px; margin: 20px 0; }}
            .info-banner strong {{ color: #00aaff; }}
        </style>
    </head>
    <body>
        <h1>🌐 Public Threat Intelligence Feeds</h1>
        <p><a href="index.html" class="back-link">&larr; Back to Dashboard</a> | <a href="ioc_database.html" class="back-link">IOC Database</a> | Last Updated: {timestamp}</p>
        
        <div class="info-banner">
            <strong>ℹ️ About These Feeds:</strong> Real-time threat intelligence from public sources (Abuse.ch). 
            Feeds update hourly. All data sourced from reputable security researchers and automated malware analysis systems.
        </div>
        
        <div class="summary-grid">
            <div class="summary-box">
                <div class="summary-label">Total Threats</div>
                <div class="summary-value">{total_threats}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">Malware URLs</div>
                <div class="summary-value">{len(feed_data['feeds'].get('urlhaus', []))}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">IOC Indicators</div>
                <div class="summary-value">{len(feed_data['feeds'].get('threatfox', []))}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">C2 IP Addresses</div>
                <div class="summary-value">{len(feed_data['feeds'].get('feodotracker', []))}</div>
            </div>
            <div class="summary-box">
                <div class="summary-label">Malicious SSL Certs</div>
                <div class="summary-value">{len(feed_data['feeds'].get('sslbl', []))}</div>
            </div>
        </div>
        
        <div>
            <a href="threat_feeds.json" class="download-btn" download>⬇ Download JSON Feed</a>
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search all feeds (URL, IP, hash, malware family, IOC)..." onkeyup="searchFeeds()">
        </div>
    """
    
    # URLhaus Feed
    urlhaus_data = feed_data['feeds'].get('urlhaus', [])
    if urlhaus_data:
        html += f"""
        <div class="feed-section">
            <div class="feed-header">
                <div class="feed-title">🦠 URLhaus - Malware Distribution URLs</div>
                <div class="feed-count">{len(urlhaus_data)} URLs</div>
            </div>
            <div class="feed-description">Recent URLs distributing malware. Source: Abuse.ch URLhaus</div>
            <table id="urlhausTable">
                <thead>
                    <tr>
                        <th style="width: 15%">Date Added</th>
                        <th style="width: 40%">Malware URL</th>
                        <th style="width: 10%">Status</th>
                        <th style="width: 20%">Threat Type</th>
                        <th style="width: 15%">Tags</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in urlhaus_data[:50]:  # Show first 50
            status_class = 'status-online' if item.get('url_status') == 'online' else 'status-offline'
            html += f"""
                    <tr data-search="{item.get('url', '').lower()} {item.get('threat_type', '').lower()} {item.get('tags', '').lower()}">
                        <td>{item.get('date_added', 'N/A')}</td>
                        <td class="threat-url">{item.get('url', 'N/A')}</td>
                        <td class="{status_class}">{item.get('url_status', 'N/A').upper()}</td>
                        <td>{item.get('threat_type', 'N/A')}</td>
                        <td>{item.get('tags', 'N/A')}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    # ThreatFox Feed
    threatfox_data = feed_data['feeds'].get('threatfox', [])
    if threatfox_data:
        html += f"""
        <div class="feed-section">
            <div class="feed-header">
                <div class="feed-title">🎯 ThreatFox - Multi-Source IOCs</div>
                <div class="feed-count">{len(threatfox_data)} IOCs</div>
            </div>
            <div class="feed-description">Indicators of Compromise from various threat intelligence sources</div>
            <table id="threatfoxTable">
                <thead>
                    <tr>
                        <th style="width: 12%">Date</th>
                        <th style="width: 30%">IOC</th>
                        <th style="width: 12%">Type</th>
                        <th style="width: 18%">Threat Type</th>
                        <th style="width: 18%">Malware</th>
                        <th style="width: 10%">Confidence</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in threatfox_data[:50]:
            confidence = item.get('confidence', '0')
            conf_class = 'confidence-high' if int(confidence) >= 75 else 'confidence-medium' if int(confidence) >= 50 else 'confidence-low'
            
            html += f"""
                    <tr data-search="{item.get('ioc', '').lower()} {item.get('malware', '').lower()} {item.get('threat_type', '').lower()}">
                        <td>{item.get('date_added', 'N/A')}</td>
                        <td class="threat-ioc">{item.get('ioc', 'N/A')}</td>
                        <td>{item.get('ioc_type', 'N/A')}</td>
                        <td>{item.get('threat_type', 'N/A')}</td>
                        <td>{item.get('malware', 'N/A')}</td>
                        <td class="{conf_class}">{confidence}%</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    # Feodo Tracker Feed
    feodo_data = feed_data['feeds'].get('feodotracker', [])
    if feodo_data:
        html += f"""
        <div class="feed-section">
            <div class="feed-header">
                <div class="feed-title">🤖 Feodo Tracker - Botnet C2 Servers</div>
                <div class="feed-count">{len(feodo_data)} IPs</div>
            </div>
            <div class="feed-description">Active Command & Control servers for banking trojans and botnets</div>
            <table id="feodoTable">
                <thead>
                    <tr>
                        <th style="width: 15%">Date</th>
                        <th style="width: 25%">IP Address</th>
                        <th style="width: 10%">Port</th>
                        <th style="width: 15%">Status</th>
                        <th style="width: 35%">Malware Family</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in feodo_data[:50]:
            status_class = 'status-online' if item.get('status') == 'online' else 'status-offline'
            html += f"""
                    <tr data-search="{item.get('ip_address', '').lower()} {item.get('malware', '').lower()}">
                        <td>{item.get('date_added', 'N/A')}</td>
                        <td class="threat-ip">{item.get('ip_address', 'N/A')}</td>
                        <td>{item.get('port', 'N/A')}</td>
                        <td class="{status_class}">{item.get('status', 'N/A').upper()}</td>
                        <td>{item.get('malware', 'N/A')}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    # SSL Blacklist Feed
    sslbl_data = feed_data['feeds'].get('sslbl', [])
    if sslbl_data:
        html += f"""
        <div class="feed-section">
            <div class="feed-header">
                <div class="feed-title">🔐 SSL Blacklist - Malicious Certificates</div>
                <div class="feed-count">{len(sslbl_data)} Certificates</div>
            </div>
            <div class="feed-description">SSL certificates associated with malware C2 communications</div>
            <table id="sslblTable">
                <thead>
                    <tr>
                        <th style="width: 15%">Date Detected</th>
                        <th style="width: 50%">SHA1 Certificate Hash</th>
                        <th style="width: 35%">Reason</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in sslbl_data[:50]:
            html += f"""
                    <tr data-search="{item.get('sha1_hash', '').lower()} {item.get('reason', '').lower()}">
                        <td>{item.get('date_added', 'N/A')}</td>
                        <td class="threat-hash">{item.get('sha1_hash', 'N/A')}</td>
                        <td>{item.get('reason', 'N/A')}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    html += """
        <p style="margin-top:50px; font-size: 0.8em; color: #555;">
            <i>Automated Threat Intelligence Sentinel | Public Feed Aggregator | Data Sources: Abuse.ch</i>
        </p>
        
        <script>
        function searchFeeds() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const allRows = document.querySelectorAll('table tbody tr');
            
            allRows.forEach(row => {
                const searchData = row.dataset.search || '';
                const rowText = row.textContent.toLowerCase();
                
                if (searchData.includes(searchTerm) || rowText.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
        </script>
    </body>
    </html>
    """
    
    # Save HTML
    try:
        with open(FEED_DASHBOARD, 'w') as f:
            f.write(html)
        print(f"[+] Threat feed dashboard generated: {FEED_DASHBOARD}")
    except Exception as e:
        print(f"[!] Failed to generate dashboard: {e}")

if __name__ == "__main__":
    feed_data = aggregate_all_feeds()
    generate_feed_dashboard(feed_data)
    print("\n[✓] Threat feed aggregation complete!")

