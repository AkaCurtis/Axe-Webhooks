import os
import json
import requests
import socket
import subprocess
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, jsonify

app = Flask(__name__)

CONFIG_PATH = "/data/config.json"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()

def get_host_ip():
    """Get the Docker host IP (gateway) where Umbrel is running"""
    try:
        # Try to get default gateway (Docker host)
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            # Parse output like: "default via 172.17.0.1 dev eth0"
            parts = result.stdout.split()
            if "via" in parts:
                gateway_ip = parts[parts.index("via") + 1]
                return gateway_ip
    except Exception:
        pass
    
    # Fallback: try to detect by connecting to external host
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            # Gateway is typically .1 in the same subnet
            parts = local_ip.split(".")
            parts[-1] = "1"
            return ".".join(parts)
    except Exception:
        pass
    
    return "192.168.1.1"  # Final fallback

def parse_url(url):
    """Extract base URL and path/port from a full URL"""
    if not url:
        return "", ""
    try:
        # Handle paths like http://192.168.1.1/apps/axebch2/
        if "/apps/" in url:
            base_end = url.find("/apps/")
            base = url[:base_end]
            path = url[base_end:]
            return base, path
        # Handle ports like http://192.168.1.1:21212
        elif ":" in url:
            parts = url.rsplit(":", 1)
            if len(parts) == 2:
                # Check if it's a port number
                port_part = parts[1].split("/")[0]  # Handle :21212/api/...
                if port_part.isdigit():
                    return parts[0], ":" + port_part
    except Exception:
        pass
    return url, ""

def load_config():
    host_ip = get_host_ip()
    
    defaults = {
        "base_url": f"http://{host_ip}",
        "bch_port": "21212",
        "xec_port": "21218",
        "btc_port": "21215",
        "dbg_port": "21213",
        "bc2_path": "",
        "bch2_path": "",
        "proxy_token": "",
        "discord_webhook": "",
    }
    
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # If new format exists, use it
            if "base_url" in data:
                for key in defaults:
                    if key in data and data[key]:
                        defaults[key] = data[key]
            else:
                # Backward compatibility: parse old full URLs
                base_url_detected = None
                
                # Original 4 pools use ports
                for chain in ["bch", "xec", "btc", "dbg"]:
                    old_key = f"{chain}_base"
                    if old_key in data and data[old_key]:
                        base, path = parse_url(data[old_key])
                        if base and not base_url_detected:
                            base_url_detected = base
                        if path and path.startswith(":"):
                            defaults[f"{chain}_port"] = path[1:]  # Remove colon
                
                # BC2 and BCH2 use flexible paths
                for chain in ["bc2", "bch2"]:
                    old_key = f"{chain}_base"
                    if old_key in data and data[old_key]:
                        base, path = parse_url(data[old_key])
                        if base and not base_url_detected:
                            base_url_detected = base
                        if path:
                            defaults[f"{chain}_path"] = path
                
                if base_url_detected:
                    defaults["base_url"] = base_url_detected
                
                # Preserve other fields
                if "proxy_token" in data:
                    defaults["proxy_token"] = data["proxy_token"]
                if "discord_webhook" in data:
                    defaults["discord_webhook"] = data["discord_webhook"]
    except Exception:
        pass
    
    # Generate full URLs for watcher
    base = defaults.get("base_url", f"http://{host_ip}").rstrip("/")
    
    # Original 4 pools: simple port-based
    for chain in ["bch", "xec", "btc", "dbg"]:
        port = defaults.get(f"{chain}_port", "")
        if port:
            defaults[f"{chain}_base"] = f"{base}:{port}"
        else:
            defaults[f"{chain}_base"] = ""
    
    # BC2 and BCH2: flexible path/port
    for chain in ["bc2", "bch2"]:
        path = defaults.get(f"{chain}_path", "").strip()
        if path:
            if path.startswith(":"):
                defaults[f"{chain}_base"] = f"{base}{path}"
            elif path.startswith("/"):
                defaults[f"{chain}_base"] = f"{base}{path}"
            else:
                # Assume it's a port number without colon
                defaults[f"{chain}_base"] = f"{base}:{path}"
        else:
            defaults[f"{chain}_base"] = ""
    
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
    detected_ip = get_host_ip()
    return render_template("index.html", cfg=cfg, needs_pw=needs_pw, detected_ip=detected_ip)

