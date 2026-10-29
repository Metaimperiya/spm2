import sqlite3
import os

DB_PATH = "data/bot_database.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT,
        category TEXT, ad_type TEXT, title TEXT, description TEXT, price TEXT, 
        game_id TEXT, contact TEXT, photo_id TEXT, status TEXT DEFAULT 'pending', 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, 
        lang TEXT DEFAULT 'ru', joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def add_ad_to_db(user_id, username, category, ad_type, title, description, price, game_id, contact, photo_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO ads (user_id, username, category, ad_type, title, description, price, game_id, contact, photo_id) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                   (user_id, username, category, ad_type, title, description, price, game_id, contact, photo_id))
    ad_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ad_id

def get_ad_by_id(ad_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def approve_ad(ad_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE ads SET status = "approved" WHERE id = ?', (ad_id,))
    conn.commit()
    conn.close()

def get_approved_ads(category, ad_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ads WHERE status = "approved" AND category = ? AND ad_type = ? ORDER BY id DESC', (category, ad_type))
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_user_to_db(user_id, username, first_name, lang="ru"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, lang) VALUES (?, ?, ?, ?)', (user_id, username, first_name, lang))
    conn.commit()
    conn.close()

def get_user_lang(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT lang FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "ru"

def update_user_lang(user_id, lang):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET lang = ? WHERE user_id = ?', (lang, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]
