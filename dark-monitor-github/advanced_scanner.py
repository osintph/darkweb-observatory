# -*- coding: utf-8 -*-
"""
advanced_scanner.py  -- Dark Web Observatory
=============================================
All original features preserved:
  - Deep scan / IOC extraction
  - Content change detection
  - Uptime history (96-check rolling window)
  - Concurrent scanning
  - On-demand scan viewer
  - News feed integration
  - Timeout: 60s -> 15s  (onion sites respond fast or not at all)
  - Retries: removed      (a DOWN onion is DOWN, retries waste minutes)
  - Workers: 5 -> 25      (I/O-bound, safe to parallelise heavily)
  - Expanded TARGETS list (ransomware, leak sites, markets, CTI trackers)
  - remote_targets.py integration (alecmuffett + fastfire/deepdarkCTI)
  - Card-based sidebar dashboard replaces flat table
"""

import concurrent.futures
import datetime
import hashlib
import json
import os
import re
import time
import urllib3

import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_HTML    = "/var/www/html/index.html"
OUTPUT_JSON    = "/var/www/html/intelligence.json"
DEEP_SCAN_DB   = "/var/www/html/deep_scan_results.json"
DEEP_SCAN_DIR  = "/var/www/html/deep_scans"
UPTIME_HISTORY = "/var/www/html/uptime_history.json"
CHANGE_HISTORY = "/var/www/html/change_history.json"
PREVIOUS_STATUS= "/var/www/html/previous_status.json"
NEWS_FEED_JSON = "/var/www/html/news_feed.json"
SCAN_VIEWER    = "/var/www/html/scan_viewer.html"

MAX_WORKERS    = 25   # I/O-bound -- safe to go high
REQUEST_TIMEOUT= 10   # seconds -- if it hasn't responded in 10s it's down
# No retries -- a DOWN onion is DOWN. Retries turn 15s into 45s per dead host.

PROXIES = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'}

os.makedirs(DEEP_SCAN_DIR, exist_ok=True)

# ── Targets ───────────────────────────────────────────────────────────────────
# Categories must match manager.py dropdown:
#   news | search | social | government | forums | marketplace |
#   ransomware | leak_site | monitoring | intel | email | privacy | index

