with open('advanced_scanner.py', 'r') as f:
    content = f.read()

# Find the section where we build last_changed_cell (around line 1593-1598)
# Replace the whole block with proper logic
old_block = '''        # Last changed - show actual timestamp from history
        last_changed_val = result.get("last_changed", "")
        if last_changed_val and last_changed_val != "":
            last_changed_cell = f'<span style="color: #ffa500;">{last_changed_val}</span>'
        else:
            last_changed_cell = '<span style="color: #555;">-</span>'''

new_block = '''        # Last changed - get from change history
        history = load_change_history()
        target_name = result.get('target', '')
        if target_name in history and history[target_name].get('last_changed'):
            last_changed_cell = f'<span style="color: #ffa500;">{history[target_name]["last_changed"]}</span>'
        else:
            last_changed_cell = '<span style="color: #555;">Never</span>'''

content = content.replace(old_block, new_block)

with open('advanced_scanner.py', 'w') as f:
    f.write(content)

print("[+] Fixed last_changed to read from change history")
