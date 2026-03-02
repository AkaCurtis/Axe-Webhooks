import os
import time
import json
import requests
import threading
import sys
from typing import Any, Dict
from datetime import datetime, timezone

print("=" * 50, flush=True)
print("ATH Monitor Watcher Starting...", flush=True)
print("=" * 50, flush=True)
sys.stdout.flush()

CONFIG_PATH = "/data/config.json"

POLL_SECONDS = int(os.getenv("POLL_SECONDS", "15"))

# -----------------------------
# Config Loader
# -----------------------------

def load_config() -> Dict[str, str]:
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
            for k in defaults:
                if k in data and data[k] is not None:
                    defaults[k] = str(data[k]).strip()
    except Exception:
        pass

    # Normalize URLs
    for k in ("bch_base", "xec_base", "btc_base", "dbg_base"):
        defaults[k] = defaults[k].rstrip("/")

    return defaults


# -----------------------------
# Utilities
# -----------------------------

def format_mining_number(value: int) -> str:
    try:
        num = float(value)
    except Exception:
        return str(value)

    units = ["", "K", "M", "G", "T", "P", "E"]
    index = 0
    while num >= 1000 and index < len(units) - 1:
        num /= 1000.0
        index += 1

    return f"{int(num)}" if index == 0 else f"{num:.2f}{units[index]}"


def progress_bar(ratio: float, width: int = 18) -> str:
    ratio = max(0.0, ratio)
    filled = int(min(ratio, 1.0) * width)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    pct = min(ratio, 1.0) * 100
    return f"`{bar}` **{pct:.2f}%**"