TARGETS = [
    # ── News / Journalism ─────────────────────────────────────────────────────
    {"name": "BBC News",           "url": "https://www.bbcweb3hytmzhn5d532owbu6oqadra5z3ar726vq5kgwwn6aucdccrad.onion",   "category": "news",        "deep_scan": False, "risk": "low"},
    {"name": "New York Times",     "url": "https://nytimesn7cgmftshazwhfgzm37qxb44r64ytbb2dj3x62d2lljsciiyd.onion",      "category": "news",        "deep_scan": False, "risk": "low"},
    {"name": "The Guardian",       "url": "https://www.guardian2zotagl6tmjucg3lrhxdk4dw3lhbqnkvvkywawy3oqfoprid.onion",  "category": "news",        "deep_scan": False, "risk": "low"},
    {"name": "ProPublica",         "url": "https://p53lf57qovyuvwsc6xnrppyply3vtqm7l6pcobkmyqsiofyeznfu5uqd.onion",      "category": "news",        "deep_scan": False, "risk": "low"},
    {"name": "DarkNetLive",        "url": "http://darkzzx4avcsuofgfez5zq75cqc4mprjvfqywo45dfcaxrwqg6qrlfid.onion",       "category": "news",        "deep_scan": False, "risk": "low"},
    # ── Search ────────────────────────────────────────────────────────────────
    {"name": "DuckDuckGo",         "url": "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion",       "category": "search",      "deep_scan": False, "risk": "low"},
    {"name": "Ahmia",              "url": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion",        "category": "search",      "deep_scan": False, "risk": "low"},
    # ── Social ────────────────────────────────────────────────────────────────
    {"name": "Facebook",           "url": "https://www.facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion",  "category": "social",      "deep_scan": False, "risk": "low"},
    {"name": "Reddit",             "url": "https://www.reddittorjg6rue252oqsxryoxengawnmo46qy4kyii5wtqnwfj4ooad.onion",  "category": "social",      "deep_scan": False, "risk": "low"},
    # ── Government ────────────────────────────────────────────────────────────
    {"name": "CIA",                "url": "https://ciadotgov4sjwlzihbbgxnqg3xiyrg7so2r2o3lt5wz5ypk4sxyjstad.onion",      "category": "government",  "deep_scan": False, "risk": "low"},
    # ── Privacy / Infrastructure ──────────────────────────────────────────────
    {"name": "Tor Project",        "url": "http://2gzyxa5ihm7nsggfxnu52rck2vv4rvmdlkiu3zzui5du4xyclen53wid.onion/index.html", "category": "privacy", "deep_scan": False, "risk": "low"},
    {"name": "Riseup",             "url": "http://vww6ybal4bd7szmgncyruucpgfkqahzddi37ktceo3ah7ngmcopnpyyd.onion",        "category": "privacy",     "deep_scan": False, "risk": "low"},
    {"name": "OnionShare",         "url": "http://lldan5gahapx5k7iafb3s4ikijc4ni7gx5iywdflkba5y2ezyg6sjgyd.onion",        "category": "privacy",     "deep_scan": False, "risk": "low"},
    # ── Email ─────────────────────────────────────────────────────────────────
    {"name": "Mail2Tor",           "url": "http://mail2torjgmxgexntbrmhvgluavhj7ouul5yar6ylbvjkxwqf6ixkwyd.onion",       "category": "email",       "deep_scan": False, "risk": "low"},
    {"name": "Elude Mail",         "url": "http://eludemailxhnqzfmxehy3bk5guyhlxbunfyhkcksv4gvx6d3wcf6smad.onion",       "category": "email",       "deep_scan": False, "risk": "low"},
    # ── Index ─────────────────────────────────────────────────────────────────
    {"name": "Hidden Wiki",        "url": "http://bfbzii56g2brpsg3a6hng45noo4lnby3ux5sgvpd53dyzpu3cre35ryd.onion",        "category": "index",       "deep_scan": False, "risk": "medium"},
    {"name": "OnionLinks",         "url": "http://s4k4ceiapwwgcm3mkb6e4diqecpo7kvdnfr5gg7sph7jjppqkvwwqtyd.onion",        "category": "index",       "deep_scan": False, "risk": "medium"},
    # ── Forums ────────────────────────────────────────────────────────────────
    {"name": "Dread",              "url": "http://dreadytofatroptsdj6io7l3xptbet6onoyno2yv7jicoxknyazubrad.onion",         "category": "forums",      "deep_scan": True,  "risk": "medium"},
    {"name": "DefCon Forums",      "url": "https://ezdhgsy2aw7zg54z6dqsutrduhl22moami5zv2zt6urr6vub7gs6wfad.onion",        "category": "forums",      "deep_scan": False, "risk": "low"},
    {"name": "RAMP Forum",         "url": "http://rampjcdlqvgkoz5oywutpo6ggl7g6tvddysustfl6qzhr5osr24xxqqd.onion",         "category": "forums",      "deep_scan": True,  "risk": "high"},
    {"name": "Best Carding World", "url": "http://bestteermb42clir6ux7xm76d4jjodh3fpahjqgbddbmfrgp4skg2wqd.onion/",       "category": "forums",      "deep_scan": True,  "risk": "high"},
    # ── Intel trackers ────────────────────────────────────────────────────────
    {"name": "RansomWiki",         "url": "http://ransomwr3tsydeii4q43vazm7wofla5ujdajquitomtd47cxjtfgwyyd.onion",          "category": "intel",       "deep_scan": False, "risk": "medium"},
    {"name": "RansomWiki Mirror",  "url": "http://ranswikiif2mir7mnnscyrsvppxmwwqrvc43fhtddvtnmhedkj4hopyd.onion",          "category": "intel",       "deep_scan": False, "risk": "medium"},
    # ── Ransomware groups ─────────────────────────────────────────────────────
    {"name": "Qilin",              "url": "http://ijzn3sicrcy7guixkzjkib4ukbiilwc3xhnmby4mcbccnsd7j2rekvqd.onion/",        "category": "ransomware",  "deep_scan": True,  "risk": "high"},
    {"name": "LockBit",            "url": "http://lockbitapyx2kr5b7ma7qn6ziwqgbrij2czhcbojuxmgnwpkgv2yx2yd.onion",         "category": "ransomware",  "deep_scan": True,  "risk": "high"},
    {"name": "CLOP",               "url": "http://santat7kpllt6iyvqbr7q4amdv6dzrh6paatvyrzl7ry3zm72zigf4ad.onion",          "category": "ransomware",  "deep_scan": True,  "risk": "high"},
    {"name": "BlackCat/ALPHV",     "url": "http://alphvmmm27o3abo3r2mlmjrpdmzle3rykajqc5xsj7j7ejksbpsa36ad.onion",          "category": "ransomware",  "deep_scan": True,  "risk": "high"},
    {"name": "Akira",              "url": "http://akiral2iz6a7qgd3ayp3l6yub7xx2uep76idk3u2kollpj5z3z636bad.onion",           "category": "ransomware",  "deep_scan": True,  "risk": "high"},
    {"name": "BianLian",           "url": "http://bianlianlbc5an4kgnay3opdemgcryg2kpfcbgczopmm3dnbz3uaunad.onion",           "category": "ransomware",  "deep_scan": True,  "risk": "high"},
    {"name": "RansomHub",          "url": "http://ransomxifxwc5eteopdobynonjctkxxvap77yqifu2emfbecgbqdw6qd.onion",           "category": "ransomware",  "deep_scan": True,  "risk": "high"},
    {"name": "Cicada3301",         "url": "http://cicadabv7vicyvgz5khl7v2x5yygcgow7ryy6yppwmxii4eoobdaztqd.onion",           "category": "ransomware",  "deep_scan": True,  "risk": "high"},
    {"name": "0APT",               "url": "http://oaptxiyisljt2kv3we2we34kuudmqda7f2geffoylzpeo7ourhtz4dad.onion",            "category": "ransomware",  "deep_scan": True,  "risk": "high"},
    # ── Leak sites ────────────────────────────────────────────────────────────
    {"name": "BreachForums",       "url": "http://breachforumsn55bgkuukf5zthzxzpqqwk2nttwe5qeqmilkiqvnlgqd.onion",          "category": "leak_site",   "deep_scan": True,  "risk": "high"},
    # ── Markets ───────────────────────────────────────────────────────────────
    {"name": "DarkWebLink",        "url": "http://dwltorbltw3tdjskxn23j2mwz2f4q25j4ninl5bdvttiy4xb6cqzikid.onion",           "category": "marketplace", "deep_scan": True,  "risk": "high"},
    {"name": "Dark Zone",          "url": "http://darkzonzfz7l4ophqzo5as5xv5y6ufjztrkjsqjmlvxjs6j2a4ito7yd.onion",           "category": "marketplace", "deep_scan": True,  "risk": "high"},
    # ── Monitoring ────────────────────────────────────────────────────────────
    {"name": "Dark Web Observatory","url": "http://u6q3zfc2i4w3dkjkpawbpgigkfthn7xebqhnpkzd7bufbysmpdud24ad.onion/",       "category": "monitoring",  "deep_scan": True,  "risk": "low"},
]


# ── Utilities ─────────────────────────────────────────────────────────────────
def load_json(p):
    if not os.path.exists(p):
        return {}
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(p, d):
    try:
        with open(p, 'w') as f:
            json.dump(d, f, indent=2)
    except Exception as e:
        print(f"[!] Error saving {p}: {e}")


def sanitize_filename(n):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', n).lower()


# ── Uptime / sparkline ────────────────────────────────────────────────────────
def update_uptime(name, status):
    h = load_json(UPTIME_HISTORY)
    if name not in h:
        h[name] = {'checks': []}
    h[name]['checks'].append({'ts': datetime.datetime.now().isoformat(), 'up': status == 'UP'})
    h[name]['checks'] = h[name]['checks'][-96:]
    checks = h[name]['checks']
    val = round((sum(1 for c in checks if c['up']) / len(checks)) * 100, 1) if checks else 0.0
    h[name]['uptime_24h'] = val
    save_json(UPTIME_HISTORY, h)
    return val


def get_sparkline(name):
    h = load_json(UPTIME_HISTORY)
    checks = h.get(name, {}).get('checks', [])[-12:]
    if not checks:
        return '<span style="color:#333">· · ·</span>'
    dots = []
    for c in checks:
        if c.get('up'):
            dots.append('<span style="color:#00ff00">●</span>')
        else:
            dots.append('<span style="color:#ff3333">●</span>')
    return ''.join(dots)


# ── Change detection ──────────────────────────────────────────────────────────
def detect_changes(name, curr_hash, curr_tech):
    h = load_json(CHANGE_HISTORY)
    ts = datetime.datetime.now().isoformat()
    if name not in h:
        h[name] = {'last_hash': curr_hash, 'last_technologies': curr_tech,
                   'last_changed': ts, 'changes': []}
        save_json(CHANGE_HISTORY, h)
        return {'changed': False}
    prev = h[name]
    changes = []
    if prev.get('last_hash') != curr_hash:
        changes.append('content')
    if changes:
        prev['changes'].append({'timestamp': ts, 'type': changes})
        prev['last_hash'] = curr_hash
        prev['last_changed'] = ts
        save_json(CHANGE_HISTORY, h)
        return {'changed': True, 'change_type': ', '.join(changes), 'last_changed': ts}
    return {'changed': False, 'last_changed': prev.get('last_changed')}


# ── Deep scan ─────────────────────────────────────────────────────────────────
def perform_deep_scan(url, resp):
    html = resp.text
    return {
        'emails':  list(set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', html)))[:10],
        'bitcoin': list(set(re.findall(r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b', html)))[:5],
        'onions':  [o for o in list(set(re.findall(r'[a-z2-7]{56}\.onion', html))) if o not in url][:10],
        'server':  resp.headers.get('Server', 'Unknown'),
        'technologies': ['WordPress'] if 'wp-content' in html else [],
        'hash':    hashlib.md5(html.encode()).hexdigest(),
        'forms':   len(re.findall(r'<form', html)),
    }


# ── Scanner ───────────────────────────────────────────────────────────────────
def extract_page_title(html):
    try:
        m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip()[:60] if m else "Unknown Title"
    except Exception:
        return "Unknown Title"


def check_site(t):
    """
    Single attempt, 15s timeout.
    No retries -- dead onion sites waste far more time on retry than they're worth.
    """
    try:
        s = time.time()
        r = requests.get(
            t['url'], proxies=PROXIES, headers=HEADERS,
            timeout=REQUEST_TIMEOUT, verify=False, allow_redirects=True,
        )
        lat  = round(time.time() - s, 2)
        code = r.status_code
        if 200 <= code < 300:
            status, color = 'UP', 'green'
        elif code == 403:
            status, color = 'UP (Blocked)', 'orange'
        elif code == 429:
            status, color = 'UP (Rate-limited)', 'orange'
        else:
            status, color = f'HTTP {code}', 'orange'
        res = {
            'status': status, 'latency': f"{lat}s", 'color': color,
            'title':  extract_page_title(r.text),
            'server': r.headers.get('Server', '-'),
            'deep_data': None,
        }
        if t.get('deep_scan'):
            res['deep_data'] = perform_deep_scan(t['url'], r)
        return res
    except requests.exceptions.ConnectionError:
        return {'status': 'DOWN', 'latency': '-', 'color': 'red', 'title': 'Connection Failed', 'server': '-', 'deep_data': None}
    except requests.exceptions.Timeout:
        return {'status': 'DOWN', 'latency': f'>{REQUEST_TIMEOUT}s', 'color': 'red', 'title': 'Timed Out', 'server': '-', 'deep_data': None}
    except Exception as e:
        return {'status': 'DOWN', 'latency': '-', 'color': 'red', 'title': str(e)[:50], 'server': '-', 'deep_data': None}


def scan_wrapper(t):
    print(f"  > {t['name']}")
    return t, check_site(t)


# ── Scan viewer (unchanged from original) ─────────────────────────────────────
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
                    <div class="box">${content}</div>`;
            }
        });
    </script>
</body>
</html>"""
    with open(SCAN_VIEWER, 'w') as f:
        f.write(html)


# ── Category colours ──────────────────────────────────────────────────────────
CAT_COLORS = {
    "news":        "#daa520",
    "search":      "#3cb371",
    "social":      "#20b2aa",
    "government":  "#4169e1",
    "privacy":     "#7b68ee",
    "email":       "#9370db",
    "index":       "#708090",
    "forums":      "#cd853f",
    "intel":       "#00ced1",
    "ransomware":  "#dc143c",
    "leak_site":   "#b22222",
    "marketplace": "#ff8c00",
    "monitoring":  "#2e8b57",
}
RISK_ICON = {"low": "🟢", "medium": "🟡", "high": "🔴"}


def _badge(category):
    color = CAT_COLORS.get(category, "#555")
    return (f'<span style="background:{color};color:#fff;border-radius:3px;'
            f'padding:2px 6px;font-size:0.72em;white-space:nowrap">{category}</span>')


def _status_cls(status):
    if "UP" in status:  return "status-UP"
    if status == "DOWN": return "status-DOWN"
    return "status-OTHER"


# ── Dashboard ─────────────────────────────────────────────────────────────────

def generate_report(targets_override=None):
    create_scan_viewer()
    ts_str  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    targets = targets_override if targets_override is not None else TARGETS

    print(f"[*] Scanning {len(targets)} targets with {MAX_WORKERS} workers (timeout={REQUEST_TIMEOUT}s)...")

    all_results = []
    deep_data   = load_json(DEEP_SCAN_DB)
    change_hist = load_json(CHANGE_HISTORY)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(scan_wrapper, t): t for t in targets}
        for f in concurrent.futures.as_completed(futures):
            t, r = f.result()
            name = t['name']
            chg  = {'changed': False}

            if r['deep_data']:
                deep_data[name] = r['deep_data']
                chg = detect_changes(name, r['deep_data']['hash'], [])

            uptime   = update_uptime(name, r['status'])
            l_change = chg.get('last_changed', change_hist.get(name, {}).get('last_changed', '-'))
            if l_change and l_change != '-':
                l_change = l_change[5:16].replace('T', ' ')

            all_results.append({
                'name':              name,
                'url':               t['url'],
                'category':          t.get('category', 'other'),
                'risk':              t.get('risk', 'low'),
                'result':            r,
                'deep_scan_enabled': t.get('deep_scan', False),
                'uptime_24h':        uptime,
                'last_changed':      l_change,
                'known_status':      t.get('known_status', ''),
                'source':            t.get('source', ''),
            })

    save_json(DEEP_SCAN_DB, deep_data)

    # Deep scan sub-pages
    for n, d in deep_data.items():
        with open(f"{DEEP_SCAN_DIR}/{sanitize_filename(n)}.html", 'w') as fh:
            fh.write(
                f"<html><body style='background:#111;color:#ccc;font-family:monospace;padding:20px'>"
                f"<h1>{n}</h1><p>Generated: {ts_str}</p>"
                f"<div style='background:#000;padding:20px;border:1px solid #333'>"
                f"<h3>Emails</h3>{len(d.get('emails', []))} found<br>"
                f"<h3>Bitcoin</h3>{len(d.get('bitcoin', []))} found</div></body></html>"
            )

    # Metrics
    tot      = len(targets)
    up       = sum(1 for x in all_results if x['result']['status'] == 'UP')
    down     = sum(1 for x in all_results if x['result']['status'] == 'DOWN')
    deep_act = sum(1 for x in all_results if x['deep_scan_enabled'])
    iocs     = sum(len(d.get('emails', [])) + len(d.get('bitcoin', [])) for d in deep_data.values())
    em_cnt   = sum(len(d.get('emails', [])) for d in deep_data.values())
    btc_cnt  = sum(len(d.get('bitcoin', [])) for d in deep_data.values())

    print(f"[+] Scan complete: {up} UP / {down} DOWN / {tot-up-down} other out of {tot}")

    # Group by category for sidebar + cards
    grouped = {}
    for row in all_results:
        grouped.setdefault(row['category'], []).append(row)

    # Sidebar nav
    nav_items = ""
    for cat in sorted(grouped):
        color    = CAT_COLORS.get(cat, "#555")
        up_in    = sum(1 for row in grouped[cat] if "UP" in row['result']['status'])
        total_in = len(grouped[cat])
        nav_items += (
            f'<a href="#cat-{cat}" class="nav-item" style="border-left:3px solid {color}">'
            f'{cat} <span class="nav-count">{up_in}/{total_in}</span></a>\n'
        )

    # Card sections
    sections_html = ""
    for cat in sorted(grouped):
        color = CAT_COLORS.get(cat, "#555")
        cards = ""
        for row in grouped[cat]:
            res    = row['result']
            spark  = get_sparkline(row['name'])
            risk   = RISK_ICON.get(row['risk'], '🟢')
            sc     = _status_cls(res['status'])
            deep_lnk = (
                f'<a href="deep_scans/{sanitize_filename(row["name"])}.html" class="card-deep">scan →</a>'
                if row['deep_scan_enabled'] else ''
            )
            known = (
                f'<span class="known-offline">repo:{row["known_status"]}</span>'
                if row.get('known_status') else ''
            )
            src = (
                f'<div class="card-source">{row["source"]}</div>'
                if row.get('source') else ''
            )
            badge = _badge(cat)
            cards += (
                f'<div class="card">'
                f'<div class="card-header"><span class="card-name" title="{row["url"]}">{risk} {row["name"]}</span>{badge}</div>'
                f'<div class="card-status {sc}">{res["status"]}</div>'
                f'<div class="card-meta"><span>⏱ {res["latency"]}</span><span>📈 {row["uptime_24h"]}%</span>'
                f'<span class="card-spark">{spark}</span></div>'
                f'<div class="card-detail" title="{res["title"]}">{res["title"][:55]}{"…" if len(res["title"]) > 55 else ""}</div>'
                f'<div class="card-footer">{deep_lnk}{known}{src}</div>'
                f'</div>'
            )

        sections_html += (
            f'<section class="cat-section" id="cat-{cat}">'
            f'<h2 class="cat-title" style="border-left:4px solid {color}">'
            f'{cat.upper()} <span class="cat-count">{len(grouped[cat])}</span></h2>'
            f'<div class="card-grid">{cards}</div>'
            f'</section>'
        )

    # ── CSS ───────────────────────────────────────────────────────────────────
    css = """
        :root {
            --bg:#050505; --bg2:#0f0f0f; --bg3:#1a1a1a;
            --border:#252525; --text:#e0e0e0; --muted:#666;
            --green:#00ff00; --red:#ff3333; --orange:#ffa500;
            --blue:#00aaff; --sidebar:210px;
        }
        * { box-sizing:border-box; margin:0; padding:0; }
        body { font-family:'Courier New',monospace; background:var(--bg); color:var(--text); display:flex; min-height:100vh; font-size:14px; }
        a { color:var(--blue); text-decoration:none; }
        a:hover { text-decoration:underline; }
        .sidebar { width:var(--sidebar); background:var(--bg2); border-right:1px solid var(--border); position:fixed; top:0; left:0; height:100vh; overflow-y:auto; padding:16px 0; z-index:100; }
        .sidebar-logo { color:var(--green); font-size:0.8em; font-weight:bold; text-transform:uppercase; padding:0 14px 14px; border-bottom:1px solid var(--border); letter-spacing:2px; }
        .nav-section-title { color:var(--muted); font-size:0.65em; text-transform:uppercase; letter-spacing:2px; padding:14px 14px 4px; }
        .nav-item { display:flex; justify-content:space-between; align-items:center; padding:6px 14px; color:var(--text); text-decoration:none; font-size:0.78em; transition:background 0.15s; }
        .nav-item:hover { background:var(--bg3); color:#fff; text-decoration:none; }
        .nav-count { background:var(--bg3); border:1px solid var(--border); border-radius:10px; padding:1px 6px; font-size:0.8em; color:var(--muted); }
        .main { margin-left:var(--sidebar); flex:1; padding:20px 24px; }
        h1 { color:var(--green); border-bottom:2px solid #333; padding-bottom:10px; margin-bottom:5px; text-transform:uppercase; }
        .sub-header { color:var(--muted); font-size:0.85em; margin-bottom:20px; }
        .metrics-container { border:2px solid var(--green); padding:14px; margin-bottom:24px; background:var(--bg2); }
        .metrics-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:10px; }
        .metric-box { background:var(--bg3); padding:10px; border-left:3px solid var(--border); }
        .metric-label { font-size:0.72em; color:var(--muted); text-transform:uppercase; }
        .metric-value { font-size:1.4em; font-weight:bold; color:#fff; margin-top:4px; }
        .val-green { color:var(--green); } .val-red { color:var(--red); }
        .cat-section { margin-bottom:32px; scroll-margin-top:16px; }
        .cat-title { font-size:0.82em; text-transform:uppercase; letter-spacing:2px; padding:5px 10px; margin-bottom:12px; background:var(--bg2); border-radius:4px; display:flex; align-items:center; gap:10px; }
        .cat-count { background:var(--bg3); border:1px solid var(--border); border-radius:10px; padding:1px 7px; font-size:0.75em; color:var(--muted); }
        .card-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:10px; }
        .card { background:var(--bg2); border:1px solid var(--border); border-radius:6px; padding:12px; transition:border-color 0.2s; }
        .card:hover { border-color:#3a3a3a; }
        .card-header { display:flex; justify-content:space-between; align-items:flex-start; gap:6px; margin-bottom:7px; }
        .card-name { font-size:0.82em; font-weight:bold; color:#ccc; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1; }
        .card-status { font-size:0.82em; font-weight:bold; padding:2px 7px; border-radius:3px; display:inline-block; margin-bottom:7px; }
        .status-UP    { color:var(--green);  background:#00ff0012; }
        .status-DOWN  { color:var(--red);    background:#ff333312; }
        .status-OTHER { color:var(--orange); background:#ffa50012; }
        .card-meta { display:flex; gap:8px; font-size:0.72em; color:var(--muted); margin-bottom:5px; flex-wrap:wrap; }
        .card-detail { font-size:0.72em; color:#888; font-style:italic; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .card-footer { margin-top:5px; font-size:0.68em; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
        .card-deep { color:var(--green); border:1px solid var(--green); padding:1px 5px; border-radius:2px; }
        .card-source { color:#444; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .known-offline { background:#2a0000; color:#ff6666; border-radius:3px; padding:1px 5px; }
        .tool-section { margin-bottom:24px; background:var(--bg2); border:1px solid var(--border); padding:14px; border-left:4px solid var(--blue); }
        .input-group { display:flex; gap:10px; margin-top:10px; }
        input[type=text] { background:#000; border:1px solid #333; color:#fff; padding:8px; flex:1; font-family:inherit; }
        button { background:#003366; color:var(--blue); border:1px solid var(--blue); padding:8px 14px; cursor:pointer; font-weight:bold; }
        .news-section { border-left:4px solid var(--orange) !important; }
        .news-header { display:flex; justify-content:space-between; margin-bottom:14px; }
        .news-filters button { background:#111; color:#666; border:1px solid #333; margin-left:5px; }
        .news-filters button.active { background:#221100; color:var(--orange); border-color:var(--orange); }
        .news-item { border-bottom:1px solid #222; padding:7px 0; }
        .refresh-btn { background:#1a1000 !important; color:var(--orange) !important; border:1px solid var(--orange) !important; margin-right:14px; }
        .ip-card { margin-top:10px; padding:10px; background:#000; border-left:3px solid var(--red); }
        .ip-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.9em; }
        .ip-label { color:#666; font-size:0.8em; text-transform:uppercase; }
        .dot-up { color:var(--green); } .dot-down { color:var(--red); } .dot-none { color:#333; }
        @media(max-width:768px) { .sidebar { display:none; } .main { margin-left:0; } }
    """

    # ── JS -- plain string, zero f-string brace issues ────────────────────────
    js = """
  let allNews = [];
  fetch('news_feed.json').then(r=>r.json()).then(d=>{
      allNews=d.articles||[];
      const c=document.getElementById('newsFilters');
      const cats=[...new Set(allNews.map(a=>a.category))].filter(Boolean);
      c.innerHTML='<button class="active" onclick="filt(\'all\')">ALL</button>';
      cats.forEach(x=>c.innerHTML+=`<button onclick="filt('${x}')">${x.toUpperCase()}</button>`);
      render(allNews.slice(0,20));
  }).catch(()=>document.getElementById('news-feed-container').innerHTML='Feed unavailable.');

  function filt(cat){
      document.querySelectorAll('.news-filters button').forEach(b=>
          b.classList.toggle('active',b.innerText===cat.toUpperCase()||(cat==='all'&&b.innerText==='ALL')));
      render(cat==='all'?allNews:allNews.filter(a=>a.category===cat));
  }
  function render(list){
      const d=document.getElementById('news-feed-container');
      if(!list.length)return d.innerHTML='No news.';
      d.innerHTML=list.map(a=>`
          <div class="news-item">
              <div style="font-size:0.75em;color:#666;margin-bottom:3px;">
                  <span style="color:#00ff00;">[${a.category.toUpperCase()}]</span>
                  <span style="color:#00aaff;margin-left:10px;">${a.source}</span>
                  <span style="float:right;">${a.published||''}</span>
              </div>
              <a href="${a.link}" target="_blank" style="color:#e0e0e0;font-weight:bold;">${a.title}</a>
          </div>`).join('');
  }
  function refreshNews(){
      document.querySelector('.refresh-btn').innerHTML='⏳...';
      fetch('/cgi-bin/refresh_news.py',{method:'POST'}).then(()=>location.reload());
  }
  function startScan(){
      const u=document.getElementById('ondemandUrl').value.trim();
      if(!u)return alert('Enter URL');
      window.open('scan_viewer.html?url='+encodeURIComponent(u),'_blank');
  }
  function checkIP(){
      const i=document.getElementById('ipInput').value.trim();
      const d=document.getElementById('ipResult');
      if(!i)return;
      d.innerHTML='Analyzing...';
      fetch('/cgi-bin/check_ip.py',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ip:i})})
      .then(r=>r.json()).then(res=>{
          if(res.error){d.innerHTML=`<span style="color:red">${res.error}</span>`;return;}
          const x=res.data;
          d.innerHTML=`<div class="ip-card">
              <h3 style="margin-top:0;color:${x.abuseConfidenceScore>50?'#f33':'#0f0'}">Risk: ${x.abuseConfidenceScore}%</h3>
              <div class="ip-grid">
                  <div><span class="ip-label">ISP:</span> ${x.isp}</div>
                  <div><span class="ip-label">Country:</span> ${x.countryCode}</div>
                  <div><span class="ip-label">Domain:</span> ${x.domain||'N/A'}</div>
                  <div><span class="ip-label">Usage:</span> ${x.usageType||'N/A'}</div>
                  <div><span class="ip-label">Reports:</span> ${x.totalReports}</div>
                  <div><span class="ip-label">Last Reported:</span> ${x.lastReportedAt||'Never'}</div>
              </div></div>`;
      });
  }
"""

    # ── Assemble final HTML ───────────────────────────────────────────────────
    html = (
        '<!DOCTYPE html>\n<html>\n<head>\n'
        '<title>Dark Web Observatory</title>\n'
        '<meta charset="UTF-8">\n'
        f'<style>{css}</style>\n'
        '</head>\n<body>\n'

        # Sidebar
        '<nav class="sidebar">\n'
        '<div class="sidebar-logo">👁 Observatory</div>\n'
        '<div class="nav-section-title">Categories</div>\n'
        f'{nav_items}'
        '<div class="nav-section-title">Pages</div>\n'
        '<a href="/index.html" class="nav-item" style="border-left:3px solid #333">Dashboard</a>\n'
        '<a href="/intelligence.json" class="nav-item" style="border-left:3px solid #333">JSON Feed</a>\n'
        '<a href="/alert_statistics.html" class="nav-item" style="border-left:3px solid #333">Alert Stats</a>\n'
        '<a href="/historical_trends.html" class="nav-item" style="border-left:3px solid #333">Trends</a>\n'
        '<a href="/threat_feeds.html" class="nav-item" style="border-left:3px solid #333">Threat Feeds</a>\n'
        '</nav>\n'

        # Main
        '<main class="main">\n'
        '<h1>Dark Web Observatory</h1>\n'
        f'<div class="sub-header">Last Scan: {ts_str} &nbsp;·&nbsp; '
        f'{tot} targets &nbsp;·&nbsp; {MAX_WORKERS} workers &nbsp;·&nbsp; {REQUEST_TIMEOUT}s timeout &nbsp;·&nbsp;'
        '<a href="intelligence.json">JSON</a> | '
        '<a href="alert_statistics.html">Alert Stats</a> | '
        '<a href="historical_trends.html">Trends</a> | '
        '<a href="threat_feeds.html">Threat Feeds</a></div>\n'

        # Metrics
        '<div class="metrics-container">\n'
        '<div style="color:#00ff00;font-weight:bold;margin-bottom:12px;">📊 INTELLIGENCE SUMMARY (LAST SCAN)</div>\n'
        '<div class="metrics-grid">\n'
        f'<div class="metric-box"><div class="metric-label">Targets</div><div class="metric-value">{tot}</div></div>\n'
        f'<div class="metric-box"><div class="metric-label">Up</div><div class="metric-value val-green">{up}</div></div>\n'
        f'<div class="metric-box"><div class="metric-label">Down</div><div class="metric-value val-red">{down}</div></div>\n'
        f'<div class="metric-box"><div class="metric-label">Deep Scans</div><div class="metric-value">{deep_act}</div></div>\n'
        f'<div class="metric-box"><div class="metric-label">IOCs</div><div class="metric-value val-red">{iocs}</div></div>\n'
        f'<div class="metric-box"><div class="metric-label">Emails</div><div class="metric-value">{em_cnt}</div></div>\n'
        f'<div class="metric-box"><div class="metric-label">BTC</div><div class="metric-value">{btc_cnt}</div></div>\n'
        '</div>\n</div>\n'

        # Card sections
        f'{sections_html}\n'

        # On-demand scan
        '<div class="tool-section">\n'
        '<div style="color:#00aaff;font-weight:bold;text-transform:uppercase;">🔍 On-Demand Deep Scan</div>\n'
        '<div style="font-size:0.8em;color:#666;margin-bottom:5px;">Enter .onion URL. Opens report in new tab.</div>\n'
        '<div class="input-group">'
        '<input type="text" id="ondemandUrl" placeholder="http://example.onion">'
        '<button onclick="startScan()">Scan Now →</button>'
        '</div>\n</div>\n'

        # IP check
        '<div class="tool-section" style="border-left-color:#ff3333;">\n'
        '<div style="color:#ff3333;font-weight:bold;text-transform:uppercase;">🛑 IP Reputation Check</div>\n'
        '<div class="input-group">'
        '<input type="text" id="ipInput" placeholder="1.2.3.4">'
        '<button onclick="checkIP()" style="border-color:#ff3333;color:#ff3333;">Check IP →</button>'
        '</div>\n<div id="ipResult"></div>\n</div>\n'

        # News
        '<div class="tool-section news-section">\n'
        '<div class="news-header">'
        '<div style="color:#ffa500;font-weight:bold;text-transform:uppercase;">📰 Latest Cybersecurity News</div>'
        '<div><button class="refresh-btn" onclick="refreshNews()">🔄 Refresh Feed</button>'
        '<div class="news-filters" id="newsFilters" style="display:inline-block;"></div></div>'
        '</div>\n'
        '<div id="news-feed-container">Loading...</div>\n'
        '</div>\n'

        '<p style="margin-top:40px;font-size:0.75em;color:#444;">Dark Web Observatory &nbsp;·&nbsp; For educational/OSINT research use only.</p>\n'
        '</main>\n'
        f'<script>{js}</script>\n'
        '</body>\n</html>'
    )

    with open(OUTPUT_HTML, 'w') as f:
        f.write(html)
    print(f"[+] Dashboard updated: {OUTPUT_HTML}")

    # Downstream modules
    print("[*] Triggering aggregators...")
    try:
        from news_feed_aggregator import aggregate_news_feed
        aggregate_news_feed()
    except Exception as e:
        print(f"[!] News feed error: {e}")
    try:
        from generate_alert_stats import generate_alert_statistics
        generate_alert_statistics()
    except Exception as e:
        print(f"[!] Alert stats error: {e}")
    try:
        from generate_historical_trends import generate_historical_trends
        generate_historical_trends()
    except Exception as e:
        print(f"[!] Trend stats error: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Dark Web Observatory Scanner")
    parser.add_argument("--fetch-remote", action="store_true",
                        help="Force refresh remote CTI target feeds")
    args = parser.parse_args()

    try:
        from remote_targets import fetch_and_merge, merge_with_local
        print("[*] Loading remote CTI feeds...")
        remote  = fetch_and_merge(force=args.fetch_remote)
        targets = merge_with_local(TARGETS, remote)
    except ImportError:
        print("[!] remote_targets.py not found — using local TARGETS only")
        targets = TARGETS
    except Exception as e:
        print(f"[!] Remote merge failed ({e}) — using local TARGETS only")
        targets = TARGETS

    generate_report(targets_override=targets)
