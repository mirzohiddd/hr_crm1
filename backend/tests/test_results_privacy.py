"""
Test natijalarining maxfiyligi:
- nomzod (ochiq API) javobida ball, foiz, to‘g‘ri/xato soni, holat, tahlil va tavsiyalar YO‘Q — faqat neytral tasdiq;
- natija serverda hisoblanib saqlanadi va faqat HR/admin (login + rol) endpointlarida ko‘rinadi;
- natija mavjud nomzod profiliga to‘g‘ri bog‘lanadi, boshqa nomzod profilida ko‘rinmaydi;
- eski (candidateId maydonisiz) yozuvlar ham o‘qish paytida bog‘lanadi va o‘zgartirilmaydi.
"""
import json
from datetime import date

import pytest

from app import final_test as ft
from app.security import create_token, hash_password
from app.store import get_store

from .conftest import API

FINAL_REG = f"{API}/public/final-test/register"
FINAL_SUBMIT = f"{API}/public/final-test/submit"
LANDING_SUBMIT = f"{API}/public/tests/sotuv/submit"
NEUTRAL = "Test muvaffaqiyatli yakunlandi. Natijangiz HR mutaxassisi tomonidan ko‘rib chiqiladi"

# Nomzodga hech qachon yuborilmasligi kerak bo‘lgan baholash maydonlari
SCORE_KEYS = {
    "correct", "wrong", "total", "points", "maxPoints", "percent", "passPercent", "passed", "status", "items",
    "answers", "participantNo", "attemptNo", "report", "reportText", "sections", "scores", "reliability",
    "reliabilityLevel", "bestPosition", "profileTitle", "positive", "negative", "candidateId", "employeeId",
}


def _keys(obj) -> set:
    """JSON ichidagi barcha kalitlar (ichma-ich)."""
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k)
            out |= _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= _keys(v)
    return out


def birth_for(age: int) -> str:
    return date(date.today().year - age, 1, 1).isoformat()


def final_answers(correct_count: int) -> dict:
    test = ft.load()
    return {str(q["id"]): q["correctIndex"] if i < correct_count else (q["correctIndex"] + 1) % len(q["options"])
            for i, q in enumerate(test["questions"])}


def final_take(client, first, last, age=27, correct=17, client_id=None):
    p = client.post(FINAL_REG, json={"firstName": first, "lastName": last, "age": age, "birthDate": birth_for(age)})
    assert p.status_code == 201, p.text
    p = p.json()["participant"]
    body = {"participantId": p["id"], "participantKey": p["key"], "answers": final_answers(correct)}
    if client_id:
        body["clientId"] = client_id
    r = client.post(FINAL_SUBMIT, json=body)
    assert r.status_code == 201, r.text
    return p, r


def landing_take(client, full_name, phone):
    q = client.get(f"{API}/public/tests/sotuv").json()
    r = client.post(LANDING_SUBMIT, json={
        "fullName": full_name, "age": 25, "date": date.today().isoformat(), "position": q["positions"][0],
        "phone": phone, "answers": {str(i["id"]): 1 for i in q["questions"]},
        "pictures": {p["id"]: 0 for p in q.get("pictures") or []},
    })
    assert r.status_code == 201, r.text
    return r


def make_candidate(client, hr_headers, full_name, phone, age=None):
    pos = client.get(f"{API}/positions", headers=hr_headers).json()[0]["id"]
    r = client.post(f"{API}/candidates", headers=hr_headers,
                    json={"fullName": full_name, "phone": phone, "positionId": pos, "age": age})
    assert r.status_code == 200, r.text
    return r.json()


def headers_for_role(role: str) -> dict:
    """Bazaga to‘g‘ridan-to‘g‘ri yozilgan foydalanuvchi (masalan, kelajakdagi yoki noto‘g‘ri rol) uchun token."""
    store = get_store()
    login = f"user-{role}"
    user = store.users.first(lambda u: u["login"] == login) or store.users.insert({
        "login": login, "fullName": f"Test {role}", "role": role, "active": True, "passwordHash": hash_password("x" * 10),
    })
    return {"Authorization": f"Bearer {create_token(user)}"}


