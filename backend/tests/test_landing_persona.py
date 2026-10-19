"""
Landing (/test/sotuv) — «Ishdagi shaxsiyat 360» (app/persona_test.py, format=persona):
40 savol (matni va tartibi), 13 xususiyat, 4 yo‘nalish, diqqat tekshiruvi, ishonchlilik, profil, HR xulosasi,
lavozimlar, naqshlar, nusxalash matni, landing API orqali saqlash va xodimga bog‘lash.
"""
import copy
import itertools
import json
from datetime import date

import pytest

from app import landing
from app import persona_test as ps

from .conftest import API

PUBLIC = f"{API}/public/tests/sotuv"
SUBMIT = f"{API}/public/tests/sotuv/submit"

FIRST_Q = "Va'da qilgan ishimni hech kim eslatmasa ham o'z vaqtida bajaraman."
Q21 = "Diqqat tekshiruvi: bu savolga «Mutlaqo qo'shilmayman» deb javob bering."
LAST_Q = "Rejalar o'zgarishini yoqtirmayman va unga qarshilik qilaman."


@pytest.fixture(scope="module")
def cfg():
    return landing.load_questionnaire("sotuv")


def answers_for(cfg, points: dict, attention_ok=True):
    """Har bir xususiyat uchun nechta savol 1 ball berishini belgilab, haqiqiy javoblar to‘plamini yasaydi."""
    left = dict(points)
    out = {}
    # Ball avval teskari savollarga beriladi (real javobga yaqin: hamma savolga «Qo‘shilaman» bo‘lib qolmaydi)
    order = sorted((q for q in cfg["questions"] if not q.get("attention")), key=lambda q: q["key"] != "reverse")
    for q in order:
        give = left.get(q["trait"], 0) > 0
        if give:
            left[q["trait"]] -= 1
        out[q["id"]] = (1 if give else 0) if q["key"] == "direct" else (0 if give else 1)
    for q in cfg["questions"]:
        if q.get("attention"):
            out[q["id"]] = q["expected"] if attention_ok else 1 - q["expected"]
    return {k: out[k] for k in sorted(out)}


def all_traits(cfg, n):
    return {t["id"]: n for t in cfg["traits"]}


# Foydalanuvchi namunasidagi profil (Mirzohid): 67% → 3 tadan 2 ta, 100% → 3 ta
SAMPLE = {"innovatsiya": 2, "feedback": 2, "yordam": 3, "ijtimoiylik": 2, "tasdiqlash": 3, "qaramlik": 3, "ruhiy_bosim": 2,
          "qattiqqollik": 3, "xusumat": 3, "nazorat": 3, "raqobat": 3, "masuliyat": 2, "yutuq": 3}


# ---------- Savollar ----------
def test_40_questions_exact_order_and_text(cfg):
    qs = cfg["questions"]
    assert len(qs) == 40 and [q["id"] for q in qs] == list(range(1, 41))
    assert qs[0]["text"] == FIRST_Q and qs[20]["text"] == Q21 and qs[39]["text"] == LAST_Q
    assert qs[20]["attention"] and qs[20]["expected"] == 0
    assert [len(s["questionIds"]) for s in ps.stages(cfg)] == [10, 10, 10, 10]
    assert cfg["options"] == ["Qo‘shilmayman", "Qo‘shilaman"]


def test_13_traits_with_3_questions_each(cfg):
    assert len(cfg["traits"]) == 13
    for t in cfg["traits"]:
        assert sum(1 for q in cfg["questions"] if q.get("trait") == t["id"]) == 3, t["id"]
    reverse = sorted(q["id"] for q in cfg["questions"] if q.get("key") == "reverse")
    assert reverse == [16, 28, 32, 34, 35]


# ---------- Hisoblash ----------
def test_sample_profile_matches_expected_report(cfg):
    g = ps.grade(cfg, answers_for(cfg, SAMPLE, attention_ok=False), 276, "Shermanov Mirzohid")
    s = g["scores"]
    assert s == {"innovatsiya": 67, "feedback": 67, "yordam": 100, "ijtimoiylik": 67, "tasdiqlash": 100, "qaramlik": 100,
                 "ruhiy_bosim": 67, "qattiqqollik": 100, "xusumat": 100, "nazorat": 100, "raqobat": 100, "masuliyat": 67, "yutuq": 100}
    r = g["report"]
    assert (r["positive"], r["negative"]) == (78, 95)
    d = {x["id"]: x["percent"] for x in r["directions"]}
    assert d["natija"] == 84 and d["jamoa"] == 78 and d["moslashish"] == 89
    assert r["profile"]["title"] == "E'tibor talab qiladigan profil"
    assert r["reliability"]["level"] == "past" and not r["reliability"]["attentionOk"]
    assert r["decision"]["title"] == "Natija ishonchsiz" == g["status"]
    assert [x["title"] for x in r["strengths"]] == ["Yordamsevarlik", "Raqobatchilik", "Yutuqqa intilish", "Innovatsiya"]
    assert [x["title"] for x in r["development"]] == ["Tasdiqlash izlash", "Qaramlik", "Qattiqqo'llik", "Xusumat"]
    titles = [p["title"] for p in r["patterns"]]
    for t in ("Iliq, lekin qizishganda qattiq", "Ergashuvchan va ikkilanuvchi", "Raqobat jamoaga to‘siq bo‘lishi mumkin",
              "Sog‘lom raqobatchi", "G‘oyasi ko‘p, lekin o‘zinikiga yopishadi", "Jamoaning tayanchi"):
        assert t in titles
    assert "Oldingi ishingizdan nima sababdan ketgansiz?" in r["interview"]
    assert r["name"] == "Mirzohid"


