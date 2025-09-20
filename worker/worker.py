import os
import time
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("SQLITE_PATH") or "./devices.db"
APPLE_EMAIL = os.getenv("APPLE_EMAIL", "")
APPLE_PASSWORD = os.getenv("APPLE_PASSWORD", "")
ANISETTE_URL = os.getenv("ANISETTE_URL", "https://ani.sidestore.io")

def db_conn():
    return sqlite3.connect(DB_PATH)

def get_pending():
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT udid, device_name FROM devices WHERE apple_registered=0")
        return cur.fetchall()

def mark_registered(udid: str):
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE devices SET apple_registered=1 WHERE udid=?", (udid,))
        conn.commit()

def run_mock():
    print("[WORKER] MOCK mode: marking devices as registered without Apple API.")
    for udid, name in get_pending():
        print(f"[WORKER] (MOCK) Registering {name} / {udid}")
        time.sleep(0.25)
        mark_registered(udid)

def run_real():
    from PyDunk import XcodeAPI, GSAuthSync, GSUserAuth, Anisette

    ani = Anisette(ANISETTE_URL)
    gs = GSAuthSync(GSUserAuth(APPLE_EMAIL, APPLE_PASSWORD, ani))
    xcode = XcodeAPI.from_gsauth(gs)
    team = xcode.teams[0]

    for udid, name in get_pending():
        try:
            exists = any(getattr(d, "device_number", None) == udid for d in team.devices)
            if not exists:
                print(f"[WORKER] Adding {name} / {udid} to Apple developer portal...")
                                add_device_to_apple(team, udid=udid, name=name)

            mark_registered(udid)
            print(f"[WORKER] Marked registered: {udid}")
        except Exception as e:
            print(f"[WORKER] Error registering {udid}: {e}")


def add_device_to_apple(team, udid: str, name: str):
    """
    Attempt to add a device to Apple Developer Portal via PyDunk's Xcode session.
    Falls back gracefully if the private endpoint shape changes.
    """
    try:
        # XcodeAPI session hidden on team object
        xcode_session = getattr(team, "_x", None)
        if xcode_session is None:
            raise RuntimeError("No Xcode session found on team (_x is None).")

        # team id attribute sometimes varies across libs
        team_id = getattr(team, "team_id", None) or getattr(team, "identifier", None) or getattr(team, "id", None)
        if not team_id:
            raise RuntimeError("Could not resolve team id attribute on team.")

        payload = {
            "teamId": team_id,
            "deviceNumber": udid,
            "deviceName": name,
            "devicePlatform": "ios",
        }

        # Private request helper used by PyDunk to speak to QH65B2
        resp = xcode_session._pr("/services/QH65B2/ios/addDevice.action", content=payload)
        if not isinstance(resp, dict):
            raise RuntimeError(f"Unexpected response type: {type(resp)}")

        rc = resp.get("resultCode")
        if str(rc) == "0":
            print(f"[WORKER] Successfully added {udid} ({name}) to team {team_id}")
            return True
        else:
            msg = resp.get("userString") or resp.get("resultString") or json.dumps(resp)
            raise RuntimeError(f"Apple addDevice failed (code={rc}): {msg}")
    except Exception as e:
        raise


def main():
    real = bool(APPLE_EMAIL and APPLE_PASSWORD)
    print(f"[WORKER] Starting. Real mode: {real}. DB: {DB_PATH}")
    while True:
        try:
            if real:
                run_real()
            else:
                run_mock()
        except Exception as e:
            print(f"[WORKER] Loop error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()
