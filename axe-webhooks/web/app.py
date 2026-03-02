import os
import json
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

CONFIG_PATH = "/data/config.json"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()

def load_config():
    defaults = {
        "bch_base": "http://umbrel.local:21212",
        "xec_base": "http://umbrel.local:21218",
        "btc_base": "http://umbrel.local:21215",
        "dbg_base": "http://umbrel.local:21213",
        "proxy_token": "",
        "discord_webhook": "",
    }
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            defaults.update(data)
    except Exception:
        pass
    return defaults

def save_config(data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def check_password(pw):
    if not ADMIN_PASSWORD:
        return True
    return pw == ADMIN_PASSWORD

@app.route("/")
def index():
    pw = request.args.get("pw", "")
    needs_pw = ADMIN_PASSWORD and not check_password(pw)
    cfg = load_config()
    return render_template("index.html", cfg=cfg, needs_pw=needs_pw)

@app.route("/save", methods=["POST"])
def save():
    pw = request.form.get("pw", "")
    if not check_password(pw):
        return redirect("/?pw=" + pw)
    
    cfg = {
        "bch_base": request.form.get("bch_base", "").strip(),
        "xec_base": request.form.get("xec_base", "").strip(),
        "btc_base": request.form.get("btc_base", "").strip(),
        "dbg_base": request.form.get("dbg_base", "").strip(),
        "proxy_token": request.form.get("proxy_token", "").strip(),
        "discord_webhook": request.form.get("discord_webhook", "").strip(),
    }
    save_config(cfg)
    return redirect("/?pw=" + pw)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3456, debug=False)
