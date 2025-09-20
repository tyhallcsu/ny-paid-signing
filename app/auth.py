import json
import uuid
import redis
from flask_discord import DiscordOAuth2Session
from flask import current_app

r_client = None
discord_oauth = None

def init_discord_oauth(app):
    global discord_oauth, r_client
    discord_oauth = DiscordOAuth2Session(app)
    r_client = redis.from_url(app.config["REDIS_URL"], decode_responses=True)

def create_session_blob(discord_id: int, discord_name: str) -> str:
    token = str(uuid.uuid4())
    payload = {"discord_id": str(discord_id), "discord_name": discord_name}
    r_client.setex(f"session:{token}", 600, json.dumps(payload))
    return token

def pop_session_blob(token: str):
    key = f"session:{token}"
    raw = r_client.get(key)
    if raw:
        r_client.delete(key)
        return json.loads(raw)
    return None
