"""
Kiruvchi so‘rov sxemalari. JSON maydonlari camelCase (frontend bilan bir xil),
Python ichida snake_case. Yangilashda (PUT) faqat yuborilgan maydonlar o‘zgaradi.
"""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class In(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")

    def values(self) -> dict:
        """Faqat yuborilgan maydonlar, JSON faylga mos camelCase kalitlar bilan."""
        return self.model_dump(exclude_unset=True, by_alias=True)


def _strip(v):
    return v.strip() if isinstance(v, str) else v


# ---------- Auth / foydalanuvchilar ----------
class LoginIn(BaseModel):
    login: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class MeIn(In):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None


class UserIn(In):
    full_name: str | None = None
    login: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9._-]{3,32}$")
    password: str | None = Field(default=None, min_length=6)
    role: Literal["admin", "hr"] | None = None
    email: str | None = None
    phone: str | None = None
    active: bool | None = None


# ---------- Katalog ----------
class CatalogIn(In):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v):
        return _strip(v)


# ---------- Xodimlar ----------
class EmployeeIn(In):
    full_name: str | None = Field(default=None, min_length=3)
    first_name: str | None = None  # Ism
    last_name: str | None = None  # Familiya
    middle_name: str | None = None  # Otasining ismi
    telegram: str | None = None  # @username
    previous_work: str | None = None  # Qayerda ishlagan
    computer_skill: str | None = None  # Kompyuter savodxonligi
    expected_salary: int | None = Field(default=None, ge=0)  # Kutilayotgan oylik (so‘m)
    gender: str | None = None
    birth_date: str | None = None
    age: int | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    department_id: int | None = None
    position_id: int | None = None
    hire_date: str | None = None
    status: Literal["Yangi", "Faol", "Faol emas"] | None = None
    left_at: str | None = None
    candidate_id: int | None = None
    photo: str | None = None


# ---------- Nomzodlar ----------
CandidateStatus = Literal["Yangi", "Bog‘lanildi", "Bog‘lanilmadi", "Suhbat", "Ishga qabul qilindi", "Rad etildi"]


class CandidateIn(In):
    full_name: str | None = Field(default=None, min_length=3)
    gender: str | None = None
    phone: str | None = None
    age: int | None = None
    city: str | None = None
    position_id: int | None = None
    department_id: int | None = None
    source: str | None = None
    note: str | None = None
    created_at: str | None = None


class CandidateStatusIn(In):
    status: CandidateStatus
    interview_at: str | None = None
    reject_reason: str | None = None


class HireIn(In):
    hire_date: str
    position_id: int
    department_id: int
    start_training: bool = True


class ImportIn(In):
    rows: list[CandidateIn]


# ---------- Darslar ----------
class LessonIn(In):
    title: str | None = None
    duration: int | None = Field(default=None, ge=5, le=600)
    description: str | None = None
    content: str | None = None
    link: str | None = None


class TrainingStartIn(In):
    employee_id: int
    start_date: str | None = None


# ---------- Testlar ----------
class QuestionIn(In):
    id: int
    text: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_index: int = Field(ge=0)


class TestIn(In):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    position_ids: list[int] | None = None
    pass_percent: int | None = Field(default=None, ge=1, le=100)
    active: bool | None = None
    questions: list[QuestionIn] | None = None

    def values(self) -> dict:
        data = super().values()
        if self.questions is not None:
            # JSON da frontend bilan bir xil camelCase saqlanadi
            data["questions"] = [q.model_dump(by_alias=True) for q in self.questions]
        return data


class AssignIn(In):
    employee_id: int
    test_id: int | None = None


class SubmitIn(In):
    answers: dict[str, Any]


class TestSettingsIn(In):
    pass_percent: int | None = Field(default=None, ge=1, le=100)
    max_attempts: int | None = Field(default=None, ge=1, le=10)
    shuffle_questions: bool | None = None
    shuffle_options: bool | None = None
    auto_assign: bool | None = None
    activate_on_pass: bool | None = None


# ---------- Nomzodlar testi (landing) ----------
class LandingSubmitIn(In):
    full_name: str = Field(min_length=5, max_length=120)
    age: int = Field(ge=16, le=70)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    position: str = Field(min_length=2, max_length=80)
    phone: str = Field(default="", max_length=30)
    answers: dict[str, Any]
    duration_sec: int | None = Field(default=None, ge=0, le=86400)
    client_id: str | None = Field(default=None, max_length=64)

    _strip_text = field_validator("full_name", "position", "phone", mode="before")(_strip)

    @field_validator("full_name")
    @classmethod
    def _full_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v.split(" ")) < 2:
            raise ValueError("F.I.Sh. to‘liq kiritilsin (kamida familiya va ism)")
        return v


# ---------- Yakuniy bilim testi (ochiq, /test/yakuniy) ----------
class FinalRegisterIn(In):
    """Testdan oldingi ro‘yxatdan o‘tish: ism, familiya, yosh, tug‘ilgan sana (tekshiruv — final_test.validate_participant)."""
    first_name: str = Field(max_length=200)
    last_name: str = Field(max_length=200)
    age: Any = None
    birth_date: str = Field(default="", max_length=20)
    client_id: str | None = Field(default=None, max_length=64)  # ikki marta bosilsa — bitta ishtirokchi

    _strip_text = field_validator("first_name", "last_name", "birth_date", mode="before")(_strip)


class FinalSubmitIn(In):
    answers: dict[str, Any]
    duration_sec: int | None = Field(default=None, ge=0, le=86400)
    client_id: str | None = Field(default=None, max_length=64)  # takroriy yuborishdan himoya
    participant_id: int | None = None  # /register javobidagi id
    participant_key: str | None = Field(default=None, max_length=128)  # /register javobidagi maxfiy kalit


# ---------- Hujjatlar ----------
class DocumentStatusIn(In):
    status: Literal["Tasdiqlangan", "Kutilmoqda", "Rad etilgan"]
    comment: str = ""