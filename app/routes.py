from flask import Blueprint, current_app, request, Response, redirect, url_for, jsonify
from .mobileconfig import make_profile, extract_plist_from_pkcs7
from .auth import discord_oauth, create_session_blob, pop_session_blob
from .db import register_device, list_user_devices

bp = Blueprint("routes", __name__)

@bp.get("/register")
def register():
    if not discord_oauth.authorized:
        return discord_oauth.create_session(scope=["identify"])
    user = discord_oauth.fetch_user()
    token = create_session_blob(user.id, f"{user.name}#{user.discriminator}")
    base = current_app.config["BASE_URL"]
    return redirect(f"{base}/retrieve/?session={token}")

@bp.get("/callback")
def discord_callback():
    discord_oauth.callback()
    return redirect(url_for("routes.register"))

@bp.route("/retrieve/", methods=["GET", "POST"])
def retrieve():
    base = current_app.config["BASE_URL"]
    if request.method == "GET":
        session_token = request.args.get("session", "")
        callback = f"{base}/retrieve/?session={session_token}" if session_token else f"{base}/retrieve/"
        payload = make_profile(callback)
        r = Response(payload)
        r.headers["Content-Type"] = "application/x-apple-aspen-config"
        r.headers["Content-Disposition"] = 'inline; filename="ny_udid.mobileconfig"'
        return r

    # POST
    try:
        d = extract_plist_from_pkcs7(request.data)
    except Exception as e:
        return f"<p>Failed to parse plist: {e}</p>", 400

    session_token = request.args.get("session")
    sess = pop_session_blob(session_token) if session_token else None

    if sess:
        try:
            register_device(
                discord_id=sess["discord_id"],
                discord_name=sess["discord_name"],
                udid=d["UDID"],
                product=d["PRODUCT"],
                version=d["VERSION"],
                serial=d["SERIAL"],
            )
        except Exception as e:
            return f"<p>Registration error: {e}</p>", 400

        return redirect(f"{base}/success?device={d['PRODUCT']}&udid={d['UDID'][:8]}...")

    params = f"?Product={d['PRODUCT']}&UDID={d['UDID']}&Serial={d['SERIAL']}"
    return redirect(f"{base}/retrieve/device.html{params}", code=301)

@bp.get("/retrieve/device.html")
def device_echo():
    return "".join(f"<p>{k}: {v}</p>" for k, v in request.args.items())

@bp.get("/success")
def success():
    return "<h2>✅ Device captured. Apple registration will process shortly.</h2>"

@bp.get("/me/devices")
def my_devices():
    if not discord_oauth.authorized:
        return discord_oauth.create_session(scope=["identify"])
    user = discord_oauth.fetch_user()
    rows = list_user_devices(str(user.id))
    devices = [
        {
            "udid": r[0],
            "product": r[1],
            "version": r[2],
            "serial": r[3],
            "apple_registered": bool(r[4]),
            "registered_date": str(r[5]),
        }
        for r in rows
    ]
    return jsonify(devices)
