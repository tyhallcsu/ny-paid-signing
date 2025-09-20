# ny-paid-signing

Capture iOS UDIDs via a `.mobileconfig`, tie them to Discord buyers, and queue device registration on your Apple Developer account via **PyDunk**. Ships with a Flask web app, a background worker, and a Discord bot—plus systemd + nginx configs for production.

---

## Features

- 🔐 **Discord OAuth** to link purchases → users
- 📱 **UDID capture** using iOS configuration profile flow
- 🗄️ **SQLite** schema for purchases/devices with idempotent inserts
- 🚚 **Background worker** to add devices to Apple (PyDunk)
- 🤖 **Discord bot**: auto-DM registration link and `!status` for users
- 🧪 **MOCK mode**: test end-to-end without Apple credentials
- 🧰 **Ops bundle**: systemd unit files + nginx site config

---

## Architecture

```
Flask (/register → .mobileconfig) → iOS POSTs device info → DB
                                     ↓
                              Worker picks up
                        → PyDunk addDevice → mark registered
                                     ↓
                           Discord bot !status
```

Key endpoints:
- `GET /register` → kicks off Discord OAuth and serves `.mobileconfig`
- `GET /callback` → Discord OAuth callback
- `GET|POST /retrieve/` → serves `.mobileconfig` (GET) and ingests plist (POST)
- `GET /me/devices` → authenticated list of user devices (JSON)

---

## Requirements

- Python 3.11+
- Redis (`redis-server` running locally or a URL in `.env`)
- (Optional for **real** Apple calls) An Apple Developer account (email + app-specific password) and working PyDunk

Install Python deps listed in `requirements.txt` (includes `flask`, `discord.py`, `flask-discord`, `redis`, and PyDunk from GitHub).

---

## Quick Start (Local / Staging)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set real values (see below)

# Terminal 1: Flask
python run_flask.py

# Terminal 2: Worker (MOCK mode if Apple creds are empty)
python worker/worker.py

# Terminal 3: Discord bot
python bot/discord_bot.py
```

Open `http://localhost:8080/register` on **an iOS device** to receive and install the profile. After installation, your device data will be recorded in the DB.

---

## Environment Variables

Copy `.env.example` to `.env` and fill the following:

- `FLASK_SECRET_KEY` — generate via `python -c "import secrets;print(secrets.token_hex(32))"`  
- `DISCORD_CLIENT_ID` / `DISCORD_CLIENT_SECRET` — from Discord Developer Portal  
- `DISCORD_REDIRECT_URI` — e.g., `https://paid.nythepegas.us/callback`  
- `DISCORD_BOT_TOKEN` — bot token from Discord Developer Portal  
- `DISCORD_GUILD_ID` — your Discord server ID (optional for future use)  
- `DISCORD_DEVELOPER_ROLE_ID` — the role ID purchasers receive  
- `REDIS_URL` — e.g., `redis://localhost:6379/0`  
- `SQLITE_PATH` — e.g., `/opt/ny-paid-signing/devices.db`  
- `BASE_URL` — e.g., `https://paid.nythepegas.us`  
- `APPLE_EMAIL` / `APPLE_PASSWORD` — your Apple Developer credentials (leave blank to run in MOCK mode)  
- `ANISETTE_URL` — Anisette endpoint (default: `https://ani.sidestore.io`)

**MOCK mode**: If `APPLE_EMAIL` or `APPLE_PASSWORD` is blank, the worker **does not** call Apple and simply marks devices as registered, enabling full flow testing.

---

## Discord OAuth Setup

1. In Discord Developer Portal → **OAuth2** → **Redirects**, add:  
   `https://your-domain/callback`  
2. Ensure the **Bot** has “Server Members Intent” enabled.  
3. Invite your bot to the server; assign necessary permissions.

---

## Production Deployment (systemd + nginx)

This repo includes an **ops bundle** under `ops/`:

- `ops/systemd/ny-flask.service`
- `ops/systemd/ny-worker.service`
- `ops/systemd/ny-bot.service`
- `ops/nginx/ny-paid-signing.conf`
- `ops/scripts/install_services.sh`

**Install outline:**

```bash
# Place repo at /opt/ny-paid-signing-final (or your chosen path)
cd /opt
sudo unzip ny-paid-signing-final.zip
cd ny-paid-signing-final
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env

# Install ops files
cd ops
sudo bash scripts/install_services.sh
```

Configure TLS via certbot (example):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d paid.nythepegas.us
```
Then enforce HTTPS by uncommenting the redirect in `ops/nginx/ny-paid-signing.conf` and reloading nginx.

**Manage services:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable ny-flask ny-worker ny-bot
sudo systemctl start ny-flask ny-worker ny-bot
sudo journalctl -u ny-flask -f
```

---

## Database

SQLite file path is configurable via `SQLITE_PATH`. Two tables are created automatically:

- `purchases(discord_id, discord_name, purchase_date, expires_date, slots_allowed, slots_used)`  
- `devices(udid, discord_id, product, version, serial, device_name, registered_date, apple_registered)`

Run `scripts/migrate_existing.py` to seed known users/devices (edit it first).

---

## PyDunk Integration (Worker)

`worker/worker.py` uses PyDunk for Apple device registration. It attempts a private QH65B2 endpoint via the underlying Xcode session:

```python
resp = team._x._pr(
    "/services/QH65B2/ios/addDevice.action",
    content={
        "teamId": team.team_id,
        "deviceNumber": udid,
        "deviceName": name,
        "devicePlatform": "ios",
    }
)
# success when resp.get("resultCode") == 0
```

This path is wrapped in `add_device_to_apple(team, udid, name)` with defensive checks.

---

## Testing Checklist

- ✅ `GET /register` on iOS returns a `.mobileconfig`  
- ✅ After installing, check: `sqlite3 devices.db "SELECT * FROM devices;"`  
- ✅ Worker logs show (MOCK) or Apple device addition  
- ✅ Discord `!status` displays device + registration state

---

## Troubleshooting

- **Nothing happens after installing profile**: check Flask logs (`/healthz` for liveness), verify `BASE_URL`, and that your device posted back to `/retrieve/` (iOS preserves the `?session=` query).  
- **`apple_registered` never flips**: worker might be in MOCK mode—set `APPLE_EMAIL`/`APPLE_PASSWORD`.  
- **Discord bot doesn’t DM**: ensure “Server Members Intent” is enabled and the bot has permission to DM members.  
- **Redis errors**: verify `REDIS_URL` points to a running instance.

---

## Notes & Compliance

- Apple device limits and developer program terms apply—use responsibly.  
- Consider moving to Postgres if you outgrow SQLite.  
- For large-scale signing/distribution, add rate limits and audit logging.

---

## License

You can adopt your own license. (MIT is a common choice.)