@app.route("/save", methods=["POST"])
def save():
    pw = request.form.get("pw", "")
    if not check_password(pw):
        return redirect("/?pw=" + pw)
    
    base_url = request.form.get("base_url", "").strip().rstrip("/")
    
    cfg = {
        "base_url": base_url,
        "bch_port": request.form.get("bch_port", "").strip(),
        "xec_port": request.form.get("xec_port", "").strip(),
        "btc_port": request.form.get("btc_port", "").strip(),
        "dbg_port": request.form.get("dbg_port", "").strip(),
        "bc2_path": request.form.get("bc2_path", "").strip(),
        "bch2_path": request.form.get("bch2_path", "").strip(),
        "proxy_token": request.form.get("proxy_token", "").strip(),
        "discord_webhook": request.form.get("discord_webhook", "").strip(),
    }
    
    # Generate full URLs for watcher
    # Original 4 pools: simple port-based
    for chain in ["bch", "xec", "btc", "dbg"]:
        port = cfg.get(f"{chain}_port", "")
        if base_url and port:
            cfg[f"{chain}_base"] = f"{base_url}:{port}"
        else:
            cfg[f"{chain}_base"] = ""
    
    # BC2 and BCH2: flexible path/port
    for chain in ["bc2", "bch2"]:
        path = cfg.get(f"{chain}_path", "")
        if base_url and path:
            if path.startswith(":"):
                cfg[f"{chain}_base"] = f"{base_url}{path}"
            elif path.startswith("/"):
                cfg[f"{chain}_base"] = f"{base_url}{path}"
            else:
                # Assume it's a port number without colon
                cfg[f"{chain}_base"] = f"{base_url}:{path}"
        else:
            cfg[f"{chain}_base"] = ""
    
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
        ("BCH", cfg.get("bch_base", "").strip()),
        ("XEC", cfg.get("xec_base", "").strip()),
        ("BTC", cfg.get("btc_base", "").strip()),
        ("DBG", cfg.get("dbg_base", "").strip()),
        ("BC2", cfg.get("bc2_base", "").strip()),
        ("BCH2", cfg.get("bch2_base", "").strip()),
    ]
    
    proxy_token = cfg.get("proxy_token", "").strip()
    cookies = {"UMBREL_PROXY_TOKEN": proxy_token} if proxy_token else None
    
    fields = []
    stats_summary = []
    
    for chain, base_url in chains:
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
            workers_details = workers_data.get("workers_details", [])
            workers_count = len(workers_details)
            network_diff = pool_data.get("network_difficulty", 0)
            
            # Calculate hashrate from workers (in TH/s)
            hashrate_ths = 0
            for worker in workers_details:
                hashrate_ths += float(worker.get("hashrate_ths", 0))
            
            # Convert TH/s to H/s for formatting
            hashrate_hs = hashrate_ths * 1_000_000_000_000  # TH to H
            
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
            
            hashrate_fmt = format_num(hashrate_hs) + "H/s"
            diff_fmt = format_num(network_diff)
            
            stats_summary.append(f"**{chain}**: {workers_count} workers, {hashrate_fmt}")
            
            # Add field for this chain
            fields.append({
                "name": f"{'✅' if workers_count > 0 else '⚠️'} {chain} Pool",
                "value": f"👷 **Workers:** {workers_count}\n⚡ **Hashrate:** {hashrate_fmt}\n🎯 **Difficulty:** {diff_fmt}",
                "inline": True
            })
            
        except Exception as e:
            stats_summary.append(f"**{chain}**: Offline")
            fields.append({
                "name": f"❌ {chain} Pool",
                "value": "Pool is offline or unreachable.\nMake sure your Axe app is turned on.",
                "inline": True
            })
    
    if not fields:
        return jsonify({"success": False, "error": "No pools configured"}), 400
    
    # Send single embed with all pools
    embed = {
        "title": "🧪 Test Webhook - Current Pool Status",
        "description": "Current status of all configured mining pools",
        "color": 0x667EEA,
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "ATH Monitor"}
    }
    
    payload = {"embeds": [embed]}
    
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
