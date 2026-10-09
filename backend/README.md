# HR CRM — Backend (FastAPI)

Python **FastAPI**. Ma'lumotlar bazasi ishlatilmaydi — hamma narsa **JSON fayllarda** saqlanadi (`backend/data/`):

| Fayl | Nima saqlanadi |
|---|---|
| `employees.json` | xodimlar (ism, familiya, otasining ismi, telefon, Telegram, tajriba, kompyuter savodxonligi, oylik kutuvi, bo‘lim, lavozim, rasm…) |
| `candidates.json` | nomzodlar va ularning holat tarixi |
| `documents.json` | hujjatlar ro‘yxati (fayllarning o‘zi — `backend/uploads/`) |
| `tests.json`, `test_results.json` | testlar va har bir urinishdagi javoblar |
| `users.json` | CRM foydalanuvchilari (parollar faqat xesh ko‘rinishida) |
| `final_results.json` | yakuniy bilim testi: har bir topshirish alohida — 20 ta savol nusxasi, tanlangan javoblar, to‘g‘ri/xato, ball, foiz, holat |
| `landing_results.json` | nomzodlar testi (`/test/sotuv`) natijalari: nomzod ma'lumotlari, 20 ta savol nusxasi, tanlangan javoblar, ball, foiz, holat |
| `departments.json`, `positions.json`, `lessons.json`, `trainings.json`, `settings.json` | bo‘limlar, lavozimlar, 7 kunlik darslar, dars progressi, test sozlamalari |

Yozish atomik (vaqtinchalik fayl → almashtirish), har yozishda oldingi holat `*.json.bak` sifatida saqlanadi. Oldingi versiyadagi `hr_crm.db` (SQLite) mavjud bo‘lsa, birinchi ishga tushirishda avtomatik JSON ga ko‘chiriladi va `hr_crm.db.migrated` deb qayta nomlanadi. Uvicorn’ni **bitta worker** bilan ishlating (standart).

## Ishga tushirish

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

yoki `run.bat` (Windows) / `./run.sh` (macOS, Linux).

- API: `http://localhost:8000/api/v1`
- Interaktiv hujjatlar (Swagger): `http://localhost:8000/docs`

Birinchi ishga tushirishda jadvallar yaratiladi va bo‘sh bo‘lsa to‘ldiriladi: bo‘limlar (Dermolife, Gepomer, Halila, Marketing, Boshqa), 6 ta lavozim, 7 kunlik dars rejasi, 2 ta test, test sozlamalari (o‘tish chegarasi 80%) va administrator (`admin` / `admin123`). Xodim yoki nomzod kabi soxta ma'lumotlar yaratilmaydi. Server qayta ishga tushganda mavjud ma'lumotlarga tegilmaydi.

## Sozlamalar (`.env`)

`.env.example` dan nusxa oling:

```bash
cp .env.example .env
```

| O‘zgaruvchi | Tavsif |
|---|---|
| `DATA_DIR` | JSON fayllar papkasi (standart `backend/data`) |
| `SECRET_KEY` | JWT kaliti. Bo‘sh bo‘lsa avtomatik yaratilib `.secret_key` ga yoziladi |
| `TOKEN_HOURS` | sessiya muddati (soat), standart 12 |
| `CORS_ORIGINS` | frontend boshqa domenda bo‘lsa, uning manzili |
| `UPLOAD_DIR`, `MAX_UPLOAD_MB` | hujjatlar papkasi va hajm chegarasi (10 MB) |
| `ADMIN_LOGIN`, `ADMIN_PASSWORD`, `ADMIN_NAME` | birinchi administrator (faqat foydalanuvchilar jadvali bo‘sh bo‘lganda) |
| `FRONTEND_DIST` | frontend build papkasi (standart `../frontend/dist`) — mavjud bo‘lsa, backend uni `/` da ochadi |
| `LANDING2_DIST` | yakuniy bilim testi build papkasi (standart `../landing-2/dist`) — `/test/yakuniy` da ochiladi |
| `LANDING_DIST` | nomzodlar testi build papkasi (standart `../landing/dist`) — mavjud bo‘lsa, `/test/` da ochiladi (`/test/sotuv`) |

## Tuzilma

```
backend/
  app/
    main.py        ilova, CORS, routerlar, frontend build’ni ochish
    config.py      .env sozlamalari
    store.py       JSON fayllarda saqlash (atomik yozish, zaxira .bak)
    migrate_sqlite.py  eski hr_crm.db dan JSON ga bir martalik ko‘chirish
    schemas.py     kiruvchi so‘rovlar validatsiyasi (camelCase JSON)
    security.py    parol xeshi (PBKDF2-SHA256), JWT, ruxsatlar
    services.py    test biriktirish, baholash, kaskad o‘chirish
    seed.py        boshlang‘ich ma'lumotnomalar
    landing.py     nomzodlar testi: savolnomani o‘qish, baholash kaliti, ball hisoblash
    final_test.py  yakuniy bilim testi: savollar, kalit, baholash
    landing_tests/ savolnomalar: sotuv.json (nomzodlar), yakuniy.json (yakuniy bilim testi + kalit)
    routers/       auth, catalog, employees, candidates, trainings, tests, documents, landing, final_test
  uploads/         yuklangan hujjat fayllari
  requirements.txt
```

