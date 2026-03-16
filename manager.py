from flask import Flask, render_template_string, request, redirect, url_for, flash, session
import json
import os
import subprocess
from functools import wraps
import hashlib
import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate random secret key

# ============== PASSWORD CONFIGURATION ==============
# Change these credentials!
USERNAME = 'sigmund'
PASSWORD_HASH = 'e74fd4623ac0e5c92892d2fc4ea4b690024aa9a25198a3d16fa39d69fe8980b1'

# To generate a new password hash, run:
# python3 -c "import hashlib; print(hashlib.sha256('your_password'.encode()).hexdigest())"
# ===================================================

SCANNER_FILE = '/home/osint_lab/dark-monitor/advanced_scanner.py'
BACKUP_DIR = '/home/osint_lab/dark-monitor/backups'

# Create backup directory
os.makedirs(BACKUP_DIR, exist_ok=True)

def check_password(username, password):
    """Verify username and password"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return username == USERNAME and password_hash == PASSWORD_HASH

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def read_targets():
    """Extract TARGETS list from advanced_scanner.py"""
    with open(SCANNER_FILE, 'r') as f:
        content = f.read()
    
    # Find TARGETS array
    start = content.find('TARGETS = [')
    end = content.find(']', start) + 1
    targets_str = content[start:end]
    
    # Parse it (simple eval - in production use ast.literal_eval)
    targets = eval(targets_str.replace('TARGETS = ', ''))
    return targets, content

def write_targets(targets, original_content):
    """Write updated TARGETS back to advanced_scanner.py"""
    # Backup first
    backup_name = f"{BACKUP_DIR}/advanced_scanner_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    with open(backup_name, 'w') as f:
        f.write(original_content)
    
    # Generate new TARGETS string
    targets_str = "TARGETS = [\n"
    for target in targets:
        targets_str += "    {\n"
        targets_str += f'        "name": "{target["name"]}",\n'
        targets_str += f'        "url": "{target["url"]}",\n'
        targets_str += f'        "category": "{target["category"]}",\n'
        targets_str += f'        "deep_scan": {str(target["deep_scan"])}\n'
        targets_str += "    },\n"
    targets_str += "]\n"
    
    # Replace in original content
    start = original_content.find('TARGETS = [')
    end = original_content.find(']', start) + 1
    new_content = original_content[:start] + targets_str + original_content[end+1:]
    
    # Write back
    with open(SCANNER_FILE, 'w') as f:
        f.write(new_content)

# Login Page Template
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dark Web Monitor - Login</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0d0d0d;
            color: #e0e0e0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-container {
            background: #1a1a1a;
            padding: 40px;
            border: 2px solid #00ff00;
            max-width: 400px;
            width: 100%;
        }
        h1 {
            color: #00ff00;
            text-transform: uppercase;
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.5em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            color: #888;
            text-transform: uppercase;
            font-size: 0.9em;
            margin-bottom: 8px;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            background: #0a0a0a;
            border: 1px solid #333;
            color: #e0e0e0;
            padding: 12px;
            font-family: 'Courier New', monospace;
            font-size: 1em;
            box-sizing: border-box;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            border-color: #00ff00;
            outline: none;
        }
        button {
            width: 100%;
            background: #003300;
            color: #00ff00;
            border: 1px solid #00ff00;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 1em;
            cursor: pointer;
            text-transform: uppercase;
            margin-top: 10px;
        }
        button:hover {
            background: #004400;
        }
        .alert {
            background: #3a1a1a;
            color: #ff3333;
            border: 1px solid #ff3333;
            padding: 12px;
            margin-bottom: 20px;
            text-align: center;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #555;
            font-size: 0.85em;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔒 Secure Access</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit">Login</button>
        </form>
        
        <div class="footer">
            Dark Web Observatory<br>Target Management System
        </div>
    </div>
</body>
</html>
'''

# Main Dashboard Template
TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dark Web Monitor - Target Manager</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0d0d0d;
            color: #e0e0e0;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #00ff00;
            text-transform: uppercase;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        h2 {
            color: #ffa500;
            margin-top: 30px;
        }
        .nav-links {
            margin: 20px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .nav-links a {
            color: #00aaff;
            text-decoration: none;
            margin-right: 20px;
        }
        .nav-links a:hover {
            text-decoration: underline;
        }
        .logout-btn {
            background: #330000;
            color: #ff3333;
            border: 1px solid #ff3333;
            padding: 8px 20px;
            text-decoration: none;
            display: inline-block;
            font-size: 0.9em;
        }
        .logout-btn:hover {
            background: #440000;
        }
        .user-info {
            color: #888;
            font-size: 0.9em;
        }
        .form-container {
            background: #1a1a1a;
            padding: 25px;
            border-left: 4px solid #00ff00;
            margin: 20px 0;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            color: #888;
            text-transform: uppercase;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        input[type="text"], select {
            width: 100%;
            background: #0a0a0a;
            border: 1px solid #333;
            color: #e0e0e0;
            padding: 10px;
            font-family: 'Courier New', monospace;
            font-size: 1em;
        }
        input[type="text"]:focus, select:focus {
            border-color: #00ff00;
            outline: none;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            margin-top: 10px;
        }
        .checkbox-group input[type="checkbox"] {
            margin-right: 10px;
            width: 20px;
            height: 20px;
        }
        .checkbox-group label {
            margin: 0;
            display: inline;
        }
        button {
            background: #003300;
            color: #00ff00;
            border: 1px solid #00ff00;
            padding: 12px 30px;
            font-family: 'Courier New', monospace;
            font-size: 1em;
            cursor: pointer;
            text-transform: uppercase;
            margin-top: 15px;
        }
        button:hover {
            background: #004400;
        }
        .targets-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .targets-table th, .targets-table td {
            border: 1px solid #333;
            padding: 12px;
            text-align: left;
        }
        .targets-table th {
            background: #1a1a1a;
            color: #fff;
            text-transform: uppercase;
        }
        .targets-table tr:nth-child(even) {
            background: #111;
        }
        .delete-btn {
            background: #330000;
            color: #ff3333;
            border: 1px solid #ff3333;
            padding: 5px 15px;
            font-size: 0.85em;
        }
        .delete-btn:hover {
            background: #440000;
        }
        .deep-scan-badge {
            background: #003300;
            color: #00ff00;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
        }
        .alert {
            background: #1a3a1a;
            color: #00ff00;
            border: 1px solid #00ff00;
            padding: 15px;
            margin: 20px 0;
        }
        .alert-error {
            background: #3a1a1a;
            color: #ff3333;
            border-color: #ff3333;
        }
        .category-badge {
            background: #0a0a0a;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            color: #888;
        }
    </style>
</head>
<body>
    <h1>Dark Web Observatory - Target Manager</h1>
    
    <div class="nav-links">
        <div>
            <a href="/">Manager Dashboard</a> |
            <a href="/index.html" target="_blank">View Live Dashboard →</a>
        </div>
        <div>
            <span class="user-info">Logged in as: {{ session.get('username') }}</span>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    </div>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="alert {% if category == 'error' %}alert-error{% endif %}">
                    {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <h2>Add New Target</h2>
    <div class="form-container">
        <form method="POST" action="/add">
            <div class="form-group">
                <label for="name">Target Name *</label>
                <input type="text" id="name" name="name" required placeholder="e.g., Example Forum">
            </div>
            
            <div class="form-group">
                <label for="url">Onion URL *</label>
                <input type="text" id="url" name="url" required placeholder="http://example...onion or https://example...onion">
            </div>
            
            <div class="form-group">
                <label for="category">Category *</label>
                <select id="category" name="category" required onchange="toggleCustomCategory()">
                    <option value="">-- Select Category --</option>
                    <option value="forums">Forums</option>
                    <option value="marketplace">Marketplace</option>
                    <option value="news">News</option>
                    <option value="social">Social</option>
                    <option value="government">Government</option>
                    <option value="search">Search</option>
                    <option value="ransomware">Ransomware</option>
                    <option value="leak_site">Leak Site</option>
                    <option value="custom">Other (Custom)</option>
                </select>
            </div>
            
            <div class="form-group" id="customCategoryGroup" style="display: none;">
                <label for="custom_category">Custom Category Name *</label>
                <input type="text" id="custom_category" name="custom_category" placeholder="e.g., phishing, crypters, botnets">
            </div>
            
            <div class="checkbox-group">
                <input type="checkbox" id="deep_scan" name="deep_scan" value="true">
                <label for="deep_scan">Enable Deep Scan (IOC extraction, reconnaissance)</label>
            </div>
            
            <button type="submit">Add Target</button>
        </form>
    </div>
    
    <h2>Current Targets ({{ targets|length }})</h2>
    <table class="targets-table">
        <thead>
            <tr>
                <th style="width: 15%">Name</th>
                <th style="width: 40%">Onion URL</th>
                <th style="width: 12%">Category</th>
                <th style="width: 15%">Deep Scan</th>
                <th style="width: 10%">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for target in targets %}
            <tr>
                <td>{{ target.name }}</td>
                <td style="font-size: 0.85em; color: #888;">{{ target.url }}</td>
                <td><span class="category-badge">{{ target.category }}</span></td>
                <td>
                    {% if target.deep_scan %}
                        <span class="deep-scan-badge">ENABLED</span>
                    {% else %}
                        <span style="color: #555;">Disabled</span>
                    {% endif %}
                </td>
                <td>
                    <form method="POST" action="/delete/{{ loop.index0 }}" style="display: inline;" 
                          onsubmit="return confirm('Delete {{ target.name }}?');">
                        <button type="submit" class="delete-btn">Delete</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <p style="margin-top: 50px; font-size: 0.8em; color: #555;">
        <i>Target Manager | Changes take effect on next scan cycle (within 15 minutes)</i>
    </p>
    
    <script>
    function toggleCustomCategory() {
        var select = document.getElementById('category');
        var customGroup = document.getElementById('customCategoryGroup');
        var customInput = document.getElementById('custom_category');
        
        if (select.value === 'custom') {
            customGroup.style.display = 'block';
            customInput.required = true;
        } else {
            customGroup.style.display = 'none';
            customInput.required = false;
            customInput.value = '';
        }
    }
    </script>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if check_password(username, password):
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    targets, _ = read_targets()
    return render_template_string(TEMPLATE, targets=targets, session=session)

@app.route('/add', methods=['POST'])
@login_required
def add_target():
    try:
        name = request.form.get('name', '').strip()
        url = request.form.get('url', '').strip()
        category = request.form.get('category', '').strip()
        custom_category = request.form.get('custom_category', '').strip()
        deep_scan = request.form.get('deep_scan') == 'true'
        
        # Handle custom category
        if category == 'custom':
            if not custom_category:
                flash('Please enter a custom category name!', 'error')
                return redirect(url_for('index'))
            category = custom_category.lower().replace(' ', '_')
        
        # Validation
        if not name or not url or not category:
            flash('All fields are required!', 'error')
            return redirect(url_for('index'))
        
        if '.onion' not in url:
            flash('URL must be a valid .onion address!', 'error')
            return redirect(url_for('index'))
        
        if not url.startswith('http://') and not url.startswith('https://'):
            flash('URL must start with http:// or https://', 'error')
            return redirect(url_for('index'))
        
        # Read current targets
        targets, original_content = read_targets()
        
        # Check for duplicates
        if any(t['url'] == url for t in targets):
            flash('This URL already exists in the target list!', 'error')
            return redirect(url_for('index'))
        
        # Add new target
        new_target = {
            'name': name,
            'url': url,
            'category': category,
            'deep_scan': deep_scan
        }
        targets.append(new_target)
        
        # Write back
        write_targets(targets, original_content)
        
        flash(f'Successfully added: {name} [{category}]', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/delete/<int:index>', methods=['POST'])
@login_required
def delete_target(index):
    try:
        targets, original_content = read_targets()
        
        if 0 <= index < len(targets):
            deleted_name = targets[index]['name']
            del targets[index]
            write_targets(targets, original_content)
            flash(f'Successfully deleted: {deleted_name}', 'success')
        else:
            flash('Invalid target index', 'error')
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Run on localhost only (access via SSH tunnel or configure for onion)
    app.run(host='127.0.0.1', port=5000, debug=False)

