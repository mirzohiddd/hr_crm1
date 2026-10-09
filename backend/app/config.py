"""Sozlamalar: .env fayldan yoki muhit o‘zgaruvchilaridan o‘qiladi."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


def _load_env_file() -> None:
    """backend/.env faylini o‘qish (qo‘shimcha kutubxonasiz)."""
    env = BASE_DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


def _secret_key() -> str:
    """SECRET_KEY berilmasa — bir marta yaratiladi va backend/.secret_key da saqlanadi."""
    key = os.getenv("SECRET_KEY")
    if key:
        return key
    path = BASE_DIR / ".secret_key"
    if path.exists():
        return path.read_text().strip()
    key = secrets.token_urlsafe(48)
    path.write_text(key)
    return key


# Ma'lumotlar JSON fayllarda saqlanadi (employees.json, candidates.json, ...)
DATA_DIR = Path(os.getenv("DATA_DIR") or str(BASE_DIR / "data"))
# Oldingi versiyadagi SQLite fayli — mavjud bo‘lsa, birinchi ishga tushirishda JSON ga ko‘chiriladi
LEGACY_SQLITE = BASE_DIR / "hr_crm.db"
SECRET_KEY = _secret_key()
TOKEN_HOURS = int(os.getenv("TOKEN_HOURS") or 12)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR") or str(BASE_DIR / "uploads"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB") or 10)
CORS_ORIGINS = [o.strip() for o in (os.getenv("CORS_ORIGINS") or "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]

# Birinchi ishga tushirishda yaratiladigan administrator
ADMIN_LOGIN = os.getenv("ADMIN_LOGIN") or "admin"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or "admin123"
ADMIN_NAME = os.getenv("ADMIN_NAME") or "Administrator"

# Frontend build (frontend/dist) — mavjud bo‘lsa backend uni ham ochib beradi
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST") or str(BASE_DIR.parent / "frontend" / "dist"))
# Yakuniy bilim testi (landing-2/) build papkasi — mavjud bo‘lsa, backend uni /test/yakuniy da ochadi
LANDING2_DIST = Path(os.getenv("LANDING2_DIST") or str(BASE_DIR.parent / "landing-2" / "dist"))

# Nomzodlar testi (landing/) build papkasi — mavjud bo‘lsa, backend uni /test/ da ochadi
LANDING_DIST = Path(os.getenv("LANDING_DIST") or str(BASE_DIR.parent / "landing" / "dist"))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
