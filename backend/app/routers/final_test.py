"""
Yakuniy bilim testi (/test/yakuniy) — ochiq test (login yo‘q), savollardan oldin ishtirokchi ro‘yxatdan o‘tadi.

Ochiq (login yo‘q):
    GET  /public/final-test            20 ta savol (to‘g‘ri javoblarsiz)
    POST /public/final-test/register   { firstName, lastName, age, birthDate, clientId? }
                                       → { participant: { id, key, firstName, lastName, fullName, age, birthDate } }
    POST /public/final-test/submit     { participantId, participantKey, answers, durationSec?, clientId? }
                                       → { result: { submittedAt, fullName }, message } — FAQAT neytral tasdiq.
                                       Ball, foiz, to‘g‘ri/xato soni va holat serverda hisoblanib saqlanadi,
                                       lekin nomzodga (javobda ham, takroriy yuborishda ham) qaytarilmaydi.

Ishtirokchilar data/final_participants.json da saqlanadi (barqaror butun son id). Natija CRM’dagi xodim va
nomzod profiliga familiya + ism bo‘yicha bog‘lanadi (faqat yagona mos yozuv bo‘lsa — app/result_links.py).
"key" — faqat shu brauzerga beriladigan maxfiy kalit: natija
faqat to‘g‘ri id + kalit bilan bog‘lanadi, HR javoblarida kalit ko‘rsatilmaydi.

HR (login + HR/admin roli — security.hr_user):
    GET    /final-test/info            test haqida (savollar soni, o‘tish foizi)
    GET    /final-results              barcha topshirishlar (qisqa)
    GET    /final-results/{id}         batafsil: 20 ta savol, variantlar, tanlangan javob, to‘g‘ri javob
    DELETE /final-results/{id}         natijani o‘chirish
"""
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from .. import final_test as ft
from ..schemas import FinalRegisterIn, FinalSubmitIn
from ..result_links import candidate_brief, final_candidate_id, match_final_person
from ..security import hr_user
from ..store import _lock, get_store
from ..utils import get_or_404, now_local

public_router = APIRouter(prefix="/public/final-test", tags=["Yakuniy test (ochiq)"])
router = APIRouter(tags=["Yakuniy bilim testi"], dependencies=[Depends(hr_user)])

SUMMARY_FIELDS = (
    "id", "participantNo", "participantId", "employeeId", "candidateId", "attemptNo", "fullName", "firstName", "lastName", "age",
    "birthDate", "position", "department", "submittedAt", "durationSec", "correct", "wrong", "total", "points",
    "maxPoints", "percent", "passPercent", "status", "testTitle", "testSlug",
)
# Nomzodga qaytariladigan yagona ma'lumot: topshirilgani tasdig‘i (ball, foiz, holat — yo‘q)
SUBMIT_MESSAGE = "Test muvaffaqiyatli yakunlandi. Natijangiz HR mutaxassisi tomonidan ko‘rib chiqiladi"
PUBLIC_RESULT_FIELDS = ("submittedAt", "fullName")
# Ishtirokchining HR uchun ko‘rinadigan maydonlari (maxfiy kalit va clientId — yo‘q)
PARTICIPANT_FIELDS = ("id", "firstName", "lastName", "fullName", "age", "birthDate", "registeredAt")

# Ochiq testni suiiste’moldan himoya: bitta IP manzildan 1 soatda ko‘pi bilan 60 ta topshirish
# va 60 ta ro‘yxatdan o‘tish (har biri alohida hisoblanadi)
RATE_LIMIT, RATE_WINDOW = 60, 3600
_hits: dict[str, deque] = defaultdict(deque)
_hits_lock = threading.Lock()


def _rate_limit(request: Request, bucket: str = "submit") -> None:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "?")
    now = time.monotonic()
    with _hits_lock:
        q = _hits[f"{bucket}:{ip}"]
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
    out = {k: r.get(k) for k in SUMMARY_FIELDS}
    out["candidateId"] = final_candidate_id(get_store(), r)
    return out


def _public_ack(row: dict, **extra) -> dict:
    """Nomzodga javob: faqat "qabul qilindi" — baholash natijasi umuman yuborilmaydi."""
    return {"result": {k: row.get(k) for k in PUBLIC_RESULT_FIELDS}, "message": SUBMIT_MESSAGE, **extra}


def _participant_public(p: dict, with_key: bool = False) -> dict:
    """Ishtirokchining o‘ziga qaytariladigan ma'lumot (kalit faqat ro‘yxatdan o‘tgan brauzerga beriladi)."""
    out = {k: p.get(k) for k in PARTICIPANT_FIELDS}
    if with_key:
        out["key"] = p["accessKey"]
    return out


