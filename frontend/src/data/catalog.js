/**
 * Bo‘limlar va lavozimlar (boshlang‘ich ma'lumot).
 * Bo‘lim va lavozim bir-biridan mustaqil: xodimga ikkalasi alohida tanlanadi
 * (masalan, "Dermolife" bo‘limida "Call Center" lavozimi).
 * Sozlamalar sahifasida qo‘shish / tahrirlash / o‘chirish mumkin.
 * Backend ulanganda: GET /departments, GET /positions
 */
export const departments = [
  { id: 1, name: 'Dermolife', description: 'Dermolife yo‘nalishi' },
  { id: 2, name: 'Gepomer', description: 'Gepomer yo‘nalishi' },
  { id: 3, name: 'Halila', description: 'Halila yo‘nalishi' },
  { id: 4, name: 'Marketing', description: 'Reklama, ijtimoiy tarmoqlar va izohlar' },
  { id: 5, name: 'Boshqa', description: 'Umumiy va xo‘jalik xodimlari' },
]

export const DEPARTMENT_NAMES = departments.map((d) => d.name)

export const positions = [
  { id: 1, name: 'Call Center', description: 'Kiruvchi va chiquvchi qo‘ng‘iroqlar, buyurtmalarni qabul qilish' },
  { id: 2, name: 'Kommentiy', description: 'Instagram va Telegram izohlari hamda direct xabarlarga javob berish' },
  { id: 3, name: 'Marketing', description: 'Reklama kampaniyalari va kontent rejasi' },
  { id: 4, name: 'Logistika', description: 'Yetkazib berish jadvali, kuryerlar va ombor nazorati' },
  { id: 5, name: 'Tozalik xodimi', description: 'Ofis va ish joylari tozaligi' },
  { id: 6, name: 'HR Admin', description: 'Nomzodlar, xodimlar va o‘quv jarayonini boshqarish' },
]

/** Lavozimga qarab odatiy bo‘lim (seed va migratsiya uchun) */
export function defaultDepartmentFor(positionId, n = 0) {
  if (positionId === 3) return 4 // Marketing
  if (positionId === 5 || positionId === 6) return 5 // Boshqa
  return [1, 2, 3][n % 3] // Dermolife / Gepomer / Halila
}
