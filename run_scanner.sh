#!/bin/bash
cd /home/osint_lab/dark-monitor
source venv/bin/activate
python advanced_scanner.py
python generate_alert_stats.py
python generate_historical_trends.py
python threat_feed_aggregator.py
deactivate

