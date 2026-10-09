export const MONTHS = [
  'Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun',
  'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr',
]
export const MONTHS_SHORT = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyn', 'Iyl', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']
export const WEEKDAYS = ['Yakshanba', 'Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba']
export const WEEKDAYS_SHORT = ['Ya', 'Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh']

/** 'YYYY-MM-DD' -> mahalliy Date (timezone siljishisiz) */
export function parseISO(iso) {
  const [y, m, d] = String(iso).slice(0, 10).split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function toISO(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export const todayISO = () => toISO(new Date())

export function addDays(iso, days) {
  const d = parseISO(iso)
  d.setDate(d.getDate() + days)
  return toISO(d)
}

export function diffDays(fromIso, toIso) {
  return Math.round((parseISO(toIso) - parseISO(fromIso)) / 86400000)
}

export function isWeekend(iso) {
  const day = parseISO(iso).getDay()
  return day === 0 || day === 6
}

/** 30.09.2026 */
export function formatDate(iso) {
  if (!iso) return '—'
  const [y, m, d] = String(iso).slice(0, 10).split('-')
  return `${d}.${m}.${y}`
}

/** 30 Sentabr 2026 */
export function formatDateLong(iso) {
  if (!iso) return '—'
  const d = parseISO(iso)
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`
}

export const weekdayName = (iso) => WEEKDAYS[parseISO(iso).getDay()]
export const weekdayShort = (iso) => WEEKDAYS_SHORT[parseISO(iso).getDay()]

export function ageFrom(birthIso, onIso = todayISO()) {
  const b = parseISO(birthIso)
  const on = parseISO(onIso)
  let age = on.getFullYear() - b.getFullYear()
  const m = on.getMonth() - b.getMonth()
  if (m < 0 || (m === 0 && on.getDate() < b.getDate())) age--
  return age
}

/** Ish staji: "2 yil 3 oy", "5 oy", "12 kun" */
export function tenure(hireIso, onIso = todayISO()) {
  const days = diffDays(hireIso, onIso)
  if (days < 0) return `${formatDateLong(hireIso)} dan boshlaydi`
  if (days === 0) return 'Bugun boshlagan'
  if (days < 31) return `${days} kun`
  const h = parseISO(hireIso)
  const on = parseISO(onIso)
  let months = (on.getFullYear() - h.getFullYear()) * 12 + (on.getMonth() - h.getMonth())
  if (on.getDate() < h.getDate()) months--
  const years = Math.floor(months / 12)
  const rest = months % 12
  if (years === 0) return `${Math.max(rest, 1)} oy`
  return rest ? `${years} yil ${rest} oy` : `${years} yil`
}

export function formatAgo(minutes) {
  if (minutes < 1) return 'hozirgina'
  if (minutes < 60) return `${minutes} daqiqa oldin`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} soat oldin`
  const days = Math.floor(hours / 24)
  return days === 1 ? 'kecha' : `${days} kun oldin`
}

/** "08:47" -> daqiqalar */
export function timeToMinutes(value) {
  if (!value) return null
  const [h, m] = value.split(':').map(Number)
  return h * 60 + m
}

export function minutesToTime(total) {
  const h = String(Math.floor(total / 60)).padStart(2, '0')
  const m = String(total % 60).padStart(2, '0')
  return `${h}:${m}`
}

export function formatDuration(minutes) {
  if (minutes == null || minutes <= 0) return '—'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m ? `${h} soat ${m} daq` : `${h} soat`
}

/** Hozirgi mahalliy vaqt: 'YYYY-MM-DDTHH:MM' */
export function nowLocal() {
  const d = new Date()
  return `${toISO(d)}T${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

/** '2026-10-08T14:30' -> '08.10.2026, 14:30' */
export function formatDateTime(value) {
  if (!value) return '—'
  const [date, time] = String(value).split('T')
  return time ? `${formatDate(date)}, ${time.slice(0, 5)}` : formatDate(date)
}

/** Xodim yoshi: tug‘ilgan sanadan, bo‘lmasa nomzodlikda ko‘rsatilgan yoshdan */
export function employeeAge(employee) {
  if (!employee) return null
  if (employee.birthDate) return ageFrom(employee.birthDate)
  return employee.age || null
}
