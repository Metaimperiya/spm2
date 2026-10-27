import sqlite3
import json
import os

DB_PATH = "data/bot_database.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Таблица объявлений
    cursor.execute('''CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, category TEXT, ad_type TEXT,
        title TEXT, description TEXT, price TEXT, game_id TEXT, contact TEXT, photo_id TEXT,
        status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # Таблица настроек (каналы)
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    # Добавляем каналы по умолчанию
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('channels', json.dumps({
        "main": "@cpm_2_clan", "sale": "@cpm_2_sale", "trade": "@cpm_2_trade",
        "sell_acc": "@Sell_CPM_2_accounts", "buy_acc": "@BuyCPM2accounts"
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

def add_ad_to_db(user_id, category, ad_type, title, description, price, game_id, contact, photo_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO ads (user_id, category, ad_type, title, description, price, game_id, contact, photo_id) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                   (user_id, category, ad_type, title, description, price, game_id, contact, photo_id))
    ad_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ad_id
