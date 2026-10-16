"""
Yangi kelgan xodimlar / nomzodlar uchun shaxsiy-kasbiy test (landing, /test/sotuv) — 40 ta fikr,
4 bosqich × 10 ta, javob: «Qo‘shilmayman» / «Qo‘shilaman».

Bu modul faqat hisoblash va HR hisobotini tuzadi. Savollar, shkalalar, kalit va lavozimlar:
    app/landing_tests/sotuv.json  ("format": "profile")
Landing bilan bog‘lanish: app/landing.py (yuklash, tekshirish) va app/routers/landing.py (saqlash, HR API).

Hisoblash qoidalari (hammasi haqiqiy javoblardan, tasodifiy son ishlatilmaydi):
1. Javob: 0 = «Qo‘shilmayman», 1 = «Qo‘shilaman».
2. Har bir savol bitta shkalaga tegishli va kalitga ega:
     key = "direct"  → «Qo‘shilaman» = 1 ball, «Qo‘shilmayman» = 0 ball
     key = "reverse" → teskari savol: «Qo‘shilmayman» = 1 ball, «Qo‘shilaman» = 0 ball
3. Shkala foizi = to‘plangan ball / shu shkaladagi savollar soni × 100 (butun songa yaxlitlanadi).
   Daraja: 75–100 — Yuqori, 50–74 — O‘rtacha, 0–49 — Past.
4. Samimiylik shkalasi (scale = sincerity.id) asosiy ko‘rsatkichlarga qo‘shilmaydi. Unda «hamma odamga xos»
   kamchiliklarni inkor etish (masalan, «Hech qachon yolg‘on gapirmaganman» — «Qo‘shilaman») ijtimoiy
   ma’qul ko‘rinishga intilish belgisi hisoblanadi. Samimiylik foizi = samimiy javoblar / samimiylik savollari × 100.
5. Natija ishonchliligi (0–100) quyidagilardan hisoblanadi:
     - samimiylik: har bir nosamimiy javob uchun −SINCERITY_PENALTY ball;
     - izchillik: "pairs" dagi har bir juft (bir xil xususiyatni qarama-qarshi tomondan o‘lchaydigan
       ikki savol) bo‘yicha ziddiyatli javob uchun −PAIR_PENALTY ball;
     - bir xil javob berish: asosiy savollarning ≥85 % yoki ≤15 % i «Qo‘shilaman» bo‘lsa, −ACQUIESCENCE_PENALTY;
     - juda tez topshirish: o‘rtacha 1 savolga 2 soniyadan kam vaqt — −FAST_PENALTY (1,5 soniyadan kam — ko‘proq).
   Daraja: 75–100 — Yuqori, 50–74 — O‘rtacha, 0–49 — Past.
6. Lavozimga moslik = shkala foizlarining lavozim uchun belgilangan og‘irliklar bo‘yicha o‘rtachasi.
7. Umumiy profil indeksi = asosiy shkalalar foizlarining o‘rtachasi.
8. HR tavsiyasi: ishonchlilik < 50 → "Ishonchsiz natija"; indeks ≥ 70, har bir shkala ≥ 50 va ishonchlilik ≥ 70 →
   "Tavsiya etiladi"; indeks ≥ 50 → "Suhbatda aniqlashtirish"; aks holda → "Qo‘shimcha baholash kerak".

Muhim: bu test klinik yoki psixologik tashxis emas. U HR suhbati uchun yo‘naltiruvchi ma’lumot beradi va
ishga qabul qilish to‘g‘risidagi yagona asos bo‘lmasligi kerak.
"""
from __future__ import annotations

AGREE, DISAGREE = 1, 0
OPTIONS = ["Qo‘shilmayman", "Qo‘shilaman"]

LEVEL_HIGH, LEVEL_MID, LEVEL_LOW = "Yuqori", "O‘rtacha", "Past"

SINCERITY_PENALTY = 8
PAIR_PENALTY = 8
ACQUIESCENCE_PENALTY = 15
FAST_PENALTY = 15
VERY_FAST_PENALTY = 25
FAST_SEC_PER_Q = 2.0
VERY_FAST_SEC_PER_Q = 1.5

# "Tavsiya etiladi" uchun kamida shuncha ishonchlilik kerak (aks holda — suhbatda aniqlashtirish)
RECOMMEND_MIN_RELIABILITY = 70

