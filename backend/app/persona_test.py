"""
«Ishdagi shaxsiyat 360» — yangi kelgan xodimlar / nomzodlar uchun 40 savolli test (landing, /test/sotuv).
Savollar, xususiyatlar, yo‘nalishlar, matnlar va lavozimlar: app/landing_tests/sotuv.json ("format": "persona").

Hisoblash (hammasi haqiqiy javoblardan, tasodifiy son yo‘q):
1. Javob: 0 = «Qo‘shilmayman», 1 = «Qo‘shilaman».
2. 39 ta savol 13 ta xususiyatga bo‘lingan (har birida 3 tadan), 1 ta savol — diqqat tekshiruvi.
   key = "direct"  → «Qo‘shilaman» = 1 ball;  key = "reverse" (teskari savol) → «Qo‘shilmayman» = 1 ball.
   Xususiyat foizi = ball / savollar soni × 100 (3 ta savolda: 0, 33, 67, 100).
3. Xususiyatlar ikki guruhda:
   - "positive" — yuqori samaradorlik xususiyatlari (yuqori bo‘lgani yaxshi);
   - "negative" — to‘sqinlik qiluvchi xususiyatlar (past bo‘lgani yaxshi).
   Guruh foizi = guruhdagi xususiyatlar foizlarining o‘rtachasi.
4. Yo‘nalish (4 ta) foizi = undagi xususiyatlar foizlarining o‘rtachasi. "goodHigh": false — past bo‘lgani yaxshi.
5. Lavozimga moslik = Σ og‘irlik × ball / Σ og‘irlik; "negative" xususiyat uchun ball = 100 − foiz.
6. Javoblar ishonchliligi (daraja: yuqori / o‘rtacha / past):
   - diqqat tekshiruvi savoliga noto‘g‘ri javob → past;
   - asosiy savollarning ≥ 90 % iga bir xil javob → past;
   - juda tez topshirish (< 1,5 s/savol → past, < 2,5 s/savol → o‘rtacha);
   - qarama-qarshi ma’noli juft savollardagi ziddiyat (5 juftlikdan: hammasi → past, ≥ 3 → o‘rtacha);
   - barcha yaxshi xususiyatlar 100 % va barcha to‘sqinlik qiluvchilar 0 % → o‘rtacha (o‘zini ideal ko‘rsatish ehtimoli).
7. Profil, HR xulosasi, kuchli/zaif tomonlar, xulq-atvor naqshlari, suhbat savollari va rivojlanish tavsiyalari
   shu foizlardan qoidalar bo‘yicha tuziladi (quyida).

Bu test klinik yoki psixologik tashxis emas — HR suhbati uchun yo‘naltiruvchi ma’lumot.
"""
from __future__ import annotations

AGREE, DISAGREE = 1, 0
OPTIONS = ["Qo‘shilmayman", "Qo‘shilaman"]
FORMAT = "persona"

REL_HIGH, REL_MID, REL_LOW = "yuqori", "o‘rtacha", "past"
_REL_ORDER = {REL_HIGH: 0, REL_MID: 1, REL_LOW: 2}

# HR xulosasi (natija "status" maydonida saqlanadi)
DEC_HIRE = "Ishga olish tavsiya etiladi"
DEC_INTERVIEW = "Suhbatdan keyin qaror qiling"
DEC_CAUTION = "Ehtiyotkorlik bilan"
DEC_UNRELIABLE = "Natija ishonchsiz"
DECISIONS = (DEC_HIRE, DEC_INTERVIEW, DEC_CAUTION, DEC_UNRELIABLE)

LIKELY = 67  # 3 savoldan kamida 2 tasi — xususiyat "yaqqol" hisoblanadi
WEAK = 33

DISCLAIMER = (
    "Bu test klinik yoki psixologik tashxis emas. Natija xodimning o‘zi haqidagi javoblariga asoslanadi va "
    "HR suhbati uchun yo‘naltiruvchi ma’lumot hisoblanadi. Qaror faqat shu natija asosida qabul qilinmasin."
)


def item_point(key: str, answer: int) -> int:
    agree = answer == AGREE
    return int(agree if key == "direct" else not agree)


