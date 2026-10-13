"""
Yakuniy bilim testi (7 kunlik darslardan keyin) — savollar, javoblar kaliti va baholash.

Savollar va kalit:  app/landing_tests/yakuniy.json  (correct — to‘g‘ri variant harfi)
Natijalar:          data/final_results.json  (har bir topshirish alohida yozuv)

Ishtirokchilar:     data/final_participants.json  (testdan oldin ro‘yxatdan o‘tganlar)

Test ochiq: /test/yakuniy sahifasiga kirgan har kim topshira oladi (havola yoki token talab qilinmaydi),
lekin savollardan oldin ism, familiya, yosh va tug‘ilgan sana kiritiladi (validate_participant).
Baholash faqat backendda: har bir to‘g‘ri javob — 1 ball (jami 20);
foiz >= passPercent (80, ya'ni 16–20 ball) → "O‘tdi", aks holda (0–15 ball) → "O‘tmadi".
"""
import copy
import json
import re
from datetime import date, timedelta

from .landing import LANDING_DIR

FINAL_SLUG = "yakuniy"
LETTERS = "ABCDEFGH"
STATUS_PASSED = "O‘tdi"
STATUS_FAILED = "O‘tmadi"

# Ishtirokchi ma'lumotlari chegaralari (nomzodlar testi — landing/ bilan bir xil yosh oralig‘i)
AGE_MIN, AGE_MAX = 16, 70
NAME_MIN, NAME_MAX = 2, 50
# Harflar (lotin, kirill va h.k.), o‘zbekcha tutuq belgilari (' ʻ ʼ ‘ ’ `), chiziqcha va bo‘sh joy
_NAME_RE = re.compile(r"^[^\W\d_](?:[^\W\d_]|[̀-ͯ '\-ʻʼ‘’`])*$")

_cache: dict = {}


class FinalTestError(ValueError):
    pass


def age_on(birth: date, on: date) -> int:
    """To‘liq yillar soni (tug‘ilgan kun hali kelmagan bo‘lsa — bir yil kam)."""
    return on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))


def _clean_name(value: str, label: str) -> str:
    v = " ".join(str(value or "").split())
    if not v:
        raise FinalTestError(f"{label}ni kiriting")
    if len(v) < NAME_MIN:
        raise FinalTestError(f"{label} kamida {NAME_MIN} ta harfdan iborat bo‘lsin")
    if len(v) > NAME_MAX:
        raise FinalTestError(f"{label} {NAME_MAX} ta belgidan oshmasin")
    if not _NAME_RE.fullmatch(v):
        raise FinalTestError(f"{label}da faqat harflar, tutuq belgisi (ʻ) va chiziqcha (-) bo‘lishi mumkin")
    return v


def validate_participant(first_name, last_name, age, birth_date, today: date | None = None) -> dict:
    """
    Ishtirokchi ma'lumotlarini serverda tekshiradi (frontend tekshiruviga ishonilmaydi).
    Yosh tug‘ilgan sanadan hisoblangan yoshga teng bo‘lishi kerak; vaqt mintaqalari farqi uchun
    bugungi sanadan ±1 kun bo‘yicha hisoblangan yosh ham qabul qilinadi.
    """
    first = _clean_name(first_name, "Ism")
    last = _clean_name(last_name, "Familiya")

    if age is None or age == "" or isinstance(age, bool):
        raise FinalTestError("Yoshingizni kiriting")
    if isinstance(age, float) and age.is_integer():
        age = int(age)
    if isinstance(age, str) and re.fullmatch(r"\s*\d{1,3}\s*", age):
        age = int(age)
    if not isinstance(age, int):
        raise FinalTestError("Yosh butun son bo‘lishi kerak")
    if not AGE_MIN <= age <= AGE_MAX:
        raise FinalTestError(f"Yosh {AGE_MIN} dan {AGE_MAX} gacha bo‘lishi kerak")

    raw = str(birth_date or "").strip()
    if not raw:
        raise FinalTestError("Tug‘ilgan sanani tanlang")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        raise FinalTestError("Tug‘ilgan sana noto‘g‘ri formatda")
    try:
        birth = date.fromisoformat(raw)
    except ValueError:
        raise FinalTestError("Bunday sana mavjud emas")
    today = today or date.today()
    if birth > today + timedelta(days=1):
        raise FinalTestError("Tug‘ilgan sana kelajakdagi sana bo‘lishi mumkin emas")
    if birth.year < 1900:
        raise FinalTestError("Tug‘ilgan sana noto‘g‘ri")
    possible = {age_on(birth, today + timedelta(days=d)) for d in (-1, 0, 1)}
    if age not in possible:
        raise FinalTestError(f"Yosh tug‘ilgan sanaga mos emas: tug‘ilgan sanaga ko‘ra {age_on(birth, today)} yosh")

    return {
        "firstName": first,
        "lastName": last,
        "fullName": f"{last} {first}",  # o‘zbekcha tartib: Familiya Ism (CRM’dagi boshqa ro‘yxatlar bilan bir xil)
        "age": age,
        "birthDate": birth.isoformat(),
    }


