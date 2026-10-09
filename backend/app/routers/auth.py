"""Kirish, profil va CRM foydalanuvchilari (users.json)."""
from fastapi import APIRouter, Depends, HTTPException, Response

from ..schemas import ChangePasswordIn, LoginIn, MeIn, UserIn
from ..security import admin_user, create_token, current_user, hash_password, verify_password
from ..store import get_store
from ..utils import conflict, get_or_404, not_found, now_local, public

router = APIRouter(tags=["Kirish va foydalanuvchilar"])


def _by_login(login: str) -> dict | None:
    login = login.strip().lower()
    return get_store().users.first(lambda u: u["login"].lower() == login)


@router.post("/auth/login")
def login(body: LoginIn):
    user = _by_login(body.login)
    if not user or not verify_password(body.password, user.get("passwordHash", "")):
        raise HTTPException(status_code=401, detail="Login yoki parol noto‘g‘ri")
    if not user.get("active", True):
        raise HTTPException(status_code=403, detail="Hisobingiz bloklangan. Administratorga murojaat qiling.")
    user = get_store().users.update(user["id"], {"lastLoginAt": now_local()})
    return {"access_token": create_token(user), "token_type": "bearer", "user": public(user)}


@router.get("/auth/me")
def me(user: dict = Depends(current_user)):
    return public(user)


@router.put("/auth/me")
def update_me(body: MeIn, user: dict = Depends(current_user)):
    return public(get_store().users.update(user["id"], body.values()))


@router.post("/auth/change-password", status_code=204)
def change_password(body: ChangePasswordIn, user: dict = Depends(current_user)):
    if not verify_password(body.current_password, user.get("passwordHash", "")):
        raise HTTPException(status_code=400, detail="Joriy parol noto‘g‘ri")
    get_store().users.update(user["id"], {"passwordHash": hash_password(body.new_password)})
    return Response(status_code=204)


# ---------- Foydalanuvchilar (faqat administrator) ----------
def _active_admins() -> int:
    return get_store().users.count(role="admin", active=True)


def _check_login(login: str, user_id: int | None = None):
    found = _by_login(login)
    if found and found["id"] != user_id:
        raise conflict("Bu login band. Boshqa login tanlang.")


@router.get("/users")
def list_users(_: dict = Depends(admin_user)):
    return [public(u) for u in sorted(get_store().users.all(), key=lambda u: u["fullName"])]


@router.post("/users")
def create_user(body: UserIn, _: dict = Depends(admin_user)):
    data = body.values()
    if not data.get("fullName") or not data.get("login") or not data.get("password"):
        raise HTTPException(status_code=422, detail="F.I.Sh, login va parol majburiy")
    data["login"] = data["login"].strip().lower()
    _check_login(data["login"])
    password = data.pop("password")
    user = get_store().users.insert({
        "role": "hr", "active": True, "email": "", "phone": "",
        **data,
        "passwordHash": hash_password(password),
        "createdAt": now_local()[:10],
        "lastLoginAt": None,
    })
    return public(user)


@router.put("/users/{user_id}")
def update_user(user_id: int, body: UserIn, me_: dict = Depends(admin_user)):
    user = get_or_404(get_store().users, user_id, "Foydalanuvchi")
    data = body.values()
    if "login" in data:
        data["login"] = data["login"].strip().lower()
        _check_login(data["login"], user_id)
    is_active_admin = user["role"] == "admin" and user.get("active", True)
    demoting = is_active_admin and (data.get("role", "admin") != "admin" or data.get("active") is False)
    if demoting and _active_admins() <= 1:
        raise conflict("Tizimda kamida bitta faol administrator qolishi kerak")
    if user_id == me_["id"] and data.get("active") is False:
        raise conflict("O‘zingizni bloklay olmaysiz")
    password = data.pop("password", None)
    if password:
        data["passwordHash"] = hash_password(password)
    return public(get_store().users.update(user_id, data))


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, me_: dict = Depends(admin_user)):
    user = get_store().users.get(user_id)
    if not user:
        raise not_found("Foydalanuvchi")
    if user_id == me_["id"]:
        raise conflict("O‘zingizni o‘chira olmaysiz")
    if user["role"] == "admin" and user.get("active", True) and _active_admins() <= 1:
        raise conflict("Oxirgi administratorni o‘chirib bo‘lmaydi")
    get_store().users.delete(user_id)
    return Response(status_code=204)
