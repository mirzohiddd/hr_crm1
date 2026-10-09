"""Xodimlar (employees.json)."""
from fastapi import APIRouter, Depends, Response

from ..schemas import EmployeeIn
from ..security import current_user
from ..services import delete_employee_cascade
from ..store import get_store
from ..utils import bad_request, full_name, get_or_404, split_name, today

router = APIRouter(prefix="/employees", tags=["Xodimlar"], dependencies=[Depends(current_user)])

EMPTY = {
    "firstName": "", "lastName": "", "middleName": "", "fullName": "",
    "phone": "", "telegram": "", "previousWork": "", "computerSkill": "", "expectedSalary": None,
    "gender": "", "address": "", "email": "", "birthDate": "", "age": None,
    "departmentId": None, "positionId": None, "hireDate": "", "status": "Yangi",
    "leftAt": None, "candidateId": None, "photo": None,
}


def _names(current: dict, data: dict) -> None:
    """Ism / familiya / otasining ismi ↔ F.I.Sh (fullName) — doim mos holda."""
    if any(k in data for k in ("firstName", "lastName", "middleName")):
        merged = {**current, **data}
        data["fullName"] = full_name(merged.get("lastName"), merged.get("firstName"), merged.get("middleName"))
    elif "fullName" in data:
        last, first, middle = split_name(data["fullName"])
        data.update(lastName=last, firstName=first, middleName=middle)


def _left_at(current: dict, data: dict) -> None:
    """“Faol emas” bo‘lganda ishdan ketgan sana, qayta faollashganda — tozalanadi."""
    if "status" not in data:
        return
    if data["status"] == "Faol emas":
        data["leftAt"] = data.get("leftAt") or current.get("leftAt") or today()
    else:
        data["leftAt"] = None


def _with_names(e: dict) -> dict:
    """Eski yozuvlarda (faqat fullName) ism qismlarini to‘ldirib qaytarish."""
    if not e.get("firstName") and e.get("fullName"):
        last, first, middle = split_name(e["fullName"])
        e = {**e, "lastName": last, "firstName": first, "middleName": middle}
    return {**EMPTY, **e}


@router.get("")
def list_employees():
    rows = get_store().employees.all()
    rows.sort(key=lambda e: (e.get("hireDate") or "", e["id"]), reverse=True)
    return [_with_names(e) for e in rows]


@router.get("/{employee_id}")
def get_employee(employee_id: int):
    return _with_names(get_or_404(get_store().employees, employee_id, "Xodim"))


@router.post("")
def create_employee(body: EmployeeIn):
    data = body.values()
    _names({}, data)
    if not data.get("firstName") or not data.get("lastName") or not data.get("phone"):
        raise bad_request("Ism, familiya va telefon majburiy")
    _left_at({}, data)
    return _with_names(get_store().employees.insert({**EMPTY, "hireDate": today(), **data}))


@router.put("/{employee_id}")
def update_employee(employee_id: int, body: EmployeeIn):
    current = _with_names(get_or_404(get_store().employees, employee_id, "Xodim"))
    data = body.values()
    _names(current, data)
    _left_at(current, data)
    return _with_names(get_store().employees.update(employee_id, data))


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: int):
    store = get_store()
    get_or_404(store.employees, employee_id, "Xodim")
    delete_employee_cascade(store, employee_id)
    store.employees.delete(employee_id)
    return Response(status_code=204)