def test_attention_check_decides_reliability(cfg):
    good = ps.grade(cfg, answers_for(cfg, SAMPLE), 300)
    assert good["report"]["reliability"]["level"] == "yuqori"
    assert good["status"] == "Ehtiyotkorlik bilan"   # to‘sqinlik qiluvchilar 95%
    bad = ps.grade(cfg, answers_for(cfg, SAMPLE, attention_ok=False), 300)
    assert bad["report"]["reliability"]["level"] == "past" and bad["status"] == "Natija ishonchsiz"


def test_reverse_items_inverted(cfg):
    base = answers_for(cfg, all_traits(cfg, 0))
    assert ps.grade(cfg, base, 300)["scores"]["ijtimoiylik"] == 0
    base[16] = 0  # teskari: «Imkon bo'lsa, ... kamroq muloqot» — «Qo‘shilmayman» → 1 ball
    assert ps.grade(cfg, base, 300)["scores"]["ijtimoiylik"] == 33


def test_strong_profile_recommended(cfg):
    pts = {t["id"]: (3 if t["group"] == "positive" else 0) for t in cfg["traits"]}
    pts["innovatsiya"] = 2  # to‘liq "ideal" emas
    g = ps.grade(cfg, answers_for(cfg, pts), 320)
    assert g["report"]["profile"]["title"] == "Kuchli profil"
    assert g["report"]["reliability"]["level"] == "yuqori"
    assert g["status"] == "Ishga olish tavsiya etiladi"
    assert g["report"]["development"] == [] and len(g["report"]["strengths"]) == 4


def test_ideal_answers_lower_reliability(cfg):
    pts = {t["id"]: (3 if t["group"] == "positive" else 0) for t in cfg["traits"]}
    g = ps.grade(cfg, answers_for(cfg, pts), 320)
    assert g["report"]["reliability"]["level"] == "o‘rtacha"
    assert any("ideal" in i for i in g["report"]["reliability"]["issues"])


def test_all_agree_like_sample_is_detected(cfg):
    """Hamma savolga «Qo‘shilaman» — namunadagi profilga o‘xshash foizlar chiqadi, lekin ishonchlilik past."""
    g = ps.grade(cfg, {q["id"]: 1 for q in cfg["questions"]}, 276)
    assert g["report"]["reliability"]["level"] == "past"
    assert any("bir xil javob" in i for i in g["report"]["reliability"]["issues"])
    assert any("Diqqat tekshiruvi" in i for i in g["report"]["reliability"]["issues"])


def test_one_sided_and_fast_answers_unreliable(cfg):
    all_yes = {q["id"]: 1 for q in cfg["questions"]}
    all_yes[21] = 0
    assert ps.grade(cfg, all_yes, 300)["report"]["reliability"]["level"] == "past"
    g = ps.grade(cfg, answers_for(cfg, SAMPLE), 50)  # 1.25 s/savol
    assert g["report"]["reliability"]["level"] == "past"
    g = ps.grade(cfg, answers_for(cfg, SAMPLE), 90)  # 2.25 s/savol
    assert g["report"]["reliability"]["level"] == "o‘rtacha"


def test_role_match_weighted_and_negative_inverted(cfg):
    g = ps.grade(cfg, answers_for(cfg, SAMPLE), 300)
    s = g["scores"]
    by = {r["name"]: r["percent"] for r in g["report"]["roles"]}
    for role in cfg["roles"]:
        grp = {t["id"]: t["group"] for t in cfg["traits"]}
        w = role["weights"]
        exp = round(sum((s[k] if grp[k] == "positive" else 100 - s[k]) * v for k, v in w.items()) / sum(w.values()))
        assert by[role["name"]] == exp
    pcts = [r["percent"] for r in g["report"]["roles"]]
    assert pcts == sorted(pcts, reverse=True)


def test_deterministic(cfg):
    a = answers_for(cfg, SAMPLE)
    assert all(ps.grade(cfg, a, 300) == ps.grade(cfg, a, 300) for _ in range(3))


