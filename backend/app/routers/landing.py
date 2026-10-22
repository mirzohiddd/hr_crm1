"""
Nomzodlar uchun ochiq test (landing) va HR uchun natijalar.

Joriy test (sotuv.json, format=persona): «Ishdagi shaxsiyat 360» — 40 ta savol, 4 bosqich × 10,
javob 0 = «Qo‘shilmayman», 1 = «Qo‘shilaman». Hisoblash va HR hisoboti — app/persona_test.py
(avval saqlangan format=profile natijalari — app/profile_test.py).

Ochiq (login talab qilinmaydi):
    GET  /public/tests/{slug}          savolnoma (baholash kalitisiz) + bosqichlar (stages) + rasmli savollar (pictures)
    GET  /public/tests/{slug}/images/{name}  rasmli savol rasmi (landing va CRM hisobotida ko‘rsatiladi)
    POST /public/tests/{slug}/phone-check  { phone } — savollardan OLDIN: raqam to‘g‘ri va hali ishlatilmaganmi
                                       200 { phone: '+998 90 123 45 67', available: true } | 422 noto‘g‘ri | 409 band
    POST /public/tests/{slug}/submit   javoblarni yuborish — hisoblash serverda.
                                       Telefon majburiy; bitta raqam bilan faqat bitta natija (409 — band).
                                       persona testida: pictures = { rasm_id: variant_indeksi } (barcha rasmlar majburiy).
                                       Natija F.I.Sh. bilan saqlanadi; xodimlar ro‘yxatida F.I.Sh. mos keladigan
                                       YAGONA xodim bo‘lsa, natija unga ham bog‘lanadi (employeeId).

HR (login bilan):
    GET    /landing-tests                     savolnomalar ro‘yxati
    GET    /landing-tests/{slug}/key          baholash kaliti
    GET    /landing-results                   natijalar ro‘yxati
    GET    /landing-results/{id}              batafsil: savollar, javoblar; profil testida — HR hisoboti (report, reportText)
                                              persona testida foiz o‘rniga daraja va tavsiflar (persona_test.describe)
    PATCH  /landing-results/{id}/viewed       "ko‘rildi" belgisi
    DELETE /landing-results/{id}
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse

from .. import landing
from .. import persona_test as ps
from .. import profile_test as pt
from ..schemas import LandingPhoneCheckIn, LandingSubmitIn
from ..security import current_user
from ..store import get_store
from ..utils import bad_request, conflict, get_or_404, not_found, now_local, phone_key

public_router = APIRouter(prefix="/public", tags=["Landing (ochiq)"])
router = APIRouter(tags=["Landing natijalari"], dependencies=[Depends(current_user)])

# Oddiy himoya: bitta IP manzildan 1 soatda ko‘pi bilan 20 ta topshirish va 40 ta telefon tekshiruvi
# (raqamlarni ommaviy tekshirib chiqishdan himoya)
RATE_LIMIT, RATE_WINDOW = 20, 3600
LIMITS = {"submit": RATE_LIMIT, "phone": 40}
_hits: dict[str, deque] = defaultdict(deque)
_hits_lock = threading.Lock()

PHONE_TAKEN = "Bu telefon raqami bilan avval ro‘yxatdan o‘tilgan. Boshqa raqam kiriting yoki HR bo‘limiga murojaat qiling."


def _rate_limit(request: Request, bucket: str = "submit") -> None:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "?")
    now = time.monotonic()
    with _hits_lock:
        q = _hits[f"{bucket}:{ip}"]
        while q and now - q[0] > RATE_WINDOW:
            q.popleft()
        if len(q) >= LIMITS.get(bucket, RATE_LIMIT):
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
    # persona testi: profil nomi, ishonchlilik darajasi, samaradorlik / to‘sqinlik foizlari
    "profileTitle", "reliabilityLevel", "positive", "negative",
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
    out = {k: row.get(k) for k in SUMMARY_FIELDS}
    if row.get("format") == "persona":
        # Ro‘yxat va Excel uchun foiz o‘rniga so‘z bilan daraja
        out["positiveWord"] = ps.LEVEL_WORD[ps.positive_level(int(row.get("positive") or 0))]
        out["negativeWord"] = ps.LEVEL_WORD[ps.negative_level(int(row.get("negative") or 0))]
        if row.get("bestPosition"):
            out["bestPosition"] = {**row["bestPosition"], "fit": ps.role_fit(int(row["bestPosition"].get("percent") or 0))}
        out["traitLevels"] = [{"title": s.get("title"), "levelLabel": ps.TRAIT_LEVEL_LABEL[ps.trait_level(int(s.get("percent") or 0))]}
                              for s in row.get("sections") or []]
        pics = (row.get("report") or {}).get("pictures") or []
        # Qaysi rasmda qaysi variant tanlangani (ro‘yxat va Excel uchun): 1-rasm → B «Otlar»
        out["pictures"] = [{"title": p["title"], "answer": p.get("answer"), "letter": "ABCDEFGH"[p["answer"]] if isinstance(p.get("answer"), int) else "",
                            "answerText": p["answerText"]} for p in pics]
    return out


def _same_phone(key: str):
    """Saqlangan natijalarda shu raqam bormi (eski yozuvlar ham — har xil yozilgan bo‘lsa ham, oxirgi 9 raqam bo‘yicha)."""
    return lambda r: bool(key) and phone_key(r.get("phoneKey") or r.get("phone")) == key


# ---------- Ochiq ----------
@public_router.get("/tests/{slug}")
def public_test(slug: str):
    return landing.public_view(_questionnaire(slug))


@public_router.get("/tests/{slug}/images/{name}")
def public_test_image(slug: str, name: str):
    """Rasmli savol rasmi — faqat savolnomada ko‘rsatilgan fayllar."""
    if not ps.IMAGE_NAME_RE.fullmatch(name or ""):
        raise not_found("Rasm")
    _questionnaire(slug)
    path = landing.picture_path(slug, name)
    if not path:
        raise not_found("Rasm")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@public_router.post("/tests/{slug}/phone-check")
def public_phone_check(slug: str, body: LandingPhoneCheckIn, request: Request):
    """Savollarga o‘tishdan oldin: raqam formati (sxemada) va bandligi tekshiriladi."""
    _questionnaire(slug)
    _rate_limit(request, "phone")
    if get_store().landing_results.first(_same_phone(phone_key(body.phone))):
        raise conflict(PHONE_TAKEN)
    return {"phone": body.phone, "available": True}


@public_router.post("/tests/{slug}/submit", status_code=201)
def public_submit(slug: str, body: LandingSubmitIn, request: Request):
    q = _questionnaire(slug)
    store = get_store()
    # Ikki marta bosilsa yoki tarmoq qayta yuborsa — takroriy yozuv yaratilmaydi
    if body.client_id:
        existing = store.landing_results.first(lambda r: r.get("clientId") == body.client_id)
        if existing:
            return {"id": existing["id"], "submittedAt": existing["submittedAt"], "duplicate": True}
    key = phone_key(body.phone)
    if store.landing_results.first(_same_phone(key)):
        raise conflict(PHONE_TAKEN)
    if q.get("positions") and body.position not in landing.position_names(q):
        raise bad_request("Lavozim noto‘g‘ri tanlangan")
    try:
        answers = landing.validate_answers(q, body.answers)
        pictures = landing.validate_pictures(q, body.pictures)
    except landing.QuestionnaireError as e:
        raise bad_request(str(e))
    _rate_limit(request)

    result = landing.score(q, answers, body.duration_sec, body.full_name, pictures)
    employee = _match_employee(store, body.full_name) if landing.is_profile(q) else None
    # Noyoblik saqlash qatlamida ham: tekshirish + yozish bitta qulf ichida (bir vaqtdagi ikki so‘rov ham o‘tmaydi)
    row, taken = store.landing_results.insert_unique({
        "employeeId": employee["id"] if employee else None,
        "testSlug": q["slug"],
        "testTitle": q["title"],
        "fullName": body.full_name,
        "age": body.age,
        "date": body.date,
        "position": body.position,
        "phone": body.phone,
        "phoneKey": key,
        "submittedAt": now_local(),
        "durationSec": body.duration_sec,
        "clientId": body.client_id,
        "answers": {str(k): v for k, v in answers.items()},
        "scale": q.get("scale"),
        "sectionsInfo": q.get("sections", []),
        "viewed": False,
        **result,
    }, conflict=_same_phone(key))
    if taken:
        raise conflict(PHONE_TAKEN)
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
    if landing.is_persona(q):
        return {
            "slug": q["slug"], "title": q["title"], "format": "persona", "options": q["options"],
            "stageSize": q.get("stageSize", 10), "passPercent": None,
            "sections": [{"id": t["id"], "title": t["title"], "description": t.get("description", ""), "group": t["group"]}
                         for t in q["traits"]] + [{"id": "attention", "title": "Diqqat tekshiruvi",
                                                   "description": "Noto‘g‘ri javob — natija ishonchsiz"}],
            "directions": [{"id": d["id"], "title": d["title"], "traits": d["traits"], "goodHigh": d.get("goodHigh", True)}
                           for d in q.get("directions") or []],
            "pairs": q.get("pairs") or [],
            "roles": q.get("roles") or [],
            "maxPoints": sum(k["maxPoints"] for k in key if not k.get("attention")), "questions": key,
            # Rasmli savollar: har bir variant va HR uchun tavsifi
            "pictures": [{"id": p["id"], "title": p["title"], "question": p["question"],
                          "image": ps.image_url(q["slug"], p["image"]), "options": p["options"]}
                         for p in q.get("pictures") or []],
            "picturesNote": q.get("picturesNote") or ps.PICTURES_NOTE,
        }
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
    if row.get("format") == "persona" and row.get("report"):
        # Foiz o‘rniga daraja va tavsiflar — joriy savolnoma matnlaridan (eski natijalar uchun ham)
        try:
            q = landing.load_questionnaire(row.get("testSlug") or "")
        except (landing.QuestionnaireError, ValueError):
            q = None
        ps.describe(row["report"], q if q and landing.is_persona(q) else None)
        # Nusxalash uchun matn ("ISHDAGI SHAXSIYAT 360 — NATIJA") — saqlangan natijadan tuziladi, foizsiz
        row["reportText"] = ps.report_text(row)
    elif row.get("format") == "profile" and row.get("report"):
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