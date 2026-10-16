"""
4 shkalali 40 savolli test dvigateli (app/profile_test.py, format=profile) — avval saqlangan natijalar va
shu formatdagi savolnomalar uchun. Namuna savolnoma: tests/fixtures/profile_sotuv.json.
Joriy «Ishdagi shaxsiyat 360» testi — test_landing_persona.py.
"""
import copy
import json
from pathlib import Path

import pytest

from app import landing
from app import profile_test as fp


@pytest.fixture(scope="module")
def test_cfg():
    raw = json.loads((Path(__file__).parent / "fixtures" / "profile_sotuv.json").read_text(encoding="utf-8"))
    raw.pop("_izoh", None)
    return fp.validate_config(raw)


def ideal(test):
    """Har bir savoldan 1 ball (samimiylik savollarida — samimiy javob)."""
    return {q["id"]: fp.AGREE if q["key"] == "direct" else fp.DISAGREE for q in test["questions"]}


def flip(ans, ids):
    out = dict(ans)
    for i in ids:
        out[i] = 1 - out[i]
    return out


def qids(test, scale, key=None):
    return [q["id"] for q in test["questions"] if q["scale"] == scale and (key is None or q["key"] == key)]


# ---------- Tuzilma ----------
def test_config_40_questions_4_stages_and_balanced_keys(test_cfg):
    qs = test_cfg["questions"]
    assert len(qs) == 40 and [q["id"] for q in qs] == list(range(1, 41))
    assert [len(s["questionIds"]) for s in fp.stages(test_cfg)] == [10, 10, 10, 10]
    assert test_cfg["options"] == ["Qo‘shilmayman", "Qo‘shilaman"]
    for s in test_cfg["scales"]:
        direct, reverse = qids(test_cfg, s["id"], "direct"), qids(test_cfg, s["id"], "reverse")
        assert len(direct) == len(reverse) == 4, s["id"]  # teskari savollar teng — bir xil javob berish ta’siri kamayadi
    assert len(qids(test_cfg, test_cfg["sincerity"]["id"])) == 8
    assert len(test_cfg["pairs"]) == 8


# ---------- Hisoblash ----------
def test_item_point_direct_and_reverse():
    assert fp.item_point("direct", fp.AGREE) == 1 and fp.item_point("direct", fp.DISAGREE) == 0
    assert fp.item_point("reverse", fp.AGREE) == 0 and fp.item_point("reverse", fp.DISAGREE) == 1


def test_ideal_answers_give_full_scores_and_full_reliability(test_cfg):
    g = fp.grade(test_cfg, ideal(test_cfg), duration_sec=400)
    assert g["scores"] == {"masuliyat": 100, "stress": 100, "muloqot": 100, "hamdardlik": 100}
    assert g["percent"] == 100 and g["reliability"] == 100 and g["status"] == fp.REC_RECOMMENDED
    rel = g["report"]["reliability"]
    assert rel["sincerity"] == 100 and rel["inconsistentPairs"] == 0 and not rel["oneSided"]
    assert g["points"] == 32 and g["maxPoints"] == 32 and g["total"] == 40


def test_reverse_items_are_scored_inverted(test_cfg):
    """Teskari savolga «Qo‘shilaman» — shkala bali kamayadi; to‘g‘ri savolga «Qo‘shilmayman» — ham kamayadi."""
    base = ideal(test_cfg)
    rev = qids(test_cfg, "stress", "reverse")[:2]   # 2 ta teskari savolga «Qo‘shilaman»
    g = fp.grade(test_cfg, flip(base, rev), 400)
    assert g["scores"]["stress"] == 75 and g["scores"]["masuliyat"] == 100
    direct = qids(test_cfg, "muloqot", "direct")[:4]  # 4 ta to‘g‘ri savolga «Qo‘shilmayman»
    g = fp.grade(test_cfg, flip(base, direct), 400)
    assert g["scores"]["muloqot"] == 50


def test_sincerity_affects_reliability_not_scores(test_cfg):
    sid = test_cfg["sincerity"]["id"]
    insincere = flip(ideal(test_cfg), qids(test_cfg, sid))  # barcha samimiylik savollarida o‘zini ideal ko‘rsatish
    g = fp.grade(test_cfg, insincere, 400)
    assert g["scores"] == {"masuliyat": 100, "stress": 100, "muloqot": 100, "hamdardlik": 100}
    rel = g["report"]["reliability"]
    assert rel["sincerity"] == 0 and rel["desirableAnswers"] == 8
    assert g["reliability"] == 100 - 8 * fp.SINCERITY_PENALTY
    assert g["status"] == fp.REC_UNRELIABLE
    assert any("Samimiylik past" in n for n in rel["notes"])


