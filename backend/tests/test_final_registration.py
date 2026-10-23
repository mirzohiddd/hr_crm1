"""
Yakuniy bilim testi (landing-2, /test/yakuniy): ro‘yxatdan o‘tish → test → HR panelidagi natija.
"""
import json
import threading
from datetime import date

import pytest

from app import final_test as ft
from app.config import DATA_DIR

from .conftest import API

REG = f"{API}/public/final-test/register"
SUBMIT = f"{API}/public/final-test/submit"


def birth_for(age: int) -> str:
    """Bugun aynan `age` yosh bo‘ladigan tug‘ilgan sana (1-yanvar — tug‘ilgan kun allaqachon o‘tgan)."""
    return date(date.today().year - age, 1, 1).isoformat()


def person(**over):
    data = {"firstName": "Aziz", "lastName": "Karimov", "age": 25, "birthDate": birth_for(25)}
    data.update(over)
    return data


def answers_with(correct_count: int) -> dict:
    """Aynan `correct_count` ta to‘g‘ri javob."""
    test = ft.load()
    out = {}
    for i, q in enumerate(test["questions"]):
        right = q["correctIndex"]
        out[str(q["id"])] = right if i < correct_count else (right + 1) % len(q["options"])
    return out


def register(client, **over):
    r = client.post(REG, json=person(**over))
    assert r.status_code == 201, r.text
    return r.json()["participant"]


# ---------- Ro‘yxatdan o‘tish: validatsiya ----------
def test_register_ok_returns_stable_id_and_key(client):
    p = register(client, firstName="  Dilnoza ", lastName="Rahimova  ", clientId="reg-ok-1")
    assert isinstance(p["id"], int) and p["key"]
    assert p["firstName"] == "Dilnoza" and p["lastName"] == "Rahimova"
    assert p["fullName"] == "Rahimova Dilnoza"
    assert p["age"] == 25 and p["birthDate"] == birth_for(25)
    assert "accessKey" not in p and "clientId" not in p


@pytest.mark.parametrize(
    "over, message",
    [
        ({"firstName": ""}, "Ismni kiriting"),
        ({"lastName": "   "}, "Familiyani kiriting"),
        ({"firstName": "A"}, "kamida 2"),
        ({"firstName": "Aziz2"}, "faqat harflar"),
        ({"lastName": "<script>"}, "faqat harflar"),
        ({"age": ""}, "Yoshingizni kiriting"),
        ({"age": "yigirma"}, "butun son"),
        ({"age": 25.5}, "butun son"),
        ({"age": 12, "birthDate": birth_for(12)}, "16 dan 70 gacha"),
        ({"birthDate": ""}, "Tug‘ilgan sanani tanlang"),
        ({"birthDate": "2001-02-30"}, "mavjud emas"),
        ({"birthDate": "01.02.2001"}, "formatda"),
        ({"birthDate": f"{date.today().year + 1}-01-01"}, "kelajakdagi"),
        ({"age": 30}, "mos emas"),
    ],
)
def test_register_validation(client, over, message):
    r = client.post(REG, json=person(**over))
    assert r.status_code == 400, r.text
    assert message in r.json()["detail"]


def test_register_accepts_uzbek_apostrophes_and_cyrillic(client):
    p = register(client, firstName="Gʻayrat", lastName="O‘g‘ilov")
    assert p["fullName"] == "O‘g‘ilov Gʻayrat"
    p2 = register(client, firstName="Ольга", lastName="Ким-Ли")
    assert p2["fullName"] == "Ким-Ли Ольга"


def test_register_same_client_id_is_idempotent(client):
    a = client.post(REG, json=person(clientId="dup-reg-1")).json()["participant"]
    b = client.post(REG, json=person(clientId="dup-reg-1"))
    assert b.status_code == 201 and b.json()["duplicate"] is True
    assert b.json()["participant"]["id"] == a["id"] and b.json()["participant"]["key"] == a["key"]
    c = client.post(REG, json=person(clientId="dup-reg-1", firstName="Boshqa"))
    assert c.status_code == 409


