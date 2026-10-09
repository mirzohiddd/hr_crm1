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