# HR tavsiyasi (natija "status" maydonida saqlanadi)
REC_RECOMMENDED = "Tavsiya etiladi"
REC_INTERVIEW = "Suhbatda aniqlashtirish"
REC_EXTRA = "Qo‘shimcha baholash kerak"
REC_UNRELIABLE = "Ishonchsiz natija"
RECOMMENDATIONS = (REC_RECOMMENDED, REC_INTERVIEW, REC_EXTRA, REC_UNRELIABLE)

DISCLAIMER = (
    "Bu test klinik yoki psixologik tashxis emas. Natija xodimning o‘zi haqidagi javoblariga asoslanadi va "
    "HR suhbati uchun yo‘naltiruvchi ma’lumot hisoblanadi. Ishga qabul qilish yoki lavozim bo‘yicha qaror faqat "
    "shu natija asosida qabul qilinmasligi kerak — suhbat, tavsiyanomalar va amaliy sinov bilan birga talqin qiling."
)

# ---------------------------------------------------------------------------
# Shkalalar bo‘yicha matnlar (shkala id lari landing_tests/sotuv.json dagi "scales" bilan bir xil).
# JSON ga yangi shkala qo‘shilsa va bu yerda matni bo‘lmasa — umumiy (generic) matn ishlatiladi.
# ---------------------------------------------------------------------------
SCALE_TEXTS: dict[str, dict] = {
    "masuliyat": {
        "strength": "Topshiriqlarni muddatida va oxirigacha bajarishga intiladi, o‘z xatolari uchun javobgarlikni zimmasiga oladi.",
        "mid": "Odatda vazifalarni bajaradi, ammo yuklama oshganda yoki nazorat bo‘lmaganda izchillik pasayishi mumkin.",
        "weakness": "Vazifalarni kechiktirish yoki oxiriga yetkazmaslik ehtimoli bor; aniq muddat va nazorat talab etilishi mumkin.",
        "questions_low": [
            "Oxirgi marta muddatni o‘tkazib yuborgan holatingizni aytib bering: sababi nima edi va qanday yo‘l tutdingiz?",
            "Ishda xatoga yo‘l qo‘ygan vaziyatingizni eslang: buni kimga, qachon va qanday aytdingiz?",
        ],
        "questions_high": [
            "Sizga ishonib topshirilgan eng mas’uliyatli vazifa qaysi edi va natijani qanday nazorat qildingiz?",
        ],
        "develop": "Kunlik vazifalar ro‘yxati va aniq muddatlar bilan ishlash; dastlabki oylarda haftalik nazorat uchrashuvi; tajribali murabbiy (mentor) biriktirish.",
    },
    "stress": {
        "strength": "Bosim, shoshilinch vazifalar va qo‘pol muomala sharoitida ham xotirjamlikni saqlab, ishni davom ettira oladi.",
        "mid": "Odatiy bosimni yengadi, lekin uzoq davom etadigan zo‘riqish yoki keskin tanqiddan keyin tiklanishga vaqt kerak bo‘lishi mumkin.",
        "weakness": "Kutilmagan muammo, tanqid yoki qo‘pol muomaladan keyin ish samaradorligi sezilarli pasayishi mumkin.",
        "questions_low": [
            "Ishda sizni eng ko‘p asabiylashtiradigan vaziyat qanday? Oxirgi marta shunday bo‘lganda nima qildingiz?",
            "Mijoz yoki rahbar sizga qo‘pol gapirgan holatni aytib bering: o‘sha kuni ishingiz qanday davom etdi?",
        ],
        "questions_high": [
            "Bir vaqtda bir nechta shoshilinch vazifa tushgan kuningizni aytib bering: ustuvorlikni qanday belgiladingiz?",
        ],
        "develop": "Ustuvorlikni belgilash (muhim/shoshilinch) usullarini o‘rgatish; qiyin mijozlar bilan ishlash bo‘yicha amaliy mashg‘ulot; yuklamani bosqichma-bosqich oshirish.",
    },
    "muloqot": {
        "strength": "Notanish odamlar bilan oson til topishadi, fikrini aniq va xotirjam bayon qila oladi.",
        "mid": "Tanish muhitda yaxshi muloqot qiladi, ammo notanish odamlar yoki ko‘pchilik oldida gapirishda ikkilanishi mumkin.",
        "weakness": "Notanish odamlar bilan suhbat, telefon orqali muloqot yoki ko‘pchilik oldida gapirish qiyinchilik tug‘dirishi mumkin.",
        "questions_low": [
            "Notanish mijozga birinchi bo‘lib qo‘ng‘iroq qilishingiz kerak bo‘lsa, suhbatni qanday boshlaysiz? Hozir namuna sifatida ko‘rsating.",
            "Jamoa yig‘ilishida rahbaringiz fikriga qo‘shilmagan holatingiz bo‘lganmi? Fikringizni qanday bildirdingiz?",
        ],
        "questions_high": [
            "Murakkab narsani boshqa odamga sodda qilib tushuntirgan holatingizni aytib bering.",
        ],
        "develop": "Telefon va yozishma bo‘yicha tayyor nutq namunalari (skriptlar); rolli o‘yinlar orqali mashq; tajribali hamkasbning suhbatlarini tinglab o‘rganish.",
    },
    "hamdardlik": {
        "strength": "Boshqalarning holatini tez sezadi, mijoz va hamkasblarni diqqat bilan tinglaydi, yordam berishga tayyor.",
        "mid": "Boshqalarning his-tuyg‘ulariga e’tibor beradi, lekin ish bosimi ostida bu e’tibor kamayishi mumkin.",
        "weakness": "Mijoz yoki hamkasbning his-tuyg‘ularini e’tiborsiz qoldirishi, muloqotda quruq va rasmiy bo‘lib qolishi mumkin.",
        "questions_low": [
            "Mijoz xafa bo‘lib shikoyat qilsa, birinchi gapingiz nima bo‘ladi?",
            "Hamkasbingiz qiynalayotganini sezgan holatingiz bo‘lganmi? Nima qildingiz?",
        ],
        "questions_high": [
            "Mijozning aytilmagan ehtiyojini sezib, unga yordam bergan holatingizni aytib bering.",
        ],
        "develop": "Faol tinglash va mijoz e’tirozlari bilan ishlash bo‘yicha trening; mijoz bilan suhbatlarni tahlil qilish; jamoaviy loyihalarga jalb qilish.",
    },
}

