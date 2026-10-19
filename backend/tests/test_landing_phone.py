"""
Landing (/test/sotuv) — telefon raqami: majburiy, formati tekshiriladi, bitta raqam bilan faqat bitta natija.
Tekshiruv uch joyda: /phone-check (savollardan oldin), /submit (sxema + 409) va saqlash qatlami (insert_unique).
"""
import threading

import pytest

from app import landing
from app.store import get_store
from app.utils import normalize_phone, phone_key

from .conftest import API
from .test_landing_persona import SAMPLE, answers_for, as_json, candidate

CHECK = f"{API}/public/tests/sotuv/phone-check"
SUBMIT = f"{API}/public/tests/sotuv/submit"


@pytest.fixture(scope="module")
def cfg():
    return landing.load_questionnaire("sotuv")


def body(cfg, **over):
    return {**candidate(**over), "answers": as_json(answers_for(cfg, SAMPLE))}


# ---------- Formatlash ----------
@pytest.mark.parametrize("raw", ["+998901234567", "+998 90 123 45 67", "998 (90) 123-45-67", "901234567", "90 123 45 67", "  +998 90 1234567 "])
def test_normalize_valid(raw):
    assert normalize_phone(raw) == "+998 90 123 45 67"


@pytest.mark.parametrize("raw, message", [
    ("", "Telefon raqamini kiriting"),
    ("   ", "Telefon raqamini kiriting"),
    (None, "Telefon raqamini kiriting"),
    ("90123", "noto‘g‘ri"),
    ("+99890123456", "noto‘g‘ri"),            # 11 ta raqam
    ("+9989012345678", "noto‘g‘ri"),          # 13 ta raqam
    ("+7 901 234 56 78", "noto‘g‘ri"),        # boshqa davlat
    ("+901234567", "noto‘g‘ri"),              # "+" bilan, lekin 998 siz
    ("998 012 345 678", "noto‘g‘ri"),         # 0 bilan boshlanadigan milliy raqam
    ("90abc1234567", "noto‘g‘ri"),            # harflar
    ("90 123 45 67+", "noto‘g‘ri"),           # "+" o‘rtada/oxirida
])
def test_normalize_invalid(raw, message):
    with pytest.raises(ValueError, match=message):
        normalize_phone(raw)


# ---------- /phone-check ----------
def test_check_free_number(client):
    r = client.post(CHECK, json={"phone": "+998 97 000 00 01"})
    assert r.status_code == 200, r.text
    assert r.json() == {"phone": "+998 97 000 00 01", "available": True}


@pytest.mark.parametrize("phone", ["", "12345", "+7 901 234 56 78"])
def test_check_invalid_number(client, phone):
    r = client.post(CHECK, json={"phone": phone})
    assert r.status_code == 422
    assert "Telefon raqami" in r.json()["detail"][0]["msg"]


def test_check_missing_field(client):
    r = client.post(CHECK, json={})
    assert r.status_code == 422 and "Telefon raqamini kiriting" in r.json()["detail"][0]["msg"]


def test_check_unknown_test(client):
    assert client.post(f"{API}/public/tests/yoq-test/phone-check", json={"phone": "+998970000002"}).status_code == 404


# ---------- /submit ----------
def test_submit_requires_phone(client, cfg):
    data = body(cfg)
    data.pop("phone")
    r = client.post(SUBMIT, json=data)
    assert r.status_code == 422 and "Telefon raqamini kiriting" in r.json()["detail"][0]["msg"]
    r = client.post(SUBMIT, json={**data, "phone": "   "})
    assert r.status_code == 422


def test_submit_rejects_invalid_phone(client, cfg):
    r = client.post(SUBMIT, json=body(cfg, phone="+998 90 12"))
    assert r.status_code == 422 and "noto‘g‘ri" in r.json()["detail"][0]["msg"]


def test_duplicate_phone_rejected_in_any_format(client, cfg, hr_headers):
    first = client.post(SUBMIT, json=body(cfg, fullName="Aliyev Vali", phone="+998 99 555 11 22"))
    assert first.status_code == 201, first.text
    row = client.get(f"{API}/landing-results/{first.json()['id']}", headers=hr_headers).json()
    assert row["phone"] == "+998 99 555 11 22"  # yagona ko‘rinishda saqlanadi

    # Boshqa odam, boshqa brauzer, boshqacha yozilgan o‘sha raqam — rad etiladi
    for same in ("+998995551122", "995551122", "998 (99) 555-11-22"):
        r = client.post(SUBMIT, json=body(cfg, fullName="Karimova Nodira", phone=same))
        assert r.status_code == 409, (same, r.text)
        assert "avval ro‘yxatdan o‘tilgan" in r.json()["detail"]
        c = client.post(CHECK, json={"phone": same})
        assert c.status_code == 409 and "avval ro‘yxatdan o‘tilgan" in c.json()["detail"]

    assert sum(1 for x in get_store().landing_results.all() if phone_key(x.get("phone")) == "995551122") == 1


def test_same_browser_retry_is_not_blocked(client, cfg):
    """Tarmoq qayta yuborsa (o‘sha clientId) — 409 emas, avvalgi natija qaytadi."""
    data = {**body(cfg, phone="+998 91 777 00 01"), "clientId": "retry-phone-1"}
    a = client.post(SUBMIT, json=data)
    b = client.post(SUBMIT, json=data)
    assert a.status_code == 201 and b.status_code == 201
    assert b.json()["duplicate"] is True and b.json()["id"] == a.json()["id"]


def test_old_records_without_phone_key_are_checked(client, cfg):
    """O‘zgarishdan oldin saqlangan natijalar (phoneKey yo‘q, raqam boshqacha yozilgan) ham hisobga olinadi."""
    get_store().landing_results.insert({"fullName": "Eski Nomzod", "phone": "8 (90) 400-00-01", "testSlug": "sotuv"})
    assert client.post(CHECK, json={"phone": "+998 90 400 00 01"}).status_code == 409
    assert client.post(SUBMIT, json=body(cfg, phone="904000001")).status_code == 409


def test_phone_freed_after_hr_deletes_result(client, cfg, hr_headers):
    r = client.post(SUBMIT, json=body(cfg, phone="+998 88 123 00 01"))
    assert r.status_code == 201
    assert client.post(CHECK, json={"phone": "+998881230001"}).status_code == 409
    assert client.delete(f"{API}/landing-results/{r.json()['id']}", headers=hr_headers).status_code == 204
    assert client.post(CHECK, json={"phone": "+998881230001"}).status_code == 200


# ---------- Saqlash qatlami: bir vaqtdagi so‘rovlar ----------
def test_store_insert_unique_under_concurrency():
    coll = get_store().landing_results
    key = "335550099"
    results = []
    barrier = threading.Barrier(12)

    def worker(i):
        barrier.wait()
        row, taken = coll.insert_unique({"phone": "+998 33 555 00 99", "phoneKey": key, "n": i},
                                        conflict=lambda r: phone_key(r.get("phoneKey") or r.get("phone")) == key)
        results.append(bool(row))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count(True) == 1
    assert sum(1 for r in coll.all() if r.get("phoneKey") == key) == 1


def test_concurrent_api_submits_same_phone(client, cfg):
    codes = []
    barrier = threading.Barrier(6)

    def worker(i):
        barrier.wait()
        codes.append(client.post(SUBMIT, json=body(cfg, fullName=f"Parallel Nomzod{chr(65 + i)}", phone="+998 94 000 77 66")).status_code)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(codes) == [201, 409, 409, 409, 409, 409]
