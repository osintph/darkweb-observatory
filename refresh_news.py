#!/usr/bin/python3
import cgitb
import sys
import json
import datetime
import re
from datetime import datetime as dt

# Enable debug reporting (prints to stderr, won't break JSON)
cgitb.enable(format="text")

# REQUIRED: Tell the browser we are sending JSON
print("Content-Type: application/json\n")

# Configuration
OUTPUT_FILE = "/var/www/html/news_feed.json"
NEWS_SOURCES = [
    {'name': 'The Hacker News', 'url': 'https://feeds.feedburner.com/TheHackersNews', 'category': 'General'},
    {'name': 'Krebs on Security', 'url': 'https://krebsonsecurity.com/feed/', 'category': 'Investigation'},
    {'name': 'Bleeping Computer', 'url': 'https://www.bleepingcomputer.com/feed/', 'category': 'General'},
    {'name': 'Dark Reading', 'url': 'https://www.darkreading.com/rss_simple.asp', 'category': 'Enterprise'},
    {'name': 'Threatpost', 'url': 'https://threatpost.com/feed/', 'category': 'Threat Intel'}
]

def clean_html(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', text).strip()

try:
    # Capture standard output to prevent print() from breaking JSON
    from io import StringIO
    original_stdout = sys.stdout
    sys.stdout = sys.stderr

    import feedparser
    
    all_articles = []
    
    # FETCH NEWS
    for source in NEWS_SOURCES:
        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries[:5]:
                published = entry.get('published', entry.get('updated', datetime.datetime.now().isoformat()))
                article = {
                    'title': clean_html(entry.get('title', 'No Title')),
                    'link': entry.get('link', '#'),
                    'description': clean_html(entry.get('summary', entry.get('description', '')))[:300],
                    'published': published,
                    'source': source['name'],
                    'category': source['category']
                }
                all_articles.append(article)
        except Exception as e:
            continue

    # SAVE JSON
    output = {
        'generated': datetime.datetime.now().isoformat(),
        'total_articles': len(all_articles),
        'articles': all_articles
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
        
    # RESTORE OUTPUT AND PRINT SUCCESS
    sys.stdout = original_stdout
    print(json.dumps({"success": True, "message": f"Refreshed {len(all_articles)} articles"}))

except Exception as e:
    sys.stdout = sys.__stdout__
    print(json.dumps({"success": False, "error": str(e)}))