# ---------- 1. Nomzod natijani API orqali ko‘ra olmaydi ----------
def test_final_submit_returns_only_neutral_ack(client):
    p, r = final_take(client, "Nilufar", "Ergasheva", correct=20, client_id="privacy-final-1")
    data = r.json()
    assert data["message"] == NEUTRAL
    assert set(data["result"]) == {"submittedAt", "fullName"}
    assert not (_keys(data) & SCORE_KEYS), _keys(data) & SCORE_KEYS
    # Takroriy yuborish (shu clientId) ham ball qaytarmaydi
    again = client.post(FINAL_SUBMIT, json={"participantId": p["id"], "participantKey": p["key"],
                                            "answers": final_answers(20), "clientId": "privacy-final-1"}).json()
    assert again["duplicate"] is True and not (_keys(again) & SCORE_KEYS)


def test_landing_submit_returns_only_neutral_ack(client):
    data = landing_take(client, "Qodirov Bobur Akmalovich", "+998 97 700 00 01").json()
    assert set(data) <= {"id", "submittedAt", "message", "duplicate"}
    assert data["message"] == NEUTRAL


def test_public_test_views_have_no_answer_key(client):
    final = json.dumps(client.get(f"{API}/public/final-test").json(), ensure_ascii=False)
    assert "correctIndex" not in final and '"correct"' not in final
    landing = client.get(f"{API}/public/tests/sotuv").json()
    assert not ({"key", "trait", "expected", "weights", "description"} & _keys(landing["questions"]))


def test_results_are_saved_on_server(client, hr_headers):
    p, _ = final_take(client, "Sardor", "Mirzayev", correct=15)
    row = next(r for r in client.get(f"{API}/final-results", headers=hr_headers).json() if r["participantId"] == p["id"])
    assert (row["correct"], row["wrong"], row["percent"], row["status"]) == (15, 5, 75, "O‘tmadi")
    detail = client.get(f"{API}/final-results/{row['id']}", headers=hr_headers).json()
    assert len(detail["items"]) == 20 and all("isCorrect" in i for i in detail["items"])


# ---------- 2. HR endpointlari: login + HR/admin roli ----------
HR_ENDPOINTS = ["/final-results", "/final-results/1", "/final-test/info", "/landing-results", "/landing-results/1",
                "/landing-tests", "/landing-tests/sotuv/key"]


@pytest.mark.parametrize("path", HR_ENDPOINTS + ["/candidates/1/test-results"])
def test_hr_endpoints_require_login(client, path):
    assert client.get(f"{API}{path}").status_code == 401
    assert client.get(f"{API}{path}", headers={"Authorization": "Bearer notogri"}).status_code == 401


@pytest.mark.parametrize("path", ["/final-results", "/landing-results", "/landing-tests/sotuv/key", "/final-test/info"])
def test_hr_endpoints_reject_non_hr_role(client, path):
    assert client.get(f"{API}{path}", headers=headers_for_role("viewer")).status_code == 403


def test_hr_role_can_read_results(client):
    h = headers_for_role("hr")
    assert client.get(f"{API}/final-results", headers=h).status_code == 200
    assert client.get(f"{API}/landing-results", headers=h).status_code == 200


def test_non_hr_cannot_delete_results(client, hr_headers):
    p, _ = final_take(client, "Oybek", "Nazarov")
    row = next(r for r in client.get(f"{API}/final-results", headers=hr_headers).json() if r["participantId"] == p["id"])
    assert client.delete(f"{API}/final-results/{row['id']}", headers=headers_for_role("viewer")).status_code == 403
    assert client.delete(f"{API}/final-results/{row['id']}").status_code == 401
    assert client.get(f"{API}/final-results/{row['id']}", headers=hr_headers).status_code == 200


def test_data_files_not_served_statically(client):
    for path in ("/data/final_results.json", "/backend/data/final_results.json", "/test/yakuniy/../../backend/data/final_results.json",
                 "/test/../backend/data/landing_results.json", "/api/v1/../data/final_results.json"):
        r = client.get(path)
        assert r.status_code in (404, 200) and '"items"' not in r.text and '"correctIndex"' not in r.text, path