def test_report_text_format(cfg):
    g = ps.grade(cfg, answers_for(cfg, SAMPLE, attention_ok=False), 300, "Shermanov Mirzohid")
    text = ps.report_text({**g, "fullName": "Shermanov Mirzohid", "submittedAt": "2026-10-16T10:22"})
    for part in ("ISHDAGI SHAXSIYAT 360 — NATIJA", "Ism: Shermanov Mirzohid", "Sana: 16.10.2026",
                 "Profil: E'tibor talab qiladigan profil", "Yuqori samaradorlik: 78%, to‘sqinlik qiluvchi: 95%",
                 "Natijaga ishlash 84%", "Innovatsiya 67%", "Kuchli tomonlari: Yordamsevarlik, Raqobatchilik",
                 "Ishonchlilik: past", "HR xulosasi: Natija ishonchsiz", "Eng mos lavozimlar:"):
        assert part in text, part


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d["questions"][0].update(trait="yoq"), "xususiyati noma’lum"),
    (lambda d: d["questions"][20].update(expected=5), "diqqat"),
    (lambda d: d.update(pairs=[[1, 14]]), "qarama-qarshi"),
    (lambda d: d["roles"][0]["weights"].update(foo=1), "weights"),
    (lambda d: d["traits"][0].update(group="x"), "group"),
])
def test_validate_config_errors(cfg, mutate, message):
    d = copy.deepcopy(cfg)
    mutate(d)
    with pytest.raises(ValueError, match=message):
        ps.validate_config(d)


# ---------- API ----------
_phones = itertools.count(1)


def candidate(**over):
    # Telefon majburiy va noyob — har bir nomzodga alohida raqam
    data = {"fullName": "Shermanov Mirzohid", "age": 25, "date": date.today().isoformat(), "position": "Marketing",
            "phone": f"+99893{next(_phones):07d}"}
    data.update(over)
    return data


def as_json(a):
    return {str(k): v for k, v in a.items()}


def test_public_view_hides_key(client):
    t = client.get(PUBLIC).json()
    assert t["format"] == "persona" and len(t["questions"]) == 40 and t["questions"][20]["text"] == Q21
    assert [len(s["questionIds"]) for s in t["stages"]] == [10, 10, 10, 10]
    assert t["positions"] == ["Sotuv menejeri", "Sotuv operatori (Call Center)", "Savdo maslahatchisi", "Marketing", "Logistika"]
    text = json.dumps(t, ensure_ascii=False)
    for secret in ("reverse", "direct", "trait", "expected", "attention", "weights", "riskText"):
        assert secret not in text, secret


def test_submit_and_hr_report(client, hr_headers, cfg):
    r = client.post(SUBMIT, json={**candidate(phone="903544499"), "answers": as_json(answers_for(cfg, SAMPLE, False)), "durationSec": 276})
    assert r.status_code == 201, r.text and set(r.json()) == {"id", "submittedAt"}
    rid = r.json()["id"]
    row = next(x for x in client.get(f"{API}/landing-results", headers=hr_headers).json() if x["id"] == rid)
    assert row["format"] == "persona" and row["status"] == "Natija ishonchsiz"
    assert row["profileTitle"] == "E'tibor talab qiladigan profil" and row["reliabilityLevel"] == "past"
    assert (row["positive"], row["negative"]) == (78, 95)
    d = client.get(f"{API}/landing-results/{rid}", headers=hr_headers).json()
    assert len(d["items"]) == 40 and d["report"]["version"] == 2
    assert d["reportText"].startswith("ISHDAGI SHAXSIYAT 360 — NATIJA") and "Telefon: +998 90 354 44 99" in d["reportText"]


@pytest.mark.parametrize("bad", [2, -1, "ha", 0.5])
def test_submit_rejects_invalid(client, cfg, bad):
    a = as_json(answers_for(cfg, SAMPLE))
    a["5"] = bad
    assert client.post(SUBMIT, json={**candidate(), "answers": a}).status_code == 400


def test_submit_rejects_missing(client, cfg):
    a = as_json(answers_for(cfg, SAMPLE))
    a.pop("21")
    r = client.post(SUBMIT, json={**candidate(), "answers": a})
    assert r.status_code == 400 and "21" in r.json()["detail"]


def test_linked_to_employee_by_name(client, hr_headers, cfg):
    e = client.post(f"{API}/employees", headers=hr_headers, json={"firstName": "Dilshod", "lastName": "Qodirov", "phone": "+998901110000"})
    assert e.status_code in (200, 201), e.text
    rid = client.post(SUBMIT, json={**candidate(fullName="Qodirov Dilshod"), "answers": as_json(answers_for(cfg, SAMPLE))}).json()["id"]
    assert client.get(f"{API}/landing-results/{rid}", headers=hr_headers).json()["employeeId"] == e.json()["id"]


def test_hr_key(client, hr_headers):
    k = client.get(f"{API}/landing-tests/sotuv/key", headers=hr_headers).json()
    assert k["format"] == "persona" and len(k["questions"]) == 40 and k["maxPoints"] == 39
    assert len(k["sections"]) == 14 and len(k["directions"]) == 4
    q21 = next(q for q in k["questions"] if q["id"] == 21)
    assert q21["attention"] and [c["points"] for c in q21["choices"]] == [1, 0]