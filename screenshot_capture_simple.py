import os
import time
import json
from datetime import datetime
import subprocess

# Configuration
SCREENSHOT_DIR = "/var/www/html/screenshots"
SCREENSHOT_HISTORY = "/var/www/html/screenshot_history.json"
SCREENSHOT_GALLERY = "/var/www/html/screenshot_gallery.html"

# Create directories
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def sanitize_filename(name):
    """Create safe filename"""
    import re
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name).lower()

def capture_screenshot_cutycapt(target_name, url):
    """Capture screenshot using cutycapt (simple webkit screenshotter)"""
    try:
        print(f"  [*] Capturing screenshot: {target_name}")
        print(f"    [DEBUG] URL: {url}")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = sanitize_filename(target_name)
        filename = f"{safe_name}_{timestamp}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        print(f"    [DEBUG] Output file: {filepath}")
        
        # Use cutycapt with Tor proxy
        cmd = [
            'cutycapt',
            f'--url={url}',
            f'--out={filepath}',
            '--delay=5000',  # Wait 5 seconds for page load
            '--max-wait=60000',  # Max wait 60 seconds
            '--proxy=127.0.0.1:9050',
            '--proxy-type=socks5'
        ]
        
        print(f"    [DEBUG] Command: {' '.join(cmd)}")
        
        # Set environment for cutycapt
        env = os.environ.copy()
        env['XDG_RUNTIME_DIR'] = '/tmp/runtime-osint_lab'
        
        result = subprocess.run(cmd, capture_output=True, timeout=90, env=env)
        
        # Debug output
        print(f"    [DEBUG] Return code: {result.returncode}")
        if result.stdout:
            print(f"    [DEBUG] STDOUT: {result.stdout.decode()}")
        if result.stderr:
            print(f"    [DEBUG] STDERR: {result.stderr.decode()}")
        print(f"    [DEBUG] File exists: {os.path.exists(filepath)}")
        if os.path.exists(filepath):
            print(f"    [DEBUG] File size: {os.path.getsize(filepath)} bytes")
        
        if result.returncode == 0 and os.path.exists(filepath):
            filesize = os.path.getsize(filepath)
            print(f"    [+] Screenshot saved: {filename} ({filesize} bytes)")
            
            return {
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'filesize': filesize
            }
        else:
            error_msg = result.stderr.decode() if result.stderr else "Unknown error"
            print(f"    [!] Screenshot failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'url': url
            }
        
    except subprocess.TimeoutExpired:
        print(f"    [!] Screenshot timeout (>90s)")
        return {
            'success': False,
            'error': 'Timeout exceeded',
            'timestamp': datetime.now().isoformat(),
            'url': url
        }
    except Exception as e:
        print(f"    [!] Failed to capture screenshot: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'url': url
        }

