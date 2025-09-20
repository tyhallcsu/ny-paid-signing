import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("SQLITE_PATH") or "./devices.db"

def main():
    existing = [
        # Replace with real Discord IDs (not names) when possible.
        {"discord_id": "123456789012345678", "discord_name": "sharmanhall#0001",
         "udid": "00008101-001579C40189003A", "product": "iPhone"},
    ]

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        for u in existing:
            c.execute("""INSERT OR IGNORE INTO purchases
                         (discord_id, discord_name, purchase_date, expires_date, slots_allowed, slots_used)
                         VALUES (?, ?, ?, ?, 1, 0)""",
                      (u["discord_id"], u["discord_name"], datetime.now(), datetime.now() + timedelta(days=365)))
            c.execute("""INSERT OR IGNORE INTO devices
                         (udid, discord_id, product, version, serial, device_name, registered_date, apple_registered)
                         VALUES (?, ?, ?, '', '', ?, ?, 1)""",
                      (u["udid"], u["discord_id"], u["product"], f"{u['discord_name']}'s {u['product']}", datetime.now()))
        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    main()