def test_inconsistent_pairs_lower_reliability_and_create_interview_question(test_cfg):
    a, b = test_cfg["pairs"][0]
    ans = flip(ideal(test_cfg), [b])  # juftlikning bittasiga qarama-qarshi javob
    g = fp.grade(test_cfg, ans, 400)
    rel = g["report"]["reliability"]
    assert rel["inconsistentPairs"] == 1 and g["reliability"] == 100 - fp.PAIR_PENALTY
    assert rel["inconsistencies"][0]["ids"] == [a, b]
    assert any(q["reason"] == "Javoblardagi ziddiyat" for q in g["report"]["interviewQuestions"])


def test_all_agree_is_detected_as_one_sided_and_unreliable(test_cfg):
    g = fp.grade(test_cfg, {q["id"]: fp.AGREE for q in test_cfg["questions"]}, 400)
    rel = g["report"]["reliability"]
    assert rel["oneSided"] and rel["agreeRatio"] == 100
    assert all(v == 50 for v in g["scores"].values())  # 4 to‘g‘ri + 4 teskari savol
    assert rel["inconsistentPairs"] == 8
    assert g["status"] == fp.REC_UNRELIABLE and g["reliability"] == 0


def test_too_fast_submission_penalty(test_cfg):
    assert fp.grade(test_cfg, ideal(test_cfg), 70)["reliability"] == 100 - fp.FAST_PENALTY        # 1.75 s/savol
    assert fp.grade(test_cfg, ideal(test_cfg), 40)["reliability"] == 100 - fp.VERY_FAST_PENALTY   # 1 s/savol
    assert fp.grade(test_cfg, ideal(test_cfg), None)["reliability"] == 100                        # vaqt noma’lum


def test_results_are_deterministic(test_cfg):
    ans = flip(ideal(test_cfg), [2, 5, 13, 22, 31])
    first = fp.grade(test_cfg, ans, 300)
    for _ in range(5):
        assert fp.grade(test_cfg, ans, 300) == first


def test_position_match_is_weighted_average(test_cfg):
    base = ideal(test_cfg)
    # Muloqot: 0% (4 to‘g‘ri → «Qo‘shilmayman», 4 teskari → «Qo‘shilaman»), qolganlari 100%
    ans = flip(base, qids(test_cfg, "muloqot"))
    g = fp.grade(test_cfg, ans, 400)
    assert g["scores"]["muloqot"] == 0
    by_name = {p["name"]: p["percent"] for p in g["report"]["positions"]}
    for p in test_cfg["positions"]:
        w = p["weights"]
        expected = round(sum(g["scores"][k] * v for k, v in w.items()) / sum(w.values()))
        assert by_name[p["name"]] == expected
    pcts = [p["percent"] for p in g["report"]["positions"]]
    assert pcts == sorted(pcts, reverse=True)
    assert by_name["Sotuv menejeri"] == 60   # muloqot og‘irligi 0.4
    assert g["report"]["positions"][0]["name"] == "Logistika"  # muloqot og‘irligi eng kichik (0.15)


def test_report_sections_for_mixed_profile(test_cfg):
    base = ideal(test_cfg)
    ans = flip(base, qids(test_cfg, "stress")[:5] + qids(test_cfg, "hamdardlik")[:3])
    g = fp.grade(test_cfg, ans, 420)
    rep = g["report"]
    levels = {s["id"]: s["level"] for s in rep["scales"]}
    assert levels["stress"] == "Past" and levels["hamdardlik"] == "O‘rtacha" and levels["masuliyat"] == "Yuqori"
    assert [s["scale"] for s in rep["weaknesses"]] == ["Stressga chidamlilik", "Hamdardlik"]
    assert {s["scale"] for s in rep["strengths"]} == {"Mas’uliyat", "Muloqot"}
    stress_q = [q for q in rep["interviewQuestions"] if q["scale"] == "Stressga chidamlilik" and "past" in q["reason"]]
    assert len(stress_q) == 2
    assert rep["thinkingStyle"]["title"] and rep["hardSituations"]["title"]
    assert rep["development"][0]["scale"] == "Stressga chidamlilik"
    assert g["status"] in (fp.REC_INTERVIEW, fp.REC_RECOMMENDED, fp.REC_EXTRA)
    assert "tashxis emas" in rep["disclaimer"]


