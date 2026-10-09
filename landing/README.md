# HR CRM — Landing (nomzodlar testi)

Sotuv lavozimiga nomzodlar uchun ochiq test sahifasi. Login talab qilinmaydi.
Vue 3 + Vite + Tailwind CSS (CRM bilan bir xil texnologiya), alohida ilova.
Yakuniy bilim testi — alohida ilova: `../landing-2/`.


- Manzil: **`/test/sotuv`**
- Savollar, variantlar va baholash kaliti backendda: `backend/app/landing_tests/sotuv.json`
- Ball serverda hisoblanadi; nomzodga ko‘rsatilmaydi
- Natijalar: `backend/data/landing_results.json` → CRM: **Testlar → Nomzodlar testi**

## Ishga tushirish (ishlab chiqish)

Avval backend ishlayotgan bo‘lsin (`backend/`), keyin:

```bash
cd landing
npm install
npm run dev
```

Brauzerda: **http://localhost:5174/test/sotuv**

CRM dev-serveri (`frontend`, 5173) ham `/test/...` so‘rovlarini shu serverga uzatadi, shuning uchun
CRM dagi “Ochish” tugmasi (`http://localhost:5173/test/sotuv`) ham ishlaydi.

## Build (production)

```bash
npm run build      # landing/dist
```

Backend `landing/dist` ni avtomatik `/test/` manzilida ochadi: `http://server:8000/test/sotuv`.
Landingni alohida domenda joylashtirsangiz, `.env` da `VITE_API_URL=https://crm.kompaniya.uz/api/v1`
yozing va backend `.env` dagi `CORS_ORIGINS` ga landing manzilini qo‘shing.

## Tuzilma

```
landing/
  index.html
  vite.config.js        base: /test/, port 5174, /api → backend proxy
  src/
    App.vue             /test/sotuv: ma'lumotlar → 20 ta savol → tekshirish → yakun
    api.js              GET /public/tests/{slug}, POST /public/tests/{slug}/submit
    utils.js
    components/         ScaleAnswer (1–5), ChoiceAnswer (A/B/C/D), BrandLogo
    assets/             main.css, logo.png
```