def test_same_name_is_never_merged_automatically(client):
    a = register(client, firstName="Ali", lastName="Valiyev")
    b = register(client, firstName="Ali", lastName="Valiyev")
    assert a["id"] != b["id"]


# ---------- Topshirish ----------
def test_submit_requires_registration(client):
    r = client.post(SUBMIT, json={"answers": answers_with(20)})
    assert r.status_code == 400
    assert "shaxsiy ma’lumot" in r.json()["detail"]


def test_submit_rejects_wrong_key_or_unknown_participant(client):
    p = register(client)
    r = client.post(SUBMIT, json={"participantId": p["id"], "participantKey": "notogri", "answers": answers_with(20)})
    assert r.status_code == 403
    r = client.post(SUBMIT, json={"participantId": 999999, "participantKey": p["key"], "answers": answers_with(20)})
    assert r.status_code == 403


def test_submit_rejects_incomplete_answers(client):
    p = register(client)
    ans = answers_with(20)
    ans.pop(next(iter(ans)))
    r = client.post(SUBMIT, json={"participantId": p["id"], "participantKey": p["key"], "answers": ans})
    assert r.status_code == 400 and "Javobsiz" in r.json()["detail"]


def _hr_row_for(client, hr_headers, participant_id):
    rows = [r for r in client.get(f"{API}/final-results", headers=hr_headers).json() if r["participantId"] == participant_id]
    return sorted(rows, key=lambda r: r["id"])


@pytest.mark.parametrize("correct, status, percent", [(20, "O‘tdi", 100), (16, "O‘tdi", 80), (15, "O‘tmadi", 75)])
def test_scoring_rules_unchanged(client, hr_headers, correct, status, percent):
    """Ball qoidalari o‘zgarmagan — lekin natija faqat HR endpointida ko‘rinadi, nomzod javobida yo‘q."""
    p = register(client)
    r = client.post(SUBMIT, json={"participantId": p["id"], "participantKey": p["key"], "answers": answers_with(correct)})
    assert r.status_code == 201, r.text
    res = r.json()["result"]
    assert set(res) == {"submittedAt", "fullName"} and res["fullName"] == p["fullName"]
    row = _hr_row_for(client, hr_headers, p["id"])[-1]
    assert (row["correct"], row["status"], row["percent"], row["passPercent"]) == (correct, status, percent, 80)


def test_duplicate_submit_creates_one_result_and_attempts_count(client, hr_headers):
    p = register(client, firstName="Jasur", lastName="Toshmatov")
    body = {"participantId": p["id"], "participantKey": p["key"], "answers": answers_with(18), "clientId": "dup-sub-1"}
    first = client.post(SUBMIT, json=body).json()["result"]
    again = client.post(SUBMIT, json=body).json()
    assert again["duplicate"] is True and again["result"] == first  # takroriy javobda ham ball yo‘q
    assert len(_hr_row_for(client, hr_headers, p["id"])) == 1
    client.post(SUBMIT, json={**body, "clientId": "dup-sub-2"})
    rows = _hr_row_for(client, hr_headers, p["id"])
    assert sorted(r["attemptNo"] for r in rows) == [1, 2]


# ---------- HR paneli ----------
def test_hr_sees_participant_data_and_answers(client, hr_headers):
    p = register(client, firstName="Madina", lastName="Yusupova", age=31, birthDate=birth_for(31))
    ans = answers_with(17)
    client.post(SUBMIT, json={"participantId": p["id"], "participantKey": p["key"], "answers": ans})

    row = _hr_row_for(client, hr_headers, p["id"])[-1]
    assert row["fullName"] == "Yusupova Madina"
    assert (row["firstName"], row["lastName"], row["age"], row["birthDate"]) == ("Madina", "Yusupova", 31, birth_for(31))
    assert row["testTitle"] and row["submittedAt"] and row["percent"] == 85 and row["status"] == "O‘tdi"

    d = client.get(f"{API}/final-results/{row['id']}", headers=hr_headers).json()
    assert d["participant"]["id"] == p["id"] and d["participant"]["fullName"] == "Yusupova Madina"
    assert len(d["items"]) == 20 and d["answers"] == ans
    assert "accessKey" not in json.dumps(d) and "clientId" not in d


