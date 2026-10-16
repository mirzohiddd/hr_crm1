"""
Nomzodlar uchun ochiq test (landing) — savolnoma, baholash kaliti va hisoblash.

Savolnomalar: app/landing_tests/<slug>.json (masalan, sotuv.json).
Natijalar:    data/landing_results.json

Formatlar:
- "format": "persona" (joriy sotuv.json) — «Ishdagi shaxsiyat 360»: 40 ta savol, 4 bosqich × 10,
  javob 0 = «Qo‘shilmayman», 1 = «Qo‘shilaman»; 13 xususiyat, 4 yo‘nalish, diqqat tekshiruvi.
  Hisoblash va HR hisoboti — app/persona_test.py.
- "format": "profile" — 4 shkalali 40 savolli test (app/profile_test.py); avval saqlangan natijalar uchun.
- eski format (scale/choice) — quyidagi qoidalar bo‘yicha (o‘zgarmagan).

Baholash (eski format, HR bilan kelishilgan kalit):
- scale (1–5): key=direct → ball = tanlangan raqam; key=reverse → ball = 6 - tanlangan raqam.
  Maksimal ball har savolda 5.
- choice (A/B/C/D): har bir variantning "points" qiymati; maksimal ball — eng yuqori variant bali.
- Foiz = to‘plangan / maksimal * 100 (butun songa yaxlitlanadi); foiz >= passPercent → O‘tdi, aks holda Yiqildi.
"""
import copy
import json
import re
from pathlib import Path

from . import persona_test as ps
from . import profile_test as pt

FORMAT_PROFILE = "profile"
FORMAT_PERSONA = "persona"
LANDING_DIR = Path(__file__).resolve().parent / "landing_tests"
LETTERS = "ABCDEFGH"
STATUS_PASSED = "O‘tdi"
STATUS_FAILED = "Yiqildi"

_cache: dict[str, tuple[float, dict]] = {}


class QuestionnaireError(ValueError):
    pass


def _validate(q: dict, path: Path) -> dict:
    scale = q.get("scale") or {}
    lo, hi = int(scale.get("min", 1)), int(scale.get("max", 5))
    if lo >= hi:
        raise QuestionnaireError(f"{path.name}: scale noto‘g‘ri")
    ids = set()
    for item in q.get("questions", []):
        qid = item.get("id")
        if not isinstance(qid, int) or qid in ids:
            raise QuestionnaireError(f"{path.name}: savol id takrorlangan yoki noto‘g‘ri ({qid})")
        ids.add(qid)
        if item.get("type") == "scale":
            if item.get("key") not in ("direct", "reverse"):
                raise QuestionnaireError(f"{path.name}: {qid}-savol key 'direct' yoki 'reverse' bo‘lishi kerak")
        elif item.get("type") == "choice":
            opts = item.get("options") or []
            if len(opts) < 2 or any(not isinstance(o.get("points"), (int, float)) for o in opts):
                raise QuestionnaireError(f"{path.name}: {qid}-savol variantlari va ballari to‘liq emas")
        else:
            raise QuestionnaireError(f"{path.name}: {qid}-savol turi noma’lum")
    if not ids:
        raise QuestionnaireError(f"{path.name}: savollar yo‘q")
    return q


def load_questionnaire(slug: str) -> dict | None:
    """Savolnomani fayldan o‘qiydi (fayl o‘zgarsa, avtomatik qayta o‘qiladi)."""
    if not re.fullmatch(r"[a-z0-9-]{1,40}", slug or ""):
        return None
    path = LANDING_DIR / f"{slug}.json"
    if not path.is_file():
        return None
    mtime = path.stat().st_mtime
    cached = _cache.get(slug)
    if not cached or cached[0] != mtime:
        raw = json.loads(path.read_text(encoding="utf-8"))
        # Yakuniy bilim testi (kind=final) — boshqa format, final_test.py da ishlanadi
        if raw.get("kind") == "final":
            data = None
        elif raw.get("format") in (FORMAT_PROFILE, FORMAT_PERSONA):
            try:
                data = (ps if raw["format"] == FORMAT_PERSONA else pt).validate_config(raw)
            except ValueError as e:
                raise QuestionnaireError(f"{path.name}: {e}")
        else:
            data = _validate(raw, path)
        if data:
            data.pop("_izoh", None)
        _cache[slug] = (mtime, data)
    return copy.deepcopy(_cache[slug][1])


def list_questionnaires() -> list[dict]:
    out = []
    for p in sorted(LANDING_DIR.glob("*.json")):
        q = load_questionnaire(p.stem)
        if q:
            out.append(q)
    return out


