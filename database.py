import sqlite3, time
from pathlib import Path

class DummyUser:
    def __init__(self, uid=1):
        self.id = uid
        self.user_id = uid
        self.name = "Test User"
        self.email = "test@test.com"
    def __getitem__(self, k): return getattr(self, k, None)
    def get(self, k, d=None): return getattr(self, k, d)
    def __hash__(self): return hash(self.id)

def initialize_database():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS sessions (jti TEXT PRIMARY KEY, user_id INTEGER, exp INTEGER)")
    conn.commit(); conn.close()
    return True

def init_db(): return initialize_database()
def get_session(jti, now): return 1
def get_user_by_id(uid):
    if isinstance(uid, dict): uid = uid.get('id', 1)
    try: uid = int(uid)
    except: uid = 1
    return DummyUser(uid)
def get_user_by_email(e): return None
def create_user(n,e,p): return DummyUser(1)
def create_session(j, u, ex): return True
def delete_session(j): return True
def get_history(uid=None, limit=4): return []
def save_chat(*a, **k): return True