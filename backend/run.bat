@echo off
REM HR CRM backend: virtual muhit, kutubxonalar va server
cd /d "%~dp0"
if not exist .venv (
  echo Virtual muhit yaratilmoqda...
  python -m venv .venv || (echo Python topilmadi. https://www.python.org dan o'rnating. & pause & exit /b 1)
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
if not exist .env copy .env.example .env >nul
echo.
echo Backend: http://localhost:8000   (API hujjatlari: http://localhost:8000/docs)
uvicorn app.main:app --reload --port 8000
pause
