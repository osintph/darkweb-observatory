#!/usr/bin/env python3
import json

# Read the current HTML
with open('/var/www/html/index.html', 'r') as f:
    html = f.read()

# Read the news data
try:
    with open('/var/www/html/news_feed.json', 'r') as f:
        news_data = f.read()
except:
    news_data = '{"articles":[],"last_updated":"","total_articles":0}'

# Find where the fetch is and replace with embedded data
old_fetch = '''        // Load news feed
        fetch('/news_feed.json?t=' + Date.now())  // Cache bust
            .then(response => response.json())
            .then(data => {
                allNewsArticles = data.articles || [];
                
                // Update last update time
                const lastUpdate = new Date(data.last_updated);
                document.getElementById('news-last-update').textContent = 
                    'Updated: ' + lastUpdate.toLocaleString();
                
                renderNews();
            })
            .catch(error => {
                console.error('Error loading news feed:', error);
                document.getElementById('news-feed-container').innerHTML = 
                    '<p style="color: #ff3333; text-align: center; padding: 40px;">⚠️ Failed to load news feed. Check connection.</p>';
            });'''

new_embedded = f'''        // Load news from embedded data
        const newsData = {news_data};
        
        allNewsArticles = newsData.articles || [];
        
        if (allNewsArticles.length > 0) {{
            const lastUpdate = new Date(newsData.last_updated);
            document.getElementById('news-last-update').textContent = 
                'Updated: ' + lastUpdate.toLocaleString();
            renderNews();
        }} else {{
            document.getElementById('news-feed-container').innerHTML = 
                '<p style="color: #888; text-align: center; padding: 40px;">No news articles available yet.</p>';
        }}'''

html = html.replace(old_fetch, new_embedded)

# Write back
with open('/var/www/html/index.html', 'w') as f:
    f.write(html)

print("[+] Embedded news data directly into index.html")
