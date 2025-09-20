import sqlite3
from datetime import datetime
from flask import current_app

DDL_PURCHASES = """
CREATE TABLE IF NOT EXISTS purchases (
  discord_id TEXT PRIMARY KEY,
  discord_name TEXT,
  purchase_date TIMESTAMP,
  expires_date TIMESTAMP,
  slots_allowed INTEGER DEFAULT 1,
  slots_used INTEGER DEFAULT 0
);
"""

DDL_DEVICES = """
CREATE TABLE IF NOT EXISTS devices (
  udid TEXT PRIMARY KEY,
  discord_id TEXT,
  product TEXT,
  version TEXT,
  serial TEXT,
  device_name TEXT,
  registered_date TIMESTAMP,
  apple_registered INTEGER DEFAULT 0,
  FOREIGN KEY (discord_id) REFERENCES purchases(discord_id)
);
"""

def get_conn():
    return sqlite3.connect(current_app.config["SQLITE_PATH"], detect_types=sqlite3.PARSE_DECLTYPES)

def init_db(app):
    path = app.config["SQLITE_PATH"]
    with sqlite3.connect(path) as conn:
        c = conn.cursor()
        c.execute(DDL_PURCHASES)
        c.execute(DDL_DEVICES)
        conn.commit()

def ensure_purchase(discord_id: str, discord_name: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT discord_id FROM purchases WHERE discord_id=?", (discord_id,))
    exists = c.fetchone()
    if not exists:
        c.execute(
            """INSERT INTO purchases(discord_id, discord_name, purchase_date, expires_date, slots_allowed, slots_used)
               VALUES(?, ?, ?, datetime('now','+1 year'), 1, 0)""",
            (discord_id, discord_name, datetime.now()),
        )
        conn.commit()
    conn.close()

def register_device(discord_id: str, discord_name: str, udid: str, product: str, version: str, serial: str):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT udid FROM devices WHERE udid=?", (udid,))
    already = c.fetchone()

    ensure_purchase(discord_id, discord_name)

    if not already:
        c.execute("SELECT slots_allowed, slots_used FROM purchases WHERE discord_id=?", (discord_id,))
        slots_allowed, slots_used = c.fetchone()
        if slots_used >= slots_allowed:
            conn.close()
            raise RuntimeError("No available slots for this account.")

        c.execute(
            """INSERT INTO devices (udid, discord_id, product, version, serial, device_name, registered_date, apple_registered)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
            (udid, discord_id, product, version, serial, f"{discord_name}'s {product}", datetime.now()),
        )
        c.execute("UPDATE purchases SET slots_used = slots_used + 1 WHERE discord_id=?", (discord_id,))
        conn.commit()

    conn.close()

def list_user_devices(discord_id: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT udid, product, version, serial, apple_registered, registered_date
                 FROM devices WHERE discord_id=? ORDER BY registered_date DESC""", (discord_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_pending_devices():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT udid, device_name FROM devices WHERE apple_registered=0""")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_registered(udid: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE devices SET apple_registered=1 WHERE udid=?", (udid,))
    conn.commit()
    conn.close()
