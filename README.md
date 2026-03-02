# Axe Webhooks - ATH Monitor

Monitor your Axe mining pool workers and receive Discord notifications when they hit new All-Time High (ATH) best shares!

![Version](https://img.shields.io/badge/version-0.5.5-blue)
![Umbrel](https://img.shields.io/badge/platform-Umbrel-purple)

## 🎯 Overview

Axe Webhooks is an Umbrel app that monitors your mining workers across multiple chains (BCH, XEC, BTC, DBG) and sends beautiful Discord notifications when a worker achieves a new best share. Track your mining progress and celebrate those near-block-solution moments!

## ✨ Features

- 🔍 **Multi-Chain Support**: Monitor BCH, XEC, BTC, and DBG pools simultaneously
- 🔔 **Discord Notifications**: Beautiful embeds with worker stats, best shares, and block progress bars
- 🌐 **Web UI**: Easy configuration through a user-friendly interface
- 📊 **Pool Status Testing**: Test your webhook and view current pool stats
- 🔄 **Auto-Detection**: Automatically detects your Umbrel host IP
- 📈 **Progress Tracking**: Visual progress bars showing how close shares are to solving a block
- 💾 **Persistent State**: Remembers worker ATHs across restarts

## 📋 Requirements

- Umbrel home server
- Axe mining pool apps installed (AxeBCH, AxeXEC, AxeBTC, and/or AxeDBG)
- Discord webhook URL
- Umbrel Proxy Token (for accessing local Axe APIs)

## 🚀 Installation

### Install from Community App Store

1. Open your Umbrel dashboard
2. Go to **App Store** → **Community App Stores**
3. Add the community app store using this GitHub link:
   ```
   https://github.com/AkaCurtis/Axe-Webhooks
   ```
4. Once added, find "ATH Monitor" in your app store
5. Click **Install**

## ⚙️ Configuration

### Step 1: Access the Web UI

1. Open Axe Webhooks from your Umbrel apps
2. The configuration page will load

### Step 2: Get Your Umbrel Proxy Token

The proxy token is required to access your local Axe pool APIs. The cookie is **HttpOnly** (for security), so you need to use browser DevTools to extract it:

#### Method 1: Browser DevTools - Cookies (Recommended)

1. Open any Axe app in your browser (e.g., `http://umbrel.local:21212/` for AxeBCH)
2. Open Browser Developer Tools:
   - **Chrome/Edge**: Press `F12` or right-click → "Inspect"
   - **Firefox**: Press `F12` or right-click → "Inspect Element"
   - **Safari**: Enable Developer Menu first, then press `Option + Command + I`

3. Go to the **Application** tab (Chrome/Edge) or **Storage** tab (Firefox)
4. In the left sidebar, expand **Cookies**
5. Click on your Umbrel domain (e.g., `http://umbrel.local:21212`)
6. Find the cookie named `UMBREL_PROXY_TOKEN`
7. Copy the **Value** (it will be a long JWT token starting with `eyJ...`)

#### Method 2: Network Tab - Request Headers

1. Open any Axe app in your browser (e.g., `http://umbrel.local:21212/`)
2. Press `F12` and go to the **Network** tab
3. Refresh the page or navigate within the app
4. Click on any request in the list
5. Look at the **Request Headers** section
6. Find the `Cookie:` header
7. Copy the value after `UMBREL_PROXY_TOKEN=` (everything until the next `;` or end of line)

> **Note**: The token is a JWT that looks like: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### Step 3: Get Your Discord Webhook URL

1. Open Discord and go to the server where you want notifications
2. Go to **Server Settings** → **Integrations** → **Webhooks**
3. Click **New Webhook** (or use an existing one)
4. Customize the webhook name and channel
5. Click **Copy Webhook URL**
6. Save the webhook

### Step 4: Configure Pool Endpoints

In the Axe Webhooks web UI:

1. **Pool URLs**: The app auto-detects your Umbrel IP. Default values are:
   - BCH: `http://[YOUR_UMBREL_IP]:21212`
   - XEC: `http://[YOUR_UMBREL_IP]:21218`
   - BTC: `http://[YOUR_UMBREL_IP]:21215`
   - DBG: `http://[YOUR_UMBREL_IP]:21213`
   
   You typically won't need to change these unless you have custom ports.

2. **Proxy Token**: Paste the `UMBREL_PROXY_TOKEN` value you copied earlier

3. **Discord Webhook**: Paste your Discord webhook URL

4. Click **Save Configuration**

### Step 5: Test Your Setup

1. Click the **Test Webhook** button in the web UI
2. Check your Discord channel for a test message showing current pool status
3. If successful, you're all set! If not, check the troubleshooting section below

## 📱 Usage

Once configured, the app runs automatically in the background:

1. **Monitoring**: The watcher checks your pools every 15 seconds (configurable)
2. **Detection**: When a worker achieves a new best share, it's compared against the stored ATH
3. **Notification**: If it's a new ATH, a Discord notification is sent with:
   - Worker name
   - Best share value
   - Current block difficulty
   - Progress bar showing proximity to solving a block
4. **State Tracking**: ATH values are persisted, so restarts won't trigger duplicate notifications

### Discord Notification Format

When a worker hits a new ATH, you'll receive an embed like this:

```
🔥 NEW WORKER ATH! (BCH)
[Worker Name] just hit a new best share!

🏷 Worker: [Worker Display Name]
🎯 Best Share: [Formatted Value]
⛏ Block Diff: [Network Difficulty]
📈 Progress to Block: [████████░░░░░░░░░░] XX.XX%
```

## 🔧 Advanced Configuration

### Environment Variables

#### Admin Password
Protect your configuration with a password:
```yaml
environment:
  ADMIN_PASSWORD: "your-secure-password"
```

#### Poll Interval
Adjust how often pools are checked (in seconds):
```yaml
environment:
  POLL_SECONDS: "15"  # Default is 15 seconds
```

### Data Persistence

Configuration and state files are stored in `${APP_DATA_DIR}`:
- `config.json`: Your configuration (URLs, tokens, webhook)
- `bch_state.json`, `xec_state.json`, etc.: ATH tracking for each chain

## 🐛 Troubleshooting

### "Webhook not configured" or "Pool offline" errors

1. **Verify Axe apps are running**: Make sure your AxeBCH, AxeXEC, etc. apps are started
2. **Check proxy token**: Ensure the token is current (Umbrel may rotate tokens on restart)
3. **Validate URLs**: Confirm pool URLs match your Umbrel IP and ports
4. **Test webhook**: Use the Test Webhook button to diagnose issues

### Discord notifications not appearing

1. **Check webhook URL**: Ensure you copied the full Discord webhook URL
2. **Verify permissions**: Make sure the webhook has permission to post in the channel
3. **Check Discord server status**: Ensure Discord isn't experiencing outages

### Workers not being detected

1. **Verify workers are active**: Check your mining software is running and connected
2. **Check pool response**: Use the Test Webhook feature to see if workers appear in the status
3. **Review logs**: Check Umbrel app logs for error messages

### Auto-detection of Umbrel IP fails

If the app can't detect your Umbrel IP:

1. Manually enter your Umbrel server IP in the pool URL fields
2. Common Umbrel IPs: `192.168.1.X`, `10.0.0.X` (check your router)
3. You can find your Umbrel IP in: **Umbrel Settings** → **About**

### Proxy token expires

Umbrel may rotate the proxy token after updates or restarts:

1. Get a fresh token using the steps in Configuration
2. Update it in the Axe Webhooks web UI
3. Save and test again

## 📊 Monitored Metrics

For each chain, the app tracks:
- Worker names and display names
- Current hashrate (per worker and total)
- Best shares (all-time high per worker)
- Network difficulty
- Block progress percentage

## 🛠️ Development

### Project Structure

```
axe-webhooks/
├── docker-compose.yml          # Docker orchestration
├── umbrel-app.yml             # Umbrel app manifest
├── watcher/                   # Background monitoring service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── watcher.py            # Main monitoring logic
└── web/                       # Configuration web UI
    ├── Dockerfile
    ├── app.py                # Flask web server
    └── templates/
        └── index.html        # Configuration interface
```

### Building Locally

```bash
cd axe-webhooks
docker-compose build
docker-compose up
```

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/AkaCurtis/Axe-Webhooks/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AkaCurtis/Axe-Webhooks/discussions)

## 💰 Support the Project

If you find this app useful and want to support development, donations are greatly appreciated!

### Cryptocurrency

- **Bitcoin Cash (BCH)**: `bitcoincash:qpx8jdmgef3z3zj3a4r2p2fykql2stkzpcgnlvy6k6`
- **Bitcoin (BTC)**: `36hE3rMDd5D3tKXwyBwb6osCaS8WaEobMQ`
- **eCash (XEC)**: `ecash:qzupqgsekhsc9t0zgkcvt6c6m5k07xrruqx9rz4z9x`

### Fiat

- **CashApp**: [$WRDSY](https://cash.app/$WRDSY)

Every contribution helps maintain and improve ATH Monitor. Thank you for your support! ⚡

## �🙏 Credits

Developed by Curtis for the Axe mining community.

---

**Happy Mining! 🎉**
