import sqlite3

conn = sqlite3.connect("database.db", check_same_thread=False)
cur = conn.cursor()

# Tables
cur.execute("CREATE TABLE IF NOT EXISTS movies(code TEXT PRIMARY KEY, file_id TEXT, name TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(channel TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS users(user_id TEXT PRIMARY KEY, username TEXT)")
conn.commit()

# Movies
def add_movie(code, file_id, name):
    cur.execute("INSERT OR REPLACE INTO movies VALUES(?,?,?)", (code, file_id, name))
    conn.commit()

def del_movie(code):
    cur.execute("DELETE FROM movies WHERE code=?", (code,))
    conn.commit()

def get_movie(code):
    cur.execute("SELECT file_id,name FROM movies WHERE code=?", (code,))
    return cur.fetchone()

# Channels
def add_channel(channel):
    cur.execute("INSERT OR IGNORE INTO channels VALUES(?)", (channel,))
    conn.commit()

def del_channel(channel):
    cur.execute("DELETE FROM channels WHERE channel=?", (channel,))
    conn.commit()

def get_all_channels():
    cur.execute("SELECT channel FROM channels")
    return [i[0] for i in cur.fetchall()]

# Users
def add_user(user_id, username):
    cur.execute("INSERT OR IGNORE INTO users VALUES(?,?)", (user_id, username))
    conn.commit()

def get_all_users():
    cur.execute("SELECT user_id, username FROM users")
    return cur.fetchall()
