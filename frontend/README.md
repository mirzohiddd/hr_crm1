# HR CRM — Frontend

Kompaniya HR bo‘limi uchun CRM interfeysi: **Vue 3 + Vite + Tailwind CSS + Vue Router + Pinia**.
Ma’lumotlar `../backend` (FastAPI) orqali saqlanadi. Ishga tushirishdan oldin backendni yoqing — umumiy yo‘riqnoma: `../README.md`.

## Ishga tushirish

```bash
npm install
npm run dev       # http://localhost:5173
npm run build     # production build (dist/)
npm run preview   # build natijasini ko‘rish
```

Node.js 20.19+ yoki 22.12+ talab qilinadi.

`.env` da `VITE_API_URL=/api/v1` — so‘rovlar Vite proxy orqali `VITE_BACKEND_URL` (standart `http://127.0.0.1:8000`) ga uzatiladi.

### Kirish

Backend bilan: `admin` / `admin123` (birinchi ishga tushirishda backend yaratadi).

Backendsiz demo rejim (`.env` da `VITE_USE_MOCK=true`) — ma’lumotlar faqat brauzerda saqlanadi:

| Login | Parol | Rol |
|---|---|---|
| `admin` | `admin123` | Administrator (foydalanuvchilarni ham boshqaradi) |
| `hr` | `hr12345` | HR menejer |

Birinchi kirishdan so‘ng **Sozlamalar → Profil va parol** bo‘limida parolni almashtiring.

## Modullar (menyu)

| Sahifa | Route | Imkoniyatlar |
|---|---|---|
| Kirish | `/login` | login + parol, “Meni eslab qol”, 5 ta noto‘g‘ri urinishdan so‘ng 1 daqiqa bloklash. Login qilmagan foydalanuvchi boshqa sahifalarga kira olmaydi |
| Bosh sahifa | `/dashboard` | xodimlar, yangi nomzodlar, o‘qiyotganlar, testdan o‘tish %; 12 oylik xodimlar grafigi; nomzodlar voronkasi; bugungi suhbatlar; darsdagi xodimlar; bo‘limlar / lavozimlar kesimi |
| Nomzodlar | `/candidates` | Voronka (kanban, sudrab o‘tkazish) va ro‘yxat ko‘rinishi; **Yangi → Bog‘lanildi / Bog‘lanilmadi → Suhbat → Ishga qabul qilindi / Rad etildi**; “Bog‘lanilmadi”da urinishlar soni hisoblanadi; suhbat vaqti, rad etish sababi, tarix; Google Sheets / CSV / nusxa-joylash orqali import (telefon bo‘yicha takrorlar o‘tkazib yuboriladi). “Ishga qabul qilish” → nomzod avtomatik xodimga aylanadi va 7 kunlik darsga qo‘shiladi |
| Xodimlar | `/employees` | F.I.Sh, telefon, lavozim, **bo‘lim** (Dermolife, Gepomer, Halila, Marketing, Boshqa), ishga kirgan sana, holat; bo‘lim bo‘yicha tezkor filtr (soni bilan), qidiruv, filtrlar, bir nechta xodimni belgilab bo‘limga ommaviy o‘tkazish |
| Xodim profili | `/employees/:id` | barcha ma’lumotlar, bo‘lim va lavozim, Darslar (7 kun), Test natijalari (har bir savol bo‘yicha javoblar), Hujjatlar (yuklash/ko‘rish/yuklab olish/o‘chirish), nomzodlik tarixi |
| Darslar | `/lessons` | 7 kunlik o‘quv dasturi: har kun “Bajarildi” → progress saqlanadi; kunlar ketma-ket ochiladi; 7-kun tugagach xodim lavozimiga mos testga avtomatik yuboriladi |
| Testlar | `/tests` | Topshirganlar jadvali: **Ism, Familiya, Telefon, Yosh, Jinsi, To‘g‘ri javoblar, Jami savollar, Foiz, Testdan o‘tdi/o‘tmadi, Sana**; qatorni bosganda har bir savol: savol, xodim javobi, to‘g‘ri javob, to‘g‘ri/noto‘g‘ri (urinishlar bo‘yicha); Excel (CSV) eksport; **80% va yuqori — “Testdan o‘tdi”**; Testlar bazasi: savollar, variantlar, to‘g‘ri javob, lavozimlarga bog‘lash |
| Hujjatlar | `/documents` | Yuklash (PDF, rasm, Word, Excel, 10 MB gacha, bir nechta fayl), ko‘rish (rasm/PDF preview), yuklab olish, o‘chirish, tasdiqlash/rad etish |
| Sozlamalar | `/settings` | Lavozimlar, Bo‘limlar, Darslar (7 kun mazmuni), Test sozlamalari, Foydalanuvchilar (faqat administrator), Profil va parol, Tizim (demo ma’lumotlarni tiklash) |

