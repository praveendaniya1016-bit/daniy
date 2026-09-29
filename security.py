import base64
import hashlib
import hmac
import json
import os
import secrets
import time


SESSION_TTL = 60 * 60 * 24 * 7


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${_b64(salt)}${_b64(digest)}"


def verify_password(password, stored):
    try:
        algorithm, salt, expected = stored.split("$", 2)
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(password.encode(), salt=_unb64(salt), n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, _unb64(expected))
    except (ValueError, TypeError):
        return False


def issue_token(user_id):
    now = int(time.time())
    claims = {"sub": str(user_id), "iat": now, "exp": now + SESSION_TTL, "jti": secrets.token_urlsafe(20)}
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps(claims, separators=(",", ":")).encode())
    unsigned = f"{header}.{payload}"
    signature = hmac.new(_secret(), unsigned.encode(), hashlib.sha256).digest()
    return f"{unsigned}.{_b64(signature)}", claims


def decode_token(token):
    try:
        header, payload, signature = token.split(".")
        unsigned = f"{header}.{payload}"
        expected = hmac.new(_secret(), unsigned.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(signature)):
            return None
        claims = json.loads(_unb64(payload))
        if claims.get("exp", 0) <= int(time.time()) or claims.get("sub") is None or claims.get("jti") is None:
            return None
        return claims
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _secret():
    return os.getenv("APP_SECRET", "local-development-secret-change-me").encode()


def _b64(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))