<p align="center">
  <img src="https://raw.githubusercontent.com/UndeadSec/SocialFishMobile/master/content/logo.png" width="200"/>
</a></p>
<h1 align="center">SocialFish v3.0</h1>
<h3 align="center">Modern Dynamic Phishing Toolkit</h3>

**SocialFish v3.0** brings powerful new features for cloning modern login pages, capturing cookies, and intercepting 2FA codes with a live operator panel.

## 🆕 What's New in v3.0

- **Playwright Browser Automation** — Clone modern JS-heavy login pages
- **Full Cookie Capture & Analysis** — Detailed metadata, security attributes, auth tokens
- **Template System** — Save and reuse clones across multiple victims
- **Live OTP Interception Panel** — Real-time 2FA code capture and injection
- **MITM Reverse Proxy** — ngrok/cloudflared tunneling with auto-installation
- **6 Clone Modes** — Login-only, cookies-only, or full capture
- **Multi-step Login Detection** — Automatic heuristics for complex flows (Office365, etc.)
- **Webhook Notifications** — Real-time alerts to Slack, Discord, custom APIs
- **Session Management** — Full session tracking with export to JSON/CSV
- **Network Interception** — Log all HTTP requests/responses
- **Victim Tracking** — Track clicks, IP addresses, geolocation, device type

## 📖 Documentation

