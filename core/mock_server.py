#!/usr/bin/env python3
"""
Mock Login Server Simulator
Simulates OAuth, SSO, and password authentication flows for testing.
Generates synthetic credentials, session tokens, and tracks sessions.
"""

import random
import string
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import hashlib
import secrets
from flask import Flask, request, jsonify, redirect, render_template_string, session
from functools import wraps

class MockLoginServer:
    """Simulate various auth flows (OAuth, SSO, password)"""
    
    def __init__(self, port=5001):
        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_hex(32)
        self.port = port
        
        # Session storage
        self.sessions = {}
        self.users = self._generate_mock_users(10)
        self.tokens = {}
        self.auth_flows = {}
        self.password_salt = secrets.token_hex(16)  # Store salt for consistent hashing in demo
        
        # Register routes
        self._register_routes()
    
    def _generate_mock_users(self, count: int) -> List[Dict]:
        """Generate synthetic test users"""
        users = []
        domains = ['example.com', 'test.org', 'demo.net']
        
        for i in range(count):
            users.append({
                'id': str(uuid.uuid4()),
                'username': f'user{i+1}@{random.choice(domains)}',
                'password': self._hash_password(f'password{i+1}'),
                'name': f'Test User {i+1}',
                'email': f'user{i+1}@{random.choice(domains)}',
                'phone': f'+1234567{i:03d}',
                'created_at': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
            })
        
        return users
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt using PBKDF2"""
        # For mock server: use PBKDF2 which is more secure than plain SHA256
        import hashlib
        try:
            # Try to use PBKDF2 (Python 3.7+)
            hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), 
                                        self.password_salt.encode(), 100000)
            return hashed.hex()
        except:
            # Fallback to salted SHA256 for compatibility
            salted = f"{self.password_salt}{password}"
            return hashlib.sha256(salted.encode()).hexdigest()
    
    def _generate_token(self, user_id: str, token_type='access') -> str:
        """Generate JWT-like token"""
        payload = {
            'user_id': user_id,
            'type': token_type,
            'iat': datetime.now().isoformat(),
            'exp': (datetime.now() + timedelta(hours=1)).isoformat()
        }
        token = secrets.token_urlsafe(32)
        self.tokens[token] = payload
        return token
    
    def _register_routes(self):
        """Register mock auth endpoints"""
        
        # Login page
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'GET':
                return render_template_string(self._login_html())
            
            # POST - authenticate
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = next((u for u in self.users if u['username'] == username), None)
            
            if user and user['password'] == self._hash_password(password):
                # Create session
                access_token = self._generate_token(user['id'], 'access')
                refresh_token = self._generate_token(user['id'], 'refresh')
                
                session_id = str(uuid.uuid4())
                self.sessions[session_id] = {
                    'user_id': user['id'],
                    'username': username,
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'created_at': datetime.now().isoformat(),
                    'ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent')
                }
                
                return redirect(f'/dashboard?session={session_id}')
            
            return render_template_string(self._login_html(error='Invalid credentials'))
        
        # Dashboard (protected)
        @self.app.route('/dashboard')
        def dashboard():
            session_id = request.args.get('session')
            if not session_id or session_id not in self.sessions:
                return redirect('/login')
            
            sess = self.sessions[session_id]
            user = next((u for u in self.users if u['id'] == sess['user_id']), None)
            
            return render_template_string(self._dashboard_html(), 
                                        user=user, 
                                        session_id=session_id,
                                        access_token=sess['access_token'])
        
        # OAuth provider - authorization endpoint
        @self.app.route('/oauth/authorize')
        def oauth_authorize():
            client_id = request.args.get('client_id')
            redirect_uri = request.args.get('redirect_uri')
            state = request.args.get('state')
            
            if not all([client_id, redirect_uri, state]):
                return 'Invalid OAuth request', 400
            
            # Store auth flow
            auth_code = secrets.token_urlsafe(32)
            self.auth_flows[auth_code] = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'state': state,
                'created_at': datetime.now().isoformat()
            }
            
            return render_template_string(self._oauth_consent_html(),
                                        client_id=client_id,
                                        state=state,
                                        auth_code=auth_code)
        
        # OAuth provider - token endpoint
        @self.app.route('/oauth/token', methods=['POST'])
        def oauth_token():
            auth_code = request.form.get('code')
            client_id = request.form.get('client_id')
            
            if auth_code not in self.auth_flows:
                return jsonify({'error': 'invalid_code'}), 400
            
            flow = self.auth_flows[auth_code]
            
            # Generate tokens
            access_token = self._generate_token(str(uuid.uuid4()), 'access')
            
            return jsonify({
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': 3600,
                'refresh_token': self._generate_token(str(uuid.uuid4()), 'refresh')
            })
        
        # OAuth - user info endpoint
        @self.app.route('/oauth/userinfo')
        def oauth_userinfo():
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'unauthorized'}), 401
            
            token = auth_header[7:]
            token_data = self.tokens.get(token)
            
            if not token_data:
                return jsonify({'error': 'invalid_token'}), 401
            
            user = next((u for u in self.users if u['id'] == token_data['user_id']), None)
            
            if not user:
                return jsonify({'error': 'user_not_found'}), 404
            
            return jsonify({
                'id': user['id'],
                'username': user['username'],
                'name': user['name'],
                'email': user['email'],
                'phone': user['phone']
            })
        
        # SSO - SAML-like endpoint
        @self.app.route('/sso/login', methods=['POST'])
        def sso_login():
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = next((u for u in self.users if u['username'] == username), None)
            
            if user and user['password'] == self._hash_password(password):
                sso_token = self._generate_token(user['id'], 'sso')
                return jsonify({
                    'status': 'success',
                    'sso_token': sso_token,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email']
                    }
                })
            
            return jsonify({'status': 'failed', 'error': 'Invalid credentials'}), 401
        
        # 2FA endpoint
        @self.app.route('/2fa/request')
        def mfa_request():
            session_id = request.args.get('session_id')
            if session_id not in self.sessions:
                return {'error': 'Invalid session'}, 400
            
            # Generate OTP
            otp = ''.join(random.choices(string.digits, k=6))
            
            self.sessions[session_id]['otp'] = otp
            self.sessions[session_id]['otp_issued_at'] = datetime.now().isoformat()
            
            # In real scenario, would send via SMS/email
            return jsonify({
                'status': 'otp_sent',
                'message': f'OTP sent to registered email (OTP for testing: {otp})',
                'session_id': session_id
            })
        
        # Verify 2FA
        @self.app.route('/2fa/verify', methods=['POST'])
        def mfa_verify():
            session_id = request.form.get('session_id')
            otp = request.form.get('otp')
            
            if session_id not in self.sessions:
                return {'error': 'Invalid session'}, 400
            
            sess = self.sessions[session_id]
            
            if sess.get('otp') == otp:
                sess['mfa_verified'] = True
                return redirect(f'/dashboard?session={session_id}')
            
            return render_template_string(self._mfa_html(error='Invalid OTP'),
                                        session_id=session_id)
        
        # API - get sessions (for testing)
        @self.app.route('/api/sessions')
        def api_sessions():
            return jsonify({
                'sessions': list(self.sessions.values())
            })
        
        # API - get users (for testing)
        @self.app.route('/api/users')
        def api_users():
            return jsonify({
                'users': [
                    {k: v for k, v in u.items() if k != 'password'}
                    for u in self.users
                ]
            })
    
    def _login_html(self, error=''):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mock Login - Test Server</title>
            <style>
                body { font-family: Arial; background: #f5f5f5; }
                .login-box { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h2 { text-align: center; }
                .form-group { margin: 15px 0; }
                label { display: block; margin-bottom: 5px; }
                input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                button { width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
                .error { color: red; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h2>Mock Login Server</h2>
                <p style="text-align: center; color: #666;">Test your phishing clones here</p>
                {% if error %}<div class="error">{{ error }}</div>{% endif %}
                <form method="POST">
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" name="username" required>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit">Login</button>
                </form>
                <hr>
                <p style="font-size: 0.9em; color: #999;">Test credentials: user1@example.com / password1</p>
            </div>
        </body>
        </html>
        '''
    
    def _dashboard_html(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Mock Login</title>
            <style>
                body { font-family: Arial; margin: 0; background: #f5f5f5; }
                nav { background: #333; color: white; padding: 15px; }
                .container { max-width: 800px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; }
                .user-info { background: #e8f5e9; padding: 15px; border-radius: 4px; margin: 15px 0; }
                code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <nav>
                <h2>Dashboard</h2>
            </nav>
            <div class="container">
                <h3>Welcome, {{ user.name }}!</h3>
                <div class="user-info">
                    <p><strong>Username:</strong> {{ user.username }}</p>
                    <p><strong>Email:</strong> {{ user.email }}</p>
                    <p><strong>User ID:</strong> <code>{{ user.id }}</code></p>
                    <p><strong>Access Token:</strong> <code>{{ access_token[:20] }}...</code></p>
                </div>
                <p>You have successfully logged in to the mock server.</p>
            </div>
        </body>
        </html>
        '''
    
    def _oauth_consent_html(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Consent</title></head>
        <body>
            <h2>App Requests Permission</h2>
            <p>Application is requesting access to your profile.</p>
            <form action="/oauth/callback" method="POST">
                <input type="hidden" name="auth_code" value="{{ auth_code }}">
                <input type="hidden" name="state" value="{{ state }}">
                <button type="submit">Allow</button>
            </form>
        </body>
        </html>
        '''
    
    def _mfa_html(self, error=''):
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>2FA Verification</title></head>
        <body>
            <h2>Verify Your Identity</h2>
            <p>Enter the OTP code sent to your email:</p>
            {% if error %}<p style="color: red;">{{ error }}</p>{% endif %}
            <form method="POST">
                <input type="hidden" name="session_id" value="{{ session_id }}">
                <input type="text" name="otp" placeholder="000000" required>
                <button type="submit">Verify</button>
            </form>
        </body>
        </html>
        '''
    
    def run(self):
        """Start the mock server"""
        print(f"[+] Mock Login Server running on http://localhost:{self.port}")
        print("[+] Test endpoints:")
        print(f"    - Basic login: http://localhost:{self.port}/login")
        print(f"    - OAuth: http://localhost:{self.port}/oauth/authorize")
        print(f"    - SSO: http://localhost:{self.port}/sso/login")
        print(f"    - API users: http://localhost:{self.port}/api/users")
        print(f"    - API sessions: http://localhost:{self.port}/api/sessions")
        
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mock Login Server')
    parser.add_argument('--port', type=int, default=5001, help='Port to run on')
    
    args = parser.parse_args()
    
    server = MockLoginServer(port=args.port)
    server.run()

if __name__ == '__main__':
    main()
