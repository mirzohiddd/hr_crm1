"""
Yakuniy bilim testi (/test/yakuniy) — ochiq test, havola/token/ism talab qilinmaydi.

Ochiq (login yo‘q):
    GET  /public/final-test            20 ta savol (to‘g‘ri javoblarsiz)
    POST /public/final-test/submit     { answers, durationSec?, clientId? } → natija (ball serverda)

HR (login bilan):
    GET    /final-test/info            test haqida (savollar soni, o‘tish foizi)
    GET    /final-results              barcha topshirishlar (qisqa)
    GET    /final-results/{id}         batafsil: 20 ta savol, variantlar, tanlangan javob, to‘g‘ri javob
    DELETE /final-results/{id}         natijani o‘chirish
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from .. import final_test as ft
from ..schemas import FinalSubmitIn
from ..security import current_user
from ..store import _lock, get_store
from ..utils import get_or_404, now_local

public_router = APIRouter(prefix="/public/final-test", tags=["Yakuniy test (ochiq)"])
router = APIRouter(tags=["Yakuniy bilim testi"], dependencies=[Depends(current_user)])

SUMMARY_FIELDS = (
    "id", "participantNo", "employeeId", "attemptNo", "fullName", "position", "department", "submittedAt",
    "durationSec", "correct", "wrong", "total", "points", "maxPoints", "percent", "passPercent", "status", "testTitle",
)

# Ochiq testni suiiste’moldan himoya: bitta IP manzildan 1 soatda ko‘pi bilan 60 ta topshirish
RATE_LIMIT, RATE_WINDOW = 60, 3600
_hits: dict[str, deque] = defaultdict(deque)
_hits_lock = threading.Lock()


def _rate_limit(request: Request) -> None:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "?")
    now = time.monotonic()
    with _hits_lock:
        q = _hits[ip]
        while q and now - q[0] > RATE_WINDOW:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Juda ko‘p urinish. Birozdan keyin qayta urinib ko‘ring.")
        q.append(now)


def _test() -> dict:
    try:
        return ft.load()
    except (ft.FinalTestError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"Yakuniy test faylida xato: {e}")


def _summary(r: dict) -> dict:
    return {k: r.get(k) for k in SUMMARY_FIELDS}


# ---------- Ochiq ----------
@public_router.get("")
def public_open():
    """Sahifa ochilishi bilan savollar shu yerdan olinadi."""
    return {"test": ft.public_view(_test())}


@public_router.post("/submit", status_code=201)
def public_submit(body: FinalSubmitIn, request: Request):
    test = _test()
    try:
        answers = ft.validate_answers(test, body.answers)
    except ft.FinalTestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    store = get_store()
    keys = ("participantNo", "submittedAt", "correct", "wrong", "total", "percent", "passPercent", "status")
    with _lock:
        # Ikki marta bosilsa yoki tarmoq qayta yuborsa — takroriy yozuv yaratilmaydi
        if body.client_id:
            existing = store.final_results.first(lambda r: r.get("clientId") == body.client_id)
            if existing:
                return {"result": {k: existing.get(k) for k in keys}, "duplicate": True}
        _rate_limit(request)
        g = ft.grade(test, answers)
        row = store.final_results.insert({
            "employeeId": None,
            "attemptNo": 1,
            "fullName": "",
            "position": "",
            "department": "",
            "testSlug": test["slug"],
            "testTitle": test["title"],
            "submittedAt": now_local(),
            "durationSec": body.duration_sec,
            "clientId": body.client_id,
            "answers": {str(k): v for k, v in answers.items()},
            **{k: v for k, v in g.items() if k != "passed"},
        })
        # Ishtirokchi raqami = yozuv raqami (CRM’da "Ishtirokchi #N")
        row = store.final_results.update(row["id"], {"participantNo": row["id"]})
    return {"result": {k: row.get(k) for k in keys}}


# ---------- HR ----------
@router.get("/final-test/info")
def info():
    test = _test()
    return {"title": test["title"], "questions": len(test["questions"]), "passPercent": test["passPercent"], "path": f"/test/{ft.FINAL_SLUG}"}


@router.get("/final-results")
def list_results():
    rows = get_store().final_results.all()
    rows.sort(key=lambda r: (r.get("submittedAt") or "", r["id"]), reverse=True)
    return [_summary(r) for r in rows]


@router.get("/final-results/{result_id}")
def get_result(result_id: int):
    row = get_or_404(get_store().final_results, result_id, "Natija")
    for hidden in ("tokenId", "clientId"):
        row.pop(hidden, None)
    return row


@router.delete("/final-results/{result_id}", status_code=204)
def delete_result(result_id: int):
    store = get_store()
    get_or_404(store.final_results, result_id, "Natija")
    store.final_results.delete(result_id)
    return Response(status_code=204)
