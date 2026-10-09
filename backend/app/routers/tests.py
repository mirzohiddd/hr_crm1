"""Testlar (tests.json), natijalar (test_results.json) va test sozlamalari (settings.json)."""
from fastapi import APIRouter, Depends, Response

from ..schemas import AssignIn, SubmitIn, TestIn, TestSettingsIn
from ..security import current_user
from ..services import DEFAULT_PASS_PERCENT, assign_test, get_settings, grade
from ..store import get_store
from ..utils import bad_request, conflict, get_or_404, now_local

router = APIRouter(tags=["Testlar"], dependencies=[Depends(current_user)])


# ---------- Testlar bazasi ----------
@router.get("/tests")
def list_tests():
    return sorted(get_store().tests.all(), key=lambda t: t["id"])


@router.get("/tests/{test_id}")
def get_test(test_id: int):
    return get_or_404(get_store().tests, test_id, "Test")


def _validate_questions(questions: list[dict]) -> None:
    for i, q in enumerate(questions, 1):
        if q["correctIndex"] >= len(q["options"]):
            raise bad_request(f"{i}-savol: to‘g‘ri javob variantlar orasida bo‘lishi kerak")


@router.post("/tests")
def create_test(body: TestIn):
    store = get_store()
    data = body.values()
    if not data.get("title") or not data.get("questions"):
        raise bad_request("Test nomi va kamida bitta savol majburiy")
    _validate_questions(data["questions"])
    return store.tests.insert({
        "description": "", "positionIds": [], "active": True,
        "passPercent": get_settings(store)["passPercent"], **data,
    })


@router.put("/tests/{test_id}")
def update_test(test_id: int, body: TestIn):
    get_or_404(get_store().tests, test_id, "Test")
    data = body.values()
    if "questions" in data:
        if not data["questions"]:
            raise bad_request("Kamida bitta savol bo‘lishi kerak")
        _validate_questions(data["questions"])
    return get_store().tests.update(test_id, data)


@router.delete("/tests/{test_id}", status_code=204)
def delete_test(test_id: int):
    store = get_store()
    get_or_404(store.tests, test_id, "Test")
    if store.test_results.count(testId=test_id):
        raise conflict("Bu test bo‘yicha natijalar bor. O‘chirish o‘rniga nofaol qiling.")
    store.tests.delete(test_id)
    return Response(status_code=204)


# ---------- Natijalar ----------
@router.get("/test-results")
def list_results():
    return sorted(get_store().test_results.all(), key=lambda r: r["id"], reverse=True)


@router.post("/test-results")
def assign(body: AssignIn):
    """Testni xodimga qo‘lda yuborish (testId bo‘lmasa — lavozimga mos test)."""
    store = get_store()
    if store.test_results.count(employeeId=body.employee_id, status="Kutilmoqda"):
        raise conflict("Bu xodimda topshirilmagan test bor")
    return assign_test(store, body.employee_id, body.test_id)


@router.post("/test-results/{result_id}/submit")
def submit(result_id: int, body: SubmitIn):
    """Javoblarni qabul qilib, natijani serverda hisoblaydi: score >= o‘tish foizi → O‘tdi."""
    store = get_store()
    result = get_or_404(store.test_results, result_id, "Natija")
    test = get_or_404(store.tests, result["testId"], "Test")
    settings = get_settings(store)
    attempts = result.get("attempts") or []
    if result["status"] == "O‘tdi":
        raise conflict("Test allaqachon topshirilgan")
    if len(attempts) >= settings["maxAttempts"]:
        raise conflict(f"Urinishlar soni tugagan ({settings['maxAttempts']} ta)")

    pass_percent = settings["passPercent"] or DEFAULT_PASS_PERCENT
    g = grade(test, body.answers, pass_percent)
    at = now_local()
    # Savollar nusxasi — test keyin tahrirlansa ham javoblar tahlili to‘g‘ri ko‘rinadi
    questions = [{k: q[k] for k in ("id", "text", "options", "correctIndex")} for q in test["questions"]]
    answers = {str(k): v for k, v in body.answers.items()}
    updated = store.test_results.update(result_id, {
        "attempts": [*attempts, {"at": at, **g, "answers": answers, "questions": questions}],
        "status": "O‘tdi" if g["passed"] else "O‘tmadi",
        "score": g["score"],
        "correct": g["correct"],
        "total": g["total"],
        "completedAt": at,
        "passPercent": pass_percent,
    })

    employee = None
    if g["passed"] and settings["activateOnPass"]:
        e = store.employees.get(result["employeeId"])
        if e and e.get("status") == "Yangi":
            employee = store.employees.update(e["id"], {"status": "Faol"})
    return {"result": updated, "employee": employee}


@router.delete("/test-results/{result_id}", status_code=204)
def delete_result(result_id: int):
    store = get_store()
    get_or_404(store.test_results, result_id, "Natija")
    for t in store.trainings.filter(testResultId=result_id):
        store.trainings.update(t["id"], {"testResultId": None})
    store.test_results.delete(result_id)
    return Response(status_code=204)


# ---------- Sozlamalar ----------
@router.get("/settings/tests")
def read_settings():
    return get_settings(get_store())


@router.put("/settings/tests")
def save_settings(body: TestSettingsIn):
    store = get_store()
    merged = {**get_settings(store), **body.values(), "id": 1}
    store.settings.replace_all([merged])
    return merged
