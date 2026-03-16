with open('advanced_scanner.py', 'r') as f:
    content = f.read()

# Fix the broken news header
old_broken = '''        <div class="news-widget">
            <div class="news-header">
                <h2 class="news-title">📰 Latest Cybersecurity News</h2>
                <div class="news-filters" id="newsFilters">
                    <button class="refresh-news-btn" onclick="refreshNewsFeed()" id="refreshNewsBtn">🔄 Refresh Feed</button>
                    <button class="news-filter-btn active" onclick="filterNews('all')">ALL</button>
                    </div>
            </div>'''

new_fixed = '''        <div class="news-widget">
            <div class="news-header">
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <h2 class="news-title" style="margin: 0;">📰 Latest Cybersecurity News</h2>
                    <button onclick="refreshNewsFeed()" id="refreshNewsBtn" class="refresh-news-btn">
                        🔄 Refresh Feed
                    </button>
                </div>
            </div>
            <div class="news-filters" id="newsFilters" style="margin: 15px 0;">
                <!-- Categories populated by JavaScript -->
            </div>'''

content = content.replace(old_broken, new_fixed)

with open('advanced_scanner.py', 'w') as f:
    f.write(content)

print("[✓] Fixed!")
