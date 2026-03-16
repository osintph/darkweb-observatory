#!/usr/bin/env python3
import re

with open('advanced_scanner.py', 'r') as f:
    lines = f.readlines()

# Find the calculate_page_hash function
for i, line in enumerate(lines):
    if 'def calculate_page_hash(content):' in line:
        # Replace the function with a version that strips dynamic content
        lines[i] = '''def calculate_page_hash(content):
    """Calculate page hash after removing dynamic elements"""
    # Remove timestamps, dates, counters that change frequently
    content = re.sub(r'\\d{4}-\\d{2}-\\d{2}[T\\s]\\d{2}:\\d{2}:\\d{2}', 'TIMESTAMP', content)
    content = re.sub(r'\\d{4}-\\d{2}-\\d{2}', 'DATE', content)
    content = re.sub(r'Last (updated|seen|checked|scan):?\\s*[^<]+', 'LAST_UPDATE', content, flags=re.IGNORECASE)
    content = re.sub(r'\\b\\d+\\s+(views?|visitors?|online|members?)\\b', 'COUNTER', content, flags=re.IGNORECASE)
    content = re.sub(r'\\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s+\\d{1,2},?\\s+\\d{4}', 'DATE', content)
    
'''
        break

with open('advanced_scanner.py', 'w') as f:
    f.writelines(lines)

print("[+] Improved change detection - now ignores dynamic content")
