#!/usr/bin/env python3
"""
On-Demand Deep Scan API
Allows users to scan any onion URL and get a one-time report
"""

import sys
import json
import requests
import urllib3
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import hashlib
import re

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'
}

# Import extraction functions from main scanner
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
BITCOIN_PATTERN = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|bc1[a-z0-9]{39,59}\b')
PGP_BLOCK_PATTERN = re.compile(r'-----BEGIN PGP PUBLIC KEY BLOCK-----(.*?)-----END PGP PUBLIC KEY BLOCK-----', re.DOTALL)
PGP_FINGERPRINT_PATTERN = re.compile(r'[A-F0-9]{8,40}')
ONION_PATTERN = re.compile(r'[a-z2-7]{16,56}\.onion')
TITLE_PATTERN = re.compile(r'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)

def extract_emails(content):
    return list(set(EMAIL_PATTERN.findall(content)))[:10]

def extract_bitcoin_addresses(content):
    return list(set(BITCOIN_PATTERN.findall(content)))[:5]

def extract_pgp_keys(content):
    blocks = PGP_BLOCK_PATTERN.findall(content)[:3]
    fingerprints = []
    for block in blocks:
        m = PGP_FINGERPRINT_PATTERN.search(block)
        if m: fingerprints.append(m.group(0))
    return fingerprints

def extract_onion_links(html_content, base_url):
    onions = list(set(ONION_PATTERN.findall(html_content)))
    base = urlparse(base_url).netloc
    return [o for o in onions if o != base][:10]

def extract_page_title(html_content):
    try:
        match = TITLE_PATTERN.search(html_content)
        if match: return match.group(1).strip()[:60]
    except: pass
    return "Unknown Title"

def analyze_server_headers(headers):
    analysis = {
        'server': headers.get('Server', 'Unknown'),
        'x_powered_by': headers.get('X-Powered-By', 'None'),
        'backend': headers.get('X-Backend-Server', 'None'),
        'real_ip_leaked': headers.get('X-Real-IP', 'No'),
        'php_version': None, 'apache_version': None, 'nginx_version': None
    }
    if 'Apache' in analysis['server']:
        m = re.search(r'Apache/([\d.]+)', analysis['server'])
        if m: analysis['apache_version'] = m.group(1)
    if 'nginx' in analysis['server']:
        m = re.search(r'nginx/([\d.]+)', analysis['server'])
        if m: analysis['nginx_version'] = m.group(1)
    if 'PHP' in analysis['x_powered_by']:
        m = re.search(r'PHP/([\d.]+)', analysis['x_powered_by'])
        if m: analysis['php_version'] = m.group(1)
    return analysis

def check_security_headers(headers):
    return {
        'csp': headers.get('Content-Security-Policy', 'Missing'),
        'x_frame_options': headers.get('X-Frame-Options', 'Missing'),
        'xss_protection': headers.get('X-XSS-Protection', 'Missing'),
        'hsts': headers.get('Strict-Transport-Security', 'Missing'),
        'referrer_policy': headers.get('Referrer-Policy', 'Missing')
    }

def detect_technologies(html, headers):
    techs = []
    html_l = html.lower()
    if 'wp-content' in html_l or 'wordpress' in html_l: techs.append('WordPress')
    if 'drupal' in html_l: techs.append('Drupal')
    if 'joomla' in html_l: techs.append('Joomla')
    if 'django' in html_l: techs.append('Django')
    if 'laravel' in html_l: techs.append('Laravel')
    if 'react' in html_l: techs.append('React')
    if 'phpbb' in html_l: techs.append('phpBB')
    if 'PHP' in headers.get('X-Powered-By', ''): techs.append('PHP')
    if 'ASP.NET' in headers.get('X-Powered-By', ''): techs.append('ASP.NET')
    return techs

def extract_forms(soup):
    forms = []
    for form in soup.find_all('form')[:5]:
        data = {'action': form.get('action', 'N/A'), 'method': form.get('method', 'GET').upper(), 'inputs': []}
        for inp in form.find_all(['input', 'textarea']):
            data['inputs'].append({'name': inp.get('name', 'unnamed'), 'type': inp.get('type', 'text')})
        forms.append(data)
    return forms

def perform_deep_scan(url):
    """
    Perform a one-time deep scan on any onion URL
    Returns JSON result
    """
    
    # Validate onion URL
    if not url.endswith('.onion') and '.onion/' not in url:
        return {
            'success': False,
            'error': 'Invalid URL: Must be a .onion address',
            'url': url
        }
    
    try:
        print(f"[*] Scanning: {url}", file=sys.stderr)
        
        resp = requests.get(url, proxies=PROXIES, headers=HEADERS, timeout=90, verify=False)
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Build scan result
        result = {
            'success': True,
            'timestamp': datetime.datetime.now().isoformat(),
            'url': url,
            'http_code': resp.status_code,
            'title': extract_page_title(resp.text),
            'emails': extract_emails(resp.text),
            'bitcoin_addresses': extract_bitcoin_addresses(resp.text),
            'pgp_keys': extract_pgp_keys(resp.text),
            'linked_onions': extract_onion_links(resp.text, url),
            'server_analysis': analyze_server_headers(resp.headers),
            'security_headers': check_security_headers(resp.headers),
            'technologies': detect_technologies(resp.text, resp.headers),
            'forms': extract_forms(soup),
            'content_length': len(resp.content),
            'ssl_info': {
                'enabled': url.startswith('https'),
                'version': getattr(resp.raw, 'version', 'Unknown')
            }
        }
        
        print(f"[+] Scan complete", file=sys.stderr)
        return result
        
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Connection failed - site may be down or unreachable',
            'url': url
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timeout (>90s) - site is very slow or unresponsive',
            'url': url
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Scan error: {str(e)}',
            'url': url
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'No URL provided. Usage: python3 on_demand_scan.py <onion_url>'
        }))
        sys.exit(1)
    
    url = sys.argv[1].strip()
    result = perform_deep_scan(url)
    
    # Output JSON to stdout
    print(json.dumps(result, indent=2))