def _same_person(p: dict, data: dict) -> bool:
    return all(p.get(k) == data[k] for k in ("firstName", "lastName", "age", "birthDate"))


# ---------- Ochiq ----------
@public_router.get("")
def public_open():
    """Sahifa ochilishi bilan savollar shu yerdan olinadi."""
    return {"test": ft.public_view(_test())}


@public_router.post("/register", status_code=201)
def public_register(body: FinalRegisterIn, request: Request):
    """Testdan oldingi ro‘yxatdan o‘tish. Ma'lumotlar shu yerda tekshiriladi — xato bo‘lsa 400 va o‘zbekcha sabab."""
    try:
        data = ft.validate_participant(body.first_name, body.last_name, body.age, body.birth_date)
    except ft.FinalTestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    store = get_store()
    with _lock:
        # Ikki marta bosilsa yoki tarmoq qayta yuborsa — o‘sha ishtirokchi qaytariladi (yangisi yaratilmaydi)
        if body.client_id:
            existing = store.final_participants.first(lambda p: p.get("clientId") == body.client_id)
            if existing:
                if not _same_person(existing, data):
                    raise HTTPException(status_code=409, detail="Ma’lumotlar o‘zgargan. Sahifani yangilab, qayta yuboring.")
                return {"participant": _participant_public(existing, with_key=True), "duplicate": True}
        _rate_limit(request, "register")
        row = store.final_participants.insert({
            **data,
            "testSlug": ft.FINAL_SLUG,
            "registeredAt": now_local(),
            "clientId": body.client_id,
            "accessKey": secrets.token_urlsafe(24),
            "source": "landing-2",
        })
    return {"participant": _participant_public(row, with_key=True)}


@public_router.post("/submit", status_code=201)
def public_submit(body: FinalSubmitIn, request: Request):
    test = _test()
    if not body.participant_id or not body.participant_key:
        raise HTTPException(status_code=400, detail="Avval shaxsiy ma’lumotlaringizni kiriting (ism, familiya, yosh, tug‘ilgan sana).")
    try:
        answers = ft.validate_answers(test, body.answers)
    except ft.FinalTestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    store = get_store()
    with _lock:
        participant = store.final_participants.get(body.participant_id)
        if not participant or not hmac.compare_digest(str(participant.get("accessKey", "")), body.participant_key):
            raise HTTPException(
                status_code=403,
                detail="Ishtirokchi ma’lumotlari topilmadi yoki eskirgan. Ma’lumotlaringizni qayta kiriting.",
            )
        # Ikki marta bosilsa yoki tarmoq qayta yuborsa — takroriy yozuv yaratilmaydi
        if body.client_id:
            existing = store.final_results.first(lambda r: r.get("clientId") == body.client_id)
            if existing:
                return _public_ack(existing, duplicate=True)
        _rate_limit(request)
        g = ft.grade(test, answers)  # baholash faqat serverda
        employee_id, candidate_id = match_final_person(
            store, participant["lastName"], participant["firstName"], participant.get("age"), participant.get("birthDate") or "")
        attempt_no = store.final_results.count(participantId=participant["id"]) + 1
        row = store.final_results.insert({
            "employeeId": employee_id,
            "candidateId": candidate_id,
            "participantId": participant["id"],
            "attemptNo": attempt_no,
            # Topshirish paytidagi nusxa — natija keyin ham o‘zgarmasdan qoladi
            "firstName": participant["firstName"],
            "lastName": participant["lastName"],
            "fullName": participant["fullName"],
            "age": participant["age"],
            "birthDate": participant["birthDate"],
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
    return _public_ack(row)


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
    store = get_store()
    row = get_or_404(store.final_results, result_id, "Natija")
    for hidden in ("tokenId", "clientId"):
        row.pop(hidden, None)
    participant = store.final_participants.get(row["participantId"]) if row.get("participantId") else None
    row["participant"] = {k: participant.get(k) for k in PARTICIPANT_FIELDS} if participant else None
    row["candidateId"] = final_candidate_id(store, row)
    row["candidate"] = candidate_brief(store.candidates.get(row["candidateId"])) if row["candidateId"] else None
    return row


@router.delete("/final-results/{result_id}", status_code=204)
def delete_result(result_id: int):
    store = get_store()
    get_or_404(store.final_results, result_id, "Natija")
    store.final_results.delete(result_id)
    return Response(status_code=204)