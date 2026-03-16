import json
import os
from datetime import datetime, timedelta
import asyncio

try:
    from telegram import Bot
    from telegram.error import TelegramError
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("[!] python-telegram-bot not installed")

try:
    from telegram_config import *
except ImportError:
    print("[!] telegram_config.py not found")
    TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
    ALERT_ON_DOWN = True
    ALERT_ON_UP_RECOVERY = True
    ALERT_ON_NEW_IOCS = True
    ALERT_ON_CHANGES = True
    ALERT_ON_UPTIME_DROP = True
    UPTIME_THRESHOLD = 80.0
    ALERT_COOLDOWN_MINUTES = 15

ALERT_HISTORY_FILE = "/var/www/html/alert_history.json"

EMOJI_DOWN = "🔴"
EMOJI_UP = "🟢"
EMOJI_WARNING = "🟡"
EMOJI_IOC = "🚨"
EMOJI_CHANGE = "🔄"
EMOJI_INFO = "ℹ️"

def load_alert_history():
    try:
        with open(ALERT_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'last_alerts': {}, 'all_alerts': []}

def save_alert_history(history):
    try:
        with open(ALERT_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"[!] Failed to save alert history: {e}")

def should_send_alert(alert_type, target_name):
    history = load_alert_history()
    alert_key = f"{alert_type}_{target_name}"
    last_alerts = history.get('last_alerts', {})
    
    if alert_key in last_alerts:
        last_time = datetime.fromisoformat(last_alerts[alert_key])
        cooldown = timedelta(minutes=ALERT_COOLDOWN_MINUTES)
        if datetime.now() - last_time < cooldown:
            return False
    return True

def record_alert(alert_type, target_name, message):
    history = load_alert_history()
    alert_key = f"{alert_type}_{target_name}"
    history['last_alerts'][alert_key] = datetime.now().isoformat()
    
    history['all_alerts'].append({
        'timestamp': datetime.now().isoformat(),
        'type': alert_type,
        'target': target_name,
        'message': message
    })
    history['all_alerts'] = history['all_alerts'][-100:]
    save_alert_history(history)

async def _send_message_async(message):
    """Internal async message sender"""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )


# IOC History Management
IOC_HISTORY_FILE = '/var/www/html/ioc_history.json'

def load_ioc_history():
    """Load previously reported IOCs"""
    try:
        with open(IOC_HISTORY_FILE, 'r') as f:
            data = json.load(f)
            # Convert lists back to sets
            return {
                'bitcoin': set(data['reported_iocs'].get('bitcoin', [])),
                'emails': set(data['reported_iocs'].get('emails', [])),
                'pgp': set(data['reported_iocs'].get('pgp', [])),
                'ipv4': set(data['reported_iocs'].get('ipv4', [])),
                'domains': set(data['reported_iocs'].get('domains', []))
            }
    except:
        return {'bitcoin': set(), 'emails': set(), 'pgp': set(), 'ipv4': set(), 'domains': set()}

def save_ioc_history(history):
    """Save reported IOCs"""
    try:
        json_data = {
            'reported_iocs': {
                'bitcoin': list(history['bitcoin']),
                'emails': list(history['emails']),
                'pgp': list(history['pgp']),
                'ipv4': list(history['ipv4']),
                'domains': list(history['domains'])
            }
        }
        with open(IOC_HISTORY_FILE, 'w') as f:
            json.dump(json_data, f, indent=2)
    except Exception as e:
        print(f"[!] Failed to save IOC history: {e}")

def check_new_iocs(current_iocs):
    """Check if IOCs are truly new"""
    history = load_ioc_history()
    new_iocs = {
        'bitcoin': [],
        'emails': [],
        'pgp': [],
        'ipv4': [],
        'domains': []
    }
    
    # Check Bitcoin addresses
    for btc in current_iocs.get('bitcoin', []):
        if btc not in history['bitcoin']:
            new_iocs['bitcoin'].append(btc)
            history['bitcoin'].add(btc)
    
    # Check emails
    for email in current_iocs.get('emails', []):
        if email not in history['emails']:
            new_iocs['emails'].append(email)
            history['emails'].add(email)
    
    # Save updated history
    if any(new_iocs.values()):
        save_ioc_history(history)
    
    return new_iocs


def send_telegram_message(message):
    """Synchronous wrapper for sending Telegram messages"""
    if not TELEGRAM_AVAILABLE:
        print("[!] Telegram module not available")
        return False
    
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[!] Configure telegram_config.py first")
        return False
    
    try:
        # Run the async function synchronously
        asyncio.run(_send_message_async(message))
        return True
    except Exception as e:
        print(f"[!] Telegram error: {e}")
        return False

