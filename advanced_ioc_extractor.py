import re
import hashlib

def extract_ipv4_addresses(content):
    """Extract IPv4 addresses"""
    ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    ips = list(set(re.findall(ipv4_pattern, content)))
    
    # Filter out private/reserved IPs
    filtered_ips = []
    for ip in ips:
        octets = ip.split('.')
        first_octet = int(octets[0])
        second_octet = int(octets[1])
        
        # Skip private ranges
        if first_octet == 10:  # 10.0.0.0/8
            continue
        if first_octet == 172 and 16 <= second_octet <= 31:  # 172.16.0.0/12
            continue
        if first_octet == 192 and second_octet == 168:  # 192.168.0.0/16
            continue
        if first_octet == 127:  # 127.0.0.0/8 (localhost)
            continue
        if first_octet == 0:  # 0.0.0.0/8
            continue
        
        filtered_ips.append(ip)
    
    return filtered_ips[:15]  # Limit to 15

def extract_ipv6_addresses(content):
    """Extract IPv6 addresses"""
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b|\b::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b'
    ipv6s = list(set(re.findall(ipv6_pattern, content, re.IGNORECASE)))
    return ipv6s[:10]

def extract_clearnet_domains(content):
    """Extract clearnet domains (not onion)"""
    domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
    domains = list(set(re.findall(domain_pattern, content)))
    
    # Filter out .onion and common false positives
    filtered = []
    for domain in domains:
        if '.onion' in domain.lower():
            continue
        if domain.lower() in ['localhost.local', 'example.com', 'test.com']:
            continue
        # Must have valid TLD
        if '.' not in domain:
            continue
        filtered.append(domain)
    
    return filtered[:20]

def extract_file_hashes(content):
    """Extract MD5, SHA1, SHA256 hashes"""
    hashes = {
        'md5': [],
        'sha1': [],
        'sha256': []
    }
    
    # MD5 (32 hex chars)
    md5_pattern = r'\b[a-fA-F0-9]{32}\b'
    hashes['md5'] = list(set(re.findall(md5_pattern, content)))[:10]
    
    # SHA1 (40 hex chars)
    sha1_pattern = r'\b[a-fA-F0-9]{40}\b'
    hashes['sha1'] = list(set(re.findall(sha1_pattern, content)))[:10]
    
    # SHA256 (64 hex chars)
    sha256_pattern = r'\b[a-fA-F0-9]{64}\b'
    hashes['sha256'] = list(set(re.findall(sha256_pattern, content)))[:10]
    
    return hashes

def extract_urls(content):
    """Extract URLs (http/https)"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = list(set(re.findall(url_pattern, content, re.IGNORECASE)))
    
    # Filter out onion URLs
    filtered = [url for url in urls if '.onion' not in url.lower()]
    return filtered[:15]

def extract_telegram_handles(content):
    """Extract Telegram usernames"""
    telegram_pattern = r'@[a-zA-Z0-9_]{5,32}\b'
    handles = list(set(re.findall(telegram_pattern, content)))
    return handles[:10]

def extract_crypto_addresses(content):
    """Extract various cryptocurrency addresses"""
    crypto = {
        'bitcoin': [],
        'ethereum': [],
        'monero': [],
        'litecoin': []
    }
    
    # Bitcoin (already have this, but let's be more thorough)
    btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|bc1[a-z0-9]{39,59}\b'
    crypto['bitcoin'] = list(set(re.findall(btc_pattern, content)))[:10]
    
    # Ethereum (0x followed by 40 hex chars)
    eth_pattern = r'\b0x[a-fA-F0-9]{40}\b'
    crypto['ethereum'] = list(set(re.findall(eth_pattern, content)))[:10]
    
    # Monero (starts with 4, 8, or 9, 95 chars)
    xmr_pattern = r'\b[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'
    crypto['monero'] = list(set(re.findall(xmr_pattern, content)))[:10]
    
    # Litecoin (starts with L or M)
    ltc_pattern = r'\b[LM][a-km-zA-HJ-NP-Z1-9]{26,33}\b'
    crypto['litecoin'] = list(set(re.findall(ltc_pattern, content)))[:10]
    
    return crypto

def extract_phone_numbers(content):
    """Extract phone numbers"""
    # International format
    phone_pattern = r'\+?[1-9]\d{1,14}'
    phones = list(set(re.findall(phone_pattern, content)))
    
    # Filter out likely false positives (too short, etc)
    filtered = [p for p in phones if len(p) >= 10]
    return filtered[:10]

def extract_cve_ids(content):
    """Extract CVE identifiers"""
    cve_pattern = r'CVE-\d{4}-\d{4,7}'
    cves = list(set(re.findall(cve_pattern, content, re.IGNORECASE)))
    return cves[:15]

def extract_all_advanced_iocs(content):
    """Extract all advanced IOCs from content"""
    
    return {
        'ipv4_addresses': extract_ipv4_addresses(content),
        'ipv6_addresses': extract_ipv6_addresses(content),
        'clearnet_domains': extract_clearnet_domains(content),
        'file_hashes': extract_file_hashes(content),
        'urls': extract_urls(content),
        'telegram_handles': extract_telegram_handles(content),
        'crypto_addresses': extract_crypto_addresses(content),
        'phone_numbers': extract_phone_numbers(content),
        'cve_ids': extract_cve_ids(content)
    }

