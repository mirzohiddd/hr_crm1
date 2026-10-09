"""
Oldingi versiyadagi SQLite bazasidan (backend/hr_crm.db) JSON fayllarga bir martalik ko‘chirish.

Server ishga tushganda avtomatik chaqiriladi: hr_crm.db mavjud va JSON fayllar hali bo‘sh bo‘lsa,
barcha yozuvlar JSON ga ko‘chiriladi, so‘ng baza fayli hr_crm.db.migrated deb qayta nomlanadi
(o‘chirilmaydi — zaxira sifatida qoladi). Qo‘lda: python -m app.migrate_sqlite
Faqat Python standart kutubxonasi (sqlite3) ishlatiladi.
"""
import json
import re
import sqlite3
from pathlib import Path

from .store import Store

# SQLite jadvali → JSON to‘plami
TABLES = {
    "users": "users",
    "departments": "departments",
    "positions": "positions",
    "employees": "employees",
    "candidates": "candidates",
    "lessons": "lessons",
    "trainings": "trainings",
    "tests": "tests",
    "test_results": "test_results",
    "documents": "documents",
    "test_settings": "settings",
}
JSON_COLUMNS = {"history", "completed_days", "position_ids", "questions", "attempts"}
BOOL_COLUMNS = {"active", "shuffle_questions", "shuffle_options", "auto_assign", "activate_on_pass"}


def _camel(name: str) -> str:
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), name)


def _convert(column: str, value):
    if column in JSON_COLUMNS and isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return []
    if column in BOOL_COLUMNS and value is not None:
        return bool(value)
    return value


def migrate(db_path: Path, store: Store) -> dict[str, int]:
    """Ko‘chirilgan yozuvlar soni (to‘plam bo‘yicha)."""
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    existing = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    counts = {}
    for table, collection in TABLES.items():
        if table not in existing:
            continue
        rows = [
            {_camel(k): _convert(k, row[k]) for k in row.keys()}
            for row in con.execute(f'SELECT * FROM "{table}" ORDER BY id')
        ]
        getattr(store, collection).replace_all(rows)
        counts[collection] = len(rows)
    con.close()
    return counts


def migrate_if_needed(store: Store, db_path: Path) -> dict[str, int] | None:
    """hr_crm.db bo‘lsa va JSON ma'lumotlar hali yo‘q bo‘lsa — ko‘chiradi."""
    if not db_path.exists():
        return None
    has_json_data = any(not getattr(store, c).is_empty() for c in ("users", "employees", "candidates"))
    if has_json_data:
        return None
    counts = migrate(db_path, store)
    db_path.rename(db_path.with_suffix(".db.migrated"))
    return counts


if __name__ == "__main__":
    from .config import LEGACY_SQLITE
    from .store import get_store

    result = migrate_if_needed(get_store(), LEGACY_SQLITE)
    print(result or "Ko‘chirish kerak emas (hr_crm.db yo‘q yoki JSON fayllarda ma'lumot bor).")