def _pct(points: int, n: int) -> int:
    return round(points / n * 100) if n else 0


def _avg(values) -> int:
    values = list(values)
    return round(sum(values) / len(values)) if values else 0


# ---------------------------------------------------------------------------
# JSON tekshiruvi
# ---------------------------------------------------------------------------
def validate_config(data: dict) -> dict:
    traits = data.get("traits") or []
    if not traits:
        raise ValueError("traits (xususiyatlar) ro‘yxati bo‘sh")
    ids = [t.get("id") for t in traits]
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        raise ValueError("xususiyat id lari bo‘sh yoki takrorlangan")
    for t in traits:
        if t.get("group") not in ("positive", "negative"):
            raise ValueError(f"{t['id']}: group 'positive' yoki 'negative' bo‘lishi kerak")
        if not t.get("title"):
            raise ValueError(f"{t['id']}: title yo‘q")

    data["options"] = list(data.get("options") or OPTIONS)
    if len(data["options"]) != 2:
        raise ValueError("options faqat 2 ta bo‘lishi kerak: «Qo‘shilmayman», «Qo‘shilaman»")
    stage = data.get("stageSize", 10)
    if not isinstance(stage, int) or stage < 1:
        raise ValueError("stageSize musbat butun son bo‘lishi kerak")

    questions = data.get("questions") or []
    if not questions:
        raise ValueError("savollar yo‘q")
    seen: set[int] = set()
    per_trait = {i: 0 for i in ids}
    for q in questions:
        qid = q.get("id")
        if not isinstance(qid, int) or qid in seen:
            raise ValueError(f"savol id noto‘g‘ri yoki takrorlangan ({qid})")
        seen.add(qid)
        if not isinstance(q.get("text"), str) or not q["text"].strip():
            raise ValueError(f"{qid}-savol matni bo‘sh")
        if q.get("attention"):
            if q.get("expected") not in (0, 1):
                raise ValueError(f"{qid}-savol (diqqat tekshiruvi): expected 0 yoki 1 bo‘lishi kerak")
        else:
            if q.get("trait") not in per_trait:
                raise ValueError(f"{qid}-savol xususiyati noma’lum: {q.get('trait')}")
            if q.get("key") not in ("direct", "reverse"):
                raise ValueError(f"{qid}-savol key 'direct' yoki 'reverse' bo‘lishi kerak")
            per_trait[q["trait"]] += 1
        q["options"] = data["options"]
    empty = [i for i, n in per_trait.items() if n == 0]
    if empty:
        raise ValueError(f"xususiyatda savol yo‘q: {', '.join(empty)}")

    for d in data.get("directions") or []:
        unknown = set(d.get("traits") or []) - set(ids)
        if not d.get("id") or not d.get("traits") or unknown:
            raise ValueError(f"directions: {d.get('id')} — xususiyatlar noto‘g‘ri {sorted(unknown)}")

    by_id = {q["id"]: q for q in questions}
    for pair in data.get("pairs") or []:
        if not (isinstance(pair, list) and len(pair) == 2 and all(p in by_id and not by_id[p].get("attention") for p in pair)):
            raise ValueError(f"pairs: juftlik noto‘g‘ri {pair}")
        a, b = by_id[pair[0]], by_id[pair[1]]
        if a["trait"] != b["trait"] or a["key"] == b["key"]:
            raise ValueError(f"pairs: {pair} — bir xususiyatda va qarama-qarshi kalitli bo‘lishi kerak")

    for r in data.get("roles") or []:
        w = r.get("weights") or {}
        if not r.get("name") or not w or set(w) - set(ids):
            raise ValueError(f"roles: {r.get('name')} — name va to‘g‘ri weights kerak")
        if any(not isinstance(v, (int, float)) or v < 0 for v in w.values()) or sum(w.values()) <= 0:
            raise ValueError(f"roles: {r['name']} — og‘irliklar musbat son bo‘lishi kerak")
    return data