def load_screenshot_history():
    """Load screenshot history"""
    try:
        with open(SCREENSHOT_HISTORY, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_screenshot_history(history):
    """Save screenshot history"""
    try:
        with open(SCREENSHOT_HISTORY, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"[!] Failed to save screenshot history: {e}")

def update_screenshot_history(target_name, screenshot_info):
    """Update screenshot history for target"""
    history = load_screenshot_history()
    
    if target_name not in history:
        history[target_name] = {'screenshots': []}
    
    # Add new screenshot
    history[target_name]['screenshots'].append(screenshot_info)
    
    # Keep only last 10 screenshots per target
    history[target_name]['screenshots'] = history[target_name]['screenshots'][-10:]
    
    save_screenshot_history(history)

def generate_screenshot_gallery(history, timestamp):
    """Generate screenshot gallery HTML"""
    
    # Count total successful screenshots
    total_screenshots = sum(
        len([s for s in data.get('screenshots', []) if s.get('success')])
        for data in history.values()
    )
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Screenshot Gallery - Dark Web Observatory</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0d0d0d; color: #e0e0e0; padding: 20px; }}
            h1 {{ color: #00ff00; text-transform: uppercase; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            h2 {{ color: #ffa500; margin-top: 30px; border-bottom: 1px solid #444; padding-bottom: 8px; }}
            .back-link {{ color: #00aaff; text-decoration: none; }}
            .back-link:hover {{ text-decoration: underline; }}
            .info-box {{ background: #1a1a1a; padding: 15px; margin: 20px 0; border-left: 4px solid #00aaff; }}
            .target-section {{ background: #1a1a1a; padding: 20px; margin: 20px 0; border-left: 4px solid #00ff00; }}
            .target-title {{ color: #00ff00; font-size: 1.3em; margin-bottom: 15px; }}
            .screenshot-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
            .screenshot-card {{ background: #0a0a0a; border: 1px solid #333; padding: 10px; transition: transform 0.2s; }}
            .screenshot-card:hover {{ transform: scale(1.02); border-color: #00ff00; }}
            .screenshot-img {{ width: 100%; height: 200px; object-fit: cover; cursor: pointer; border: 1px solid #222; }}
            .screenshot-info {{ margin-top: 10px; font-size: 0.85em; }}
            .screenshot-time {{ color: #888; }}
            .screenshot-size {{ color: #00aaff; }}
            .lightbox {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 1000; cursor: pointer; }}
            .lightbox-content {{ position: relative; max-width: 90%; max-height: 90%; margin: 2% auto; text-align: center; }}
            .lightbox-img {{ max-width: 100%; max-height: 90vh; border: 2px solid #00ff00; }}
            .lightbox-close {{ position: fixed; top: 20px; right: 40px; color: #fff; font-size: 40px; cursor: pointer; z-index: 1001; }}
            .no-screenshots {{ color: #888; font-style: italic; padding: 20px; }}
        </style>
    </head>
    <body>
        <h1>📸 Screenshot Gallery</h1>
        <p><a href="index.html" class="back-link">&larr; Back to Dashboard</a> | Last Updated: {timestamp}</p>
        
        <div class="info-box">
            <strong>ℹ️ Screenshot Archive:</strong> Visual snapshots of deep-scanned targets. 
            Screenshots are captured every 6 hours for targets with deep scanning enabled. 
            Total archived: <strong>{total_screenshots} screenshots</strong>
        </div>
    """
    
    if total_screenshots == 0:
        html += """
        <div class="no-screenshots">
            📷 No screenshots captured yet. Run the screenshot capture module to populate this gallery.
        </div>
        """
    else:
        # Generate gallery for each target
        for target_name, data in sorted(history.items()):
            screenshots = data.get('screenshots', [])
            if not screenshots:
                continue
            
            # Filter only successful screenshots
            successful = [s for s in screenshots if s.get('success')]
            if not successful:
                continue
            
            html += f"""
        <div class="target-section">
            <div class="target-title">{target_name} ({len(successful)} screenshots)</div>
            <div class="screenshot-grid">
            """
            
            for idx, shot in enumerate(reversed(successful)):
                filesize_kb = shot.get('filesize', 0) // 1024
                timestamp_str = shot.get('timestamp', 'Unknown')[:19].replace('T', ' ')
                filename = shot.get('filename', 'unknown.png')
                
                html += f"""
                <div class="screenshot-card">
                    <img src="screenshots/{filename}" 
                         class="screenshot-img" 
                         onclick="openLightbox('screenshots/{filename}')"
                         alt="{target_name} screenshot"
                         title="Click to enlarge">
                    <div class="screenshot-info">
                        <div class="screenshot-time">📅 {timestamp_str}</div>
                        <div class="screenshot-size">💾 {filesize_kb} KB</div>
                    </div>
                </div>
                """
            
            html += """
            </div>
        </div>
            """
    
    html += """
        <div id="lightbox" class="lightbox" onclick="closeLightbox()">
            <span class="lightbox-close">&times;</span>
            <div class="lightbox-content">
                <img id="lightbox-img" class="lightbox-img" src="" alt="Full size screenshot">
            </div>
        </div>
        
        <p style="margin-top:50px; font-size: 0.8em; color: #555;">
            <i>Automated Threat Intelligence Sentinel | Screenshot Archive Module</i>
        </p>
        
        <script>
        function openLightbox(src) {
            document.getElementById('lightbox').style.display = 'block';
            document.getElementById('lightbox-img').src = src;
        }
        
        function closeLightbox() {
            document.getElementById('lightbox').style.display = 'none';
        }
        
        // Also close on ESC key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeLightbox();
            }
        });
        </script>
    </body>
    </html>
    """
    
    # Save gallery
    try:
        with open(SCREENSHOT_GALLERY, 'w') as f:
            f.write(html)
        print(f"[+] Screenshot gallery generated: {SCREENSHOT_GALLERY}")
    except Exception as e:
        print(f"[!] Failed to generate gallery: {e}")

def capture_all_screenshots(targets):
    """Capture screenshots for all targets"""
    
    print("[*] Starting screenshot capture session...")
    print(f"[*] XDG_RUNTIME_DIR set to: /tmp/runtime-osint_lab")
    
    history = load_screenshot_history()
    successful_count = 0
    failed_count = 0
    
    for target in targets:
        # Only capture screenshots for deep scan targets
        if not target.get('deep_scan', False):
            continue
        
        result = capture_screenshot_cutycapt(target['name'], target['url'])
        update_screenshot_history(target['name'], result)
        
        if result.get('success'):
            successful_count += 1
        else:
            failed_count += 1
        
        time.sleep(3)  # Pause between captures
    
    # Generate gallery
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    generate_screenshot_gallery(load_screenshot_history(), timestamp)
    
    print(f"\n[✓] Screenshot capture complete!")
    print(f"    Successful: {successful_count}")
    print(f"    Failed: {failed_count}")

if __name__ == "__main__":
    # Load targets from advanced_scanner.py
    import sys
    sys.path.insert(0, '/home/osint_lab/dark-monitor')
    from advanced_scanner import TARGETS
    
    capture_all_screenshots(TARGETS)

