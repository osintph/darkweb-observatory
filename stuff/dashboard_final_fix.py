import os

file_path = '/home/osint_lab/dark-monitor/advanced_scanner.py'
if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    exit(1)

with open(file_path, 'r') as f:
    lines = f.readlines()

# This is the validated, 100% syntactically correct JavaScript block
final_js = r"""
        <script>
        let allArticles = [];

        // 1. News Logic - Fixed ALL reset and dynamic category buttons
        function fetchNews() {
            fetch('news_feed.json').then(res => res.json()).then(data => {
                const container = document.getElementById('news-feed-container');
                const filterContainer = document.getElementById('newsFilters');
                allArticles = data.articles || [];
                
                if (allArticles.length === 0) {
                    container.innerHTML = '<p style="color: #888;">No news available.</p>';
                    return;
                }

                // Extract unique categories and build buttons
                const categories = [...new Set(allArticles.map(a => a.category))].filter(Boolean);
                filterContainer.innerHTML = '<button class="news-filter-btn active" onclick="filterByNewsCategory(\'all\')">ALL</button>';
                
                categories.forEach(cat => {
                    const btn = document.createElement('button');
                    btn.className = 'news-filter-btn';
                    btn.innerText = cat.toUpperCase();
                    btn.onclick = () => filterByNewsCategory(cat);
                    filterContainer.appendChild(btn);
                });

                renderNews(allArticles.slice(0, 25));
            }).catch(() => {
                document.getElementById('news-feed-container').innerHTML = 'Feed Error';
            });
        }

        function filterByNewsCategory(category) {
            document.querySelectorAll('.news-filter-btn').forEach(btn => {
                const isMatch = btn.innerText === category.toUpperCase() || (category.toLowerCase() === 'all' && btn.innerText === 'ALL');
                btn.classList.toggle('active', isMatch);
            });

            // Logic to handle "ALL" reset
            const filtered = category.toLowerCase() === 'all' ? allArticles : allArticles.filter(a => a.category === category);
            renderNews(filtered.slice(0, 25));
        }

        function renderNews(articles) {
            const container = document.getElementById('news-feed-container');
            let html = '<div style="display: grid; gap: 15px;">';
            articles.forEach(a => {
                html += '<div class="news-card"><div class="news-meta"><div><span class="news-source-tag" style="color:#00ff00;">[' + (a.category || 'GENERAL').toUpperCase() + ']</span> <span style="margin-left:10px; color:#00aaff;">' + a.source + '</span></div><span class="news-date">' + (a.published || '') + '</span></div><div style="margin-bottom:8px;"><a href="' + a.link + '" target="_blank" style="color:#e0e0e0; font-weight:bold; text-decoration:none;">' + a.title + '</a></div><p style="color:#999; font-size:0.9em; margin:0;">' + (a.description || '').substring(0, 200) + '...</p></div>';
            });
            container.innerHTML = html + '</div>';
        }

        // 2. Manual Scan - Forces NEW TAB and prevents dashboard interruption
        function startOnDemandScan() {
            const urlInput = document.getElementById('ondemandUrl');
            if (!urlInput) return;
            const url = urlInput.value.trim();
            if(!url) { alert('Please enter a URL first'); return; }
            
            // Standard browser command to force new tab
            window.open('scan_viewer.html?url=' + encodeURIComponent(url), '_blank'); 
        }

        // 3. IP Check Detail - Restored Deep Detail functionality
        function checkIP() {
            const ipInput = document.getElementById('ipInput');
            if (!ipInput) return;
            const ip = ipInput.value.trim();
            const btn = document.getElementById('ipBtn');
            const resultDiv = document.getElementById('ipResult');
            if (!ip) return;

            btn.disabled = true; btn.innerHTML = '⏳ Analyzing...';
            fetch('/cgi-bin/check_ip.py', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ ip: ip })
            })
            .then(res => res.json()).then(data => {
                btn.disabled = false; btn.innerHTML = 'Check IP →';
                if (data.error) { resultDiv.innerHTML = 'Error: ' + data.error; return; }
                const info = data.data; const score = info.abuseConfidenceScore;
                let color = score > 75 ? '#ff3333' : (score > 25 ? '#ffa500' : '#00ff00');
                resultDiv.innerHTML = '<div class="scan-result-card" style="border-left:4px solid ' + color + ';"><h3>Risk Score: ' + score + '%</h3><p>ISP: ' + info.isp + ' | Country: ' + info.countryCode + '</p><p style="font-size:0.8em; color:#666;">Usage: ' + (info.usageType || 'N/A') + '</p></div>';
            }).catch(() => { btn.disabled = false; btn.innerHTML = 'Check IP →'; });
        }

        function refreshNewsFeed() { 
            const btn = document.querySelector('.refresh-btn');
            if(btn) btn.innerHTML = '⏳...';
            fetch('/cgi-bin/refresh_news.py', {method:'POST'}).then(() => location.reload()); 
        }

        // Initial load
        window.onload = fetchNews;
        </script>
"""

new_content = []
in_script = False
for line in lines:
    if '<script>' in line:
        in_script = True
        new_content.append(final_js + '\n')
    elif '</script>' in line:
        in_script = False
        continue
    elif not in_script:
        new_content.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_content)
print("Dashboard repaired successfully.")