def stages(test: dict) -> list[dict]:
    size = test.get("stageSize", 10)
    qids = [q["id"] for q in test["questions"]]
    return [{"no": i // size + 1, "questionIds": qids[i:i + size]} for i in range(0, len(qids), size)]


# ---------------------------------------------------------------------------
# Xulq-atvor naqshlari: (sarlavha, matn, shart). Shart — xususiyat foizlari (s) bo‘yicha.
# ---------------------------------------------------------------------------
def _hi(s, k):
    return s.get(k, 0) >= LIKELY


def _lo(s, k):
    return s.get(k, 100) <= WEAK


PATTERNS = [
    ("Iliq, lekin qizishganda qattiq",
     "Odamlar bilan tez kirishadi va samimiy ko‘rinadi, lekin keskin bahsda tez qizishib, ovozini ko‘tarishi mumkin.",
     lambda s: _hi(s, "ijtimoiylik") and _hi(s, "xusumat")),
    ("Ergashuvchan va ikkilanuvchi",
     "Kelishmovchilikdan qochadi, qarorni boshqalarga qoldiradi. Sodiq va kamtar, lekin mustaqillik yetishmaydi.",
     lambda s: _hi(s, "qaramlik") and _hi(s, "tasdiqlash")),
    ("Raqobat jamoaga to‘siq bo‘lishi mumkin",
     "G‘olib bo‘lish istagi qattiqqo‘llik yoki nazorat bilan birga kelganda hamkasblar bilan munosabat buziladi.",
     lambda s: _hi(s, "raqobat") and (_hi(s, "qattiqqollik") or _hi(s, "nazorat"))),
    ("Sog‘lom raqobatchi",
     "Yutishni xohlaydi, lekin boshqalarga ham yordam beradi. «Talabchan, lekin samimiy» formulasi.",
     lambda s: _hi(s, "raqobat") and _hi(s, "yordam")),
    ("G‘oyasi ko‘p, lekin o‘zinikiga yopishadi",
     "Yangi g‘oyalar topadi, ammo boshqalarning g‘oyalarini qabul qilishga qiynaladi.",
     lambda s: _hi(s, "innovatsiya") and _hi(s, "qattiqqollik")),
    ("Jamoaning tayanchi",
     "Muloqotchan, yordamsevar va tanqidga ochiq. Jamoada iliq muhit yaratadi.",
     lambda s: _hi(s, "ijtimoiylik") and _hi(s, "yordam") and _hi(s, "feedback")),
    ("Mustaqil va tashabbuskor",
     "Qarorni o‘zi qabul qiladi va katta maqsad sari intiladi. Ko‘rsatmani kutib o‘tirmaydi.",
     lambda s: _lo(s, "qaramlik") and _hi(s, "yutuq")),
    ("Bosim ostida barqaror ijrochi",
     "Ish ko‘payganda ham xotirjam qoladi va ishini oxiriga yetkazadi.",
     lambda s: _lo(s, "ruhiy_bosim") and _hi(s, "masuliyat")),
    ("Hammasini o‘zi qilishni xohlaydi",
     "Ishni boshqaga topshirishga qiynaladi, har bir qadamni tekshiradi. Ko‘p ish o‘zida to‘planib qolishi mumkin.",
     lambda s: _hi(s, "nazorat") and _hi(s, "masuliyat")),
    ("Bosim ostida tez charchaydi",
     "Ish ko‘payganda xavotir kuchayadi va boshqalarning fikriga ko‘proq bog‘lanib qoladi.",
     lambda s: _hi(s, "ruhiy_bosim") and _hi(s, "tasdiqlash")),
    ("Tanqidni qabul qilishga qiynaladi",
     "Fikr-mulohazaga yopiq va o‘z fikrida qattiq turadi — o‘rganish sekinlashishi mumkin.",
     lambda s: _lo(s, "feedback") and _hi(s, "qattiqqollik")),
]


# ---------------------------------------------------------------------------
# Hisoblash
# ---------------------------------------------------------------------------
def grade(test: dict, answers: dict[int, int], duration_sec: int | None = None, full_name: str = "") -> dict:
    traits = test["traits"]
    t_by_id = {t["id"]: t for t in traits}
    points = {t["id"]: 0 for t in traits}
    counts = {t["id"]: 0 for t in traits}
    items, attention = [], []
    agree = total_core = 0
    for q in test["questions"]:
        a = answers[q["id"]]
        if q.get("attention"):
            ok = a == q["expected"]
            attention.append({"id": q["id"], "text": q["text"], "answer": a, "expected": q["expected"], "ok": ok})
            items.append({"id": q["id"], "text": q["text"], "options": q["options"], "answer": a,
                          "attention": True, "ok": ok, "traitTitle": "Diqqat tekshiruvi"})
            continue
        pt = item_point(q["key"], a)
        points[q["trait"]] += pt
        counts[q["trait"]] += 1
        total_core += 1
        agree += a == AGREE
        items.append({"id": q["id"], "text": q["text"], "options": q["options"], "answer": a, "trait": q["trait"],
                      "traitTitle": t_by_id[q["trait"]]["title"], "key": q["key"], "point": pt,
                      "group": t_by_id[q["trait"]]["group"]})

    scores = {k: _pct(points[k], counts[k]) for k in points}
    trait_rows = [{"id": t["id"], "title": t["title"], "group": t["group"], "direction": t.get("direction"),
                   "percent": scores[t["id"]], "points": points[t["id"]], "max": counts[t["id"]],
                   "description": t.get("description", "")} for t in traits]
    positive = _avg(scores[t["id"]] for t in traits if t["group"] == "positive")
    negative = _avg(scores[t["id"]] for t in traits if t["group"] == "negative")

    directions = [{"id": d["id"], "title": d["title"], "description": d.get("description", ""),
                   "color": d.get("color", ""), "goodHigh": d.get("goodHigh", True),
                   "traits": d["traits"], "percent": _avg(scores[k] for k in d["traits"])}
                  for d in test.get("directions") or []]

    # ---------- Ishonchlilik ----------
    issues = []  # (daraja, matn)
    for att in attention:
        if not att["ok"]:
            issues.append((REL_LOW, "Diqqat tekshiruvi savoliga noto‘g‘ri javob berilgan: savollar o‘qilmasdan belgilangan bo‘lishi mumkin."))
    ratio = agree / total_core if total_core else 0.5
    if ratio >= 0.9 or ratio <= 0.1:
        word = "«Qo‘shilaman»" if ratio >= 0.9 else "«Qo‘shilmayman»"
        issues.append((REL_LOW, f"Savollarning {round(ratio * 100)}% iga {word} deb javob berilgan — bir xil javob belgilangan."))
    sec = (duration_sec / len(items)) if duration_sec and items else None
    if sec is not None and sec < 1.5:
        issues.append((REL_LOW, f"Test juda tez topshirilgan ({duration_sec} soniya) — savollar o‘qilmagan bo‘lishi mumkin."))
    elif sec is not None and sec < 2.5:
        issues.append((REL_MID, f"Test tez topshirilgan ({duration_sec} soniya)."))
    by_id = {i["id"]: i for i in items}
    contradictions = [p for p in test.get("pairs") or [] if by_id[p[0]]["point"] != by_id[p[1]]["point"]]
    n_pairs = len(test.get("pairs") or [])
    if n_pairs and len(contradictions) == n_pairs:
        issues.append((REL_LOW, f"Barcha qarama-qarshi juft savollarga zid javob berilgan ({len(contradictions)} ta)."))
    elif len(contradictions) >= 3:
        issues.append((REL_MID, f"Bir-biriga zid javoblar bor ({len(contradictions)} ta juftlik)."))
    if positive == 100 and negative == 0:
        issues.append((REL_MID, "Barcha javoblar «ideal» — o‘zini yaxshi ko‘rsatishga intilish ehtimoli bor."))
    level = max((lvl for lvl, _ in issues), key=_REL_ORDER.get, default=REL_HIGH)
    rel_text = {
        REL_HIGH: "Javoblar izchil — natijaga ishonsa bo‘ladi.",
        REL_MID: "Natijani suhbatda savollar orqali tekshirib ko‘ring.",
        REL_LOW: "Natija ishonchsiz bo‘lishi mumkin. Testni suhbat paytida, xotirjam muhitda qayta topshirtiring.",
    }[level]
    reliability = {"level": level, "text": rel_text, "issues": [t for _, t in issues],
                   "attentionOk": all(a["ok"] for a in attention), "contradictions": len(contradictions),
                   "pairsTotal": len(test.get("pairs") or []), "agreeRatio": round(ratio * 100),
                   "secondsPerQuestion": round(sec, 1) if sec is not None else None}

    # ---------- Profil ----------
    if negative >= 60:
        profile = ("E'tibor talab qiladigan profil",
                   "To‘sqinlik qiluvchi xususiyatlar yuqori. Ular kuchli tomonlarni xiralashtirib qo‘yishi mumkin.", "attention")
    elif positive >= 70 and negative < 45:
        profile = ("Kuchli profil", "Yuqori samaradorlik xususiyatlari ustun, to‘sqinlik qiluvchilar past.", "strong")
    elif positive < 50:
        profile = ("Rivojlanishi kerak bo‘lgan profil",
                   "Samaradorlik xususiyatlari hali yetarli namoyon bo‘lmagan. Yo‘l-yo‘riq va murabbiylik bilan o‘sishi mumkin.", "develop")
    else:
        profile = ("Muvozanatli profil", "Kuchli tomonlar va to‘sqinlik qiluvchi xususiyatlar o‘rtacha darajada.", "balanced")

    # ---------- Kuchli tomonlar / rivojlanish ----------
    order = {t["id"]: i for i, t in enumerate(traits)}
    strength_ids = [t["id"] for t in traits if t.get("strengthCandidate", t["group"] == "positive")]
    strengths = sorted((k for k in strength_ids if scores[k] >= LIKELY), key=lambda k: (-scores[k], order[k]))[:4]
    dev = sorted((t["id"] for t in traits if t["group"] == "negative" and t.get("developCandidate", True) and scores[t["id"]] >= LIKELY),
                 key=lambda k: (-scores[k], order[k]))
    dev += sorted((t["id"] for t in traits if t["group"] == "positive" and scores[t["id"]] <= WEAK), key=lambda k: (scores[k], order[k]))
    dev = dev[:4]
    strengths_out = [{"id": k, "title": t_by_id[k]["title"], "percent": scores[k], "text": t_by_id[k].get("strengthText", "")} for k in strengths]
    dev_out = [{"id": k, "title": t_by_id[k]["title"], "percent": scores[k],
                "text": t_by_id[k].get("riskText" if t_by_id[k]["group"] == "negative" else "lowText", "")} for k in dev]
    patterns = [{"title": t, "text": x} for t, x, cond in PATTERNS if cond(scores)]

    # ---------- Lavozimlar ----------
    roles = []
    for r in test.get("roles") or []:
        w = r["weights"]
        val = sum((scores[k] if t_by_id[k]["group"] == "positive" else 100 - scores[k]) * v for k, v in w.items()) / sum(w.values())
        roles.append({"name": r["name"], "percent": round(val)})
    roles.sort(key=lambda r: (-r["percent"], r["name"]))

    # ---------- HR xulosasi ----------
    if level == REL_LOW:
        decision = (DEC_UNRELIABLE, "Javoblar diqqatsiz yoki o‘zini ideal ko‘rsatish uchun berilgan bo‘lishi mumkin. "
                                    "Bu natijaga qarab qaror chiqarmang, testni qayta topshirtiring.")
    elif negative >= 60:
        decision = (DEC_CAUTION, "To‘sqinlik qiluvchi xususiyatlar yuqori. Ishga olishdan oldin quyidagi savollar bilan suhbat "
                                 "o‘tkazing va sinov muddati belgilang.")
    elif positive >= 70 and negative < 45:
        decision = (DEC_HIRE, "Ish uchun muhim xususiyatlar kuchli, to‘sqinlik qiluvchilar past. Suhbatda kuchli tomonlarni "
                              "hayotiy misollar bilan tasdiqlang.")
    else:
        decision = (DEC_INTERVIEW, "Profil o‘rtacha. Rivojlanish kerak bo‘lgan tomonlarni suhbatda aniqlashtiring, keyin qaror qiling.")

    # ---------- Suhbat savollari ----------
    questions = []
    for k in dev:
        questions += t_by_id[k].get("interview") or []
    for k in sorted((t["id"] for t in traits if t["group"] == "negative" and scores[t["id"]] >= LIKELY and t["id"] not in dev),
                    key=lambda k: (-scores[k], order[k])):
        questions += (t_by_id[k].get("interview") or [])[:1]
    questions += test.get("commonInterview") or []
    seen_q, interview = set(), []
    for q in questions:
        if q not in seen_q:
            seen_q.add(q)
            interview.append(q)
    interview = interview[:8]

    development = [{"title": t_by_id[k]["title"], "text": t_by_id[k].get("developText", "")} for k in dev]

    first = (full_name.split(" ")[1] if len(full_name.split(" ")) > 1 else full_name).strip()
    report = {
        "version": 2,
        "name": first,
        "profile": {"title": profile[0], "text": profile[1], "kind": profile[2]},
        "positive": positive, "negative": negative,
        "reliability": reliability,
        "traits": trait_rows,
        "directions": directions,
        "strengths": strengths_out,
        "development": dev_out,
        "patterns": patterns,
        "decision": {"title": decision[0], "text": decision[1]},
        "roles": roles,
        "interview": interview,
        "recommendations": development,
        "disclaimer": DISCLAIMER,
    }
    return {
        "format": FORMAT,
        "items": items,
        "total": len(items),
        "points": sum(points.values()), "maxPoints": sum(counts.values()),
        "percent": positive,  # ro‘yxat/CSV uchun: yuqori samaradorlik foizi
        "passPercent": None,
        "status": decision[0],
        "passed": decision[0] == DEC_HIRE,
        "scores": scores,
        "profileTitle": profile[0],
        "reliabilityLevel": level,
        "positive": positive, "negative": negative,
        "bestPosition": roles[0] if roles else None,
        "sections": [{"id": t["id"], "title": t["title"], "points": t["points"], "maxPoints": t["max"], "percent": t["percent"]}
                     for t in trait_rows],
        "report": report,
    }


def report_text(result: dict) -> str:
    """Nusxalash uchun matn (HR bo‘limiga Telegram orqali yuborish)."""
    r = result.get("report") or {}
    sub = str(result.get("submittedAt") or "")
    date = f"{sub[8:10]}.{sub[5:7]}.{sub[:4]}" if sub else ""
    lines = [
        "ISHDAGI SHAXSIYAT 360 — NATIJA",
        f"Ism: {result.get('fullName') or r.get('name') or '—'}",
        f"Sana: {date}",
    ]
    if result.get("position"):
        lines.append(f"Lavozim (tanlangan): {result['position']}")
    if result.get("phone"):
        lines.append(f"Telefon: {result['phone']}")
    lines += [
        f"Profil: {(r.get('profile') or {}).get('title', '')}",
        f"Yuqori samaradorlik: {r.get('positive')}%, to‘sqinlik qiluvchi: {r.get('negative')}%",
        "Yo‘nalishlar: " + ", ".join(f"{d['title']} {d['percent']}%" for d in r.get("directions") or []),
        "Xususiyatlar: " + ", ".join(f"{t['title']} {t['percent']}%" for t in r.get("traits") or []),
        "Kuchli tomonlari: " + (", ".join(s["title"] for s in r.get("strengths") or []) or "—"),
        "Rivojlanish kerak: " + (", ".join(s["title"] for s in r.get("development") or []) or "—"),
        f"Ishonchlilik: {(r.get('reliability') or {}).get('level', '')}",
        f"HR xulosasi: {(r.get('decision') or {}).get('title', '')}",
        "Eng mos lavozimlar: " + ", ".join(f"{p['name']} {p['percent']}%" for p in (r.get("roles") or [])[:3]),
    ]
    if r.get("interview"):
        lines.append("Suhbat savollari:")
        lines += [f"  {i}. {q}" for i, q in enumerate(r["interview"], 1)]
    return "\n".join(lines)
