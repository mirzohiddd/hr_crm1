export const onlyDigits = (value) => String(value ?? '').replace(/\D/g, '')

// Telefon raqami — backend bilan bir xil qoidalar (backend/app/utils.py → normalize_phone)
export const PHONE_REQUIRED = 'Telefon raqamini kiriting'
export const PHONE_INVALID = 'Telefon raqami noto‘g‘ri. Namuna: +998 90 123 45 67'

/**
 * O‘zbekiston raqamini yagona ko‘rinishga keltiradi: '+998 90 123 45 67'.
 * Qabul qilinadi: '+998901234567', '998 90 123-45-67', '(90) 123 45 67', '901234567'. Noto‘g‘ri bo‘lsa — null.
 */
export function normalizePhone(value) {
  const raw = String(value ?? '').trim()
  if (!raw || !/^[\d\s+\-()]+$/.test(raw)) return null
  if ((raw.match(/\+/g) || []).length > 1 || (raw.includes('+') && !raw.startsWith('+'))) return null
  const digits = onlyDigits(raw)
  let national = null
  if (digits.length === 12 && digits.startsWith('998')) national = digits.slice(3)
  else if (digits.length === 9 && !raw.startsWith('+')) national = digits
  if (!national || national[0] === '0') return null
  return `+998 ${national.slice(0, 2)} ${national.slice(2, 5)} ${national.slice(5, 7)} ${national.slice(7)}`
}

/** Telefon maydoni xatosi: '' — xato yo‘q */
export function phoneError(value) {
  if (!String(value ?? '').trim()) return PHONE_REQUIRED
  return normalizePhone(value) ? '' : PHONE_INVALID
}

export function todayISO() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** '2026-10-09' -> '09.10.2026' */
export function formatDate(iso) {
  if (!iso) return ''
  const [y, m, d] = String(iso).slice(0, 10).split('-')
  return `${d}.${m}.${y}`
}

/** URL dan test nomi: /test/sotuv -> 'sotuv' */
export function slugFromPath(pathname = window.location.pathname) {
  const m = pathname.match(/\/test\/([a-z0-9-]+)\/?$/)
  return m ? m[1] : 'sotuv'
}