#!/usr/bin/env python3
import json

# Read current IOC database
try:
    with open('/var/www/html/ioc_database.json', 'r') as f:
        current_iocs = json.load(f)
except:
    current_iocs = {'bitcoin_addresses': [], 'emails': []}

# Create IOC history tracker
ioc_history = {
    'reported_iocs': {
        'bitcoin': set(),
        'emails': set(),
        'pgp': set(),
        'ipv4': set(),
        'domains': set()
    }
}

# Populate from existing IOCs
for btc_entry in current_iocs.get('bitcoin_addresses', []):
    ioc_history['reported_iocs']['bitcoin'].add(btc_entry['ioc'])

for email_entry in current_iocs.get('emails', []):
    ioc_history['reported_iocs']['emails'].add(email_entry['ioc'])

# Save IOC history
with open('/var/www/html/ioc_history.json', 'w') as f:
    # Convert sets to lists for JSON
    json_data = {
        'reported_iocs': {
            'bitcoin': list(ioc_history['reported_iocs']['bitcoin']),
            'emails': list(ioc_history['reported_iocs']['emails']),
            'pgp': list(ioc_history['reported_iocs']['pgp']),
            'ipv4': list(ioc_history['reported_iocs']['ipv4']),
            'domains': list(ioc_history['reported_iocs']['domains'])
        }
    }
    json.dump(json_data, f, indent=2)

print("[+] IOC history initialized")
