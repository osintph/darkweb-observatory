import os

file_path = 'advanced_scanner.py'
with open(file_path, 'r') as f:
    lines = f.readlines()

enhanced_js = r"""
        <script>
        let allArticles = [];

        // 1. Enhanced IP Check with Usage Type and Domain
        function checkIP() {
            const ip = document.getElementById('ipInput').value.trim();
            const btn = document.getElementById('ipBtn');
            const resultDiv = document.getElementById('ipResult');
            if (!ip) return;
            btn.disabled = true; btn.innerHTML = '⏳ Analyzing...';
            fetch('/cgi-bin/check_ip.py', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ ip: ip })
            })
            .then(res => res.json())
            .then(data => {
                btn.disabled = false; btn.innerHTML = 'Check IP →';
                if (data.error) { resultDiv.innerHTML = 'Error: ' + data.error; return; }
                const info = data.data;
                const score = info.abuseConfidenceScore;
                let color = score > 75 ? '#ff3333' : (score > 25 ? '#ffa500' : '#00ff00');
                
                resultDiv.innerHTML = `
                    <div class="scan-result-card" style="border-left: 4px solid ${color};">
                        <h3 style="color:${color}; margin-top:0;">Risk Profile: ${score}% Confidence</h3>
                        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:15px;">
                            <div style="background:#0a0a0a; padding:12px; border:1px solid #222;">
                                <span style="color:#888; font-size:0.8em;">INFRASTRUCTURE</span><br>
                                <span>${info.isp}</span><br>
                                <span style="color:#666; font-size:0.85em;">Type: ${info.usageType || 'N/A'}</span>
                            </div>
                            <div style="background:#0a0a0a; padding:12px; border:1px solid #222;">
                                <span style="color:#888; font-size:0.8em;">GEOLOCATION</span><br>
                                <span>${info.countryName || info.countryCode}</span><br>
                                <span style="color:#666; font-size:0.85em;">Domain: ${info.domain || 'N/A'}</span>
                            </div>
                            <div style="background:#0a0a0a; padding:12px; border:1px solid #222;">
                                <span style="color:#888; font-size:0.8em;">REPORT SUMMARY</span><br>
                                <span>Total Reports: ${info.totalReports}</span><br>
                                <span style="color:#666; font-size:0.85em;">Distinct Users: ${info.numDistinctUsers}</span>
                            </div>
                        </div>
                    </div>`;
            }).catch(() => { btn.disabled = false; });
        }

        // 2. Enhanced Manual Scan with Tech Fingerprinting & Links
        function startOnDemandScan() {
            const url = document.getElementById('ondemandUrl').value.trim();
            const btn = document.getElementById('scanBtn');
            const resultsDiv = document.getElementById('scanResults');
            if (!url) return;
            btn.disabled = true; btn.innerHTML = '⏳ Scanning...';
            resultsDiv.innerHTML = '<p style="color:#ffa500;">🔄 Performing Reconnaissance on Tor Network...</p>';
            fetch('/cgi-bin/on_demand_scan.py', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: url })
            })
            .then(res => res.json())
            .then(data => {
                btn.disabled = false; btn.innerHTML = 'Scan Now →';
                if (!data.success) { resultsDiv.innerHTML = 'Error: ' + data.error; return; }
                
                let techHtml = data.technologies.length > 0 
                    ? data.technologies.map(t => `<span style="background:#003300; color:#00ff00; padding:2px 6px; border-radius:3px; font-size:0.8em; margin-right:5px;">${t}</span>`).join('')
                    : '<span style="color:#555;">No signatures detected</span>';

                resultsDiv.innerHTML = `
                    <div class="scan-result-card" style="border-left-color: #00ff00;">
                        <h3 style="color:#00ff00; margin-top:0;">✓ Target Identification: ${data.title}</h3>
                        <p style="color:#888; font-size:0.9em; margin-bottom:15px;">URL: ${data.url}</p>
                        
                        <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; margin-bottom:20px;">
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

                        <div style="background:#0d0d0d; padding:15px; border:1px solid #222;">
                            <div style="margin-bottom:10px;"><strong>Server signature:</strong> <span style="color:#00aaff;">${data.server_analysis.server}</span></div>
                            <div style="margin-bottom:10px;"><strong>Tech Stack:</strong> ${techHtml}</div>
                            <div><strong>OPSEC Audit:</strong> ${data.server_analysis.real_ip_leaked === 'No' ? '<span style="color:#00ff00;">No clear IP leaks found</span>' : '<span style="color:#ff3333;">WARNING: IP Leak Possible</span>'}</div>
                        </div>
                    </div>`;
            }).catch(() => { btn.disabled = false; });
        }

        // 3. News Feed logic (Restored)
        fetch('news_feed.json').then(res => res.json()).then(data => {
            allArticles = data.articles || [];
            renderNews(allArticles.slice(0, 20));
        });

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
                            <a href="${a.link}" target="_blank" style="color:#e0e0e0; font-weight:bold;">${a.title}</a>
                        </div>
                    </div>`;
            });
            container.innerHTML = html + '</div>';
        }

        function refreshNewsFeed() { fetch('/cgi-bin/refresh_news.py', {method:'POST'}).then(() => location.reload()); }
        function filterCategory(category) {
            document.querySelectorAll('.category-tag').forEach(tag => tag.classList.toggle('active', tag.dataset.category === category));
            document.querySelectorAll('#targetsTable tbody tr').forEach(row => row.classList.toggle('hidden', category !== 'all' && row.dataset.category !== category));
        }
        </script>
"""

new_content = []
in_script = False
for line in lines:
    if '<script>' in line:
        in_script = True
        new_content.append(enhanced_js + '\n')
    if '</script>' in line:
        in_script = False
        continue
    if not in_script:
        new_content.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_content)
