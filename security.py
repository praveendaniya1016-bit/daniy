def decode_token(t):
    if not t: return None
    return {"jti": "dummy123", "sub": 1, "exp": 9999999999}
def create_access_token(d): return "dummy_token"
def hash_password(p): return p
def verify_password(p,h): return True
SESSION_TTL = 3600