# HR CRM

Nomzodlar, xodimlar, 7 kunlik o‘quv dasturi, testlar va hujjatlarni boshqarish tizimi.

```
hr-crm/
├── backend/    Python FastAPI, ma'lumotlar JSON fayllarda  (API va saqlash)
├── frontend/   Vue 3 + Vite + Tailwind CSS + Pinia  (HR CRM paneli, login bilan)
├── landing/    Vue 3 + Vite + Tailwind CSS  (nomzodlar testi — /test/sotuv)
└── landing-2/  Vue 3 + Vite + Tailwind CSS  (yakuniy bilim testi — /test/yakuniy)
```

Frontend faqat API orqali ishlaydi; barcha ma'lumotlar `backend/data/` papkasidagi JSON fayllarda (`employees.json`, `candidates.json`, `documents.json`, `tests.json`, `test_results.json`, `users.json` va boshqalar), hujjat fayllari esa `backend/uploads/` da saqlanadi. Ma'lumotlar bazasi o‘rnatish shart emas; sahifa yangilanganda yoki server qayta ishga tushganda ma'lumotlar yo‘qolmaydi.

## Talablar

- **Python 3.10+** (backend)
- **Node.js 20.19+ yoki 22.12+** (frontend)

## Tez ishga tushirish

### 1. Backend (birinchi terminal)

Windows:
```bat
cd backend
run.bat
```

macOS / Linux:
```bash
cd backend
./run.sh
```

Skript virtual muhit yaratadi, kutubxonalarni o‘rnatadi va serverni ishga tushiradi:
`http://localhost:8000` (API hujjatlari: `http://localhost:8000/docs`).

Qo‘lda:
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (ikkinchi terminal)

```bash
cd frontend
npm install
npm run dev
```

Brauzerda: **http://localhost:5173**

### 3. Landing — nomzodlar testi (uchinchi terminal)

```bash
cd landing
npm install
npm run dev
```

Brauzerda: **http://localhost:5174/test/sotuv** (yoki CRM orqali: http://localhost:5173/test/sotuv).

### 4. Landing 2 — yakuniy bilim testi (to‘rtinchi terminal)

```bash
cd landing-2
npm install
npm run dev
```

Brauzerda: **http://localhost:5173/test/yakuniy** (CRM dev-serveri uni landing-2 ga — 5175 — uzatadi) yoki **http://localhost:5175/test/yakuniy**.

### 5. Kirish

Birinchi ishga tushirishda administrator yaratiladi:

| Login | Parol |
|---|---|
| `admin` | `admin123` |

Kirgandan so‘ng **Sozlamalar → Profil va parol** bo‘limida parolni darhol almashtiring. Boshqa HR xodimlarini **Sozlamalar → Foydalanuvchilar** bo‘limida qo‘shing.
Boshlang‘ich login/parolni `backend/.env` faylida (`ADMIN_LOGIN`, `ADMIN_PASSWORD`) birinchi ishga tushirishdan oldin o‘zgartirish mumkin.

## Nomzodlar testi (Sotuv lavozimi)

Nomzodlar uchun ochiq test sahifasi — login talab qilinmaydi:

Bu alohida ilova — `landing/` papkasi (batafsil: `landing/README.md`).

- Ishlab chiqishda: **http://localhost:5174/test/sotuv**
- Serverda: **http://server:8000/test/sotuv**

Nomzod F.I.Sh., yosh, sana va lavozimni kiritadi, 20 ta savolga bosqichma-bosqich javob beradi (1–14 — 1–5 ballik, 15–20 — A/B/C/D variantli) va barcha savollarga javob bergandan keyin testni topshiradi. Ball serverda hisoblanadi: **80% va yuqori — “Testdan o‘tdi”, past — “Testdan yiqildi”**.

Natijalar `backend/data/landing_results.json` faylida saqlanadi va CRM’da **Testlar → Nomzodlar testi** bo‘limida ko‘rinadi: har bir nomzod alohida qator, bosilganda 20 ta savol, variantlar, nomzod tanlagan javob va baholash kaliti bo‘yicha ball. Havolani nusxalash va “Baholash kaliti” tugmalari ham shu yerda.

