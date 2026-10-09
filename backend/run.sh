#!/usr/bin/env bash
# HR CRM backend: virtual muhit, kutubxonalar va server
set -e
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python)
[ -d .venv ] || { echo "Virtual muhit yaratilmoqda..."; "$PY" -m venv .venv; }
source .venv/bin/activate
pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env
echo
echo "Backend: http://localhost:8000   (API hujjatlari: http://localhost:8000/docs)"
exec uvicorn app.main:app --reload --port 8000
