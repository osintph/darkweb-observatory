with open('advanced_scanner.py', 'r') as f:
    lines = f.readlines()

# Find and fix the last_changed display logic (around line 1593-1598)
for i in range(len(lines)):
    if 'if change_info.get(' in lines[i] and i > 1590 and i < 1600:
        # Found it - replace the next 5 lines
        lines[i] = '        # Last changed - show actual timestamp from history\n'
        lines[i+1] = '        last_changed_val = result.get("last_changed", "")\n'
        lines[i+2] = '        if last_changed_val and last_changed_val != "":\n'
        lines[i+3] = '            last_changed_cell = f\'<span style="color: #ffa500;">{last_changed_val}</span>\'\n'
        lines[i+4] = '        else:\n'
        lines[i+5] = '            last_changed_cell = \'<span style="color: #555;">-</span>\'\n'
        break

with open('advanced_scanner.py', 'w') as f:
    f.writelines(lines)

print("[+] Fixed last_changed to use actual timestamp from change history")