def load() -> dict:
    """yakuniy.json ni o‘qiydi va tekshiradi (fayl o‘zgarsa avtomatik qayta o‘qiladi)."""
    path = LANDING_DIR / f"{FINAL_SLUG}.json"
    if not path.is_file():
        raise FinalTestError("yakuniy.json topilmadi")
    mtime = path.stat().st_mtime
    if _cache.get("mtime") != mtime:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("_izoh", None)
        questions = data.get("questions") or []
        if not questions:
            raise FinalTestError("yakuniy.json: savollar yo‘q")
        ids = set()
        for q in questions:
            qid = q.get("id")
            if not isinstance(qid, int) or qid in ids:
                raise FinalTestError(f"yakuniy.json: savol id noto‘g‘ri yoki takrorlangan ({qid})")
            ids.add(qid)
            opts = q.get("options") or []
            if not 2 <= len(opts) <= len(LETTERS) or not all(isinstance(o, str) and o.strip() for o in opts):
                raise FinalTestError(f"yakuniy.json: {qid}-savol variantlari noto‘g‘ri")
            letter = str(q.get("correct", "")).strip().upper()
            if len(letter) != 1 or LETTERS.find(letter) < 0 or LETTERS.find(letter) >= len(opts):
                raise FinalTestError(f"yakuniy.json: {qid}-savol uchun to‘g‘ri javob (correct) A–{LETTERS[len(opts) - 1]} bo‘lishi kerak")
            q["correctIndex"] = LETTERS.find(letter)
        data.setdefault("passPercent", 80)
        _cache.update(mtime=mtime, data=data)
    return copy.deepcopy(_cache["data"])


def public_view(test: dict) -> dict:
    """Sahifaga yuboriladigan shakl — to‘g‘ri javoblarsiz (kalit faqat backendda)."""
    return {
        "slug": test["slug"],
        "title": test["title"],
        "subtitle": test.get("subtitle", ""),
        "passPercent": test["passPercent"],
        "questions": [{"id": q["id"], "text": q["text"], "options": q["options"]} for q in test["questions"]],
    }


def validate_answers(test: dict, answers: dict) -> dict[int, int]:
    """Barcha savollarga javob berilganini va har bir javob mavjud variant ekanini tekshiradi."""
    clean, missing = {}, []
    for q in test["questions"]:
        raw = answers.get(str(q["id"]), answers.get(q["id"]))
        if raw is None or isinstance(raw, bool):
            missing.append(q["id"])
            continue
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise FinalTestError(f"{q['id']}-savol javobi noto‘g‘ri")
        if not 0 <= value < len(q["options"]):
            raise FinalTestError(f"{q['id']}-savol uchun bunday variant yo‘q")
        clean[q["id"]] = value
    if missing:
        raise FinalTestError(f"Barcha savollarga javob bering. Javobsiz: {', '.join(map(str, missing))}")
    extra = {str(k) for k in answers} - {str(q["id"]) for q in test["questions"]}
    if extra:
        raise FinalTestError("Noma’lum savol raqami yuborildi")
    return clean


def grade(test: dict, answers: dict[int, int]) -> dict:
    """Har bir to‘g‘ri javob — 1 ball. Savollar nusxasi bilan qaytaradi (HR tahlili uchun)."""
    items = []
    for q in test["questions"]:
        a = answers[q["id"]]
        items.append({
            "id": q["id"], "text": q["text"], "options": q["options"],
            "correctIndex": q["correctIndex"], "answer": a, "isCorrect": a == q["correctIndex"],
        })
    total = len(items)
    correct = sum(i["isCorrect"] for i in items)
    percent = round(correct / total * 100) if total else 0
    passed = percent >= int(test["passPercent"])
    return {
        "items": items, "total": total, "correct": correct, "wrong": total - correct,
        "points": correct, "maxPoints": total, "percent": percent, "passPercent": int(test["passPercent"]),
        "passed": passed, "status": STATUS_PASSED if passed else STATUS_FAILED,
    }