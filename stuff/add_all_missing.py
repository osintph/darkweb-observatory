#!/usr/bin/env python3
import re

# Read the file
with open('advanced_scanner.py', 'r') as f:
    content = f.read()

# The code to insert - all three features
insert_code = '''
    # Generate alert statistics dashboard
    try:
        from generate_alert_stats import generate_alert_statistics
        generate_alert_statistics()
    except Exception as e:
        print(f"[!] Failed to generate alert statistics: {e}")
    
    # Generate historical trends dashboard
    try:
        from generate_historical_trends import generate_historical_trends
        generate_historical_trends()
    except Exception as e:
        print(f"[!] Failed to generate historical trends: {e}")
    
    # Generate news feed
    try:
        from news_feed_aggregator import aggregate_news_feed
        aggregate_news_feed()
    except Exception as e:
        print(f"[!] Failed to generate news feed: {e}")

'''

# Find the position to insert (right before "if __name__")
pattern = r'(\n    print\(f"\\n\[✓\] Scan complete.*?\n\n)(if __name__ == "__main__":)'
replacement = r'\1' + insert_code + r'\2'

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('advanced_scanner.py', 'w') as f:
    f.write(new_content)

print("Added alert statistics, historical trends, AND news feed generation!")