def test_hr_endpoints_require_login(client):
    assert client.get(f"{API}/final-results").status_code == 401
    assert client.get(f"{API}/final-results/1").status_code == 401


def test_public_endpoints_do_not_expose_other_participants(client):
    register(client, firstName="Maxfiy", lastName="Shaxs")
    other = register(client)
    text = json.dumps(client.get(f"{API}/public/final-test").json(), ensure_ascii=False)
    assert "Maxfiy" not in text and "correct" not in text
    r = client.post(SUBMIT, json={"participantId": other["id"], "participantKey": other["key"], "answers": answers_with(20)})
    assert "Maxfiy" not in r.text


# ---------- Ma'lumotlar yaxlitligi ----------
def test_parallel_submits_do_not_lose_data(client, hr_headers):
    before_results = len(client.get(f"{API}/final-results", headers=hr_headers).json())
    participants = [register(client, firstName=f"Parallel", lastName=f"Ishtirokchi{'abcdefghij'[i]}") for i in range(10)]
    errors = []

    def go(i, p):
        r = client.post(SUBMIT, json={"participantId": p["id"], "participantKey": p["key"], "answers": answers_with(i + 10),
                                      "clientId": f"par-{i}"})
        if r.status_code != 201:
            errors.append(r.text)

    threads = [threading.Thread(target=go, args=(i, p)) for i, p in enumerate(participants)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert not errors
    rows = client.get(f"{API}/final-results", headers=hr_headers).json()
    assert len(rows) == before_results + 10
    assert len({r["id"] for r in rows}) == len(rows)
    # Diskdagi fayllar butun va to‘liq
    on_disk = json.loads((DATA_DIR / "final_results.json").read_text(encoding="utf-8"))
    assert len(on_disk) == len(rows)
    people = json.loads((DATA_DIR / "final_participants.json").read_text(encoding="utf-8"))
    assert {p["id"] for p in participants} <= {p["id"] for p in people}


# ---------- Landing 1 (nomzodlar testi) o‘zgarmagan ----------
def test_landing1_still_works(client):
    q = client.get(f"{API}/public/tests/sotuv").json()
    assert "Marketing" in q["positions"] and "Logistika" in q["positions"]
    answers = {str(i["id"]): 1 for i in q["questions"]}  # 40 savolli test: 1 = «Qo‘shilaman»
    r = client.post(f"{API}/public/tests/sotuv/submit", json={
        "fullName": "Testov Test Testovich", "age": 25, "date": date.today().isoformat(),
        "position": "Marketing", "phone": "+998 95 100 00 01", "answers": answers,  # telefon — majburiy
        "pictures": {"rasm-1": 0, "rasm-2": 0, "rasm-3": 0},  # rasmli savollar — majburiy
    })
    assert r.status_code == 201, r.text


def test_old_results_without_participant_still_listed(client, hr_headers):
    """Bu o‘zgarishdan oldingi (ismsiz) yozuvlar o‘chmaydi va HR ro‘yxatida ko‘rinadi."""
    from app.store import get_store

    old = get_store().final_results.insert({
        "employeeId": None, "attemptNo": 1, "fullName": "", "position": "", "department": "",
        "testSlug": "yakuniy", "testTitle": "Yakuniy bilim testi", "submittedAt": "2026-10-10T12:00",
        "answers": {}, "items": [], "total": 20, "correct": 10, "wrong": 10, "points": 10, "maxPoints": 20,
        "percent": 50, "passPercent": 80, "status": "O‘tmadi",
    })
    rows = client.get(f"{API}/final-results", headers=hr_headers).json()
    row = next(r for r in rows if r["id"] == old["id"])
    assert row["participantId"] is None and row["fullName"] == ""
    d = client.get(f"{API}/final-results/{old['id']}", headers=hr_headers).json()
    assert d["participant"] is None