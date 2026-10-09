"""
HR CRM — backend (FastAPI). Ma'lumotlar backend/data/*.json fayllarida saqlanadi.

Ishga tushirish (backend/ papkasida):
    uvicorn app.main:app --reload --port 8000

API: http://localhost:8000/api/v1   Hujjatlar: http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import CORS_ORIGINS, DATA_DIR, FRONTEND_DIST, LANDING2_DIST, LANDING_DIST, LEGACY_SQLITE
from .migrate_sqlite import migrate_if_needed
from .final_test import load as load_final
from .landing import list_questionnaires
from .routers import auth, candidates, catalog, documents, employees, final_test, landing, tests, trainings
from .seed import seed
from .store import get_store

log = logging.getLogger("hr-crm")


@asynccontextmanager
async def lifespan(_: FastAPI):
    store = get_store()
    # Oldingi versiyadagi SQLite ma'lumotlari bo‘lsa — JSON fayllarga ko‘chiriladi (bir marta)
    migrated = migrate_if_needed(store, LEGACY_SQLITE)
    if migrated:
        log.warning("hr_crm.db dan JSON ga ko‘chirildi: %s", migrated)
    # Bo‘sh JSON fayllarni boshlang‘ich ma'lumotnomalar bilan to‘ldirish (mavjud ma'lumotlarga tegmaydi)
    created = seed(store)
    log.warning("Ma'lumotlar papkasi: %s", DATA_DIR)
    if created:
        log.warning("Boshlang‘ich ma'lumotlar yaratildi: %s", ", ".join(created))
    # Landing savolnomalarini tekshirish (fayldagi xato darhol ko‘rinsin)
    try:
        log.warning("Landing testlar: %s", ", ".join(f"/test/{q['slug']}" for q in list_questionnaires()) or "yo‘q")
    except ValueError as e:
        log.error("Landing savolnoma faylida xato: %s", e)
    try:
        q = load_final()
        log.warning("Yakuniy bilim testi: /test/yakuniy (%s ta savol)", len(q["questions"]))
    except ValueError as e:
        log.error("yakuniy.json faylida xato: %s", e)
    yield


app = FastAPI(title="HR CRM API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api/v1")


@api.get("/health", tags=["Tizim"])
def health():
    return {"status": "ok"}


for module in (auth, catalog, employees, candidates, trainings, tests, documents, landing, final_test):
    api.include_router(module.router)
api.include_router(landing.public_router)  # nomzodlar uchun ochiq test (login talab qilinmaydi)
api.include_router(final_test.public_router)  # yakuniy bilim testi (bir martalik havola bilan)
app.include_router(api)


# ---------- Landing 2 build (ixtiyoriy): landing-2/dist — yakuniy bilim testi /test/yakuniy ----------
if (LANDING2_DIST / "index.html").exists():
    if (LANDING2_DIST / "assets").exists():
        app.mount("/test/yakuniy/assets", StaticFiles(directory=LANDING2_DIST / "assets"), name="landing2-assets")

    @app.get("/test/yakuniy", include_in_schema=False)
    @app.get("/test/yakuniy/{path:path}", include_in_schema=False)
    def landing2_page(path: str = ""):
        file = (LANDING2_DIST / path).resolve()
        if path and file.is_file() and LANDING2_DIST.resolve() in file.parents:
            return FileResponse(file)
        return FileResponse(LANDING2_DIST / "index.html", headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


# ---------- Landing build (ixtiyoriy): landing/dist — nomzodlar testi /test/sotuv ----------
if (LANDING_DIST / "index.html").exists():
    if (LANDING_DIST / "assets").exists():
        app.mount("/test/assets", StaticFiles(directory=LANDING_DIST / "assets"), name="landing-assets")

    @app.get("/test", include_in_schema=False)
    @app.get("/test/{path:path}", include_in_schema=False)
    def landing_page(path: str = ""):
        file = (LANDING_DIST / path).resolve()
        if path and file.is_file() and LANDING_DIST.resolve() in file.parents:
            return FileResponse(file)
        return FileResponse(LANDING_DIST / "index.html")


# ---------- Frontend build (ixtiyoriy): frontend/dist mavjud bo‘lsa, bitta serverdan ochiladi ----------
if (FRONTEND_DIST / "index.html").exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Topilmadi")
        file = (FRONTEND_DIST / path).resolve()
        if path and file.is_file() and FRONTEND_DIST.resolve() in file.parents:
            return FileResponse(file)
        return FileResponse(FRONTEND_DIST / "index.html")
