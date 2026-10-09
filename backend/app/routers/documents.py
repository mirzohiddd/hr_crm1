"""Xodimlar hujjatlari (documents.json + uploads/ papkasidagi fayllar)."""
import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from ..config import MAX_UPLOAD_MB, UPLOAD_DIR
from ..schemas import DocumentStatusIn
from ..security import current_user
from ..services import delete_document_file
from ..store import get_store
from ..utils import get_or_404, not_found, public, today

router = APIRouter(prefix="/documents", tags=["Hujjatlar"])

ALLOWED = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx", ".xls", ".xlsx"}
STATUSES = {"Tasdiqlangan", "Kutilmoqda", "Rad etilgan"}


@router.get("")
def list_documents(employee_id: int | None = None, _: dict = Depends(current_user)):
    store = get_store()
    rows = store.documents.filter(employeeId=employee_id) if employee_id else store.documents.all()
    rows.sort(key=lambda d: (d.get("uploadedAt") or "", d["id"]), reverse=True)
    return [public(d) for d in rows]


@router.get("/{doc_id}")
def get_document(doc_id: int, _: dict = Depends(current_user)):
    return public(get_or_404(get_store().documents, doc_id, "Hujjat"))


@router.post("")
async def upload_document(
    employeeId: int = Form(...),
    type: str = Form(...),
    status: str = Form("Tasdiqlangan"),
    comment: str = Form(""),
    file: UploadFile = File(...),
    user: dict = Depends(current_user),
):
    store = get_store()
    if not store.employees.get(employeeId):
        raise not_found("Xodim")
    name = Path(file.filename or "fayl").name
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail="Bu turdagi fayl qabul qilinmaydi (PDF, rasm, Word, Excel)")
    if status not in STATUSES:
        status = "Kutilmoqda"

    stored = f"{uuid.uuid4().hex}{ext}"
    target = UPLOAD_DIR / stored
    size = 0
    limit = MAX_UPLOAD_MB * 1024 * 1024
    with target.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                out.close()
                target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"Fayl hajmi {MAX_UPLOAD_MB} MB dan oshmasin")
            out.write(chunk)

    approved = status == "Tasdiqlangan"
    doc = store.documents.insert({
        "employeeId": employeeId,
        "type": type,
        "fileName": name,
        "fileSize": size,
        "mimeType": file.content_type or mimetypes.guess_type(name)[0] or "application/octet-stream",
        "filePath": stored,
        "uploadedAt": today(),
        "uploadedBy": user["fullName"],
        "status": status,
        "reviewedBy": user["fullName"] if approved else None,
        "reviewedAt": today() if approved else None,
        "comment": comment,
    })
    return public(doc)


@router.get("/{doc_id}/file")
def download_file(doc_id: int, _: dict = Depends(current_user)):
    doc = get_or_404(get_store().documents, doc_id, "Hujjat")
    path = UPLOAD_DIR / doc["filePath"] if doc.get("filePath") else None
    if not path or not path.exists():
        raise not_found("Fayl")
    return FileResponse(path, media_type=doc.get("mimeType") or None, filename=doc["fileName"])


@router.patch("/{doc_id}/status")
def set_status(doc_id: int, body: DocumentStatusIn, user: dict = Depends(current_user)):
    get_or_404(get_store().documents, doc_id, "Hujjat")
    return public(get_store().documents.update(doc_id, {
        "status": body.status, "comment": body.comment, "reviewedBy": user["fullName"], "reviewedAt": today(),
    }))


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: int, _: dict = Depends(current_user)):
    doc = get_or_404(get_store().documents, doc_id, "Hujjat")
    delete_document_file(doc)
    get_store().documents.delete(doc_id)
    return Response(status_code=204)
