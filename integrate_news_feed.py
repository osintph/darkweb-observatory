#!/usr/bin/env python3
"""
Script to add news feed widget to advanced_scanner.py main dashboard
"""

import re

SCANNER_FILE = '/home/osint_lab/dark-monitor/advanced_scanner.py'

# News feed widget HTML to insert
NEWS_WIDGET_HTML = '''
        <!-- Cybersecurity News Feed Widget -->
        <div class="news-widget">
            <h2 style="color: #ffa500; border-bottom: 1px solid #444; padding-bottom: 8px; margin-top: 30px;">
                📰 Latest Cybersecurity News
            </h2>
            <div id="news-feed-container">
                <p style="color: #888;">Loading news feed...</p>
            </div>
        </div>
        
        <script>
        // Load news feed
        fetch('news_feed.json')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('news-feed-container');
                const articles = data.articles.slice(0, 5); // Show top 5 articles
                
                if (articles.length === 0) {
                    container.innerHTML = '<p style="color: #888;">No news articles available.</p>';
                    return;
                }
                
                let html = '<div style="display: grid; gap: 15px;">';
                
                articles.forEach(article => {
                    const cleanTitle = article.title.replace(/<[^>]*>/g, '');
                    const cleanDesc = article.description.replace(/<[^>]*>/g, '').substring(0, 150) + '...';
                    const publishDate = article.published ? article.published.substring(0, 16).replace('T', ' ') : 'Unknown';
                    
                    html += `
                        <div style="background: #1a1a1a; padding: 15px; border-left: 3px solid #ffa500;">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                                <strong style="color: #00aaff; font-size: 1.05em;">${cleanTitle}</strong>
                                <span style="color: #666; font-size: 0.85em; white-space: nowrap; margin-left: 10px;">${article.source}</span>
                            </div>
                            <p style="color: #ccc; font-size: 0.9em; margin: 8px 0;">${cleanDesc}</p>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                                <span style="color: #888; font-size: 0.85em;">📅 ${publishDate}</span>
                                <a href="${article.link}" target="_blank" style="color: #00ff00; text-decoration: none; font-size: 0.9em;" rel="noopener noreferrer">Read More →</a>
                            </div>
                        </div>
                    `;
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

def integrate_news_feed():
    """Add news feed widget to main dashboard"""
    
    print("[*] Reading advanced_scanner.py...")
    
    try:
        with open(SCANNER_FILE, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"[!] Failed to read file: {e}")
        return False
    
    # Check if already integrated
    if 'Cybersecurity News Feed Widget' in content:
        print("[!] News feed widget already integrated!")
        return True
    
    # Find the insertion point (before the closing </body> tag in generate_report function)
    # Look for the final </body></html> in the main dashboard HTML
    pattern = r'(</body>\s*</html>\s*""")'
    
    match = re.search(pattern, content)
    
    if not match:
        print("[!] Could not find insertion point in HTML")
        return False
    
    # Insert news widget before </body>
    insertion_point = match.start()
    new_content = content[:insertion_point] + NEWS_WIDGET_HTML + '\n        ' + content[insertion_point:]
    
    # Backup original
    import shutil
    from datetime import datetime
    backup_file = f"{SCANNER_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(SCANNER_FILE, backup_file)
    print(f"[+] Backup created: {backup_file}")
    
    # Write new content
    try:
        with open(SCANNER_FILE, 'w') as f:
            f.write(new_content)
        print("[+] News feed widget integrated successfully!")
        return True
    except Exception as e:
        print(f"[!] Failed to write file: {e}")
        # Restore backup
        shutil.copy2(backup_file, SCANNER_FILE)
        print("[!] Restored from backup")
        return False

if __name__ == "__main__":
    print("="*60)
    print("News Feed Integration Script")
    print("="*60)
    
    success = integrate_news_feed()
    
    if success:
        print("\n[✓] Integration complete!")
        print("\nNext steps:")
        print("1. Run: cd ~/dark-monitor && source venv/bin/activate")
        print("2. Run: python advanced_scanner.py")
        print("3. Access your dashboard to see the news feed!")
    else:
        print("\n[✗] Integration failed!")