GENERIC_TEXTS = {
    "strength": "Bu yo‘nalishda yuqori natija ko‘rsatdi.",
    "mid": "Bu yo‘nalishda o‘rtacha natija ko‘rsatdi.",
    "weakness": "Bu yo‘nalish rivojlantirishni talab qiladi.",
    "questions_low": ["Bu yo‘nalish bo‘yicha o‘zingizdagi qiyinchiliklarni misol bilan aytib bering."],
    "questions_high": ["Bu yo‘nalishdagi eng yaxshi natijangizni misol bilan aytib bering."],
    "develop": "Bu yo‘nalish bo‘yicha murabbiy bilan individual rivojlanish rejasini tuzish.",
}


def level_of(percent: int) -> str:
    if percent >= 75:
        return LEVEL_HIGH
    if percent >= 50:
        return LEVEL_MID
    return LEVEL_LOW


def _texts(scale_id: str) -> dict:
    return SCALE_TEXTS.get(scale_id) or GENERIC_TEXTS


def item_point(key: str, answer: int) -> int:
    """Savol bali: direct — «Qo‘shilaman» = 1; reverse (teskari) — «Qo‘shilmayman» = 1."""
    agree = answer == AGREE
    return int(agree if key == "direct" else not agree)


# ---------------------------------------------------------------------------
# JSON tekshiruvi
# ---------------------------------------------------------------------------
def validate_config(data: dict) -> dict:
    """Savolnoma (format=profile) ni tekshiradi; xato bo‘lsa ValueError (o‘zbekcha sabab bilan)."""
    scales = data.get("scales") or []
    if not scales:
        raise ValueError("scales (shkalalar) ro‘yxati bo‘sh")
    scale_ids = [s.get("id") for s in scales]
    if len(set(scale_ids)) != len(scale_ids) or not all(isinstance(i, str) and i for i in scale_ids):
        raise ValueError("shkala id lari bo‘sh yoki takrorlangan")
    sincerity_id = (data.get("sincerity") or {}).get("id")
    if not sincerity_id or sincerity_id in scale_ids:
        raise ValueError("sincerity.id (samimiylik shkalasi) ko‘rsatilmagan yoki asosiy shkala bilan bir xil")

    data["options"] = list(data.get("options") or OPTIONS)
    if len(data["options"]) != 2:
        raise ValueError("options faqat 2 ta bo‘lishi kerak: «Qo‘shilmayman», «Qo‘shilaman»")
    stage = data.get("stageSize", 10)
    if not isinstance(stage, int) or stage < 1:
        raise ValueError("stageSize musbat butun son bo‘lishi kerak")

    questions = data.get("questions") or []
    if not questions:
        raise ValueError("savollar yo‘q")
    ids: set[int] = set()
    per_scale = {sid: 0 for sid in scale_ids + [sincerity_id]}
    for q in questions:
        qid = q.get("id")
        if not isinstance(qid, int) or qid in ids:
            raise ValueError(f"savol id noto‘g‘ri yoki takrorlangan ({qid})")
        ids.add(qid)
        if not isinstance(q.get("text"), str) or not q["text"].strip():
            raise ValueError(f"{qid}-savol matni bo‘sh")
        if q.get("scale") not in per_scale:
            raise ValueError(f"{qid}-savol shkalasi noma’lum: {q.get('scale')}")
        if q.get("key") not in ("direct", "reverse"):
            raise ValueError(f"{qid}-savol key 'direct' yoki 'reverse' bo‘lishi kerak")
        per_scale[q["scale"]] += 1
        q["options"] = data["options"]
    empty = [sid for sid, n in per_scale.items() if n == 0]
    if empty:
        raise ValueError(f"shkalada savol yo‘q: {', '.join(empty)}")

    by_id = {q["id"]: q for q in questions}
    for pair in data.get("pairs") or []:
        if not (isinstance(pair, list) and len(pair) == 2 and all(p in by_id for p in pair)):
            raise ValueError(f"pairs: juftlik noto‘g‘ri {pair}")
        a, b = by_id[pair[0]], by_id[pair[1]]
        if a["scale"] != b["scale"] or a["key"] == b["key"]:
            raise ValueError(f"pairs: {pair} — juftlik bir shkalada va qarama-qarshi kalitli (direct/reverse) bo‘lishi kerak")

    positions = data.get("positions") or []
    for p in positions:
        w = p.get("weights") or {}
        if not p.get("name") or not w:
            raise ValueError("positions: har bir lavozimda name va weights bo‘lishi kerak")
        unknown = set(w) - set(scale_ids)
        if unknown:
            raise ValueError(f"positions: {p['name']} — noma’lum shkala: {', '.join(unknown)}")
        if any(not isinstance(v, (int, float)) or v < 0 for v in w.values()) or sum(w.values()) <= 0:
            raise ValueError(f"positions: {p['name']} — og‘irliklar musbat son bo‘lishi kerak")
    return data


