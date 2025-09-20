import os
from dotenv import load_dotenv

def load_config(app):
    load_dotenv(override=False)

    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-key")
    app.config["SQLITE_PATH"] = os.getenv("SQLITE_PATH", "./devices.db")
    app.config["BASE_URL"] = os.getenv("BASE_URL", "http://localhost:8080")

    app.config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    app.config["DISCORD_CLIENT_ID"] = int(os.getenv("DISCORD_CLIENT_ID", "0") or "0")
    app.config["DISCORD_CLIENT_SECRET"] = os.getenv("DISCORD_CLIENT_SECRET", "")
    app.config["DISCORD_REDIRECT_URI"] = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8080/callback")
    app.config["DISCORD_BOT_TOKEN"] = os.getenv("DISCORD_BOT_TOKEN", "")
    app.config["DISCORD_GUILD_ID"] = int(os.getenv("DISCORD_GUILD_ID", "0") or "0")
    app.config["DISCORD_DEVELOPER_ROLE_ID"] = int(os.getenv("DISCORD_DEVELOPER_ROLE_ID", "0") or "0")

    app.config["APPLE_EMAIL"] = os.getenv("APPLE_EMAIL", "")
    app.config["APPLE_PASSWORD"] = os.getenv("APPLE_PASSWORD", "")
    app.config["ANISETTE_URL"] = os.getenv("ANISETTE_URL", "https://ani.sidestore.io")