def alert_target_down(target_name, target_url, error_message):
    if not ALERT_ON_DOWN or not should_send_alert('down', target_name):
        return
    
    message = f"""
{EMOJI_DOWN} <b>TARGET DOWN ALERT</b>

<b>Target:</b> {target_name}
<b>URL:</b> <code>{target_url}</code>
<b>Status:</b> OFFLINE
<b>Error:</b> {error_message}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if send_telegram_message(message):
        record_alert('down', target_name, f"DOWN: {error_message}")
        print(f"    [TELEGRAM] Alert sent: TARGET DOWN")

def alert_target_recovery(target_name, target_url):
    if not ALERT_ON_UP_RECOVERY or not should_send_alert('recovery', target_name):
        return
    
    message = f"""
{EMOJI_UP} <b>TARGET RECOVERY ALERT</b>

<b>Target:</b> {target_name}
<b>URL:</b> <code>{target_url}</code>
<b>Status:</b> BACK ONLINE
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if send_telegram_message(message):
        record_alert('recovery', target_name, "Recovered")
        print(f"    [TELEGRAM] Alert sent: TARGET RECOVERY")

def alert_new_iocs(target_name, ioc_summary):
    if not ALERT_ON_NEW_IOCS or not should_send_alert('iocs', target_name):
        return
    
    details = []
    if ioc_summary.get('emails'): 
        details.append(f"📧 Emails: {len(ioc_summary['emails'])}")
    if ioc_summary.get('bitcoin'): 
        details.append(f"₿ Bitcoin: {len(ioc_summary['bitcoin'])}")
    if ioc_summary.get('pgp'): 
        details.append(f"🔐 PGP Keys: {len(ioc_summary['pgp'])}")
    
    if not details:
        return
    
    message = f"""
{EMOJI_IOC} <b>NEW IOCs DISCOVERED</b>

<b>Target:</b> {target_name}
<b>Indicators Found:</b>
{chr(10).join(details)}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if send_telegram_message(message):
        record_alert('iocs', target_name, f"IOCs: {', '.join(details)}")
        print(f"    [TELEGRAM] Alert sent: NEW IOCs")

def alert_content_change(target_name, target_url, change_type):
    if not ALERT_ON_CHANGES or not should_send_alert('change', target_name):
        return
    
    message = f"""
{EMOJI_CHANGE} <b>CHANGE DETECTED</b>

<b>Target:</b> {target_name}
<b>URL:</b> <code>{target_url}</code>
<b>Change Type:</b> {change_type.upper()}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if send_telegram_message(message):
        record_alert('change', target_name, f"Changed: {change_type}")
        print(f"    [TELEGRAM] Alert sent: CHANGE DETECTED")

def alert_uptime_drop(target_name, current_uptime):
    if not ALERT_ON_UPTIME_DROP or current_uptime >= UPTIME_THRESHOLD:
        return
    if not should_send_alert('uptime', target_name):
        return
    
    message = f"""
{EMOJI_WARNING} <b>LOW UPTIME ALERT</b>

<b>Target:</b> {target_name}
<b>24h Uptime:</b> {current_uptime}%
<b>Threshold:</b> {UPTIME_THRESHOLD}%
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if send_telegram_message(message):
        record_alert('uptime', target_name, f"Low uptime: {current_uptime}%")
        print(f"    [TELEGRAM] Alert sent: LOW UPTIME")

def send_scan_summary(summary_data):
    """Send scan completion summary"""
    message = f"""
{EMOJI_INFO} <b>Scan Completed</b>

<b>Targets Scanned:</b> {summary_data.get('total_targets', 0)}
<b>UP:</b> {summary_data.get('up_targets', 0)} | <b>DOWN:</b> {summary_data.get('down_targets', 0)}
<b>IOCs Found:</b> {summary_data.get('total_iocs', 0)}
<b>Changes:</b> {summary_data.get('changes_detected', 0)}
<b>Avg Response:</b> {summary_data.get('avg_latency', 0)}s

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    send_telegram_message(message)
    print(f"    [TELEGRAM] Scan summary sent")

def test_telegram_connection():
    """Test Telegram bot connection"""
    message = f"""
{EMOJI_UP} <b>Telegram Bot Connected!</b>

Your Dark Web Observatory alert system is now active.

<b>Alerts Enabled:</b>
• Target DOWN: {'✅' if ALERT_ON_DOWN else '❌'}
• Target Recovery: {'✅' if ALERT_ON_UP_RECOVERY else '❌'}
• New IOCs: {'✅' if ALERT_ON_NEW_IOCS else '❌'}
• Content Changes: {'✅' if ALERT_ON_CHANGES else '❌'}
• Low Uptime: {'✅' if ALERT_ON_UPTIME_DROP else '❌'}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return send_telegram_message(message)

