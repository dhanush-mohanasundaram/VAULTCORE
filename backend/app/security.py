import hashlib
import json
import time
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from app.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Fail fast at startup if the secret is missing, too short, or still the default.
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY must be at least 32 characters")
if SECRET_KEY in ("dev-secret-change-me", "change-me-in-production", "secret"):
    raise RuntimeError("SECRET_KEY must not be a default value")

pwd_context = PasswordHasher()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(hashed_password, plain_password)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


# Simple in-process login rate limiter: per (ip, email) pair.
# Stores timestamps of failed attempts; blocks after 5 failures within 300 seconds.
_LOGIN_ATTEMPTS: dict[tuple[str, str], list[float]] = {}
_LOGIN_LIMIT = 5
_LOGIN_WINDOW = 300  # seconds


def register_login_attempt(identifier: str, success: bool) -> None:
    now = time.time()
    key = identifier
    attempts = _LOGIN_ATTEMPTS.get(key, [])
    attempts = [t for t in attempts if now - t < _LOGIN_WINDOW]
    if not success:
        attempts.append(now)
    _LOGIN_ATTEMPTS[key] = attempts


def is_login_rate_limited(identifier: str) -> bool:
    now = time.time()
    attempts = _LOGIN_ATTEMPTS.get(identifier, [])
    attempts = [t for t in attempts if now - t < _LOGIN_WINDOW]
    _LOGIN_ATTEMPTS[identifier] = attempts
    return len(attempts) >= _LOGIN_LIMIT


def login_rate_limit_key(client_host: str | None, email: str) -> str:
    host = client_host or "unknown"
    email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
    return f"login:{host}:{email_hash}"


def _hash_body(body: dict | None) -> str:
    return hashlib.sha256(json.dumps(body or {}, sort_keys=True).encode()).hexdigest()
