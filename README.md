# Dark Web Observatory — Threat Intelligence Platform

A self-hosted dark web monitoring portal that scans `.onion` sites via Tor, tracks uptime history, extracts IOCs, and serves a card-based dashboard as a Tor Hidden Service. No ports opened on your router.

> **For educational, OSINT, and threat intelligence research use only.**

---

## Dashboard

- Card-based layout grouped by category with sidebar navigation
- Per-card uptime sparkline, latency, status history
- Risk indicators (🟢 low / 🟡 medium / 🔴 high)
- On-demand deep scan tool
- IP reputation check (AbuseIPDB)
- Live cybersecurity news feed (BleepingComputer, Krebs, THN, Dark Reading)
- Alert statistics and historical trend pages

## Target Sources

**Built-in seed list** — 36 curated targets across:
`news` `search` `social` `government` `privacy` `email` `index` `forums` `intel` `ransomware` `leak_site` `marketplace` `monitoring`

**Auto-fetched remote CTI feeds** (cached 24h, refreshed daily):
- [`alecmuffett/real-world-onion-sites`](https://github.com/alecmuffett/real-world-onion-sites) — legitimate sites with onion mirrors
- [`fastfire/deepdarkCTI`](https://github.com/fastfire/deepdarkCTI) — ransomware groups and threat actor infrastructure (ONLINE entries only, deduped by group name)

## Deep Scan

Targets with `deep_scan: true` get full IOC extraction on every scan:
- Email addresses
- Bitcoin/crypto wallet addresses
- Linked onion addresses
- Page content hash (change detection)
- Server headers
- Form count

## Quick Deploy (Fresh Ubuntu 22.04 / 24.04)

```bash
git clone https://github.com/osintph/dark-observatory.git
cd dark-onion-monitor
bash deploy.sh
```

That's it. The script handles everything — packages, Tor, Nginx, venv, first scan, cron.

## Manual Install

### 1. System packages

```bash
sudo apt update && sudo apt install -y tor nginx python3 python3-venv python3-pip ufw
```

### 2. Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.0.0/24 to any port 22   # adjust to your subnet
sudo ufw enable
```

### 3. Tor hidden service

Add to `/etc/tor/torrc`:
```
SocksPort 9050
HiddenServiceDir /var/lib/tor/onion_monitor/
HiddenServicePort 80 127.0.0.1:80
```

```bash
sudo systemctl restart tor
sudo cat /var/lib/tor/onion_monitor/hostname   # your .onion address
sudo chown -R $USER /var/www/html
```

### 4. Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. First scan

```bash
python advanced_scanner.py --fetch-remote
```

### 6. Cron (3x daily)

```bash
crontab -e
```

```
0 6,14,22 * * * /path/to/venv/bin/python /path/to/advanced_scanner.py >> /path/to/logs/cron.log 2>&1
0 3 * * *  /path/to/venv/bin/python /path/to/advanced_scanner.py --fetch-remote >> /path/to/logs/cron.log 2>&1
```

## Target Manager

`manager.py` is a Flask web UI for adding/removing targets without editing code.

```bash
source venv/bin/activate
python manager.py
# Access via SSH tunnel: ssh -L 5000:127.0.0.1:5000 user@yourserver
# Then open http://127.0.0.1:5000
```

Default credentials are set in `manager.py` — change them before use:
```python
USERNAME = 'your_username'
# Generate hash: python3 -c "import hashlib; print(hashlib.sha256('yourpassword'.encode()).hexdigest())"
PASSWORD_HASH = 'your_hash_here'
```

## CLI Flags

```
python advanced_scanner.py                # normal scan
python advanced_scanner.py --fetch-remote # force refresh remote CTI feeds
```

## Project Structure

```
dark-onion-monitor/
├── advanced_scanner.py      # main scanner + dashboard generator
├── remote_targets.py        # remote CTI feed fetcher (alecmuffett + deepdarkCTI)
├── manager.py               # Flask target manager UI
├── news_feed_aggregator.py  # RSS news aggregator
├── threat_feed_aggregator.py# abuse.ch threat feed aggregator
├── generate_alert_stats.py  # alert statistics page generator
├── generate_historical_trends.py
├── deploy.sh                # one-shot fresh-install deploy script
├── requirements.txt
├── config/
│   └── settings.json        # tunable parameters
├── data/                    # runtime data (gitignored)
└── logs/                    # scan logs (gitignored)
```

## OPSEC

- All connections are outbound through Tor — no inbound ports required
- Never run as root
- `data/`, `logs/`, `config/targets.json`, and `config/remote_cache.json` are gitignored — they may contain sensitive intelligence
- Manager runs on `127.0.0.1:5000` only — access via SSH tunnel, never expose externally

## Legal

For defensive OSINT and threat intelligence research only. Follow your local laws. Do not interact with or purchase from any dark web marketplace.

## Credits

- [alecmuffett/real-world-onion-sites](https://github.com/alecmuffett/real-world-onion-sites)
- [fastfire/deepdarkCTI](https://github.com/fastfire/deepdarkCTI)
- [ransomware.live](https://www.ransomware.live)
- Original concept: [Sigmund Brandstaetter](https://medium.com/@sigmund.brandstaetter)
