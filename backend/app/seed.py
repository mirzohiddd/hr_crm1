"""
Birinchi ishga tushirishda yaratiladigan ma'lumotnomalar:
bo‘limlar, lavozimlar, 7 kunlik dars rejasi, ikkita test, test sozlamalari va administrator.
Xodim/nomzod kabi soxta ma'lumotlar YARATILMAYDI — bazaga faqat real ma'lumot kiritiladi.
Har bir JSON fayl faqat bo‘sh bo‘lsa to‘ldiriladi (mavjud ma'lumotlarga tegmaydi).
"""
from .config import ADMIN_LOGIN, ADMIN_NAME, ADMIN_PASSWORD
from .security import hash_password
from .services import DEFAULT_SETTINGS
from .store import Store
from .utils import now_local

DEPARTMENTS = [
    ("Dermolife", "Dermolife yo‘nalishi"),
    ("Gepomer", "Gepomer yo‘nalishi"),
    ("Halila", "Halila yo‘nalishi"),
    ("Marketing", "Reklama, ijtimoiy tarmoqlar va izohlar"),
    ("Boshqa", "Umumiy va xo‘jalik xodimlari"),
]

POSITIONS = [
    ("Call Center", "Kiruvchi va chiquvchi qo‘ng‘iroqlar, buyurtmalarni qabul qilish"),
    ("Kommentiy", "Instagram va Telegram izohlari hamda direct xabarlarga javob berish"),
    ("Marketing", "Reklama kampaniyalari va kontent rejasi"),
    ("Logistika", "Yetkazib berish jadvali, kuryerlar va ombor nazorati"),
    ("Tozalik xodimi", "Ofis va ish joylari tozaligi"),
    ("HR Admin", "Nomzodlar, xodimlar va o‘quv jarayonini boshqarish"),
]

LESSONS = [
    (1, "Kompaniya bilan tanishuv", 60, "Kompaniya tarixi, missiyasi, tuzilmasi va jamoa bilan tanishish.",
     "Kompaniyaning qisqacha tarixi va qadriyatlari\nBo‘limlar va ularning vazifalari\nRahbarlar va murojaat tartibi\nIsh joyi, jihozlar va aloqa kanallari"),
    (2, "Ichki tartib qoidalari", 45, "Ish vaqti, kiyinish qoidalari, xavfsizlik va intizom talablari.",
     "Ish vaqti 09:00 – 18:00, tushlik 13:00 – 14:00\nKechikish va ruxsat so‘rash tartibi\nKiyinish qoidalari\nMaxfiylik va axborot xavfsizligi"),
    (3, "Mahsulot va xizmatlar", 90, "Kompaniya mahsulotlari, narxlar va eng ko‘p beriladigan savollar.",
     "Asosiy mahsulotlar va ularning afzalliklari\nNarxlar va chegirmalar siyosati\nYetkazib berish shartlari\nKo‘p beriladigan savollar va javoblar"),
    (4, "Mijozlar bilan muloqot", 90, "Muloqot standarti, e’tirozlar bilan ishlash va norozi mijoz bilan gaplashish.",
     "Salomlashish va o‘zini tanishtirish standarti\nMijoz ehtiyojini aniqlash\nE’tirozlar bilan ishlash\nNorozi mijoz bilan muloqot qoidalari"),
    (5, "CRM va ish vositalari", 60, "Ichki tizimlar, buyurtma kiritish va hisobot berish tartibi.",
     "CRM tizimiga kirish va buyurtma kiritish\nIchki chat va vazifalar\nKunlik hisobot shakli\nParol va hisob xavfsizligi"),
    (6, "Lavozim bo‘yicha amaliyot", 120, "Tajribali xodim (murabbiy) yonida real ish jarayonida amaliyot.",
     "Murabbiy bilan birga ish jarayonini kuzatish\nMustaqil vazifalarni murabbiy nazoratida bajarish\nXatolar ustida ishlash"),
    (7, "Takrorlash va yakuniy tayyorgarlik", 60, "O‘tilgan mavzularni takrorlash va yakuniy testga tayyorgarlik.",
     "1–6 kun mavzularini takrorlash\nSavol-javob\nYakuniy testga tayyorgarlik"),
]


def _q(qid, text, options, correct):
    return {"id": qid, "text": text, "options": options, "correctIndex": correct}