# ---------- 3. Nomzod profiliga bog‘lash ----------
def test_landing_result_linked_to_candidate_by_phone(client, hr_headers):
    c = make_candidate(client, hr_headers, "Ahmedova Gulnora Rustamovna", "+998 93 555 11 22")
    other = make_candidate(client, hr_headers, "Boshqa Nomzod", "+998 93 555 11 23")
    sub = landing_take(client, "Ahmedova Gulnora", "93 555 11 22").json()

    linked = client.get(f"{API}/candidates/{c['id']}/test-results", headers=hr_headers).json()
    assert [r["id"] for r in linked["landing"]] == [sub["id"]]
    assert linked["landing"][0]["candidateId"] == c["id"] and linked["landing"][0]["status"]
    assert client.get(f"{API}/candidates/{other['id']}/test-results", headers=hr_headers).json() == {"landing": [], "final": []}

    d = client.get(f"{API}/landing-results/{sub['id']}", headers=hr_headers).json()
    assert d["candidate"]["id"] == c["id"] and d["candidate"]["fullName"] == "Ahmedova Gulnora Rustamovna"


def test_final_result_linked_to_candidate_by_name_and_age(client, hr_headers):
    c = make_candidate(client, hr_headers, "Rasulova Kamola", "+998 93 555 22 33", age=29)
    p, _ = final_take(client, "Kamola", "Rasulova", age=29, correct=18)
    linked = client.get(f"{API}/candidates/{c['id']}/test-results", headers=hr_headers).json()
    assert len(linked["final"]) == 1 and linked["final"][0]["participantId"] == p["id"]
    assert linked["final"][0]["percent"] == 90
    rid = linked["final"][0]["id"]
    assert client.get(f"{API}/final-results/{rid}", headers=hr_headers).json()["candidate"]["id"] == c["id"]


def test_final_result_not_linked_when_ambiguous_or_age_differs(client, hr_headers):
    a = make_candidate(client, hr_headers, "Usmonov Javlon", "+998 93 555 33 44")
    b = make_candidate(client, hr_headers, "Usmonov Javlon", "+998 93 555 33 45")
    old = make_candidate(client, hr_headers, "Saidov Rustam", "+998 93 555 33 46", age=40)
    final_take(client, "Javlon", "Usmonov", age=30)
    final_take(client, "Rustam", "Saidov", age=22)
    for c in (a, b, old):
        assert client.get(f"{API}/candidates/{c['id']}/test-results", headers=hr_headers).json()["final"] == []


def test_final_result_linked_through_hired_employee(client, hr_headers):
    c = make_candidate(client, hr_headers, "Tursunova Malika", "+998 93 555 44 55")
    pos = client.get(f"{API}/positions", headers=hr_headers).json()[0]["id"]
    dep = client.get(f"{API}/departments", headers=hr_headers).json()[0]["id"]
    hired = client.post(f"{API}/candidates/{c['id']}/hire", headers=hr_headers,
                        json={"hireDate": date.today().isoformat(), "positionId": pos, "departmentId": dep, "startTraining": False})
    assert hired.status_code == 200, hired.text
    final_take(client, "Malika", "Tursunova", age=24)
    row = client.get(f"{API}/candidates/{c['id']}/test-results", headers=hr_headers).json()["final"][0]
    assert row["employeeId"] == hired.json()["employee"]["id"] and row["candidateId"] == c["id"]


def test_old_rows_without_candidate_id_are_linked_on_read_and_not_modified(client, hr_headers):
    c = make_candidate(client, hr_headers, "Eski Yozuv Egasi", "+998 93 555 55 66")
    store = get_store()
    old = store.landing_results.insert({
        "testSlug": "sotuv", "testTitle": "Eski test", "fullName": "Eski Yozuv Egasi", "phone": "+998 93 555 55 66",
        "submittedAt": "2026-01-05T10:00", "percent": 70, "status": "O‘tdi", "viewed": True,
    })
    linked = client.get(f"{API}/candidates/{c['id']}/test-results", headers=hr_headers).json()
    assert [r["id"] for r in linked["landing"]] == [old["id"]]
    assert "candidateId" not in store.landing_results.get(old["id"])  # saqlangan yozuv o‘zgarmagan


def test_candidate_test_results_requires_hr(client, hr_headers):
    c = make_candidate(client, hr_headers, "Maxfiy Nomzod", "+998 93 555 66 77")
    assert client.get(f"{API}/candidates/{c['id']}/test-results").status_code == 401
    assert client.get(f"{API}/candidates/{c['id']}/test-results", headers=headers_for_role("viewer")).status_code == 403
    assert client.get(f"{API}/candidates/999999/test-results", headers=hr_headers).status_code == 404
