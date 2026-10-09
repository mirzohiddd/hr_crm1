"""Bo‘limlar (departments.json) va lavozimlar (positions.json)."""
from fastapi import APIRouter, Depends, Response

from ..schemas import CatalogIn
from ..security import current_user
from ..store import get_store
from ..utils import bad_request, conflict, get_or_404

router = APIRouter(tags=["Bo‘limlar va lavozimlar"], dependencies=[Depends(current_user)])


def _crud(prefix: str, name: str, what: str, field: str, label: str):
    def coll():
        return getattr(get_store(), name)

    def duplicate(value: str, exclude: int | None = None) -> bool:
        v = value.strip().lower()
        return coll().first(lambda r: r["name"].lower() == v and r["id"] != exclude) is not None

    @router.get(f"/{prefix}")
    def list_():
        return sorted(coll().all(), key=lambda r: r["id"])

    @router.get(f"/{prefix}/{{item_id}}")
    def get_(item_id: int):
        return get_or_404(coll(), item_id, what)

    @router.post(f"/{prefix}")
    def create_(body: CatalogIn):
        data = body.values()
        if not data.get("name"):
            raise bad_request("Nomini kiriting")
        if duplicate(data["name"]):
            raise conflict(f"Bunday {what.lower()} mavjud")
        return coll().insert({"description": "", **data})

    @router.put(f"/{prefix}/{{item_id}}")
    def update_(item_id: int, body: CatalogIn):
        get_or_404(coll(), item_id, what)
        data = body.values()
        if data.get("name") and duplicate(data["name"], item_id):
            raise conflict(f"Bunday {what.lower()} mavjud")
        return coll().update(item_id, data)

    @router.delete(f"/{prefix}/{{item_id}}", status_code=204)
    def delete_(item_id: int):
        get_or_404(coll(), item_id, what)
        store = get_store()
        e = store.employees.count(**{field: item_id})
        c = store.candidates.count(**{field: item_id})
        if e or c:
            raise conflict(f"{label}ga {e} ta xodim va {c} ta nomzod bog‘langan. Avval ularni boshqasiga o‘tkazing.")
        coll().delete(item_id)
        return Response(status_code=204)


_crud("departments", "departments", "Bo‘lim", "departmentId", "Bo‘lim")
_crud("positions", "positions", "Lavozim", "positionId", "Lavozim")
