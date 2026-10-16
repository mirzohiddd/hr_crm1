// ---------- Xodimlar ----------
// Yangi — 7 kunlik o‘quv dasturida; test topshirilgach "Faol" bo‘ladi.
export const EMPLOYEE_STATUSES = ['Yangi', 'Faol', 'Faol emas']
export const GENDERS = ['Erkak', 'Ayol']
// Kompyuter savodxonligi darajasi (1–4)
export const COMPUTER_SKILLS = [
  { value: 'Boshlang‘ich', level: 1, hint: 'Telefon va oddiy dasturlar' },
  { value: 'O‘rta', level: 2, hint: 'Word, Excel, internet' },
  { value: 'Yaxshi', level: 3, hint: 'Office, CRM, tez yozish' },
  { value: 'A’lo', level: 4, hint: 'Murakkab dasturlar, jadvallar' },
]

// ---------- Nomzodlar ----------
export const CANDIDATE_STAGES = [
  { value: 'Yangi', label: 'Yangi', tone: 'blue' },
  { value: 'Bog‘lanildi', label: 'Bog‘lanildi', tone: 'sky' },
  { value: 'Bog‘lanilmadi', label: 'Bog‘lanilmadi', tone: 'orange' },
  { value: 'Suhbat', label: 'Suhbat', tone: 'amber' },
  { value: 'Ishga qabul qilindi', label: 'Ishga qabul qilindi', tone: 'green' },
  { value: 'Rad etildi', label: 'Rad etildi', tone: 'red' },
]
export const CANDIDATE_STATUSES = CANDIDATE_STAGES.map((s) => s.value)
// Voronkadagi faol bosqichlar (yakuniy bo‘lmaganlar)
export const CANDIDATE_OPEN_STATUSES = ['Yangi', 'Bog‘lanildi', 'Bog‘lanilmadi', 'Suhbat']
export const CANDIDATE_SOURCES = ['Instagram', 'Google Sheets', 'Tavsiya', 'Boshqa']

// ---------- Hujjatlar ----------
export const DOCUMENT_TYPES = ['Pasport', 'Diplom', 'CV', 'Mehnat shartnomasi', 'Tibbiy ma’lumotnoma', 'Boshqa']
export const DOCUMENT_STATUSES = ['Tasdiqlangan', 'Kutilmoqda', 'Rad etilgan']
export const DOCUMENT_ACCEPT = '.pdf,.jpg,.jpeg,.png,.webp,.doc,.docx,.xls,.xlsx'
export const DOCUMENT_MAX_SIZE = 10 * 1024 * 1024 // 10 MB

// ---------- Darslar ----------
export const TRAINING_DAYS = 7

// ---------- Testlar ----------
export const TEST_RESULT_STATUSES = ['Kutilmoqda', 'O‘tdi', 'O‘tmadi']
// 80% va undan yuqori — "Testdan o‘tdi", past — "Testdan o‘tmadi" (Sozlamalarda o‘zgartirish mumkin)
export const DEFAULT_PASS_PERCENT = 80
export const RESULT_LABELS = { 'O‘tdi': 'Testdan o‘tdi', 'O‘tmadi': 'Testdan o‘tmadi', Kutilmoqda: 'Kutilmoqda' }
// Nomzodlar testi (landing, /test/sotuv): 80% va yuqori — o‘tdi, past — yiqildi
/** Landing natijasi holati: eski test — O‘tdi/Yiqildi; 40 savolli test — HR tavsiyasi (backend/app/profile_test.py) */
export const LANDING_RESULT_LABELS = {
  'O‘tdi': 'Testdan o‘tdi',
  Yiqildi: 'Testdan yiqildi',
  'Tavsiya etiladi': 'Tavsiya etiladi',
  'Suhbatda aniqlashtirish': 'Suhbatda aniqlashtirish',
  'Qo‘shimcha baholash kerak': 'Qo‘shimcha baholash kerak',
  'Ishonchsiz natija': 'Ishonchsiz natija',
}
/** Ijobiy natija: eski testdan o‘tgan yoki 40 savolli testda "Tavsiya etiladi" */
export const isLandingPositive = (r) => r?.status === 'O‘tdi' || r?.status === 'Tavsiya etiladi'
export const LANDING_TEST_SLUG = 'sotuv'

// ---------- Foydalanuvchilar ----------
export const USER_ROLES = [
  { value: 'admin', label: 'Administrator' },
  { value: 'hr', label: 'HR menejer' },
]
export const roleLabel = (role) => USER_ROLES.find((r) => r.value === role)?.label || role