- **[FEATURES_v3.md](FEATURES_v3.md)** — Complete feature guide with workflows
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** — Technical implementation details
- **[Wiki](https://github.com/UndeadSec/SocialFish/wiki)** — Original setup and advanced guides

## 🚀 Quick Start

### Option 1: Interactive Setup (Recommended)
```bash
python setup.py
```
This will:
- Install all dependencies
- Setup Playwright browsers
- Initialize database
- Configure tunneling (optional)
- Display quick-start guide

### Option 2: Manual Setup
```bash
pip install -r requirements.txt
playwright install chromium
python SocialFish.py admin password
```

Then access: **http://localhost:5000/neptune**

## 🎯 Basic Workflow

1. **Create Template**
   ```
   /templates → New Template → Enter target URL
   ```

2. **Setup Tunnel** (optional, for remote testing)
   ```
   Click "Tunnel" → Choose ngrok/cloudflared → Authorize
   ```

3. **Generate Lure URL**
   ```
   Click "Lure" → Copy unguessable URL
   ```

4. **Send to Victims**
   ```
   Distribute lure URL in emails, messages, etc.
   ```

5. **Monitor in Real-Time**
   ```
   /sessions → View captured credentials, cookies, OTP codes
   /admin/otp_panel.html → Intercept & inject 2FA codes
   ```

## 🔧 Key Features

### Templates Library
- Save clone configurations
- Reuse across multiple users
- Clone modes: `both` (credentials + cookies), `login` (credentials only), `cookies` (session only)
- Browser engines: Playwright (default), Selenium (optional)

### Cookie Capture
- Full cookie jar (domain, path, secure, httponly, samesite, expiry)
- JavaScript cookie interception
- Auth token detection
- Security attribute analysis
- Export to JSON/CSV

### Live OTP Panel
- WebSocket-based real-time communication
- Display victim session details
- Wait for OTP codes (manual or automatic)
- Inject OTP back to victim's browser
- Network activity monitoring

### MITM & Reverse Proxy
- Auto-setup ngrok or cloudflared tunnels
- Reverse proxy all victim traffic
- Automatic cookie + credential capture
- No setup overhead

### Webhook Notifications
- Slack, Discord, custom APIs
- Triggerable on credential submit, OTP received, session created
- JSON, form-encoded, or XML payloads

### Multi-step & 2FA Detection
- Automatic heuristics for complex flows
- OTP endpoint detection
- Manual breakpoints for user interaction
- 2FA indicators in analytics

## 📊 Supported Sites

Works with any login page that uses:
- ✅ HTML forms
- ✅ JavaScript form submission
- ✅ XHR/fetch-based authentication
- ✅ SPA logins (React, Vue, Angular)
- ✅ 2FA/OTP flows
- ✅ Multi-step authentication (Office365, Gmail, GitHub, etc.)

## 🌐 API & CLI

### Web API
```bash
# List templates
curl http://localhost:5000/templates

# Generate lure URL
curl -X POST http://localhost:5000/lure/generate \
  -d "template_id=1"

# View session
curl http://localhost:5000/session/1
```

### CLI Commands
```bash
# Setup
python setup.py                    # Interactive setup

# Tunneling
python core/tunnel_manager.py setup
python core/tunnel_manager.py start --type ngrok

# Database
python core/db_migration.py
```

## 📂 Project Structure

```
SocialFish/
├── SocialFish.py               # Main Flask app
├── setup.py                    # Interactive setup wizard
├── FEATURES_v3.md             # Feature documentation
├── IMPLEMENTATION_SUMMARY.md   # Technical details
├── core/
│   ├── recorder_playwright.py  # Browser automation
│   ├── cookie_inspector.py     # Cookie analysis
│   ├── tunnel_manager.py       # Tunneling support
│   ├── db_migration.py         # Database schema
│   └── ... (other modules)
└── templates/
    └── admin/
        ├── templates.html      # Templates library UI
        ├── otp_panel.html     # OTP interception UI
        ├── sessions.html       # Session management UI
        └── ... (other templates)
```

## 🔐 Security & Ethics

⚠️ **EDUCATIONAL USE ONLY**

- ✅ **Consent Required** — Only test systems you own or have explicit written permission for
- ✅ **Audit Logging** — All operations logged with user attribution
- ✅ **Data Protection** — Implement proper data retention policies
- ✅ **GDPR Compliance** — Comply with local privacy regulations
- ✅ **Disclosure** — Report vulnerabilities responsibly

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [LICENSE](LICENSE) for details.

## 📱 Mobile Controller

Looking for the mobile controller? Check [SocialFishMobile](https://github.com/UndeadSec/SocialFishMobile)

## 👥 Maintainers

- **Alisson Moretto**, Twitter: [@UndeadSec][tw-alisson], GitHub: [@UndeadSec][git-alisson]
- **Vandré Augusto**, Twitter: [@dr1nKoRdi3][tw-drink], GitHub: [@dr1nK0Rdi3][git-drink]

## 📚 Documentation

- **Fernando Bellincanta**, Twitter: [@ErvalhouS][tw-fernando], GitHub: [@ErvalhouS][git-fernando]

## ⚖️ Disclaimer

TO BE USED FOR EDUCATIONAL PURPOSES ONLY

The use of the SocialFish is COMPLETE RESPONSIBILITY of the END-USER. Developers assume NO liability and are NOT responsible for any misuse or damage caused by this program.

"DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."

Taken from [LICENSE](LICENSE).

## 🐳 Docker

Run with Docker:
```bash
docker compose up
```

---

**Status**: Production-ready for authorized security testing and red team exercises

[tw-alisson]: https://twitter.com/UndeadSec
[git-alisson]: https://github.com/UndeadSec
[tw-drink]: https://twitter.com/dr1nKoRdi3
[git-drink]: https://github.com/dr1nK0Rdi3
[tw-fernando]: https://twitter.com/ErvalhouS
[git-fernando]: https://github.com/ErvalhouS
[sf-mobile]: https://github.com/UndeadSec/SocialFishMobile
[sf-sharknet]: https://github.com/UndeadSec/SocialFish/tree/sharkNet

# CONTRIBUTING

[![Open Source Helpers](https://www.codetriage.com/undeadsec/socialfish/badges/users.svg)](https://www.codetriage.com/undeadsec/socialfish)

We encourage you to contribute to SocialFish! Please check out the [Contributing to SocialFish](https://github.com/UndeadSec/SocialFish/blob/master/CONTRIBUTING.md) guide for guidelines about how to proceed. Join us!

# CONTRIBUTOR CODE OF CONDUCT

This project adheres to No Code of Conduct. We are all adults. We accept anyone's contributions. Nothing else matters.

For more information please visit the [No Code of Conduct homepage](https://github.com/domgetter/NCoC).

[//]: # 'links references'
[tw-alisson]: https://twitter.com/UndeadSec
[git-alisson]: https://github.com/UndeadSec
[tw-drink]: https://twitter.com/Dr1nkOrdi3
[git-drink]: https://github.com/dr1nk0rdi3
[sf-mobile]: https://github.com/UndeadSec/SocialFishMobile
[git-tiago]: https://github.com/tiagorlampert
[git-fernando]: https://github.com/ErvalhouS
[tw-fernando]: https://twitter.com/ErvalhouS
[sf-sharknet]: https://github.com/UndeadSec/SocialFish/releases/tag/sharkNet
