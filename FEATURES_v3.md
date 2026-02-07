# SocialFish v3.0 - Modern Dynamic Cloning & Phishing Toolkit

## What's New in v3.0

This release modernizes SocialFish with:
- **Playwright-based browser automation** for cloning modern JS-heavy login pages
- **Full cookie capture and analysis** with detailed metadata
- **Template system** to save and reuse clones
- **Live OTP interception panel** with webhook notifications
- **MITM reverse proxy support** with auto-tunneling (ngrok/cloudflared)
- **6 clone modes**: login-only, cookies-only, or both
- **Multi-step login detection** for complex flows (Office365, etc.)
- **2FA/OTP detection** with manual or auto-injection
- **Live victim notifications** via WebSocket and webhooks
- **Lure URL auto-generation** with tracking

---

## Quick Start

### Installation & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# (Optional) Setup tunneling
python core/tunnel_manager.py setup
```

### Run Application

```bash
python SocialFish.py admin password
# Or with Flask-SocketIO
socketio run SocialFish.py --port 5000
```

Access at: `http://localhost:5000/neptune`

---

## Features & Workflows

### 1. **Templates Library** — Save Reusable Clones
- **Path**: `/templates`
- **Features**:
  - Create new template by entering target URL
  - Saves form structure, fields, CSRF tokens, auth endpoints
  - Clone modes: `both` (default), `login`, `cookies`
  - Browser engines: `playwright` (default), `selenium` (optional)
  - Headless (default) or headful visibility
  - Stealth options to evade headless detection

**Example**: Clone Office365 → save template → reuse for multiple users

---

### 2. **Recording Flow**
1. Go to `/templates` → Click "New Template"
2. Enter target URL (e.g., `https://login.office.com`)
3. Choose:
   - **Clone Mode**: `both` (captures credentials + cookies), `login` (credentials only), `cookies` (cookies + session only)
   - **Browser**: `playwright` or `selenium`
   - **Headless**: Yes/No
   - **Stealth**: Yes/No
4. System opens a browser and records:
   - Navigation & page changes
   - Form fields detected
   - XHR/fetch requests
   - All cookies set
   - Screenshots at each step

---

### 3. **Victim Capture Page** — Generic Phishing Form
- **Path**: `/capture/<lure_hash>`
- **How it works**:
  1. Generate lure URL from template
  2. Send to victims
  3. Victim lands on generic form matching clone
  4. Form auto-submits to `/login` endpoint
  5. Credentials captured in database
  6. If OTP breakpoint enabled, live panel activates

**Captured Data**:
- Username/password
- All cookies from browser
- User-Agent, IP address, device/OS
- Screenshots (if configured)
- Timestamp

---

### 4. **Live OTP Panel** — Intercept 2FA Codes
- **Path**: `/admin/otp_panel.html` (auto-opened on 2FA detection)
- **Features**:
  - Real-time victim session display
  - Captured credentials shown
  - Wait for OTP (automatic or manual entry)
  - Inject OTP back to victim's browser
  - Network activity log
  - Auto-continue to redirect after OTP

**For 2FA-protected sites**:
1. Template detects OTP requirement (heuristics: `/otp/`, `/2fa/` endpoints, OTP input fields)
2. On victim submission, system pauses at OTP screen
3. Operator receives notification (webhook, WebSocket)
4. Operator enters/waits for OTP code
5. Code injected to victim's browser
6. Login completes

---

### 5. **Tunneling & Lure URLs** — Remote Testing & Phishing
- **Path**: `/tunnel/setup` and `/lure/generate`
- **Tunnel Options**:
  - **ngrok** (recommended): Fast, reliable tunneling service
  - **cloudflared**: Free Cloudflare Tunnel (requires account)
  - **localhost**: Local testing (default)

**Setup Tunnel**:
```bash
# Interactive setup
python core/tunnel_manager.py setup

# Or manual start
python core/tunnel_manager.py start --type ngrok --port 5000
```

**Generate Lure URL**:
1. Create/select template
2. Click "Tunnel" → provide ngrok token or use cloudflared
3. Click "Lure" → auto-generates unguessable URL
4. Copy and distribute to victims

**Lure URL Example**:
```
https://something.ngrok.io/capture/a1b2c3d4e5f6g7h8
```

**Tracking**:
- Click count per lure
- Victim IPs and sessions
- Capture success rate

---

### 6. **Cookie Inspector & Analysis**
- **Path**: `/sessions` → view session → cookies tab
- **Captures**:
  - Cookie name, value
  - Domain, path
  - Secure, HttpOnly, SameSite flags
  - Expiration time
  - Step at which set

**Analysis Features**:
- Count session vs persistent cookies
- Flag insecure cookies (missing flags)
- Identify auth tokens (`session`, `jwt`, `token` keywords)
- Detect tracking cookies
- Cross-domain cookie detection

**Export**:
- JSON (structured format)
- CSV (spreadsheet import)
- Raw browser format

---

### 7. **Multi-step & 2FA Detection**
- **Automatic detection** of complex login flows:
  - Multiple form submissions
  - Redirect chains
  - OTP/SMS/Email steps
  - Verification endpoints

**Heuristics**:
- Multiple distinct POST endpoints → multi-step
- `/otp/`, `/mfa/`, `/2fa/`, `/twofa/` in URL → 2FA required
- `<input type="tel">` or `<input type="number">` with OTP patterns → OTP field
- SMS/email patterns in response → OTP delivery method

