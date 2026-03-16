import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import json
import re
from email.utils import parsedate_to_datetime

# Output files
NEWS_DATABASE = "/var/www/html/news_feed.json"

# Active cybersecurity news feeds
NEWS_FEEDS = {
    'bleeping_computer': 'https://www.bleepingcomputer.com/feed/',
    'krebs': 'https://krebsonsecurity.com/feed/',
    'the_hacker_news': 'https://thehackernews.com/feeds/posts/default',
    'security_week': 'https://www.securityweek.com/feed/',
    'dark_reading': 'https://www.darkreading.com/rss.xml'
}

def clean_tag(tag):
    """Remove namespace definition from tag name for easier parsing"""
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

def get_text_safe(element, tag_name):
    """Recursively search for a tag ignoring namespaces"""
    # Direct match
    if element.find(tag_name) is not None:
        return element.find(tag_name).text
    
    # Namespace match
    for child in element:
        if clean_tag(child.tag) == tag_name:
            return child.text
    return None

def get_attrib_safe(element, tag_name, attrib):
    """Get attribute from tag ignoring namespaces"""
    for child in element:
        if clean_tag(child.tag) == tag_name:
            return child.get(attrib)
    return None

def determine_category(title, description):
    """Auto-categorize article based on keywords"""
    text = (str(title) + " " + str(description)).lower()
    
    if any(x in text for x in ['ransomware', 'encrypt', 'extortion', 'lockbit', 'clop', 'blackcat', 'negotiation']):
        return 'Ransomware'
    if any(x in text for x in ['breach', 'leak', 'stolen', 'database', 'exposed', 'exfiltrated', 'dumped']):
        return 'Data Breaches'
    if any(x in text for x in ['cve', 'vulnerability', 'patch', 'zero-day', '0-day', 'exploit', 'flaw', 'bug']):
        return 'Vulnerabilities'
    if any(x in text for x in ['apt', 'malware', 'spyware', 'trojan', 'campaign', 'actor', 'phishing', 'backdoor', 'botnet']):
        return 'Threat Intel'
    if any(x in text for x in ['fbi', 'arrest', 'sentenced', 'court', 'charge', 'police', 'seized', 'guilty']):
        return 'Law Enforcement'
    if any(x in text for x in ['bank', 'crypto', 'bitcoin', 'scam', 'fraud', 'laundering']):
        return 'Financial Crime'
        
    return 'General News'

def fetch_rss_feed(feed_name, feed_url):
    try:
        print(f"  [*] Fetching {feed_name}...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'}
        resp = requests.get(feed_url, timeout=15, headers=headers)
        
        # Parse XML
        root = ET.fromstring(resp.content)
        articles = []
        
        # Find all items/entries regardless of namespace
        items = []
        for elem in root.iter():
            if clean_tag(elem.tag) in ['item', 'entry']:
                items.append(elem)
            
        for item in items[:8]:  # Fetch top 8 from each source
            try:
                # Extract fields using namespace-safe helper
                title = get_text_safe(item, 'title') or 'No Title'
                
                # Link can be text or href attribute
                link = get_text_safe(item, 'link')
                if not link:
                    link = get_attrib_safe(item, 'link', 'href')
                if not link:
                    link = '#'

                # Description
                description = get_text_safe(item, 'description') or get_text_safe(item, 'summary') or ''
                
                # Date
                pub_date_str = get_text_safe(item, 'pubDate') or get_text_safe(item, 'published') or ''
                
                # Attempt to parse date for sorting
                sort_key = 0
                if pub_date_str:
                    try:
                        dt_obj = parsedate_to_datetime(pub_date_str)
                        sort_key = dt_obj.timestamp()
                    except:
                        pass

                # Clean HTML from description
                clean_desc = ''
                if description:
                    clean_desc = re.sub(r'<[^>]+>', '', description)[:250] + '...'
                
                # Auto-Categorize
                category = determine_category(title, clean_desc)

                articles.append({
                    'title': title,
                    'link': link,
                    'description': clean_desc,
                    'published': pub_date_str,
                    'source': feed_name.replace('_', ' ').title(),
                    'category': category,
                    'sort_key': sort_key
                })
            except Exception as e:
                continue
        
        return articles
    except Exception as e:
        print(f"    [!] Failed {feed_name}: {e}")
        return []

def aggregate_news_feed():
    print("[*] Aggregating cybersecurity news feeds...")
    all_news = []
    
    for name, url in NEWS_FEEDS.items():
        all_news.extend(fetch_rss_feed(name, url))
    
    # Sort by date (newest first)
    all_news.sort(key=lambda x: x['sort_key'], reverse=True)
    
    # Take top 30 to keep JSON light
    final_list = all_news[:30]
    
    data = {
        'last_updated': datetime.now().isoformat(),
        'articles': final_list
    }
    
    try:
        with open(NEWS_DATABASE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[+] Saved {len(final_list)} articles to {NEWS_DATABASE}")
    except Exception as e:
        print(f"[!] Failed to save database: {e}")

if __name__ == "__main__":
    aggregate_news_feed()
