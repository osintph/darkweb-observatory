from telegram_alerts import test_telegram_connection

if test_telegram_connection():
    print("[✓] SUCCESS!")
else:
    print("[✗] FAILED")

