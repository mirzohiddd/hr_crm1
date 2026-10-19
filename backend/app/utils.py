"""Umumiy yordamchilar: serializatsiya, sana, xatolar."""
import re
from datetime import datetime

from fastapi import HTTPException

HIDDEN = {"passwordHash", "filePath"}


def public(row: dict | None) -> dict | None:
    """Ichki maydonlarsiz (parol xeshi, diskdagi fayl yo‘li) yozuv."""
    if row is None:
        return None
    return {k: v for k, v in row.items() if k not in HIDDEN}


def now_local() -> str:
    """'YYYY-MM-DDTHH:MM' — frontend bilan bir xil format."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def phone_key(value: str | None) -> str:
    digits = re.sub(r"\D", "", value or "")
    return digits[-9:]


# O‘zbekiston raqami: +998 XX XXX XX XX (9 ta milliy raqam, birinchisi 0 emas).
# Ruxsat etilgan belgilar: raqamlar, bo‘sh joy, "+", "-", "(", ")".
_PHONE_CHARS_RE = re.compile(r"^[\d\s+\-()]+$")
PHONE_REQUIRED = "Telefon raqamini kiriting"
PHONE_INVALID = "Telefon raqami noto‘g‘ri. Namuna: +998 90 123 45 67"


def normalize_phone(value: str | None) -> str:
    """
    Telefon raqamini tekshiradi va yagona ko‘rinishga keltiradi: '+998 90 123 45 67'.
    Qabul qilinadi: '+998901234567', '998 90 123-45-67', '(90) 123 45 67', '901234567'.
    Noto‘g‘ri bo‘lsa — ValueError (o‘zbekcha sabab bilan).
    """
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(PHONE_REQUIRED)
    if not _PHONE_CHARS_RE.fullmatch(raw) or raw.count("+") > 1 or ("+" in raw and not raw.startswith("+")):
        raise ValueError(PHONE_INVALID)
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 12 and digits.startswith("998"):
        national = digits[3:]
    elif len(digits) == 9 and not raw.startswith("+"):
        national = digits
    else:
        raise ValueError(PHONE_INVALID)
    if national[0] == "0":
        raise ValueError(PHONE_INVALID)
    return f"+998 {national[:2]} {national[2:5]} {national[5:7]} {national[7:]}"


def not_found(what: str = "Ma’lumot"):
    return HTTPException(status_code=404, detail=f"{what} topilmadi")


def conflict(message: str):
    return HTTPException(status_code=409, detail=message)


def bad_request(message: str):
    return HTTPException(status_code=400, detail=message)


def get_or_404(collection, obj_id: int, what: str = "Ma’lumot") -> dict:
    row = collection.get(obj_id)
    if row is None:
        raise not_found(what)
    return row


def full_name(last: str | None, first: str | None, middle: str | None = None) -> str:
    """O‘zbekcha tartib: Familiya Ism Otasining ismi"""
    return " ".join(p.strip() for p in (last, first, middle) if p and p.strip())


def split_name(name: str | None) -> tuple[str, str, str]:
    parts = (name or "").split()
    return (parts[0] if parts else "", parts[1] if len(parts) > 1 else "", " ".join(parts[2:]))