TESTS = [
    {
        "title": "Umumiy yakuniy test",
        "description": "7 kunlik o‘quv dasturi bo‘yicha barcha yangi xodimlar uchun yakuniy test.",
        "position_names": [],
        "questions": [
            _q(1, "Ish kuni soat nechada boshlanadi?", ["08:00", "09:00", "10:00", "Erkin grafik"], 1),
            _q(2, "Ishga kechikadigan bo‘lsangiz nima qilishingiz kerak?", ["Hech narsa", "Rahbarga oldindan xabar berish", "Ertasi kuni aytish", "Hamkasbga aytish"], 1),
            _q(3, "Mijoz ma’lumotlarini begonalarga berish mumkinmi?", ["Ha, so‘rasa", "Faqat tanishlarga", "Yo‘q, bu maxfiy ma’lumot", "Faqat telefon raqamini"], 2),
            _q(4, "Mijoz bilan suhbat nimadan boshlanadi?", ["Narxni aytishdan", "Salomlashish va o‘zini tanishtirishdan", "Chegirma taklif qilishdan", "Buyurtma raqamini so‘rashdan"], 1),
            _q(5, "Norozi mijoz bilan qanday gaplashish kerak?", ["Ovozni ko‘tarib", "Xotirjam tinglab, yechim taklif qilib", "Suhbatni tugatib", "Rahbarga darhol uzatib"], 1),
            _q(6, "Buyurtmalar qayerga kiritiladi?", ["Daftarga", "Shaxsiy telefonga", "CRM tizimiga", "Telegram guruhga"], 2),
            _q(7, "Hisob parolingizni hamkasbingizga aytish mumkinmi?", ["Ha", "Yo‘q", "Faqat rahbarga", "Faqat bir marta"], 1),
            _q(8, "Kunlik hisobot qachon topshiriladi?", ["Hafta oxirida", "Ish kuni yakunida", "Oy oxirida", "Talab qilinmaydi"], 1),
            _q(9, "Savolga javob bilmasangiz nima qilasiz?", ["Taxminiy javob beraman", "Mijozni kuttirib, aniqlab javob beraman", "Javob bermayman", "Suhbatni uzaman"], 1),
            _q(10, "Murabbiy kim?", ["Yangi xodim", "Tajribali xodim, amaliyotda yordam beradi", "Mijoz", "Tashqi tekshiruvchi"], 1),
        ],
    },
    {
        "title": "Call Center testi",
        "description": "Call Center xodimlari uchun qo‘ng‘iroqlar standarti bo‘yicha test.",
        "position_names": ["Call Center"],
        "questions": [
            _q(1, "Qo‘ng‘iroqqa necha signal ichida javob berish kerak?", ["3 signal ichida", "10 signal", "Farqi yo‘q", "1 daqiqa ichida"], 0),
            _q(2, "Suhbat boshida nima aytiladi?", ["Faqat “Allo”", "Kompaniya nomi, ismingiz va salomlashish", "Narxlar ro‘yxati", "Hech narsa"], 1),
            _q(3, "Mijoz buyurtma bermasa nima qilinadi?", ["Qayta qo‘ng‘iroq qilmaslik", "Sababini yozib, CRMda belgilash", "Raqamni o‘chirish", "Bahslashish"], 1),
            _q(4, "Buyurtma tasdiqlanganda mijozga nima aytiladi?", ["Hech narsa", "Yetkazib berish sanasi va summasi", "Faqat rahmat", "Boshqa mahsulot narxi"], 1),
            _q(5, "Bir kunda nechta qo‘ng‘iroqlar hisobotga yoziladi?", ["Faqat muvaffaqiyatlilari", "Barchasi", "Faqat kiruvchilar", "Hech biri"], 1),
        ],
    },
]


def seed(store: Store) -> list[str]:
    """Bo‘sh JSON fayllarni to‘ldiradi. Nima yaratilganini qaytaradi (log uchun)."""
    done = []
    if store.departments.is_empty():
        for n, d in DEPARTMENTS:
            store.departments.insert({"name": n, "description": d})
        done.append("bo‘limlar")
    if store.positions.is_empty():
        for n, d in POSITIONS:
            store.positions.insert({"name": n, "description": d})
        done.append("lavozimlar")
    if store.lessons.is_empty():
        for day, t, m, d, c in LESSONS:
            store.lessons.insert({"day": day, "title": t, "duration": m, "description": d, "content": c, "link": ""})
        done.append("7 kunlik darslar")
    if store.tests.is_empty():
        by_name = {p["name"]: p["id"] for p in store.positions.all()}
        for t in TESTS:
            store.tests.insert({
                "title": t["title"],
                "description": t["description"],
                "positionIds": [by_name[n] for n in t["position_names"] if n in by_name],
                "passPercent": 80,
                "active": True,
                "questions": t["questions"],
            })
        done.append("testlar")
    if store.settings.is_empty():
        store.settings.replace_all([DEFAULT_SETTINGS])
    if store.users.is_empty():
        store.users.insert({
            "fullName": ADMIN_NAME,
            "login": ADMIN_LOGIN.lower(),
            "role": "admin",
            "email": "",
            "phone": "",
            "active": True,
            "passwordHash": hash_password(ADMIN_PASSWORD),
            "createdAt": now_local()[:10],
            "lastLoginAt": None,
        })
        done.append(f"administrator ({ADMIN_LOGIN})")
    # Bo‘sh to‘plamlar uchun ham fayl yaratiladi — qaysi fayllar borligi aniq ko‘rinsin
    for name in ("employees", "candidates", "trainings", "test_results", "documents"):
        coll = getattr(store, name)
        if not coll.path.exists():
            coll.replace_all([])
    return done
