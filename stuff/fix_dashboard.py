import re

with open('advanced_scanner.py', 'r') as f:
    lines = f.readlines()

# Find the last_changed_cell block (around line 1590-1605)
for i in range(len(lines)):
    if 'last_changed_cell' in lines[i] and 'result.get("last_changed"' in lines[i]:
        # Replace the entire block with working code
        lines[i] = '        # Last changed - use change_info field\\n'
        lines[i+1] = '        change_info = result.get("change_info", {})\\n'
        lines[i+2] = '        last_changed_val = change_info.get("last_changed", "Never")\\n'
        lines[i+3] = '        if last_changed_val and last_changed_val != "Never":\\n'
        lines[i+4] = '            last_changed_cell = f\'<span style="color: #ffa500;">{last_changed_val[:19]}</span>\'\\n'
        lines[i+5] = '        else:\\n'
        lines[i+6] = '            last_changed_cell = \'<span style="color: #555;">Never</span>\'\\n'
        print("[+] Fixed last_changed_cell logic")
        break

with open('advanced_scanner.py', 'w') as f:
    f.writelines(lines)
