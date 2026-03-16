import os

file_path = 'advanced_scanner.py'
with open(file_path, 'r') as f:
    lines = f.readlines()

crawl_js = r"""
        function startOnDemandScan() {
            const url = document.getElementById('ondemandUrl').value.trim();
            const resultsDiv = document.getElementById('scanResults');
            if (!url) return;
            resultsDiv.innerHTML = '<p style="color:#ffa500;">🔄 Crawling and Extracting Deep Web Intel...</p>';
            
            fetch('/cgi-bin/on_demand_scan.py', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: url })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) { resultsDiv.innerHTML = 'Error: ' + data.error; return; }
                
                const main = data.main_page;
                resultsDiv.innerHTML = `
                    <div class="scan-result-card" style="border-left-color: #00aaff;">
                        <h3 style="color:#00ff00;">✓ Target: ${main.title}</h3>
                        <p style="color:#888; font-size:0.85em;">Crawl depth complete. Pages analyzed: ${data.crawled_pages.length + 1}</p>
                        
                        <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:10px; margin:15px 0;">
                            <div style="background:#0d0d0d; padding:10px; border:1px solid #333;">
                                <div style="color:#888; font-size:0.7em;">TOTAL UNIQUE EMAILS</div>
                                <div style="color:#ff3333; font-size:1.2em; font-weight:bold;">${data.total_iocs.emails.length}</div>
                            </div>
                            <div style="background:#0d0d0d; padding:10px; border:1px solid #333;">
                                <div style="color:#888; font-size:0.7em;">TOTAL UNIQUE BITCOIN</div>
                                <div style="color:#ffa500; font-size:1.2em; font-weight:bold;">${data.total_iocs.btc.length}</div>
                            </div>
                        </div>

                        <details style="cursor:pointer; color:#00aaff; font-size:0.9em;">
                            <summary>View Crawled URLs (${data.crawled_pages.length})</summary>
                            <div style="background:#050505; padding:10px; margin-top:5px; max-height:150px; overflow-y:auto;">
                                ${data.crawled_pages.map(p => `<div style="color:#777; font-size:0.8em; margin-bottom:4px;">→ ${p.url}</div>`).join('')}
                            </div>
                        </details>
                    </div>`;
            });
        }
"""

new_content = []
in_script = False
for line in lines:
    if 'function startOnDemandScan()' in line:
        in_script = True
        new_content.append(crawl_js + '\n')
    if in_script and '}' in line: # This is a simple closer logic; might need manual check if JS is complex
        # We look for the end of the previous function to stop skipping
        if line.strip() == '}': 
            in_script = False
            continue
    if not in_script:
        new_content.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_content)
