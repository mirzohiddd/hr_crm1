"""
Test natijalarini CRM’dagi nomzod va xodim profillariga bog‘lash.

Bog‘lash qoidalari (noto‘g‘ri bog‘lashdan himoya — faqat YAGONA mos yozuv bo‘lsa bog‘lanadi):
- Nomzodlar testi (landing, /test/sotuv): telefon raqami bo‘yicha (oxirgi 9 raqam). CRM’da telefon
  nomzodlar orasida noyob, shuning uchun bu eng ishonchli kalit.
- Yakuniy bilim testi (landing-2, /test/yakuniy): familiya + ism bo‘yicha.
    * xodim: familiya va ism mos, xodimda tug‘ilgan sana yozilgan bo‘lsa — u ham mos bo‘lishi kerak;
    * nomzod: xodimning candidateId si (ishga olingan nomzod) yoki familiya + ism mos va yoshi
      (nomzodda ko‘rsatilgan bo‘lsa) mos keladigan yagona nomzod.

Topshirish paytida topilgan bog‘lanish natijaga yoziladi (candidateId, employeeId).
Bu o‘zgarishdan oldin saqlangan natijalarda bu maydonlar yo‘q — ular uchun bog‘lanish o‘qish paytida
shu qoidalar bilan hisoblanadi (eski yozuvlar o‘zgartirilmaydi).
"""
from .utils import phone_key

# HR javobida bog‘langan nomzod haqida qisqa ma'lumot
CANDIDATE_BRIEF = ("id", "fullName", "phone", "status", "positionId", "employeeId")


def norm(v) -> str:
    """Ismlarni solishtirish uchun: tutuq belgilari bir xil, ortiqcha bo‘sh joysiz, katta-kichik harf farqsiz."""
    return " ".join(str(v or "").replace("ʻ", "‘").replace("'", "‘").replace("`", "‘").replace("’", "‘").replace("ʼ", "‘").split()).casefold()


def candidate_brief(c: dict | None) -> dict | None:
    return {k: c.get(k) for k in CANDIDATE_BRIEF} if c else None


def _unique(rows: list[dict]) -> dict | None:
    return rows[0] if len(rows) == 1 else None


# ---------- Nomzodlar testi (telefon bo‘yicha) ----------
def candidate_by_phone(store, phone: str | None) -> dict | None:
    key = phone_key(phone)
    if not key:
        return None
    return _unique([c for c in store.candidates.all() if phone_key(c.get("phone")) == key])


def phone_index(store) -> dict[str, int | None]:
    """Telefon kaliti → nomzod id (bir raqam bir nechta nomzodda bo‘lsa — None). Ro‘yxatlar uchun bir marta tuziladi."""
    index: dict[str, int | None] = {}
    for c in store.candidates.all():
        key = phone_key(c.get("phone"))
        if key:
            index[key] = None if key in index else c["id"]
    return index


def landing_candidate_id(store, row: dict, index: dict | None = None) -> int | None:
    """Saqlangan candidateId; eski yozuvda — telefon bo‘yicha (o‘qish paytida)."""
    if "candidateId" in row:
        return row.get("candidateId")
    key = phone_key(row.get("phoneKey") or row.get("phone"))
    if not key:
        return None
    if index is None:
        index = phone_index(store)
    return index.get(key)


# ---------- Yakuniy bilim testi (familiya + ism bo‘yicha) ----------
def _name_parts(full_name: str) -> tuple[str, str]:
    parts = norm(full_name).split(" ")
    return (parts[0], parts[1]) if len(parts) >= 2 else ("", "")


def match_final_person(store, last_name: str, first_name: str, age=None, birth_date: str = "") -> tuple[int | None, int | None]:
    """(employeeId, candidateId) — ishtirokchi ma'lumotlari bo‘yicha; mos yozuv yagona bo‘lmasa — None."""
    last, first = norm(last_name), norm(first_name)
    if not last or not first:
        return None, None

    def employee_ok(e):
        if norm(e.get("lastName")) != last or norm(e.get("firstName")) != first:
            return False
        return not (e.get("birthDate") and birth_date) or e["birthDate"] == birth_date

    employee = _unique([e for e in store.employees.all() if employee_ok(e)])

    candidate = None
    if employee and employee.get("candidateId"):
        candidate = store.candidates.get(employee["candidateId"])
    if not candidate:
        def candidate_ok(c):
            if _name_parts(c.get("fullName")) != (last, first):
                return False
            if c.get("age") in (None, "") or age in (None, ""):
                return True
            try:
                return int(c["age"]) == int(age)
            except (TypeError, ValueError):
                return False

        candidate = _unique([c for c in store.candidates.all() if candidate_ok(c)])
    if candidate and not employee and candidate.get("employeeId"):
        employee = store.employees.get(candidate["employeeId"])
    return (employee["id"] if employee else None), (candidate["id"] if candidate else None)


def final_candidate_id(store, row: dict) -> int | None:
    """Saqlangan candidateId; eski yozuvda — familiya/ism bo‘yicha (o‘qish paytida)."""
    if "candidateId" in row:
        return row.get("candidateId")
    if row.get("employeeId"):
        e = store.employees.get(row["employeeId"])
        if e and e.get("candidateId"):
            return e["candidateId"]
    _, cid = match_final_person(store, row.get("lastName"), row.get("firstName"), row.get("age"), row.get("birthDate") or "")
    return cid
