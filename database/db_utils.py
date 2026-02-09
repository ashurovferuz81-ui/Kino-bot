import sqlite3

DB_PATH = "database/database.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS movies(code TEXT PRIMARY KEY, file_id TEXT, name TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(channel_id TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS users(user_id TEXT PRIMARY KEY)")
conn.commit()

def add_movie(code, file_id, name):
    cur.execute("INSERT OR REPLACE INTO movies VALUES(?,?,?)", (code, file_id, name))
    conn.commit()

def del_movie(code):
    cur.execute("DELETE FROM movies WHERE code=?", (code,))
    conn.commit()

def get_movie(code):
    cur.execute("SELECT file_id,name FROM movies WHERE code=?", (code,))
    return cur.fetchone()

def add_channel(channel_id):
    cur.execute("INSERT OR IGNORE INTO channels VALUES(?)", (channel_id,))
    conn.commit()

def del_channel(channel_id):
    cur.execute("DELETE FROM channels WHERE channel_id=?", (channel_id,))
    conn.commit()

def get_all_channels():
    cur.execute("SELECT channel_id FROM channels")
    return [i[0] for i in cur.fetchall()]

def add_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    conn.commit()

def total_users():
    cur.execute("SELECT COUNT(*) FROM users")
    return cur.fetchone()[0]