Lavozimlar (boshlang‘ich): **Call Center, Kommentiy, Marketing, Logistika, Tozalik xodimi, HR Admin**.
Bo‘limlar: **Dermolife, Gepomer, Halila, Marketing, Boshqa**. Bo‘lim va lavozim bir-biridan mustaqil — xodimga (va ixtiyoriy nomzodga) ikkalasi alohida tanlanadi, `positionId` / `departmentId` orqali bog‘lanadi (nom o‘zgarsa hamma joyda yangilanadi).

Sidebar: desktopda ochiladi/yig‘iladi (yig‘ilganda faqat ikonlar va hover’da nom), holat eslab qolinadi; planshetda ikonlar + ochiladigan panel; mobilda chiqib keluvchi menyu.

### Asosiy jarayon

```
Nomzod (Instagram / Google Sheets) → Bog‘lanildi → Suhbat → Ishga qabul qilish
   → Xodim ("Yangi") → 7 kunlik darslar (har kun progress) → Test (avtomatik)
   → Natija avtomatik: O‘tdi (xodim "Faol" bo‘ladi) / O‘tmadi (qayta topshirish)
```

## Tuzilma

```
src/
  api/          client.js, resource.js, mockDb.js (localStorage “baza”), auth.js (login + users),
                catalog.js, candidates.js, employees.js, trainings.js, tests.js, documents.js
  assets/       global CSS
  components/
    layout/     Sidebar, Topbar, PageHeader
    ui/         Button, Modal, StatusBadge, SearchInput, Select, ... (umumiy)
    dashboard/  StatCard, EmployeeStatsChart, DepartmentBreakdown
    candidates/ CandidateForm, CandidateDetails, HireDialog, StageDialog, ImportDialog, SourceIcon
    employees/  EmployeeTable, EmployeeForm
    lessons/    TrainingTimeline, TrainingProgress
    tests/      TestRunner, TestForm
    documents/  DocumentTable, DocumentDetails, DocumentUpload
    settings/   SettingsSection, ProfileSettings, CatalogSettings, LessonsSettings, TestSettings, UsersSettings
  composables/  usePagination, useToast, useClickOutside, useTrainingActions, useDocumentActions
  constants/    holatlar, manbalar, hujjat turlari, rollar
  data/         seed ma’lumotlar (catalog, employees, lessons, tests, seed.js)
  router/       marshrutlar + login himoyasi (beforeEach)
  stores/       Pinia: auth, catalog, employees, candidates, trainings, tests, documents, users, toast
  utils/        sana, formatlash, validatsiya, csv (import), hash (SHA-256), fileStore (IndexedDB)
  views/        *View.vue sahifalar
```

Ma’lumot oqimi: **Komponent → Pinia store → `src/api/*` → (mock yoki FastAPI)**.

## Mock rejim

Ma’lumotlar tuzilmasi o‘zgarganda (`src/api/mockDb.js` → `VERSION`, `MIGRATIONS`) avvalgi saqlangan ma’lumotlar **o‘chirilmaydi**, balki yangi tuzilmaga ko‘chiriladi. v2 → v3: eski bo‘limlar yangi ro‘yxatga (nomi mos kelmasa “Boshqa”ga) o‘tkaziladi, test natijalari 80% qoidasi bo‘yicha qayta baholanadi.

`VITE_API_URL` bo‘sh bo‘lsa, barcha ma’lumotlar brauzerning `localStorage` (`hr-crm:db:*`) va yuklangan fayllar `IndexedDB` (`hr-crm-files`) da saqlanadi — sahifa yangilanganda progress yo‘qolmaydi. Ma’lumotlar faqat shu brauzerda ko‘rinadi. Boshlang‘ich holatga qaytarish: **Sozlamalar → Tizim → Demo ma’lumotlarni tiklash**.