def stages(test: dict) -> list[dict]:
    """Savollarni bosqichlarga bo‘lish (tartib JSON dagi tartib bilan bir xil)."""
    size = test.get("stageSize", 10)
    ids = [q["id"] for q in test["questions"]]
    return [{"no": i // size + 1, "questionIds": ids[i:i + size]} for i in range(0, len(ids), size)]


# ---------------------------------------------------------------------------
# Hisoblash
# ---------------------------------------------------------------------------
def _pct(points: int, n: int) -> int:
    return round(points / n * 100) if n else 0


def _thinking_style(s: dict[str, int]) -> dict:
    structure = s.get("masuliyat", 50)
    people = round((s.get("muloqot", 50) + s.get("hamdardlik", 50)) / 2)
    if structure >= 60 and people >= 60:
        return {
            "title": "Tizimli va odamlarga yo‘naltirilgan",
            "text": "Ishni reja va qoidaga tayanib bajaradi, shu bilan birga odamlar bilan munosabatga e’tibor beradi. "
                    "Mijoz bilan ishlash va aniq jarayonlar uyg‘unlashgan vazifalarda samarali.",
        }
    if structure >= 60:
        return {
            "title": "Tizimli-amaliy",
            "text": "Aniq vazifa, tartib va natijaga tayanib fikrlaydi. Jarayon, hujjat va nazorat bilan bog‘liq ishlarda kuchli; "
                    "odamlar bilan ko‘p muloqot talab qiladigan vazifalarda qo‘llab-quvvatlash kerak bo‘lishi mumkin.",
        }
    if people >= 60:
        return {
            "title": "Kommunikativ-intuitiv",
            "text": "Qarorlarni ko‘proq odamlar bilan muloqot va vaziyatni his qilish orqali qabul qiladi. "
                    "Mijoz bilan jonli ishlashda kuchli; tartib, muddat va hisobotlarda tashqi nazorat foydali.",
        }
    return {
        "title": "Mustaqil-vaziyatga qarab",
        "text": "Aniq tizim yoki muloqotga kuchli tayanmaydi, vaziyatga qarab harakat qiladi. "
                "Dastlabki davrda aniq ko‘rsatmalar, namunalar va yaqin murabbiylik bilan tezroq moslashadi.",
    }


def _hard_situation(s: dict[str, int]) -> dict:
    stress = s.get("stress", 50)
    social = round((s.get("muloqot", 50) + s.get("hamdardlik", 50)) / 2)
    if stress >= 60 and social >= 60:
        return {
            "title": "Faol hal qiluvchi",
            "text": "Qiyin vaziyatda xotirjamlikni saqlab, muammoni odamlar bilan gaplashib hal qilishga intiladi. "
                    "Norozi mijoz yoki shoshilinch holatda tashabbusni o‘z qo‘liga olishi mumkin.",
        }
    if stress >= 60:
        return {
            "title": "Mustaqil, o‘zini tutib turuvchi",
            "text": "Bosim ostida o‘zini yo‘qotmaydi, lekin muammoni ko‘proq yolg‘iz hal qilishga urinadi va yordam so‘rashni kechiktirishi mumkin.",
        }
    if social >= 60:
        return {
            "title": "Qo‘llab-quvvatlash izlovchi",
            "text": "Qiyin vaziyatni hissiy qabul qiladi, ammo hamkasblar yoki rahbardan maslahat so‘rab chiqish yo‘lini topadi. "
                    "Jamoaviy qo‘llab-quvvatlash bo‘lsa, tez tiklanadi.",
        }
    return {
        "title": "Vaziyatdan chetlanishga moyil",
        "text": "Kutilmagan muammo yoki ziddiyatda ishni kechiktirish, javobni ortga surish yoki vaziyatdan chetlanish ehtimoli bor. "
                "Aniq harakat algoritmi (kimga murojaat qilish, nima deyish) berilsa, xatti-harakati barqarorlashadi.",
    }


def grade(test: dict, answers: dict[int, int], duration_sec: int | None = None) -> dict:
    """
    Javoblardan to‘liq HR hisobotini hisoblaydi. answers: {savol_id: 0|1} (validate_answers dan o‘tgan).
    Qaytaradi: natija yozuviga qo‘shiladigan maydonlar (status, percent, scores, reliability, report, reportText, items).
    """
    scales = test["scales"]
    scale_ids = [s["id"] for s in scales]
    titles = {s["id"]: s["title"] for s in scales}
    sincerity = test["sincerity"]
    sid = sincerity["id"]

    items, points, counts = [], {k: 0 for k in scale_ids + [sid]}, {k: 0 for k in scale_ids + [sid]}
    core_agree = core_total = 0
    for q in test["questions"]:
        a = answers[q["id"]]
        pt = item_point(q["key"], a)
        points[q["scale"]] += pt
        counts[q["scale"]] += 1
        if q["scale"] != sid:
            core_total += 1
            core_agree += a == AGREE
        items.append({
            "id": q["id"], "text": q["text"], "options": q["options"], "scale": q["scale"],
            "scaleTitle": titles.get(q["scale"], sincerity.get("title", "Samimiylik")),
            "key": q["key"], "answer": a, "point": pt,
            "sincerity": q["scale"] == sid,
        })

    scores = {k: _pct(points[k], counts[k]) for k in scale_ids}
    scale_rows = [
        {"id": k, "title": titles[k], "short": next((s.get("short") for s in scales if s["id"] == k), "") or titles[k],
         "description": next((s.get("description", "") for s in scales if s["id"] == k), ""),
         "percent": scores[k], "points": points[k], "max": counts[k], "level": level_of(scores[k])}
        for k in scale_ids
    ]
    index = round(sum(scores.values()) / len(scores)) if scores else 0

    # ---------- Ishonchlilik ----------
    sincere_points, sincere_max = points[sid], counts[sid]
    sincerity_pct = _pct(sincere_points, sincere_max)
    desirable = sincere_max - sincere_points
    by_id = {i["id"]: i for i in items}
    inconsistent = []
    for a_id, b_id in test.get("pairs") or []:
        a, b = by_id[a_id], by_id[b_id]
        if a["point"] != b["point"]:
            inconsistent.append({"ids": [a_id, b_id], "scale": a["scale"], "scaleTitle": a["scaleTitle"],
                                 "texts": [a["text"], b["text"]],
                                 "answers": [a["options"][a["answer"]], b["options"][b["answer"]]]})
    pairs_total = len(test.get("pairs") or [])
    agree_ratio = core_agree / core_total if core_total else 0.5
    one_sided = agree_ratio >= 0.85 or agree_ratio <= 0.15

    penalties, notes = [], []
    if desirable:
        penalties.append(desirable * SINCERITY_PENALTY)
        if sincerity_pct < 50:
            notes.append(f"Samimiylik past ({sincerity_pct}%): {desirable} ta savolda o‘zini ideal ko‘rsatishga intilgan. "
                         "Ko‘rsatkichlar haqiqiydan yuqori chiqqan bo‘lishi mumkin.")
        elif sincerity_pct < 75:
            notes.append(f"Samimiylik o‘rtacha ({sincerity_pct}%): ba’zi javoblarda o‘zini yaxshiroq ko‘rsatishga intilish bor.")
    if inconsistent:
        penalties.append(len(inconsistent) * PAIR_PENALTY)
        notes.append(f"Javoblarda {len(inconsistent)} ta ziddiyat bor (o‘xshash mazmundagi savollarga qarama-qarshi javob).")
    if one_sided:
        penalties.append(ACQUIESCENCE_PENALTY)
        word = "«Qo‘shilaman»" if agree_ratio >= 0.85 else "«Qo‘shilmayman»"
        notes.append(f"Asosiy savollarning {round(agree_ratio * 100)}% iga {word} deb javob berilgan — savollarni o‘qimasdan "
                     "bir xil javob belgilash ehtimoli bor.")
    sec_per_q = (duration_sec / len(items)) if duration_sec and items else None
    if sec_per_q is not None and sec_per_q < VERY_FAST_SEC_PER_Q:
        penalties.append(VERY_FAST_PENALTY)
        notes.append(f"Test juda tez topshirilgan ({duration_sec} soniya, har savolga ~{sec_per_q:.1f} s).")
    elif sec_per_q is not None and sec_per_q < FAST_SEC_PER_Q:
        penalties.append(FAST_PENALTY)
        notes.append(f"Test tez topshirilgan ({duration_sec} soniya, har savolga ~{sec_per_q:.1f} s).")
    reliability_pct = max(0, min(100, 100 - sum(penalties)))
    if not notes:
        notes.append("Javoblar izchil va samimiy — natijaga ishonsa bo‘ladi.")
    reliability = {
        "percent": reliability_pct, "level": level_of(reliability_pct),
        "sincerity": sincerity_pct, "sincerityLevel": level_of(sincerity_pct),
        "desirableAnswers": desirable, "sincerityMax": sincere_max,
        "inconsistentPairs": len(inconsistent), "pairsTotal": pairs_total, "inconsistencies": inconsistent,
        "agreeRatio": round(agree_ratio * 100), "oneSided": one_sided,
        "secondsPerQuestion": round(sec_per_q, 1) if sec_per_q is not None else None,
        "notes": notes,
    }

    # ---------- Lavozimlar ----------
    positions = []
    for p in test.get("positions") or []:
        w = p["weights"]
        total_w = sum(w.values())
        match = round(sum(scores[k] * v for k, v in w.items()) / total_w)
        key_scales = sorted(w, key=lambda k: -w[k])[:2]
        positions.append({"name": p["name"], "percent": match, "level": level_of(match),
                          "keyScales": [titles[k] for k in key_scales], "description": p.get("description", "")})
    positions.sort(key=lambda p: (-p["percent"], p["name"]))

    # ---------- Kuchli / zaif tomonlar ----------
    ordered = sorted(scale_rows, key=lambda r: (-r["percent"], r["title"]))
    strengths = [{"scale": r["title"], "percent": r["percent"], "text": _texts(r["id"])["strength"]}
                 for r in ordered if r["level"] == LEVEL_HIGH]
    weaknesses = [{"scale": r["title"], "percent": r["percent"],
                   "text": _texts(r["id"])["weakness" if r["level"] == LEVEL_LOW else "mid"]}
                  for r in reversed(ordered) if r["level"] != LEVEL_HIGH]
    if not strengths and ordered:  # hech bir shkala yuqori bo‘lmasa — eng yaxshisi nisbiy kuchli tomon
        top = ordered[0]
        strengths.append({"scale": top["title"], "percent": top["percent"],
                          "text": f"Boshqa yo‘nalishlarga nisbatan eng yaxshi natija. {_texts(top['id'])['mid']}"})

    # ---------- Suhbat savollari ----------
    interview = []
    for r in sorted(scale_rows, key=lambda r: r["percent"]):
        t = _texts(r["id"])
        if r["level"] == LEVEL_LOW:
            interview += [{"scale": r["title"], "reason": f"{r['title']} past ({r['percent']}%)", "question": q} for q in t["questions_low"][:2]]
        elif r["level"] == LEVEL_MID:
            interview += [{"scale": r["title"], "reason": f"{r['title']} o‘rtacha ({r['percent']}%)", "question": t["questions_low"][0]}]
        else:
            interview += [{"scale": r["title"], "reason": f"{r['title']} yuqori ({r['percent']}%) — misol bilan tasdiqlang",
                           "question": t["questions_high"][0]}]
    for inc in inconsistent[:2]:
        interview.append({
            "scale": inc["scaleTitle"], "reason": "Javoblardagi ziddiyat",
            "question": f"Siz «{inc['texts'][0]}» fikriga «{inc['answers'][0]}», «{inc['texts'][1]}» fikriga esa "
                        f"«{inc['answers'][1]}» deb javob bergansiz. Buni hayotiy misol bilan tushuntirib bering.",
        })
    if sincerity_pct < 75:
        interview.append({
            "scale": sincerity.get("title", "Samimiylik"), "reason": f"Samimiylik {sincerity_pct}%",
            "question": "Ishdagi kamchiliklaringizdan birini va uni qanday tuzatayotganingizni aytib bering.",
        })

    thinking = _thinking_style(scores)
    hard = _hard_situation(scores)
    development = [{"scale": r["title"], "text": _texts(r["id"])["develop"]}
                   for r in sorted(scale_rows, key=lambda r: r["percent"]) if r["level"] != LEVEL_HIGH]
    if not development:
        development.append({"scale": "Umumiy", "text": "Barcha asosiy ko‘rsatkichlar yuqori. Murabbiylik, yangi xodimlarni o‘rgatish "
                                                      "yoki mas’uliyatli loyihalarga jalb qilish orqali salohiyatini rivojlantirish tavsiya etiladi."})

    # ---------- Tavsiya ----------
    min_score = min(scores.values()) if scores else 0
    if reliability_pct < 50:
        recommendation = REC_UNRELIABLE
    elif index >= 70 and min_score >= 50 and reliability_pct >= RECOMMEND_MIN_RELIABILITY:
        recommendation = REC_RECOMMENDED
    elif index >= 50:
        recommendation = REC_INTERVIEW
    else:
        recommendation = REC_EXTRA

    best, worst = (ordered[0], ordered[-1]) if ordered else (None, None)
    summary_parts = [f"Umumiy profil indeksi — {index}% ({level_of(index).lower()})."]
    if best and worst:
        if best["percent"] == worst["percent"]:
            summary_parts.append(f"Barcha asosiy yo‘nalishlar bir xil darajada — {best['percent']}%.")
        elif worst["level"] == LEVEL_HIGH:
            summary_parts.append(f"Eng kuchli yo‘nalish — {best['title'].lower()} ({best['percent']}%); "
                                 f"barcha asosiy ko‘rsatkichlar yuqori (eng pasti — {worst['title'].lower()}, {worst['percent']}%).")
        else:
            summary_parts.append(f"Eng kuchli yo‘nalish — {best['title'].lower()} ({best['percent']}%), "
                                 f"eng ko‘p e’tibor talab qiladigan yo‘nalish — {worst['title'].lower()} ({worst['percent']}%).")
    if positions:
        top3 = ", ".join(f"{p['name']} ({p['percent']}%)" for p in positions[:3])
        summary_parts.append(f"Eng mos lavozimlar: {top3}.")
    summary_parts.append(f"Natija ishonchliligi — {reliability_pct}% ({reliability['level'].lower()}).")
    rec_text = {
        REC_RECOMMENDED: "Profil talab qilinadigan sifatlarga mos keladi — suhbatda kuchli tomonlarni misollar bilan tasdiqlash tavsiya etiladi.",
        REC_INTERVIEW: "Profil qisman mos — past va o‘rtacha ko‘rsatkichlarni suhbatda quyidagi savollar orqali aniqlashtiring.",
        REC_EXTRA: "Bir nechta asosiy ko‘rsatkich past — qaror qabul qilishdan oldin qo‘shimcha suhbat va amaliy sinov o‘tkazing.",
        REC_UNRELIABLE: "Javoblar ishonchliligi past — natijani asos qilib olmang; testni nazorat ostida qayta topshirish yoki suhbat orqali baholash tavsiya etiladi.",
    }[recommendation]
    summary_parts.append(rec_text)

    report = {
        "version": 1,
        "summary": " ".join(summary_parts),
        "recommendation": recommendation,
        "index": index, "indexLevel": level_of(index),
        "scales": scale_rows,
        "reliability": reliability,
        "positions": positions,
        "interviewQuestions": interview[:10],
        "strengths": strengths,
        "weaknesses": weaknesses,
        "thinkingStyle": thinking,
        "hardSituations": hard,
        "development": development,
        "disclaimer": DISCLAIMER,
    }
    core_points = sum(points[k] for k in scale_ids)
    core_max = sum(counts[k] for k in scale_ids)
    return {
        "format": "profile",
        "items": items,
        "total": len(items),
        "correct": None, "wrong": None,  # bilim testidagi "to‘g‘ri/xato" bu testda yo‘q
        "points": core_points, "maxPoints": core_max,
        "percent": index,
        "passPercent": None,
        "status": recommendation,
        "passed": recommendation == REC_RECOMMENDED,
        "scores": scores,
        "reliability": reliability_pct,
        "bestPosition": positions[0] if positions else None,
        "report": report,
    }


# ---------------------------------------------------------------------------
# Nusxalash uchun to‘liq matnli hisobot
# ---------------------------------------------------------------------------
def report_text(result: dict) -> str:
    r = result.get("report") or {}
    rel = r.get("reliability") or {}
    lines: list[str] = []
    add = lines.append
    title = result.get("testTitle") or "Yangi xodimlar uchun shaxsiy-kasbiy test"
    add(f"HR HISOBOTI — {title}")
    add("=" * 60)
    add(f"Xodim: {result.get('fullName') or '—'}")
    if result.get("age") is not None:
        add(f"Yosh: {result.get('age')}" + (f" (tug‘ilgan sana: {result.get('birthDate')})" if result.get("birthDate") else ""))
    if result.get("position"):
        add(f"Tanlangan lavozim: {result['position']}")
    if result.get("phone"):
        add(f"Telefon: {result['phone']}")
    sub = str(result.get("submittedAt") or "")
    if sub:
        add(f"Topshirilgan: {sub[8:10]}.{sub[5:7]}.{sub[:4]} {sub[11:16]}")
    if result.get("durationSec") is not None:
        s = int(result["durationSec"])
        add(f"Sarflangan vaqt: {s // 60} daq {s % 60} son")
    add("")
    add("1. HR XULOSASI")
    add(r.get("summary", ""))
    add(f"Tavsiya: {r.get('recommendation', '')}")
    add(f"Natija ishonchliligi: {rel.get('percent', '—')}% ({rel.get('level', '')})")
    add(f"Samimiylik: {rel.get('sincerity', '—')}% · ziddiyatli juftliklar: {rel.get('inconsistentPairs', 0)}/{rel.get('pairsTotal', 0)}"
        f" · «Qo‘shilaman» ulushi: {rel.get('agreeRatio', '—')}%")
    for n in rel.get("notes") or []:
        add(f"  - {n}")
    add("")
    add("2. ASOSIY KO‘RSATKICHLAR")
    for s in r.get("scales") or []:
        add(f"  - {s['title']}: {s['percent']}% ({s['level']}) — {s['points']}/{s['max']} ball")
    add(f"  Umumiy profil indeksi: {r.get('index', '—')}%")
    add("")
    add("3. ENG MOS LAVOZIMLAR")
    for i, p in enumerate(r.get("positions") or [], 1):
        add(f"  {i}. {p['name']} — {p['percent']}% (asosiy talablar: {', '.join(p.get('keyScales') or [])})")
    add("")
    add("4. SUHBATDA SO‘RALADIGAN SAVOLLAR")
    for i, q in enumerate(r.get("interviewQuestions") or [], 1):
        add(f"  {i}. {q['question']}  [{q['reason']}]")
    add("")
    add("5. KUCHLI TOMONLAR")
    for s in r.get("strengths") or []:
        add(f"  + {s['scale']} ({s['percent']}%): {s['text']}")
    add("")
    add("6. ZAIF TOMONLAR / E’TIBOR TALAB QILADI")
    for s in r.get("weaknesses") or []:
        add(f"  - {s['scale']} ({s['percent']}%): {s['text']}")
    if not r.get("weaknesses"):
        add("  Sezilarli zaif tomon aniqlanmadi.")
    add("")
    ts, hs = r.get("thinkingStyle") or {}, r.get("hardSituations") or {}
    add(f"7. FIKRLASH USLUBI: {ts.get('title', '')}")
    add(f"  {ts.get('text', '')}")
    add("")
    add(f"8. QIYIN VAZIYATDAGI XULQ: {hs.get('title', '')}")
    add(f"  {hs.get('text', '')}")
    add("")
    add("9. RIVOJLANISH TAVSIYALARI")
    for d in r.get("development") or []:
        add(f"  - {d['scale']}: {d['text']}")
    add("")
    add("Eslatma: " + r.get("disclaimer", DISCLAIMER))
    return "\n".join(lines)
