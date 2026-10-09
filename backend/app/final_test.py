"""
Yakuniy bilim testi (7 kunlik darslardan keyin) — savollar, javoblar kaliti va baholash.

Savollar va kalit:  app/landing_tests/yakuniy.json  (correct — to‘g‘ri variant harfi)
Natijalar:          data/final_results.json  (har bir topshirish alohida yozuv)

Test ochiq: /test/yakuniy sahifasiga kirgan har kim topshira oladi (havola, token, ism talab qilinmaydi).
Baholash faqat backendda: har bir to‘g‘ri javob — 1 ball (jami 20);
foiz >= passPercent (80, ya'ni 16–20 ball) → "O‘tdi", aks holda (0–15 ball) → "O‘tmadi".
"""
import copy
import json

from .landing import LANDING_DIR

FINAL_SLUG = "yakuniy"
LETTERS = "ABCDEFGH"
STATUS_PASSED = "O‘tdi"
STATUS_FAILED = "O‘tmadi"

_cache: dict = {}


class FinalTestError(ValueError):
    pass


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
