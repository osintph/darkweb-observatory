import requests
import socks
import socket
import datetime
import urllib3
import re
import time

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
OUTPUT_HTML = "/var/www/html/index.html"

# Pre-configured Target List
TARGETS = [
    {
        "name": "New York Times",
        "url": "https://nytimesn7cgmftshazwhfgzm37qxb44r64ytbb2dj3x62d2lljsciiyd.onion"
    },
    {
        "name": "BBC News",
        "url": "https://www.bbcweb3hytmzhn5d532owbu6oqadra5z3ar726vq5kgwwn6aucdccrad.onion"
    },
    {
        "name": "ProPublica",
        "url": "https://p53lf57qovyuvwsc6xnrppyply3vtqm7l6pcobkmyqsiofyeznfu5uqd.onion"
    },
    {
        "name": "CIA",
        "url": "https://ciadotgov4sjwlzihbbgxnqg3xiyrg7so2r2o3lt5wz5ypk4sxyjstad.onion"
    },
    {
        "name": "Facebook",
        "url": "https://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion"
    },
    {
        "name": "The Guardian",
        "url": "https://www.guardian2zotagl6tmjucg3lrhxdk4dw3lhbqnkvvkywawy3oqfoprid.onion"
    },
    {
        "name": "DuckDuckGo",
        "url": "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion"
    }
]
# ---------------------


# Configure Tor Proxy (Remote DNS Resolution)
PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'
}

def get_page_title(html_content):
    """Simple regex to extract the <title> tag"""
    try:
        match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()[:40]  # Truncate to 40 chars
    except:
        pass
    return "Unknown Title"

def check_site(url):
    try:
        start_time = time.time()
        # Timeout 60s
        resp = requests.get(url, proxies=PROXIES, headers=HEADERS, timeout=60, verify=False)
        latency = round(time.time() - start_time, 2)
        
        title = get_page_title(resp.text)
        
        if 200 <= resp.status_code < 300:
            return "UP", "green", f"{latency}s", title
        elif resp.status_code == 403:
            return "UP (Blocked)", "orange", f"{latency}s", "403 Forbidden"
        else:
            return "ISSUES", "orange", f"{latency}s", f"Status {resp.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "DOWN", "red", "-", "Connection Failed"
    except requests.exceptions.Timeout:
        return "DOWN", "red", ">60s", "Timed Out"
    except Exception as e:
        return "ERROR", "red", "-", str(e)[:30]

def generate_report():
    # FIX: Get local time with correct Timezone Name (e.g., PST/CST)
    now = datetime.datetime.now().astimezone()
    timestamp = now.strftime("%Y-%m-%d %H:%M %Z")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dark Web Observatory</title>
        <meta http-equiv="refresh" content="300"> 
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0d0d0d; color: #e0e0e0; padding: 20px; }}
            h1 {{ color: #00ff00; text-transform: uppercase; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            table {{ border-collapse: collapse; width: 100%; max-width: 1400px; margin-top: 20px; font-size: 0.9em; }}
            th, td {{ border: 1px solid #333; padding: 12px; text-align: left; vertical-align: middle; }}
            th {{ background-color: #1a1a1a; color: #fff; text-transform: uppercase; letter-spacing: 1px; }}
            tr:nth-child(even) {{ background-color: #111; }}
            a {{ color: #888; text-decoration: none; }}
            a:hover {{ color: #fff; text-decoration: underline; }}
         .green {{ color: #00ff00; font-weight: bold; background-color: #001a00; text-align: center; }}
         .orange {{ color: #ffa500; font-weight: bold; background-color: #1a1000; text-align: center; }}
         .red {{ color: #ff3333; font-weight: bold; background-color: #1a0000; text-align: center; }}
         .small {{ font-size: 0.85em; color: #999; }}
         .title-text {{ font-style: italic; color: #aaa; }}
        </style>
    </head>
    <body>
        <h1>/var/log/onion_status</h1>
        <p>Last Scan: {timestamp}</p>
        <table>
            <tr>
                <th style="width: 15%">Target Name</th>
                <th style="width: 35%">Onion Address</th>
                <th style="width: 8%">Status</th>
                <th style="width: 8%">Latency</th>
                <th style="width: 34%">Page Title / Error</th>
            </tr>
    """

    print(f"[*] Starting scan at {timestamp}")
    for target in TARGETS:
        print(f"  > Scanning {target['name']}...")
        status, color, latency, detail = check_site(target['url'])
        print(f"    Result: {status} ({latency}s)")
        
        html_content += f"""
            <tr>
                <td>{target['name']}</td>
                <td class="small"><a href="{target['url']}">{target['url']}</a></td>
                <td class="{color}">{status}</td>
                <td style="text-align: center;">{latency}</td>
                <td class="title-text">{detail}</td>
            </tr>
        """

    html_content += """
        </table>
        <p style="margin-top:50px; font-size: 0.8em; color: #555;">
            <i>Generated by Automated Local Sentinel (Ubuntu 25.04)</i>
        </p>
    </body>
    </html>
    """

    try:
        with open(OUTPUT_HTML, "w") as f:
            f.write(html_content)
        print(f"[*] Report successfully updated")
    except PermissionError:
        print("[!] Error: Cannot write to /var/www/html.")

if __name__ == "__main__":
    generate_report()
