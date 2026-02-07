#!/usr/bin/env python3
"""
Cookie inspector for analyzing and capturing cookies from login flows.
Provides detailed metadata and heuristics detection.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Set
from collections import defaultdict

class CookieInspector:
    """Analyze and track cookies with detailed metadata"""
    
    def __init__(self, database_path="./database.db"):
        self.db_path = database_path
        self.cookies_by_step = defaultdict(list)
        self.heuristics = {}
    
    def analyze_cookies(self, cookies: List[Dict]) -> Dict:
        """Analyze cookie set for patterns and security attributes"""
        
        if not cookies:
            return {'total': 0, 'warnings': ['No cookies captured']}
        
        analysis = {
            'total_cookies': len(cookies),
            'persistent_cookies': 0,
            'session_cookies': 0,
            'secure_cookies': 0,
            'httponly_cookies': 0,
            'samesite_cookies': 0,
            'cross_domain_cookies': set(),
            'unique_domains': set(),
            'unique_paths': set(),
            'suspicious_cookies': [],
            'session_tokens': [],
            'warnings': [],
            'recommendations': []
        }
        
        for cookie in cookies:
            domain = cookie.get('domain', 'unknown')
            name = cookie.get('name', 'unknown')
            
            # Count security attributes
            if cookie.get('expires'):
                analysis['persistent_cookies'] += 1
            else:
                analysis['session_cookies'] += 1
            
            if cookie.get('secure'):
                analysis['secure_cookies'] += 1
            
            if cookie.get('httponly'):
                analysis['httponly_cookies'] += 1
            
            if cookie.get('samesite'):
                analysis['samesite_cookies'] += 1
            
            # Track domains and paths
            analysis['unique_domains'].add(domain)
            analysis['unique_paths'].add(cookie.get('path', '/'))
            
            # Detect session/auth tokens
            token_keywords = ['session', 'token', 'auth', 'jwt', 'bearer', 'access_token', 'refresh_token', 'sid', 'id']
            if any(keyword in name.lower() for keyword in token_keywords):
                analysis['session_tokens'].append({
                    'name': name,
                    'domain': domain,
                    'secure': cookie.get('secure'),
                    'httponly': cookie.get('httponly')
                })
            
            # Detect suspicious patterns
            if not cookie.get('secure') and domain not in ['localhost', '127.0.0.1']:
                analysis['suspicious_cookies'].append(f"Insecure cookie: {name} on {domain}")
            
            if not cookie.get('httponly'):
                analysis['suspicious_cookies'].append(f"HttpOnly not set: {name} (vulnerable to XSS)")
            
            if cookie.get('samesite') == 'None' or not cookie.get('samesite'):
                analysis['suspicious_cookies'].append(f"No SameSite: {name} (vulnerable to CSRF)")
        
        # Convert sets to lists for JSON serialization
        analysis['unique_domains'] = list(analysis['unique_domains'])
        analysis['unique_paths'] = list(analysis['unique_paths'])
        analysis['cross_domain_cookies'] = list(analysis['cross_domain_cookies'])
        
        # Generate warnings
        if analysis['session_cookies'] == 0 and analysis['persistent_cookies'] > 0:
            analysis['recommendations'].append("No session cookies detected - may be persistent login only")
        
        if not analysis['session_tokens']:
            analysis['recommendations'].append("No obvious auth tokens detected - verify login was successful")
        
        if analysis['total_cookies'] > 50:
            analysis['warnings'].append(f"High cookie count ({analysis['total_cookies']}) - may indicate tracking cookies")
        
        return analysis
    
    def detect_2fa_indicators(self, cookies: List[Dict], network_logs: List[Dict]) -> Dict:
        """Detect indicators of 2FA/OTP requirements"""
        
        indicators = {
            'has_2fa': False,
            'indicators': [],
            'otp_endpoints': [],
            'otp_input_selectors': [],
            'suspicious_redirects': []
        }
        
        # Check network logs for 2FA patterns
        for log in network_logs:
            url = log.get('request', {}).get('url', '').lower()
            
            # Check URLs for 2FA/OTP patterns
            otp_keywords = ['/mfa/', '/2fa/', '/otp/', '/twofa/', '/verify/', '/challenge/', '/sms/', '/sms-verify', '/twoFactorAuth']
            if any(keyword in url for keyword in otp_keywords):
                indicators['has_2fa'] = True
                indicators['otp_endpoints'].append(url)
                indicators['indicators'].append(f"Detected 2FA endpoint: {url}")
        
        # Check for OTP-like input fields in captured forms
        # This would require form data - simplified check here
        indicators['indicators'].append("Run form analyzer to detect OTP input fields")
        
        return indicators
    
    def detect_login_step_cookies(self, cookies_before: List[Dict], cookies_after: List[Dict]) -> List[Dict]:
        """Detect cookies that changed during login step"""
        
        before_set = {(c['name'], c['domain']) for c in cookies_before}
        after_set = {(c['name'], c['domain']) for c in cookies_after}
        
        new_cookies = after_set - before_set
        removed_cookies = before_set - after_set
        
        step_changes = {
            'new_cookies': list(new_cookies),
            'removed_cookies': list(removed_cookies),
            'likely_auth_cookies': []
        }
        
        # Identify auth cookies
        for cookie in cookies_after:
            if (cookie['name'], cookie['domain']) in new_cookies:
                if any(keyword in cookie['name'].lower() for keyword in ['session', 'token', 'auth']):
                    step_changes['likely_auth_cookies'].append(cookie['name'])
        
        return step_changes
    
    def export_cookies_json(self, cookies: List[Dict], filename: str = None) -> str:
        """Export cookies to JSON file"""
        
        if not filename:
            filename = f"cookies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'cookie_count': len(cookies),
            'cookies': cookies
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return filename
    
    def export_cookies_csv(self, cookies: List[Dict], filename: str = None) -> str:
        """Export cookies to CSV file"""
        import csv
        
        if not filename:
            filename = f"cookies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if not cookies:
            print("[-] No cookies to export")
            return None
        
        with open(filename, 'w', newline='') as f:
            fieldnames = ['name', 'value', 'domain', 'path', 'secure', 'httponly', 'samesite', 'expires']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for cookie in cookies:
                writer.writerow({
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'domain': cookie.get('domain'),
                    'path': cookie.get('path'),
                    'secure': cookie.get('secure'),
                    'httponly': cookie.get('httponly'),
                    'samesite': cookie.get('samesite'),
                    'expires': cookie.get('expires')
                })
        
        return filename
    
    def store_cookies_in_db(self, session_id: int, cookies: List[Dict]):
        """Store cookies in database"""
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        for cookie in cookies:
            cur.execute("""
                INSERT INTO cookies(session_id, name, value, domain, path, secure, httponly, samesite, expires)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                cookie.get('name'),
                cookie.get('value'),
                cookie.get('domain'),
                cookie.get('path'),
                cookie.get('secure'),
                cookie.get('httponly'),
                cookie.get('samesite'),
                cookie.get('expires')
            ))
        
        conn.commit()
        conn.close()
        
        print(f"[+] Stored {len(cookies)} cookies in database")
    
    def get_session_cookies(self, session_id: int) -> List[Dict]:
        """Retrieve cookies for a session"""
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT name, value, domain, path, secure, httponly, samesite, expires
            FROM cookies WHERE session_id = ?
        """, (session_id,))
        
        rows = cur.fetchall()
        conn.close()
        
        cookies = []
        for row in rows:
            cookies.append({
                'name': row[0],
                'value': row[1],
                'domain': row[2],
                'path': row[3],
                'secure': row[4],
                'httponly': row[5],
                'samesite': row[6],
                'expires': row[7]
            })
        
        return cookies
    
    def generate_cookie_report(self, session_id: int) -> Dict:
        """Generate comprehensive cookie analysis report"""
        
        cookies = self.get_session_cookies(session_id)
        analysis = self.analyze_cookies(cookies)
        
        report = {
            'session_id': session_id,
            'generated_at': datetime.now().isoformat(),
            'analysis': analysis,
            'cookies': cookies
        }
        
        return report

def main():
    """CLI test"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cookie Inspector')
    subparsers = parser.add_subparsers(dest='command')
    
    analyze_parser = subparsers.add_parser('analyze', help='Analyze cookies')
    analyze_parser.add_argument('--session-id', type=int, help='Session ID')
    
    export_parser = subparsers.add_parser('export', help='Export cookies')
    export_parser.add_argument('--session-id', type=int, help='Session ID')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json')
    
    args = parser.parse_args()
    
    inspector = CookieInspector()
    
    if args.command == 'analyze' and args.session_id:
        report = inspector.generate_cookie_report(args.session_id)
        print(json.dumps(report, indent=2))
    elif args.command == 'export' and args.session_id:
        cookies = inspector.get_session_cookies(args.session_id)
        if args.format == 'json':
            filename = inspector.export_cookies_json(cookies)
        else:
            filename = inspector.export_cookies_csv(cookies)
        print(f"[+] Exported to {filename}")

if __name__ == "__main__":
    main()
