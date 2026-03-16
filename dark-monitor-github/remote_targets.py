# -*- coding: utf-8 -*-
"""
remote_targets.py
=================
Fetches and merges .onion target lists from two remote CTI repos:

  1. alecmuffett/real-world-onion-sites  -- legitimate/research sites
  2. fastfire/deepdarkCTI                -- ransomware groups (ONLINE-only)

Caps prevent importing hundreds of dead links that would bloat scan time:
  - alecmuffett : top ALEC_CAP unique URLs
  - deepdarkCTI : ONLINE-status entries only, capped at CTI_CAP

Drop this file into ~/dark-monitor/ alongside advanced_scanner.py.
"""

import json
import os
import re
import datetime
import requests

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
CACHE_FILE = os.path.join(CONFIG_DIR, "remote_cache.json")
CACHE_HOURS = 24

# No caps -- scan everything
ALEC_CAP = 9999
CTI_CAP  = 9999

SOURCES = {
    "alecmuffett": "https://raw.githubusercontent.com/alecmuffett/real-world-onion-sites/master/README.md",
    "deepdarkCTI": "https://raw.githubusercontent.com/fastfire/deepdarkCTI/main/ransomware_gang.md",
}

ONION_RE   = re.compile(r'https?://[a-z2-7]{56}\.onion[^\s\)\"\'\<\>\|]*', re.I)
CTI_ROW_RE = re.compile(
    r'\|\s*\[([^\]]+)\]\((http[^\)]+\.onion[^\)]*)\)\s*\|\s*(ONLINE|OFFLINE)', re.I
)


def _cache_age_hours():
    if not os.path.exists(CACHE_FILE):
        return 9999
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
    return (datetime.datetime.now() - mtime).total_seconds() / 3600


def _fetch(url):
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "curl/8.0"})
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  [!] Remote fetch failed: {e}")
        return None


def _parse_alecmuffett(text):
    """
    The alecmuffett README is a markdown table where each site row can have
    multiple mirror URL columns under the same heading — causing duplicate
    names. Fix: one entry per unique site name (first URL wins).
    """
    results   = []
    seen_urls = set()
    seen_names= set()           # dedupe by name — one card per real-world site
    current_section = "Unknown"

    for line in text.splitlines():
        if len(results) >= ALEC_CAP:
            break

        # Track the section heading (## BBC, ## Facebook, etc.)
        h = re.match(r'^#{1,3}\s+(.+)', line)
        if h:
            current_section = h.group(1).strip()[:50]
            # Reset per-section URL tracking so we pick the first URL per section
            continue

        urls_in_line = ONION_RE.findall(line)
        if not urls_in_line:
            continue

        # Pick first unseen URL in this line
        for url in urls_in_line:
            url = url.rstrip(".,;)|\"'")
            if url in seen_urls:
                continue
            # Skip if we already have an entry for this section name
            if current_section in seen_names:
                seen_urls.add(url)   # still mark URL seen to avoid it being re-added later
                continue
            seen_urls.add(url)
            seen_names.add(current_section)
            results.append({
                "name":      current_section,
                "url":       url,
                "category":  "news",
                "deep_scan": False,
                "risk":      "low",
                "source":    "alecmuffett/real-world-onion-sites",
            })
            break   # only first URL per section

    return results


def _parse_deepdarkCTI(text):
    """
    Parse fastfire/deepdarkCTI ransomware_gang.md.
    ONLINE entries only. One entry per group name (first URL wins).
    Hard-capped at CTI_CAP.
    """
    results    = []
    seen_urls  = set()
    seen_names = set()

    for m in CTI_ROW_RE.finditer(text):
        if len(results) >= CTI_CAP:
            break
        name   = m.group(1).strip()[:60]
        url    = m.group(2).strip().rstrip(".,;)|\"'")
        status = m.group(3).upper()

        if status != "ONLINE":
            continue
        if not re.search(r'[a-z2-7]{56}\.onion', url, re.I):
            continue
        if url in seen_urls:
            continue
        # Skip mirror entries for already-seen group names
        if name in seen_names:
            seen_urls.add(url)
            continue

        seen_urls.add(url)
        seen_names.add(name)
        results.append({
            "name":         name,
            "url":          url,
            "category":     "ransomware",
            "deep_scan":    True,
            "risk":         "high",
            "known_status": status,
            "source":       "fastfire/deepdarkCTI",
        })

    return results


def fetch_and_merge(force=False):
    if not force and _cache_age_hours() < CACHE_HOURS:
        print("  [*] Remote cache fresh -- skipping fetch.")
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as f:
                return json.load(f)
        return []

    remote = []

    print("  [*] Fetching alecmuffett/real-world-onion-sites ...")
    text = _fetch(SOURCES["alecmuffett"])
    if text:
        parsed = _parse_alecmuffett(text)
        print(f"      -> {len(parsed)} URLs (cap={ALEC_CAP})")
        remote.extend(parsed)

    print("  [*] Fetching fastfire/deepdarkCTI ...")
    text = _fetch(SOURCES["deepdarkCTI"])
    if text:
        parsed = _parse_deepdarkCTI(text)
        print(f"      -> {len(parsed)} ONLINE entries (cap={CTI_CAP})")
        remote.extend(parsed)

    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(remote, f, indent=2)
    print(f"  [+] Remote fetch done: {len(remote)} targets cached.")
    return remote


def merge_with_local(local_targets, remote_targets):
    local_urls = {t["url"] for t in local_targets}
    merged, added = list(local_targets), 0
    for t in remote_targets:
        if t["url"] not in local_urls:
            merged.append(t)
            local_urls.add(t["url"])
            added += 1
    print(f"  [+] {len(local_targets)} local + {added} remote = {len(merged)} total")
    return merged