def is_profile(q: dict) -> bool:
    """Bosqichli (4 × 10) «Qo‘shilmayman»/«Qo‘shilaman» testi: persona yoki profile formati."""
    return q.get("format") in (FORMAT_PROFILE, FORMAT_PERSONA)


def is_persona(q: dict) -> bool:
    return q.get("format") == FORMAT_PERSONA


def position_names(q: dict) -> list[str]:
    """Ro‘yxatdan o‘tishdagi lavozimlar: eski formatda satrlar, profil formatida {name, weights} obyektlari."""
    return [p["name"] if isinstance(p, dict) else p for p in q.get("positions") or []]


def scale_bounds(q: dict) -> tuple[int, int]:
    s = q.get("scale") or {}
    return int(s.get("min", 1)), int(s.get("max", 5))


def public_view(q: dict) -> dict:
    """Nomzodga ko‘rinadigan shakl — baholash kaliti (key, keyNote, points) olib tashlanadi."""
    if is_profile(q):
        return {
            "slug": q["slug"], "format": q["format"], "title": q["title"],
            "subtitle": q.get("subtitle", ""), "description": q.get("description", ""),
            "positions": position_names(q), "options": q["options"],
            "stageSize": q.get("stageSize", 10), "stages": (ps if is_persona(q) else pt).stages(q),
            # Kalit (key, scale, samimiylik, og‘irliklar) yuborilmaydi — faqat matn va variantlar
            "questions": [{"id": i["id"], "text": i["text"], "options": i["options"]} for i in q["questions"]],
        }
    q = copy.deepcopy(q)
    for item in q["questions"]:
        item.pop("key", None)
        item.pop("keyNote", None)
        if item["type"] == "choice":
            item["options"] = [o["text"] for o in item["options"]]
    return q


def _max_points(q: dict, item: dict) -> float:
    lo, hi = scale_bounds(q)
    if item["type"] == "scale":
        return hi
    return max(o["points"] for o in item["options"])


def answer_key(q: dict) -> list[dict]:
    """HR uchun baholash kaliti: har savolda qaysi javob qancha ball beradi."""
    if is_persona(q):
        titles = {t["id"]: t["title"] for t in q["traits"]}
        rows = []
        for item in q["questions"]:
            if item.get("attention"):
                choices = [{"label": str(i), "text": t, "points": int(i == item["expected"])} for i, t in enumerate(q["options"])]
                rows.append({"id": item["id"], "section": "attention", "type": "agree", "text": item["text"], "key": None,
                             "attention": True, "keyNote": f"Diqqat tekshiruvi: to‘g‘ri javob — «{q['options'][item['expected']]}»",
                             "choices": [{**c, "best": c["points"] == 1} for c in choices], "maxPoints": 1})
                continue
            choices = [{"label": str(i), "text": t, "points": ps.item_point(item["key"], i)} for i, t in enumerate(q["options"])]
            rows.append({
                "id": item["id"], "section": item["trait"], "type": "agree", "text": item["text"], "key": item["key"],
                "keyNote": titles[item["trait"]] + (" · teskari savol" if item["key"] == "reverse" else ""),
                "choices": [{**c, "best": c["points"] == 1} for c in choices], "maxPoints": 1,
            })
        return rows
    if is_profile(q):
        titles = {s["id"]: s["title"] for s in q["scales"]}
        sid = q["sincerity"]["id"]
        rows = []
        for item in q["questions"]:
            sincere = item["scale"] == sid
            choices = [{"label": str(i), "text": t, "points": pt.item_point(item["key"], i)} for i, t in enumerate(q["options"])]
            rows.append({
                "id": item["id"], "section": item["scale"], "type": "agree", "text": item["text"],
                "key": item["key"], "sincerity": sincere,
                "keyNote": ("Samimiylik savoli: 1 — samimiy javob (asosiy ko‘rsatkichlarga qo‘shilmaydi)" if sincere
                            else f"{titles[item['scale']]}" + (" · teskari savol" if item["key"] == "reverse" else "")),
                "choices": [{**c, "best": c["points"] == 1} for c in choices],
                "maxPoints": 1,
            })
        return rows
    lo, hi = scale_bounds(q)
    labels = (q.get("scale") or {}).get("labels") or []
    rows = []
    for item in q["questions"]:
        if item["type"] == "scale":
            values = list(range(lo, hi + 1))
            pts = [(v if item["key"] == "direct" else lo + hi - v) for v in values]
            choices = [
                {"label": str(v), "text": labels[i] if i < len(labels) else str(v), "points": p}
                for i, (v, p) in enumerate(zip(values, pts))
            ]
        else:
            choices = [{"label": LETTERS[i], "text": o["text"], "points": o["points"]} for i, o in enumerate(item["options"])]
        best = max(c["points"] for c in choices)
        rows.append({
            "id": item["id"], "section": item.get("section"), "type": item["type"], "text": item["text"],
            "key": item.get("key"), "keyNote": item.get("keyNote", ""),
            "choices": [{**c, "best": c["points"] == best} for c in choices],
            "maxPoints": best,
        })
    return rows


