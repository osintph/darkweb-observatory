import os

file_path = 'advanced_scanner.py'
with open(file_path, 'r') as f:
    lines = f.readlines()

# The final, fully featured JS block with dynamic categories
final_js = r"""
        <script>
        let allArticles = [];

        // 1. Fetch News and Build Dynamic Category Filters
        fetch('news_feed.json').then(res => res.json()).then(data => {
            const container = document.getElementById('news-feed-container');
            const filterContainer = document.getElementById('newsFilters');
            allArticles = data.articles || [];
            
            if (allArticles.length === 0) {
                container.innerHTML = '<p style="color: #888;">No news available.</p>';
                return;
            }

            // Extract unique categories
            const categories = [...new Set(allArticles.map(a => a.category))].filter(Boolean);
            
            // Build filter buttons
            categories.forEach(cat => {
                const btn = document.createElement('button');
                btn.className = 'news-filter-btn';
                btn.innerText = cat.toUpperCase();
                btn.onclick = () => filterByNewsCategory(cat);
                filterContainer.appendChild(btn);
            });

            renderNews(allArticles.slice(0, 25));
        }).catch(() => {
            document.getElementById('news-feed-container').innerHTML = '<p style="color: #ff3333;">Feed Error</p>';
        });

        function filterByNewsCategory(category) {
            // Update button styles
            document.querySelectorAll('.news-filter-btn').forEach(btn => {
                const isMatch = btn.innerText === category.toUpperCase() || (category === 'all' && btn.innerText === 'ALL');
                btn.classList.toggle('active', isMatch);
            });

            // Filter and render
            const filtered = category === 'all' ? allArticles : allArticles.filter(a => a.category === category);
            renderNews(filtered.slice(0, 25));
        }

        function renderNews(articles) {
            const container = document.getElementById('news-feed-container');
            let html = '<div style="display: grid; gap: 15px;">';
            articles.forEach(a => {
                html += `
                    <div class="news-card">
                        <div class="news-meta">
                            <div><span class="news-source-tag" style="color:#00ff00;">[${(a.category || 'GENERAL').toUpperCase()}]</span>
                            <span style="margin-left:10px; color:#00aaff;">${a.source}</span></div>
                            <span class="news-date">${a.published || ''}</span>
                        </div>
                        <div style="margin-bottom:8px;">
                            <a href="${a.link}" target="_blank" style="color:#e0e0e0; font-weight:bold; font-size:1.1em; text-decoration:none;">${a.title}</a>
                        </div>
                        <p style="color:#999; font-size:0.9em; margin:0; line-height:1.4;">${(a.description || '').substring(0, 200)}...</p>
                    </div>`;
            });
            container.innerHTML = html + '</div>';
        }

        // 2. IP Detail Logic (Maintained)
        function checkIP() {
            const ip = document.getElementById('ipInput').value.trim();
            const btn = document.getElementById('ipBtn');
            const resultDiv = document.getElementById('ipResult');
            if (!ip) return;
            btn.disabled = true; btn.innerHTML = '⏳...';
            fetch('/cgi-bin/check_ip.py', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ ip: ip })
            })
            .then(res => res.json())
            .then(data => {
                btn.disabled = false; btn.innerHTML = 'Check IP →';
                const info = data.data;
                const score = info.abuseConfidenceScore;
                let color = score > 75 ? '#ff3333' : (score > 25 ? '#ffa500' : '#00ff00');
                resultDiv.innerHTML = `
                    <div class="scan-result-card" style="border-left: 4px solid ${color};">
                        <h3 style="color:${color}; margin-top:0;">Risk: ${score}% (${info.usageType || 'Standard'})</h3>
                        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:10px;">
                            <div style="background:#0d0d0d; padding:10px;"><span style="color:#888;">ISP</span><br><span>${info.isp}</span></div>
                            <div style="background:#0d0d0d; padding:10px;"><span style="color:#888;">COUNTRY</span><br><span>${info.countryCode}</span></div>
                            <div style="background:#0d0d0d; padding:10px;"><span style="color:#888;">HOSTS</span><br><span>${info.hostnames?.[0] || 'None'}</span></div>
                        </div>
                    </div>`;
            }).catch(() => { btn.disabled = false; btn.innerHTML = 'Check IP →'; });
        }

        // 3. Manual Scan Logic (Maintained)
        function startOnDemandScan() {
            const url = document.getElementById('ondemandUrl').value.trim();
            const btn = document.getElementById('scanBtn');
            const resultsDiv = document.getElementById('scanResults');
            if (!url) return;
            btn.disabled = true; btn.innerHTML = '⏳...';
            resultsDiv.innerHTML = '<p style="color:#ffa500;">🔄 Scanning Onion Network...</p>';
            fetch('/cgi-bin/on_demand_scan.py', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: url })
            })
            .then(res => res.json())
            .then(data => {
                btn.disabled = false; btn.innerHTML = 'Scan Now →';
                if (!data.success) { resultsDiv.innerHTML = 'Error: ' + data.error; return; }
                resultsDiv.innerHTML = `
                    <div class="scan-result-card">
                        <h3 style="color:#00ff00; margin-top:0;">✓ Recon: ${data.title}</h3>
                        <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; margin-top:10px;">
                            <div style="background:#0d0d0d; padding:10px; border:1px solid #333; text-align:center;">
                                <div style="color:#888; font-size:0.8em;">EMAILS</div><div style="color:#ff3333; font-weight:bold;">${data.emails.length}</div>
                            </div>
                            <div style="background:#0d0d0d; padding:10px; border:1px solid #333; text-align:center;">
                                <div style="color:#888; font-size:0.8em;">BITCOIN</div><div style="color:#ffa500; font-weight:bold;">${data.bitcoin_addresses.length}</div>
                            </div>
                            <div style="background:#0d0d0d; padding:10px; border:1px solid #333; text-align:center;">
                                <div style="color:#888; font-size:0.8em;">ONIONS</div><div style="color:#00aaff; font-weight:bold;">${data.linked_onions.length}</div>
                            </div>
                        </div>
                    </div>`;
            }).catch(() => { btn.disabled = false; });
        }

        function refreshNewsFeed() { fetch('/cgi-bin/refresh_news.py', {method:'POST'}).then(() => location.reload()); }
        </script>
"""

new_content = []
in_script = False
for line in lines:
    if '<script>' in line:
        in_script = True
        new_content.append(final_js + '\n')
    if '</script>' in line:
        in_script = False
        continue
    if not in_script:
        new_content.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_content)
