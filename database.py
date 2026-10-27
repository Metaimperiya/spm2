import sqlite3
import json
from datetime import datetime

DB_PATH = "data/bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Таблица объявлений
    cursor.execute('''CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        ad_type TEXT,
        title TEXT,
        description TEXT,
        price TEXT,
        game_id TEXT,
        contact TEXT,
        photo_id TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Таблица заявок на гонки
    cursor.execute('''CREATE TABLE IF NOT EXISTS races (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        game_nick TEXT,
        game_id TEXT,
        car_class TEXT,
        photo_id TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Таблица настроек (для каналов)
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # Дефолтные каналы
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('channels', json.dumps({
        "main": "@cpm_2_clan",
        "sale": "@cpm_2_sale",
        "trade": "@cpm_2_trade",
        "sell_acc": "@Sell_CPM_2_accounts",
        "buy_acc": "@BuyCPM2accounts"
    })))
    
    conn.commit()
    conn.close()

def get_channels():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = "channels"')
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}

def add_ad(user_id, category, ad_type, title, description, price, game_id, contact, photo_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO ads (user_id, category, ad_type, title, description, price, game_id, contact, photo_id, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')''', 
                   (user_id, category, ad_type, title, description, price, game_id, contact, photo_id))
    ad_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ad_id

def approve_ad(ad_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE ads SET status = "published" WHERE id = ?', (ad_id,))
    conn.commit()
    conn.close()