Savollar, variantlar, lavozimlar va baholash kaliti bitta faylda: `backend/app/landing_tests/sotuv.json` (tahrirlash qoidalari fayl boshida). Avval topshirilgan natijalar o‘zgarmaydi — ularda savollar nusxasi saqlanadi.

## Yakuniy bilim testi (7 kunlik darslardan keyin)

Alohida ilova: **`landing-2/`** papkasi, manzili **/test/yakuniy** (batafsil: `landing-2/README.md`).

- Ochiq test: havola, token, ism kiritish va “Testni boshlash” tugmasi yo‘q — sahifaga kirish bilan 1-savol chiqadi.
- 20 ta savol ketma-ket (A/B/C/D), javob tanlangach keyingi savolga avtomatik o‘tiladi; yuqorida “1/20 savol” va progress; oldingi savolga qaytib javobni o‘zgartirish mumkin.
- 20-savoldan keyin **“Testni yakunlash”** — javoblar backendga yuboriladi. Har to‘g‘ri javob 1 ball: **16–20 — “Testdan o‘tdi”**, 0–15 — “Testdan o‘tmadi”.
- Natija `backend/data/final_results.json` ga yoziladi va CRM → **Testlar → Yakuniy bilim testi** da ko‘rinadi (“Ishtirokchi #N”, sana, to‘g‘ri/xato, ball, foiz, holat; bosilganda 20 ta savol, variantlar, tanlangan va to‘g‘ri javob).

Savollar va javoblar kaliti: `backend/app/landing_tests/yakuniy.json` (`correct` — to‘g‘ri variant harfi). Kalit frontendga yuborilmaydi.

## Serverga joylash (production)

Bitta server yetarli — backend frontend, landing va landing-2 build’larini ham ochib beradi:

```bash
cd frontend && npm install && npm run build      # frontend/dist yaratiladi
cd ../landing && npm install && npm run build    # landing/dist yaratiladi
cd ../landing-2 && npm install && npm run build  # landing-2/dist yaratiladi
cd ../backend && pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Endi `http://server:8000` — CRM paneli, `http://server:8000/test/sotuv` — nomzodlar testi, `http://server:8000/test/yakuniy` — yakuniy bilim testi, `http://server:8000/api/v1` — API.
Nginx ortida ishlatish va boshqa sozlamalar: `backend/README.md`.

## Qayerda nima

| Kerak bo‘lsa | Fayl / papka |
|---|---|
| Sahifalar va dizayn | `frontend/src/views`, `frontend/src/components` |
| API manzili | `frontend/.env` (`VITE_API_URL`) |
| Endpointlar | `backend/app/routers/` |
| Xodim maydonlari va validatsiya | `backend/app/schemas.py`, `backend/app/routers/employees.py` |
| JSON saqlash qatlami | `backend/app/store.py` |
| Boshlang‘ich bo‘limlar, lavozimlar, darslar, testlar | `backend/app/seed.py` |
| Ma'lumotlar (JSON) | `backend/data/*.json` |
| Sozlamalar va kalitlar | `backend/.env` |
| Yuklangan hujjatlar | `backend/uploads/` |
| Nomzodlar testi savollari va baholash kaliti | `backend/app/landing_tests/sotuv.json` |
| Nomzodlar testi sahifasi | `landing/src/App.vue` |
| Nomzodlar testi natijalari (CRM) | `frontend/src/components/tests/LandingResults.vue` |
| Yakuniy bilim testi savollari va kaliti | `backend/app/landing_tests/yakuniy.json` |
| Yakuniy bilim testi sahifasi | `landing-2/src/App.vue` |
| Yakuniy test natijalari (CRM) | `frontend/src/components/tests/FinalResults.vue` |

## Zaxira nusxa (backup)

Ikkita papkani nusxalang: `backend/data/` (barcha JSON fayllar) va `backend/uploads/` (hujjat fayllari).
Yangi versiyani o‘rnatganda shu ikki papkani saqlab qoling — ma'lumotlaringiz ularda.
