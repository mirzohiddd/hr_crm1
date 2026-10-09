# HR CRM — Landing 2 (yakuniy bilim testi)

7 kunlik o‘quv dasturidan keyingi yakuniy bilim testi. Alohida ilova (Vue 3 + Vite + Tailwind CSS — CRM bilan bir xil texnologiya).

- Manzil: **`/test/yakuniy`** — ochiq test: havola/token, ism kiritish va “Testni boshlash” tugmasi yo‘q.
- Sahifaga kirish bilan 1-savol chiqadi; javob tanlangach keyingi savolga avtomatik o‘tiladi.
- Yuqorida “1/20 savol” hisoblagichi va progress bar; savol raqamlari orqali oldingi savolga qaytib, javobni o‘zgartirish mumkin.
- 20-savoldan keyin **“Testni yakunlash”** — barcha savollarga javob berilmaguncha yuborilmaydi.
- Savollar to‘g‘ri javoblarsiz keladi; tekshirish va ball faqat backendda (`backend/app/landing_tests/yakuniy.json`).
- Natija: to‘g‘ri/xato javoblar soni, ball, foiz, holat (16–20 ball — “Testdan o‘tdi”, 0–15 — “Testdan o‘tmadi”).
- Natijalar: `backend/data/final_results.json` → CRM: **Testlar → Yakuniy bilim testi**.
- Sahifa yangilansa, javoblar (yoki natija) saqlanib qoladi.

## Ishga tushirish (ishlab chiqish)

Avval backend ishlayotgan bo‘lsin (`backend/`), keyin:

```bash
cd landing-2
npm install
npm run dev
```

Brauzerda: **http://localhost:5175/test/yakuniy** (yoki CRM dev-serveri orqali: http://localhost:5173/test/yakuniy).

## Build (production)

```bash
npm run build      # landing-2/dist
```

Backend `landing-2/dist` ni avtomatik `/test/yakuniy` manzilida ochadi: `http://server:8000/test/yakuniy`.
Alohida domenda joylashtirsangiz, `.env` da `VITE_API_URL=https://crm.kompaniya.uz/api/v1` yozing va backend `.env` dagi `CORS_ORIGINS` ga manzilni qo‘shing.

## Tuzilma

```
landing-2/
  index.html
  vite.config.js        base: /test/yakuniy/, port 5175, /api → backend proxy
  src/
    App.vue             chapda rasm, o‘ngda test: 20 savol → “Testni yakunlash” → natija
    api.js              GET /public/final-test, POST /public/final-test/submit
    components/         ChoiceAnswer (A/B/C/D), BrandLogo
    assets/             main.css, logo.png, yakuniy-hero.svg (chap tomondagi rasm)
```
