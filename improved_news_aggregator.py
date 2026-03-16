#!/usr/bin/env python3
import feedparser
import json
from datetime import datetime
import requests

NEWS_SOURCES = [
    {'name': 'The Hacker News', 'url': 'https://feeds.feedburner.com/TheHackersNews', 'category': 'general'},
    {'name': 'Krebs on Security', 'url': 'https://krebsonsecurity.com/feed/', 'category': 'investigation'},
    {'name': 'Bleeping Computer', 'url': 'https://www.bleepingcomputer.com/feed/', 'category': 'news'},
    {'name': 'Threat Post', 'url': 'https://threatpost.com/feed/', 'category': 'threats'},
    {'name': 'Dark Reading', 'url': 'https://www.darkreading.com/rss.xml', 'category': 'enterprise'},
]

def aggregate_news_feed():
    """Aggregate cybersecurity news from multiple sources"""
    all_articles = []
    
    print("[*] Aggregating cybersecurity news...")
    
    for source in NEWS_SOURCES:
        try:
            print(f"  [*] Fetching from {source['name']}...")
            feed = feedparser.parse(source['url'])
            
            for entry in feed.entries[:10]:  # Top 10 from each
                article = {
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', '#'),
                    'description': entry.get('summary', entry.get('description', 'No description'))[:300],
                    'published': entry.get('published', datetime.now().isoformat()),
                    'source': source['name'],
                    'category': source['category']
                }
                all_articles.append(article)
            
            print(f"    [+] Retrieved {len(feed.entries[:10])} articles")
        except Exception as e:
            print(f"    [!] Failed: {e}")
    
    # Sort by publication date (newest first)
    all_articles.sort(key=lambda x: x['published'], reverse=True)
    
    # Save to JSON
    output = {
        'last_updated': datetime.now().isoformat(),
        'total_articles': len(all_articles),
        'articles': all_articles[:25]  # Keep top 25
    }
    
    with open('/var/www/html/news_feed.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"[+] Saved {len(all_articles[:25])} articles to news_feed.json")

if __name__ == '__main__':
    aggregate_news_feed()