> **Xavfsizlik:** mock rejimdagi login faqat interfeysni himoyalaydi (parollar SHA-256 + tuz bilan saqlanadi). Haqiqiy himoya uchun backend ulang — server har bir so‘rovda tokenni va rolni tekshirishi shart.

## Backendga ulash

`.env` (namuna: `.env.example`):

```env
VITE_API_URL=/api/v1
VITE_BACKEND_URL=http://127.0.0.1:8000
VITE_USE_MOCK=false
```

Backend boshqa domenda bo‘lsa: `VITE_API_URL=https://api.kompaniya.uz/api/v1` va backend `.env` da `CORS_ORIGINS` ga frontend manzilini yozing. Endpointlar to‘liq ro‘yxati: `../backend/README.md`.

So‘rovlarga `Authorization: Bearer <token>` qo‘shiladi; server `401` qaytarsa foydalanuvchi login sahifasiga qaytariladi.

FastAPI tomonda kutilayotgan endpointlar:

| Metod | Endpoint | Tavsif |
|---|---|---|
| POST | `/auth/login` | `{ login, password }` → `{ access_token, user }` |
| GET / PUT | `/auth/me` | joriy foydalanuvchi / profilni yangilash |
| POST | `/auth/change-password` | `{ current_password, new_password }` |
| GET/POST, PUT/DELETE | `/users`, `/users/{id}` | CRM foydalanuvchilari (faqat admin) |
| GET/POST, PUT/DELETE | `/departments`, `/positions` (+ `/{id}`) | bo‘lim va lavozimlar (bog‘langan yozuv bo‘lsa 409) |
| GET/POST, PUT/DELETE | `/candidates`, `/candidates/{id}` | nomzodlar |
| PATCH | `/candidates/{id}/status` | `{ status, interviewAt?, rejectReason? }` |
| POST | `/candidates/{id}/hire` | `{ hireDate, positionId, departmentId, startTraining }` → `{ candidate, employee, training }` |
| POST | `/candidates/import` | `{ rows: [...] }` → `{ created, skipped }` |
| GET/POST, PUT/DELETE | `/employees`, `/employees/{id}` | xodimlar (o‘chirishda darslar, natijalar, hujjatlar ham o‘chadi) |
| GET, PUT | `/lessons`, `/lessons/{id}` | 7 kunlik dastur mazmuni |
| GET/POST, DELETE | `/trainings`, `/trainings/{id}` | xodim o‘quv dasturi |
| POST | `/trainings/{id}/days/{day}/complete` | kun bajarildi → `{ training, testResult }` (7-kunda test yaratiladi) |
| DELETE | `/trainings/{id}/days/{day}` | oxirgi belgini bekor qilish |
| GET/POST, PUT/DELETE | `/tests`, `/tests/{id}` | testlar bazasi |
| GET/POST | `/test-results` | natijalar / testni qo‘lda yuborish `{ employeeId, testId? }` |
| POST | `/test-results/{id}/submit` | `{ answers: { [savolId]: variantIndeksi } }` → `{ result, employee }`; natija serverda hisoblanadi (`score >= passPercent`), har bir urinishda `answers` va savollar nusxasi (`questions`) saqlanadi |
| GET / PUT | `/settings/tests` | `passPercent` (standart 80), urinishlar, avtomatik yuborish |
| GET | `/documents` | hujjatlar ro‘yxati |
| POST | `/documents` | multipart: `employeeId, type, status, comment, file` |
| GET | `/documents/{id}/file` | fayl (ko‘rish / yuklab olish) |
| PATCH | `/documents/{id}/status` | `{ status, comment }` |
| DELETE | `/documents/{id}` | hujjatni o‘chirish |

## Dizayn tizimi

Oq + ko‘k: primary `#2563EB`, light blue `#EFF6FF`, fon `#F8FAFC`, matn `#0F172A`, ikkinchi darajali matn `#64748B`, chegara `#E2E8F0`. Shrift — Onest. Yumshoq soyalar, qisqa animatsiyalar, `prefers-reduced-motion` hisobga olinadi.

Responsive: desktop — to‘liq sidebar, planshet — ixcham sidebar, mobil — hamburger menyu; jadvallar mobil ekranda kartalarga o‘tadi, kanban ustunlari gorizontal suriladi.
