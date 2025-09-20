from flask import Flask
from .config import load_config
from .db import init_db
from .auth import init_discord_oauth
from .routes import bp as routes_bp

def create_app():
    app = Flask(__name__)
    load_config(app)
    init_db(app)
    init_discord_oauth(app)

    app.register_blueprint(routes_bp)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    return app
