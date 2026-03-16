import os

# FULL CONTENT OF ADVANCED_SCANNER.PY
content = r'''import requests, datetime, urllib3, re, time, json, hashlib, os, concurrent.futures
from functools import lru_cache
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# 1. SETUP
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from telegram_alerts import alert_target_down, alert_target_recovery, alert_new_iocs, alert_content_change, send_scan_summary
    ALERTS_ENABLED = True
except ImportError:
    ALERTS_ENABLED = False

# --- CONFIGURATION ---
OUTPUT_HTML = "/var/www/html/index.html"
OUTPUT_JSON = "/var/www/html/intelligence.json"
DEEP_SCAN_DB = "/var/www/html/deep_scan_results.json"
DEEP_SCAN_DIR = "/var/www/html/deep_scans"
UPTIME_HISTORY = "/var/www/html/uptime_history.json"
IOC_DATABASE = "/var/www/html/ioc_database.html"
IOC_JSON = "/var/www/html/ioc_database.json"
CHANGE_HISTORY = "/var/www/html/change_history.json"
PREVIOUS_STATUS = "/var/www/html/previous_status.json"
NEWS_FEED_JSON = "/var/www/html/news_feed.json"
SCAN_VIEWER = "/var/www/html/scan_viewer.html"

MAX_WORKERS = 5
DOWNTIME_ALERT_THRESHOLD_HOURS = 12

TARGETS = [
    {"name": "BBC News", "url": "https://www.bbcweb3hytmzhn5d532owbu6oqadra5z3ar726vq5kgwwn6aucdccrad.onion", "category": "news", "deep_scan": False},
    {"name": "The Guardian", "url": "https://www.guardian2zotagl6tmjucg3lrhxdk4dw3lhbqnkvvkywawy3oqfoprid.onion", "category": "news", "deep_scan": False},
    {"name": "DuckDuckGo", "url": "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion", "category": "search", "deep_scan": False},
    {"name": "Best Carding World", "url": "http://bestteermb42clir6ux7xm76d4jjodh3fpahjqgbddbmfrgp4skg2wqd.onion/", "category": "forums", "deep_scan": True},
    {"name": "Qilin Ransomware Blog", "url": "http://ijzn3sicrcy7guixkzjkib4ukbiilwc3xhnmby4mcbccnsd7j2rekvqd.onion/", "category": "ransomware", "deep_scan": True},
    {"name": "Dark Web Observatory", "url": "http://u6q3zfc2i4w3dkjkpawbpgigkfthn7xebqhnpkzd7bufbysmpdud24ad.onion/", "category": "monitoring", "deep_scan": True},
    {"name": "ProPublica", "url": "https://p53lf57qovyuvwsc6xnrppyply3vtqm7l6pcobkmyqsiofyeznfu5uqd.onion", "category": "news", "deep_scan": False},
    {"name": "Facebook", "url": "https://www.facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion", "category": "social", "deep_scan": False},
]

PROXIES = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'}
os.makedirs(DEEP_SCAN_DIR, exist_ok=True)

# --- UTILS ---
def load_json(p):
    if not os.path.exists(p): return {}
    try:
        with open(p,'r') as f: return json.load(f)
    except: return {}

def save_json(p, d):
    try:
        with open(p,'w') as f: json.dump(d, f, indent=2)
    except: pass

def load_previous_scans(): return load_json(DEEP_SCAN_DB)
def load_previous_status(): return load_json(PREVIOUS_STATUS)
def load_change_history(): return load_json(CHANGE_HISTORY)
def load_uptime_history(): return load_json(UPTIME_HISTORY)

def update_uptime(name, status):
    h = load_uptime_history()
    if name not in h: h[name] = {'checks': []}
    h[name]['checks'].append({'ts': datetime.datetime.now().isoformat(), 'up': status=='UP'})
    h[name]['checks'] = h[name]['checks'][-96:]
    checks = h[name]['checks']
    if not checks: return 0.0
    val = round((sum(1 for c in checks if c['up']) / len(checks)) * 100, 1)
    h[name]['uptime_24h'] = val
    save_json(UPTIME_HISTORY, h)
    return val

def extract_page_title(html):
    try:
        m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE|re.DOTALL)
        return m.group(1).strip()[:60] if m else "Unknown Title"
    except: return "Unknown Title"

def sanitize_filename(n): return re.sub(r'[^a-zA-Z0-9_-]', '_', n).lower()

# --- DEEP SCAN ---
def perform_deep_scan(url, resp):
    html = resp.text
    return {
        'emails': list(set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', html)))[:10],
        'bitcoin': list(set(re.findall(r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b', html)))[:5],
        'onions': [o for o in list(set(re.findall(r'[a-z2-7]{56}\.onion', html))) if o not in url][:10],
        'server': resp.headers.get('Server', 'Unknown'),
        'technologies': ['WordPress'] if 'wp-content' in html else [],
        'hash': hashlib.md5(html.encode()).hexdigest(),
        'forms': len(re.findall(r'<form', html))
    }

def detect_changes(name, curr_hash, curr_tech):
    h = load_change_history()
    ts = datetime.datetime.now().isoformat()
    if name not in h:
        h[name] = {'last_hash': curr_hash, 'last_technologies': curr_tech, 'last_changed': ts, 'changes': []}
        save_json(CHANGE_HISTORY, h)
        return {'changed': False}
    prev = h[name]
    changes = []
    if prev.get('last_hash') != curr_hash: changes.append('content')
    if changes:
        prev['changes'].append({'timestamp': ts, 'type': changes})
        prev['last_hash'] = curr_hash
        prev['last_changed'] = ts
        save_json(CHANGE_HISTORY, h)
        return {'changed': True, 'change_type': ', '.join(changes), 'last_changed': ts}
    return {'changed': False, 'last_changed': prev.get('last_changed')}

# --- SCANNER ---
def check_site(t):
    try:
        s = time.time()
        r = requests.get(t['url'], proxies=PROXIES, headers=HEADERS, timeout=60, verify=False)
        lat = round(time.time()-s, 2)
        res = {'status': 'UP' if r.status_code==200 else 'ISSUES', 'latency': f"{lat}s", 'color': 'green' if r.status_code==200 else 'orange', 'title': extract_page_title(r.text), 'server': r.headers.get('Server','-'), 'deep_data': None}
        if t.get('deep_scan'): res['deep_data'] = perform_deep_scan(t['url'], r)
        return res
    except: return {'status': 'DOWN', 'latency': '-', 'color': 'red', 'title': 'Connection Failed', 'server': '-', 'deep_data': None}

def scan_wrapper(t):
    print(f" > Scanning {t['name']}...")
    return t, check_site(t)

# --- GENERATE SCAN VIEWER (Fixed Encoding & Listing) ---
def create_scan_viewer():
    html = r"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Deep Scan | Active Workspace</title>
    <style>
        body { font-family:'Courier New',monospace; background:#0d0d0d; color:#e0e0e0; padding:40px; }
        .box { background:#111; padding:20px; border:1px solid #333; margin-top:20px; border-left:4px solid #00aaff; }
        h1 { color:#00ff00; border-bottom:1px solid #333; padding-bottom:10px; }
        .stat { display:inline-block; margin-right:30px; }
        .val { font-size:2em; font-weight:bold; color:#fff; }
        .label { color:#888; font-size:0.8em; }
        .item { padding:8px 0; border-bottom:1px solid #222; font-size:0.9em; }
        .sec-header { color:#ffa500; font-weight:bold; margin-top:15px; border-bottom:1px solid #444; }
    </style>
</head>
<body>
    <h1 id="status">🚀 Initializing Deep Scan...</h1>
    <div id="target" style="color:#888;"></div>
    <div id="results"></div>
    <script>
        const params = new URLSearchParams(window.location.search);
        const url = params.get('url');
        document.getElementById('target').innerText = 'TARGET: ' + url;
        
        fetch('/cgi-bin/on_demand_scan.py', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ url: url })
        }).then(r => r.json()).then(d => {
            if(d.error) {
                document.getElementById('status').innerText = "SCAN FAILED";
                document.getElementById('status').style.color = "#ff3333";
                document.getElementById('results').innerHTML = `<p>${d.error}</p>`;
            } else {
                document.getElementById('status').innerText = "✓ SCAN COMPLETE";
                // Handle different backend response structures
                const em = d.total_iocs ? d.total_iocs.emails : (d.emails || []);
                const btc = d.total_iocs ? d.total_iocs.btc : (d.btc || []);
                const pages = d.crawled_pages || [];
                
                let content = '';
                if(em.length > 0) content += '<div class="sec-header">EMAILS</div>' + em.map(e=>`<div class="item" style="color:#f33">@ ${e}</div>`).join('');
                if(btc.length > 0) content += '<div class="sec-header">BITCOIN</div>' + btc.map(b=>`<div class="item" style="color:#fa0">BTC: ${b}</div>`).join('');
                if(pages.length > 0) content += '<div class="sec-header">CRAWL PATH</div>' + pages.map(p=>`<div class="item">→ ${p.url}</div>`).join('');
                if(!content) content = '<div class="item">No specific IOCs found.</div>';

                document.getElementById('results').innerHTML = `
                    <div class="box">
                        <div class="stat"><div class="label">EMAILS</div><div class="val" style="color:${em.length>0?'#f33':'#0f0'}">${em.length}</div></div>
                        <div class="stat"><div class="label">BITCOIN</div><div class="val" style="color:${btc.length>0?'#fa0':'#0f0'}">${btc.length}</div></div>
                        <div class="stat"><div class="label">PAGES</div><div class="val" style="color:#0af">${pages.length+1}</div></div>
                    </div>
                    <div class="box">${content}</div>
                `;
            }
        });
    </script>
</body>
</html>
"""
    with open(SCAN_VIEWER, 'w') as f: f.write(html)

# --- MAIN GENERATOR ---
def generate_report():
    create_scan_viewer()
    ts_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    print(f"[*] Starting Scan: {ts_str}")
    
    all_res = []
    deep_data = load_previous_scans()
    change_hist = load_change_history()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(scan_wrapper, t): t for t in TARGETS}
        for f in concurrent.futures.as_completed(futures):
            t, r = f.result()
            name = t['name']
            chg = {'changed': False}
            
            if r['deep_data']:
                deep_data[name] = r['deep_data']
                chg = detect_changes(name, r['deep_data']['hash'], [])
                if chg['changed'] and ALERTS_ENABLED: alert_content_change(name, t['url'], chg['change_type'])
            
            if r['status'] == 'DOWN' and ALERTS_ENABLED:
                alert_target_down(name, t['url'], "Connection Failed")

            uptime = update_uptime(name, r['status'])
            l_change = chg.get('last_changed', change_hist.get(name, {}).get('last_changed', '-'))
            if l_change != '-': l_change = l_change[5:16].replace('T', ' ')

            all_res.append({'name': name, 'url': t['url'], 'cat': t['category'], 'res': r, 'deep': t['deep_scan'], 'up': uptime, 'l_chg': l_change})

    save_json(DEEP_SCAN_DB, deep_data)
    
    # Sub-pages
    for n, d in deep_data.items():
        with open(f"{DEEP_SCAN_DIR}/{sanitize_filename(n)}.html", 'w') as f:
            f.write(f"<html><body style='background:#111;color:#ccc;font-family:monospace;padding:20px'><h1>{n}</h1><p>Generated: {ts_str}</p><div style='background:#000;padding:20px;border:1px solid #333'><h3>Emails</h3>{len(d['emails'])} found<br><h3>Bitcoin</h3>{len(d['bitcoin'])} found</div></body></html>")

    # Metrics
    tot = len(TARGETS)
    up = sum(1 for x in all_res if x['res']['status']=='UP')
    deep_act = sum(1 for x in all_res if x['deep'])
    iocs = sum(len(d.get('emails',[]))+len(d.get('bitcoin',[])) for d in deep_data.values())
    em_cnt = sum(len(d.get('emails',[])) for d in deep_data.values())
    btc_cnt = sum(len(d.get('bitcoin',[])) for d in deep_data.values())
    
    # Categories for Filter Bar
    categories = sorted(list(set(t['category'] for t in TARGETS)))
    cat_buttons = f'<button class="cat-btn active" onclick="filterTable(\'all\')">ALL TARGETS <span class="badge">{tot}</span></button> '
    for c in categories:
        count = sum(1 for t in TARGETS if t['category'] == c)
        cat_buttons += f'<button class="cat-btn" onclick="filterTable(\'{c}\')">{c.upper()} <span class="badge">{count}</span></button> '

    if ALERTS_ENABLED: send_scan_summary({'total_targets': tot, 'up_targets': up, 'deep_scan_count': deep_act})

    # --- SOPHISTICATED DASHBOARD (RAW STRING) ---
    html = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Dark Web Observatory - Threat Intelligence Platform</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Courier New', monospace; background: #050505; color: #e0e0e0; padding: 20px; font-size: 14px; }
        a { color: #00aaff; text-decoration: none; } a:hover { text-decoration: underline; }
        h1 { color: #00ff00; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 5px; text-transform: uppercase; }
        .sub-header { color: #888; font-size: 0.9em; margin-bottom: 30px; }
        
        /* METRICS */
        .metrics-container { border: 2px solid #00ff00; padding: 15px; margin-bottom: 30px; background: #0a0a0a; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom:15px; }
        .metric-box { background: #111; padding: 10px; border-left: 3px solid #333; }
        .metric-label { font-size: 0.75em; color: #888; text-transform: uppercase; }
        .metric-value { font-size: 1.4em; font-weight: bold; color: #fff; margin-top: 5px; }
        .val-green { color: #00ff00; } .val-red { color: #ff3333; }
        
        /* FILTER BAR */
        .filter-bar { border-top:1px solid #333; padding-top:10px; }
        .cat-btn { background: #111; color: #888; border: 1px solid #333; padding: 5px 10px; margin-right: 5px; cursor: pointer; text-transform: uppercase; font-size: 0.8em; }
        .cat-btn.active { background: #004400; color: #00ff00; border-color: #00ff00; }
        .badge { background: #222; padding: 1px 4px; font-size: 0.8em; margin-left: 5px; }
        
        /* TABLE */
        table { width: 100%; border-collapse: collapse; margin-bottom: 40px; font-size: 0.9em; }
        th { text-align: left; padding: 10px; background: #111; color: #888; border-bottom: 2px solid #333; text-transform: uppercase; }
        td { padding: 10px; border-bottom: 1px solid #222; }
        .status-UP { background: #002200; color: #00ff00; padding: 2px 6px; font-weight: bold; text-align: center; }
        .status-DOWN { background: #220000; color: #ff3333; padding: 2px 6px; font-weight: bold; text-align: center; }
        .uptime-bar-bg { width: 100px; height: 6px; background: #222; display: inline-block; margin-right: 5px; }
        .uptime-bar-fill { height: 100%; background: linear-gradient(90deg, #ff3333, #00ff00); }
        .view-report { color: #00ff00; border: 1px solid #00ff00; padding: 2px 8px; font-size: 0.8em; }
        
        /* TOOLS */
        .tool-section { margin-bottom: 30px; background: #0f0f0f; border: 1px solid #222; padding: 15px; border-left: 4px solid #00aaff; }
        .input-group { display: flex; gap: 10px; margin-top: 10px; }
        input { background: #000; border: 1px solid #333; color: #fff; padding: 8px; flex: 1; font-family: inherit; }
        button { background: #003366; color: #00aaff; border: 1px solid #00aaff; padding: 8px 15px; cursor: pointer; font-weight: bold; }
        
        /* NEWS */
        .news-section { border-left: 4px solid #ffa500; }
        .news-header { display: flex; justify-content: space-between; margin-bottom: 15px; }
        .news-filters button { background: #111; color: #666; border: 1px solid #333; margin-left: 5px; }
        .news-filters button.active { background: #221100; color: #ffa500; border-color: #ffa500; }
        .news-item { border-bottom: 1px solid #222; padding: 8px 0; }
        .refresh-btn { background: #1a1000 !important; color: #ffa500 !important; border: 1px solid #ffa500 !important; margin-right:15px; }
        
        /* IP CARD */
        .ip-card { margin-top: 10px; padding: 10px; background: #000; border-left: 3px solid #ff3333; }
        .ip-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.9em; }
        .ip-label { color: #666; font-size: 0.8em; text-transform: uppercase; }
    </style>
</head>
<body>
    <h1>Dark Web Observatory - Threat Intelligence Platform</h1>
    <div class="sub-header">Last Scan: {{TIMESTAMP}} | <a href="intelligence.json">Download JSON</a> | <a href="deep_scan_results.html">Deep Scan DB</a> | <a href="alert_statistics.html">Alert Stats</a></div>

    <div class="metrics-container">
        <div style="color:#0f0; font-weight:bold; margin-bottom:15px;">📊 INTELLIGENCE SUMMARY (LAST SCAN)</div>
        <div class="metrics-grid">
            <div class="metric-box"><div class="metric-label">Targets</div><div class="metric-value">{{TOT}}</div></div>
            <div class="metric-box"><div class="metric-label">Up</div><div class="metric-value val-green">{{UP}}</div></div>
            <div class="metric-box"><div class="metric-label">Deep Scans</div><div class="metric-value">{{DEEP}}</div></div>
            <div class="metric-box"><div class="metric-label">IOCs</div><div class="metric-value val-red">{{IOCS}}</div></div>
            <div class="metric-box"><div class="metric-label">Emails</div><div class="metric-value">{{EM}}</div></div>
            <div class="metric-box"><div class="metric-label">BTC</div><div class="metric-value">{{BTC}}</div></div>
        </div>
        <div class="filter-bar">
            <span style="color:#888; font-size:0.8em; margin-right:10px;">FILTER BY CATEGORY:</span>
            {{CAT_BUTTONS}}
        </div>
    </div>

    <table id="mainTable">
        <thead><tr><th>Target</th><th>Address</th><th>Status</th><th>Uptime (24h)</th><th>Latency</th><th>Server</th><th>Changed</th><th>Title</th><th>Scan</th></tr></thead>
        <tbody>{{ROWS}}</tbody>
    </table>

    <div class="tool-section">
        <div style="color:#00aaff; font-weight:bold; text-transform:uppercase;">🔍 On-Demand Deep Scan</div>
        <div style="font-size:0.8em; color:#666; margin-bottom:5px;">Enter .onion URL. Opens detailed report in new tab.</div>
        <div class="input-group">
            <input type="text" id="ondemandUrl" placeholder="http://example.onion">
            <button onclick="startScan()">Scan Now →</button>
        </div>
    </div>

    <div class="tool-section" style="border-left-color: #ff3333;">
        <div style="color:#ff3333; font-weight:bold; text-transform:uppercase;">🛑 IP Reputation Check</div>
        <div class="input-group">
            <input type="text" id="ipInput" placeholder="1.2.3.4">
            <button onclick="checkIP()" style="border-color:#ff3333; color:#ff3333;">Check IP →</button>
        </div>
        <div id="ipResult"></div>
    </div>

    <div class="tool-section news-section" style="border-left-color: #ffa500;">
        <div class="news-header">
            <div style="color:#ffa500; font-weight:bold; text-transform:uppercase;">📰 Latest Cybersecurity News</div>
            <div>
                <button class="refresh-btn" onclick="refreshNews()">🔄 Refresh Feed</button>
                <div class="news-filters" id="newsFilters" style="display:inline-block;"></div>
            </div>
        </div>
        <div id="news-feed-container">Loading...</div>
    </div>

    <script>
    let allNews = [];
    fetch('news_feed.json').then(r=>r.json()).then(d=>{
        allNews=d.articles||[];
        const c=document.getElementById('newsFilters');
        const cats=[...new Set(allNews.map(a=>a.category))].filter(Boolean);
        c.innerHTML='<button class="active" onclick="filt(\'all\')">ALL</button>';
        cats.forEach(x=>c.innerHTML+=`<button onclick="filt('${x}')">${x.toUpperCase()}</button>`);
        render(allNews.slice(0,20));
    });

    function filt(cat) {
        document.querySelectorAll('.news-filters button').forEach(b=>{
            b.classList.toggle('active', b.innerText===cat.toUpperCase() || (cat==='all' && b.innerText==='ALL'));
        });
        render(cat==='all' ? allNews : allNews.filter(a=>a.category===cat));
    }

    function render(list) {
        const d=document.getElementById('news-feed-container');
        if(!list.length) return d.innerHTML='No news.';
        d.innerHTML = list.map(a=>`
            <div class="news-item">
                <div style="font-size:0.75em; color:#666; margin-bottom:3px;">
                    <span style="color:#0f0;">[${a.category.toUpperCase()}]</span> 
                    <span style="color:#0af; margin-left:10px;">${a.source}</span>
                    <span style="float:right;">${a.published || ''}</span>
                </div>
                <a href="${a.link}" target="_blank" style="color:#e0e0e0; font-weight:bold;">${a.title}</a>
            </div>`).join('');
    }

    function refreshNews() {
        const btn = document.querySelector('.refresh-btn');
        btn.innerHTML = '⏳...';
        fetch('/cgi-bin/refresh_news.py', {method:'POST'}).then(()=>{ location.reload() });
    }

    function filterTable(cat) {
        document.querySelectorAll('.cat-btn').forEach(b => {
            const isActive = b.textContent.includes(cat.toUpperCase()) || (cat === 'all' && b.textContent.includes('ALL'));
            b.classList.toggle('active', isActive);
        });
        document.querySelectorAll('#mainTable tbody tr').forEach(r => {
            if(cat === 'all' || r.dataset.cat === cat) r.style.display = '';
            else r.style.display = 'none';
        });
    }

    function startScan() {
        const u = document.getElementById('ondemandUrl').value.trim();
        if(!u) return alert('Enter URL');
        window.open('scan_viewer.html?url='+encodeURIComponent(u), '_blank');
    }

    function checkIP() {
        const i = document.getElementById('ipInput').value.trim();
        const d = document.getElementById('ipResult');
        if(!i) return;
        d.innerHTML = 'Analyzing...';
        fetch('/cgi-bin/check_ip.py', {
            method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ip:i})
        }).then(r=>r.json()).then(res=>{
            if(res.error) { d.innerHTML=`<span style="color:red">${res.error}</span>`; return; }
            const x = res.data;
            d.innerHTML = `
                <div class="ip-card">
                    <h3 style="margin-top:0; color:${x.abuseConfidenceScore>50?'#f33':'#0f0'}">Risk: ${x.abuseConfidenceScore}%</h3>
                    <div class="ip-grid">
                        <div><span class="ip-label">ISP:</span> ${x.isp}</div>
                        <div><span class="ip-label">Country:</span> ${x.countryCode}</div>
                        <div><span class="ip-label">Domain:</span> ${x.domain||'N/A'}</div>
                        <div><span class="ip-label">Usage:</span> ${x.usageType||'N/A'}</div>
                        <div><span class="ip-label">Hostnames:</span> ${(x.hostnames||[]).join(', ')||'N/A'}</div>
                        <div><span class="ip-label">Reports:</span> ${x.totalReports}</div>
                        <div><span class="ip-label">Last Reported:</span> ${x.lastReportedAt||'Never'}</div>
                    </div>
                </div>`;
        });
    }
    </script>
</body>
</html>
"""

    rows = ""
    for r in all_res:
        res = r['result']
        deep = f'<a href="deep_scans/{sanitize_filename(r["name"])}.html" class="view-report">view report →</a>' if r['deep_scan_enabled'] else '<span style="color:#444">Not enabled</span>'
        bar = f'<div class="uptime-bar-bg"><div class="uptime-bar-fill" style="width:{r["up"]}%"></div></div> {r["up"]}%'
        rows += f"""<tr data-cat="{r['category']}">
            <td><span style="color:#888; font-size:0.8em">[{r['category'].upper()}]</span><br>{r['name']}</td>
            <td style="color:#666; font-size:0.85em">{r['url']}</td>
            <td><div class="status-{res['status']}">{res['status']}</div></td>
            <td>{bar}</td>
            <td>{res['latency']}</td>
            <td style="color:#888">{res['server']}</td>
            <td style="color:#ffa500">{r['l_chg']}</td>
            <td style="font-style:italic; color:#aaa">{res['title']}</td>
            <td>{deep}</td>
        </tr>"""

    final = html.replace('{{TIMESTAMP}}', ts_str).replace('{{TOT}}', str(tot)).replace('{{UP}}', str(up)).replace('{{DEEP}}', str(deep_act)).replace('{{IOCS}}', str(iocs)).replace('{{EM}}', str(em_cnt)).replace('{{BTC}}', str(btc_cnt)).replace('{{ROWS}}', rows).replace('{{CAT_BUTTONS}}', cat_buttons)
    
    with open(OUTPUT_HTML, "w") as f: f.write(final)
    print(f"[+] Dashboard Updated: {OUTPUT_HTML}")

    # --- EXTERNAL TRIGGERS ---
    print("[*] Triggering Aggregators...")
    try:
        from news_feed_aggregator import aggregate_news_feed
        aggregate_news_feed()
    except Exception as e: print(f"[!] News feed error: {e}")

    try:
        from generate_alert_stats import generate_alert_statistics
        generate_alert_statistics()
    except Exception as e: print(f"[!] Alert stats error: {e}")

    try:
        from generate_historical_trends import generate_historical_trends
        generate_historical_trends()
    except Exception as e: print(f"[!] Trend stats error: {e}")

if __name__ == "__main__": generate_report()
'''

with open("advanced_scanner.py", "w") as f:
    f.write(content)

print("SUCCESS: Run 'python3 advanced_scanner.py'")