def test_low_profile_gets_extra_assessment(test_cfg):
    """Barcha shkalalar past, lekin javoblar izchil va samimiy — ishonchli, ammo qo‘shimcha baholash kerak."""
    sid = test_cfg["sincerity"]["id"]
    ans = {q["id"]: (fp.DISAGREE if q["key"] == "direct" else fp.AGREE) if q["scale"] != sid
           else (fp.AGREE if q["key"] == "direct" else fp.DISAGREE) for q in test_cfg["questions"]}
    g = fp.grade(test_cfg, ans, 400)
    assert all(v == 0 for v in g["scores"].values())
    assert g["reliability"] == 100 and g["status"] == fp.REC_EXTRA


def test_report_text_contains_every_section(test_cfg):
    g = fp.grade(test_cfg, ideal(test_cfg), 400)
    text = fp.report_text({**g, "fullName": "Karimov Aziz", "age": 25, "birthDate": "2001-01-01",
                           "submittedAt": "2026-10-16T10:30", "durationSec": 400, "testTitle": test_cfg["title"]})
    for part in ("HR XULOSASI", "ASOSIY KO‘RSATKICHLAR", "ENG MOS LAVOZIMLAR", "SUHBATDA SO‘RALADIGAN SAVOLLAR",
                 "KUCHLI TOMONLAR", "ZAIF TOMONLAR", "FIKRLASH USLUBI", "QIYIN VAZIYATDAGI XULQ", "RIVOJLANISH TAVSIYALARI",
                 "Karimov Aziz", "16.10.2026 10:30", "Mas’uliyat: 100%", "tashxis emas"):
        assert part in text, part


# ---------- JSON tekshiruvi ----------
@pytest.mark.parametrize("mutate, message", [
    (lambda d: d["questions"][0].update(scale="noma"), "shkalasi noma’lum"),
    (lambda d: d["questions"][0].update(key="x"), "key"),
    (lambda d: d.update(pairs=[[1, 6], [1, 2]]), "juftlik"),
    (lambda d: d["positions"][0]["weights"].update(foo=1), "noma’lum shkala"),
    (lambda d: d.update(options=["Ha"]), "2 ta"),
    (lambda d: d["questions"].append(dict(d["questions"][0])), "takrorlangan"),
])
def test_validate_config_errors(test_cfg, mutate, message):
    d = copy.deepcopy(test_cfg)
    mutate(d)
    with pytest.raises(ValueError, match=message):
        fp.validate_config(d)


def test_old_scale_format_still_scored():
    """Eski 1–5 shkala va A/B/C/D formatidagi savolnomalar ham avvalgidek baholanadi."""
    q = {"slug": "eski", "title": "Eski", "passPercent": 80, "scale": {"min": 1, "max": 5}, "sections": [], "questions": [
        {"id": 1, "type": "scale", "text": "?", "key": "direct"},
        {"id": 2, "type": "scale", "text": "?", "key": "reverse"},
        {"id": 3, "type": "choice", "text": "?", "options": [{"text": "a", "points": 0}, {"text": "b", "points": 5}]},
    ]}
    r = landing.score(q, landing.validate_answers(q, {"1": 5, "2": 1, "3": 1}))
    assert (r["points"], r["maxPoints"], r["percent"], r["status"]) == (15, 15, 100, "O‘tdi")


def test_summary_wording_depends_on_real_spread(test_cfg):
    """Xulosa matni haqiqiy ko‘rsatkichlarga mos: hammasi teng bo‘lsa — "zaif yo‘nalish" deb yozilmaydi."""
    same = fp.grade(test_cfg, ideal(test_cfg), 400)["report"]["summary"]
    assert "bir xil darajada — 100%" in same and "e’tibor talab" not in same
    mixed = fp.grade(test_cfg, flip(ideal(test_cfg), qids(test_cfg, "stress")[:5]), 400)["report"]["summary"]
    assert "e’tibor talab qiladigan yo‘nalish — stressga chidamlilik" in mixed
