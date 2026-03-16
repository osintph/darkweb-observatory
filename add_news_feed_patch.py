#!/usr/bin/env python3
import re

SCANNER_FILE = '/home/osint_lab/dark-monitor/advanced_scanner.py'

NEWS_FEED_WIDGET = '''        
        <!-- Cybersecurity News Feed Widget -->
        <div style="background: #1a1a1a; padding: 20px; margin: 30px 0; border-left: 4px solid #ffa500;">
            <h2 style="color: #ffa500; border-bottom: 1px solid #444; padding-bottom: 8px; margin-top: 0;">
                📰 Latest Cybersecurity News
            </h2>
            <div id="news-feed-container">
                <p style="color: #888;">Loading news feed...</p>
            </div>
        </div>
        
        <script>
        fetch('news_feed.json')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('news-feed-container');
                const articles = data.articles.slice(0, 5);
                
                if (!articles || articles.length === 0) {
                    container.innerHTML = '<p style="color: #888;">No news articles available.</p>';
                    return;
                }
                
                let html = '<div style="display: grid; gap: 15px;">';
                
                articles.forEach(article => {
                    const cleanTitle = (article.title || '').replace(/<[^>]*>/g, '');
                    const cleanDesc = (article.description || '').replace(/<[^>]*>/g, '').substring(0, 150) + '...';
                    const publishDate = article.published ? article.published.substring(0, 16) : 'Unknown';
                    
                    html += '<div style="background: #0a0a0a; padding: 15px; border-left: 3px solid #00aaff;">';
                    html += '<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">';
                    html += '<strong style="color: #00aaff; font-size: 1.05em;">' + cleanTitle + '</strong>';
                    html += '<span style="color: #666; font-size: 0.85em; white-space: nowrap; margin-left: 10px;">' + article.source + '</span>';
                    html += '</div>';
                    html += '<p style="color: #ccc; font-size: 0.9em; margin: 8px 0;">' + cleanDesc + '</p>';
                    html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">';
                    html += '<span style="color: #888; font-size: 0.85em;">📅 ' + publishDate + '</span>';
                    html += '<a href="' + article.link + '" target="_blank" style="color: #00ff00; text-decoration: none; font-size: 0.9em;" rel="noopener noreferrer">Read More →</a>';
                    html += '</div></div>';
                });
                
                html += '</div>';
                container.innerHTML = html;
            })
            .catch(error => {
                console.error('Error loading news feed:', error);
                document.getElementById('news-feed-container').innerHTML = '<p style="color: #ff3333;">Failed to load news feed.</p>';
            });
        </script>
'''

# Read file
with open(SCANNER_FILE, 'r') as f:
    content = f.read()

# Check if already added
if 'Cybersecurity News Feed Widget' in content:
    print("[!] News feed already exists in scanner!")
    exit(0)

# Find the LAST </body> tag (main dashboard, not deep scan pages)
# Look for the pattern with "Powered by Tor Network" footer nearby
pattern = r'(Powered by Tor Network.*?</p>\s*)(</body>)'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Insert news widget before </body>
    new_content = content[:match.end(1)] + NEWS_FEED_WIDGET + '\n        ' + match.group(2) + content[match.end():]
    
    # Backup
    import shutil
    from datetime import datetime
    backup = f"{SCANNER_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(SCANNER_FILE, backup)
    print(f"[+] Backup created: {backup}")
    
    # Write
    with open(SCANNER_FILE, 'w') as f:
        f.write(new_content)
    print("[✓] News feed widget added successfully!")
    print("\nRun: cd ~/dark-monitor && source venv/bin/activate && python advanced_scanner.py")
else:
    print("[!] Could not find insertion point. Please add manually.")

