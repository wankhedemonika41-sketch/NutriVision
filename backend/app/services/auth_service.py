"""
Passwords and login tokens.

 * Passwords are hashed with scrypt (built into Python, no extra package).
 * Login tokens are JWTs (HS256) signed with JWT_SECRET from the .env file.
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("nutrivision.auth")

# ------------------------------------------------------------------
# Password hashing
# ------------------------------------------------------------------

_N, _R, _P = 2 ** 14, 8, 1
_MAXMEM = 64 * 1024 * 1024


def _b64(data):
    return base64.b64encode(data).decode("ascii")


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P,
        dklen=32, maxmem=_MAXMEM)
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(digest)}"


def verify_password(password, stored):
    try:
        scheme, n, r, p, salt, expected = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=base64.b64decode(salt),
            n=int(n), r=int(r), p=int(p),
            dklen=32, maxmem=_MAXMEM)
        return hmac.compare_digest(digest, base64.b64decode(expected))
    except Exception:
        return False


_dummy_hash = None


def burn_time(password):
    """Same work as a real check, so 'unknown email' is not faster."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password(secrets.token_hex(8))
    verify_password(password, _dummy_hash)


# ------------------------------------------------------------------
# Tokens
# ------------------------------------------------------------------

_ALGORITHM = "HS256"
_secret = os.getenv("JWT_SECRET", "").strip()

if len(_secret) < 32:
    _secret = secrets.token_hex(32)
    logger.warning(
        "JWT_SECRET is missing or shorter than 32 characters in .env. "
        "A temporary secret is used, so everyone is logged out whenever "
        "the server restarts.")


def _expire_days():
    try:
        return max(1, int(os.getenv("JWT_EXPIRE_DAYS", "7")))
    except ValueError:
        return 7


def create_token(user_id):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=_expire_days()),
    }
    return jwt.encode(payload, _secret, algorithm=_ALGORITHM)


def read_token(token):
    """Token -> user id, or None if it is invalid / expired."""
    try:
        payload = jwt.decode(token, _secret, algorithms=[_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None


# ------------------------------------------------------------------
# Login throttle (in memory: resets when the server restarts)
# ------------------------------------------------------------------

MAX_FAILS = 5
WINDOW_SECONDS = 300

_fails = {}
_lock = threading.Lock()


def seconds_until_allowed(key):
    """0 if the user may try, otherwise seconds to wait."""
    now = time.time()
    with _lock:
        recent = [t for t in _fails.get(key, []) if now - t < WINDOW_SECONDS]
        _fails[key] = recent
        if len(recent) >= MAX_FAILS:
            return int(WINDOW_SECONDS - (now - recent[0])) + 1
    return 0


def record_failure(key):
    with _lock:
        _fails.setdefault(key, []).append(time.time())


def clear_failures(key):
    with _lock:
        _fails.pop(key, None)


def reset_throttle():
    with _lock:
        _fails.clear()