**User Control**:
- Manual breakpoints between steps
- Wait for OTP with operator notification
- Auto-continue after successful capture

---

### 8. **Webhook Notifications** — Real-time Alerts
- **Path**: `/webhooks`
- **Setup**:
  1. Create template
  2. Go to "Webhooks" → Add webhook URL
  3. Choose trigger: `credential_submit`, `otp_received`, `session_created`
  4. Choose format: `json`, `form-encoded`, `xml`

**Example Webhook Payload**:
```json
{
  "session_id": 123,
  "template_id": 5,
  "victim_ip": "203.0.113.45",
  "event": "credential_submit",
  "credentials": {
    "username": "user@example.com",
    "password": "pass123"
  },
  "timestamp": "2026-02-07T10:30:00Z"
}
```

**Integration Examples**:
- Slack webhook → real-time alerts
- Discord bot → automation
- Custom API → database logging
- Telegram bot → mobile notifications

---

### 9. **Sessions Management** — View & Export Captures
- **Path**: `/sessions`
- **Per-session data**:
  - Session hash (unique ID)
  - Victim IP & geolocation (if available)
  - Browser, OS, device type
  - Form data submitted
  - Captured credentials
  - Cookies (full jar)
  - Screenshot(s)
  - Timestamp

**Actions**:
- View full session details  
- Export session to JSON/CSV
- Download screenshots
- Copy credentials
- Delete session

**Bulk Operations** (planned):
- Filter by date range, IP, template
- Export sessions to PDF report
- Chart/analytics dashboard

---

## CLI Commands

```bash
# Tunnel management
python core/tunnel_manager.py setup              # Interactive setup
python core/tunnel_manager.py start --type ngrok # Start ngrok tunnel
python core/tunnel_manager.py stop               # Stop tunnel
python core/tunnel_manager.py status             # Check tunnel status

# Database migration
python core/db_migration.py                       # Initialize/migrate schema

# Recorder (async)
python core/recorder_playwright.py record https://login.example.com

# Cookie inspector
python core/cookie_inspector.py analyze --session-id 1
python core/cookie_inspector.py export --session-id 1 --format csv
```

---

## Database Schema (SQLite)

**New Tables** (v3.0):
- `templates` — Saved clone configurations
- `sessions` — Victim interaction records
- `cookies` — Detailed cookie data per session
- `network_logs` — HTTP requests/responses
- `screenshots` — Captured images
- `mitm_config` — Tunnel & proxy settings
- `webhooks` — Notification endpoints
- `webhook_logs` — Webhook delivery tracking
- `lure_urls` — Phishing link tracking
- `analyzer_logs` — 2FA/multi-step detection
- `tunnel_sessions` — Active tunnel management

---

## Clone Modes Explained

| Mode | Captures | Use Case |
|------|----------|----------|
| `both` (default) | Credentials + Cookies | Full impersonation, SSO testing |
| `login` | Credentials only | Credential harvesting, testing |
| `cookies` | Session cookies only | Using existing sessions, cookie theft |

---

## Browser Engines

| Engine | Pros | Cons |
|--------|------|------|
| **Playwright** | Modern, fast, built-in stealth | Heavier binaries |
| **Selenium** | Wider ecosystem, mature | Slower, requires driver setup |

Both support:
- Headless mode (default)
- Custom User-Agent
- Viewport emulation
- Cookie interception
- Screenshot capture
- Network logging

---

## Security & Ethics

⚠️ **Legal Disclaimer**:
1. **Consent Required** — Only test systems you own or have explicit written permission to test
2. **Audit Logging** — All operations logged with user attribution
3. **Data Protection** — Implement proper data retention policies
4. **GDPR/Privacy** — Comply with local regulations on credential storage

**Built-in Protections**:
- Mandatory consent checkbox in UI
- User audit trail in database
- Optional data masking (passwords redacted in logs)
- Auto-delete old sessions (configurable)

---

## Troubleshooting

**Playwright browser not found**:
```bash
playwright install chromium
```

**ngrok tunnel fails**:
```bash
# Get token from https://dashboard.ngrok.com/auth
python core/tunnel_manager.py setup
```

**OTP panel not opening**:
- Check WebSocket connection in browser console
- Ensure Flask-SocketIO running (`pip install flask-socketio eventlet`)
- Verify browser supports WebSockets

**Cookies not captured**:
- Check browser DevTools → Network tab
- Verify clone is rendering correctly (take screenshot)
- Check DB schema: `sqlite3 database.db "PRAGMA table_info(cookies);"`

---

## Next Steps (Planned)

- [ ] Selenium full support
- [ ] Advanced stealth (perfection.js, cloud browser pools)
- [ ] CAPTCHA auto-solving integration
- [ ] PDF report generation
- [ ] Team management & multi-user
- [ ] Cloud deployment templates (AWS Lambda, GCP Cloud Run)
- [ ] Mobile app for notifications
- [ ] Reverse HTTP proxy for complete MITM

---

## Support & Contributing

For issues, feature requests, or contributions:
- GitHub: https://github.com/UndeadSec/SocialFish
- Issues: https://github.com/UndeadSec/SocialFish/issues

---

**Made with ❤️ by UndeadSec**
