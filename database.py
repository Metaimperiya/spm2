import sqlite3
import os

DB_PATH = "data/bot_database.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        category TEXT,
        ad_type TEXT,
        title TEXT,
        description TEXT,
        price TEXT,
        game_id TEXT,
        contact TEXT,
        photo_id TEXT,
        media_type TEXT DEFAULT 'photo',
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute("PRAGMA table_info(ads)")
    ad_columns = [row[1] for row in cursor.fetchall()]
    if "media_type" not in ad_columns:
        cursor.execute("ALTER TABLE ads ADD COLUMN media_type TEXT DEFAULT 'photo'")

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        language TEXT DEFAULT 'ru',
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cursor.fetchall()]
    if "language" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ru'")

    conn.commit()
    conn.close()

def add_ad_to_db(user_id, username, category, ad_type, title, description, price, game_id, contact, photo_id, media_type="photo"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO ads (user_id, username, category, ad_type, title, description, price, game_id, contact, photo_id, media_type)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (user_id, username, category, ad_type, title, description, price, game_id, contact, photo_id, media_type))
    ad_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ad_id

def get_ad_by_id(ad_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, username, category, ad_type, title, description, price, game_id, contact, photo_id, media_type FROM ads WHERE id = ?', (ad_id,))
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
    cursor.execute('SELECT id, user_id, username, category, ad_type, title, description, price, game_id, contact, photo_id, media_type FROM ads WHERE status = "approved" AND category = ? AND ad_type = ? ORDER BY id DESC', (category, ad_type))
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_user_to_db(user_id, username, first_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)', (user_id, username, first_name))
    is_new_user = cursor.rowcount == 1
    if not is_new_user:
        cursor.execute(
            'UPDATE users SET username = ?, first_name = ? WHERE user_id = ?',
            (username, first_name, user_id),
        )
    conn.commit()
    conn.close()
    return is_new_user

def get_user_language(user_id, default="ru"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else default

def set_user_language(user_id, language):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


