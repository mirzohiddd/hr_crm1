"""
Nomzodlar uchun ochiq test (landing) va HR uchun natijalar.

Joriy test (sotuv.json, format=profile): yangi kelgan xodimlar uchun 40 ta fikr, 4 bosqich × 10,
javob 0 = «Qo‘shilmayman», 1 = «Qo‘shilaman». Hisoblash va HR hisoboti — app/profile_test.py.

Ochiq (login talab qilinmaydi):
    GET  /public/tests/{slug}          savolnoma (baholash kalitisiz) + bosqichlar (stages)
    POST /public/tests/{slug}/submit   javoblarni yuborish — hisoblash serverda.
                                       Natija F.I.Sh. bilan saqlanadi; xodimlar ro‘yxatida F.I.Sh. mos keladigan
                                       YAGONA xodim bo‘lsa, natija unga ham bog‘lanadi (employeeId).

HR (login bilan):
    GET    /landing-tests                     savolnomalar ro‘yxati
    GET    /landing-tests/{slug}/key          baholash kaliti
    GET    /landing-results                   natijalar ro‘yxati
    GET    /landing-results/{id}              batafsil: savollar, javoblar; profil testida — HR hisoboti (report, reportText)
    PATCH  /landing-results/{id}/viewed       "ko‘rildi" belgisi
    DELETE /landing-results/{id}
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from .. import landing
from .. import profile_test as pt
from ..schemas import LandingSubmitIn
from ..security import current_user
from ..store import get_store
from ..utils import bad_request, get_or_404, not_found, now_local

public_router = APIRouter(prefix="/public", tags=["Landing (ochiq)"])
router = APIRouter(tags=["Landing natijalari"], dependencies=[Depends(current_user)])

# Oddiy himoya: bitta IP manzildan 1 soatda ko‘pi bilan 20 ta topshirish
RATE_LIMIT, RATE_WINDOW = 20, 3600
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


def _questionnaire(slug: str) -> dict:
    try:
        q = landing.load_questionnaire(slug)
    except (landing.QuestionnaireError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"Savolnoma faylida xato: {e}")
    if not q:
        raise not_found("Test")
    return q


SUMMARY_FIELDS = (
    "id", "testSlug", "testTitle", "fullName", "age", "date", "position", "phone", "submittedAt",
    "points", "maxPoints", "percent", "passPercent", "status", "viewed", "durationSec", "sections",
    # Profil testi: shkalalar foizi, ishonchlilik, eng mos lavozim, bog‘langan xodim
    "format", "scores", "reliability", "bestPosition", "employeeId",
)


def _norm(v) -> str:
    return " ".join(str(v or "").replace("ʻ", "‘").replace("'", "‘").replace("`", "‘").replace("’", "‘").split()).casefold()


def _match_employee(store, full_name: str) -> dict | None:
    """
    Natijani xodimga bog‘lash: F.I.Sh. dagi familiya va ism (otasining ismi ham yozilgan bo‘lsa — u ham) mos keladigan
    xodim YAGONA bo‘lsagina. Bir nechta mos xodim bo‘lsa — bog‘lanmaydi (noto‘g‘ri bog‘lashdan himoya).
    """
    parts = _norm(full_name).split(" ")
    if len(parts) < 2:
        return None
    last, first, middle = parts[0], parts[1], " ".join(parts[2:])

    def ok(e):
        if _norm(e.get("lastName")) != last or _norm(e.get("firstName")) != first:
            return False
        em = _norm(e.get("middleName"))
        return not (middle and em) or em == middle

    found = store.employees.filter()
    found = [e for e in found if ok(e)]
    return found[0] if len(found) == 1 else None


def _summary(row: dict) -> dict:
    return {k: row.get(k) for k in SUMMARY_FIELDS}


# ---------- Ochiq ----------
@public_router.get("/tests/{slug}")
def public_test(slug: str):
    return landing.public_view(_questionnaire(slug))


@public_router.post("/tests/{slug}/submit", status_code=201)
def public_submit(slug: str, body: LandingSubmitIn, request: Request):
    q = _questionnaire(slug)
    store = get_store()
    # Ikki marta bosilsa yoki tarmoq qayta yuborsa — takroriy yozuv yaratilmaydi
    if body.client_id:
        existing = store.landing_results.first(lambda r: r.get("clientId") == body.client_id)
        if existing:
            return {"id": existing["id"], "submittedAt": existing["submittedAt"], "duplicate": True}
    if q.get("positions") and body.position not in landing.position_names(q):
        raise bad_request("Lavozim noto‘g‘ri tanlangan")
    try:
        answers = landing.validate_answers(q, body.answers)
    except landing.QuestionnaireError as e:
        raise bad_request(str(e))
    _rate_limit(request)

    result = landing.score(q, answers, body.duration_sec)
    employee = _match_employee(store, body.full_name) if landing.is_profile(q) else None
    row = store.landing_results.insert({
        "employeeId": employee["id"] if employee else None,
        "testSlug": q["slug"],
        "testTitle": q["title"],
        "fullName": body.full_name,
        "age": body.age,
        "date": body.date,
        "position": body.position,
        "phone": body.phone,
        "submittedAt": now_local(),
        "durationSec": body.duration_sec,
        "clientId": body.client_id,
        "answers": {str(k): v for k, v in answers.items()},
        "scale": q.get("scale"),
        "sectionsInfo": q.get("sections", []),
        "viewed": False,
        **result,
    })
    # Nomzodga ball ko‘rsatilmaydi — natijani HR ko‘radi
    return {"id": row["id"], "submittedAt": row["submittedAt"]}


# ---------- HR ----------
@router.get("/landing-tests")
def hr_tests():
    return [
        {"slug": q["slug"], "title": q["title"], "format": q.get("format", "scale"), "questions": len(q["questions"]),
         "passPercent": q.get("passPercent", 80), "positions": landing.position_names(q)}
        for q in landing.list_questionnaires()
    ]


@router.get("/landing-tests/{slug}/key")
def hr_key(slug: str):
    q = _questionnaire(slug)
    key = landing.answer_key(q)
    if landing.is_profile(q):
        sid = q["sincerity"]["id"]
        return {
            "slug": q["slug"], "title": q["title"], "format": "profile", "options": q["options"],
            "stageSize": q.get("stageSize", 10), "passPercent": None,
            # Shkalalar "sections" shaklida (kalit oynasidagi jadvallar uchun) + samimiylik
            "sections": [{"id": s["id"], "title": s["title"], "description": s.get("description", "")} for s in q["scales"]]
                        + [{"id": sid, "title": q["sincerity"].get("title", "Samimiylik"),
                            "description": "Ishonchlilikni tekshiradi, asosiy ko‘rsatkichlarga qo‘shilmaydi"}],
            "pairs": q.get("pairs") or [],
            "positions": [{"name": p["name"], "weights": p["weights"]} for p in q.get("positions") or []],
            "rules": {
                "sincerityPenalty": pt.SINCERITY_PENALTY, "pairPenalty": pt.PAIR_PENALTY,
                "acquiescencePenalty": pt.ACQUIESCENCE_PENALTY, "fastPenalty": pt.FAST_PENALTY,
                "veryFastPenalty": pt.VERY_FAST_PENALTY, "recommendMinReliability": pt.RECOMMEND_MIN_RELIABILITY,
            },
            "maxPoints": sum(k["maxPoints"] for k in key if not k["sincerity"]), "questions": key,
        }
    return {
        "slug": q["slug"], "title": q["title"], "passPercent": q.get("passPercent", 80),
        "scale": q.get("scale"), "sections": q.get("sections", []),
        "maxPoints": sum(k["maxPoints"] for k in key), "questions": key,
    }


@router.get("/landing-results")
def hr_results():
    rows = get_store().landing_results.all()
    rows.sort(key=lambda r: (r.get("submittedAt") or "", r["id"]), reverse=True)
    return [_summary(r) for r in rows]


@router.get("/landing-results/{result_id}")
def hr_result(result_id: int):
    row = get_or_404(get_store().landing_results, result_id, "Natija")
    row.pop("clientId", None)
    if row.get("format") == "profile" and row.get("report"):
        # To‘liq matnli HR hisoboti (nusxalash uchun) — saqlangan natijadan tuziladi
        row["reportText"] = pt.report_text(row)
    return row


@router.patch("/landing-results/{result_id}/viewed")
def hr_mark_viewed(result_id: int):
    store = get_store()
    get_or_404(store.landing_results, result_id, "Natija")
    return _summary(store.landing_results.update(result_id, {"viewed": True}))


@router.delete("/landing-results/{result_id}", status_code=204)
def hr_delete(result_id: int):
    store = get_store()
    get_or_404(store.landing_results, result_id, "Natija")
    store.landing_results.delete(result_id)
    return Response(status_code=204)