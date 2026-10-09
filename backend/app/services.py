"""Bir nechta router ishlatadigan biznes mantiq."""
from .config import UPLOAD_DIR
from .store import Store
from .utils import bad_request, not_found, now_local

DEFAULT_PASS_PERCENT = 80

DEFAULT_SETTINGS = {
    "id": 1,
    "passPercent": DEFAULT_PASS_PERCENT,
    "maxAttempts": 3,
    "shuffleQuestions": True,
    "shuffleOptions": False,
    "autoAssign": True,
    "activateOnPass": True,
}


def get_settings(store: Store) -> dict:
    rows = store.settings.all()
    if not rows:
        store.settings.replace_all([DEFAULT_SETTINGS])
        return dict(DEFAULT_SETTINGS)
    return {**DEFAULT_SETTINGS, **rows[0]}


def pick_test_for(employee: dict, tests: list[dict]) -> dict | None:
    """Avval xodim lavozimiga xos test, bo‘lmasa umumiy (lavozim tanlanmagan) test."""
    active = [t for t in tests if t.get("active", True) and t.get("questions")]
    for t in active:
        if employee.get("positionId") in (t.get("positionIds") or []):
            return t
    for t in active:
        if not t.get("positionIds"):
            return t
    return None


def assign_test(store: Store, employee_id: int, test_id: int | None = None, training_id: int | None = None) -> dict:
    employee = store.employees.get(employee_id)
    if not employee:
        raise not_found("Xodim")
    test = store.tests.get(test_id) if test_id else pick_test_for(employee, sorted(store.tests.all(), key=lambda t: t["id"]))
    if not test:
        raise bad_request("Mos test topilmadi. Testlar bo‘limida test yarating.")
    return store.test_results.insert({
        "employeeId": employee_id,
        "testId": test["id"],
        "trainingId": training_id,
        "passPercent": get_settings(store)["passPercent"] or DEFAULT_PASS_PERCENT,
        "assignedAt": now_local(),
        "status": "Kutilmoqda",
        "score": None,
        "correct": None,
        "total": len(test.get("questions") or []),
        "completedAt": None,
        "attempts": [],
    })


def grade(test: dict, answers: dict, pass_percent: int) -> dict:
    """To‘g‘ri javoblar soni, foiz va o‘tdi/o‘tmadi (score >= pass_percent)."""
    questions = test.get("questions") or []
    total = len(questions)
    correct = 0
    for q in questions:
        given = answers.get(str(q["id"]))
        try:
            if given is not None and int(given) == int(q["correctIndex"]):
                correct += 1
        except (TypeError, ValueError):
            pass
    score = round(correct / total * 100) if total else 0
    return {"total": total, "correct": correct, "score": score, "passed": score >= pass_percent}


def delete_document_file(doc: dict) -> None:
    if doc.get("filePath"):
        path = UPLOAD_DIR / doc["filePath"]
        if path.exists():
            path.unlink()


def delete_employee_cascade(store: Store, employee_id: int) -> None:
    """Xodim bilan bog‘liq dastur, test natijalari va hujjatlarni (fayllari bilan) o‘chirish."""
    store.trainings.delete_where(employeeId=employee_id)
    store.test_results.delete_where(employeeId=employee_id)
    store.final_results.delete_where(employeeId=employee_id)
    for doc in store.documents.delete_where(employeeId=employee_id):
        delete_document_file(doc)
