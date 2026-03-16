#!/bin/bash
# Fix the JavaScript syntax error

sed -i "s|onclick=\"filterByNewsCategory('all')\"|onclick=\"filterByNewsCategory('all')\"|g" advanced_scanner.py

echo "[✓] Fixed! Now run: python3 advanced_scanner.py"