def validate_answers(q: dict, answers: dict) -> dict[int, int]:
    """Barcha savollarga javob berilganini va qiymatlar chegarada ekanini tekshiradi."""
    lo, hi = scale_bounds(q)
    clean: dict[int, int] = {}
    missing = []
    for item in q["questions"]:
        raw = answers.get(str(item["id"]), answers.get(item["id"]))
        if raw is None or isinstance(raw, bool):
            missing.append(item["id"])
            continue
        if isinstance(raw, float) and not raw.is_integer():
            raise QuestionnaireError(f"{item['id']}-savol javobi noto‘g‘ri")
        if is_profile(q):
            try:
                value = int(raw)
            except (TypeError, ValueError):
                raise QuestionnaireError(f"{item['id']}-savol javobi noto‘g‘ri")
            if value not in (0, 1):
                raise QuestionnaireError(f"{item['id']}-savol javobi «Qo‘shilmayman» (0) yoki «Qo‘shilaman» (1) bo‘lishi kerak")
            clean[item["id"]] = value
            continue
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise QuestionnaireError(f"{item['id']}-savol javobi noto‘g‘ri")
        if item["type"] == "scale" and not lo <= value <= hi:
            raise QuestionnaireError(f"{item['id']}-savol javobi {lo}–{hi} oralig‘ida bo‘lishi kerak")
        if item["type"] == "choice" and not 0 <= value < len(item["options"]):
            raise QuestionnaireError(f"{item['id']}-savol uchun bunday variant yo‘q")
        clean[item["id"]] = value
    if missing:
        raise QuestionnaireError(f"Barcha savollarga javob bering. Javobsiz: {', '.join(map(str, missing))}")
    extra = {str(k) for k in answers} - {str(i["id"]) for i in q["questions"]}
    if is_profile(q) and extra:
        raise QuestionnaireError("Noma’lum savol raqami yuborildi")
    return clean


def score(q: dict, answers: dict[int, int], duration_sec: int | None = None, full_name: str = "") -> dict:
    """Javoblarni kalit bo‘yicha baholaydi va har bir savol tahlilini qaytaradi."""
    if is_persona(q):
        return ps.grade(q, answers, duration_sec, full_name)
    if is_profile(q):
        g = pt.grade(q, answers, duration_sec)
        # Ro‘yxat uchun "sections" — shkalalar bo‘yicha ball (eski natijalar bilan bir xil shakl)
        g["sections"] = [{"id": s["id"], "title": s["title"], "points": s["points"], "maxPoints": s["max"], "percent": s["percent"]}
                         for s in g["report"]["scales"]]
        return g
    key = {row["id"]: row for row in answer_key(q)}
    lo, _ = scale_bounds(q)
    items, earned_total, max_total = [], 0, 0
    for item in q["questions"]:
        k = key[item["id"]]
        value = answers[item["id"]]
        idx = value - lo if item["type"] == "scale" else value
        chosen = k["choices"][idx]
        earned_total += chosen["points"]
        max_total += k["maxPoints"]
        items.append({
            **k,
            "answer": value,
            "answerLabel": chosen["label"],
            "answerText": chosen["text"],
            "points": chosen["points"],
        })
    percent = round(earned_total / max_total * 100) if max_total else 0
    pass_percent = int(q.get("passPercent", 80))
    passed = percent >= pass_percent
    sections = []
    for s in q.get("sections", []):
        sec = [i for i in items if i["section"] == s["id"]]
        if sec:
            sections.append({
                "id": s["id"], "title": s["title"],
                "points": sum(i["points"] for i in sec), "maxPoints": sum(i["maxPoints"] for i in sec),
            })
    return {
        "items": items,
        "points": earned_total,
        "maxPoints": max_total,
        "percent": percent,
        "passPercent": pass_percent,
        "passed": passed,
        "status": STATUS_PASSED if passed else STATUS_FAILED,
        "sections": sections,
    }