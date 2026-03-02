import os
import json
import requests
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, jsonify

app = Flask(__name__)

CONFIG_PATH = "/data/config.json"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()

def load_config():
    defaults = {
        "bch_base": "",
        "xec_base": "",
        "btc_base": "",
        "dbg_base": "",
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

@app.route("/test", methods=["POST"])
def test_webhook():
    pw = request.form.get("pw", "")
    if not check_password(pw):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    cfg = load_config()
    webhook = cfg.get("discord_webhook", "").strip()
    
    if not webhook:
        return jsonify({"success": False, "error": "Discord webhook not configured"}), 400
    
    chains = [
        ("BCH", cfg.get("bch_base", "").strip(), 0x8DC351, "https://cryptologos.cc/logos/bitcoin-cash-bch-logo.png"),
        ("XEC", cfg.get("xec_base", "").strip(), 0x0074C2, "https://cryptologos.cc/logos/ecash-xec-logo.png"),
        ("BTC", cfg.get("btc_base", "").strip(), 0xF7931A, "https://cryptologos.cc/logos/bitcoin-btc-logo.png"),
        ("DBG", cfg.get("dbg_base", "").strip(), 0xDC3545, "https://via.placeholder.com/150/8B4513/FFFFFF?text=DBG"),
    ]
    
    proxy_token = cfg.get("proxy_token", "").strip()
    cookies = {"UMBREL_PROXY_TOKEN": proxy_token} if proxy_token else None
    
    embeds = []
    stats_summary = []
    
    for chain, base_url, color, thumbnail in chains:
        if not base_url:
            continue
        
        try:
            # Fetch pool stats
            pool_url = f"{base_url.rstrip('/')}/api/pool"
            workers_url = f"{base_url.rstrip('/')}/api/pool/workers"
            
            pool_resp = requests.get(pool_url, cookies=cookies, timeout=10)
            pool_resp.raise_for_status()
            pool_data = pool_resp.json()
            
            workers_resp = requests.get(workers_url, cookies=cookies, timeout=10)
            workers_resp.raise_for_status()
            workers_data = workers_resp.json()
            
            # Extract stats
            hashrate = pool_data.get("hashrate", 0)
            network_diff = pool_data.get("network_difficulty", 0)
            workers_count = len(workers_data.get("workers_details", []))
            
            # Format numbers
            def format_num(val):
                try:
                    num = float(val)
                    units = ["", "K", "M", "G", "T", "P", "E"]
                    idx = 0
                    while num >= 1000 and idx < len(units) - 1:
                        num /= 1000.0
                        idx += 1
                    return f"{num:.2f}{units[idx]}" if idx > 0 else f"{int(num)}"
                except:
                    return str(val)
            
            hashrate_fmt = format_num(hashrate) + "H/s"
            diff_fmt = format_num(network_diff)
            
            stats_summary.append(f"**{chain}**: {workers_count} workers, {hashrate_fmt}")
            
            embeds.append({
                "title": f"{chain} Pool Status",
                "color": color,
                "thumbnail": {"url": thumbnail},
                "fields": [
                    {"name": "👷 Workers", "value": f"`{workers_count}`", "inline": True},
                    {"name": "⚡ Hashrate", "value": f"`{hashrate_fmt}`", "inline": True},
                    {"name": "🎯 Network Diff", "value": f"`{diff_fmt}`", "inline": True},
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            
        except Exception as e:
            stats_summary.append(f"**{chain}**: Error - {str(e)}")
            embeds.append({
                "title": f"{chain} Pool Status",
                "color": 0xFF0000,
                "description": f"❌ Error fetching stats: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    
    if not embeds:
        return jsonify({"success": False, "error": "No pools configured"}), 400
    
    # Send to Discord
    payload = {
        "content": "🧪 **Test Webhook - Current Pool Status**",
        "embeds": embeds
    }
    
    try:
        resp = requests.post(webhook, json=payload, timeout=15)
        resp.raise_for_status()
        return jsonify({
            "success": True,
            "message": "Test webhook sent successfully!",
            "stats": "\n".join(stats_summary)
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to send webhook: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3456, debug=False)
