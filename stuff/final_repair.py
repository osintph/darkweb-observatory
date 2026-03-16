import re

file_path = '/home/osint_lab/dark-monitor/advanced_scanner.py'
with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
skip_js = False

# This re-writes the core JS block to ensure no nested functions or broken braces
fixed_js = """
        <script>
        let allArticles = [];

        function filterNews(category) {
            document.querySelectorAll('.news-filter-btn').forEach(btn => {
                if (btn.innerText === category.toUpperCase() || (category === 'all' && btn.innerText === 'ALL')) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            if (category === 'all') { renderNews(allArticles); } 
            else { renderNews(allArticles.filter(a => a.category === category)); }
        }

        function checkIP() {
            const ip = document.getElementById('ipInput').value.trim();
            const btn = document.getElementById('ipBtn');
            const resultDiv = document.getElementById('ipResult');
            if (!ip) return;
            btn.disabled = true; btn.innerHTML = 'Checking...';
            fetch('/cgi-bin/check_ip.py', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ ip: ip })
            })
            .then(res => res.json())
            .then(data => {
                btn.disabled = false; btn.innerHTML = 'Check IP →';
                if (data.error) { resultDiv.innerHTML = 'Error: ' + data.error; return; }
                const score = data.data.abuseConfidenceScore;
                resultDiv.innerHTML = `<div style="padding:10px; border-left:4px solid #ff3333;">Risk: ${score}%</div>`;
            }).catch(() => { btn.disabled = false; });
        }

        function startOnDemandScan() {
            const url = document.getElementById('ondemandUrl').value.trim();
            if (!url) return;
            document.getElementById('scanResults').innerHTML = 'Scanning...';
            fetch('/cgi-bin/on_demand_scan.py', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: url })
            }).then(res => res.json()).then(data => {
                document.getElementById('scanResults').innerHTML = JSON.stringify(data);
            });
        }

        function refreshNewsFeed() {
            fetch('/cgi-bin/refresh_news.py', {method: 'POST'}).then(() => location.reload());
        }

        // Initialize News
        fetch('news_feed.json').then(res => res.json()).then(data => {
            allArticles = data.articles || [];
            renderNews(allArticles);
        }).catch(() => { document.getElementById('news-feed-container').innerHTML = 'Feed error'; });

        function renderNews(articles) {
            const container = document.getElementById('news-feed-container');
            let html = '';
            articles.forEach(a => {
                html += `<div style="margin-bottom:10px; border-bottom:1px solid #333;">
                    <a href="${a.link}" target="_blank">${a.title}</a></div>`;
            });
            container.innerHTML = html;
        }
        </script>
"""

# We look for the start of the <script> and replace the entire mess
in_script = False
for line in lines:
    if '<script>' in line:
        in_script = True
        new_lines.append(fixed_js + '\n')
    if '</script>' in line:
        in_script = False
        continue
    if not in_script:
        new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)
