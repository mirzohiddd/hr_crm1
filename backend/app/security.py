"""Parollar (PBKDF2-SHA256) va JWT tokenlar."""
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import SECRET_KEY, TOKEN_HOURS
from .store import get_store

ITERATIONS = 260_000
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, digest = stored.split("$")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(iterations))
        return hmac.compare_digest(check, base64.b64decode(digest))
    except Exception:
        return False


def create_token(user: dict) -> str:
    payload = {"sub": str(user["id"]), "role": user["role"], "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    """Har bir himoyalangan so‘rovda token va foydalanuvchi faolligini tekshiradi."""
    if not creds:
        raise HTTPException(status_code=401, detail="Tizimga kiring")
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sessiya muddati tugagan. Qayta kiring.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token noto‘g‘ri")
    user = get_store().users.get(int(payload.get("sub", 0)))
    if not user or not user.get("active", True):
        raise HTTPException(status_code=401, detail="Foydalanuvchi topilmadi yoki bloklangan")
    return user


HR_ROLES = ("admin", "hr")


def hr_user(user: dict = Depends(current_user)) -> dict:
    """Test natijalari kabi maxfiy HR ma'lumotlari: faqat HR xodimi yoki administrator (rol serverda tekshiriladi)."""
    if user.get("role") not in HR_ROLES:
        raise HTTPException(status_code=403, detail="Bu ma’lumot faqat HR xodimlari va administrator uchun")
    return user


def admin_user(user: dict = Depends(current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bu amal faqat administrator uchun")
    return user