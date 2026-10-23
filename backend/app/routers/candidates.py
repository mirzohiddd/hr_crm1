"""Nomzodlar (candidates.json): voronka, ishga qabul qilish, import, nomzodning test natijalari (faqat HR)."""
from fastapi import APIRouter, Depends, Response

from ..schemas import CandidateIn, CandidateStatusIn, HireIn, ImportIn
from ..result_links import final_candidate_id, landing_candidate_id, phone_index
from ..security import current_user, hr_user
from ..store import get_store
from ..utils import bad_request, conflict, get_or_404, now_local, phone_key, split_name

router = APIRouter(prefix="/candidates", tags=["Nomzodlar"])

EMPTY = {
    "fullName": "", "gender": "", "phone": "", "age": None, "city": "", "positionId": None, "departmentId": None,
    "source": "Boshqa", "status": "Yangi", "contactAttempts": 0, "note": "", "createdAt": "",
    "interviewAt": None, "rejectReason": "", "employeeId": None, "history": [],
}


def _entry(status: str, by: str, at: str | None = None) -> dict:
    return {"status": status, "at": at or now_local(), "by": by}


@router.get("")
def list_candidates(_: dict = Depends(current_user)):
    rows = get_store().candidates.all()
    rows.sort(key=lambda c: (c.get("createdAt") or "", c["id"]), reverse=True)
    return rows


@router.get("/{candidate_id}")
def get_candidate(candidate_id: int, _: dict = Depends(current_user)):
    return get_or_404(get_store().candidates, candidate_id, "Nomzod")


@router.get("/{candidate_id}/test-results")
def candidate_test_results(candidate_id: int, _: dict = Depends(hr_user)):
    """
    Nomzod profiliga bog‘langan test natijalari (qisqa ko‘rinish) — faqat HR/admin.
    landing — nomzodlar testi (/test/sotuv, telefon bo‘yicha), final — yakuniy bilim testi (/test/yakuniy).
    To‘liq hisobot: GET /landing-results/{id} va GET /final-results/{id}.
    """
    from . import final_test as final_router
    from . import landing as landing_router

    store = get_store()
    get_or_404(store.candidates, candidate_id, "Nomzod")
    index = phone_index(store)
    landing_rows = [r for r in store.landing_results.all() if landing_candidate_id(store, r, index) == candidate_id]
    final_rows = [r for r in store.final_results.all() if final_candidate_id(store, r) == candidate_id]
    newest = lambda r: (r.get("submittedAt") or "", r["id"])  # noqa: E731
    return {
        "landing": [landing_router._summary(r, index) for r in sorted(landing_rows, key=newest, reverse=True)],
        "final": [final_router._summary(r) for r in sorted(final_rows, key=newest, reverse=True)],
    }


@router.post("")
def create_candidate(body: CandidateIn, user: dict = Depends(current_user)):
    data = body.values()
    if not data.get("fullName") or not data.get("phone") or not data.get("positionId"):
        raise bad_request("F.I.Sh, telefon va lavozim majburiy")
    at = now_local()
    return get_store().candidates.insert({**EMPTY, "createdAt": at, **data, "history": [_entry("Yangi", user["fullName"], at)]})


@router.put("/{candidate_id}")
def update_candidate(candidate_id: int, body: CandidateIn, _: dict = Depends(current_user)):
    get_or_404(get_store().candidates, candidate_id, "Nomzod")
    return get_store().candidates.update(candidate_id, body.values())


@router.delete("/{candidate_id}", status_code=204)
def delete_candidate(candidate_id: int, _: dict = Depends(current_user)):
    get_or_404(get_store().candidates, candidate_id, "Nomzod")
    get_store().candidates.delete(candidate_id)
    return Response(status_code=204)


@router.patch("/{candidate_id}/status")
def set_status(candidate_id: int, body: CandidateStatusIn, user: dict = Depends(current_user)):
    c = get_or_404(get_store().candidates, candidate_id, "Nomzod")
    if c["status"] == "Ishga qabul qilindi":
        raise conflict("Nomzod allaqachon ishga qabul qilingan")
    if body.status == "Ishga qabul qilindi":
        raise bad_request("Ishga qabul qilish uchun /hire dan foydalaning")
    patch = {
        "status": body.status,
        "rejectReason": (body.reject_reason or "") if body.status == "Rad etildi" else "",
        "history": [*(c.get("history") or []), _entry(body.status, user["fullName"])],
    }
    if "interview_at" in body.model_fields_set:
        patch["interviewAt"] = body.interview_at
    if body.status == "Bog‘lanilmadi":
        patch["contactAttempts"] = (c.get("contactAttempts") or 0) + 1
    return get_store().candidates.update(candidate_id, patch)


@router.post("/{candidate_id}/hire")
def hire(candidate_id: int, body: HireIn, user: dict = Depends(current_user)):
    """Nomzodni xodimga aylantiradi va (ixtiyoriy) 7 kunlik o‘quv dasturini boshlaydi."""
    store = get_store()
    c = get_or_404(store.candidates, candidate_id, "Nomzod")
    if c.get("employeeId") and store.employees.get(c["employeeId"]):
        raise conflict("Bu nomzod allaqachon xodimlar ro‘yxatida")
    last, first, middle = split_name(c["fullName"])
    employee = store.employees.insert({
        "fullName": c["fullName"], "lastName": last, "firstName": first, "middleName": middle,
        "gender": c.get("gender") or "", "birthDate": "", "age": c.get("age"),
        "phone": c.get("phone") or "", "telegram": "", "email": "", "address": c.get("city") or "",
        "previousWork": "", "computerSkill": "", "expectedSalary": None,
        "departmentId": body.department_id, "positionId": body.position_id,
        "hireDate": body.hire_date, "status": "Yangi", "leftAt": None, "candidateId": c["id"], "photo": None,
    })
    training = None
    if body.start_training:
        training = store.trainings.insert({
            "employeeId": employee["id"], "startDate": body.hire_date, "completedDays": [],
            "status": "Jarayonda", "finishedAt": None, "testResultId": None,
        })
    candidate = store.candidates.update(candidate_id, {
        "status": "Ishga qabul qilindi",
        "positionId": body.position_id,
        "departmentId": body.department_id,
        "employeeId": employee["id"],
        "rejectReason": "",
        "history": [*(c.get("history") or []), _entry("Ishga qabul qilindi", user["fullName"])],
    })
    return {"candidate": candidate, "employee": employee, "training": training}


@router.post("/import")
def import_candidates(body: ImportIn, user: dict = Depends(current_user)):
    """Google Sheets / CSV qatorlari. Telefon raqami bazada bo‘lsa — o‘tkazib yuboriladi."""
    store = get_store()
    seen = {phone_key(c.get("phone")) for c in store.candidates.all() if phone_key(c.get("phone"))}
    created, skipped = [], 0
    for row in body.rows:
        data = row.values()
        if not data.get("fullName") or not data.get("phone") or not data.get("positionId"):
            skipped += 1
            continue
        key = phone_key(data["phone"])
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        at = data.get("createdAt") or now_local()
        by = f"{data.get('source') or 'Fayl'} importi ({user['fullName']})"
        created.append(store.candidates.insert({**EMPTY, **data, "createdAt": at, "history": [_entry("Yangi", by, at)]}))
    return {"created": created, "skipped": skipped}