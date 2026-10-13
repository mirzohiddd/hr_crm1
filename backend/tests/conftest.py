"""
Backend testlari uchun umumiy sozlamalar.

Testlar vaqtinchalik papkadagi JSON fayllar bilan ishlaydi — backend/data ga tegilmaydi.
Ishga tushirish (backend papkasida):
    pip install -r requirements.txt pytest httpx
    python -m pytest tests -q
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# app import qilinishidan OLDIN: alohida ma'lumotlar papkasi, kalit va administrator paroli
_TMP = tempfile.mkdtemp(prefix="hr-crm-tests-")
os.environ["DATA_DIR"] = _TMP
os.environ["UPLOAD_DIR"] = str(Path(_TMP) / "uploads")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-0123456789")
os.environ["ADMIN_LOGIN"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin12345"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.routers import final_test as final_router  # noqa: E402
from app.routers import landing as landing_router  # noqa: E402

API = "/api/v1"


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # lifespan: seed (administrator va ma'lumotnomalar)
        yield c


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    final_router._hits.clear()
    landing_router._hits.clear()
    yield


@pytest.fixture(scope="session")
def hr_headers(client):
    r = client.post(f"{API}/auth/login", json={"login": "admin", "password": "admin12345"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
