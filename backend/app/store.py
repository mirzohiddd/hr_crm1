"""
JSON fayllarda saqlash (ma'lumotlar bazasisiz).

Har bir to‘plam alohida fayl: backend/data/<nom>.json
    employees.json, candidates.json, documents.json, tests.json, test_results.json, users.json,
    departments.json, positions.json, lessons.json, trainings.json, settings.json,
    landing_results.json (nomzodlarning landing test natijalari),
    final_results.json (yakuniy bilim testi natijalari),
    final_participants.json (yakuniy testdan oldin ro‘yxatdan o‘tgan ishtirokchilar)

- Yozuvlar frontend bilan bir xil camelCase ko‘rinishida saqlanadi (fayllarni ochib o‘qish oson).
- Yozish atomik: avval vaqtinchalik faylga, keyin os.replace — server to‘satdan o‘chsa ham fayl buzilmaydi.
- Har yozishda oldingi holat <nom>.json.bak sifatida saqlanadi.
- Bitta jarayon ichida qulf (RLock) bilan himoyalangan; uvicorn'ni bitta worker bilan ishlating.
"""
import copy
import json
import os
import threading
from pathlib import Path

COLLECTIONS = {
    "users": "users.json",
    "departments": "departments.json",
    "positions": "positions.json",
    "employees": "employees.json",
    "candidates": "candidates.json",
    "lessons": "lessons.json",
    "trainings": "trainings.json",
    "tests": "tests.json",
    "test_results": "test_results.json",
    "documents": "documents.json",
    "settings": "settings.json",
    "landing_results": "landing_results.json",
    "final_results": "final_results.json",
    "final_participants": "final_participants.json",
}

_lock = threading.RLock()


class Collection:
    """Bitta JSON fayl: yozuvlar ro‘yxati, har birida butun son `id`."""

    def __init__(self, path: Path):
        self.path = path
        self._rows: list[dict] | None = None

    # ---------- o‘qish / yozish ----------
    def _load(self) -> list[dict]:
        if self._rows is None:
            if self.path.exists():
                text = self.path.read_text(encoding="utf-8").strip()
                self._rows = json.loads(text) if text else []
            else:
                self._rows = []
        return self._rows

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(self._rows, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        if self.path.exists():
            os.replace(self.path, self.path.with_suffix(".json.bak"))
        os.replace(tmp, self.path)

    # ---------- amallar (har biri nusxa qaytaradi) ----------
    def all(self) -> list[dict]:
        with _lock:
            return copy.deepcopy(self._load())

    def filter(self, **match) -> list[dict]:
        with _lock:
            return [copy.deepcopy(r) for r in self._load() if all(r.get(k) == v for k, v in match.items())]

    def first(self, predicate) -> dict | None:
        with _lock:
            for r in self._load():
                if predicate(r):
                    return copy.deepcopy(r)
            return None

    def count(self, **match) -> int:
        with _lock:
            return sum(1 for r in self._load() if all(r.get(k) == v for k, v in match.items()))

    def get(self, item_id: int) -> dict | None:
        return self.first(lambda r: r.get("id") == item_id)

    def insert(self, data: dict) -> dict:
        with _lock:
            rows = self._load()
            row = {**data, "id": max((r.get("id", 0) for r in rows), default=0) + 1}
            rows.append(row)
            self._save()
            return copy.deepcopy(row)

    def update(self, item_id: int, patch: dict) -> dict | None:
        with _lock:
            for i, r in enumerate(self._load()):
                if r.get("id") == item_id:
                    self._rows[i] = {**r, **{k: v for k, v in patch.items() if k != "id"}}
                    self._save()
                    return copy.deepcopy(self._rows[i])
            return None

    def delete(self, item_id: int) -> bool:
        with _lock:
            rows = self._load()
            kept = [r for r in rows if r.get("id") != item_id]
            if len(kept) == len(rows):
                return False
            self._rows = kept
            self._save()
            return True

    def delete_where(self, **match) -> list[dict]:
        with _lock:
            rows = self._load()
            removed = [r for r in rows if all(r.get(k) == v for k, v in match.items())]
            if removed:
                self._rows = [r for r in rows if r not in removed]
                self._save()
            return removed

    def replace_all(self, rows: list[dict]) -> None:
        with _lock:
            self._rows = copy.deepcopy(rows)
            self._save()

    def is_empty(self) -> bool:
        with _lock:
            return not self._load()


class Store:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._collections = {name: Collection(data_dir / file) for name, file in COLLECTIONS.items()}

    def __getattr__(self, name: str) -> Collection:
        try:
            return self._collections[name]
        except KeyError:
            raise AttributeError(name) from None

    def reload(self) -> None:
        """Fayllarni diskdan qayta o‘qish (masalan, qo‘lda tahrirlangandan keyin)."""
        with _lock:
            for c in self._collections.values():
                c._rows = None


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        from .config import DATA_DIR

        _store = Store(DATA_DIR)
    return _store