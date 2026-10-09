export const onlyDigits = (value) => String(value ?? '').replace(/\D/g, '')

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
