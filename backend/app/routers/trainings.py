"""7 kunlik o‘quv dasturi: darslar (lessons.json) va xodimlar progressi (trainings.json)."""
from fastapi import APIRouter, Depends, HTTPException, Response

from ..schemas import LessonIn, TrainingStartIn
from ..security import current_user
from ..services import assign_test, get_settings
from ..store import get_store
from ..utils import bad_request, conflict, get_or_404, not_found, now_local, today

router = APIRouter(tags=["Darslar"])
TRAINING_DAYS = 7


@router.get("/lessons")
def list_lessons(_: dict = Depends(current_user)):
    return sorted(get_store().lessons.all(), key=lambda x: x["day"])


@router.put("/lessons/{lesson_id}")
def update_lesson(lesson_id: int, body: LessonIn, _: dict = Depends(current_user)):
    get_or_404(get_store().lessons, lesson_id, "Dars")
    return get_store().lessons.update(lesson_id, body.values())


@router.get("/trainings")
def list_trainings(_: dict = Depends(current_user)):
    return sorted(get_store().trainings.all(), key=lambda x: x["id"], reverse=True)


@router.post("/trainings")
def start_training(body: TrainingStartIn, _: dict = Depends(current_user)):
    store = get_store()
    if not store.employees.get(body.employee_id):
        raise not_found("Xodim")
    if store.trainings.count(employeeId=body.employee_id):
        raise conflict("Bu xodim allaqachon o‘quv dasturiga qo‘shilgan")
    return store.trainings.insert({
        "employeeId": body.employee_id, "startDate": body.start_date or today(), "completedDays": [],
        "status": "Jarayonda", "finishedAt": None, "testResultId": None,
    })


@router.post("/trainings/{training_id}/days/{day}/complete")
def complete_day(training_id: int, day: int, user: dict = Depends(current_user)):
    """Kunni bajarildi deb belgilash. 7-kun tugasa — test avtomatik yuboriladi."""
    store = get_store()
    t = get_or_404(store.trainings, training_id, "O‘quv dasturi")
    days = t.get("completedDays") or []
    done = [d["day"] for d in days]
    if day in done:
        raise conflict(f"{day}-kun allaqachon bajarilgan")
    if day != len(done) + 1:
        raise bad_request(f"Avval {len(done) + 1}-kunni yakunlang")
    at = now_local()
    patch = {"completedDays": [*days, {"day": day, "at": at, "by": user["fullName"]}]}
    result = None
    if len(patch["completedDays"]) >= TRAINING_DAYS:
        patch.update(status="Yakunlandi", finishedAt=at)
        if get_settings(store)["autoAssign"] and not t.get("testResultId"):
            try:
                result = assign_test(store, t["employeeId"], training_id=training_id)
                patch["testResultId"] = result["id"]
            except HTTPException:
                result = None  # mos test yo‘q — HR keyin qo‘lda yuboradi
    return {"training": store.trainings.update(training_id, patch), "testResult": result}


@router.delete("/trainings/{training_id}/days/{day}")
def undo_day(training_id: int, day: int, _: dict = Depends(current_user)):
    t = get_or_404(get_store().trainings, training_id, "O‘quv dasturi")
    if t.get("status") == "Yakunlandi":
        raise conflict("Dastur yakunlangan, kunlarni bekor qilib bo‘lmaydi")
    days = t.get("completedDays") or []
    if not days or days[-1]["day"] != day:
        raise bad_request("Faqat oxirgi bajarilgan kunni bekor qilish mumkin")
    return get_store().trainings.update(training_id, {"completedDays": days[:-1]})


@router.delete("/trainings/{training_id}", status_code=204)
def delete_training(training_id: int, _: dict = Depends(current_user)):
    get_or_404(get_store().trainings, training_id, "O‘quv dasturi")
    get_store().trainings.delete(training_id)
    return Response(status_code=204)