def get_json(url: str, proxy_token: str) -> Dict[str, Any]:
    cookies = {"UMBREL_PROXY_TOKEN": proxy_token} if proxy_token else None
    r = requests.get(
        url,
        cookies=cookies,
        headers={"Accept": "application/json"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, dict) else {"_raw": data}


def pretty_worker_name(workername: str) -> str:
    if not workername:
        return "Unknown"
    suffix = workername.split(".", 1)[1] if "." in workername else workername
    suffix = " ".join(suffix.strip().split())
    return suffix.title() if suffix else "Unknown"


# -----------------------------
# Discord
# -----------------------------

def discord_post_ath(display: str, bestever: int, worker_data: Dict[str, Any],
                     pool_data: Dict[str, Any], chain: str,
                     webhook: str):

    if not webhook:
        print(f"[Discord][{chain}] Webhook not set")
        return

    colors = {
        "BCH": 706958,
        "XEC": 0x0074C2,
        "BTC": 0xF7931A,
        "DBG": 0x8B4513,
    }

    thumbnails = {
        "BCH": "https://cryptologos.cc/logos/bitcoin-cash-bch-logo.png",
        "XEC": "https://cryptologos.cc/logos/ecash-xec-logo.png",
        "BTC": "https://cryptologos.cc/logos/bitcoin-btc-logo.png",
        "DBG": "https://via.placeholder.com/150/8B4513/FFFFFF?text=DBG",
    }

    embed_color = colors.get(chain, 706958)
    thumbnail = thumbnails.get(chain)

    best_formatted = format_mining_number(bestever)

    diff = pool_data.get("network_difficulty")
    diff_int = None
    diff_formatted = "—"

    try:
        if diff:
            diff_int = int(float(diff))
            diff_formatted = format_mining_number(diff_int)
    except Exception:
        pass

    ratio = float(bestever) / float(diff_int) if diff_int else 0.0
    bar_text = progress_bar(ratio)

    fields = [
        {"name": "🏷 Worker", "value": f"**{display}**", "inline": True},
        {"name": "🎯 Best Share", "value": f"`{best_formatted}`", "inline": True},
        {"name": "⛏ Block Diff", "value": f"`{diff_formatted}`", "inline": True},
        {"name": "📈 Progress to Block", "value": bar_text, "inline": False},
    ]

    payload = {
        "embeds": [{
            "title": f"🔥 NEW WORKER ATH! ({chain})",
            "description": f"**{display}** just hit a new best share!",
            "color": embed_color,
            "thumbnail": {"url": thumbnail},
            "fields": fields,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {"text": f"Axe{chain} Solo Node"},
        }]
    }

    r = requests.post(webhook, json=payload, timeout=15)
    r.raise_for_status()


# -----------------------------
# Monitor Logic
# -----------------------------

def monitor_chain(chain: str, base_key: str):

    state_file = f"/data/{chain.lower()}_state.json"

    last_bestever: Dict[str, int] = {}

    try:
        with open(state_file, "r") as f:
            d = json.load(f)
            if isinstance(d, dict):
                last_bestever = d.get("last_bestever", {})
    except Exception:
        pass

    print(f"[{chain}] Monitor started")

    while True:
        try:
            cfg = load_config()

            base_url = cfg[base_key]
            proxy_token = cfg["proxy_token"]
            webhook = cfg["discord_webhook"]
            
            # Skip if base URL is not configured
            if not base_url or base_url.strip() == "":
                print(f"[{chain}] Skipping - no URL configured")
                time.sleep(POLL_SECONDS)
                continue

            workers_url = f"{base_url}/api/pool/workers"
            pool_url = f"{base_url}/api/pool"
            
            print(f"[{chain}] Fetching from {base_url}...")

            workers_data = get_json(workers_url, proxy_token)
            pool_data = get_json(pool_url, proxy_token)
            
            print(f"[{chain}] Got {len(workers_data.get('workers_details', []))} workers")

            details = workers_data.get("workers_details", [])
            if not isinstance(details, list):
                details = []

            changed = False

            for w in details:
                raw_name = str(w.get("workername", "")).strip()
                if not raw_name:
                    continue

                bestever = (
                    w.get("best_share_since_block")
                    or w.get("bestshare_since_block")
                    or w.get("bestever_since_block")
                    or w.get("bestever")
                )

                if bestever is None:
                    continue

                try:
                    bestever_int = int(bestever)
                except Exception:
                    continue

                prev = last_bestever.get(raw_name)

                if prev is None:
                    print(f"[{chain}] Tracking new worker: {pretty_worker_name(raw_name)} (bestever: {format_mining_number(bestever_int)})")
                    last_bestever[raw_name] = bestever_int
                    changed = True
                    continue

                if bestever_int > int(prev):
                    display = pretty_worker_name(raw_name)
                    print(f"[{chain}] ATH {display}: {format_mining_number(prev)} → {format_mining_number(bestever_int)}")

                    try:
                        discord_post_ath(display, bestever_int, w, pool_data, chain, webhook)
                        print(f"[{chain}] Discord sent")
                    except Exception as e:
                        print(f"[{chain}] Discord failed: {e}")

                    last_bestever[raw_name] = bestever_int
                    changed = True

            if changed:
                with open(state_file + ".tmp", "w") as f:
                    json.dump({"last_bestever": last_bestever}, f)
                os.replace(state_file + ".tmp", state_file)

        except Exception as e:
            print(f"[{chain}] Error: {e}")

        time.sleep(POLL_SECONDS)


# -----------------------------
# Main
# -----------------------------

def main():
    print("Multi-Chain ATH Monitor")
    print(f"Polling every {POLL_SECONDS}s")
    print("=" * 40)

    threads = [
        threading.Thread(target=monitor_chain, args=("BCH", "bch_base"), daemon=True),
        threading.Thread(target=monitor_chain, args=("XEC", "xec_base"), daemon=True),
        threading.Thread(target=monitor_chain, args=("BTC", "btc_base"), daemon=True),
        threading.Thread(target=monitor_chain, args=("DBG", "dbg_base"), daemon=True),
    ]

    for t in threads:
        t.start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    try:
        print("Starting main()...", flush=True)
        main()
    except Exception as e:
        print(f"FATAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)