## Xavfsizlik

- Parollar PBKDF2-SHA256 (260 000 iteratsiya, tuz bilan) xeshlanadi.
- Barcha endpointlar (`/auth/login`, `/health` va nomzodlar testi uchun ochiq `/public/*` dan tashqari) `Authorization: Bearer <token>` talab qiladi; har so‘rovda foydalanuvchi faolligi tekshiriladi (bloklangan foydalanuvchi darhol chiqariladi).
- `/users` — faqat administrator. Oxirgi faol administratorni o‘chirish/bloklash mumkin emas.
- Nomzodlar testi: ochiq so‘rovda baholash kaliti qaytarilmaydi, nomzodga ball ko‘rsatilmaydi; javoblar va lavozim serverda tekshiriladi, takroriy yuborish (`clientId`) bitta yozuv yaratadi.
- Hujjatlar: faqat PDF, rasm, Word, Excel; fayllar tasodifiy nom bilan saqlanadi, diskdagi yo‘l tashqariga chiqmaydi.
- Production’da HTTPS (masalan, Nginx + Let’s Encrypt) ortida ishlating va `SECRET_KEY` ni o‘rnating.

## Endpointlar (`/api/v1`)

| Metod | Endpoint | Tavsif |
|---|---|---|
| POST | `/auth/login` | `{ login, password }` → `{ access_token, user }` |
| GET / PUT | `/auth/me` | joriy foydalanuvchi / profil |
| POST | `/auth/change-password` | `{ current_password, new_password }` |
| GET, POST, PUT, DELETE | `/users`, `/users/{id}` | CRM foydalanuvchilari (admin) |
| GET, POST, PUT, DELETE | `/departments`, `/positions` | bo‘limlar, lavozimlar (bog‘langan bo‘lsa 409) |
| GET, POST, PUT, DELETE | `/employees`, `/employees/{id}` | xodimlar (o‘chirishda dars, natija, hujjatlar ham o‘chadi) |
| GET, POST, PUT, DELETE | `/candidates`, `/candidates/{id}` | nomzodlar |
| PATCH | `/candidates/{id}/status` | Yangi / Bog‘lanildi / Bog‘lanilmadi / Suhbat / Rad etildi |
| POST | `/candidates/{id}/hire` | nomzod → xodim (+ 7 kunlik dastur) |
| POST | `/candidates/import` | Google Sheets / CSV qatorlari (takroriy telefonlar o‘tkazib yuboriladi) |
| GET, PUT | `/lessons`, `/lessons/{id}` | 7 kunlik dastur mazmuni |
| GET, POST, DELETE | `/trainings`, `/trainings/{id}` | xodim dasturlari |
| POST / DELETE | `/trainings/{id}/days/{day}/complete`, `/trainings/{id}/days/{day}` | kunni belgilash / bekor qilish; 7-kunda test avtomatik |
| GET, POST, PUT, DELETE | `/tests`, `/tests/{id}` | testlar bazasi |
| GET, POST | `/test-results` | natijalar / testni qo‘lda yuborish |
| POST | `/test-results/{id}/submit` | javoblar → natija serverda: **80% va yuqori — O‘tdi** |
| GET / PUT | `/settings/tests` | o‘tish chegarasi, urinishlar soni va h.k. |
| GET, POST | `/documents` | ro‘yxat (`?employee_id=`) / yuklash (multipart) |
| GET | `/documents/{id}/file` | faylni ko‘rish / yuklab olish |
| PATCH | `/documents/{id}/status` | tasdiqlash / rad etish |
| DELETE | `/documents/{id}` | hujjat va faylni o‘chirish |
| GET | `/public/tests/{slug}` | **ochiq**: nomzodlar testi savollari (baholash kalitisiz) |
| POST | `/public/tests/{slug}/submit` | **ochiq**: `{ fullName, age, date, position, phone?, answers }` — barcha savollarga javob majburiy; ball serverda; 1 IP dan soatiga 20 tadan ko‘p emas |
| GET | `/landing-tests`, `/landing-tests/{slug}/key` | savolnomalar / baholash kaliti (HR) |
| GET | `/landing-results`, `/landing-results/{id}` | nomzodlar natijalari / batafsil: savollar, variantlar, javob, ball |
| PATCH | `/landing-results/{id}/viewed` | “ko‘rildi” belgisi |
| DELETE | `/landing-results/{id}` | natijani o‘chirish |
| GET | `/public/final-test` | **ochiq**: yakuniy test — 20 ta savol (to‘g‘ri javoblarsiz); havola/token talab qilinmaydi |
| POST | `/public/final-test/submit` | **ochiq**: `{ answers, durationSec?, clientId? }` — barcha savollarga javob majburiy; ball serverda: 16–20 — O‘tdi, 0–15 — O‘tmadi; takroriy yuborish (`clientId`) bitta yozuv |
| GET | `/final-test/info` | test haqida (savollar soni, o‘tish foizi) |
| GET, DELETE | `/final-results`, `/final-results/{id}` | barcha topshirishlar / batafsil: savollar, variantlar, tanlangan javob, to‘g‘ri javob; o‘chirish |
| GET | `/health` | server holati |
