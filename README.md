# Axe Webhooks - ATH Monitor

Monitor your Axe mining pool workers and receive Discord notifications when they hit new All-Time High (ATH) best shares!

![Version](https://img.shields.io/badge/version-1.0.3-blue)
![Umbrel](https://img.shields.io/badge/platform-Umbrel-purple)

## 🎯 Overview

ATH Monitor is an Umbrel app that polls your solo mining pools every 15 seconds and sends a Discord notification whenever a worker achieves a new best share since the last block. It tracks each worker independently, persists state across restarts, and fires a special celebration embed when a worker's share meets or exceeds the current block difficulty (i.e. a block is found).

## ✨ Features

- 🔍 **Multi-Chain Support**: BCH, XEC, BTC, DBG (multi-algo: SHA256 + Scrypt), BC2, BCH2, and PowPow
- 🔔 **Discord Notifications**: Rich embeds with worker name, best share, block difficulty, and a visual progress bar
- 🎉 **Block Detection**: Fires a separate celebration embed (with Kirby gif) when a worker solves a block
- 🌐 **Web UI**: Configure everything through a browser — no terminal needed
- 🧪 **Test Webhook**: One-click test that shows live status of every configured pool in Discord
- 🔄 **Auto IP Detection**: Automatically detects your Umbrel host IP from the Docker gateway
- 📊 **Per-Algo Tracking**: DBG monitors each configured algorithm (SHA256, Scrypt, etc.) in separate threads
- 💾 **Persistent State**: Per-chain JSON state files survive container restarts without triggering duplicate alerts
- 🔒 **Optional Password**: Protect the config UI with `ADMIN_PASSWORD` environment variable

## 📋 Requirements

- Umbrel home server
- One or more Axe mining pool apps (AxeBCH, AxeXEC, AxeBTC, AxeDBG, etc.) **or** a PowPow pool
- Discord webhook URL
- Umbrel Proxy Token (pre-filled with a working default — only change if yours differs)

## 🚀 Installation

### Install from Community App Store

1. Open your Umbrel dashboard
2. Go to **App Store** → **Community App Stores**
3. Add this store URL:
   ```
   https://github.com/AkaCurtis/Axe-Webhooks
   ```
4. Find **ATH Monitor** in the store and click **Install**

## ⚙️ Configuration

### Step 1: Access the Web UI

Open ATH Monitor from your Umbrel apps (port `3456`). The configuration page loads automatically.

### Step 2: Pool Endpoints

The app auto-detects your Umbrel host IP and pre-fills sensible defaults:

| Chain | Default Port/Path |
|-------|------------------|
| BCH   | `21212`          |
| XEC   | `21218`          |
| BTC   | `21215`          |
| DBG   | `21213`          |
| BC2   | path or port (e.g. `:21216` or `/bc2`) |
| BCH2  | path or port |
| PowPow | full URL or plain IP (see below) |

Leave any chain blank to skip monitoring it.

### Step 3: PowPow Pool (Optional)

The **PowPow IP** field accepts either a plain IP or a full URL:

| What you enter | What the app uses |
|---|---|
| `203.0.113.42` | `http://203.0.113.42:21221` |
| `http://203.0.113.42:21221` | `http://203.0.113.42:21221` |
| `http://hostname:3000` | `http://hostname:3000` |

If you leave it blank, the app defaults to `http://willitmod-dev-powpow_app_1:3000` (the internal Docker service name for PowPow running on the same Umbrel).

### Step 4: Proxy Token

The proxy token is pre-filled with a working default. Only change it if your Axe pool APIs return `401` errors.

To get a fresh token:

1. Open any Axe app in your browser (e.g. `http://umbrel.local:21212/`)
2. Open DevTools → **Application** tab → **Cookies**
3. Copy the value of `UMBREL_PROXY_TOKEN`

> PowPow bypasses the Umbrel proxy entirely — no token needed for it.

### Step 5: Discord Webhook

1. In Discord: **Server Settings** → **Integrations** → **Webhooks** → **New Webhook**
2. Pick a channel, copy the URL, paste it into the **Discord Webhook** field

### Step 6: DBG Algo List

The **DBG Algos** field controls which algorithms are monitored on your DigiByte pool. Default: `sha256,scrypt`. Add or remove algorithms as a comma-separated list.

### Step 7: Save & Test

Click **Save Configuration**, then **Test Webhook**. You'll get a Discord embed showing live status for every configured pool.

## 📱 How It Works

1. **Polling**: Each chain runs in its own background thread, polling every `POLL_SECONDS` (default: `15`)
2. **Per-Worker Tracking**: Best share (`bestshare_since_block`) is tracked individually per worker
3. **New Best**: If the current value exceeds the stored value → Discord alert + state update
4. **Reset Detection**: If the current value drops below the stored value → the tracker re-bases (worker found a block or stats were reset)
5. **Block Hit**: If best share ≥ network difficulty → celebration embed fires instead of the normal ATH embed

### Discord Notification Format

**Normal ATH:**
```
🔥 NEW WORKER ATH! (BCH)
[Worker] just hit a new best share!

🏷 Worker:            [Name]
🎯 Best Share:        123.45M
⛏ Block Diff:         456.78G
📈 Progress to Block: ████████░░░░░░░░░░ 27.00%
```

**Block found:**
```
🎉 [Worker] just hit a block! (BCH)
[Worker] found a block with this share! Congratulations! 🎊
... (same fields + Kirby gif)
```

**Test webhook embed (per pool):**
```
✅ BCH Pool
👷 Workers: 2
⚡ Hashrate: 1.23TH/s
🎯 Difficulty: 456.78G

✅ POWPOW Pool
👷 Workers: 1
⚡ Hashrate: 458.13MH/s
🎯 Difficulty (LTC): 90.83M
🎯 Difficulty (DOGE): 44.62M
```

## 🔧 Advanced Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `POLL_SECONDS` | `15` | How often (in seconds) each chain is polled |
| `ADMIN_PASSWORD` | *(unset)* | If set, the web UI requires this password |

### Data Persistence

All files are stored in `${APP_DATA_DIR}` (mapped to `/data` inside containers):

| File | Contents |
|---|---|
| `config.json` | All user configuration |
| `bch_state.json` | BCH worker ATH tracking |
| `xec_state.json` | XEC worker ATH tracking |
| `btc_state.json` | BTC worker ATH tracking |
| `bc2_state.json` | BC2 worker ATH tracking |
| `bch2_state.json` | BCH2 worker ATH tracking |
| `powpow_state.json` | PowPow worker ATH tracking |
| `dbg_<algo>_state.json` | DBG per-algo ATH tracking |

## 🐛 Troubleshooting

### Pool shows "Offline" in test webhook

- Confirm the Axe app is running in Umbrel
- Check the port/path matches what your Axe pool actually listens on
- For PowPow: make sure the URL includes the correct port (e.g. `:21221` or `:3000`)

### Discord notifications not appearing

- Verify the full webhook URL is pasted correctly
- Confirm the webhook has permission to post in the target channel
- Click **Test Webhook** — if it succeeds there but ATH alerts don't fire, workers may not be achieving new bests yet

### Proxy token errors (401 / Invalid JSON)

The default token works for most installs. If yours is rotated:
1. Extract a fresh `UMBREL_PROXY_TOKEN` from browser DevTools (see Step 4 above)
2. Paste it into the web UI and save

### Auto-detection of Umbrel IP fails

Manually enter your Umbrel server IP in the **Base URL** field (e.g. `http://192.168.1.50`). Find your IP under **Umbrel Settings → About**.

### Workers not tracked after a restart

State files persist across restarts automatically. If a worker's best share resets (new block found), the tracker re-bases cleanly — no duplicate notifications.

## 🛠️ Project Structure

```
axe-webhooks/
├── axe-webhooks/
│   ├── docker-compose.yml     # Docker orchestration
│   └── umbrel-app.yml         # Umbrel app manifest
└── src/
    ├── watcher/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── watcher.py         # Multi-threaded polling & Discord alerts
    └── web/
        ├── Dockerfile
        ├── app.py             # Flask config UI & test webhook endpoint
        └── templates/
            └── index.html     # Configuration interface
```

## 📊 Monitored Metrics (per worker)

- `bestshare_since_block` — best share value since last block (the ATH trigger)
- `network_difficulty` — current block difficulty (used for progress bar & block detection)
- `hashrate_ths` — worker hashrate
- `ltcDiff` / `dogeDiff` — PowPow per-algo difficulties (from timeseries)

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/AkaCurtis/Axe-Webhooks/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AkaCurtis/Axe-Webhooks/discussions)

## 💰 Support the Project

- **Bitcoin Cash (BCH)**: `bitcoincash:qpx8jdmgef3z3zj3a4r2p2fykql2stkzpcgnlvy6k6`
- **Bitcoin (BTC)**: `36hE3rMDd5D3tKXwyBwb6osCaS8WaEobMQ`
- **eCash (XEC)**: `ecash:qzupqgsekhsc9t0zgkcvt6c6m5k07xrruqx9rz4z9x`
- **CashApp**: [$WRDSY](https://cash.app/$WRDSY)

Every contribution helps maintain and improve ATH Monitor. Thank you! ⚡

## 👨‍💻 Credits

Developed by Curtis for the Axe mining community.

---

**Happy Mining! 🎉**
